# CZOI Toolkit User Guide

## Building Intelligent Organizational Systems with CZOI in Python

**Version:** 0.1.0  
**Author:** Harris Wang  
**License:** MIT  
**Repository:** [https://github.com/harriswatau/czoi_toolkit](https://github.com/harriswatau/czoi_toolkit)

---

## Table of Contents

1. [Introduction](#1-introduction)  
2. [Installation](#2-installation)  
3. [Core Concepts](#3-core-concepts)  
    - 3.1 [Zones](#31-zones)  
    - 3.2 [Roles](#32-roles)  
    - 3.3 [Users](#33-users)  
    - 3.4 [Applications and Operations](#34-applications-and-operations)  
    - 3.5 [Gamma Mappings](#35-gamma-mappings)  
4. [Building a System](#4-building-a-system)  
    - 4.1 [Creating a Zone Hierarchy](#41-creating-a-zone-hierarchy)  
    - 4.2 [Defining Roles and Permissions](#42-defining-roles-and-permissions)  
    - 4.3 [Adding Users](#43-adding-users)  
    - 4.4 [Setting Up Gamma Mappings](#44-setting-up-gamma-mappings)  
5. [Constraints](#5-constraints)  
    - 5.1 [Identity Constraints](#51-identity-constraints)  
    - 5.2 [Trigger Constraints](#52-trigger-constraints)  
    - 5.3 [Goal Constraints](#53-goal-constraints)  
    - 5.4 [Access Constraints](#54-access-constraints)  
6. [Permission Engine](#6-permission-engine)  
    - 6.1 [Checking Permissions](#61-checking-permissions)  
    - 6.2 [Effective Permission Calculation](#62-effective-permission-calculation)  
7. [Neural Components](#7-neural-components)  
    - 7.1 [Built‑in Neural Components](#71-built-in-neural-components)  
    - 7.2 [Training a Neural Component](#72-training-a-neural-component)  
    - 7.3 [Using a Neural Component in a Daemon](#73-using-a-neural-component-in-a-daemon)  
8. [Embeddings](#8-embeddings)  
    - 8.1 [Creating Embeddings](#81-creating-embeddings)  
    - 8.2 [Similarity Search](#82-similarity-search)  
9. [Daemons](#9-daemons)  
    - 9.1 [Built‑in Daemons](#91-built-in-daemons)  
    - 9.2 [Writing a Custom Daemon](#92-writing-a-custom-daemon)  
10. [Simulation](#10-simulation)  
    - 10.1 [Running a Simulation](#101-running-a-simulation)  
    - 10.2 [Analyzing Simulation Results](#102-analyzing-simulation-results)  
11. [Web Framework Integrations](#11-web-framework-integrations)  
    - 11.1 [Django](#111-django)  
    - 11.2 [Flask](#112-flask)  
    - 11.3 [FastAPI](#113-fastapi)  
12. [Command‑Line Interface](#12-command-line-interface)  
13. [Persistence](#13-persistence)  
14. [Examples](#14-examples)  
    - 14.1 [Healthcare System](#141-healthcare-system)  
    - 14.2 [Financial Trading Desk](#142-financial-trading-desk)  
    - 14.3 [Traffic Management](#143-traffic-management)  
    - 14.4 [University Management](#144-university-management)  
    - 14.5 [Distribution Center](#145-distribution-center)  
15. [API Reference](#15-api-reference)  
16. [Contributing](#16-contributing)  
17. [License](#17-license)  

---

## 1. Introduction

The **CZOI Toolkit** is a Python implementation of the **Constrained Zone‑Object Architecture (CZOA)** – a unified formalism for building intelligent, secure, and adaptive organizational systems. CZOA combines the theoretical depth of Constrained Object Hierarchies (COH) with the engineering pragmatism of the Zoned Role‑Based (ZRB) framework. The result is a single coherent model that captures:

- **Organizational structure** through hierarchical zones.
- **Security policies** via roles, permissions, and constraints.
- **Intelligence** through neural components that learn from data.
- **Continuous monitoring** with daemons that enforce policies in real time.
- **Simulation** capabilities to validate system behaviour before deployment.

CZOI provides a set of Python classes and utilities that let you translate a CZOA model into an executable system. It is designed to be modular, extensible, and scalable – from small prototypes to large enterprise deployments.

This guide will walk you through all the features of the toolkit, with practical examples drawn from real‑world domains such as healthcare, finance, smart cities, education, and supply chain.

---

## 2. Installation

Install the core package via pip:

```bash
pip install czoi
```

For optional features, use extras:

```bash
pip install czoi[neural]      # PyTorch, transformers, scikit-learn
pip install czoi[api]          # FastAPI, uvicorn
pip install czoi[django]       # Django support
pip install czoi[flask]        # Flask support
pip install czoi[all]          # All extras
```

---

## 3. Core Concepts

### 3.1 Zones

A **Zone** represents an organizational unit. Zones form a tree: each zone (except the root) has exactly one parent and may have many children. Zones contain roles, applications, and users.

```python
from czoi.core import Zone

root = Zone("GlobalBank")
trading = Zone("Trading", parent=root)
equities = Zone("Equities", parent=trading)
```

### 3.2 Roles

A **Role** defines a job function within a specific zone. Each role has a set of base permissions (operations it can perform) and may have senior/junior relationships with other roles in the same zone (intra‑zone hierarchy).

```python
from czoi.core import Role

trader = Role("Trader", zone=equities)
head_trader = Role("HeadTrader", zone=equities)
head_trader.add_senior(trader)   # HeadTrader inherits permissions from Trader
```

### 3.3 Users

A **User** represents an individual who can be assigned to roles in different zones. A user may hold multiple roles, each with an optional weight (e.g., primary vs. secondary role).

```python
from czoi.core import User

alice = User("alice", "alice@bank.com")
alice.assign_role(equities, trader, weight=1.0)
```

### 3.4 Applications and Operations

An **Application** is a software system that exposes **Operations** – the executable actions that users can perform. Operations are the atomic units of work.

```python
from czoi.core import Application

oms = Application("OrderManagementSystem", owning_zone=equities)
enter_order = oms.add_operation("enter_order", method="POST")
cancel_order = oms.add_operation("cancel_order", method="DELETE")

trader.grant_permission(enter_order)
trader.grant_permission(cancel_order)
```

### 3.5 Gamma Mappings

A **GammaMapping** defines inter‑zone role inheritance: a role in one zone can inherit permissions from a role in another zone (usually a parent or related zone). Mappings have a weight (0..1) and a priority.

```python
from czoi.core import GammaMapping

# A trader in Equities can also trade in ProgramTrading with reduced privileges
prog = Zone("ProgramTrading", parent=trading)
gm = GammaMapping(
    child_zone=equities,
    child_role=trader,
    parent_zone=prog,
    parent_role=trader,
    weight=0.5,
    priority=2
)
system.add_gamma_mapping(gm)
```

---

## 4. Building a System

The `System` class is a container for all zones, roles, users, applications, operations, and gamma mappings. You typically start by creating a `System` object and then building its contents.

### 4.1 Creating a Zone Hierarchy

```python
from czoi.core import System, Zone

system = System()
root = Zone("NHS_Root")
system.add_zone(root)

regions = ["North", "South", "East", "West"]
for reg in regions:
    region = Zone(f"{reg}_Region", parent=root)
    system.add_zone(region)
    for i in range(2):
        hosp = Zone(f"{reg}_Hospital_{i+1}", parent=region)
        system.add_zone(hosp)
```

### 4.2 Defining Roles and Permissions

```python
from czoi.core import Role, Application

# Create an application
ehr = Application("ElectronicHealthRecord")
view_patient = ehr.add_operation("view_patient", "GET")
order_test = ehr.add_operation("order_test", "POST")
system.add_application(ehr)

# Create roles and grant permissions
attending = Role("AttendingPhysician", zone=hosp)
attending.grant_permission(view_patient)
attending.grant_permission(order_test)
system.add_role(attending)

nurse = Role("RegisteredNurse", zone=hosp)
nurse.grant_permission(view_patient)
system.add_role(nurse)
```

### 4.3 Adding Users

```python
alice = User("alice")
alice.assign_role(hosp, attending, weight=1.0)
system.add_user(alice)
```

### 4.4 Setting Up Gamma Mappings

```python
# A physician in a hospital can also serve in a nearby clinic
clinic = Zone("Clinic", parent=region)
gm = GammaMapping(hosp, attending, clinic, attending, weight=0.8, priority=1)
system.add_gamma_mapping(gm)
```

---

## 5. Constraints

Constraints are rules that govern the system’s behaviour. CZOA defines four types, all represented by the `Constraint` class.

```python
from czoi.constraint import Constraint, ConstraintType
```

### 5.1 Identity Constraints

Identity constraints are invariants that must always hold. For example, ensuring that a user in a child zone is also in the parent zone.

```python
id_con = Constraint(
    "ZoneContainment",
    ConstraintType.IDENTITY,
    {"zones": "all"},
    "user in parent.users"
)
```

### 5.2 Trigger Constraints

Trigger constraints define event‑condition‑action rules. When an event occurs and the condition is true, the associated action is executed.

```python
trigger = Constraint(
    "LowStockReorder",
    ConstraintType.TRIGGER,
    {"event": "inventory_update"},
    "quantity < reorder_point and not already_ordered",
    priority=1
)
```

### 5.3 Goal Constraints

Goal constraints represent optimization objectives, such as key performance indicators (KPIs).

```python
goal = Constraint(
    "OnTimeShipment",
    ConstraintType.GOAL,
    {"metric": "shipment_rate"},
    "value > 0.98"
)
```

### 5.4 Access Constraints

Access constraints are checked during permission decisions. They can enforce separation of duty, time‑based restrictions, etc.

```python
access = Constraint(
    "OrderDispenseSoD",
    ConstraintType.ACCESS,
    {"roles": ["AttendingPhysician", "Pharmacist"]},
    "user != last_dispenser"
)
```

Constraints are managed by a `ConstraintManager`:

```python
from czoi.constraint import ConstraintManager

manager = ConstraintManager()
manager.add(access)
```

The permission engine uses the constraint manager to evaluate access constraints.

---

## 6. Permission Engine

The `PermissionEngine` is responsible for making access decisions. It computes effective permissions for a role in a given zone, taking into account base permissions, intra‑zone inheritance, gamma mappings, and access constraints.

### 6.1 Checking Permissions

```python
from czoi.permission import SimpleEngine

engine = SimpleEngine(system)   # or use a storage‑backed engine

user = alice
operation = view_patient
zone = hosp
context = {"time": datetime.now(), "user_role": "Attending"}

if engine.decide(user, operation, zone, context):
    # perform the operation
    pass
else:
    raise PermissionDenied()
```

### 6.2 Effective Permission Calculation

You can also directly obtain the set of effective permissions for a role:

```python
perms = engine.get_effective_permissions(attending, hosp)
for op in perms:
    print(op.name)
```

The engine automatically handles:

- Base permissions of the role.
- Permissions inherited from junior roles (intra‑zone hierarchy).
- Permissions inherited via gamma mappings (inter‑zone, respecting weights and priorities).

---

## 7. Neural Components

Neural components bring learning and adaptation to your system. They implement the `NeuralComponent` abstract base class.

### 7.1 Built‑in Neural Components

The toolkit includes several ready‑to‑use neural components:

- `AnomalyDetector` – uses Isolation Forest to detect unusual access patterns.
- `RoleMiner` – discovers latent roles via HDBSCAN clustering.
- `PermissionPredictor` – suggests permissions for new roles using collaborative filtering.
- `SimilarityEmbedder` – learns embeddings for entities (to be used with the embedding service).

### 7.2 Training a Neural Component

```python
from czoi.neural import AnomalyDetector
import numpy as np

# Generate some dummy training data (features extracted from access logs)
X_train = np.random.randn(1000, 10)

detector = AnomalyDetector(contamination=0.05)
detector.train(X_train)
detector.save("anomaly_model.pkl")
```

Later, load the model and use it:

```python
detector = AnomalyDetector.load("anomaly_model.pkl")
score = detector.predict(sample_features)   # returns anomaly score in [0,1]
```

### 7.3 Using a Neural Component in a Daemon

Neural components are often used inside daemons to make real‑time decisions.

```python
from czoi.daemon import Daemon

class SecurityDaemon(Daemon):
    def __init__(self, detector, threshold=0.8, **kwargs):
        super().__init__("security", **kwargs)
        self.detector = detector
        self.threshold = threshold

    async def check(self):
        # Get recent access logs from storage
        logs = storage.get_recent_logs(limit=100)
        actions = []
        for log in logs:
            features = extract_features(log)
            risk = self.detector.predict(features)
            if risk > self.threshold:
                actions.append(f"BLOCK:{log.user_id}")
        return actions
```

---

## 8. Embeddings

Embeddings provide a semantic vector representation of entities (zones, roles, users, applications, operations). They enable similarity searches and can be used by neural components.

### 8.1 Creating Embeddings

The `EmbeddingService` manages vector storage and generation.

```python
from czoi.embedding import EmbeddingService, InMemoryVectorStore

store = InMemoryVectorStore()
service = EmbeddingService(store)

# Generate an embedding for a role (using a pre‑trained embedder or fallback)
vec = service.embed_entity(trader)
service.update_embedding(trader.id, vec)
```

You can plug in a neural embedder (e.g., a graph neural network) by passing it to the service.

### 8.2 Similarity Search

Once embeddings are stored, you can find similar entities:

```python
similar = service.find_similar(trader.id, k=5)
for entity_id, score in similar:
    print(f"Similar entity: {entity_id}, similarity: {score}")
```

This is useful for permission recommendations, anomaly detection, and cross‑zone role matching.

---

## 9. Daemons

Daemons are background processes that continuously monitor the system, enforce constraints, and trigger actions. They run as asyncio tasks.

### 9.1 Built‑in Daemons

- `SecurityDaemon` – monitors access logs and blocks suspicious users.
- `ComplianceDaemon` – checks for regulatory violations (e.g., HIPAA, GDPR).
- `PerformanceDaemon` – tracks KPIs and suggests goal adjustments.
- `AnomalyDaemon` – uses an anomaly detector to flag unusual patterns.

### 9.2 Writing a Custom Daemon

Subclass `Daemon` and implement the `check` method. The `check` method should return a list of action strings, which will be passed to `execute`.

```python
from czoi.daemon import Daemon

class TemperatureDaemon(Daemon):
    def __init__(self, sensors, threshold=4.0, **kwargs):
        super().__init__("temperature", **kwargs)
        self.sensors = sensors
        self.threshold = threshold

    async def check(self):
        violations = []
        for sensor in self.sensors:
            temp = sensor.read()
            if temp > self.threshold:
                violations.append(f"TEMP_VIOLATION:{sensor.zone_id}")
        return violations

    async def execute(self, action):
        if action.startswith("TEMP_VIOLATION"):
            _, zone_id = action.split(":")
            # Quarantine products in that zone
            zone = storage.get_zone(zone_id)
            for product in zone.get_products():
                product.quarantine()
            self.logger.warning(f"Quarantined zone {zone_id} due to high temperature")
```

Start a daemon:

```python
import asyncio

daemon = TemperatureDaemon(sensors, interval=5.0)
asyncio.create_task(daemon.run())
# later, daemon.stop()
```

---

## 10. Simulation

The simulation engine lets you test your system under various scenarios before deployment. It drives the system through time, generating random (or scripted) events and logging outcomes.

### 10.1 Running a Simulation

Create a subclass of `SimulationEngine` and implement the `step` method. The `step` method is called at each time interval.

```python
from czoi.simulation import SimulationEngine
import random
from datetime import timedelta

class TradingSim(SimulationEngine):
    def step(self, current_time):
        # Generate random access attempts
        for _ in range(random.randint(1, 5)):
            user = random.choice(self.users)
            op = random.choice(self.operations)
            zone = random.choice(list(self.system.zones))
            context = {"time": current_time, "market_open": True}
            allowed = self.permission_engine.decide(user, op, zone, context)
            self.logs.append({
                "timestamp": current_time.isoformat(),
                "user": user.username,
                "operation": op.name,
                "zone": zone.name,
                "allowed": allowed
            })

sim = TradingSim(system, permission_engine)
sim.run(duration=timedelta(minutes=10), step=timedelta(seconds=1))
```

### 10.2 Analyzing Simulation Results

After the simulation, use the `analyze` method to get summary statistics:

```python
results = sim.analyze()
print(results)
# {'total_requests': 345, 'allowed': 332, 'denied': 13, 'allow_rate': 0.9623}
```

You can also export logs to a file for deeper analysis:

```python
sim.save_logs("trading_sim.json")
```

---

## 11. Web Framework Integrations

CZOI provides decorators and middleware for popular web frameworks, so you can easily enforce permissions in your web applications.

### 11.1 Django

Add the middleware to `settings.py`:

```python
MIDDLEWARE = [
    'czoi.integrations.django.middleware.CZOAMiddleware',
]
```

Then use the `require_permission` decorator:

```python
from czoi.integrations.django.decorators import require_permission

@require_permission('view_dashboard', mode='i_rzbac')
def dashboard(request):
    return render(request, 'dashboard.html')
```

### 11.2 Flask

```python
from flask import Flask
from czoi.integrations.flask import login_required, permission_required

app = Flask(__name__)

@app.route('/admin')
@login_required
@permission_required('admin_access', mode='n_rzbac')
def admin():
    return "Admin panel"
```

### 11.3 FastAPI

```python
from fastapi import FastAPI, Depends
from czoi.integrations.fastapi import get_current_user, require_permission

app = FastAPI()

@app.get("/secure")
def secure_endpoint(user = Depends(get_current_user),
                    _ = Depends(require_permission("read:secure"))):
    return {"message": "ok"}
```

---

## 12. Command‑Line Interface

The CZOI toolkit includes a CLI for common administrative tasks. After installation, the `czoa` command is available.

```bash
# Initialize a system from a YAML config
czoi init --config system.yaml

# Check a permission
czoa check --user alice --operation view_patient --zone hosp

# Run a simulation
czoi simulate --duration 1h --output results.json

# View audit logs
czoi audit --since 2026-03-01

# Migrate the system (add a zone)
czoi migrate add-zone --name "NewClinic" --parent "North_Region"

# Train a neural component
czoi train --model anomaly --data access_logs.csv --output model.pkl

# Start a daemon
czoi daemon start security --threshold 0.9
```

The configuration file (`system.yaml`) can define zones, roles, users, and gamma mappings in a human‑readable format.

---

## 13. Persistence

CZOI supports persistent storage via SQLAlchemy. You can use SQLite for development and PostgreSQL for production.

```python
from czoi.storage import SQLAlchemyStorage

storage = SQLAlchemyStorage("sqlite:///my_system.db")
storage.save(system)   # persists all zones, roles, etc.
```

For vector embeddings, you can use `pgvector` (PostgreSQL) or an in‑memory store.

The storage layer also provides methods to retrieve gamma mappings, constraints, audit logs, etc.

---

## 14. Examples

The toolkit comes with five complete examples corresponding to the case studies in the CZOA paper. They are located in the `examples/` directory of the repository.

### 14.1 Healthcare System

- File: `examples/healthcare.py`
- Demonstrates a three‑level zone hierarchy (National → Regions → Hospitals).
- Uses gamma mappings for cross‑site privileges.
- Includes an anomaly detector for insider threat detection.
- Simulations: normal operations, flu surge, breach detection.

### 14.2 Financial Trading Desk

- File: `examples/trading.py`
- Models trading desks, risk, and compliance zones.
- Integrates a market impact predictor neural component.
- Simulations: normal trading, market crash, insider trading.

### 14.3 Traffic Management

- File: `examples/traffic.py`
- Zones for control center, signals, sensors, VMS, incidents.
- Uses a graph neural network for road network embeddings.
- Simulations: normal traffic, accident, signal failure.

### 14.4 University Management

- File: `examples/university.py`
- Colleges, departments, research labs, advising.
- FERPA identity constraints.
- Student success predictor neural component.
- Simulations: registration, grading, probation monitoring.

### 14.5 Distribution Center

- File: `examples/distribution.py`
- Receiving, storage, picking, packing, shipping, returns.
- SKU embeddings for slotting optimization.
- Temperature daemon for cold chain.
- Simulations: normal fulfillment, peak season, inventory discrepancy.

Run any example with:

```bash
python examples/healthcare.py
```

Each example includes a main block that runs the three simulations and prints summary statistics.

---

## 15. API Reference

For detailed documentation of all classes and methods, please refer to the [API Reference](https://czoi.readthedocs.io/) (under construction). Key modules:

- `czoi.core`: Zone, Role, User, Application, Operation, GammaMapping, System
- `czoi.permission`: PermissionEngine, SimpleEngine
- `czoi.constraint`: Constraint, ConstraintType, ConstraintManager
- `czoi.neural`: NeuralComponent, AnomalyDetector, RoleMiner, PermissionPredictor, SimilarityEmbedder
- `czoi.embedding`: EmbeddingService, VectorStore, InMemoryVectorStore
- `czoi.daemon`: Daemon, SecurityDaemon, ComplianceDaemon, PerformanceDaemon, AnomalyDaemon
- `czoi.simulation`: SimulationEngine
- `czoi.storage`: Storage, SQLAlchemyStorage
- `czoi.integrations`: django, flask, fastapi
- `czoi.cli`: main CLI entry point

---

## 16. Contributing

We welcome contributions! Please see the [CONTRIBUTING.md](https://github.com/harriswatau/czoi_toolkit/blob/main/CONTRIBUTING.md) file for guidelines. The project uses `pytest` for testing, `black` for code formatting, and `mypy` for type checking.

---

## 17. License

CZOI is released under the MIT License. See the [LICENSE](https://github.com/harriswatau/czoi_toolkit/blob/main/LICENSE) file for details.

---

*Happy building!*  
— The CZOI Team