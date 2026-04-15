# system5_drone_swarm.py
import random
from datetime import timedelta
from czoi.core import System, Zone, Role, User, Application

system = System()
area = Zone("OperationArea")
base = Zone("BaseStation", parent=area)
# Create grid sectors
sectors = {}
for i in range(10):
    for j in range(10):
        sec = Zone(f"Sector_{i}_{j}", parent=area)
        sectors[(i,j)] = sec
        system.add_zone(sec)
system.add_zone(area)
system.add_zone(base)

survey = Role("SurveyDrone", area)
relay = Role("RelayDrone", area)
operator = Role("BaseOperator", area)
system.add_role(survey)
system.add_role(relay)
system.add_role(operator)

app = Application("SurveillanceApp")
fly_op = app.add_operation("fly_to")
scan_op = app.add_operation("scan")
transmit_op = app.add_operation("transmit")
return_op = app.add_operation("return_to_base")
system.add_application(app)

survey.grant_permission(fly_op)
survey.grant_permission(scan_op)
survey.grant_permission(transmit_op)
relay.grant_permission(fly_op)
relay.grant_permission(transmit_op)
operator.grant_permission(return_op)  # can order return

# Drones
drones = []
for i in range(5):
    d = User(f"survey_{i}")
    d.attributes["position"] = (0,0)  # start at base
    d.attributes["battery"] = 100
    d.attributes["coverage"] = set()
    d.assign_role(area, survey)
    drones.append(d)
    system.add_user(d)

for i in range(2):
    d = User(f"relay_{i}")
    d.attributes["position"] = (0,0)
    d.attributes["battery"] = 100
    d.assign_role(area, relay)
    drones.append(d)
    system.add_user(d)

op = User("operator")
op.assign_role(area, operator)
system.add_user(op)

class DroneSim(SimulationEngine):
    def __init__(self, system, engine, storage):
        super().__init__(system, engine, storage)
        self.covered_cells = set()

    def step(self, current_time):
        for d in drones:
            if "survey" in d.username:
                # move to random sector
                cell = (random.randint(0,9), random.randint(0,9))
                d.attributes["position"] = cell
                # scan
                if cell not in d.attributes["coverage"]:
                    d.attributes["coverage"].add(cell)
                    self.covered_cells.add(cell)
                    self.logs.append({"timestamp": current_time.isoformat(),
                                      "drone": d.username, "action": "scan", "cell": cell})
                d.attributes["battery"] -= 1
            elif "relay" in d.username:
                # relay stays near base to extend comms
                d.attributes["position"] = (0,0)
                d.attributes["battery"] -= 0.5
            # return if low
            if d.attributes["battery"] < 20:
                d.attributes["position"] = (0,0)
                d.attributes["battery"] += 5

sim = DroneSim(system, None, None)
sim.run(timedelta(minutes=60), step=timedelta(minutes=1))
print(f"Unique cells covered: {len(sim.covered_cells)} / 100")