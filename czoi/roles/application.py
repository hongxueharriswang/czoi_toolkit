# czoi/roles/application.py
from dataclasses import dataclass, field
from typing import Set, Dict
from uuid import UUID, uuid4

@dataclass
class Application:
    """
    An application that provides operations in the system.
    """
    name: str
    zone_id: UUID
    description: str = ""
    operations: Set[UUID] = field(default_factory=set)  # Operation IDs
    metadata: Dict[str, str] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)