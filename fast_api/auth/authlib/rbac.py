from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fast_api.auth.authlib.oauth2 import get_current_user
from fast_api.models.user import User


def require_role(required_roles: list[str]):

    async def _require_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTHORIZATION_ERROR",
                    "message": f"One of these roles required: {', '.join(required_roles)}",
                    "details": {"required_role": " or ".join(required_roles)},
                },
            )
        return current_user

    return _require_role
