# czoi/properties/store.py
import asyncio
from typing import Dict, List, Tuple, Any, Optional, Callable
from datetime import datetime, timezone
from uuid import UUID
from collections import defaultdict
from czoi.zones.base import Zone, CompositeZone
from czoi.roles.user import User
from czoi.roles.role import Role
from czoi.core.types import Operation

class PropertyStore:
    """
    Distributed, versioned, time-series-aware property store.
    """

    def __init__(self):
        self._current: Dict[Tuple[UUID, str], Tuple[Any, int, datetime]] = {}
        self._history: List[Dict] = []
        self._subscriptions: Dict[Tuple[UUID, str], List[Tuple[Callable, Optional[Dict]]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def get(self, zone: 'Zone', prop_name: str,
                  timestamp: Optional[datetime] = None) -> Any:
        """Get current or historical property value."""
        key = (zone.id, prop_name)
        if timestamp is None:
            data = self._current.get(key)
            return data[0] if data else None
        else:
            for entry in reversed(self._history):
                if (entry['zone_id'] == zone.id and
                    entry['prop_name'] == prop_name and
                    entry['valid_from'] <= timestamp and
                    (entry['valid_to'] is None or entry['valid_to'] > timestamp)):
                    return entry['value']
            return None

    async def get_all(self, zone: 'Zone') -> Dict[str, Any]:
        """Get all current properties for a zone."""
        result = {}
        for (zid, pname), (value, _, _) in self._current.items():
            if zid == zone.id:
                result[pname] = value
        return result

    async def set(self, zone: 'Zone', prop_name: str, value: Any,
                  user: 'User', role: 'Role', operation: Optional['Operation']) -> bool:
        """Set a property value with permission checking and audit logging."""
        prop = zone.get_property(prop_name)
        if not prop:
            return False
        if not prop.can_write(role.id):
            return False

        async with self._lock:
            key = (zone.id, prop_name)
            old_value = self._current.get(key, (None, 0, None))[0]
            now = datetime.now(timezone.utc)
            new_version = self._current.get(key, (None, 0, None))[1] + 1

            self._current[key] = (value, new_version, now)

            # Close previous history entry
            for entry in self._history:
                if (entry['zone_id'] == zone.id and
                    entry['prop_name'] == prop_name and
                    entry['valid_to'] is None):
                    entry['valid_to'] = now
                    break

            self._history.append({
                'zone_id': zone.id,
                'prop_name': prop_name,
                'value': value,
                'version': new_version,
                'valid_from': now,
                'valid_to': None,
                'updated_by': user.id if user else None,
                'role_used': role.id if role else None
            })

            prop.set_value(value)
            await self._notify(zone, prop_name, old_value, value)

        return True

    async def subscribe(self, zone: 'Zone', prop_name: str, callback: Callable,
                        filters: Optional[Dict] = None) -> None:
        """Subscribe to property changes."""
        key = (zone.id, prop_name)
        self._subscriptions[key].append((callback, filters))

    async def _notify(self, zone: 'Zone', prop_name: str, old_val: Any, new_val: Any) -> None:
        key = (zone.id, prop_name)
        for callback, filters in self._subscriptions.get(key, []):
            if filters and 'condition' in filters:
                # Simple filter evaluation – use safe eval in production
                if not eval(filters['condition'], {'old': old_val, 'new': new_val}):
                    continue
            if asyncio.iscoroutinefunction(callback):
                await callback(zone, prop_name, old_val, new_val)
            else:
                callback(zone, prop_name, old_val, new_val)

    async def aggregate(self, parent_zone: 'CompositeZone', agg_fn: str) -> Dict[str, Any]:
        """Compute aggregated properties for a composite zone."""
        result = {}
        for prop_name, fn_name in parent_zone.aggregation_rules.items():
            if fn_name != agg_fn:
                continue
            child_values = []
            for child in parent_zone.children:
                val = await self.get(child, prop_name)
                if val is not None:
                    child_values.append(val)
            if child_values:
                if agg_fn == 'sum':
                    result[prop_name] = sum(child_values)
                elif agg_fn == 'avg':
                    result[prop_name] = sum(child_values) / len(child_values)
                elif agg_fn == 'max':
                    result[prop_name] = max(child_values)
                elif agg_fn == 'min':
                    result[prop_name] = min(child_values)
        return result