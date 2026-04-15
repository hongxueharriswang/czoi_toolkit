# example5_simulation.py
from datetime import timedelta
from czoi.core import System, Zone, Role, User, Application
from czoi.simulation.engine import SimulationEngine
from czoi.permission.engine import PermissionEngine
from czoi.storage.sqlalchemy import Storage

# Setup a minimal system
system = System()
root = Zone("Root")
it = Zone("IT", parent=root)
hr = Zone("HR", parent=root)
system.add_zone(root)
system.add_zone(it)
system.add_zone(hr)

# Roles
it_eng = Role("Engineer", it)
it_eng.grant_permission(Application("IT App").add_operation("reboot"))
hr_assist = Role("Assistant", hr)
hr_assist.grant_permission(Application("HR App").add_operation("view_salary"))
system.add_role(it_eng)
system.add_role(hr_assist)

# Users
alice = User("alice")
alice.assign_role(it, it_eng)
bob = User("bob")
bob.assign_role(hr, hr_assist)
system.add_user(alice)
system.add_user(bob)

# Create a simple in-memory permission engine (like Example 1's SimpleEngine)
class SimpleEngine(PermissionEngine):
    def __init__(self, system):
        self.system = system

    def get_effective_permissions(self, role, zone):
        return set(role.base_permissions)

    def decide(self, user, operation, zone, context=None):
        if zone.id not in user.zone_role_assignments:
            return False
        for role, weight in user.zone_role_assignments[zone.id]:
            if weight > 0 and operation in self.get_effective_permissions(role, zone):
                return True
        return False

engine = SimpleEngine(system)

# Storage (not really used in simulation but required)
storage = Storage("sqlite:///:memory:")

# Simulation engine
sim = SimulationEngine(system, engine, storage)

# Run simulation for 10 seconds with 1-second steps
sim.run(timedelta(seconds=10), step=timedelta(seconds=1))

# Analyze
analysis = sim.analyze()
print("Simulation results:")
print(f"Total requests: {analysis['total_requests']}")
print(f"Allowed: {analysis['allowed']}")
print(f"Denied: {analysis['denied']}")
print(f"Allow rate: {analysis['allow_rate']:.2f}")

# Save logs
sim.save_logs("simulation_logs.json")
print("Logs saved to simulation_logs.json")