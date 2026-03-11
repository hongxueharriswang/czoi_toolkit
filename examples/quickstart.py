
from czoi.core.models import Zone, Role, User, Application
from czoi.permission.engine import PermissionEngine

class FakeStorage:
    def get_gamma_mappings(self, **kwargs):
        return []
    def get_role(self, role_id):
        return None
    def get_constraints(self, **kwargs):
        return []

if __name__ == "__main__":
    root = Zone("Root")
    hr = Zone("HR", parent=root)
    manager = Role("Manager", hr)
    assistant = Role("Assistant", hr)
    assistant.add_senior(manager)

    app = Application("HR App")
    view_op = app.add_operation("view_employee")
    edit_op = app.add_operation("edit_employee")

    assistant.grant_permission(view_op)
    manager.grant_permission(edit_op)

    alice = User("alice")
    alice.assign_role(hr, assistant)

    engine = PermissionEngine(FakeStorage())

    print("View allowed:", engine.decide(alice, view_op, hr))
    print("Edit allowed:", engine.decide(alice, edit_op, hr))
