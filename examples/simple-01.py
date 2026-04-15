# example1_basic.py
from czoi.core import System, Zone, Role, User, Application, Operation
from czoi.permission import PermissionEngine
from czoi.storage.sqlalchemy import Storage

# 1. Create system and zones
system = System()
root = Zone("Company")
hr = Zone("HR", parent=root)
system.add_zone(root)
system.add_zone(hr)

# 2. Create roles
hr_manager = Role("Manager", hr)
hr_assistant = Role("Assistant", hr)
hr_assistant.add_senior(hr_manager)  # assistant is junior to manager
system.add_role(hr_manager)
system.add_role(hr_assistant)

# 3. Create application and operations
app = Application("HR System")
view_employee = app.add_operation("view_employee")
edit_employee = app.add_operation("edit_employee")
system.add_application(app)

# 4. Assign permissions
hr_assistant.grant_permission(view_employee)
hr_manager.grant_permission(edit_employee)

# 5. Create user and assign role
alice = User("alice")
alice.assign_role(hr, hr_assistant)
system.add_user(alice)

# 6. Set up storage (in-memory SQLite)
storage = Storage("sqlite:///:memory:")
# Normally we'd save system to storage; for demo we use engine directly with in-memory objects
# We'll use a simple in-memory permission engine that accesses the system directly
# For simplicity, we'll just use the permission engine with the system objects manually.

# Create a simplified permission engine that uses our in-memory objects
class SimpleEngine(PermissionEngine):
    def __init__(self, system):
        self.system = system

    def get_effective_permissions(self, role, zone):
        perms = set(role.base_permissions)
        for junior in role.junior_roles:
            perms.update(junior.base_permissions)
        return perms

    def decide(self, user, operation, zone, context=None):
        if zone.id not in user.zone_role_assignments:
            return False
        for role, weight in user.zone_role_assignments[zone.id]:
            if weight > 0 and operation in self.get_effective_permissions(role, zone):
                return True
        return False

engine = SimpleEngine(system)

# 7. Check permissions
print("Alice attempts to view employee in HR zone:", 
      engine.decide(alice, view_employee, hr))  # True
print("Alice attempts to edit employee in HR zone:", 
      engine.decide(alice, edit_employee, hr))   # False

# 8. Check with manager role
bob = User("bob")
bob.assign_role(hr, hr_manager)
print("Bob attempts to edit employee:", 
      engine.decide(bob, edit_employee, hr))     # True
