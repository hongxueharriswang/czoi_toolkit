# czoi/daemons/manager.py
import asyncio
from typing import Dict, List, Tuple, Optional
from czoi.daemons.base import Daemon, DaemonAction
from czoi.zones.base import Zone
from czoi.core.types import Operation

class DaemonManager:
    """Manages all daemons, handles conflict resolution."""
    def __init__(self):
        self.daemons: List[Daemon] = []
        self._lock = asyncio.Lock()

    def register(self, daemon: Daemon) -> None:
        self.daemons.append(daemon)

    async def check(self, zone: 'Zone', operation: Optional['Operation'],
                    props: Dict, context: Dict) -> bool:
        """Check all daemons and resolve actions. Returns True if allowed."""
        actions = []
        for daemon in self.daemons:
            action = await daemon.monitor(zone, operation, props, context)
            actions.append((daemon, action))
        return await self._resolve(actions, zone, props, context)

    async def _resolve(self, actions: List[Tuple[Daemon, DaemonAction]],
                       zone: 'Zone', props: Dict, context: Dict) -> bool:
        # If any BLOCK, block immediately
        for daemon, action in actions:
            if action == DaemonAction.BLOCK:
                await daemon.act(action, zone, props, context)
                return False

        # Find highest priority non-ALLOW action
        best_daemon = None
        best_action = DaemonAction.ALLOW
        for daemon, action in actions:
            if action != DaemonAction.ALLOW:
                if best_daemon is None or daemon.priority > best_daemon.priority:
                    best_daemon = daemon
                    best_action = action

        if best_daemon:
            await best_daemon.act(best_action, zone, props, context)
            if best_action == DaemonAction.CHALLENGE:
                return False
        return True