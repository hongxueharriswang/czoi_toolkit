"""
University Academic Management System using CZOI.
Simulates a College of Engineering with courses, students, faculty, and advising.
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

class CollegeOfEngineering(Zone):
    def __init__(self, name="Engineering_College"):
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
        cs = Zone("ComputerScience", parent=self)
        me = Zone("MechanicalEngineering", parent=self)
        ee = Zone("ElectricalEngineering", parent=self)
        ai_lab = Zone("AI_Lab", parent=self)
        robotics = Zone("RoboticsLab", parent=self)
        advising = Zone("Advising", parent=self)
        for z in [cs, me, ee, ai_lab, robotics, advising]:
            self.system.add_zone(z)

    def _roles(self):
        self.prof = Role("Professor", zone=self)
        self.student = Role("Student", zone=self)
        self.advisor = Role("AcademicAdvisor", zone=self)
        self.dean = Role("Dean", zone=self)
        for r in [self.prof, self.student, self.advisor, self.dean]:
            self.system.add_role(r)
        # Hierarchy
        self.dean.add_senior(self.prof)
        self.prof.add_senior(self.advisor)

    def _apps(self):
        lms = Application("LMS", owning_zone=self)
        lms.add_operation("view_grades", "GET")
        lms.add_operation("submit_grade", "POST")
        sis = Application("SIS", owning_zone=self)
        sis.add_operation("register", "POST")
        sis.add_operation("view_transcript", "GET")
        self.system.add_application(lms)
        self.system.add_application(sis)
        self.prof.grant_permission(lms.operations[1])  # submit_grade
        self.student.grant_permission(lms.operations[0])  # view_grades
        self.student.grant_permission(sis.operations[1])  # view_transcript
        self.advisor.grant_permission(sis.operations[0])  # register

    def _users(self):
        users = [
            ("smith", "Professor"),
            ("doe", "Student"),
            ("brown", "AcademicAdvisor"),
            ("white", "Dean")
        ]
        for uname, rname in users:
            u = User(uname, f"{uname}@univ.edu")
            role = next(r for r in self.system.roles if r.name == rname)
            u.assign_role(self, role, weight=1.0)
            self.system.add_user(u)
        # Add more students
        for i in range(10):
            u = User(f"student{i}", f"student{i}@univ.edu")
            u.assign_role(self, self.student, weight=1.0)
            self.system.add_user(u)

    def _constraints(self):
        c1 = Constraint("FERPA", ConstraintType.IDENTITY,
                        {"operations": ["view_grades", "view_transcript"]},
                        "user == student or user.role in ['Professor', 'Advisor']")
        c2 = Constraint("Prerequisites", ConstraintType.TRIGGER,
                        {"event": "registration"}, "student.has_prerequisite(course)")
        c3 = Constraint("GradeEntrySoD", ConstraintType.ACCESS,
                        {"roles": ["Professor"], "operations": ["submit_grade"]},
                        "user != student and user not in course.students")
        self.constraint_manager = ConstraintManager()
        for c in [c1, c2, c3]:
            self.constraint_manager.add(c)

    def _neural(self):
        self.success_predictor = AnomalyDetector(contamination=0.1)  # placeholder
        dummy = np.random.randn(200, 5)
        self.success_predictor.train(dummy)

    # Simulations
    def sim_registration(self, steps=100):
        class RegSim(SimulationEngine):
            def step(self, current_time):
                # Students try to register
                student = random.choice([u for u in self.system.users if any(r.name=="Student" for r in u.zone_role_assignments[self.root_zone.id])])
                op = next(o for o in self.system.operations if o.name == "register")
                zone = random.choice([z for z in self.system.zones if z.name in ["ComputerScience","MechanicalEngineering","ElectricalEngineering"]])
                # Simulate prerequisite check
                has_preq = random.choice([True, False])
                context = {"student": student.username, "course": "CS101", "has_prerequisite": has_preq}
                allowed = self.permission_engine.decide(student, op, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": student.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "allowed": allowed,
                    "has_prerequisite": has_preq
                })
        sim = RegSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_grading(self, steps=100):
        class GradeSim(SimulationEngine):
            def step(self, current_time):
                # Professor submits grades
                prof = next(u for u in self.system.users if u.username == "smith")
                op = next(o for o in self.system.operations if o.name == "submit_grade")
                zone = random.choice([z for z in self.system.zones if z.name in ["ComputerScience","MechanicalEngineering","ElectricalEngineering"]])
                context = {"course": "CS101", "student": "doe"}
                allowed = self.permission_engine.decide(prof, op, zone, context)
                self.logs.append({
                    "time": current_time.isoformat(),
                    "user": prof.username,
                    "operation": op.name,
                    "zone": zone.name,
                    "allowed": allowed
                })
        sim = GradeSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

    def sim_probation_monitoring(self, steps=100):
        class ProbationSim(SimulationEngine):
            def step(self, current_time):
                # Advisor checks at-risk students
                advisor = next(u for u in self.system.users if u.username == "brown")
                # Get all students
                students = [u for u in self.system.users if any(r.name=="Student" for r in u.zone_role_assignments[self.root_zone.id])]
                for student in students:
                    # Simulate GPA
                    gpa = random.uniform(1.5, 4.0)
                    if gpa < 2.0:
                        # Trigger probation action
                        op_view = next(o for o in self.system.operations if o.name == "view_transcript")
                        zone = next(z for z in self.system.zones if z.name == "Advising")
                        context = {"student": student.username, "gpa": gpa}
                        allowed = self.permission_engine.decide(advisor, op_view, zone, context)
                        self.logs.append({
                            "time": current_time.isoformat(),
                            "user": advisor.username,
                            "operation": op_view.name,
                            "zone": zone.name,
                            "allowed": allowed,
                            "student": student.username,
                            "gpa": gpa,
                            "action": "probation_check"
                        })
        sim = ProbationSim(self.system, self.permission_engine, storage=None)
        sim.run(datetime.timedelta(minutes=steps), step=datetime.timedelta(seconds=1))
        return sim.analyze()

if __name__ == "__main__":
    college = CollegeOfEngineering()
    print("Registration simulation...")
    print(college.sim_registration(50))
    print("Grading simulation...")
    print(college.sim_grading(50))
    print("Probation monitoring simulation...")
    print(college.sim_probation_monitoring(50))