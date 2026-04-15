# Comprehensive Developer Tutorial: Modeling and Implementing Secure abd Intelligent Organizational Systems with CZOI Toolkit

This tutorial guides you through the entire process of using the **CZOI Toolkit** – from conceptual modeling of secure, intelligent organizational systems to implementing them as live Python applications. You will learn how to leverage recursive zones, first‑class properties, roles, permissions, constraints, neural components, and daemons to build systems that are both adaptive and trustworthy.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation and Setup](#2-installation-and-setup)
3. [Core Concepts in 10 Minutes](#3-core-concepts-in-10-minutes)
4. [Step‑by‑Step: Modeling a Healthcare Triage System](#4-step-by-step-modeling-a-healthcare-triage-system)
5. [Implementing the Model with CZOI Toolkit](#5-implementing-the-model-with-czoi-toolkit)
6. [Adding Intelligence: Neural Components](#6-adding-intelligence-neural-components)
7. [Continuous Enforcement: Daemons and Constraints](#7-continuous-enforcement-daemons-and-constraints)
8. [Advanced: Recursive Zones and Permission Propagation](#8-advanced-recursive-zones-and-permission-propagation)
9. [Testing and Debugging](#9-testing-and-debugging)
10. [Deployment Considerations](#10-deployment-considerations)
11. [Full Example: Supply Chain Inventory Optimizer](#11-full-example-supply-chain-inventory-optimizer)
12. [Best Practices and Common Pitfalls](#12-best-practices-and-common-pitfalls)
13. [Next Steps and Resources](#13-next-steps-and-resources)

---

## 1. Introduction

The **Constrained Zoned‑Object Architecture (CZOA)** is a formal 11‑tuple model for building systems that are:

- **Secure** – fine‑grained, property‑aware access control.
- **Intelligent** – neural components that learn and adapt.
- **Organizational** – zones mirror real‑world hierarchies.
- **Resilient** – continuous monitoring via daemons.

The CZOI Toolkit implements this model in Python, allowing you to focus on your domain logic while the framework handles security, state management, learning, and monitoring.

**Who is this tutorial for?**  
Developers and architects who want to build production‑ready intelligent systems (e.g., healthcare, finance, logistics, smart cities) without starting from scratch.

**What you will learn:**  
- How to decompose an organization into recursive zones.
- How to define typed properties that represent state.
- How to set up role‑based permissions with recursive propagation.
- How to embed neural predictors and anomaly detectors.
- How to write daemons that enforce constraints in real time.
- How to implement all of this in Python using the CZOI Toolkit.

---

## 2. Installation and Setup

### Prerequisites
- Python 3.9 or higher
- `pip` package manager

### Install from PyPI (recommended)

```bash
pip install czoi-toolkit
```

### Install from source (for development)

```bash
git clone https://github.com/yourusername/czoi-toolkit.git
cd czoi-toolkit
pip install -e .
```

### Verify installation

```python
import czoi
print(czoi.__version__)  # 1.0.0
```

### Optional dependencies for neural components

```bash
pip install czoi-toolkit[neural]   # installs torch / tensorflow
```

---

## 3. Core Concepts in 10 Minutes

Before writing code, understand the five pillars of CZOA:

| Concept | What it represents | In code |
|---------|--------------------|---------|
| **Zones** | Hierarchical containers (recursive) | `AtomicZone`, `CompositeZone` |
| **Properties** | Typed state variables | `Property` class |
| **Roles & Permissions** | Who can do what | `Role`, `PermissionEngine` |
| **Constraints** | Rules that must hold | `IdentityConstraint`, `TriggerConstraint`, `AccessConstraint`, `GoalConstraint` |
| **Neural Components** | Learnable functions | `NeuralComponent` subclasses |
| **Daemons** | Continuous monitors | `Daemon` subclasses |

The **11‑tuple** `(Z, R, U, A, P, O, N, E, Γ, Φ, Δ)` ties everything together. You don’t need to memorise it; the toolkit provides a `CZOASystem` container that holds all components.

---

## 4. Step‑by‑Step: Modeling a Healthcare Triage System

We will model a **hospital emergency department** that:
- Tracks patient acuity.
- Assigns nurses and doctors.
- Adapts staffing based on predicted surges.

### 4.1 Identify Recursive Zones

Our hospital has departments, and the emergency department has wards. We choose a depth of 3:

```
Hospital (composite)
└── EmergencyDept (composite)
    └── TriageWard (atomic)
```

**Why composite for EmergencyDept?** Because in the future we may add embedded systems (e.g., a lab subsystem). Atomic zones are leaves.

### 4.2 Define Properties (State)

| Property | Zone | Type | Meaning |
|----------|------|------|---------|
| `patient_acuity` | TriageWard | int (1‑5) | Severity (5 = critical) |
| `nurse_staffing` | EmergencyDept | int | Number of nurses on duty |
| `waiting_time` | TriageWard | float (minutes) | Average wait |

### 4.3 Define Roles and Permissions

| Role | Zone | Permissions |
|------|------|-------------|
| `triage_nurse` | TriageWard | `read_acuity`, `update_acuity` |
| `charge_nurse` | EmergencyDept | `read_all`, `adjust_staffing` |
| `physician` | EmergencyDept | `prescribe_treatment`, `override_triage` |

**Recursive policy:** `STRICT` – child zones inherit permissions from parent (so triage_nurse can also read hospital‑wide policies).

### 4.4 Identify Constraints

- **Identity:** `patient_acuity` between 1 and 5.
- **Trigger:** If `waiting_time > 30` minutes, trigger `alert_supervisor`.
- **Access:** Only `charge_nurse` can modify `nurse_staffing`.
- **Goal:** Minimize `waiting_time` subject to `nurse_staffing ≤ budget`.

### 4.5 Neural Components for Intelligence

- **Acuity predictor (LSTM):** Input: patient vital signs over last hour. Output: predicted acuity in 30 minutes. Used to pre‑allocate resources.
- **Staffing recommender (RL):** Suggests how many nurses to call in based on predicted patient load.

### 4.6 Daemons for Continuous Monitoring

- **Safety daemon:** Monitors `patient_acuity` for sudden jumps → alert physician.
- **Compliance daemon:** Checks that nurse‑to‑patient ratio never exceeds legal limit.

Now you have a complete model. Next, we implement it.

---

## 5. Implementing the Model with CZOI Toolkit

We will write Python code that builds the system, defines components, and executes operations.

### 5.1 Create the System and Zones

```python
import asyncio
from czoi import CZOIToolkit, CZOASystem, AtomicZone, CompositeZone

# Create toolkit and system
toolkit = CZOIToolkit()
system = toolkit.create_system("CityHospital")

# Get root zone (already a CompositeZone)
root = system.root_zone

# Build hierarchy
hospital = toolkit.create_composite_zone("Hospital", parent=root)
ed = toolkit.create_composite_zone("EmergencyDept", parent=hospital)
triage = toolkit.create_atomic_zone("TriageWard", parent=ed)

root.add_child(hospital)
hospital.add_child(ed)
ed.add_child(triage)
```

### 5.2 Define Properties

```python
from czoi import Property, PropertyType
import uuid

# Property for TriageWard
acuity_prop = toolkit.create_property(
    name="patient_acuity",
    prop_type=PropertyType.INT,
    zone_id=triage.id,
    initial_value=0,
    read_roles=set(),   # empty set means all roles can read (simplify for demo)
    write_roles=set()
)
system.add_property(triage.id, acuity_prop)

waiting_prop = toolkit.create_property(
    name="waiting_time",
    prop_type=PropertyType.FLOAT,
    zone_id=triage.id,
    initial_value=0.0
)
system.add_property(triage.id, waiting_prop)

# Property for EmergencyDept
staffing_prop = toolkit.create_property(
    name="nurse_staffing",
    prop_type=PropertyType.INT,
    zone_id=ed.id,
    initial_value=2
)
system.add_property(ed.id, staffing_prop)
```

### 5.3 Define Roles and Users

```python
from czoi import Role, User

# Roles
triage_nurse_role = toolkit.create_role("triage_nurse", zone_id=triage.id)
charge_nurse_role = toolkit.create_role("charge_nurse", zone_id=ed.id)
physician_role = toolkit.create_role("physician", zone_id=ed.id)

system.add_role(triage_nurse_role)
system.add_role(charge_nurse_role)
system.add_role(physician_role)

# Users
alice = toolkit.create_user("alice", "hashed_pw", attributes={"title": "RN"})
alice.activate_role(triage_nurse_role.id, level=1.0)

bob = toolkit.create_user("bob", "hashed_pw", attributes={"title": "Charge Nurse"})
bob.activate_role(charge_nurse_role.id, level=1.0)
```

### 5.4 Define Operations (Methods)

Operations are the actions users can perform. They must subclass `Operation` and implement `execute`.

```python
from czoi import Operation

class UpdateAcuity(Operation):
    """Nurse updates a patient's acuity score."""
    async def execute(self, zone, context):
        patient_id = context.get("patient_id")
        new_acuity = context.get("acuity")
        # Business logic: validate, update property
        await system.property_store.set(
            zone, "patient_acuity", new_acuity,
            context['user'], context['active_role'], self
        )
        return {"status": "updated", "patient": patient_id, "acuity": new_acuity}

class RequestStaffingChange(Operation):
    """Charge nurse changes nurse count."""
    async def execute(self, zone, context):
        new_count = context.get("new_staffing")
        current = await system.property_store.get(zone, "nurse_staffing")
        if new_count < 1:
            raise ValueError("At least one nurse required")
        await system.property_store.set(
            zone, "nurse_staffing", new_count,
            context['user'], context['active_role'], self
        )
        return {"old": current, "new": new_count}
```

**Important:** Operations must have their `id` set (the toolkit uses UUIDs). For simplicity, assign manually or use `uuid.uuid4()`.

```python
update_op = UpdateAcuity("update_acuity", app_id=hospital.id, signature={})
update_op.id = uuid.uuid4()
update_op.required_role_ids = {triage_nurse_role.id}

staffing_op = RequestStaffingChange("adjust_staffing", app_id=hospital.id, signature={})
staffing_op.id = uuid.uuid4()
staffing_op.required_role_ids = {charge_nurse_role.id}
```

### 5.5 Execute Operations

```python
async def triage_patient():
    # Alice (triage nurse) updates acuity
    context = {
        "active_role": triage_nurse_role,
        "user": alice,
        "patient_id": "P100",
        "acuity": 4
    }
    result = await system.execute(
        zone_path=["Hospital", "EmergencyDept", "TriageWard"],
        operation=update_op,
        user=alice,
        context=context
    )
    print(result)

    # Bob (charge nurse) increases staffing
    context2 = {
        "active_role": charge_nurse_role,
        "user": bob,
        "new_staffing": 3
    }
    result2 = await system.execute(
        zone_path=["Hospital", "EmergencyDept"],
        operation=staffing_op,
        user=bob,
        context=context2
    )
    print(result2)

# Run
asyncio.run(triage_patient())
```

**Output:**
```
{'status': 'updated', 'patient': 'P100', 'acuity': 4}
{'old': 2, 'new': 3}
```

---

## 6. Adding Intelligence: Neural Components

The toolkit includes base classes for predictors and detectors. We will add a **property predictor** that forecasts waiting time based on recent acuity and staffing.

### 6.1 Create a Custom Neural Component

```python
from czoi import NeuralComponent
import numpy as np

class WaitingTimePredictor(NeuralComponent):
    """Predicts waiting time in 30 minutes using a simple linear model."""
    def __init__(self, name, zone_id):
        super().__init__(name, zone_id)
        # In real life, you'd load a trained PyTorch/TF model.
        self.coeff = np.array([0.5, -0.2])  # weights for [acuity, staffing]

    async def forward(self, inputs):
        # inputs: dict with 'acuity' and 'staffing'
        acuity = inputs.get('acuity', 0)
        staffing = inputs.get('staffing', 1)
        predicted = self.coeff[0] * acuity - self.coeff[1] * staffing
        return max(0.0, predicted)

    async def train(self, dataset):
        # Stub: training would update self.coeff
        pass
```

### 6.2 Register and Use the Predictor

```python
# Create predictor and add to system
predictor = WaitingTimePredictor("wait_predictor", zone_id=ed.id)
system.add_neural_component(predictor)

# Use it during an operation or daemon
async def predict_waiting_time():
    acuity = await system.property_store.get(triage, "patient_acuity")
    staffing = await system.property_store.get(ed, "nurse_staffing")
    prediction = await predictor.forward({"acuity": acuity, "staffing": staffing})
    print(f"Predicted waiting time in 30 min: {prediction:.1f} minutes")
```

---

## 7. Continuous Enforcement: Daemons and Constraints

Daemons run in the background and can block, alert, or adapt. Constraints are declarative rules evaluated by the `ConstraintEngine`.

### 7.1 Define a Constraint

```python
from czoi import IdentityConstraint, TriggerConstraint, AccessConstraint

# Identity: acuity between 1 and 5
def acuity_in_range(state):
    acuity = state.get("patient_acuity", 0)
    return 1 <= acuity <= 5

identity_constraint = IdentityConstraint("acuity_range", acuity_in_range)
system.constraint_engine.add_identity(identity_constraint)

# Trigger: if waiting_time > 30, send alert
async def alert_supervisor(state):
    print("ALERT: Waiting time exceeded 30 minutes!")

trigger = TriggerConstraint(
    name="wait_alert",
    event="property_change",
    condition=lambda s: s.get("waiting_time", 0) > 30,
    action=alert_supervisor
)
system.constraint_engine.add_trigger(trigger)
```

Constraints are checked automatically during state changes (via `decide`). You don't need to call them manually.

### 7.2 Create a Custom Daemon

A daemon monitors property changes and can block operations.

```python
from czoi import Daemon, DaemonAction

class StaffingSafetyDaemon(Daemon):
    """Prevents nurse_staffing from going below 2 during peak hours."""
    def __init__(self):
        super().__init__("staffing_safety", priority=90)

    async def monitor(self, zone, operation, props, context):
        if operation and operation.name == "adjust_staffing":
            new_staffing = context.get("new_staffing", 0)
            # Simulate peak hour check (8 AM - 8 PM)
            hour = datetime.now().hour
            if 8 <= hour <= 20 and new_staffing < 2:
                return DaemonAction.BLOCK
        return DaemonAction.ALLOW

    async def act(self, action, zone, props, context):
        if action == DaemonAction.BLOCK:
            print("StaffingSafetyDaemon: Blocked staffing reduction during peak hours.")
```

Register the daemon:

```python
safety_daemon = StaffingSafetyDaemon()
system.daemon_manager.register(safety_daemon)
```

Now if Bob tries to set `new_staffing = 1` during daytime, the daemon blocks it and prints a message.

---

## 8. Advanced: Recursive Zones and Permission Propagation

CZOA’s real power emerges when you nest zones. Let’s extend the healthcare model to multiple hospitals.

### 8.1 Build a Region with Two Hospitals

```python
region = toolkit.create_composite_zone("NorthRegion", parent=root)
hospital_a = toolkit.create_composite_zone("HospitalA", parent=region)
hospital_b = toolkit.create_composite_zone("HospitalB", parent=region)
root.add_child(region)
region.add_child(hospital_a)
region.add_child(hospital_b)

# Add EmergencyDept under each hospital (reuse existing code)
ed_a = toolkit.create_composite_zone("EmergencyDept", parent=hospital_a)
triage_a = toolkit.create_atomic_zone("TriageWard", parent=ed_a)
# ... similarly for hospital_b
```

### 8.2 Permission Propagation (STRICT policy)

With strict inheritance, a `charge_nurse` in `HospitalA/EmergencyDept` automatically has read access to `HospitalA` properties. To give cross‑hospital visibility, define an inter‑zone mapping (γ):

```python
# Give charge_nurse in HospitalA read access to HospitalB's staffing
charge_nurse_a = system.permission_engine.roles[charge_nurse_role.id]
charge_nurse_a.inter_zone_mappings.append(
    (hospital_b.id, charge_nurse_role.id, weight=0.5, priority=1)
)
```

Now a query from `charge_nurse_a` for `HospitalB.nurse_staffing` will succeed (γ‑closure includes the mapped role).

### 8.3 Setting Propagation Policies per Zone

```python
from czoi import PropagationPolicy

# Use REQUEST policy for inter‑hospital resource sharing
system.permission_engine.set_propagation_policy(hospital_a.id, PropagationPolicy.REQUEST)
system.permission_engine.set_propagation_policy(hospital_b.id, PropagationPolicy.REQUEST)
```

Now roles in one hospital must request permissions to access the other, and the request is evaluated against property conditions (e.g., only allowed if `surge_capacity > 0`).

---

## 9. Testing and Debugging

### 9.1 Unit Testing with Pytest

```python
import pytest
from czoi import CZOIToolkit

@pytest.mark.asyncio
async def test_acuity_update():
    toolkit = CZOIToolkit()
    system = toolkit.create_system("Test")
    # ... setup minimal zones and roles
    # Execute operation and assert property changed
    assert await system.property_store.get(triage, "patient_acuity") == 4
```

### 9.2 Debugging Tips

- Enable logging: `import logging; logging.basicConfig(level=logging.DEBUG)`
- Use the `invalidate_cache` method of `PermissionEngine` to force recomputation.
- Print the effective permissions for a role:  
  `perms = await system.permission_engine.effective_permissions(role, zone, props)`

### 9.3 Simulating Time

For daemons that depend on time, mock `datetime.now()` using `unittest.mock.patch`.

---

## 10. Deployment Considerations

### 10.1 Scaling the Property Store

The default `PropertyStore` is in‑memory. For production:
- Replace with a distributed store (Redis, PostgreSQL + TimescaleDB) by subclassing `PropertyStore` and overriding `get`/`set`.
- Use the schemas provided in Appendix B of the paper.

### 10.2 Running Daemons as Separate Processes

Daemons in the toolkit are asynchronous but run inside the same event loop. For heavy monitoring, deploy them as microservices that subscribe to property change events via a message queue (Kafka, RabbitMQ).

### 10.3 Security Hardening

- Never store plaintext passwords; use `passlib` or similar.
- Use HTTPS for all API calls.
- Encrypt property values at rest (e.g., using `cryptography` library).

### 10.4 Packaging for Production

Build a Docker image:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install czoi-toolkit
COPY . .
CMD ["python", "main.py"]
```

---

## 11. Full Example: Supply Chain Inventory Optimizer

Here is a complete, runnable example that models a simple supply chain with two warehouses and a central distribution centre.

```python
import asyncio
from czoi import *

class ReorderOperation(Operation):
    async def execute(self, zone, context):
        sku = context["sku"]
        quantity = context["quantity"]
        current = await system.property_store.get(zone, f"stock_{sku}")
        new = current + quantity
        await system.property_store.set(zone, f"stock_{sku}", new,
                                        context['user'], context['active_role'], self)
        return {"sku": sku, "old": current, "new": new}

async def main():
    toolkit = CZOIToolkit()
    system = toolkit.create_system("SupplyChain")
    root = system.root_zone

    # Zones
    dc = toolkit.create_composite_zone("DistributionCentre", parent=root)
    wh1 = toolkit.create_atomic_zone("Warehouse_North", parent=dc)
    wh2 = toolkit.create_atomic_zone("Warehouse_South", parent=dc)
    root.add_child(dc)
    dc.add_child(wh1)
    dc.add_child(wh2)

    # Properties
    for wh in [wh1, wh2]:
        for sku in ["A", "B"]:
            prop = toolkit.create_property(f"stock_{sku}", PropertyType.INT,
                                           zone_id=wh.id, initial_value=100)
            system.add_property(wh.id, prop)

    # Roles
    clerk_role = toolkit.create_role("clerk", zone_id=wh1.id)
    manager_role = toolkit.create_role("manager", zone_id=dc.id)
    system.add_role(clerk_role)
    system.add_role(manager_role)

    # Users
    alice = toolkit.create_user("alice", "pw")
    alice.activate_role(clerk_role.id)
    bob = toolkit.create_user("bob", "pw")
    bob.activate_role(manager_role.id)

    # Operations
    reorder_op = ReorderOperation("reorder", app_id=dc.id, signature={})
    reorder_op.id = uuid.uuid4()
    reorder_op.required_role_ids = {clerk_role.id}

    # Execute
    context = {"active_role": clerk_role, "user": alice, "sku": "A", "quantity": 50}
    result = await system.execute(["DistributionCentre", "Warehouse_North"],
                                  reorder_op, alice, context)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 12. Best Practices and Common Pitfalls

| Practice | Why |
|----------|-----|
| Keep zones shallow (depth ≤ 5) | Performance of recursive permission checks. |
| Use property aggregation sparingly | Aggregation recomputation can be expensive; cache results. |
| Always set `required_role_ids` for operations | Otherwise anyone can execute. |
| Test daemons in isolation | Daemons interact; use mocks for other daemons. |
| Use `PropagationPolicy.REQUEST` for cross‑trust boundaries | Prevents accidental privilege escalation. |
| Never store sensitive data in property `value` without encryption | Properties are stored in plain JSON. |

**Common Pitfalls:**
- Forgetting to call `system.add_property()` after creating a property.
- Not setting `operation.id` (results in `KeyError`).
- Using `asyncio.run()` inside a running event loop.
- Modifying `role.base_permissions` directly after registration (invalidate cache).

---

## 13. Next Steps and Resources

- **Read the full paper:** [CZOA: A Unified Formalism...](https://arxiv.org/abs/xxxx)
- **Explore more examples:** `examples/` directory in the GitHub repo.
- **API Reference:** [https://czoi.readthedocs.io](https://czoi.readthedocs.io)
- **Join the community:** GitHub Discussions or Gitter channel.

**What to build next?**
- A smart city traffic management system (zones = districts, properties = density, neural = traffic predictor)
- A financial trading risk engine (zones = desks, properties = VaR, daemons = limit enforcers)
- An autonomous warehouse (zones = robots, properties = battery, neural = collision avoidance)

You now have everything you need to model and implement secure, intelligent organizational systems using CZOI Toolkit. Happy building!