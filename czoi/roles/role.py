# czoi/roles/role.py
from dataclasses import dataclass, field
from typing import Set, List, Tuple
from uuid import UUID, uuid4

@dataclass
class Role:
    """
    Security role with base permissions and seniority hierarchy.
    """
    name: str
    zone_id: UUID
    base_permissions: Set[UUID] = field(default_factory=set)
    seniority_parents: List['Role'] = field(default_factory=list)
    inter_zone_mappings: List[Tuple[UUID, UUID, float, int]] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Role) and self.id == other.id