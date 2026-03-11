
from __future__ import annotations
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional, Set, Dict, Tuple, Any

class Zone:
    def __init__(self, name: str, parent: Optional['Zone'] = None):
        self.id: UUID = uuid4()
        self.name: str = name
        self.parent: Optional['Zone'] = parent
        self.children: List['Zone'] = []
        self.roles: List['Role'] = []
        self.applications: List['Application'] = []
        self.users: List['User'] = []
        self.created_at: datetime = datetime.utcnow()
        if parent:
            parent.add_child(self)

    def add_child(self, zone: 'Zone'):
        zone.parent = self
        self.children.append(zone)

    def get_path(self) -> List[str]:
        """Return zone path from root."""
        if self.parent:
            return self.parent.get_path() + [self.name]
        return [self.name]

    def __repr__(self) -> str:
        return f"<Zone {self.name} ({self.id})>"

class Role:
    def __init__(self, name: str, zone: Zone):
        self.id: UUID = uuid4()
        self.name: str = name
        self.zone: Zone = zone
        self.base_permissions: Set['Operation'] = set()
        self.senior_roles: List['Role'] = []  # higher in hierarchy
        self.junior_roles: List['Role'] = []
        self.created_at: datetime = datetime.utcnow()
        zone.roles.append(self)

    def grant_permission(self, operation: 'Operation'):
        self.base_permissions.add(operation)

    def add_senior(self, role: 'Role'):
        if role.zone != self.zone:
            raise ValueError("Senior roles must be in same zone")
        self.senior_roles.append(role)
        role.junior_roles.append(self)

    def __repr__(self) -> str:
        return f"<Role {self.name} in {self.zone.name}>"

class User:
    def __init__(self, username: str, email: str = None):
        self.id: UUID = uuid4()
        self.username: str = username
        self.email: str = email
        self.attributes: Dict[str, Any] = {}
        self.zone_role_assignments: Dict[UUID, List[Tuple[Role, float]]] = {}

    def assign_role(self, zone: Zone, role: Role, weight: float = 1.0):
        if role.zone != zone:
            raise ValueError("Role must belong to the zone")
        if zone.id not in self.zone_role_assignments:
            self.zone_role_assignments[zone.id] = []
        self.zone_role_assignments[zone.id].append((role, weight))

    def __repr__(self) -> str:
        return f"<User {self.username}>"

class Application:
    def __init__(self, name: str, owning_zone: Optional[Zone] = None):
        self.id: UUID = uuid4()
        self.name: str = name
        self.owning_zone: Optional[Zone] = owning_zone
        self.operations: List['Operation'] = []
        if owning_zone:
            owning_zone.applications.append(self)

    def add_operation(self, name: str, method: str = None) -> 'Operation':
        op = Operation(name, self, method)
        self.operations.append(op)
        return op

    def __repr__(self) -> str:
        return f"<Application {self.name}>"

class Operation:
    def __init__(self, name: str, app: Application, method: str = None):
        self.id: UUID = uuid4()
        self.name: str = name
        self.app: Application = app
        self.method: str = method  # e.g., 'GET', 'POST', 'EXECUTE'

    def __repr__(self) -> str:
        return f"<Operation {self.name} in {self.app.name}>"

class GammaMapping:
    """Inter-zone role mapping."""
    def __init__(self, child_zone: Zone, child_role: Role,
                 parent_zone: Zone, parent_role: Role,
                 weight: float = 1.0, priority: int = 0):
        self.child_zone = child_zone
        self.child_role = child_role
        self.parent_zone = parent_zone
        self.parent_role = parent_role
        self.weight = weight
        self.priority = priority

    def __repr__(self) -> str:
        return f"<Gamma {self.child_role.name} -> {self.parent_role.name}>"
