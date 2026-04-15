# czoi/zones/composite.py
from typing import Dict, List, Any, Optional
from czoi.zones.base import Zone
from czoi.core.exceptions import PermissionDeniedError, ConstraintViolationError
from czoi.roles.user import User
from czoi.roles.role import Role
from czoi.core.types import Operation
from czoi_toolkit.czoi.toolkit.factory import CZOASystem

class CompositeZone(Zone):
    """
    Composite zone containing an embedded CZOA system.
    Enables arbitrary nesting depth.
    """

    def __init__(self, name: str, parent: Optional['CompositeZone'] = None):
        super().__init__(name, parent)
        self.embedded_system: Optional['CZOASystem'] = None
        self.aggregation_rules: Dict[str, str] = {}  # prop_name -> agg_fn

    @property
    def is_composite(self) -> bool:
        return True

    def embed_system(self, system: 'CZOASystem') -> None:
        """Embed a full CZOA system within this composite zone."""
        self.embedded_system = system
        # Adopt all zones from the embedded system as children
        for zone in system.zones.values():
            self.add_child(zone)

    def add_aggregation_rule(self, property_name: str, agg_fn: str) -> None:
        """Define how a parent property aggregates from children."""
        self.aggregation_rules[property_name] = agg_fn

    async def execute(self, operation: 'Operation', user: 'User',
                      context: Dict) -> Any:
        """Execute operation, routing to appropriate sub‑zone if needed."""
        zone_path = context.get('zone_path', [])
        if zone_path:
            target = self._navigate(zone_path)
            if target and target != self:
                return await target.execute(operation, user, context)

        # Execute at this composite zone
        active_role = context.get('active_role')
        if not active_role or not self._permission_engine:
            raise PermissionDeniedError("No active role or permission engine")

        if not await self._permission_engine.check_access(
            user, operation, self, context
        ):
            raise PermissionDeniedError(
                f"User {user.username} not authorized for {operation.name}"
            )

        state = await self._get_state()
        if operation.precondition and not operation.precondition(state):
            raise ConstraintViolationError(f"Precondition failed for {operation.name}")

        result = await operation.execute(self, context)

        if operation.postcondition and not operation.postcondition(state, result):
            raise ConstraintViolationError(f"Postcondition failed for {operation.name}")

        # Propagate property updates to parent if needed
        if operation.write_properties and self.parent:
            await self._propagate_updates(operation.write_properties, user, active_role)

        return result

    def _navigate(self, path: List[str]) -> Optional[Zone]:
        """Navigate zone tree by path (e.g., ['region', 'hospital', 'ward'])."""
        current: Zone = self
        for segment in path:
            next_zone = current.get_child(segment)
            if not next_zone:
                return None
            current = next_zone
        return current

    async def _get_state(self) -> Dict:
        """Get aggregated state including children's properties."""
        if self._property_store:
            state = await self._property_store.get_all(self)
        else:
            state = {p.name: p.value for p in self.properties.values()}

        # Aggregate child properties
        for prop_name, agg_fn in self.aggregation_rules.items():
            child_values = []
            for child in self.children:
                child_state = await child._get_state() if hasattr(child, '_get_state') else {}
                if prop_name in child_state:
                    child_values.append(child_state[prop_name])
            if child_values:
                if agg_fn == 'sum':
                    state[prop_name] = sum(child_values)
                elif agg_fn == 'avg':
                    state[prop_name] = sum(child_values) / len(child_values)
                elif agg_fn == 'max':
                    state[prop_name] = max(child_values)
                elif agg_fn == 'min':
                    state[prop_name] = min(child_values)
        return state

    async def _propagate_updates(self, affected_props: set, user: 'User', role: 'Role') -> None:
        """Propagate property changes up the zone hierarchy."""
        if not self.parent:
            return
        for prop in self.properties.values():
            if prop.id in affected_props and prop.name in self.parent.aggregation_rules:
                await self.parent._recompute_aggregated_property(prop.name, user, role)

    async def _recompute_aggregated_property(self, prop_name: str, user: 'User', role: 'Role') -> None:
        """Recompute an aggregated property from children."""
        agg_fn = self.aggregation_rules.get(prop_name)
        if not agg_fn:
            return
        child_values = []
        for child in self.children:
            if prop_name in child.properties:
                val = child.properties[prop_name].value
                if val is not None:
                    child_values.append(val)
        if child_values:
            if agg_fn == 'sum':
                new_value = sum(child_values)
            elif agg_fn == 'avg':
                new_value = sum(child_values) / len(child_values)
            elif agg_fn == 'max':
                new_value = max(child_values)
            elif agg_fn == 'min':
                new_value = min(child_values)
            else:
                return
            if self.properties[prop_name].value != new_value:
                self.properties[prop_name].set_value(new_value)
                if self._property_store:
                    await self._property_store.set(self, prop_name, new_value, user, role, None)