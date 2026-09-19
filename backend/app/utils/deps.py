"""
Reusable FastAPI dependencies: extracting & validating the current user
from a JWT bearer token, and enforcing role-based authorization.
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories import user_repository
from app.utils.security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)

# NOTE: these dependencies are deliberately plain `def`, not `async def`.
# They call synchronous psycopg2 code; inside an `async def` that would block
# the whole event loop (every other request waits). As plain functions FastAPI
# runs them in a worker thread, so slow database calls no longer freeze the server.


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in again.",
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user_id = payload.get("sub")
    user = user_repository.get_user_by_id(user_id)
    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found or disabled.",
        )
    return user


def require_roles(*allowed_roles: str):
    """Dependency factory: raises 403 unless current_user's role is in allowed_roles."""

    def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _checker
