# example4_daemon.py
import asyncio
import random
from czoi.daemon.builtins import SecurityDaemon
from czoi.storage.sqlalchemy import Storage
from czoi.permission.engine import PermissionEngine

# Mock storage and permission engine (simplified)
class MockStorage:
    def get_recent_logs(self, limit):
        # Simulate recent access logs
        logs = []
        for i in range(limit):
            risk = random.random()
            logs.append({"user_id": f"user{i}", "operation_id": f"op{i}", "risk": risk})
        return logs

    def add_temporary_block(self, user_id, op_id):
        print(f"SECURITY: Blocked {user_id} from {op_id}")

class MockPermissionEngine:
    pass

# Custom SecurityDaemon that uses our mock storage
class TestSecurityDaemon(SecurityDaemon):
    async def check(self):
        logs = self.storage.get_recent_logs(10)
        actions = []
        for log in logs:
            # Use some risk logic (here we just use a random risk from mock)
            risk = log.get("risk", 0)
            if risk > 0.8:
                actions.append(f"BLOCK:{log['user_id']}:{log['operation_id']}")
        return actions

    async def execute(self, action):
        if action.startswith("BLOCK"):
            parts = action.split(":")
            if len(parts) == 3:
                _, user_id, op_id = parts
                self.storage.add_temporary_block(user_id, op_id)
        await super().execute(action)

async def main():
    storage = MockStorage()
    daemon = TestSecurityDaemon(storage, None, interval=1)  # check every second
    # Run for a few seconds
    asyncio.create_task(daemon.run())
    await asyncio.sleep(5)
    daemon.stop()
    print("Daemon stopped.")

asyncio.run(main())