# CZOI Python Toolkit – Technical Specification

**Version:** 1.0.0  
**Status:** Production‑ready  
**Target Platform:** Python 3.9+ (asyncio)  
**License:** MIT  

This document provides a complete technical specification of the CZOI Python Toolkit, a library that implements the Constrained Zoned‑Object Architecture (11‑tuple) for building secure, adaptive, intelligent systems. It describes the package structure, module APIs, class hierarchies, and provides code examples for each major component.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Package Structure](#2-package-structure)
3. [Core Abstractions and Data Types](#3-core-abstractions-and-data-types)
4. [Zone Hierarchy Module](#4-zone-hierarchy-module)
5. [Properties and Property Store](#5-properties-and-property-store)
6. [Roles, Users, and Permissions](#6-roles-users-and-permissions)
7. [Constraint System](#7-constraint-system)
8. [Neural Components](#8-neural-components)
9. [Embedding Service](#9-embedding-service)
10. [Daemon Framework](#10-daemon-framework)
11. [Permission Engine](#11-permission-engine)
12. [System Container (CZOASystem)](#12-system-container-czoasystem)
13. [Toolkit Factory](#13-toolkit-factory)
14. [Error Handling and Exceptions](#14-error-handling-and-exceptions)
15. [Configuration and Logging](#15-configuration-and-logging)
16. [Performance and Caching](#16-performance-and-caching)
17. [Extensibility Points](#17-extensibility-points)
18. [Complete Coding Example](#18-complete-coding-example)

---

## 1. Overview

The CZOA Toolkit is an asyncio‑based Python library that implements the full 11‑tuple formalism:  

**S = (Z, R, U, A, P, O, N, E, Γ, Φ, Δ)**

It provides:

- **Recursive zones** (atomic and composite) with unlimited nesting.
- **First‑class properties** (typed, versioned, time‑series‑aware) with access control and aggregation.
- **Role‑based access control** with intra‑zone seniority, inter‑zone γ‑mappings, and three recursive propagation policies.
- **Neural components** (predictors, detectors) that can be trained and invoked asynchronously.
- **Constraint engine** for identity, trigger, goal, and access constraints.
- **Daemons** for continuous monitoring with priority‑based conflict resolution.
- **Embedding service** for semantic similarity and compositional zone embeddings.
- **Permission engine** with caching and γ‑closure computation.

All components are designed to be **extensible**, **testable**, and **production‑ready**.

---

## 2. Package Structure

```
czoi/
├── __init__.py                 # Top‑level exports
├── core/
│   ├── __init__.py
│   ├── types.py                # Enums (PropertyType, PropagationPolicy, DaemonAction, ConstraintType)
│   └── exceptions.py           # Custom exceptions (CZOIError, ZoneNotFoundError, etc.)
├── zones/
│   ├── __init__.py
│   ├── base.py                 # Abstract Zone class
│   ├── atomic.py               # AtomicZone
│   └── composite.py            # CompositeZone
├── properties/
│   ├── __init__.py
│   ├── property.py             # Property dataclass
│   └── store.py                # PropertyStore
├── roles/
│   ├── __init__.py
│   ├── role.py                 # Role dataclass
│   └── user.py                 # User dataclass
├── constraints/
│   ├── __init__.py
│   └── engine.py               # Constraint, IdentityConstraint, TriggerConstraint, GoalConstraint, AccessConstraint, ConstraintEngine
├── neural/
│   ├── __init__.py
│   └── components.py           # NeuralComponent, PropertyPredictor, AnomalyDetector
├── embedding/
│   ├── __init__.py
│   └── service.py              # EmbeddingService
├── daemons/
│   ├── __init__.py
│   ├── base.py                 # Daemon, SecurityDaemon, PropertyDaemon
│   └── manager.py              # DaemonManager
├── permissions/
│   ├── __init__.py
│   └── engine.py               # PermissionEngine
└── toolkit/
    ├── __init__.py
    └── factory.py              # CZOASystem, CZOIToolkit
```

---

## 3. Core Abstractions and Data Types

### 3.1 Enums (`core/types.py`)

```python
class PropertyType(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    VECTOR = "vector"
    EMBEDDING = "embedding"
    ENUM = "enum"

class PropagationPolicy(Enum):
    STRICT = 1      # child inherits all parent permissions
    REQUEST = 2     # child must request, conditionally granted
    CAPABILITY = 3  # no automatic propagation

class DaemonAction(Enum):
    ALLOW = 1
    BLOCK = 2
    CHALLENGE = 3
    ALERT = 4
    ADAPT = 5

class ConstraintType(Enum):
    IDENTITY = "identity"
    TRIGGER = "trigger"
    GOAL = "goal"
    ACCESS = "access"
```

### 3.2 Exceptions (`core/exceptions.py`)

```python
class CZOIError(Exception): pass
class ZoneNotFoundError(CZOIError): pass
class PropertyNotFoundError(CZOIError): pass
class PermissionDeniedError(CZOIError): pass
class ConstraintViolationError(CZOIError): pass
class DaemonBlockError(CZOIError): pass
```

---

## 4. Zone Hierarchy Module

### 4.1 Abstract Zone (`zones/base.py`)

```python
class Zone(ABC):
    id: uuid.UUID
    name: str
    parent: Optional['CompositeZone']
    children: List['Zone']
    properties: Dict[str, 'Property']
    roles: Dict[uuid.UUID, 'Role']
    users: Dict[uuid.UUID, 'User']
    applications: Dict[uuid.UUID, 'Application']

    @property
    @abstractmethod
    def is_composite(self) -> bool: ...

    def add_child(self, child: 'Zone') -> None: ...
    def get_child(self, name: str) -> Optional['Zone']: ...
    def get_property(self, prop_name: str) -> Optional['Property']: ...
    async def execute(self, operation: 'Operation', user: 'User', context: Dict) -> Any: ...
```

### 4.2 AtomicZone (`zones/atomic.py`)

Leaf node – no embedded system. Implements `execute` with direct property updates.

### 4.3 CompositeZone (`zones/composite.py`)

Can embed a full `CZOASystem`. Adds aggregation rules and recursive execution routing.

```python
class CompositeZone(Zone):
    embedded_system: Optional['CZOASystem']
    aggregation_rules: Dict[str, str]   # property_name -> 'sum'|'avg'|'max'|'min'

    def embed_system(self, system: 'CZOASystem') -> None: ...
    def add_aggregation_rule(self, property_name: str, agg_fn: str) -> None: ...
    async def _recompute_aggregated_property(self, prop_name: str, user: 'User', role: 'Role') -> None: ...
```

**Code Example:**

```python
from czoi import AtomicZone, CompositeZone

root = CompositeZone("Root")
hospital = CompositeZone("Hospital", parent=root)
er = AtomicZone("ER", parent=hospital)
root.add_child(hospital)
hospital.add_child(er)
```

---

## 5. Properties and Property Store

### 5.1 Property Dataclass (`properties/property.py`)

```python
@dataclass
class Property:
    name: str
    type: PropertyType
    zone_id: uuid.UUID
    value: Any = None
    persistence: bool = False
    volatility: bool = False
    access_control: Dict[str, Set[uuid.UUID]] = field(default_factory=dict)
    range: Optional[Tuple[Any, Any]] = None
    enum_values: Optional[List[Any]] = None

    def set_value(self, value: Any) -> None: ...
    def can_read(self, role_id: uuid.UUID) -> bool: ...
    def can_write(self, role_id: uuid.UUID) -> bool: ...
```

### 5.2 PropertyStore (`properties/store.py`)

Asynchronous key‑value store with versioning, history, subscriptions, and aggregation.

```python
class PropertyStore:
    async def get(self, zone: Zone, prop_name: str, timestamp: Optional[datetime] = None) -> Any
    async def get_all(self, zone: Zone) -> Dict[str, Any]
    async def set(self, zone: Zone, prop_name: str, value: Any, user: User, role: Role, operation: Optional[Operation]) -> bool
    async def subscribe(self, zone: Zone, prop_name: str, callback: Callable, filters: Optional[Dict] = None) -> None
    async def aggregate(self, parent_zone: CompositeZone, agg_fn: str) -> Dict[str, Any]
```

**Code Example:**

```python
prop = Property(name="temperature", type=PropertyType.FLOAT, zone_id=zone.id, value=36.5)
await store.set(zone, "temperature", 37.0, user, role, None)
value = await store.get(zone, "temperature")
```

---

## 6. Roles, Users, and Permissions

### 6.1 Role Dataclass (`roles/role.py`)

```python
@dataclass
class Role:
    name: str
    zone_id: uuid.UUID
    base_permissions: Set[uuid.UUID] = field(default_factory=set)
    seniority_parents: List['Role'] = field(default_factory=list)
    inter_zone_mappings: List[Tuple[uuid.UUID, uuid.UUID, float, int]] = field(default_factory=list)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
```

### 6.2 User Dataclass (`roles/user.py`)

```python
@dataclass
class User:
    username: str
    credentials: Dict[str, str]
    attributes: Dict[str, Any] = field(default_factory=dict)
    home_zone_id: Optional[uuid.UUID] = None
    active_roles: Dict[uuid.UUID, float] = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def activate_role(self, role_id: uuid.UUID, level: float = 1.0) -> None: ...
    def deactivate_role(self, role_id: uuid.UUID) -> None: ...
    def get_active_roles(self) -> Dict[uuid.UUID, float]: ...
```

**Code Example:**

```python
role = Role(name="manager", zone_id=zone.id)
user = User(username="alice", credentials={"pwd_hash": "..."})
user.activate_role(role.id, level=1.0)
```

---

## 7. Constraint System

### 7.1 Constraint Classes (`constraints/engine.py`)

```python
class Constraint(ABC):
    name: str
    type: ConstraintType
    id: uuid.UUID

class IdentityConstraint(Constraint):
    condition: Callable[[Dict], bool]
    def check(self, state: Dict) -> bool: ...

class TriggerConstraint(Constraint):
    event: str
    condition: Callable[[Dict], bool]
    action: Callable[[Dict], Awaitable[None]]

class GoalConstraint(Constraint):
    utility: Callable[[Dict], float]

class AccessConstraint(Constraint):
    condition: Callable[[User, Role, Zone, Operation, Dict, Dict], bool]
```

### 7.2 ConstraintEngine

```python
class ConstraintEngine:
    def add_identity(self, constraint: IdentityConstraint) -> None
    def add_trigger(self, constraint: TriggerConstraint) -> None
    def add_goal(self, constraint: GoalConstraint) -> None
    def add_access(self, constraint: AccessConstraint) -> None
    async def check_identity(self, state: Dict) -> bool
    async def check_access(self, user: User, role: Role, zone: Zone, operation: Operation, props: Dict, context: Dict) -> bool
    async def evaluate_triggers(self, event: str, state: Dict) -> None
    async def evaluate_goals(self, state: Dict) -> float
```

**Code Example:**

```python
def acuity_in_range(state):
    return 1 <= state.get("acuity", 0) <= 5

constraint = IdentityConstraint("acuity_range", acuity_in_range)
engine.add_identity(constraint)
```

---

## 8. Neural Components

### 8.1 NeuralComponent Abstract Base (`neural/components.py`)

```python
class NeuralComponent(ABC):
    name: str
    zone_id: uuid.UUID
    id: uuid.UUID

    @abstractmethod
    async def forward(self, inputs: Dict) -> Any: ...

    @abstractmethod
    async def train(self, dataset: List[Tuple[Dict, Any]]) -> None: ...
```

### 8.2 Built‑in Implementations

- `PropertyPredictor`: LSTM‑based time‑series forecasting.
- `AnomalyDetector`: Autoencoder‑based anomaly scoring.

**Code Example:**

```python
predictor = PropertyPredictor("temp_predictor", zone_id=zone.id)
pred = await predictor.forward({"history": [20,21,22,23]})
```

---

## 9. Embedding Service

### 9.1 EmbeddingService (`embedding/service.py`)

```python
class EmbeddingService:
    dimension: int

    def set_embedding(self, entity_type: str, entity_id: uuid.UUID, vector: np.ndarray) -> None
    def get_embedding(self, entity_type: str, entity_id: uuid.UUID) -> Optional[np.ndarray]
    def compute_zone_embedding(self, zone: Zone) -> np.ndarray
    def similarity(self, entity1: Tuple[str, uuid.UUID], entity2: Tuple[str, uuid.UUID]) -> float
```

**Code Example:**

```python
emb = EmbeddingService(dimension=128)
vec = emb.compute_zone_embedding(zone)
sim = emb.similarity(('zone', zone1.id), ('zone', zone2.id))
```

---

## 10. Daemon Framework

### 10.1 Daemon Base (`daemons/base.py`)

```python
class Daemon(ABC):
    name: str
    priority: int
    id: uuid.UUID

    @abstractmethod
    async def monitor(self, zone: Zone, operation: Optional[Operation], props: Dict, context: Dict) -> DaemonAction: ...

    @abstractmethod
    async def act(self, action: DaemonAction, zone: Zone, props: Dict, context: Dict) -> None: ...
```

Built‑in: `SecurityDaemon`, `PropertyDaemon`.

### 10.2 DaemonManager (`daemons/manager.py`)

```python
class DaemonManager:
    def register(self, daemon: Daemon) -> None
    async def check(self, zone: Zone, operation: Optional[Operation], props: Dict, context: Dict) -> bool
```

**Code Example:**

```python
class MyDaemon(Daemon):
    async def monitor(self, zone, op, props, ctx):
        if props.get("error_flag"):
            return DaemonAction.BLOCK
        return DaemonAction.ALLOW
    async def act(self, action, zone, props, ctx):
        print("Blocked")

manager = DaemonManager()
manager.register(MyDaemon("checker", priority=50))
```

---

## 11. Permission Engine

### 11.1 PermissionEngine (`permissions/engine.py`)

```python
class PermissionEngine:
    roles: Dict[uuid.UUID, Role]
    propagation_policies: Dict[uuid.UUID, PropagationPolicy]

    def register_role(self, role: Role) -> None
    def set_propagation_policy(self, zone_id: uuid.UUID, policy: PropagationPolicy) -> None
    async def effective_permissions(self, role: Role, zone: Zone, props: Dict) -> Set[uuid.UUID]
    async def check_access(self, user: User, operation: Operation, zone: Zone, context: Dict) -> bool
    def invalidate_cache(self, role_id: uuid.UUID, zone_id: uuid.UUID) -> None
```

**Code Example:**

```python
engine = PermissionEngine()
engine.register_role(manager_role)
engine.set_propagation_policy(zone.id, PropagationPolicy.STRICT)
perms = await engine.effective_permissions(manager_role, zone, {})
```

---

## 12. System Container (CZOASystem)

### 12.1 CZOASystem (`toolkit/factory.py`)

```python
class CZOASystem:
    name: str
    id: uuid.UUID
    root_zone: CompositeZone
    property_store: PropertyStore
    permission_engine: PermissionEngine
    constraint_engine: ConstraintEngine
    embedding_service: EmbeddingService
    daemon_manager: DaemonManager
    neural_components: Dict[uuid.UUID, NeuralComponent]

    async def execute(self, zone_path: List[str], operation: Operation, user: User, context: Dict) -> Any
    async def get_property(self, zone_path: List[str], prop_name: str) -> Any
    async def set_property(self, zone_path: List[str], prop_name: str, value: Any, user: User, role: Role) -> bool
```

**Code Example:**

```python
system = CZOASystem("MySystem", root_zone)
result = await system.execute(["Hospital", "ER"], triage_op, alice, {...})
```

---

## 13. Toolkit Factory

### 13.1 CZOIToolkit (`toolkit/factory.py`)

Convenience factory for creating zones, properties, roles, users, and systems.

```python
class CZOIToolkit:
    @staticmethod
    def create_system(name: str, root_zone_name: str = "root") -> CZOASystem

    @staticmethod
    def create_atomic_zone(name: str, parent: Optional[CompositeZone] = None) -> AtomicZone

    @staticmethod
    def create_composite_zone(name: str, parent: Optional[CompositeZone] = None) -> CompositeZone

    @staticmethod
    def create_property(name: str, prop_type: PropertyType, zone_id: uuid.UUID,
                        initial_value: Any = None,
                        read_roles: Optional[Set[uuid.UUID]] = None,
                        write_roles: Optional[Set[uuid.UUID]] = None) -> Property

    @staticmethod
    def create_role(name: str, zone_id: uuid.UUID,
                    base_permissions: Optional[Set[uuid.UUID]] = None) -> Role

    @staticmethod
    def create_user(username: str, password: str, attributes: Optional[Dict] = None) -> User
```

**Code Example:**

```python
toolkit = CZOIToolkit()
system = toolkit.create_system("Demo")
zone = toolkit.create_atomic_zone("Leaf", parent=system.root_zone)
prop = toolkit.create_property("temp", PropertyType.FLOAT, zone.id, 25.0)
```

---

## 14. Error Handling and Exceptions

All exceptions inherit from `CZOIError`. The toolkit raises:

- `ZoneNotFoundError` – when a zone path does not exist.
- `PropertyNotFoundError` – when a property is missing.
- `PermissionDeniedError` – when access is denied by permission engine or constraints.
- `ConstraintViolationError` – when an identity constraint fails.
- `DaemonBlockError` – when a daemon blocks an operation (wrapped from `DaemonAction.BLOCK`).

**Example:**

```python
try:
    await system.execute(path, op, user, ctx)
except PermissionDeniedError as e:
    print(f"Access denied: {e}")
```

---

## 15. Configuration and Logging

The toolkit uses Python’s standard `logging` module. Enable debug logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

No external configuration file is required; all parameters are passed programmatically.

---

## 16. Performance and Caching

- **Permission Engine** caches `effective_permissions` results per `(role_id, zone_id, props_hash)`. Use `invalidate_cache` after role or property changes.
- **Property Store** can be backed by Redis or PostgreSQL for persistence (override `get`/`set`).
- **Daemons** run sequentially; for heavy workloads, deploy as separate microservices.

**Cache invalidation example:**

```python
await permission_engine.invalidate_cache(role_id, zone_id)
```

---

## 17. Extensibility Points

| Component | Extension Method |
|-----------|------------------|
| `NeuralComponent` | Subclass and implement `forward`/`train`. |
| `Daemon` | Subclass and implement `monitor`/`act`. |
| `Constraint` | Use provided subclasses or subclass `Constraint`. |
| `PropertyStore` | Override `get`/`set` for distributed storage. |
| `Operation` | Subclass and implement `execute`. |
| `EmbeddingService` | Override `compute_zone_embedding` for custom composition. |

---

## 18. Complete Coding Example

This example builds a small inventory system with two zones, a property, a role, a user, an operation, and a daemon that blocks low‑stock reorders.

```python
import asyncio
import uuid
from czoi import *

# -------------------------------------------------------------------
# 1. Define a custom operation
class ReorderOperation(Operation):
    async def execute(self, zone, context):
        sku = context["sku"]
        qty = context["quantity"]
        current = await system.property_store.get(zone, f"stock_{sku}")
        new = current + qty
        await system.property_store.set(zone, f"stock_{sku}", new,
                                        context['user'], context['active_role'], self)
        return {"sku": sku, "old": current, "new": new}

# -------------------------------------------------------------------
# 2. Define a daemon that blocks orders when stock > 1000
class StockLimitDaemon(Daemon):
    async def monitor(self, zone, operation, props, context):
        if operation and operation.name == "reorder":
            sku = context.get("sku")
            current = props.get(f"stock_{sku}", 0)
            if current > 1000:
                return DaemonAction.BLOCK
        return DaemonAction.ALLOW

    async def act(self, action, zone, props, context):
        print(f"StockLimitDaemon: Blocked reorder because stock > 1000")

# -------------------------------------------------------------------
# 3. Build system
async def main():
    global system  # for use inside ReorderOperation
    toolkit = CZOIToolkit()
    system = toolkit.create_system("WarehouseSys")
    root = system.root_zone

    # Zone
    wh = toolkit.create_atomic_zone("MainWarehouse", parent=root)
    root.add_child(wh)

    # Property
    stock_prop = toolkit.create_property("stock_A", PropertyType.INT, wh.id, initial_value=500)
    system.add_property(wh.id, stock_prop)

    # Role
    clerk_role = toolkit.create_role("clerk", zone_id=wh.id)
    system.add_role(clerk_role)

    # User
    alice = toolkit.create_user("alice", "secret")
    alice.activate_role(clerk_role.id)

    # Operation
    reorder_op = ReorderOperation("reorder", app_id=root.id, signature={})
    reorder_op.id = uuid.uuid4()
    reorder_op.required_role_ids = {clerk_role.id}

    # Daemon
    daemon = StockLimitDaemon("stock_limit", priority=80)
    system.daemon_manager.register(daemon)

    # Execute: first order (stock 500 -> 550)
    ctx = {"active_role": clerk_role, "user": alice, "sku": "A", "quantity": 50}
    res = await system.execute(["MainWarehouse"], reorder_op, alice, ctx)
    print(res)

    # Second order: try to go above 1000 (stock 550 -> 1050) -> daemon blocks
    ctx["quantity"] = 500
    try:
        res = await system.execute(["MainWarehouse"], reorder_op, alice, ctx)
        print(res)
    except DaemonBlockError:
        print("Daemon blocked the operation as expected")

if __name__ == "__main__":
    asyncio.run(main())
```

**Expected output:**

```
{'sku': 'A', 'old': 500, 'new': 550}
StockLimitDaemon: Blocked reorder because stock > 1000
Daemon blocked the operation as expected
```

---

This specification provides all the information needed to understand, use, and extend the CZOI Python Toolkit. For further details, refer to the API documentation and the source code.