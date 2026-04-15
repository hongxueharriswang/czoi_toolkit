# system5_traffic.py
from datetime import timedelta
import random
from czoi.core import System, Zone, Role, User, Application
from czoi_with_unilog_toolkit.czoi.simulation import SimulationEngine

# Road network: simple grid
city = Zone("City")
district1 = Zone("District1", parent=city)
district2 = Zone("District2", parent=city)
# Roads (as zones)
roadA = Zone("RoadA", parent=district1)
roadB = Zone("RoadB", parent=district1)
roadC = Zone("RoadC", parent=district2)
intersection = Zone("Intersection", parent=city)  # connects roads

system = System()
for z in [city, district1, district2, roadA, roadB, roadC, intersection]:
    system.add_zone(z)
    z.capacity = 10  # vehicles per zone
    z.speed_limit = 50

# Roles
commuter = Role("Commuter", city)
controller = Role("TrafficController", city)
emergency = Role("EmergencyVehicle", city)
system.add_role(commuter)
system.add_role(controller)
system.add_role(emergency)

# App
traffic_app = Application("Traffic")
navigate_op = traffic_app.add_operation("navigate")
signal_op = traffic_app.add_operation("signal_control")
reroute_op = traffic_app.add_operation("reroute")
system.add_application(traffic_app)

# Permissions
commuter.grant_permission(navigate_op)
controller.grant_permission(signal_op)
controller.grant_permission(reroute_op)
emergency.grant_permission(navigate_op)

# Create vehicles
vehicles = []
for i in range(50):
    v = User(f"vehicle_{i}")
    v.attributes["speed"] = random.uniform(20, 60)
    v.attributes["destination"] = random.choice([roadB, roadC])
    # Start at roadA
    v.assign_role(roadA, commuter)
    vehicles.append(v)
    system.add_user(v)

# Add a few emergency vehicles
for i in range(2):
    ev = User(f"emergency_{i}")
    ev.attributes["speed"] = 80
    ev.assign_role(roadA, emergency)
    vehicles.append(ev)
    system.add_user(ev)

# Controllers
ctrl = User("controller")
ctrl.assign_role(city, controller)
system.add_user(ctrl)

class TrafficSim(SimulationEngine):
    def step(self, current_time):
        # Move vehicles along simple route: RoadA -> Intersection -> Destination
        for v in vehicles:
            # Find current zone
            current_zone_id = next(iter(v.zone_role_assignments))
            current_zone = self.system.get_zone(current_zone_id)
            if current_zone == v.attributes["destination"]:
                continue  # arrived
            # Determine next zone
            if current_zone == roadA:
                next_zone = intersection
            elif current_zone == intersection:
                next_zone = v.attributes["destination"]
            else:
                continue
            # Check capacity
            if len([u for u in vehicles if next_zone.id in u.zone_role_assignments]) < next_zone.capacity:
                # Move
                del v.zone_role_assignments[current_zone_id]
                v.assign_role(next_zone, commuter if "emergency" not in v.username else emergency)
                self.logs.append({
                    "timestamp": current_time.isoformat(),
                    "vehicle": v.username,
                    "from": current_zone.name,
                    "to": next_zone.name
                })

sim = TrafficSim(system, None, None)
sim.run(timedelta(minutes=10), step=timedelta(seconds=5))
# Count arrivals
arrived = sum(1 for v in vehicles if v.attributes["destination"].id in v.zone_role_assignments)
print(f"Arrived: {arrived}/{len(vehicles)}")