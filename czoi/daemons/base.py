# czoi/daemons/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
from uuid import uuid4
from czoi.core.types import DaemonAction, Operation
from czoi.zones.base import Zone
from czoi_toolkit.czoi.neural.components import AnomalyDetector


class Daemon(ABC):
    """Abstract base class for continuous monitoring daemons."""
    def __init__(self, name: str, priority: int = 50):
        self.name = name
        self.priority = priority
        self.id = uuid4()

    @abstractmethod
    async def monitor(self, zone: 'Zone', operation: Optional['Operation'],
                      props: Dict, context: Dict) -> DaemonAction:
        """Evaluate current state and return suggested action."""
        pass

    @abstractmethod
    async def act(self, action: DaemonAction, zone: 'Zone',
                  props: Dict, context: Dict) -> None:
        """Execute the action (e.g., block, alert, adapt)."""
        pass

class SecurityDaemon(Daemon):
    """Security monitoring daemon using anomaly detection."""
    def __init__(self, name: str, anomaly_detector: 'AnomalyDetector',
                 threshold: float = 0.8, priority: int = 100):
        super().__init__(name, priority)
        self.anomaly_detector = anomaly_detector
        self.threshold = threshold

    async def monitor(self, zone: 'Zone', operation: Optional['Operation'],
                      props: Dict, context: Dict) -> DaemonAction:
        features = {
            'zone_id': str(zone.id),
            'op_name': operation.name if operation else 'none',
            'user_id': str(context.get('user', {}).id) if context.get('user') else 'none',
            'props': props
        }
        risk = await self.anomaly_detector.forward({'features': features})
        if risk > self.threshold:
            return DaemonAction.BLOCK
        elif risk > self.threshold * 0.7:
            return DaemonAction.CHALLENGE
        return DaemonAction.ALLOW

    async def act(self, action: DaemonAction, zone: 'Zone',
                  props: Dict, context: Dict) -> None:
        # Logging and alerts would be implemented here
        pass

class PropertyDaemon(Daemon):
    """Daemon that enforces property invariants."""
    def __init__(self, name: str, property_name: str,
                 condition: Callable[[Any], bool],
                 corrective_action: Optional[Callable[['Zone', str], Awaitable[None]]] = None,
                 priority: int = 60):
        super().__init__(name, priority)
        self.property_name = property_name
        self.condition = condition
        self.corrective_action = corrective_action

    async def monitor(self, zone: 'Zone', operation: Optional['Operation'],
                      props: Dict, context: Dict) -> DaemonAction:
        value = props.get(self.property_name)
        if value is None:
            return DaemonAction.ALLOW
        if not self.condition(value):
            return DaemonAction.ADAPT
        return DaemonAction.ALLOW

    async def act(self, action: DaemonAction, zone: 'Zone',
                  props: Dict, context: Dict) -> None:
        if action == DaemonAction.ADAPT and self.corrective_action:
            await self.corrective_action(zone, self.property_name)