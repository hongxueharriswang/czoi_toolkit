
from typing import List, Set
from .models import Zone, Role, User, Application, Operation, GammaMapping

class System:
    """Container for a complete CZOA system."""
    def __init__(self):
        self.zones: Set[Zone] = set()
        self.roles: Set[Role] = set()
        self.users: Set[User] = set()
        self.applications: Set[Application] = set()
        self.operations: Set[Operation] = set()
        self.gamma_mappings: List[GammaMapping] = []
        self.root_zone: Zone = None

    def add_zone(self, zone: Zone):
        self.zones.add(zone)
        if zone.parent is None:
            if self.root_zone is not None:
                raise ValueError("Multiple root zones not allowed")
            self.root_zone = zone

    def add_role(self, role: Role):
        self.roles.add(role)

    def add_user(self, user: User):
        self.users.add(user)

    def add_application(self, app: Application):
        self.applications.add(app)
        self.operations.update(app.operations)

    def add_gamma_mapping(self, mapping: GammaMapping):
        self.gamma_mappings.append(mapping)

    def get_zone(self, zone_id):
        for z in self.zones:
            if z.id == zone_id:
                return z
        return None

    def get_role(self, role_id):
        for r in self.roles:
            if r.id == role_id:
                return r
        return None
