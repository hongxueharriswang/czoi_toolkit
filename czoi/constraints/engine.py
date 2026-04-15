# czoi/constraints/engine.py
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any, Awaitable
from uuid import uuid4
from czoi.core.types import ConstraintType
from czoi.roles.user import User
from czoi.roles.role import Role
from czoi.zones.base import Zone
from czoi.core.types import Operation

class Constraint(ABC):
    """Base class for all constraints."""
    def __init__(self, name: str, constraint_type: ConstraintType):
        self.name = name
        self.type = constraint_type
        self.id = uuid4()

class IdentityConstraint(Constraint):
    """Invariant that must hold in all reachable states."""
    def __init__(self, name: str, condition: Callable[[Dict], bool]):
        super().__init__(name, ConstraintType.IDENTITY)
        self.condition = condition

    def check(self, state: Dict) -> bool:
        return self.condition(state)

class TriggerConstraint(Constraint):
    """Event-condition-action rule."""
    def __init__(self, name: str, event: str,
                 condition: Callable[[Dict], bool],
                 action: Callable[[Dict], Awaitable[None]]):
        super().__init__(name, ConstraintType.TRIGGER)
        self.event = event
        self.condition = condition
        self.action = action

class GoalConstraint(Constraint):
    """Optimization objective (maximization)."""
    def __init__(self, name: str, utility: Callable[[Dict], float]):
        super().__init__(name, ConstraintType.GOAL)
        self.utility = utility

class AccessConstraint(Constraint):
    """Access control rule (SoD, temporal, attribute, property-based)."""
    def __init__(self, name: str,
                 condition: Callable[['User', 'Role', 'Zone', 'Operation', Dict, Dict], bool]):
        super().__init__(name, ConstraintType.ACCESS)
        self.condition = condition

class ConstraintEngine:
    """
    Centralized constraint evaluation and enforcement.
    """
    def __init__(self):
        self.identity_constraints: List[IdentityConstraint] = []
        self.trigger_constraints: List[TriggerConstraint] = []
        self.goal_constraints: List[GoalConstraint] = []
        self.access_constraints: List[AccessConstraint] = []

    def add_identity(self, constraint: IdentityConstraint) -> None:
        self.identity_constraints.append(constraint)

    def add_trigger(self, constraint: TriggerConstraint) -> None:
        self.trigger_constraints.append(constraint)

    def add_goal(self, constraint: GoalConstraint) -> None:
        self.goal_constraints.append(constraint)

    def add_access(self, constraint: AccessConstraint) -> None:
        self.access_constraints.append(constraint)

    async def check_identity(self, state: Dict) -> bool:
        for c in self.identity_constraints:
            if not c.check(state):
                return False
        return True

    async def check_access(self, user: 'User', role: 'Role', zone: 'Zone',
                           operation: 'Operation', props: Dict, context: Dict) -> bool:
        for c in self.access_constraints:
            if not c.condition(user, role, zone, operation, props, context):
                return False
        return True

    async def evaluate_triggers(self, event: str, state: Dict) -> None:
        for c in self.trigger_constraints:
            if c.event == event and c.condition(state):
                await c.action(state)

    async def evaluate_goals(self, state: Dict) -> float:
        return sum(c.utility(state) for c in self.goal_constraints)