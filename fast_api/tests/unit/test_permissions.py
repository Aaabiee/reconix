import pytest
from fast_api.auth.authlib.permissions import (
    Permission,
    ROLE_PERMISSIONS,
    get_user_permissions,
    has_permission,
)


class MockUser:
    def __init__(self, role: str):
        self.role = role


class TestRolePermissions:

    def test_admin_has_all_permissions(self):
        perms = ROLE_PERMISSIONS["admin"]
        for p in Permission:
            assert p in perms, f"Admin missing permission: {p.value}"

    def test_operator_has_sim_read_write(self):
        perms = ROLE_PERMISSIONS["operator"]
        assert Permission.SIM_READ in perms
        assert Permission.SIM_WRITE in perms

    def test_operator_cannot_read_audit(self):
        perms = ROLE_PERMISSIONS["operator"]
        assert Permission.AUDIT_READ not in perms

    def test_operator_cannot_execute_retention(self):
        perms = ROLE_PERMISSIONS["operator"]
        assert Permission.RETENTION_EXECUTE not in perms

    def test_operator_cannot_delete_sim(self):
        perms = ROLE_PERMISSIONS["operator"]
        assert Permission.SIM_DELETE not in perms

    def test_auditor_has_audit_read(self):
        perms = ROLE_PERMISSIONS["auditor"]
        assert Permission.AUDIT_READ in perms

    def test_auditor_has_read_permissions(self):
        perms = ROLE_PERMISSIONS["auditor"]
        assert Permission.SIM_READ in perms
        assert Permission.LINKAGE_READ in perms
        assert Permission.DELINK_READ in perms
        assert Permission.DASHBOARD_READ in perms

    def test_auditor_cannot_write(self):
        perms = ROLE_PERMISSIONS["auditor"]
        assert Permission.SIM_WRITE not in perms
        assert Permission.LINKAGE_WRITE not in perms
        assert Permission.DELINK_CREATE not in perms
        assert Permission.DELINK_APPROVE not in perms

    def test_api_client_limited_read(self):
        perms = ROLE_PERMISSIONS["api_client"]
        assert Permission.SIM_READ in perms
        assert Permission.LINKAGE_READ in perms
        assert Permission.SIM_WRITE not in perms
        assert Permission.AUDIT_READ not in perms
        assert Permission.DASHBOARD_READ not in perms


class TestGetUserPermissions:

    def test_admin_permissions(self):
        user = MockUser("admin")
        perms = get_user_permissions(user)
        assert Permission.RETENTION_EXECUTE in perms

    def test_operator_permissions(self):
        user = MockUser("operator")
        perms = get_user_permissions(user)
        assert Permission.SIM_READ in perms
        assert Permission.RETENTION_EXECUTE not in perms

    def test_unknown_role_returns_empty(self):
        user = MockUser("unknown_role")
        perms = get_user_permissions(user)
        assert len(perms) == 0


class TestHasPermission:

    def test_has_permission_granted(self):
        user = MockUser("admin")
        assert has_permission(user, Permission.RETENTION_EXECUTE) is True

    def test_has_permission_denied(self):
        user = MockUser("operator")
        assert has_permission(user, Permission.RETENTION_EXECUTE) is False

    def test_has_permission_auditor_audit_read(self):
        user = MockUser("auditor")
        assert has_permission(user, Permission.AUDIT_READ) is True

    def test_has_permission_auditor_sim_write(self):
        user = MockUser("auditor")
        assert has_permission(user, Permission.SIM_WRITE) is False
