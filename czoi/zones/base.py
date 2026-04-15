# czoi/zones/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from czoi.operations import Operation

if TYPE_CHECKING:
    from czoi.zones.composite import CompositeZone
    from czoi.properties.property import Property
    from czoi.roles.role import Role
    from czoi.roles.user import User
    from czoi.roles.application import Application
    from czoi.permissions.engine import PermissionEngine
    from czoi.daemons.manager import DaemonManager
    from czoi.properties.store import PropertyStore
    from czoi.operations.operation import Operation

class Zone(ABC):
    """Abstract base class for all zones (atomic and composite)."""

    def __init__(self, name: str, parent: Optional['CompositeZone'] = None):
        self.id = uuid4()
        self.name = name
        self.parent = parent
        self.children: List['Zone'] = []
        self.properties: Dict[str, 'Property'] = {}
        self.roles: Dict[UUID, 'Role'] = {}
        self.users: Dict[UUID, 'User'] = {}
        self.applications: Dict[UUID, 'Application'] = {}
        # These will be injected by the system
        self._property_store: Optional['PropertyStore'] = None
        self._permission_engine: Optional['PermissionEngine'] = None
        self._daemon_manager: Optional['DaemonManager'] = None

    @property
    @abstractmethod
    def is_composite(self) -> bool:
        """Return True if this zone is composite, False if atomic."""
        pass

    def add_child(self, child: 'Zone') -> None:
        """Add a child zone to this zone."""
        self.children.append(child)
        child.parent = self

    def get_child(self, name: str) -> Optional['Zone']:
        """Retrieve a child zone by name."""
        for child in self.children:
            if child.name == name:
                return child
        return None

    def get_property(self, prop_name: str) -> Optional['Property']:
        """Get a property definition by name."""
        return self.properties.get(prop_name)

    @abstractmethod
    async def execute(self, operation: 'Operation', user: 'User',
                      context: Dict) -> Any:
        """Execute an operation within this zone."""
        pass