"""
Supply Chain Distribution Center using CZOI.
Simulates a warehouse with receiving, picking, packing, and inventory control.
"""
import random
import datetime
import numpy as np
from czoi.core import Zone, Role, User, Application, System, GammaMapping
from czoi.permission.engine import SimpleEngine
from czoi.constraint import Constraint, ConstraintType, ConstraintManager
from czoi.neural import AnomalyDetector
from czoi.daemon import SecurityDaemon
from czoi.simulation import SimulationEngine

class DistributionCenter(Zone):
    def __init__(self, name="Main_DC"):
        super().__init__(name)
        self.system = System()
        self.system.add_zone(self)
        self._build()
        self._roles()
        self._apps()
        self._users()
        self._constraints()
        self._neural()
        self.permission_engine = SimpleEngine(self.system)

    def _build(self):
        receiving = Zone("Receiving", parent=self)
        storage = Zone("Storage", parent=self)
        picking = Zone("Picking", parent=self)
        packing = Zone("Packing", parent=self)
        shipping = Zone("Shipping", parent=self)
        returns = Zone("Returns", parent=self)
        admin = Zone("Administrative", parent=self)
        for z in [receiving, storage, picking, packing, shipping, returns, admin]:
            self.system.add_zone(z)

    def _roles(self):
        self.manager = Role("WarehouseManager", zone=self)
        self.supervisor = Role("Supervisor", zone=self)
        self.picker = Role("Picker", zone=self)
        self.receiver = Role("Receiver", zone=self)
        self.inventory = Role("InventoryController", zone=self)
        for r in [self.manager, self.supervisor, self.picker, self.receiver, self.inventory]:
            self.system.add_role(r)
        # Hierarchy
        self.manager.add_senior(self.supervisor)
        self.supervisor.add_senior(self.picker)

    def _apps(self):
        wms = Application("WMS", owning_zone=self)
        wms.add_operation("receive_shipment", "POST")
        wms.add_operation("pick_order", "POST")
        wms.add_operation("cycle_count", "POST")
        lms = Application("LMS", owning_zone=self)
        lms.add_operation("track_productivity", "GET")
        self.system.add_application(wms)
        self.system.add_application(lms)
        self.receiver.grant_permission(wms.operations[0])
        self.picker.grant_permission(wms.operations[1])
        self.inventory.grant_permission(wms.operations[2])
        self.manager.grant_permission(lms.operations[0])

    def _users(self):
        users = [
            ("mgr", "WarehouseManager"),
            ("sup", "Supervisor"),
            ("pick1", "Picker"),
            ("pick2", "Picker"),
            ("rec1", "Receiver"),
            ("inv1", "InventoryController")
        ]
        for uname, rname in users:
            u = User(uname, f"{uname@dc.com}")
            role = next(r for r in self.system.roles if r.name == rname)
            u.assign_role(self, role, weight=1.0)
            self.system.add_user(u)

    def _constraints(self):
        c1 = Constraint("InventoryAccuracy", ConstraintType.IDENTITY,
                        {"zones": ["Storage"]}, "abs(system_qty - physical_qty) <= tolerance")
        c2 = Constraint("LowStockReorder", ConstraintType.TRIGGER,
                        {"event": "cycle_count"}, "quantity < reorder_point and not already_ordered")
        c3 = Constraint("SafetyCertification", ConstraintType.ACCESS,
                        {"operations": ["receive_shipment"], "roles": ["Receiver"]},
                        "user.certified == True")
        self.constraint_manager = ConstraintManager()
        for c in [c1, c2, c3]:
            self.constraint_manager.add(c)

    def _neural(self):
        self.demand_forecaster = AnomalyDetector(contamination=0.1)  # placeholder
        dummy = np.random.randn(100, 4)
        self.demand_forecaster.train(dummy)

    # Simulations
    def sim_normal_fulfillment(self, steps=100):
        class NormalSim(SimulationEngine):
            def step(self, current_time):
                # Picker picks orders
                picker = random.choice([u for u in self.system.users if any(r.name=="Picker" for r in u.zone_role_assignments[self.root_zone.id])])
                op = next(o for o in self.system.operations if o.name == "pick_order")
                zone = next(z for z in self.system.zones if z.name == "Picking")
                context = {"time": current_time}
                allowed = self.permission_engine.decide(picker, op, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": picker.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "allowed": allowed
                })
        sim = NormalSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_peak_season(self, steps=100):
        class PeakSim(SimulationEngine):
            def step(self, current_time):
                # Higher order volume, supervisor may need to help picking
                for _ in range(random.randint(2,4)):
                    picker = random.choice([u for u in self.system.users if any(r.name=="Picker" for r in u.zone_role_assignments[self.root_zone.id])])
                    op = next(o for o in self.system.operations if o.name == "pick_order")
                    zone = next(z for z in self.system.zones if z.name == "Picking")
                    context = {"time": current_time, "peak": True}
                    allowed = self.permission_engine.decide(picker, op, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": picker.username,
                        "operation": op.name,
                        "zone": zone.name,
                        "allowed": allowed,
                        "peak": True
                    })
        sim = PeakSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_inventory_discrepancy(self, steps=100):
        class InvSim(SimulationEngine):
            def step(self, current_time):
                # Inventory controller performs cycle counts; occasional discrepancies
                inv = next(u for u in self.system.users if u.username == "inv1")
                op = next(o for o in self.system.operations if o.name == "cycle_count")
                zone = next(z for z in self.system.zones if z.name == "Storage")
                # Simulate count result
                system_qty = random.randint(50, 100)
                physical_qty = system_qty + random.randint(-5, 5)
                discrepancy = abs(system_qty - physical_qty) > 2
                context = {"system_qty": system_qty, "physical_qty": physical_qty, "tolerance": 2}
                allowed = self.permission_engine.decide(inv, op, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": inv.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "allowed": allowed,
                    "system_qty": system_qty,
                    "physical_qty": physical_qty,
                    "discrepancy": discrepancy
                })
                if discrepancy:
                    # Trigger low stock reorder constraint (simulated)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "event": "LowStockReorder",
                        "item": "SKU123",
                        "action": "generate_po"
                    })
        sim = InvSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

if __name__ == "__main__":
    dc = DistributionCenter()
    print("Normal fulfillment simulation...")
    print(dc.sim_normal_fulfillment(50))
    print("Peak season simulation...")
    print(dc.sim_peak_season(50))
    print("Inventory discrepancy simulation...")
    print(dc.sim_inventory_discrepancy(50))