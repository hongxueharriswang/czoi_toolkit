# system4_assembly_line.py
import random
from datetime import timedelta
from czoi.core import System, Zone, Role, User, Application

system = System()
cell = Zone("AssemblyCell")
ws1 = Zone("Workstation1", parent=cell)
ws2 = Zone("Workstation2", parent=cell)
buffer = Zone("BufferZone", parent=cell)
for z in [cell, ws1, ws2, buffer]:
    system.add_zone(z)

picker = Role("PickerArm", cell)
welder = Role("WelderArm", cell)
inspector = Role("InspectorArm", cell)
supervisor = Role("Supervisor", cell)
system.add_role(picker)
system.add_role(welder)
system.add_role(inspector)
system.add_role(supervisor)

app = Application("AssemblyApp")
pick_op = app.add_operation("pick")
place_op = app.add_operation("place")
weld_op = app.add_operation("weld")
inspect_op = app.add_operation("inspect")
move_op = app.add_operation("move")
system.add_application(app)

for r in [picker, welder, inspector]:
    r.grant_permission(move_op)
picker.grant_permission(pick_op)
picker.grant_permission(place_op)
welder.grant_permission(weld_op)
inspector.grant_permission(inspect_op)

# Create arms
arms = []
for i in range(2):
    p = User(f"picker_{i}")
    p.attributes["position"] = (0,0)  # simplified
    p.attributes["task_queue"] = []
    p.attributes["error_rate"] = 0.01
    p.assign_role(ws1, picker)
    arms.append(p)
    system.add_user(p)

for i in range(2):
    w = User(f"welder_{i}")
    w.attributes["position"] = (10,0)
    w.attributes["error_rate"] = 0.02
    w.assign_role(ws2, welder)
    arms.append(w)
    system.add_user(w)

i = User("inspector")
i.attributes["position"] = (5,5)
i.assign_role(buffer, inspector)
arms.append(i)
system.add_user(i)

sup = User("supervisor")
sup.assign_role(cell, supervisor)
system.add_user(sup)

class AssemblySim(SimulationEngine):
    def __init__(self, system, engine, storage):
        super().__init__(system, engine, storage)
        self.products_made = 0
        self.defects = 0

    def step(self, current_time):
        # Simplified pipeline: picker picks from buffer, moves to ws1, then welder welds, inspector inspects
        # Not realistic but demonstrates flow
        for arm in arms:
            if "picker" in arm.username and arm.attributes["task_queue"] == []:
                # pick a part
                arm.attributes["task_queue"].append("pick")
                self.logs.append({"timestamp": current_time.isoformat(),
                                  "arm": arm.username, "action": "pick"})
            elif "welder" in arm.username and random.random() < 0.3:
                arm.attributes["task_queue"].append("weld")
                self.logs.append({"timestamp": current_time.isoformat(),
                                  "arm": arm.username, "action": "weld"})
            elif "inspector" in arm.username and random.random() < 0.2:
                # inspect
                if random.random() < 0.1:  # 10% defect
                    self.defects += 1
                    self.logs.append({"timestamp": current_time.isoformat(),
                                      "arm": arm.username, "action": "defect"})
                else:
                    self.products_made += 1
                    self.logs.append({"timestamp": current_time.isoformat(),
                                      "arm": arm.username, "action": "pass"})
                arm.attributes["task_queue"] = []

sim = AssemblySim(system, None, None)
sim.run(timedelta(minutes=30), step=timedelta(seconds=5))
print(f"Products made: {sim.products_made}, Defects: {sim.defects}")