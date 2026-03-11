
from enum import Enum
from uuid import uuid4, UUID
from typing import Dict, Any, List
from ..utils.eval import safe_eval

class ConstraintType(str, Enum):
    IDENTITY = "identity"
    TRIGGER = "trigger"
    GOAL = "goal"
    ACCESS = "access"

class Constraint:
    def __init__(self, name: str, type: ConstraintType,
                 target: Dict, condition: str, priority: int = 0):
        self.id: UUID = uuid4()
        self.name = name
        self.type = type
        self.target = target
        self.condition = condition
        self.priority = priority

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition in given context using safe evaluator."""
        return safe_eval(self.condition, context)

    def __repr__(self) -> str:
        return f"<Constraint {self.name} ({self.type})>"
