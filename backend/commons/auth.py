"""Authentication and authorization helpers for the WMS backend."""

import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Sequence

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from odmantic import ObjectId
from passlib.context import CryptContext

from core import logger
from core.cruds.user_crud import CRUDUser
from core.models.user_model import User, UserRole, UserStatus

load_dotenv()

logging = logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str:
    """
    Read the configured JWT signing secret.

    Supports the previous `secret` variable as a compatibility fallback.

    Returns:
        str: JWT signing secret.

    Raises:
        RuntimeError: If no JWT secret is configured.
    """
    secret = os.environ.get("JWT_SECRET_KEY") or os.environ.get("secret")
    if not secret:
        logging.error("JWT secret is not configured")
        raise RuntimeError("JWT secret is not configured")
    return secret


def _get_jwt_algorithm() -> str:
    """
    Read the configured JWT signing algorithm.

    Supports the previous `algorithm` variable as a compatibility fallback.

    Returns:
        str: JWT signing algorithm.
    """
    return os.environ.get("JWT_ALGORITHM") or os.environ.get("algorithm", "HS256")


def _get_token_expire_minutes(default_minutes: int = 60) -> int:
    """
    Read the configured access-token lifetime.

    Args:
        default_minutes: Lifetime to use when the environment value is absent or invalid.

    Returns:
        int: Access-token lifetime in minutes.
    """
    raw_value = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
    if not raw_value:
        return default_minutes

    try:
        return int(raw_value)
    except ValueError:
        logging.warning("ACCESS_TOKEN_EXPIRE_MINUTES is invalid; using default")
        return default_minutes


def validate_jwt_configuration() -> None:
    """
    Validate JWT environment configuration during application startup.

    Fails fast before serving requests if the signing secret is missing.

    Raises:
        RuntimeError: If required JWT configuration is invalid or missing.
    """
    logging.info("Executing validate_jwt_configuration")
    _get_jwt_secret()
    _get_jwt_algorithm()
    _get_token_expire_minutes()


def signJWT(user_role: str, id: str, expiry_duration: int | None = None) -> str:
    """
    Create a signed JWT access token for the given user.

    Stores user identity, role hint, and a standard `exp` claim. The role in the
    token is not treated as source of truth for authorization.

    Args:
        user_role: Role string from UserRole enum.
        id: User ID as a string.
        expiry_duration: Optional compatibility value in seconds.

    Returns:
        str: Signed JWT access token.

    Raises:
        RuntimeError: If JWT configuration is missing.
    """
    logging.info("Executing signJWT")
    if expiry_duration is None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=_get_token_expire_minutes()
        )
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiry_duration)

    role_value = user_role.value if isinstance(user_role, UserRole) else str(user_role)
    payload = {
        "sub": id,
        "id": id,
        "role": role_value,
        "exp": expires_at,
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=_get_jwt_algorithm())


def decodeJWT(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT string to decode.

    Returns:
        dict: Decoded JWT payload.

    Raises:
        HTTPException 401: If the token is expired, malformed, or invalid.
        RuntimeError: If JWT configuration is missing.
    """
    try:
        logging.info("Executing decodeJWT")
        return jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[_get_jwt_algorithm()],
        )
    except jwt.ExpiredSignatureError:
        logging.warning("Expired JWT rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        logging.warning("Invalid JWT rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def encrypt_password(password: str) -> str:
    """
    Hash a plain-text password with bcrypt.

    Args:
        password: Plain-text password to hash.

    Returns:
        str: Secure bcrypt password hash.
    """
    logging.info("Executing encrypt_password")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: Password supplied by the user.
        hashed_password: Stored bcrypt hash.

    Returns:
        bool: True when the password matches the hash.
    """
    try:
        logging.info("Executing verify_password")
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        logging.warning("Stored password hash could not be verified")
        return False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    """
    Return the currently authenticated active user.

    Loads the latest user record from MongoDB and treats the database as the
    source of truth for status and authorization.

    Args:
        credentials: Bearer credentials extracted from the Authorization header.

    Returns:
        User: Authenticated active user record.

    Raises:
        HTTPException 401: If token identity is invalid or the user no longer exists.
        HTTPException 403: If the user account is not active.
        HTTPException 500: If JWT configuration is missing.
    """
    try:
        logging.info("Executing get_current_user")
        if credentials is None:
            logging.warning("Authentication rejected because bearer token is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        payload = decodeJWT(token)
        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            logging.warning("JWT rejected because user identity is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await CRUDUser().get_by_id(id=user_id)
        if not user:
            logging.warning(f"JWT rejected because user no longer exists: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.status != UserStatus.ACTIVE:
            logging.warning(f"Inactive user rejected: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not active",
            )

        return user
    except HTTPException:
        raise
    except RuntimeError as error:
        logging.error(f"Error in get_current_user: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication configuration error",
        )
    except Exception as error:
        logging.error(f"Error in get_current_user: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


def require_roles(allowed_roles: Sequence[UserRole]) -> Callable:
    """
    Build a FastAPI dependency that requires one of the allowed roles.

    Args:
        allowed_roles: Roles permitted to access the protected endpoint.

    Returns:
        Callable: Dependency returning the authenticated user.
    """
    allowed_role_values = {
        role.value if isinstance(role, UserRole) else str(role)
        for role in allowed_roles
    }

    async def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        """
        Enforce role membership for the authenticated user.

        Args:
            current_user: Active authenticated user loaded from MongoDB.

        Returns:
            User: Authenticated user when role authorization succeeds.

        Raises:
            HTTPException 403: If the user's role is not allowed.
        """
        logging.info("Executing require_roles.role_dependency")
        current_role = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else str(current_user.role)
        )
        if current_role not in allowed_role_values:
            logging.warning(
                f"Access denied for user {current_user.id} with role {current_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user

    return role_dependency


def _normalize_object_id(value: str | ObjectId) -> ObjectId | None:
    """
    Convert a warehouse ID value to an ObjectId when possible.

    Args:
        value: Warehouse ID as a string or ObjectId.

    Returns:
        ObjectId | None: Normalized ObjectId, or None when invalid.
    """
    try:
        return value if isinstance(value, ObjectId) else ObjectId(value)
    except Exception:
        return None


def can_access_warehouse(user: User, warehouse_id: str | ObjectId) -> bool:
    """
    Check whether a user can access a warehouse.

    OWNER has global access. Other roles must have the warehouse ObjectId in
    their server-side warehouse scope.

    Args:
        user: Authenticated user record.
        warehouse_id: Warehouse ID being accessed.

    Returns:
        bool: True when access is allowed.
    """
    logging.info("Executing can_access_warehouse")
    if user.role == UserRole.OWNER:
        return True

    normalized_warehouse_id = _normalize_object_id(warehouse_id)
    if normalized_warehouse_id is None:
        return False

    allowed_warehouse_ids = {str(allowed_id) for allowed_id in user.warehouse_ids}
    return str(normalized_warehouse_id) in allowed_warehouse_ids


async def require_warehouse_access(
    warehouse_id: str,
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require the authenticated user to have access to a warehouse.

    Args:
        warehouse_id: Warehouse ID from a path, query, or trusted route parameter.
        current_user: Active authenticated user loaded from MongoDB.

    Returns:
        User: Authenticated user when warehouse authorization succeeds.

    Raises:
        HTTPException 403: If the user cannot access the warehouse.
    """
    logging.info("Executing require_warehouse_access")
    if not can_access_warehouse(current_user, warehouse_id):
        logging.warning(
            f"Warehouse access denied for user {current_user.id}: {warehouse_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this warehouse",
        )
    return current_user
