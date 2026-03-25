from __future__ import annotations

from enum import Enum
from fastapi import Depends, HTTPException, status
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.models.user import User


class Permission(str, Enum):
    SIM_READ = "sim:read"
    SIM_WRITE = "sim:write"
    SIM_DELETE = "sim:delete"
    SIM_BULK_UPLOAD = "sim:bulk_upload"

    LINKAGE_READ = "linkage:read"
    LINKAGE_WRITE = "linkage:write"

    DELINK_READ = "delink:read"
    DELINK_CREATE = "delink:create"
    DELINK_APPROVE = "delink:approve"
    DELINK_CANCEL = "delink:cancel"

    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_SEND = "notification:send"

    AUDIT_READ = "audit:read"

    WEBHOOK_READ = "webhook:read"
    WEBHOOK_MANAGE = "webhook:manage"

    DASHBOARD_READ = "dashboard:read"

    RETENTION_EXECUTE = "retention:execute"
    METRICS_READ = "metrics:read"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "admin": set(Permission),
    "operator": {
        Permission.SIM_READ,
        Permission.SIM_WRITE,
        Permission.LINKAGE_READ,
        Permission.LINKAGE_WRITE,
        Permission.DELINK_READ,
        Permission.DELINK_CREATE,
        Permission.DELINK_CANCEL,
        Permission.NOTIFICATION_READ,
        Permission.NOTIFICATION_SEND,
        Permission.WEBHOOK_READ,
        Permission.WEBHOOK_MANAGE,
        Permission.DASHBOARD_READ,
    },
    "auditor": {
        Permission.SIM_READ,
        Permission.LINKAGE_READ,
        Permission.DELINK_READ,
        Permission.NOTIFICATION_READ,
        Permission.AUDIT_READ,
        Permission.DASHBOARD_READ,
    },
    "api_client": {
        Permission.SIM_READ,
        Permission.LINKAGE_READ,
        Permission.DELINK_READ,
        Permission.WEBHOOK_READ,
    },
}


def get_user_permissions(user: User) -> set[Permission]:
    role = user.role if isinstance(user.role, str) else user.role.value
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(user: User, permission: Permission) -> bool:
    return permission in get_user_permissions(user)


def require_permission(*permissions: Permission):

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        user_perms = get_user_permissions(current_user)
        missing = [p.value for p in permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTHORIZATION_ERROR",
                    "message": f"Missing required permissions: {', '.join(missing)}",
                    "details": {"missing_permissions": missing},
                },
            )
        return current_user

    return _check
