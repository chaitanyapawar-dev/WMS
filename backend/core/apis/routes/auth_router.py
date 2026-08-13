"""
auth_router.py

This router contains authentication endpoints such as register and login.

Teaching note:
- The router handles HTTP concerns only
- The controller handles business logic
- The CRUD layer is the first place that touches the shared database engine
    so the router stays simple for beginners
"""

from fastapi import APIRouter, HTTPException, status

from core import logger
from core.apis.schemas.requests.user_request import UserLogin
from core.apis.schemas.responses.user_responses import LoginResponse, MessageResponse
from core.controllers.user_controller import UserController

logging = logger(__name__)

auth_router = APIRouter()


@auth_router.post(
    "/v1/auth/register",
    status_code=status.HTTP_403_FORBIDDEN,
    response_model=MessageResponse,
)
async def register_user(
):
    """
    Reject public self-registration for the internal WMS.

    Args:
    Returns:
        MessageResponse: This route always rejects public registration.

    Raises:
        HTTPException 403: Public registration is disabled.
    """
    logging.warning("Public registration attempt rejected")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public registration is disabled. Ask a Whitfield owner to create your account.",
    )


@auth_router.post(
    "/v1/auth/login",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponse,
)
async def login_user(
    request: UserLogin,
):
    """
    Login a user using email and password.

    Args:
        request: Validated login payload from UserLogin

    Returns:
        LoginResponse: Access token and user profile data

    Raises:
        HTTPException: Re-raises known authentication errors or returns
        a 500 error for unexpected failures.
    """
    try:
        logging.info("Calling /v1/auth/login endpoint")
        return await UserController().login_user(
            email=request.email, password=request.password
        )
    except HTTPException as httperror:
        logging.error(f"Error in /v1/auth/login endpoint: {httperror}")
        raise httperror
    except Exception as error:
        logging.error(f"Error in /v1/auth/login endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
            headers={"WWW-Authenticate": "Bearer"},
        )
