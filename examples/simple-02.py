# example2_gamma.py
from czoi.core import System, Zone, Role, User, Application, GammaMapping
from czoi.permission import PermissionEngine
from czoi.storage.sqlalchemy import Storage

# Setup
system = System()
corp = Zone("Corp")
dev = Zone("Dev", parent=corp)
system.add_zone(corp)
system.add_zone(dev)

# Roles in Corp
corp_eng = Role("Engineer", corp)
corp_eng.grant_permission(Application("Global").add_operation("access_vpn"))

# Roles in Dev
dev_eng = Role("Developer", dev)
dev_eng.grant_permission(Application("DevTools").add_operation("commit_code"))

# Gamma mapping: Dev Developer inherits from Corp Engineer
gamma = GammaMapping(dev, dev_eng, corp, corp_eng)
system.add_gamma_mapping(gamma)

# User
alice = User("alice")
alice.assign_role(dev, dev_eng)

# Simple permission engine with gamma support
class GammaEngine(PermissionEngine):
    def __init__(self, system):
        self.system = system

    def get_effective_permissions(self, role, zone):
        perms = set(role.base_permissions)
        # Intra-zone junior inheritance
        for junior in role.junior_roles:
            perms.update(junior.base_permissions)
        # Inter-zone gamma mappings (upwards)
        for gm in self.system.gamma_mappings:
            if gm.child_role == role and gm.child_zone == zone:
                perms.update(gm.parent_role.base_permissions)
        return perms

    def decide(self, user, operation, zone, context=None):
        if zone.id not in user.zone_role_assignments:
            return False
        for role, weight in user.zone_role_assignments[zone.id]:
            if weight > 0 and operation in self.get_effective_permissions(role, zone):
                return True
        return False

engine = GammaEngine(system)

vpn_op = corp_eng.base_permissions.pop()  # the VPN operation
commit_op = dev_eng.base_permissions.pop()

print("Alice in Dev zone can commit_code:", 
      engine.decide(alice, commit_op, dev))  # True (own permission)
print("Alice in Dev zone can access_vpn:", 
      engine.decide(alice, vpn_op, dev))     # True (inherited via gamma)
print("Alice in Corp zone can access_vpn:", 
      engine.decide(alice, vpn_op, corp))    # False (not assigned in Corp)