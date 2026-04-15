"""
Global Financial Trading System using CZOI.
Simulates an equities trading desk with risk management and compliance.
Under unified COH ZRB Fromalization
"""
import random
import datetime
import numpy as np
from czoi.core import Zone, Role, User, Application, System, GammaMapping
from czoi.permission.engine import SimpleEngine
from czoi.constraint import Constraint, ConstraintType, ConstraintManager
from czoi.neural import AnomalyDetector
from czoi.daemon import SecurityDaemon, ComplianceDaemon
from czoi.simulation import SimulationEngine

class EquitiesTradingDesk(Zone):
    def __init__(self, name="Global_Equities"):
        super().__init__(name)
        self.system = System()
        self.system.add_zone(self)
        self._build_hierarchy()
        self._create_roles()
        self._create_applications()
        self._create_users()
        self._create_constraints()
        self._create_gamma_mappings()
        self._create_neural_components()
        self.permission_engine = SimpleEngine(self.system)

    def _build_hierarchy(self):
        cash = Zone("CashEquities", parent=self)
        prog = Zone("ProgramTrading", parent=self)
        block = Zone("BlockTrading", parent=self)
        sales = Zone("SalesTrading", parent=self)
        research = Zone("Research", parent=self)
        market = Zone("MarketMaking", parent=self)
        for z in [cash, prog, block, sales, research, market]:
            self.system.add_zone(z)

    def _create_roles(self):
        self.trader = Role("Trader", zone=self)
        self.sales = Role("SalesTrader", zone=self)
        self.risk = Role("RiskManager", zone=self)
        self.compliance = Role("ComplianceOfficer", zone=self)
        for r in [self.trader, self.sales, self.risk, self.compliance]:
            self.system.add_role(r)

    def _create_applications(self):
        oms = Application("OMS", owning_zone=self)
        oms.add_operation("enter_order", "POST")
        oms.add_operation("cancel_order", "DELETE")
        risk_sys = Application("RiskSystem", owning_zone=self)
        risk_sys.add_operation("check_limit", "GET")
        self.system.add_application(oms)
        self.system.add_application(risk_sys)
        self.trader.grant_permission(oms.operations[0])
        self.trader.grant_permission(oms.operations[1])
        self.risk.grant_permission(risk_sys.operations[0])

    def _create_users(self):
        users = [
            ("trader1", "Trader"),
            ("trader2", "Trader"),
            ("sales1", "SalesTrader"),
            ("risk1", "RiskManager"),
            ("comp1", "ComplianceOfficer")
        ]
        for uname, rname in users:
            u = User(uname, f"{uname}@bank.com")
            role = next(r for r in self.system.roles if r.name == rname)
            u.assign_role(self, role, weight=1.0)
            self.system.add_user(u)

    def _create_constraints(self):
        # Position limit constraint (simplified)
        c1 = Constraint("PositionLimit", ConstraintType.IDENTITY,
                        {"zones": "all"}, "position <= position_limit")
        # Trigger: limit breach
        c2 = Constraint("LimitBreach", ConstraintType.TRIGGER,
                        {"event": "trade_attempt"}, "position > 0.9 * limit",
                        priority=1)
        # Access: traders cannot also be risk managers
        c3 = Constraint("SoD_TraderRisk", ConstraintType.ACCESS,
                        {"roles": ["Trader", "RiskManager"]},
                        "user.role != 'RiskManager' when trading")
        self.constraint_manager = ConstraintManager()
        for c in [c1, c2, c3]:
            self.constraint_manager.add(c)

    def _create_gamma_mappings(self):
        # Example: a trader in CashEquities can also trade in ProgramTrading with lower weight
        cash_zone = next(z for z in self.system.zones if z.name == "CashEquities")
        prog_zone = next(z for z in self.system.zones if z.name == "ProgramTrading")
        gm = GammaMapping(cash_zone, self.trader, prog_zone, self.trader,
                          weight=0.5, priority=2)
        self.system.add_gamma_mapping(gm)

    def _create_neural_components(self):
        self.anomaly_detector = AnomalyDetector(contamination=0.1)
        # Train on dummy data
        dummy = np.random.randn(200, 5)
        self.anomaly_detector.train(dummy)

    # Simulations
    def sim_normal_trading(self, steps=100):
        class TradingSim(SimulationEngine):
            def step(self, current_time):
                # Normal trading activity
                trader = random.choice([u for u in self.system.users if any(r.name=="Trader" for r in u.zone_role_assignments[self.root_zone.id])])
                op = random.choice([o for o in self.system.operations if o.name == "enter_order"])
                zone = random.choice(list(self.system.zones))
                # Simulate a position value
                position = random.uniform(0, 100)
                context = {"position": position, "limit": 100}
                allowed = self.permission_engine.decide(trader, op, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": trader.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "position": position,
                    "allowed": allowed
                })
        sim = TradingSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_market_crash(self, steps=100):
        class CrashSim(SimulationEngine):
            def step(self, current_time):
                # During crash, volatility high; many trades and limit breaches
                trader = random.choice([u for u in self.system.users if any(r.name=="Trader" for r in u.zone_role_assignments[self.root_zone.id])])
                op = random.choice([o for o in self.system.operations if o.name == "enter_order"])
                zone = random.choice(list(self.system.zones))
                # Simulate crash: positions near or over limit
                position = random.uniform(90, 120)
                context = {"position": position, "limit": 100}
                allowed = self.permission_engine.decide(trader, op, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": trader.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "position": position,
                    "allowed": allowed,
                    "crash": True
                })
                # Also log risk manager actions
                risk = random.choice([u for u in self.system.users if any(r.name=="RiskManager" for r in u.zone_role_assignments[self.root_zone.id])])
                op_risk = random.choice([o for o in self.system.operations if o.name == "check_limit"])
                allowed_risk = self.permission_engine.decide(risk, op_risk, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": risk.username,
                    "operation": op_risk.name,
                    "zone": zone.name,
                    "allowed": allowed_risk,
                    "crash": True
                })
        sim = CrashSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_insider_detection(self, steps=100):
        class InsiderSim(SimulationEngine):
            def step(self, current_time):
                # One trader occasionally engages in suspicious patterns
                trader = next(u for u in self.system.users if u.username == "trader1")
                op = random.choice([o for o in self.system.operations if o.name == "enter_order"])
                zone = random.choice(list(self.system.zones))
                # Generate features for anomaly detector
                features = np.random.randn(5)  # dummy features
                anomaly_score = self.neural_components[0].predict(features.reshape(1,-1))
                if anomaly_score > 0.9:
                    action = "block"
                else:
                    action = "allow"
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": trader.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "anomaly_score": float(anomaly_score),
                    "action": action
                })
        # Attach neural component to sim
        sim = InsiderSim(self.system, self.permission_engine, storage=None)
        sim.neural_components = [self.anomaly_detector]
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

if __name__ == "__main__":
    trading = EquitiesTradingDesk()
    print("Normal trading simulation...")
    print(trading.sim_normal_trading(50))
    print("Market crash simulation...")
    print(trading.sim_market_crash(50))
    print("Insider detection simulation...")
    print(trading.sim_insider_detection(50))