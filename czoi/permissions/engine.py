# czoi/permissions/engine.py
from typing import Dict, Set, Tuple, Optional
from uuid import UUID
from czoi.core.types import PropagationPolicy
from czoi.roles.user import User
from czoi.roles.role import Role
from czoi.zones.base import Zone
from czoi.core.types import Operation

class PermissionEngine:
    """Central permission evaluation engine with recursive propagation."""
    def __init__(self):
        self.roles: Dict[UUID, 'Role'] = {}
        self.propagation_policies: Dict[UUID, PropagationPolicy] = {}
        self._cache: Dict[Tuple[UUID, UUID, str], Set[UUID]] = {}
        self.constraint_engine = None

    def register_role(self, role: 'Role') -> None:
        self.roles[role.id] = role

    def set_propagation_policy(self, zone_id: UUID, policy: PropagationPolicy) -> None:
        self.propagation_policies[zone_id] = policy

    async def effective_permissions(self, role: 'Role', zone: 'Zone',
                                    props: Dict) -> Set[UUID]:
        cache_key = (role.id, zone.id, frozenset(props.items()).__str__())
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        perms = set(role.base_permissions)
        perms.update(await self._get_seniority_permissions(role, zone))
        perms.update(await self._get_gamma_permissions(role, zone))

        policy = self.propagation_policies.get(zone.id, PropagationPolicy.STRICT)
        perms.update(await self._recursive_propagate(role, zone, policy, props))

        self._cache[cache_key] = perms.copy()
        return perms

    async def _get_seniority_permissions(self, role: 'Role', zone: 'Zone') -> Set[UUID]:
        perms = set()
        visited = set()
        queue = list(role.seniority_parents)
        while queue:
            parent = queue.pop()
            if parent.id in visited:
                continue
            visited.add(parent.id)
            perms.update(parent.base_permissions)
            queue.extend(parent.seniority_parents)
        return perms

    async def _get_gamma_permissions(self, role: 'Role', zone: 'Zone') -> Set[UUID]:
        perms = set()
        visited = set()
        queue = [(role, zone)]
        while queue:
            r, z = queue.pop()
            key = (r.id, z.id)
            if key in visited:
                continue
            visited.add(key)
            perms.update(r.base_permissions)
            for (target_zid, target_rid, weight, _) in r.inter_zone_mappings:
                if weight > 0:
                    target_role = self.roles.get(target_rid)
                    if target_role:
                        queue.append((target_role, zone))  # simplified
        return perms

    async def _recursive_propagate(self, role: 'Role', zone: 'Zone',
                                   policy: PropagationPolicy, props: Dict) -> Set[UUID]:
        if not zone.parent:
            return set()
        parent_perms = await self.effective_permissions(role, zone.parent, props)
        if policy == PropagationPolicy.STRICT:
            return parent_perms
        elif policy == PropagationPolicy.REQUEST:
            # In production, check request conditions stored in zone metadata
            return parent_perms
        return set()

    async def check_access(self, user: 'User', operation: 'Operation',
                           zone: 'Zone', context: Dict) -> bool:
        active_role_id = None
        max_level = 0.0
        for rid, level in user.active_roles.items():
            if level > max_level:
                max_level = level
                active_role_id = rid
        if active_role_id is None:
            return False
        role = self.roles.get(active_role_id)
        if not role:
            return False
        props = await zone._property_store.get_all(zone) if zone._property_store else {}
        perms = await self.effective_permissions(role, zone, props)
        if operation.id not in perms:
            return False
        if self.constraint_engine:
            if not await self.constraint_engine.check_access(
                user, role, zone, operation, props, context):
                return False
        return True

    def invalidate_cache(self, role_id: UUID, zone_id: UUID) -> None:
        keys_to_delete = [k for k in self._cache if k[0] == role_id and k[1] == zone_id]
        for k in keys_to_delete:
            del self._cache[k]