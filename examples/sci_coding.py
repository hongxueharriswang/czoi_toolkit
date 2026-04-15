"""
Smart City Traffic Management System using CZOI.
Simulates traffic control center with sensors, signals, and incident response.
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

class TrafficManagement(Zone):
    def __init__(self, name="City_Traffic"):
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
        center = Zone("TrafficControlCenter", parent=self)
        signals = Zone("SignalSystems", parent=self)
        sensors = Zone("Sensors", parent=self)
        vms = Zone("VariableMessageSigns", parent=self)
        incidents = Zone("IncidentManagement", parent=self)
        for z in [center, signals, sensors, vms, incidents]:
            self.system.add_zone(z)

    def _roles(self):
        self.op = Role("TrafficOperator", zone=self)
        self.commander = Role("IncidentCommander", zone=self)
        self.engineer = Role("TrafficEngineer", zone=self)
        for r in [self.op, self.commander, self.engineer]:
            self.system.add_role(r)

    def _apps(self):
        atms = Application("ATMS", owning_zone=self)
        atms.add_operation("view_cameras", "GET")
        atms.add_operation("adjust_timing", "POST")
        vms_app = Application("VMSControl", owning_zone=self)
        vms_app.add_operation("post_message", "POST")
        self.system.add_application(atms)
        self.system.add_application(vms_app)
        self.op.grant_permission(atms.operations[0])
        self.commander.grant_permission(atms.operations[1])
        self.commander.grant_permission(vms_app.operations[0])

    def _users(self):
        users = [
            ("alice", "TrafficOperator"),
            ("bob", "IncidentCommander"),
            ("charlie", "TrafficEngineer")
        ]
        for uname, rname in users:
            u = User(uname, f"{uname}@city.gov")
            role = next(r for r in self.system.roles if r.name == rname)
            u.assign_role(self, role, weight=1.0)
            self.system.add_user(u)

    def _constraints(self):
        c1 = Constraint("SignalCoordination", ConstraintType.IDENTITY,
                        {"zones": ["SignalSystems"]},
                        "all(signal.timing_plan == parent.timing_plan for signal in children)")
        c2 = Constraint("IncidentResponse", ConstraintType.TRIGGER,
                        {"event": "incident_detected"},
                        "incident.severity > 3",
                        priority=1)
        c3 = Constraint("EmergencyPreemption", ConstraintType.ACCESS,
                        {"operations": ["adjust_timing"]},
                        "context.emergency == True or user.role == 'IncidentCommander'")
        self.constraint_manager = ConstraintManager()
        for c in [c1, c2, c3]:
            self.constraint_manager.add(c)

    def _neural(self):
        self.congestion_predictor = AnomalyDetector(contamination=0.1)  # placeholder
        dummy = np.random.randn(100, 8)
        self.congestion_predictor.train(dummy)

    # Simulations
    def sim_normal_traffic(self, steps=100):
        class NormalTrafficSim(SimulationEngine):
            def step(self, current_time):
                # Periodic sensor readings, no incidents
                op = random.choice([o for o in self.system.operations if o.name == "view_cameras"])
                user = random.choice(list(self.system.users))
                zone = random.choice(list(self.system.zones))
                context = {"time": current_time}
                allowed = self.permission_engine.decide(user, op, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": user.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "allowed": allowed,
                    "congestion": random.uniform(0, 0.5)
                })
        sim = NormalTrafficSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_accident(self, steps=100):
        class AccidentSim(SimulationEngine):
            def step(self, current_time):
                # At a certain time, an accident occurs
                if current_time.second == 30:  # at 30 seconds in
                    # Incident commander takes action
                    commander = next(u for u in self.system.users if u.username == "bob")
                    op_adjust = next(o for o in self.system.operations if o.name == "adjust_timing")
                    op_vms = next(o for o in self.system.operations if o.name == "post_message")
                    zone = next(z for z in self.system.zones if z.name == "IncidentManagement")
                    context = {"emergency": True, "time": current_time}
                    allowed1 = self.permission_engine.decide(commander, op_adjust, zone, context)
                    allowed2 = self.permission_engine.decide(commander, op_vms, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": commander.username,
                        "operation": op_adjust.name,
                        "zone": zone.name,
                        "allowed": allowed1,
                        "incident": True
                    })
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": commander.username,
                        "operation": op_vms.name,
                        "zone": zone.name,
                        "allowed": allowed2,
                        "incident": True
                    })
                else:
                    # normal activity
                    op = random.choice([o for o in self.system.operations if o.name == "view_cameras"])
                    user = random.choice(list(self.system.users))
                    zone = random.choice(list(self.system.zones))
                    context = {"time": current_time}
                    allowed = self.permission_engine.decide(user, op, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": user.username,
                        "operation": op.name,
                        "zone": zone.name,
                        "allowed": allowed
                    })
        sim = AccidentSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_congestion_prediction(self, steps=100):
        class CongestionSim(SimulationEngine):
            def step(self, current_time):
                # Use neural predictor to forecast congestion and adjust signals
                # Dummy prediction
                features = np.random.randn(8)
                pred = self.neural_components[0].predict(features.reshape(1,-1))  # anomaly score as proxy
                # If predicted congestion high, engineer may adjust timing
                if pred > 0.8:
                    engineer = next(u for u in self.system.users if u.username == "charlie")
                    op = next(o for o in self.system.operations if o.name == "adjust_timing")
                    zone = next(z for z in self.system.zones if z.name == "SignalSystems")
                    context = {"emergency": False, "time": current_time, "prediction": float(pred)}
                    allowed = self.permission_engine.decide(engineer, op, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": engineer.username,
                        "operation": op.name,
                        "zone": zone.name,
                        "allowed": allowed,
                        "prediction": float(pred),
                        "action": "adjust"
                    })
                else:
                    # log normal
                    op = random.choice([o for o in self.system.operations if o.name == "view_cameras"])
                    user = random.choice(list(self.system.users))
                    zone = random.choice(list(self.system.zones))
                    context = {"time": current_time}
                    allowed = self.permission_engine.decide(user, op, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": user.username,
                        "operation": op.name,
                        "zone": zone.name,
                        "allowed": allowed,
                        "prediction": float(pred)
                    })
        sim = CongestionSim(self.system, self.permission_engine, storage=None)
        sim.neural_components = [self.congestion_predictor]
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

if __name__ == "__main__":
    traffic = TrafficManagement()
    print("Normal traffic simulation...")
    print(traffic.sim_normal_traffic(50))
    print("Accident simulation...")
    print(traffic.sim_accident(50))
    print("Congestion prediction simulation...")
    print(traffic.sim_congestion_prediction(50))