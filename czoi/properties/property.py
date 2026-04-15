# czoi/properties/property.py
from dataclasses import dataclass, field
from typing import Any, Dict, Set, Tuple, List, Optional
from uuid import UUID, uuid4
from czoi.core.types import PropertyType

@dataclass
class Property:
    """
    A first-class zone property representing state.
    """
    name: str
    type: PropertyType
    zone_id: UUID
    value: Any = None
    persistence: bool = False
    volatility: bool = False
    access_control: Dict[str, Set[UUID]] = field(default_factory=dict)
    range: Optional[Tuple[Any, Any]] = None
    enum_values: Optional[List[Any]] = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        if self.type == PropertyType.ENUM and self.enum_values is None:
            raise ValueError("Enum property must specify enum_values")
        self._validate_value(self.value)

    def _validate_value(self, value: Any) -> None:
        """Validate value against type and constraints."""
        if value is None:
            return
        if self.type == PropertyType.INT:
            if not isinstance(value, int):
                raise TypeError(f"Expected int, got {type(value)}")
            if self.range and not (self.range[0] <= value <= self.range[1]):
                raise ValueError(f"Value {value} out of range {self.range}")
        elif self.type == PropertyType.FLOAT:
            if not isinstance(value, (int, float)):
                raise TypeError(f"Expected float, got {type(value)}")
            if self.range and not (self.range[0] <= value <= self.range[1]):
                raise ValueError(f"Value {value} out of range {self.range}")
        elif self.type == PropertyType.BOOL:
            if not isinstance(value, bool):
                raise TypeError(f"Expected bool, got {type(value)}")
        elif self.type == PropertyType.STRING:
            if not isinstance(value, str):
                raise TypeError(f"Expected str, got {type(value)}")
        elif self.type == PropertyType.VECTOR:
            if not isinstance(value, (list, tuple)) and not hasattr(value, '__array__'):
                raise TypeError(f"Expected list or array, got {type(value)}")
        elif self.type == PropertyType.ENUM:
            if value not in self.enum_values:
                raise ValueError(f"Value {value} not in enum {self.enum_values}")

    def set_value(self, value: Any) -> None:
        """Set and validate new value."""
        self._validate_value(value)
        self.value = value

    def can_read(self, role_id: UUID) -> bool:
        """Check if role has read access."""
        return role_id in self.access_control.get('read', set())

    def can_write(self, role_id: UUID) -> bool:
        """Check if role has write access."""
        return role_id in self.access_control.get('write', set())