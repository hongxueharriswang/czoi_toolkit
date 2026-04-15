# system3_self_driving_fleet.py
import random
import math
from datetime import timedelta
from czoi.core import System, Zone, Role, User, Application

# City zones
city = Zone("City")
downtown = Zone("Downtown", parent=city)
suburb = Zone("Suburb", parent=city)
airport = Zone("Airport", parent=city)
charging_station = Zone("ChargingStation", parent=city)
system = System()
for z in [city, downtown, suburb, airport, charging_station]:
    system.add_zone(z)

taxi_role = Role("Taxi", city)
manager_role = Role("FleetManager", city)
passenger_role = Role("Passenger", city)  # temporary
system.add_role(taxi_role)
system.add_role(manager_role)
system.add_role(passenger_role)

app = Application("RideHailing")
request_op = app.add_operation("request_ride")
accept_op = app.add_operation("accept_ride")
navigate_op = app.add_operation("navigate")
charge_op = app.add_operation("charge")
system.add_application(app)

taxi_role.grant_permission(accept_op)
taxi_role.grant_permission(navigate_op)
taxi_role.grant_permission(charge_op)
passenger_role.grant_permission(request_op)

# Taxis
taxis = []
for i in range(20):
    t = User(f"taxi_{i}")
    t.attributes["position"] = [random.uniform(-122.5, -122.3), random.uniform(37.7, 37.8)]
    t.attributes["battery"] = 100.0
    t.attributes["status"] = "idle"
    t.attributes["passenger_count"] = 0
    t.assign_role(city, taxi_role)
    taxis.append(t)
    system.add_user(t)

# Manager
mgr = User("manager")
mgr.assign_role(city, manager_role)
system.add_user(mgr)

class TaxiSim(SimulationEngine):
    def __init__(self, system, engine, storage):
        super().__init__(system, engine, storage)
        self.requests = 0
        self.served = 0
        self.wait_times = []

    def step(self, current_time):
        # Generate random ride requests
        if random.random() < 0.3:
            self.requests += 1
            pickup = random.choice([downtown, suburb, airport])
            dropoff = random.choice([downtown, suburb, airport])
            self.logs.append({"timestamp": current_time.isoformat(),
                              "event": "request", "pickup": pickup.name, "dropoff": dropoff.name})
            # Find nearest idle taxi
            nearest = None
            min_dist = float('inf')
            for t in taxis:
                if t.attributes["status"] == "idle":
                    # simplified distance
                    dist = random.uniform(0, 10)  # placeholder
                    if dist < min_dist:
                        min_dist = dist
                        nearest = t
            if nearest:
                nearest.attributes["status"] = "en route"
                self.served += 1
                wait = random.uniform(1, 5)  # minutes
                self.wait_times.append(wait)
                self.logs.append({"timestamp": current_time.isoformat(),
                                  "event": "assign", "taxi": nearest.username,
                                  "wait": wait})
        # Update taxi statuses (simulate movement)
        for t in taxis:
            if t.attributes["status"] == "en route":
                if random.random() < 0.2:
                    t.attributes["status"] = "on trip"
                t.attributes["battery"] -= 0.1
            elif t.attributes["status"] == "on trip":
                if random.random() < 0.3:
                    t.attributes["status"] = "idle"
                t.attributes["battery"] -= 0.2
            else:
                t.attributes["battery"] -= 0.05
            # Charge if low
            if t.attributes["battery"] < 20:
                t.attributes["status"] = "charging"
                t.attributes["battery"] += 1
            if t.attributes["battery"] > 100:
                t.attributes["battery"] = 100

sim = TaxiSim(system, None, None)
sim.run(timedelta(hours=1), step=timedelta(minutes=1))
avg_wait = sum(sim.wait_times)/len(sim.wait_times) if sim.wait_times else 0
print(f"Requests: {sim.requests}, Served: {sim.served}, Avg wait: {avg_wait:.2f} min")