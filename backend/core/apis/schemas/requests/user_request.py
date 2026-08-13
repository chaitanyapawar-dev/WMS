"""
user_request.py — Pydantic schemas for incoming user API payloads.

These schemas are the "contract" between the client and the API.
FastAPI validates every incoming request body against these models
before it reaches the controller — no manual validation needed.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from core.models.user_model import UserRole


class UserCreate(BaseModel):
    """
    Request body used when a new user registers.

    This schema is validated automatically by FastAPI before the request
    reaches the router function.

    Example request body:
        {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "password": "strong-password",
            "mobile_number": "+919876543210"
        }
    """

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's first name",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's last name",
    )
    email: EmailStr = Field(description="User's email address used for login")
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password entered by the user",
    )
    mobile_number: Optional[str] = Field(
        default=None,
        description="Optional mobile number for contact purposes",
    )


class UserLogin(BaseModel):
    """
    Request body used when an existing user logs in.

    The user submits the same email address stored during registration
    along with their password.
    """

    email: EmailStr = Field(description="Registered email address")
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password entered by the user",
    )


class UserUpdate(BaseModel):
    """
    Request body used to update a user's profile.

    All fields are optional so the client can send only the values
    that need to change.
    """

    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Updated first name",
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Updated last name",
    )
    mobile_number: Optional[str] = Field(
        default=None,
        description="Updated mobile number",
    )


class UserResetPassword(BaseModel):
    """
    Request body used to reset a password.

    The token is typically sent to the user's email and is used to verify
    that the reset request is genuine.
    """

    token: str = Field(description="Password reset token sent to the user")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password chosen by the user",
    )


class UserProvisionCreate(BaseModel):
    """
    Request body used by an OWNER to create an employee account.

    Public self-registration is disabled for Whitfield WMS. Employee identity
    is provisioned by an OWNER with an explicit role and warehouse scope.
    """

    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(description="Employee email address used for login")
    password: str = Field(..., min_length=8, description="Temporary employee password")
    role: UserRole = Field(description="Employee WMS role")
    warehouse_ids: list[str] = Field(default_factory=list)
    mobile_number: Optional[str] = Field(default=None, description="Optional mobile number")
