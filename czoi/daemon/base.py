
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List

class Daemon(ABC):
    """Base class for all daemons."""
    def __init__(self, name: str, interval: float = 1.0):
        self.name = name
        self.interval = interval
        self.running = False
        self.logger = logging.getLogger(f"daemon.{name}")

    @abstractmethod
    async def check(self) -> List[str]:
        """Perform a check and return list of actions (or alerts)."""
        pass

    async def execute(self, action: str):
        """Execute a single action."""
        self.logger.info(f"Executing action: {action}")

    async def run(self):
        """Main loop."""
        self.running = True
        while self.running:
            try:
                actions = await self.check()
                for action in actions:
                    await self.execute(action)
            except Exception as e:
                self.logger.error(f"Error in check: {e}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self.running = False
