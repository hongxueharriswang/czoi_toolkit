# system1_robot_transport.py
import random
import math
from datetime import timedelta, datetime
from czoi.core import System, Zone, Role, User, Application
from czoi.simulation import SimulationEngine
from czoi.permission import PermissionEngine
from czoi.daemon.builtins import Daemon
from czoi.storage.sqlalchemy import Storage

# --- CZOA Setup ---
system = System()
warehouse = Zone("Warehouse")
loading = Zone("LoadingZone", parent=warehouse)
storage = Zone("StorageZone", parent=warehouse)
obstacle_area = Zone("ObstacleArea", parent=warehouse)
system.add_zone(warehouse)
system.add_zone(loading)
system.add_zone(storage)
system.add_zone(obstacle_area)

# Roles
transporter = Role("TransporterRobot", warehouse)
supervisor = Role("SupervisorRobot", warehouse)
maintenance = Role("MaintenanceRobot", warehouse)
system.add_role(transporter)
system.add_role(supervisor)
system.add_role(maintenance)

# Application
transport_app = Application("TransportApp")
pick_op = transport_app.add_operation("pick_object")
drop_op = transport_app.add_operation("drop_object")
move_op = transport_app.add_operation("move_to")
report_op = transport_app.add_operation("report_status")
system.add_application(transport_app)

# Permissions
transporter.grant_permission(pick_op)
transporter.grant_permission(drop_op)
transporter.grant_permission(move_op)
supervisor.grant_permission(report_op)
maintenance.grant_permission(move_op)  # can move to repair

# Create robots (users)
robots = []
for i in range(10):
    r = User(f"robot_{i}")
    r.attributes["position"] = [random.uniform(0, 100), random.uniform(0, 100)]
    r.attributes["battery"] = 100.0
    r.attributes["payload"] = None
    r.attributes["speed"] = random.uniform(1, 3)
    r.assign_role(warehouse, transporter)
    robots.append(r)
    system.add_user(r)

# Supervisor
sup = User("supervisor")
sup.attributes["position"] = [50, 50]
sup.assign_role(warehouse, supervisor)
system.add_user(sup)

# Maintenance robot
maint = User("maintainer")
maint.attributes["position"] = [10, 10]
maint.assign_role(warehouse, maintenance)
system.add_user(maint)

# Simple permission engine (no constraints needed for simulation)
class SimpleEngine(PermissionEngine):
    def decide(self, user, operation, zone, context=None):
        return True  # all allowed for simulation

engine = SimpleEngine(None)
storage = Storage("sqlite:///:memory:")

# Simulation with custom step logic
class TransportSim(SimulationEngine):
    def __init__(self, system, engine, storage):
        super().__init__(system, engine, storage)
        self.objects_in_loading = 20  # objects to transport
        self.objects_in_storage = 0
        self.task_queue = []  # list of (object_id, from_zone, to_zone)

    def step(self, current_time):
        # Move robots randomly, pick/drop objects
        for r in robots:
            # Simple random walk
            r.attributes["position"][0] += random.uniform(-1, 1) * r.attributes["speed"]
            r.attributes["position"][1] += random.uniform(-1, 1) * r.attributes["speed"]
            # Boundary constraints
            r.attributes["position"][0] = max(0, min(100, r.attributes["position"][0]))
            r.attributes["position"][1] = max(0, min(100, r.attributes["position"][1]))

            # Check if at loading zone (approx)
            if self._distance(r.attributes["position"], [10, 10]) < 5:
                if self.objects_in_loading > 0 and r.attributes["payload"] is None:
                    r.attributes["payload"] = f"obj_{self.objects_in_loading}"
                    self.objects_in_loading -= 1
                    self.logs.append({"timestamp": current_time.isoformat(),
                                      "robot": r.username, "action": "pick"})
            # Check if at storage zone
            if self._distance(r.attributes["position"], [90, 90]) < 5:
                if r.attributes["payload"] is not None:
                    self.objects_in_storage += 1
                    self.logs.append({"timestamp": current_time.isoformat(),
                                      "robot": r.username, "action": "drop",
                                      "object": r.attributes["payload"]})
                    r.attributes["payload"] = None

            # Battery drain
            r.attributes["battery"] -= 0.1
            if r.attributes["battery"] <= 0:
                self.logs.append({"timestamp": current_time.isoformat(),
                                  "robot": r.username, "action": "dead"})
                robots.remove(r)  # robot stops

    def _distance(self, p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

# Run simulation
sim = TransportSim(system, engine, storage)
sim.run(timedelta(minutes=10), step=timedelta(seconds=1))
print(f"Objects transported: {sim.objects_in_storage}")
print(f"Robots alive: {len(robots)}")