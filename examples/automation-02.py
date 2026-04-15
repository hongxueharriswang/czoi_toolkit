# system2_warehouse_agv.py
import random
from datetime import timedelta
from czoi.core import System, Zone, Role, User, Application
from czoi.simulation import SimulationEngine

system = System()
warehouse = Zone("Warehouse")
aisle1 = Zone("Aisle1", parent=warehouse)
aisle2 = Zone("Aisle2", parent=warehouse)
charging = Zone("ChargingStation", parent=warehouse)
delivery = Zone("DeliveryBay", parent=warehouse)
for z in [warehouse, aisle1, aisle2, charging, delivery]:
    system.add_zone(z)
    z.capacity = 5  # max AGVs per zone

agv_role = Role("AGV", warehouse)
manager_role = Role("WarehouseManager", warehouse)
system.add_role(agv_role)
system.add_role(manager_role)

app = Application("WarehouseApp")
move_op = app.add_operation("move")
charge_op = app.add_operation("charge")
load_op = app.add_operation("load_pallet")
unload_op = app.add_operation("unload_pallet")
system.add_application(app)

agv_role.grant_permission(move_op)
agv_role.grant_permission(charge_op)
agv_role.grant_permission(load_op)
agv_role.grant_permission(unload_op)

# Create AGVs
agvs = []
for i in range(8):
    agv = User(f"AGV_{i}")
    agv.attributes["battery"] = 100.0
    agv.attributes["position"] = ("Aisle1", random.uniform(0, 10))
    agv.attributes["task"] = None
    agv.assign_role(warehouse, agv_role)
    agvs.append(agv)
    system.add_user(agv)

manager = User("manager")
manager.assign_role(warehouse, manager_role)
system.add_user(manager)

class WarehouseSim(SimulationEngine):
    def __init__(self, system, engine, storage):
        super().__init__(system, engine, storage)
        self.pallets_in = 50
        self.pallets_out = 0

    def step(self, current_time):
        for agv in agvs:
            # Simple logic: if no task, go to delivery to pick up; if has task, go to charging? Not realistic.
            # Simulate movement: position changes
            if agv.attributes["task"] is None:
                # head to delivery
                agv.attributes["position"] = ("DeliveryBay", 0)
                if agv.attributes["position"][0] == "DeliveryBay" and self.pallets_in > 0:
                    agv.attributes["task"] = f"pallet_{self.pallets_in}"
                    self.pallets_in -= 1
                    self.logs.append({"timestamp": current_time.isoformat(),
                                      "agv": agv.username, "action": "load"})
            else:
                # head to charging? no, head to some dropoff (simplified)
                agv.attributes["position"] = ("Aisle1", random.uniform(0,10))
                # randomly drop
                if random.random() < 0.3:
                    self.pallets_out += 1
                    self.logs.append({"timestamp": current_time.isoformat(),
                                      "agv": agv.username, "action": "unload",
                                      "pallet": agv.attributes["task"]})
                    agv.attributes["task"] = None
            # battery drain
            agv.attributes["battery"] -= 0.5
            if agv.attributes["battery"] < 20:
                agv.attributes["position"] = ("ChargingStation", 0)
                agv.attributes["battery"] += 2  # charge

sim = WarehouseSim(system, None, None)
sim.run(timedelta(minutes=30), step=timedelta(seconds=10))
print(f"Pallets moved: {sim.pallets_out}")