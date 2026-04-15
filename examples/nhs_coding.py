"""
National Healthcare System using CZOI.
Simulates a regional health authority with teaching hospitals, clinics, and public health units.
"""
import random
import datetime
import numpy as np
from uuid import uuid4
from czoi.core import Zone, Role, User, Application, Operation, System, GammaMapping
from czoi.permission.engine import SimpleEngine
from czoi.constraint import Constraint, ConstraintType, ConstraintManager
from czoi.neural import AnomalyDetector
from czoi.daemon import SecurityDaemon, ComplianceDaemon
from czoi.simulation import SimulationEngine
from czoi.embedding import EmbeddingService, InMemoryVectorStore

class NationalHealthSystem(Zone):
    """Root zone for the national healthcare system."""
    def __init__(self, name="NHS_Root"):
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
        self._create_daemons()
        self.permission_engine = SimpleEngine(self.system)
        self.embedding_service = EmbeddingService(InMemoryVectorStore())

    def _build_hierarchy(self):
        # Level 2: Regional Health Authorities (5 regions)
        regions = ["North", "South", "East", "West", "Central"]
        self.regions = {}
        for reg in regions:
            region = Zone(f"{reg}_Region", parent=self)
            self.system.add_zone(region)
            self.regions[reg] = region
            # Level 3: Teaching Hospitals (3 per region)
            for i in range(3):
                hosp = Zone(f"{reg}_TeachingHospital_{i+1}", parent=region)
                self.system.add_zone(hosp)
            # Level 3: Primary Care Networks (2 per region)
            for i in range(2):
                pcn = Zone(f"{reg}_PCN_{i+1}", parent=region)
                self.system.add_zone(pcn)
        # Level 2: National Specialized Agencies
        agencies = ["BloodService", "DiseaseControl", "HealthRecords"]
        for ag in agencies:
            agency = Zone(f"National_{ag}", parent=self)
            self.system.add_zone(agency)

    def _create_roles(self):
        self.attending = Role("AttendingPhysician", zone=self)
        self.resident = Role("ResidentPhysician", zone=self)
        self.nurse = Role("RegisteredNurse", zone=self)
        self.pharmacist = Role("Pharmacist", zone=self)
        self.admin = Role("HospitalAdministrator", zone=self)
        self.quality = Role("QualityOfficer", zone=self)
        for r in [self.attending, self.resident, self.nurse, self.pharmacist, self.admin, self.quality]:
            self.system.add_role(r)

    def _create_applications(self):
        ehr = Application("ElectronicHealthRecord", owning_zone=self)
        ehr.add_operation("view_patient", "GET")
        ehr.add_operation("edit_patient", "POST")
        ehr.add_operation("order_test", "POST")
        self.system.add_application(ehr)

        cpoe = Application("CPOE", owning_zone=self)
        cpoe.add_operation("prescribe_med", "POST")
        self.system.add_application(cpoe)

        # Grant base permissions
        self.attending.grant_permission(ehr.operations[0])  # view
        self.attending.grant_permission(ehr.operations[2])  # order_test
        self.attending.grant_permission(cpoe.operations[0]) # prescribe
        self.nurse.grant_permission(ehr.operations[0])      # view
        self.pharmacist.grant_permission(ehr.operations[0]) # view
        self.admin.grant_permission(ehr.operations[1])      # edit (admin only)

    def _create_users(self):
        alice = User("alice", "alice@nhs.uk")
        alice.assign_role(self, self.attending, weight=1.0)
        bob = User("bob", "bob@nhs.uk")
        bob.assign_role(self, self.nurse, weight=1.0)
        charlie = User("charlie", "charlie@nhs.uk")
        charlie.assign_role(self, self.admin, weight=1.0)
        diana = User("diana", "diana@nhs.uk")
        diana.assign_role(self, self.pharmacist, weight=1.0)
        for u in [alice, bob, charlie, diana]:
            self.system.add_user(u)

    def _create_constraints(self):
        c1 = Constraint("ZoneContainment", ConstraintType.IDENTITY,
                        {"zones": "all"}, "parent.children contains child")
        c2 = Constraint("CriticalLabAlert", ConstraintType.TRIGGER,
                        {"operation": "order_test"}, "lab_result.critical == True")
        c3 = Constraint("OrderDispenseSoD", ConstraintType.ACCESS,
                        {"roles": ["AttendingPhysician", "Pharmacist"]},
                        "user != last_dispenser")
        self.constraint_manager = ConstraintManager()
        for c in [c1, c2, c3]:
            self.constraint_manager.add(c)

    def _create_gamma_mappings(self):
        for region in self.regions.values():
            teaching_hospitals = [z for z in region.children if "TeachingHospital" in z.name]
            pcns = [z for z in region.children if "PCN" in z.name]
            for hosp in teaching_hospitals:
                for pcn in pcns:
                    gm = GammaMapping(hosp, self.attending, pcn, self.attending,
                                      weight=0.8, priority=1)
                    self.system.add_gamma_mapping(gm)

    def _create_neural_components(self):
        self.anomaly_detector = AnomalyDetector(contamination=0.05)
        # In real life, train on historical access logs
        dummy_data = np.random.randn(100, 10)
        self.anomaly_detector.train(dummy_data)

    def _create_daemons(self):
        self.security_daemon = SecurityDaemon(storage=None, permission_engine=self.permission_engine,
                                              threshold=0.9, interval=2.0)
        self.compliance_daemon = ComplianceDaemon(storage=None, interval=10.0)

    # ---------- Simulations ----------
    def sim_normal_operations(self, steps=100):
        """Simulate routine hospital activities: patients arrive, staff work."""
        class NHSNormalSim(SimulationEngine):
            def step(self, current_time):
                # Random access attempts by active users
                users = list(self.system.users)
                ops = list(self.system.operations)
                if users and ops:
                    u = random.choice(users)
                    op = random.choice(ops)
                    zone = random.choice(list(self.system.zones))
                    context = {"time": current_time, "lab_result": {"critical": False}}
                    allowed = self.permission_engine.decide(u, op, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": u.username,
                        "operation": op.name,
                        "zone": zone.name,
                        "allowed": allowed
                    })
        sim = NHSNormalSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_flu_surge(self, steps=100):
        """Simulate a flu season surge: higher patient volume, role extensions."""
        class NHSSurgeSim(SimulationEngine):
            def step(self, current_time):
                # Increase event frequency and introduce temporary role assignments
                # For simplicity, just log more accesses
                for _ in range(random.randint(2, 5)):  # surge multiplier
                    users = list(self.system.users)
                    op = random.choice(list(self.system.operations))
                    zone = random.choice(list(self.system.zones))
                    u = random.choice(users)
                    context = {"time": current_time, "lab_result": {"critical": False}}
                    allowed = self.permission_engine.decide(u, op, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": u.username,
                        "operation": op.name,
                        "zone": zone.name,
                        "allowed": allowed,
                        "surge": True
                    })
        sim = NHSSurgeSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_breach_detection(self, steps=100):
        """Simulate an insider threat and monitor daemon response."""
        class NHSBreachSim(SimulationEngine):
            def step(self, current_time):
                # Introduce anomalous behavior (e.g., accessing many patients at odd hours)
                user_bob = next(u for u in self.system.users if u.username == "bob")
                # At certain times, bob tries to view many patients rapidly
                if random.random() < 0.1:  # 10% chance of anomalous burst
                    for _ in range(20):
                        op = next(o for o in self.system.operations if o.name == "view_patient")
                        zone = random.choice(list(self.system.zones))
                        context = {"time": current_time}
                        allowed = self.permission_engine.decide(user_bob, op, zone, context)
                        self.logs.append({
                            "time": current_time.isoformat(),
                            "user": user_bob.username,
                            "operation": op.name,
                            "zone": zone.name,
                            "allowed": allowed,
                            "anomalous": True
                        })
                else:
                    # normal activity
                    u = random.choice(list(self.system.users))
                    op = random.choice(list(self.system.operations))
                    zone = random.choice(list(self.system.zones))
                    context = {"time": current_time}
                    allowed = self.permission_engine.decide(u, op, zone, context)
                    self.logs.append({
                        "time": current_time.isoformat(),
                        "user": u.username,
                        "operation": op.name,
                        "zone": zone.name,
                        "allowed": allowed
                    })
        sim = NHSBreachSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

if __name__ == "__main__":
    nhs = NationalHealthSystem()
    print("Running normal operations simulation...")
    results = nhs.sim_normal_operations(50)
    print("Normal ops summary:", results)
    print("Running flu surge simulation...")
    results = nhs.sim_flu_surge(50)
    print("Flu surge summary:", results)
    print("Running breach detection simulation...")
    results = nhs.sim_breach_detection(50)
    print("Breach detection summary:", results)