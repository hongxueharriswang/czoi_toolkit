# czoi/core/types.py
from enum import Enum

class PropertyType(Enum):
    """Supported data types for zone properties."""
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    VECTOR = "vector"
    EMBEDDING = "embedding"
    ENUM = "enum"

class PropagationPolicy(Enum):
    """Recursive permission propagation policies."""
    STRICT = 1      # child inherits all parent permissions automatically
    REQUEST = 2     # child must request; granted conditionally
    CAPABILITY = 3  # no automatic propagation; explicit capabilities only

class DaemonAction(Enum):
    """Actions that a daemon can return after monitoring."""
    ALLOW = 1
    BLOCK = 2
    CHALLENGE = 3
    ALERT = 4
    ADAPT = 5

class ConstraintType(Enum):
    """Types of constraints in the constraint system."""
    IDENTITY = "identity"
    TRIGGER = "trigger"
    GOAL = "goal"
    ACCESS = "access"