
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..core.system import System
from ..permission.engine import PermissionEngine
from ..storage.sqlalchemy import Storage

class SimulationEngine:
    def __init__(self, system: System, permission_engine: PermissionEngine,
                 storage: Storage):
        self.system = system
        self.permission_engine = permission_engine
        self.storage = storage
        self.logs: List[Dict[str, Any]] = []

    def run(self, duration: timedelta, step: timedelta = timedelta(seconds=1)):
        """Run simulation for given duration."""
        start_time = datetime.now()
        current_time = start_time
        end_time = start_time + duration
        users = list(self.system.users)
        operations = list(self.system.operations)
        zones = list(self.system.zones)
        while current_time < end_time:
            # Generate random access attempts
            for _ in range(random.randint(1, 10)):
                if not users or not operations or not zones:
                    break
                user = random.choice(users)
                operation = random.choice(operations)
                zone = random.choice(zones)
                context = {"time": current_time}
                allowed = self.permission_engine.decide(user, operation, zone, context)
                self.logs.append({
                    "timestamp": current_time.isoformat(),
                    "user": user.username,
                    "user_id": str(user.id),
                    "operation": operation.name,
                    "operation_id": str(operation.id),
                    "zone": zone.name,
                    "zone_id": str(zone.id),
                    "allowed": allowed
                })
            current_time += step

    def analyze(self) -> Dict[str, Any]:
        total = len(self.logs)
        allowed = sum(1 for log in self.logs if log["allowed"])
        denied = total - allowed
        return {
            "total_requests": total,
            "allowed": allowed,
            "denied": denied,
            "allow_rate": allowed / total if total else 0
        }

    def save_logs(self, path: str):
        import json
        with open(path, 'w') as f:
            json.dump(self.logs, f, indent=2)
