# czoi/toolkit/factory.py
import hashlib
from typing import Dict, Set, Optional, Any
from uuid import UUID
from czoi.zones.atomic import AtomicZone
from czoi.zones.composite import CompositeZone
from czoi.properties.property import Property
from czoi.properties.store import PropertyStore
from czoi.roles.role import Role
from czoi.roles.user import User
from czoi.constraints.engine import ConstraintEngine
from czoi.embedding.service import EmbeddingService
from czoi.daemons.manager import DaemonManager
from czoi.permissions.engine import PermissionEngine
from czoi.core.types import PropertyType
from czoi.core.types import Operation
from czoi.core.exceptions import ZoneNotFoundError
from czoi.zones.base import Zone
from czoi.toolkit import CZOASystem
from czoi.neural.components import NeuralComponent

class CZOASystem:
    """Main CZOA system container."""
    def __init__(self, name: str, root_zone: CompositeZone):
        self.name = name
        self.id = UUID(int=0)  # placeholder
        self.root_zone = root_zone
        self.zones: Dict[UUID, 'Zone'] = {}
        self.property_store = PropertyStore()
        self.permission_engine = PermissionEngine()
        self.constraint_engine = ConstraintEngine()
        self.embedding_service = EmbeddingService()
        self.daemon_manager = DaemonManager()
        self.neural_components: Dict[UUID, 'NeuralComponent'] = {}

        # Register all zones recursively
        self._register_zone(root_zone)
        # Inject dependencies
        for zone in self.zones.values():
            zone._property_store = self.property_store
            zone._permission_engine = self.permission_engine
            zone._daemon_manager = self.daemon_manager
        self.permission_engine.constraint_engine = self.constraint_engine

    def _register_zone(self, zone: 'Zone') -> None:
        self.zones[zone.id] = zone
        for child in zone.children:
            self._register_zone(child)
        if hasattr(zone, 'embedded_system') and zone.embedded_system:
            for subzone in zone.embedded_system.zones.values():
                self._register_zone(subzone)

    def add_property(self, zone_id: UUID, prop: Property) -> None:
        zone = self.zones.get(zone_id)
        if zone:
            zone.properties[prop.name] = prop

    def add_role(self, role: Role) -> None:
        self.permission_engine.register_role(role)

    def add_neural_component(self, component: 'NeuralComponent') -> None:
        self.neural_components[component.id] = component

    async def execute(self, zone_path: list, operation: 'Operation',
                      user: User, context: Dict) -> Any:
        zone = self._navigate(zone_path)
        if not zone:
            raise ZoneNotFoundError(f"Zone path {zone_path} not found")
        context['zone_path'] = zone_path
        return await zone.execute(operation, user, context)

    def _navigate(self, path: list) -> Optional['Zone']:
        current = self.root_zone
        for segment in path:
            current = current.get_child(segment)
            if not current:
                return None
        return current

    async def get_property(self, zone_path: list, prop_name: str) -> Any:
        zone = self._navigate(zone_path)
        if not zone:
            return None
        return await self.property_store.get(zone, prop_name)

    async def set_property(self, zone_path: list, prop_name: str,
                           value: Any, user: User, role: Role) -> bool:
        zone = self._navigate(zone_path)
        if not zone:
            return False
        return await self.property_store.set(zone, prop_name, value, user, role, None)

class CZOIToolkit:
    """Factory and utility class for creating CZOA systems."""
    @staticmethod
    def create_system(name: str, root_zone_name: str = "root") -> CZOASystem:
        root = CompositeZone(root_zone_name)
        return CZOASystem(name, root)

    @staticmethod
    def create_atomic_zone(name: str, parent: Optional[CompositeZone] = None) -> AtomicZone:
        return AtomicZone(name, parent)

    @staticmethod
    def create_composite_zone(name: str, parent: Optional[CompositeZone] = None) -> CompositeZone:
        return CompositeZone(name, parent)

    @staticmethod
    def create_property(name: str, prop_type: PropertyType, zone_id: UUID,
                        initial_value: Any = None,
                        read_roles: Optional[Set[UUID]] = None,
                        write_roles: Optional[Set[UUID]] = None) -> Property:
        access_control = {}
        if read_roles:
            access_control['read'] = read_roles
        if write_roles:
            access_control['write'] = write_roles
        prop = Property(
            name=name,
            type=prop_type,
            zone_id=zone_id,
            value=initial_value,
            access_control=access_control
        )
        if initial_value is not None:
            prop.set_value(initial_value)
        return prop

    @staticmethod
    def create_role(name: str, zone_id: UUID,
                    base_permissions: Optional[Set[UUID]] = None) -> Role:
        return Role(
            name=name,
            zone_id=zone_id,
            base_permissions=base_permissions or set()
        )

    @staticmethod
    def create_user(username: str, password: str,
                    attributes: Optional[Dict] = None) -> User:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return User(
            username=username,
            credentials={'password_hash': password_hash},
            attributes=attributes or {}
        )