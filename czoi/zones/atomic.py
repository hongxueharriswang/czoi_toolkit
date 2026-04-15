# czoi/zones/atomic.py
from typing import Dict, Any
from czoi.zones.base import Zone
from czoi.core.exceptions import PermissionDeniedError, ConstraintViolationError
from czoi.roles.user import User
from czoi.operations import Operation

class AtomicZone(Zone):
    """
    Atomic zone with no embedded CZOA instance.
    Leaves of the recursion hierarchy.
    """

    @property
    def is_composite(self) -> bool:
        return False

    async def execute(self, operation: 'Operation', user: 'User',
                      context: Dict) -> Any:
        """Execute operation directly in this atomic zone."""
        active_role = context.get('active_role')
        if not active_role or not self._permission_engine:
            raise PermissionDeniedError("No active role or permission engine")

        # Check permissions
        if not await self._permission_engine.check_access(
            user, operation, self, context
        ):
            raise PermissionDeniedError(
                f"User {user.username} not authorized for {operation.name}"
            )

        # Precondition check
        state = await self._get_state()
        if operation.precondition and not operation.precondition(state):
            raise ConstraintViolationError(f"Precondition failed for {operation.name}")

        # Execute
        result = await operation.execute(self, context)

        # Postcondition check
        if operation.postcondition and not operation.postcondition(state, result):
            raise ConstraintViolationError(f"Postcondition failed for {operation.name}")

        # Update property store if property changes occurred
        if self._property_store:
            for prop in operation.write_properties:
                if prop in self.properties:
                    await self._property_store.set(
                        self, self.properties[prop].name,
                        self.properties[prop].value, user, active_role, operation
                    )

        return result

    async def _get_state(self) -> Dict:
        """Get current property state."""
        if self._property_store:
            return await self._property_store.get_all(self)
        return {p.name: p.value for p in self.properties.values()}