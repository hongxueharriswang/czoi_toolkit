# system1_opinion_dynamics.py
import random
import numpy as np
from datetime import timedelta
from czoi.core import System, Zone, Role, User, Application
from czoi.permission import PermissionEngine
from czoi.simulation import SimulationEngine
from czoi.storage.sqlalchemy import Storage
from czoi.neural.components import AnomalyDetector  # placeholder for predictor
from czoi.daemon.builtins import Daemon

# --- CZOA Setup ---
system = System()
global_zone = Zone("Global")
community_a = Zone("CommunityA", parent=global_zone)
community_b = Zone("CommunityB", parent=global_zone)
system.add_zone(global_zone)
system.add_zone(community_a)
system.add_zone(community_b)

# Roles
influencer = Role("Influencer", global_zone)
follower = Role("Follower", global_zone)
moderator = Role("Moderator", global_zone)
system.add_role(influencer)
system.add_role(follower)
system.add_role(moderator)

# Application
opinion_app = Application("OpinionDynamics")
express_op = opinion_app.add_operation("express_opinion")
influence_op = opinion_app.add_operation("influence_neighbor")
update_op = opinion_app.add_operation("update_opinion")
system.add_application(opinion_app)

# Permissions
influencer.grant_permission(influence_op)
follower.grant_permission(express_op)
follower.grant_permission(update_op)
moderator.grant_permission(express_op)  # moderators can also express

# Create agents (users)
agents = []
for i in range(100):
    u = User(f"agent_{i}")
    u.attributes["opinion"] = random.uniform(0, 1)
    u.attributes["influence_weight"] = random.uniform(0.1, 1.0) if i < 10 else 0.2  # top 10 are influencers
    # Assign role based on influence
    if i < 10:
        u.assign_role(global_zone, influencer)
    else:
        u.assign_role(global_zone, follower)
    # Assign to community randomly
    zone = random.choice([community_a, community_b])
    u.assign_role(zone, follower)  # community-specific role (just for zone context)
    agents.append(u)
    system.add_user(u)

# Add two moderators
mod1 = User("moderator1")
mod1.assign_role(global_zone, moderator)
mod2 = User("moderator2")
mod2.assign_role(global_zone, moderator)
system.add_user(mod1)
system.add_user(mod2)

# Build random network (neighbors)
for u in agents:
    # Each agent connected to 5 random others
    neighbors = random.sample([a for a in agents if a != u], 5)
    u.attributes["neighbors"] = [n.id for n in neighbors]

# Constraints (simulated in daemon or engine)
# We'll handle dynamics in simulation step

# Neural component (dummy)
class OpinionPredictor:
    def predict(self, data): return np.mean(data)

# Daemon
class PolarizationMonitor(Daemon):
    async def check(self):
        opinions = [u.attributes["opinion"] for u in agents]
        clusters = len(set([int(o*10) for o in opinions]))  # coarse clustering
        if clusters <= 2:
            return ["POLARIZATION_ALERT: Low diversity"]
        return []
    async def execute(self, action): print(action)

# Permission engine (simplified for this simulation)
class OpinionEngine(PermissionEngine):
    def decide(self, user, operation, zone, context=None):
        # Allow if user has role in this zone (we'll ignore operation details)
        if zone.id in user.zone_role_assignments:
            return True
        return False

engine = OpinionEngine(None)  # no storage needed

# Storage (in-memory)
storage = Storage("sqlite:///:memory:")

# Simulation engine with custom step logic
class OpinionSimulation(SimulationEngine):
    def __init__(self, system, engine, storage):
        super().__init__(system, engine, storage)
        self.threshold = 0.2  # assimilation threshold

    def step(self, current_time):
        # For each agent, randomly interact with a neighbor
        for u in agents:
            if not u.attributes.get("neighbors"):
                continue
            neighbor_id = random.choice(u.attributes["neighbors"])
            neighbor = next((a for a in agents if a.id == neighbor_id), None)
            if not neighbor:
                continue
            # Influence: weighted average
            w_u = u.attributes["influence_weight"]
            w_n = neighbor.attributes["influence_weight"]
            diff = abs(u.attributes["opinion"] - neighbor.attributes["opinion"])
            if diff < self.threshold:
                # assimilate
                new_opinion = (w_u * u.attributes["opinion"] + w_n * neighbor.attributes["opinion"]) / (w_u + w_n)
                u.attributes["opinion"] = new_opinion
                neighbor.attributes["opinion"] = new_opinion
            else:
                # repulsion (optional)
                pass
            self.logs.append({
                "timestamp": current_time.isoformat(),
                "user": u.username,
                "neighbor": neighbor.username,
                "opinion_u": u.attributes["opinion"],
                "opinion_n": neighbor.attributes["opinion"]
            })

    def run(self, duration, step=timedelta(seconds=1)):
        start = datetime.now()
        end = start + duration
        current = start
        while current < end:
            self.step(current)
            current += step

# Run simulation
from datetime import datetime
sim = OpinionSimulation(system, engine, storage)
sim.run(timedelta(seconds=30))

# Analyze
opinions = [a.attributes["opinion"] for a in agents]
print(f"Final opinions: mean={np.mean(opinions):.2f}, std={np.std(opinions):.2f}")