
from typing import List, Optional
from .models import Constraint, ConstraintType

class ConstraintManager:
    def __init__(self):
        self.constraints: List[Constraint] = []

    def add(self, constraint: Constraint):
        self.constraints.append(constraint)

    def remove(self, constraint_id):
        self.constraints = [c for c in self.constraints if c.id != constraint_id]

    def get_by_type(self, type: ConstraintType) -> List[Constraint]:
        return [c for c in self.constraints if c.type == type]

    def get_for_target(self, target: dict) -> List[Constraint]:
        """Get constraints matching a target specification."""
        # Simplified matching; real implementation would be more sophisticated
        result = []
        for c in self.constraints:
            matches = True
            for key, value in target.items():
                if key not in c.target or c.target[key] != value:
                    matches = False
                    break
            if matches:
                result.append(c)
        return result
