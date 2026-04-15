# evacuation_simulation.py
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from czoi.core import System, Zone, Role, User, Application
from czoi.permission import PermissionEngine
from czoi.simulation import SimulationEngine
from czoi.daemon.base import Daemon
from czoi.storage.sqlalchemy import Storage
from czoi.constraint.models import Constraint, ConstraintType
from czoi.constraint.manager import ConstraintManager

# ----------------------------------------------------------------------
# 1. Define the building zones (hierarchical structure)
# ----------------------------------------------------------------------
building = Zone("Building")
floor1 = Zone("Floor1", parent=building)
floor2 = Zone("Floor2", parent=building)

# Rooms and corridors on floor 1
room101 = Zone("Room101", parent=floor1)
room102 = Zone("Room102", parent=floor1)
corridor1 = Zone("Corridor1", parent=floor1)
exit1 = Zone("Exit1", parent=floor1)  # main exit on floor 1

# Rooms and corridors on floor 2
room201 = Zone("Room201", parent=floor2)
room202 = Zone("Room202", parent=floor2)
corridor2 = Zone("Corridor2", parent=floor2)
exit2 = Zone("Exit2", parent=floor2)  # secondary exit on floor 2

# Set capacities (max people per zone)
for zone in [room101, room102, room201, room202]:
    zone.capacity = 10
for zone in [corridor1, corridor2]:
    zone.capacity = 20
for zone in [exit1, exit2]:
    zone.capacity = 5  # exits can only hold a few at a time (bottleneck)

# Staircase connecting floors (optional)
stairs = Zone("Stairs", parent=building)
stairs.capacity = 15

# Add all zones to the system
system = System()
for zone in [building, floor1, floor2, room101, room102, room201, room202,
             corridor1, corridor2, exit1, exit2, stairs]:
    system.add_zone(zone)

# ----------------------------------------------------------------------
# 2. Define roles
# ----------------------------------------------------------------------
evacuee = Role("Evacuee", building)
guide = Role("Guide", building)
safety_officer = Role("SafetyOfficer", building)
system.add_role(evacuee)
system.add_role(guide)
system.add_role(safety_officer)

# ----------------------------------------------------------------------
# 3. Define application and operations
# ----------------------------------------------------------------------
evac_app = Application("EvacuationApp")
move_op = evac_app.add_operation("move_to")
guide_op = evac_app.add_operation("guide")
report_op = evac_app.add_operation("report_congestion")
system.add_application(evac_app)

# Set permissions
evacuee.grant_permission(move_op)
guide.grant_permission(guide_op)
safety_officer.grant_permission(report_op)

# ----------------------------------------------------------------------
# 4. Create people (users) with attributes
# ----------------------------------------------------------------------
def create_people(num_people: int, num_guides: int = 0, base_familiarity: float = 0.5):
    people = []
    # Regular evacuees
    for i in range(num_people):
        u = User(f"person_{i}")
        u.attributes["speed"] = random.uniform(0.8, 1.5)  # m/s
        u.attributes["familiarity"] = base_familiarity + random.uniform(-0.2, 0.2)
        u.attributes["familiarity"] = max(0.1, min(1.0, u.attributes["familiarity"]))
        # Start in a random room on floor 1 or 2
        start_zone = random.choice([room101, room102, room201, room202])
        u.assign_role(start_zone, evacuee)
        u.attributes["current_zone"] = start_zone.id
        people.append(u)
        system.add_user(u)
    # Guides
    for i in range(num_guides):
        g = User(f"guide_{i}")
        g.attributes["speed"] = random.uniform(1.0, 1.8)
        g.attributes["familiarity"] = 1.0  # guides know the best routes
        # Start in same distribution
        start_zone = random.choice([room101, room102, room201, room202])
        g.assign_role(start_zone, guide)
        g.attributes["current_zone"] = start_zone.id
        people.append(g)
        system.add_user(g)
    return people

# Create initial population: 50 evacuees, 3 guides, base familiarity 0.6
people = create_people(num_people=50, num_guides=3, base_familiarity=0.6)

# ----------------------------------------------------------------------
# 5. Define constraints
# ----------------------------------------------------------------------
constraint_manager = ConstraintManager()

# Identity constraint: zone occupancy cannot exceed capacity
def capacity_constraint_eval(context: Dict[str, Any]) -> bool:
    zone = context.get("zone")
    if not zone:
        return True
    # Count people currently in this zone
    count = sum(1 for u in people if u.attributes.get("current_zone") == zone.id)
    return count <= zone.capacity

capacity_constraint = Constraint(
    name="ZoneCapacity",
    type=ConstraintType.IDENTITY,
    target={"type": "zone"},
    condition="capacity_constraint_eval"  # will be handled by custom evaluator
)
# In real implementation, we'd register a callable; here we'll enforce in simulation step

# Trigger constraint: if congestion > 80%, alert
def congestion_trigger(context):
    zone = context.get("zone")
    if not zone:
        return False
    count = sum(1 for u in people if u.attributes.get("current_zone") == zone.id)
    return count > 0.8 * zone.capacity

# We'll handle triggers via daemons

# ----------------------------------------------------------------------
# 6. Define daemons
# ----------------------------------------------------------------------
class CongestionMonitor(Daemon):
    """Monitors zone occupancy and logs congestion alerts."""
    def __init__(self, system, interval=1.0):
        super().__init__("CongestionMonitor", interval)
        self.system = system

    async def check(self) -> List[str]:
        alerts = []
        for zone in self.system.zones:
            if hasattr(zone, 'capacity'):
                count = sum(1 for u in people if u.attributes.get("current_zone") == zone.id)
                if count > 0.8 * zone.capacity:
                    alerts.append(f"CONGESTION:{zone.name}:{count}/{zone.capacity}")
        return alerts

    async def execute(self, action: str):
        if action.startswith("CONGESTION"):
            self.logger.warning(action)

class SafetyAlertDaemon(Daemon):
    """Monitors for dangerous situations (e.g., people stuck)."""
    def __init__(self, system, interval=2.0):
        super().__init__("SafetyAlert", interval)
        self.system = system
        self.previous_positions = {}

    async def check(self) -> List[str]:
        alerts = []
        for u in people:
            prev = self.previous_positions.get(u.id)
            curr = u.attributes.get("current_zone")
            if prev and prev == curr:
                # Same zone for two consecutive checks? Might be stuck.
                # In real implementation, we'd track time.
                pass
            self.previous_positions[u.id] = curr
        return alerts

# ----------------------------------------------------------------------
# 7. Custom simulation engine
# ----------------------------------------------------------------------
class EvacuationSimulation(SimulationEngine):
    def __init__(self, system, permission_engine, storage, people, exit_zones):
        super().__init__(system, permission_engine, storage)
        self.people = people
        self.exit_zones = exit_zones
        self.evacuation_time = None
        self.evacuated_count = 0

    def step(self, current_time):
        # Shuffle people to avoid order bias
        random.shuffle(self.people)

        for person in self.people:
            # Skip if already evacuated
            current_zone_id = person.attributes.get("current_zone")
            if not current_zone_id:
                continue
            current_zone = self.system.get_zone(current_zone_id)
            if current_zone in self.exit_zones:
                continue  # already safe

            # Determine next zone based on familiarity and role
            next_zone = self.choose_next_zone(person, current_zone)

            if next_zone:
                # Check capacity of next zone
                current_occupancy = sum(1 for p in self.people
                                        if p.attributes.get("current_zone") == next_zone.id)
                if current_occupancy < next_zone.capacity:
                    # Move person
                    person.attributes["current_zone"] = next_zone.id
                    # Update role assignment (for permission engine)
                    # Remove old zone assignment, add new
                    # For simplicity, we'll just track via attributes

                    self.logs.append({
                        "timestamp": current_time.isoformat(),
                        "person": person.username,
                        "from": current_zone.name,
                        "to": next_zone.name,
                        "role": "guide" if "guide" in person.username else "evacuee"
                    })

                    # Check if evacuated
                    if next_zone in self.exit_zones:
                        self.evacuated_count += 1
                        if self.evacuation_time is None:
                            self.evacuation_time = current_time

        # Stop simulation if all evacuated or time limit reached
        if self.evacuated_count == len(self.people):
            self.running = False

    def choose_next_zone(self, person, current_zone):
        """Decide next zone based on familiarity and role."""
        # Simple deterministic logic based on building layout
        # In real model, this would be a graph search; here we hardcode paths.
        if current_zone.name == "Room101":
            return self.system.get_zone_by_name("Corridor1")
        elif current_zone.name == "Room102":
            return self.system.get_zone_by_name("Corridor1")
        elif current_zone.name == "Room201":
            return self.system.get_zone_by_name("Corridor2")
        elif current_zone.name == "Room202":
            return self.system.get_zone_by_name("Corridor2")
        elif current_zone.name == "Corridor1":
            # Choose exit based on familiarity
            if "guide" in person.username:
                # Guides know which exit is less congested
                count1 = sum(1 for p in self.people if p.attributes.get("current_zone") == self.exit_zones[0].id)
                count2 = sum(1 for p in self.people if p.attributes.get("current_zone") == self.exit_zones[1].id)
                return self.exit_zones[0] if count1 <= count2 else self.exit_zones[1]
            else:
                # Evacuees follow familiarity: higher familiarity -> use main exit (exit1)
                if person.attributes["familiarity"] > 0.7:
                    return self.exit_zones[0]  # main exit
                else:
                    # Might go to stairs or other exit
                    if random.random() < 0.5:
                        return self.exit_zones[1]  # secondary exit
                    else:
                        return self.system.get_zone_by_name("Stairs")
        elif current_zone.name == "Corridor2":
            # Similar logic for floor 2
            if "guide" in person.username:
                count1 = sum(1 for p in self.people if p.attributes.get("current_zone") == self.exit_zones[0].id)
                count2 = sum(1 for p in self.people if p.attributes.get("current_zone") == self.exit_zones[1].id)
                return self.exit_zones[1] if count2 <= count1 else self.exit_zones[0]
            else:
                if person.attributes["familiarity"] > 0.7:
                    return self.exit_zones[1]
                else:
                    return self.system.get_zone_by_name("Stairs")
        elif current_zone.name == "Stairs":
            # Stairs lead to floor1 corridor
            return self.system.get_zone_by_name("Corridor1")
        else:
            return None

    def get_zone_by_name(self, name):
        for z in self.system.zones:
            if z.name == name:
                return z
        return None

# ----------------------------------------------------------------------
# 8. Run simulations
# ----------------------------------------------------------------------
def run_simulation(people_list, exit_zones, max_steps=100, step_seconds=1):
    """Run a simulation and return results."""
    # Reset people positions (reassign starting zones if needed)
    # For simplicity, we assume people list is already set up.

    # Create storage (in-memory)
    storage = Storage("sqlite:///:memory:")

    # Permission engine (simplified – all allowed for simulation)
    class AllowAllEngine(PermissionEngine):
        def decide(self, user, operation, zone, context=None):
            return True

    engine = AllowAllEngine(storage)

    sim = EvacuationSimulation(system, engine, storage, people_list, exit_zones)
    sim.run(timedelta(seconds=max_steps * step_seconds), step=timedelta(seconds=step_seconds))

    # Collect statistics
    final_positions = [p.attributes.get("current_zone") for p in people_list]
    evacuated = sum(1 for z in final_positions if z in [ez.id for ez in exit_zones])
    time_to_evacuate = sim.evacuation_time
    logs = sim.logs

    return {
        "evacuated": evacuated,
        "total": len(people_list),
        "evacuation_time": time_to_evacuate,
        "logs": logs
    }

# ----------------------------------------------------------------------
# Simulation 2.1: Baseline (normal familiarity)
# ----------------------------------------------------------------------
print("="*50)
print("Simulation 2.1: Baseline (moderate familiarity)")
print("="*50)

people_baseline = create_people(num_people=50, num_guides=3, base_familiarity=0.6)
exit_list = [exit1, exit2]
result1 = run_simulation(people_baseline, exit_list, max_steps=200)
print(f"Evacuated: {result1['evacuated']}/{result1['total']}")
if result1['evacuation_time']:
    print(f"Time to last evacuation: {result1['evacuation_time']}")
else:
    print("Not all evacuated within simulation time.")

# ----------------------------------------------------------------------
# Simulation 2.2: Guide effect (more guides, better guidance)
# ----------------------------------------------------------------------
print("\n" + "="*50)
print("Simulation 2.2: Guide effect (more guides)")
print("="*50)

people_guides = create_people(num_people=50, num_guides=10, base_familiarity=0.5)  # more guides, lower base familiarity
result2 = run_simulation(people_guides, exit_list, max_steps=200)
print(f"Evacuated: {result2['evacuated']}/{result2['total']}")
if result2['evacuation_time']:
    print(f"Time to last evacuation: {result2['evacuation_time']}")
else:
    print("Not all evacuated within simulation time.")

# ----------------------------------------------------------------------
# Simulation 2.3: Panic (low familiarity, high speed variability)
# ----------------------------------------------------------------------
print("\n" + "="*50)
print("Simulation 2.3: Panic (low familiarity, high speed variability)")
print("="*50)

# Custom create function for panic
def create_panic_people(num_people, num_guides=0):
    people = []
    for i in range(num_people):
        u = User(f"panic_person_{i}")
        u.attributes["speed"] = random.uniform(1.2, 2.5)  # faster but erratic
        u.attributes["familiarity"] = random.uniform(0.1, 0.4)  # low familiarity
        start_zone = random.choice([room101, room102, room201, room202])
        u.assign_role(start_zone, evacuee)
        u.attributes["current_zone"] = start_zone.id
        people.append(u)
        system.add_user(u)
    return people

people_panic = create_panic_people(num_people=50, num_guides=0)
result3 = run_simulation(people_panic, exit_list, max_steps=200)
print(f"Evacuated: {result3['evacuated']}/{result3['total']}")
if result3['evacuation_time']:
    print(f"Time to last evacuation: {result3['evacuation_time']}")
else:
    print("Not all evacuated within simulation time.")

# ----------------------------------------------------------------------
# Optional: Start daemons (if running as a long-lived process)
# ----------------------------------------------------------------------
# import asyncio
# async def run_daemons():
#     monitor = CongestionMonitor(system)
#     safety = SafetyAlertDaemon(system)
#     await asyncio.gather(monitor.run(), safety.run())
# 
# asyncio.run(run_daemons())