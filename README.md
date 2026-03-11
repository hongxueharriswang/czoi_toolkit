
# czoi: Constrained Zoned-Object Implementation Toolkit
`czoi` is a Python toolkit for building, simulating, and maintaining intelligent enterprise systems using the Constrained Zoned-Object Architecture (CZOA). It provides a unified framework integrating hierarchical zones, roles, permissions, neural components, embeddings, and continuous monitoring daemons.

## Features
- Core data models for Zones, Roles, Users, Applications, Operations
- Permission engine with intra-zone inheritance and inter-zone gamma mappings
- Constraint system for identity, trigger, goal, and access constraints
- Neural component framework for adaptive permission mining and anomaly detection
- Embedding service with vector similarity search
- Daemon framework for continuous monitoring and enforcement
- Simulation engine for testing system behavior
- CLI for administration
- Integrations with Django, Flask, FastAPI

## Installation
```bash
pip install czoi
```
For optional features:
```bash
pip install czoi[neural,api]
```

## Quick Start
```python
from czoi.core import System, Zone, Role, User, Application
from czoi.permission import PermissionEngine
from czoi.storage import Storage
# Create zones
root = Zone("Root")
hr = Zone("HR", parent=root)
# Create roles
hr_manager = Role("Manager", hr)
hr_assistant = Role("Assistant", hr)
hr_assistant.add_senior(hr_manager)
# Create application and operations
app = Application("HR App")
view_op = app.add_operation("view_employee")
edit_op = app.add_operation("edit_employee")
# Assign permissions
hr_assistant.grant_permission(view_op)
hr_manager.grant_permission(edit_op)
# Create user
alice = User("alice")
alice.assign_role(hr, hr_assistant)
# Save to database
storage = Storage("sqlite:///system.db")
# ... saving logic ...
# Check permission
engine = PermissionEngine(storage)
result = engine.decide(alice, view_op, hr)
print(result) # True
```

## Documentation
Full documentation at https://czoi.readthedocs.io

## License
MIT
