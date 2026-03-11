
from typing import Set, Dict, Optional
from ..core.models import User, Role, Zone, Operation
from ..storage.sqlalchemy import Storage

class PermissionEngine:
    def __init__(self, storage: Storage):
        self.storage = storage

    def get_effective_permissions(self, role: Role, zone: Zone) -> Set[Operation]:
        """Compute effective permissions for a role in a zone."""
        perms = set(role.base_permissions)
        # Intra-zone inheritance (junior roles)
        for junior in role.junior_roles:
            perms.update(junior.base_permissions)

        # Inter-zone gamma mappings (upwards)
        current_zone = zone
        visited = set()
        while current_zone and current_zone not in visited:
            visited.add(current_zone)
            mappings = self.storage.get_gamma_mappings(
                child_zone_id=current_zone.id,
                child_role_id=role.id
            )
            for mapping in mappings:
                parent_role = self.storage.get_role(mapping.parent_role_id)
                if parent_role:
                    perms.update(parent_role.base_permissions)
            current_zone = current_zone.parent
        return perms

    def decide(self, user: User, operation: Operation, zone: Zone,
               context: Optional[Dict] = None) -> bool:
        """Determine if user can perform operation in given zone context."""
        if zone.id not in user.zone_role_assignments:
            return False
        context = context or {}
        roles_with_weights = user.zone_role_assignments[zone.id]
        for role, weight in roles_with_weights:
            if weight <= 0:
                continue
            effective_perms = self.get_effective_permissions(role, zone)
            if operation in effective_perms:
                if self._check_access_constraints(user, role, zone, operation, context):
                    return True
        return False

    def _check_access_constraints(self, user, role, zone, operation, context):
        constraints = self.storage.get_constraints(
            type="access",
            target_roles=[role.id],
            target_operations=[operation.id]
        )
        for c in constraints:
            if not c.evaluate(context):
                return False
        return True
