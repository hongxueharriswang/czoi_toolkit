# CZOI Toolkit User Guide

**Version 1.0.0**  
*Build secure, adaptive, intelligent organizational systems with recursive zones, properties, roles, neural components, and daemons.*

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [Core Concepts](#4-core-concepts)
5. [Working with Zones](#5-working-with-zones)
6. [Managing Properties](#6-managing-properties)
7. [Roles, Users, and Permissions](#7-roles-users-and-permissions)
8. [Defining Operations](#8-defining-operations)
9. [Using Constraints](#9-using-constraints)
10. [Adding Neural Components](#10-adding-neural-components)
11. [Writing Daemons](#11-writing-daemons)
12. [Embedding Service](#12-embedding-service)
13. [Putting It All Together](#13-putting-it-all-together)
14. [Testing and Debugging](#14-testing-and-debugging)
15. [Deployment](#15-deployment)
16. [Best Practices](#16-best-practices)
17. [Troubleshooting](#17-troubleshooting)
18. [API Quick Reference](#18-api-quick-reference)

---

## 1. Introduction

The **CZOI Toolkit** is a Python library that implements the Constrained Zoned‑Object Architecture (11‑tuple) for building systems that are:

- **Secure** – fine‑grained, property‑aware access control.
- **Intelligent** – built‑in neural components for prediction and anomaly detection.
- **Organizational** – zones mirror real‑world hierarchies (departments, hospitals, warehouses).
- **Resilient** – daemons continuously monitor and enforce constraints.

This guide walks you through every feature with practical examples. By the end, you will be able to model and implement your own secure intelligent systems.

---

## 2. Installation

### Prerequisites

- Python 3.9 or higher
- `pip` package manager

### Install from PyPI

```bash
pip install czoi-toolkit
```

### Optional neural dependencies (PyTorch / TensorFlow)

```bash
pip install czoi-toolkit[neural]
```

### Verify installation

```python
import czoi
print(czoi.__version__)   # 1.0.0
```

---

## 3. Quick Start

Let's build a minimal system that tracks temperature in a warehouse.

```python
import asyncio
from czoi import *

async def main():
    # Create toolkit and system
    toolkit = CZOIToolkit()
    system = toolkit.create_system("MyFirstSystem")
    root = system.root_zone

    # Create an atomic zone
    warehouse = toolkit.create_atomic_zone("Warehouse", parent=root)
    root.add_child(warehouse)

    # Create a property
    temp_prop = toolkit.create_property(
        name="temperature",
        prop_type=PropertyType.FLOAT,
        zone_id=warehouse.id,
        initial_value=20.0
    )
    system.add_property(warehouse.id, temp_prop)

    # Create a role and a user
    viewer = toolkit.create_role("Viewer", zone_id=warehouse.id)
    system.add_role(viewer)
    alice = toolkit.create_user("alice", "password")
    alice.activate_role(viewer.id)

    # Define a simple operation
    class ReadTemp(Operation):
        async def execute(self, zone, context):
            temp = await system.property_store.get(zone, "temperature")
            return {"temperature": temp}

    read_op = ReadTemp("read_temp", app_id=root.id, signature={})
    read_op.id = uuid.uuid4()
    read_op.required_role_ids = {viewer.id}

    # Execute
    result = await system.execute(["Warehouse"], read_op, alice, {"active_role": viewer})
    print(result)

asyncio.run(main())
```

**Output:** `{'temperature': 20.0}`

---

## 4. Core Concepts

Before diving deeper, understand these six pillars:

| Concept | Purpose | Represented by |
|---------|---------|----------------|
| **Zone** | Hierarchical container (recursive) | `AtomicZone`, `CompositeZone` |
| **Property** | Typed state variable | `Property` class |
| **Role** | Set of permissions | `Role` dataclass |
| **Operation** | Executable action | Subclass of `Operation` |
| **Constraint** | Rule that must hold | `IdentityConstraint`, `TriggerConstraint`, etc. |
| **Daemon** | Continuous monitor | Subclass of `Daemon` |
| **Neural Component** | Learnable function | Subclass of `NeuralComponent` |

The **CZOASystem** container holds all these pieces together.

---

## 5. Working with Zones

Zones form a tree. You can have **atomic** zones (leaves) and **composite** zones (can embed another CZOA system).

### 5.1 Creating Zones

```python
toolkit = CZOIToolkit()
system = toolkit.create_system("Org")
root = system.root_zone

# Atomic zone
dept = toolkit.create_atomic_zone("HR", parent=root)

# Composite zone (can have embedded system)
region = toolkit.create_composite_zone("NorthRegion", parent=root)

root.add_child(dept)
root.add_child(region)
```

### 5.2 Navigating Zones

```python
# Get zone by path from root
zone = system.root_zone.get_child("NorthRegion")
```

### 5.3 Recursive Zones (Composite)

A composite zone can embed a full system:

```python
sub_system = toolkit.create_system("Embedded")
region.embed_system(sub_system)
```

Now all zones inside `sub_system` become children of `region`.

### 5.4 Aggregation Rules (Composite Zones)

Composite zones can aggregate properties from children:

```python
region.add_aggregation_rule("total_inventory", "sum")
region.add_aggregation_rule("avg_temperature", "avg")
```

The toolkit automatically recomputes these when child properties change.

---

## 6. Managing Properties

Properties are the state variables of zones. They are typed, versioned, and support access control.

### 6.1 Creating a Property

```python
prop = toolkit.create_property(
    name="patient_count",
    prop_type=PropertyType.INT,
    zone_id=zone.id,
    initial_value=0,
    read_roles={nurse_role.id},      # who can read
    write_roles={charge_nurse.id}    # who can write
)
system.add_property(zone.id, prop)
```

### 6.2 Reading and Writing Properties

Use the `property_store` from the system:

```python
# Read current
value = await system.property_store.get(zone, "patient_count")

# Write (requires permission)
success = await system.property_store.set(
    zone, "patient_count", new_value,
    user, role, operation
)
```

### 6.3 Subscribing to Changes

```python
async def on_temp_change(zone, prop, old, new):
    print(f"Temperature changed from {old} to {new}")

await system.property_store.subscribe(zone, "temperature", on_temp_change)
```

### 6.4 Historical Queries

```python
# Get value as of 5 minutes ago
from datetime import datetime, timedelta
old_value = await system.property_store.get(
    zone, "temperature",
    timestamp=datetime.now() - timedelta(minutes=5)
)
```

---

## 7. Roles, Users, and Permissions

### 7.1 Defining Roles

```python
role = toolkit.create_role(
    name="Manager",
    zone_id=zone.id,
    base_permissions={op1.id, op2.id}
)
```

**Seniority (intra‑zone inheritance):**

```python
senior_role.seniority_parents.append(junior_role)
```

**Inter‑zone mappings (γ):**

```python
role.inter_zone_mappings.append(
    (target_zone_id, target_role_id, weight=0.8, priority=1)
)
```

### 7.2 Creating Users and Activating Roles

```python
user = toolkit.create_user("bob", "hashed_pw", attributes={"dept": "sales"})
user.activate_role(manager_role.id, level=1.0)
```

### 7.3 Recursive Permission Policies

Set policy per zone:

```python
system.permission_engine.set_propagation_policy(
    zone.id, PropagationPolicy.STRICT   # or REQUEST, CAPABILITY
)
```

- **STRICT**: child inherits all parent permissions automatically.
- **REQUEST**: child must ask, conditionally granted.
- **CAPABILITY**: no automatic inheritance.

---

## 8. Defining Operations

Operations are the actions users can perform. Subclass `Operation` and implement `execute`.

### 8.1 Basic Operation

```python
class ShipOrder(Operation):
    async def execute(self, zone, context):
        order_id = context["order_id"]
        # Business logic
        await system.property_store.set(zone, f"order_{order_id}_status", "shipped",
                                        context['user'], context['active_role'], self)
        return {"status": "shipped", "order": order_id}
```

### 8.2 Registering an Operation

```python
ship_op = ShipOrder("ship_order", app_id=app.id, signature={})
ship_op.id = uuid.uuid4()
ship_op.required_role_ids = {logistics_role.id}
# No need to "register" – just pass to execute
```

### 8.3 Preconditions and Postconditions

```python
def check_stock(state):
    return state.get("stock") >= 5

ship_op.precondition = check_stock
```

### 8.4 Executing an Operation

```python
result = await system.execute(
    zone_path=["Warehouse", "Shipping"],
    operation=ship_op,
    user=alice,
    context={"active_role": logistics_role, "order_id": "ORD-123"}
)
```

---

## 9. Using Constraints

Constraints are declarative rules evaluated automatically by the `ConstraintEngine`.

### 9.1 Identity Constraint (Invariant)

```python
def stock_non_negative(state):
    return state.get("stock", 0) >= 0

identity = IdentityConstraint("stock_ge_zero", stock_non_negative)
system.constraint_engine.add_identity(identity)
```

If violated, the system raises `ConstraintViolationError`.

### 9.2 Trigger Constraint

```python
async def send_low_stock_alert(state):
    print("Low stock alert!")

trigger = TriggerConstraint(
    name="low_stock_trigger",
    event="property_change",
    condition=lambda s: s.get("stock", 0) < 10,
    action=send_low_stock_alert
)
system.constraint_engine.add_trigger(trigger)
```

### 9.3 Access Constraint

```python
def only_weekday_access(user, role, zone, operation, props, context):
    # Allow only Monday–Friday
    return datetime.now().weekday() < 5

access_constraint = AccessConstraint("weekday_only", only_weekday_access)
system.constraint_engine.add_access(access_constraint)
```

### 9.4 Goal Constraint

```python
def profit_utility(state):
    return state.get("revenue", 0) - state.get("cost", 0)

goal = GoalConstraint("profit_max", profit_utility)
system.constraint_engine.add_goal(goal)

# Later evaluate total utility
total = await system.constraint_engine.evaluate_goals(current_state)
```

---

## 10. Adding Neural Components

The toolkit provides base classes for predictors and detectors.

### 10.1 Using Built‑in Property Predictor

```python
predictor = PropertyPredictor("demand_forecaster", zone_id=zone.id)
system.add_neural_component(predictor)

# Predict next value from history
history = [100, 105, 110, 108]   # last 4 demand values
forecast = await predictor.forward({"history": history})
```

### 10.2 Using Anomaly Detector

```python
detector = AnomalyDetector("sensor_anomaly", zone_id=zone.id, threshold=0.8)
score = await detector.forward({"features": [0.5, 0.6, 0.55]})
if score > 0.8:
    print("Anomaly detected!")
```

### 10.3 Creating a Custom Neural Component

```python
class MyPredictor(NeuralComponent):
    async def forward(self, inputs):
        # Your inference logic
        return inputs["x"] * 2

    async def train(self, dataset):
        # Your training logic
        pass
```

---

## 11. Writing Daemons

Daemons run continuously and can **block**, **alert**, or **adapt**.

### 11.1 Simple Daemon

```python
class TemperatureSafetyDaemon(Daemon):
    async def monitor(self, zone, operation, props, context):
        temp = props.get("temperature", 0)
        if temp > 40:
            return DaemonAction.BLOCK
        return DaemonAction.ALLOW

    async def act(self, action, zone, props, context):
        print("High temperature! Blocking operation.")
        # Could also send alert, shut down equipment, etc.
```

### 11.2 Registering Daemons

```python
daemon = TemperatureSafetyDaemon("temp_safety", priority=100)
system.daemon_manager.register(daemon)
```

### 11.3 Daemon Priority and Conflict Resolution

When multiple daemons return different actions, the highest priority (largest number) wins. If two have same priority, the action order is: **BLOCK > CHALLENGE > ADAPT > ALERT > ALLOW**.

---

## 12. Embedding Service

The embedding service maps any entity (zone, role, user, property, operation) to a vector for similarity computation.

### 12.1 Setting and Getting Embeddings

```python
emb = EmbeddingService(dimension=64)
vec = np.random.randn(64)
emb.set_embedding("zone", zone.id, vec)
retrieved = emb.get_embedding("zone", zone.id)
```

### 12.2 Compositional Zone Embedding

For composite zones, the embedding is automatically computed from children:

```python
zone_vec = emb.compute_zone_embedding(composite_zone)
```

### 12.3 Similarity Search

```python
sim = emb.similarity(("role", role1.id), ("role", role2.id))
```

---

## 13. Putting It All Together

Here is a complete example of a **smart warehouse** with inventory tracking, a neural demand forecaster, and a daemon that blocks orders when stock is low.

```python
import asyncio
import uuid
from czoi import *

class DemandPredictor(NeuralComponent):
    async def forward(self, inputs):
        # Simplified: assume linear trend
        hist = inputs.get("history", [0])
        return hist[-1] * 1.05   # 5% growth

    async def train(self, dataset):
        pass

class ReorderOperation(Operation):
    async def execute(self, zone, context):
        sku = context["sku"]
        qty = context["quantity"]
        current = await system.property_store.get(zone, f"stock_{sku}")
        new = current + qty
        await system.property_store.set(zone, f"stock_{sku}", new,
                                        context['user'], context['active_role'], self)
        return {"sku": sku, "old": current, "new": new}

class LowStockDaemon(Daemon):
    def __init__(self, threshold=10):
        super().__init__("low_stock", priority=90)
        self.threshold = threshold

    async def monitor(self, zone, operation, props, context):
        if operation and operation.name == "reorder":
            sku = context.get("sku")
            stock = props.get(f"stock_{sku}", 0)
            if stock < self.threshold:
                return DaemonAction.BLOCK
        return DaemonAction.ALLOW

    async def act(self, action, zone, props, context):
        print(f"LowStockDaemon: Blocked reorder because stock < {self.threshold}")

async def main():
    global system
    toolkit = CZOIToolkit()
    system = toolkit.create_system("SmartWarehouse")
    root = system.root_zone

    # Zone
    wh = toolkit.create_atomic_zone("MainWarehouse", parent=root)
    root.add_child(wh)

    # Property: stock for SKU "A"
    stock_prop = toolkit.create_property("stock_A", PropertyType.INT, wh.id, initial_value=5)
    system.add_property(wh.id, stock_prop)

    # Role & user
    clerk = toolkit.create_role("clerk", zone_id=wh.id)
    system.add_role(clerk)
    alice = toolkit.create_user("alice", "pass")
    alice.activate_role(clerk.id)

    # Operation
    reorder = ReorderOperation("reorder", app_id=root.id, signature={})
    reorder.id = uuid.uuid4()
    reorder.required_role_ids = {clerk.id}

    # Neural component
    predictor = DemandPredictor("demand", zone_id=wh.id)
    system.add_neural_component(predictor)

    # Daemon
    low_stock_daemon = LowStockDaemon(threshold=10)
    system.daemon_manager.register(low_stock_daemon)

    # Execute: current stock=5, try to reorder 2 units -> daemon blocks
    ctx = {"active_role": clerk, "user": alice, "sku": "A", "quantity": 2}
    try:
        result = await system.execute(["MainWarehouse"], reorder, alice, ctx)
        print(result)
    except DaemonBlockError:
        print("Order blocked – stock below threshold")

    # Use predictor to forecast demand
    history = [5, 4, 3]   # last three stock levels
    forecast = await predictor.forward({"history": history})
    print(f"Forecasted next stock level: {forecast:.1f}")

asyncio.run(main())
```

**Output:**
```
LowStockDaemon: Blocked reorder because stock < 10
Order blocked – stock below threshold
Forecasted next stock level: 3.2
```

---

## 14. Testing and Debugging

### 14.1 Unit Testing with Pytest

```python
import pytest
from czoi import CZOIToolkit

@pytest.mark.asyncio
async def test_property_set():
    toolkit = CZOIToolkit()
    system = toolkit.create_system("Test")
    zone = toolkit.create_atomic_zone("Z", parent=system.root_zone)
    system.root_zone.add_child(zone)
    prop = toolkit.create_property("p", PropertyType.INT, zone.id, 0)
    system.add_property(zone.id, prop)
    await system.property_store.set(zone, "p", 42, None, None, None)
    assert await system.property_store.get(zone, "p") == 42
```

### 14.2 Enabling Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 14.3 Inspecting Effective Permissions

```python
perms = await system.permission_engine.effective_permissions(role, zone, props)
print([op_id for op_id in perms])
```

### 14.4 Manual Cache Invalidation

```python
system.permission_engine.invalidate_cache(role.id, zone.id)
```

---

## 15. Deployment

### 15.1 Running as a Service

Wrap your system in a long‑running asyncio loop:

```python
async def run_server():
    system = build_my_system()
    # Start daemons (they run automatically when check() is called)
    while True:
        await asyncio.sleep(1)
```

### 15.2 Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install czoi-toolkit
COPY . .
CMD ["python", "main.py"]
```

### 15.3 Scaling the Property Store

For production, replace `PropertyStore` with a distributed version (Redis, PostgreSQL). Subclass and override `get`/`set`.

---

## 16. Best Practices

| Practice | Rationale |
|----------|-----------|
| Keep zone depth ≤ 5 | Performance of recursive permission checks. |
| Use `PropagationPolicy.REQUEST` across trust boundaries | Prevents accidental privilege escalation. |
| Always set `required_role_ids` for operations | Otherwise any active role can execute. |
| Prefer identity constraints over manual checks | Declarative, automatically enforced. |
| Use daemons for real‑time monitoring, not for business logic | Daemons should be lightweight. |
| Cache embeddings if recomputation is expensive | Use `EmbeddingService` with weakref cache. |
| Test daemons in isolation with mocks | Daemons interact; mock other daemons. |

---

## 17. Troubleshooting

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| `PermissionDeniedError` | Role not activated or missing permission | Check `user.active_roles` and `role.base_permissions`. |
| `ZoneNotFoundError` | Path typo or zone not added | Verify zone tree with `root.children`. |
| Daemon not blocking | Priority too low or condition wrong | Log inside `monitor` to debug. |
| Property not updating | Missing `write` permission | Check `property.access_control['write']`. |
| Recursion depth error | Zone nesting > Python recursion limit | Increase limit or restructure tree. |

---

## 18. API Quick Reference

| Module | Main Classes | Key Methods |
|--------|--------------|--------------|
| `czoi.zones` | `Zone`, `AtomicZone`, `CompositeZone` | `add_child`, `execute` |
| `czoi.properties` | `Property`, `PropertyStore` | `get`, `set`, `subscribe` |
| `czoi.roles` | `Role`, `User` | `activate_role`, `deactivate_role` |
| `czoi.constraints` | `IdentityConstraint`, `TriggerConstraint`, etc. | `add_identity`, `check_access` |
| `czoi.neural` | `NeuralComponent`, `PropertyPredictor`, `AnomalyDetector` | `forward`, `train` |
| `czoi.daemons` | `Daemon`, `DaemonManager` | `register`, `check` |
| `czoi.permissions` | `PermissionEngine` | `effective_permissions`, `check_access` |
| `czoi.embedding` | `EmbeddingService` | `get_embedding`, `compute_zone_embedding`, `similarity` |
| `czoi.toolkit` | `CZOASystem`, `CZOIToolkit` | `execute`, `create_property`, `create_role` |

For complete API documentation, see [https://czoi.readthedocs.io](https://czoi.readthedocs.io).

---

## Next Steps

- Explore the `examples/` directory in the GitHub repository.
- Read the full research paper: [CZOA: A Unified Formalism...](https://arxiv.org/abs/xxxx)
- Join the community: GitHub Discussions or Gitter.

Happy building with CZOI Toolkit!