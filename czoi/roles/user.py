# czoi/roles/user.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

@dataclass
class User:
    """
    System user with authentication and attributes.
    """
    username: str
    credentials: Dict[str, str]
    attributes: Dict[str, Any] = field(default_factory=dict)
    home_zone_id: Optional[UUID] = None
    active_roles: Dict[UUID, float] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)

    def activate_role(self, role_id: UUID, level: float = 1.0) -> None:
        """Activate a role with given level (0-1)."""
        if 0 <= level <= 1:
            self.active_roles[role_id] = level
        else:
            raise ValueError("Activation level must be between 0 and 1")

    def deactivate_role(self, role_id: UUID) -> None:
        """Deactivate a role."""
        self.active_roles.pop(role_id, None)

    def get_active_roles(self) -> Dict[UUID, float]:
        """Get currently active roles with levels."""
        return self.active_roles.copy()