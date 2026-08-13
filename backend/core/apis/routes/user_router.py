"""
user_router.py

This router contains user profile endpoints.

Teaching note:
- Authentication is checked in the router because this is where request
    headers are available
- The controller is called only after the JWT has been validated
"""

from fastapi import APIRouter, HTTPException, status, Depends

from core import logger
from core.apis.schemas.requests.user_request import UserProvisionCreate
from core.apis.schemas.responses.user_responses import UserResponse
from core.controllers.user_controller import UserController
from core.models.user_model import User, UserRole
from commons.auth import get_current_user, require_roles

logging = logger(__name__)
user_router = APIRouter()


@user_router.get(
    "/v1/auth/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the profile of the currently authenticated user.

    This endpoint uses the shared authentication dependency to validate the
    token, reload the user, and reject inactive accounts before returning data.

    Args:
        current_user: Authenticated active user loaded from MongoDB.

    Returns:
        UserResponse: Authenticated user's profile

    Raises:
        HTTPException: 401 for invalid token, 404 for missing user,
        or 500 for unexpected failures.
    """
    try:
        logging.info("Calling /v1/auth/me endpoint")

        return await UserController().get_user_profile(user_id=str(current_user.id))

    except HTTPException as httperror:
        logging.error(f"Error in /v1/auth/me endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in /v1/auth/me endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
            headers={"WWW-Authenticate": "Bearer"},
        )


@user_router.get(
    "/v1/users",
    status_code=status.HTTP_200_OK,
    response_model=list[UserResponse],
)
async def list_users(
    current_user: User = Depends(require_roles([UserRole.OWNER])),
):
    """
    List user accounts for OWNER administration.

    Args:
        current_user: Authenticated OWNER user.

    Returns:
        list[UserResponse]: Safe user profile records.

    Raises:
        HTTPException: 401 for invalid token, 403 for non-owner access,
        or 500 for unexpected failures.
    """
    try:
        logging.info("Calling GET /v1/users endpoint")
        return await UserController().list_users()
    except HTTPException as httperror:
        logging.error(f"Error in GET /v1/users endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in GET /v1/users endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@user_router.post(
    "/v1/users",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def create_user(
    request: UserProvisionCreate,
    current_user: User = Depends(require_roles([UserRole.OWNER])),
):
    """
    Create an employee account for OWNER-controlled provisioning.

    Args:
        request: Validated employee creation payload.
        current_user: Authenticated OWNER user.

    Returns:
        UserResponse: Safe created user profile.

    Raises:
        HTTPException: Preserves validation, duplicate email, authorization,
        and unexpected server errors.
    """
    try:
        logging.info("Calling POST /v1/users endpoint")
        return await UserController().provision_user(user_data=request.model_dump())
    except HTTPException as httperror:
        logging.error(f"Error in POST /v1/users endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in POST /v1/users endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
