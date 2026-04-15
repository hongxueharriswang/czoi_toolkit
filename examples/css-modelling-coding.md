# Five Complex Intelligent Systems in Computational Social Science Modeled with CZOA and Implemented with CZOI

This document presents five complex systems from computational social science, each modeled using the Constrained Zone-Object Architecture (CZOA). For each system, we provide:

1. **System Description** – The social phenomenon being modeled.
2. **CZOA Model** – Mapping of the system onto zones, roles, users, applications, operations, constraints, neural components, embeddings, and daemons.
3. **CZOI Implementation** – Executable Python code using the `czoi` toolkit that sets up the system, runs simulations, and produces outputs.
4. **Three Simulations** – Distinct scenarios demonstrating the system's behavior under different conditions.

The code is written assuming the `czoi` toolkit is installed (`pip install czoi[neural]` for neural components). Each simulation produces logs and analysis results.

---

## System 1: Opinion Dynamics in Social Networks

### 1.1 Description
We model a social network where agents hold continuous opinions on an issue. Agents interact with neighbors and update their opinions based on influence, with some agents being more influential (e.g., opinion leaders). The system evolves toward consensus, polarization, or fragmentation depending on network structure and influence mechanisms.

### 1.2 CZOA Model

| CZOA Component | Mapping |
|----------------|---------|
| **Zones** | Network layers: `Global`, `Communities` (sub-networks) |
| **Roles** | `Influencer` (high influence), `Follower` (low influence), `Moderator` (can adjust network) |
| **Users** | Individual agents |
| **Applications** | `OpinionDynamicsApp` with operations: `express_opinion`, `influence_neighbor`, `update_opinion` |
| **Operations** | As above |
| **Attributes** | `opinion` (float), `influence_weight` (float), `neighbors` (list of user IDs) |
| **Neural Components** | `OpinionPredictor` (predicts future opinion distribution), `InfluenceLearner` (learns influence weights from interaction data) |
| **Embeddings** | Agent embedding based on opinion and network position |
| **Identity Constraints** | `I1`: Opinion must remain in [0,1]; `I2`: Influence weight non-negative |
| **Trigger Constraints** | `T1`: If two agents' opinions differ by less than threshold, they move closer (assimilation) |
| **Goal Constraints** | `G1`: Minimize overall opinion variance (consensus) or maximize diversity (pluralism) |
| **Daemons** | `PolarizationMonitor` (tracks opinion clusters), `InfluenceTracker` (logs influence events) |

### 1.3 CZOI Implementation

```python
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
```

### 1.4 Three Simulations

**Simulation 1.1: Baseline** – Run as above with random network and moderate influence weights. Observe convergence.

**Simulation 1.2: Polarization** – Increase influence of two agents (opinion leaders) in separate communities, reduce cross-community connections. Expect polarization.

**Simulation 1.3: Moderation** – Add moderator agents that occasionally adjust opinions toward center. Observe reduced variance.

```python
# simulation1.2_polarization.py (excerpt)
# Modify network: create two communities with few cross-edges
for u in agents[:50]: u.attributes["neighbors"] = [a.id for a in agents[:50] if a != u][:5]
for u in agents[50:]: u.attributes["neighbors"] = [a.id for a in agents[50:] if a != u][:5]
# Increase influence of first agent in each community
agents[0].attributes["influence_weight"] = 2.0
agents[50].attributes["influence_weight"] = 2.0
# Run simulation...
```

---

## System 2: Crowd Evacuation During Emergency

### 2.1 Description
We model a building with multiple rooms and corridors. Agents (people) need to evacuate to exits. Some agents act as guides (e.g., staff) who direct others. Constraints include capacity limits, congestion, and safety. Neural components predict congestion, daemons alert when bottlenecks form.

### 2.2 CZOA Model

| Component | Mapping |
|-----------|---------|
| **Zones** | Rooms, corridors, exits (hierarchical: Building → Floor → Room) |
| **Roles** | `Evacuee`, `Guide`, `SafetyOfficer` |
| **Users** | People in building |
| **Applications** | `EvacuationApp` with operations: `move_to`, `guide`, `report_congestion` |
| **Operations** | As above |
| **Attributes** | `position` (zone ID), `speed`, `familiarity` (knowledge of exits) |
| **Neural Components** | `CongestionPredictor` (predicts future occupancy per zone) |
| **Embeddings** | Zone embeddings based on connectivity and capacity |
| **Identity Constraints** | `I1`: Zone occupancy ≤ capacity; `I2`: No two agents occupy same exact position (if discrete) |
| **Trigger Constraints** | `T1`: If occupancy > threshold, trigger rerouting |
| **Goal Constraints** | `G1`: Minimize evacuation time |
| **Daemons** | `CongestionMonitor`, `SafetyAlertDaemon` |

### 2.3 CZOI Implementation

```python
# system2_evacuation.py
import random
from datetime import timedelta
from czoi.core import System, Zone, Role, User, Application

# Build building zones
building = Zone("Building")
floor1 = Zone("Floor1", parent=building)
floor2 = Zone("Floor2", parent=building)
room101 = Zone("Room101", parent=floor1)
room102 = Zone("Room102", parent=floor1)
corridor1 = Zone("Corridor1", parent=floor1)
exit1 = Zone("Exit1", parent=floor1)
exit2 = Zone("Exit2", parent=floor2)
# ... add capacities
for z in [room101, room102, corridor1, exit1, exit2]:
    z.capacity = 10 if "Room" in z.name else 20 if "Corridor" in z.name else 5

system = System()
system.add_zone(building)
system.add_zone(floor1)
system.add_zone(floor2)
system.add_zone(room101)
system.add_zone(room102)
system.add_zone(corridor1)
system.add_zone(exit1)
system.add_zone(exit2)

# Roles
evacuee = Role("Evacuee", building)
guide = Role("Guide", building)
officer = Role("SafetyOfficer", building)
system.add_role(evacuee)
system.add_role(guide)
system.add_role(officer)

# App
evac_app = Application("Evacuation")
move_op = evac_app.add_operation("move_to")
guide_op = evac_app.add_operation("guide")
report_op = evac_app.add_operation("report_congestion")
system.add_application(evac_app)

# Permissions
evacuee.grant_permission(move_op)
guide.grant_permission(guide_op)
officer.grant_permission(report_op)

# Create people
people = []
for i in range(30):
    u = User(f"person_{i}")
    u.attributes["speed"] = random.uniform(0.5, 1.5)
    u.attributes["familiarity"] = random.choice([0.2, 0.5, 1.0])  # 1.0 knows best exit
    # Assign starting zone (all in room101 initially)
    u.assign_role(room101, evacuee)  # role for zone context
    people.append(u)
    system.add_user(u)

# Add guides
for i in range(3):
    g = User(f"guide_{i}")
    g.assign_role(building, guide)
    g.attributes["speed"] = 1.2
    g.attributes["familiarity"] = 1.0
    g.assign_role(room101, evacuee)  # also evacuee
    people.append(g)
    system.add_user(g)

# Officer
officer_user = User("officer")
officer_user.assign_role(building, officer)
system.add_user(officer_user)

# Simulation engine with movement logic
class EvacuationSim(SimulationEngine):
    def __init__(self, system, engine, storage):
        super().__init__(system, engine, storage)
        self.exit_zones = [exit1, exit2]

    def step(self, current_time):
        # For each person, decide next move based on familiarity and congestion
        for u in people:
            current_zone_id = next(iter(u.zone_role_assignments.keys()))  # simplified: one zone
            current_zone = self.system.get_zone(current_zone_id)
            if current_zone in self.exit_zones:
                continue  # evacuated
            # Choose next zone: from current zone's children or parent? In graph, we need adjacency.
            # Simplified: if in room, go to corridor; if corridor, go to exit
            if "Room" in current_zone.name:
                target = corridor1
            elif "Corridor" in current_zone.name:
                target = exit1 if u.attributes["familiarity"] > 0.5 else exit2
            else:
                continue
            # Check capacity
            current_occupancy = len([p for p in people if target.id in p.zone_role_assignments])
            if current_occupancy < target.capacity:
                # Move: remove from old zone, add to new
                del u.zone_role_assignments[current_zone_id]
                u.assign_role(target, evacuee)
                self.logs.append({
                    "timestamp": current_time.isoformat(),
                    "user": u.username,
                    "from": current_zone.name,
                    "to": target.name
                })

sim = EvacuationSim(system, None, None)
sim.run(timedelta(seconds=60))
evacuated = sum(1 for u in people if any(z.name.startswith("Exit") for z in u.zone_role_assignments))
print(f"Evacuated: {evacuated}/{len(people)}")
```

### 2.4 Three Simulations

**Simulation 2.1: Normal** – All agents have moderate familiarity. Observe evacuation time.

**Simulation 2.2: Guide Effect** – Add guides that lead people to less congested exits. Compare times.

**Simulation 2.3: Panic** – Reduce familiarity, increase speed, introduce randomness in decisions. Measure congestion.

---

## System 3: Financial Market with Adaptive Traders

### 3.1 Description
We model a simple financial market with different trader types: market makers, arbitrageurs, and noise traders. Prices evolve based on order flow. Traders adapt their strategies based on past performance. Constraints include capital limits and risk controls.

### 3.2 CZOA Model

| Component | Mapping |
|-----------|---------|
| **Zones** | `Exchange`, `TradingDesk` (for each trader type) |
| **Roles** | `MarketMaker`, `Arbitrageur`, `NoiseTrader` |
| **Users** | Traders |
| **Applications** | `TradingApp` with operations: `place_order`, `cancel_order`, `get_quote` |
| **Operations** | As above |
| **Attributes** | `cash`, `holdings`, `risk_tolerance`, `strategy_params` |
| **Neural Components** | `PricePredictor` (LSTM), `StrategyOptimizer` (RL) |
| **Embeddings** | Trader embedding based on behavior |
| **Identity Constraints** | `I1`: Cash ≥ 0; `I2`: Holdings ≥ 0 |
| **Trigger Constraints** | `T1`: If price drops >10% in 1 minute, halt trading |
| **Goal Constraints** | `G1`: Maximize profit, `G2`: Minimize risk |
| **Daemons** | `FlashCrashDetector`, `RiskMonitor` |

### 3.3 CZOI Implementation

```python
# system3_market.py
import random
import numpy as np
from czoi.core import System, Zone, Role, User, Application

# Zones
exchange = Zone("Exchange")
mm_desk = Zone("MarketMakerDesk", parent=exchange)
arb_desk = Zone("ArbitrageDesk", parent=exchange)
noise_desk = Zone("NoiseDesk", parent=exchange)
system = System()
for z in [exchange, mm_desk, arb_desk, noise_desk]:
    system.add_zone(z)

# Roles
market_maker = Role("MarketMaker", exchange)
arbitrageur = Role("Arbitrageur", exchange)
noise_trader = Role("NoiseTrader", exchange)
system.add_role(market_maker)
system.add_role(arbitrageur)
system.add_role(noise_trader)

# App
trading_app = Application("Trading")
place_op = trading_app.add_operation("place_order")
cancel_op = trading_app.add_operation("cancel_order")
quote_op = trading_app.add_operation("get_quote")
system.add_application(trading_app)

# Permissions (all can place orders)
for r in [market_maker, arbitrageur, noise_trader]:
    r.grant_permission(place_op)
    r.grant_permission(cancel_op)
    r.grant_permission(quote_op)

# Create traders
traders = []
for i in range(5):
    u = User(f"mm_{i}")
    u.assign_role(mm_desk, market_maker)
    u.attributes["cash"] = 100000
    u.attributes["holdings"] = 0
    u.attributes["risk_tolerance"] = 0.2
    traders.append(u)
    system.add_user(u)

for i in range(3):
    u = User(f"arb_{i}")
    u.assign_role(arb_desk, arbitrageur)
    u.attributes["cash"] = 50000
    u.attributes["holdings"] = 0
    u.attributes["risk_tolerance"] = 0.5
    traders.append(u)
    system.add_user(u)

for i in range(10):
    u = User(f"noise_{i}")
    u.assign_role(noise_desk, noise_trader)
    u.attributes["cash"] = 10000
    u.attributes["holdings"] = 0
    u.attributes["risk_tolerance"] = 0.8
    traders.append(u)
    system.add_user(u)

# Price state
price = 100.0

class MarketSim(SimulationEngine):
    def step(self, current_time):
        nonlocal price
        # Generate orders randomly
        for u in traders:
            if random.random() < 0.3:
                # decide buy/sell based on role
                if "mm" in u.username:
                    # market maker provides liquidity
                    side = random.choice(["buy", "sell"])
                elif "arb" in u.username:
                    # arbitrageur follows trend
                    side = "buy" if random.random() > 0.5 else "sell"
                else:
                    # noise trader random
                    side = random.choice(["buy", "sell"])
                quantity = random.randint(1, 10)
                # Simulate price impact
                if side == "buy":
                    price *= 1 + 0.001 * quantity
                else:
                    price *= 1 - 0.001 * quantity
                self.logs.append({
                    "timestamp": current_time.isoformat(),
                    "trader": u.username,
                    "side": side,
                    "quantity": quantity,
                    "price": price
                })
        # Enforce constraints: cash/holdings not implemented for brevity

sim = MarketSim(system, None, None)
sim.run(timedelta(minutes=10), step=timedelta(seconds=1))
print(f"Final price: {price:.2f}")
```

### 3.4 Three Simulations

**Simulation 3.1: Baseline** – Run as above.

**Simulation 3.2: Flash Crash** – Introduce a large sell order from a noise trader, trigger circuit breaker.

**Simulation 3.3: Adaptive Strategies** – Implement a simple reinforcement learning for arbitrageurs that learns to trade based on price momentum.

---

## System 4: Epidemic Spread with Behavioral Response

### 4.1 Description
We model an SIR-type epidemic in a population divided into regions. Individuals can travel, quarantine, or get vaccinated. Behavioral responses (e.g., social distancing) emerge from perceived risk. Neural components predict infection peaks; daemons issue alerts.

### 4.2 CZOA Model

| Component | Mapping |
|-----------|---------|
| **Zones** | Regions (cities, districts) |
| **Roles** | `Susceptible`, `Infected`, `Recovered`, `Vaccinated`, `HealthOfficial` |
| **Users** | Individuals |
| **Applications** | `HealthApp` with operations: `travel`, `quarantine`, `vaccinate`, `report_case` |
| **Operations** | As above |
| **Attributes** | `health_state` (S/I/R/V), `compliance` (willingness to follow guidelines) |
| **Neural Components** | `InfectionPredictor` (time-series forecast) |
| **Embeddings** | Region embeddings based on connectivity and demographics |
| **Identity Constraints** | `I1`: Health state ∈ {S,I,R,V} |
| **Trigger Constraints** | `T1`: If infection rate > threshold, trigger lockdown in zone |
| **Goal Constraints** | `G1`: Minimize total infections, `G2`: Minimize economic cost |
| **Daemons** | `OutbreakDetector`, `ComplianceMonitor` |

### 4.3 CZOI Implementation

```python
# system4_epidemic.py
import random
from czoi.core import System, Zone, Role, User, Application

# Zones
city1 = Zone("City1")
city2 = Zone("City2")
city3 = Zone("City3")
system = System()
for z in [city1, city2, city3]:
    system.add_zone(z)

# Roles
susceptible = Role("Susceptible", city1)  # will be zone-specific
infected = Role("Infected", city1)
recovered = Role("Recovered", city1)
vaccinated = Role("Vaccinated", city1)
official = Role("HealthOfficial", city1)
system.add_role(susceptible)
system.add_role(infected)
system.add_role(recovered)
system.add_role(vaccinated)
system.add_role(official)

# App
health_app = Application("Health")
travel_op = health_app.add_operation("travel")
quarantine_op = health_app.add_operation("quarantine")
vaccinate_op = health_app.add_operation("vaccinate")
report_op = health_app.add_operation("report_case")
system.add_application(health_app)

# Permissions: all can travel, only officials can report
for r in [susceptible, infected, recovered, vaccinated]:
    r.grant_permission(travel_op)
    r.grant_permission(quarantine_op)
    r.grant_permission(vaccinate_op)
official.grant_permission(report_op)

# Create population
population = []
for i in range(300):
    u = User(f"person_{i}")
    # assign to random city
    city = random.choice([city1, city2, city3])
    # initial health: most susceptible, few infected
    if i < 5:
        role = infected
        u.attributes["health_state"] = "I"
    else:
        role = susceptible
        u.attributes["health_state"] = "S"
    u.assign_role(city, role)
    u.attributes["compliance"] = random.uniform(0, 1)
    population.append(u)
    system.add_user(u)

# Officials
for i in range(3):
    off = User(f"official_{i}")
    off.assign_role(city1, official)
    off.attributes["health_state"] = "R"
    system.add_user(off)

# Infection parameters
beta = 0.3  # transmission rate
gamma = 0.1  # recovery rate

class EpidemicSim(SimulationEngine):
    def step(self, current_time):
        # For each city, count S,I,R
        for city in [city1, city2, city3]:
            users_in_city = [u for u in population if city.id in u.zone_role_assignments]
            s = [u for u in users_in_city if u.attributes["health_state"] == "S"]
            i = [u for u in users_in_city if u.attributes["health_state"] == "I"]
            # Infections
            num_infections = int(beta * len(s) * len(i) / max(1, len(users_in_city)))
            for _ in range(min(num_infections, len(s))):
                victim = random.choice(s)
                if victim.attributes["compliance"] > 0.5:  # high compliance reduces risk
                    if random.random() > 0.5:
                        continue
                victim.attributes["health_state"] = "I"
                # Update role: remove susceptible, add infected
                del victim.zone_role_assignments[city.id]
                victim.assign_role(city, infected)
                s.remove(victim)
            # Recoveries
            for infected_person in i:
                if random.random() < gamma:
                    infected_person.attributes["health_state"] = "R"
                    del infected_person.zone_role_assignments[city.id]
                    infected_person.assign_role(city, recovered)
            # Log
            self.logs.append({
                "timestamp": current_time.isoformat(),
                "city": city.name,
                "S": len(s),
                "I": len(i),
                "R": len([u for u in users_in_city if u.attributes["health_state"] == "R"])
            })

sim = EpidemicSim(system, None, None)
sim.run(timedelta(days=30), step=timedelta(days=1))
# Analyze final counts
for city in [city1, city2, city3]:
    users = [u for u in population if city.id in u.zone_role_assignments]
    s = sum(1 for u in users if u.attributes["health_state"] == "S")
    i = sum(1 for u in users if u.attributes["health_state"] == "I")
    r = sum(1 for u in users if u.attributes["health_state"] == "R")
    print(f"{city.name}: S={s}, I={i}, R={r}")
```

### 4.4 Three Simulations

**Simulation 4.1: No Intervention** – Run as above.

**Simulation 4.2: Lockdown** – Trigger when infection rate > 0.1 in a city, reduce travel and transmission.

**Simulation 4.3: Vaccination Campaign** – Gradually vaccinate susceptibles, observe effect.

---

## System 5: Urban Traffic Flow with Adaptive Routing

### 5.1 Description
We model a city road network with intersections and segments. Vehicles (agents) navigate from origins to destinations, choosing routes based on real-time congestion. Traffic signals adapt to flow. Neural components predict congestion; daemons adjust signals.

### 5.2 CZOA Model

| Component | Mapping |
|-----------|---------|
| **Zones** | Road segments, intersections (hierarchical: City → District → Road) |
| **Roles** | `Committer`, `TrafficController`, `EmergencyVehicle` |
| **Users** | Vehicles |
| **Applications** | `TrafficApp` with operations: `navigate`, `signal_control`, `reroute` |
| **Operations** | As above |
| **Attributes** | `position` (zone), `destination`, `speed`, `route_plan` |
| **Neural Components** | `CongestionPredictor` (GNN on road graph) |
| **Embeddings** | Road segment embeddings based on traffic patterns |
| **Identity Constraints** | `I1`: Speed ≤ speed limit; `I2`: Vehicle capacity ≤ road capacity |
| **Trigger Constraints** | `T1`: If congestion > threshold, reroute vehicles |
| **Goal Constraints** | `G1`: Minimize average travel time |
| **Daemons** | `CongestionMonitor`, `SignalOptimizer` |

### 5.3 CZOI Implementation

```python
# system5_traffic.py
import random
from czoi.core import System, Zone, Role, User, Application

# Road network: simple grid
city = Zone("City")
district1 = Zone("District1", parent=city)
district2 = Zone("District2", parent=city)
# Roads (as zones)
roadA = Zone("RoadA", parent=district1)
roadB = Zone("RoadB", parent=district1)
roadC = Zone("RoadC", parent=district2)
intersection = Zone("Intersection", parent=city)  # connects roads

system = System()
for z in [city, district1, district2, roadA, roadB, roadC, intersection]:
    system.add_zone(z)
    z.capacity = 10  # vehicles per zone
    z.speed_limit = 50

# Roles
commuter = Role("Commuter", city)
controller = Role("TrafficController", city)
emergency = Role("EmergencyVehicle", city)
system.add_role(commuter)
system.add_role(controller)
system.add_role(emergency)

# App
traffic_app = Application("Traffic")
navigate_op = traffic_app.add_operation("navigate")
signal_op = traffic_app.add_operation("signal_control")
reroute_op = traffic_app.add_operation("reroute")
system.add_application(traffic_app)

# Permissions
commuter.grant_permission(navigate_op)
controller.grant_permission(signal_op)
controller.grant_permission(reroute_op)
emergency.grant_permission(navigate_op)

# Create vehicles
vehicles = []
for i in range(50):
    v = User(f"vehicle_{i}")
    v.attributes["speed"] = random.uniform(20, 60)
    v.attributes["destination"] = random.choice([roadB, roadC])
    # Start at roadA
    v.assign_role(roadA, commuter)
    vehicles.append(v)
    system.add_user(v)

# Add a few emergency vehicles
for i in range(2):
    ev = User(f"emergency_{i}")
    ev.attributes["speed"] = 80
    ev.assign_role(roadA, emergency)
    vehicles.append(ev)
    system.add_user(ev)

# Controllers
ctrl = User("controller")
ctrl.assign_role(city, controller)
system.add_user(ctrl)

class TrafficSim(SimulationEngine):
    def step(self, current_time):
        # Move vehicles along simple route: RoadA -> Intersection -> Destination
        for v in vehicles:
            # Find current zone
            current_zone_id = next(iter(v.zone_role_assignments))
            current_zone = self.system.get_zone(current_zone_id)
            if current_zone == v.attributes["destination"]:
                continue  # arrived
            # Determine next zone
            if current_zone == roadA:
                next_zone = intersection
            elif current_zone == intersection:
                next_zone = v.attributes["destination"]
            else:
                continue
            # Check capacity
            if len([u for u in vehicles if next_zone.id in u.zone_role_assignments]) < next_zone.capacity:
                # Move
                del v.zone_role_assignments[current_zone_id]
                v.assign_role(next_zone, commuter if "emergency" not in v.username else emergency)
                self.logs.append({
                    "timestamp": current_time.isoformat(),
                    "vehicle": v.username,
                    "from": current_zone.name,
                    "to": next_zone.name
                })

sim = TrafficSim(system, None, None)
sim.run(timedelta(minutes=10), step=timedelta(seconds=5))
# Count arrivals
arrived = sum(1 for v in vehicles if v.attributes["destination"].id in v.zone_role_assignments)
print(f"Arrived: {arrived}/{len(vehicles)}")
```

### 5.4 Three Simulations

**Simulation 5.1: Baseline** – Run as above.

**Simulation 5.2: Congestion** – Increase number of vehicles to exceed capacity, observe delays.

**Simulation 5.3: Adaptive Signals** – Implement controller that adjusts traffic light timing at intersection to prioritize emergency vehicles or clear queues.

---

## Summary

These five examples demonstrate how CZOA can model diverse socio-technical systems using a unified framework of zones, roles, permissions, constraints, neural components, and daemons. The CZOI toolkit provides the building blocks to implement such models and run simulations. Each system can be extended with more sophisticated neural components, realistic data, and interactive dashboards.