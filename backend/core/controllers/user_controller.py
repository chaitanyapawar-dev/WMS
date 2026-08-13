"""
user_controller.py — Business logic layer for user operations.

Architecture:
  Router (HTTP layer) → Controller (business logic) → CRUD (database layer)

Controllers:
  - Are NOT aware of HTTP details (no Request/Response objects here)
  - Contain all business rules: validation, password hashing, token creation
  - Call one or more CRUD methods to persist / retrieve data
  - Call utility helpers (email, password generation, etc.)
  - Raise HTTPException so the router can return the right status code

This keeps routes thin (just call controller, return result) and
makes business logic easy to unit-test without HTTP overhead.
"""

from fastapi import HTTPException, status
from odmantic import ObjectId
from pymongo.errors import DuplicateKeyError

from core.cruds.user_crud import CRUDUser
from core.cruds.warehouse_crud import CRUDWarehouse
from core.models.user_model import UserRole, UserStatus
from core.models.warehouse_model import WarehouseStatus
from commons.auth import encrypt_password, verify_password, signJWT
from core import logger

logging = logger(__name__)


class UserController:
    """
    Handles all business logic for user-related operations.

    Instantiate once per request (FastAPI's default DI behaviour):
        controller = UserController()
        result = await controller.create_user(data)
    """

    def __init__(self):
        """
        Initialize user controller dependencies.

        Creates the user CRUD helper used by user business operations.
        """
        self.crud_user = CRUDUser()
        self.crud_warehouse = CRUDWarehouse()

    def _safe_user_response(self, user) -> dict:
        """
        Build a safe user payload that excludes password hashes.

        Args:
            user: User model instance.

        Returns:
            dict: Client-safe user fields.
        """
        return {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "role": user.role,
            "status": user.status,
            "warehouse_ids": [str(warehouse_id) for warehouse_id in user.warehouse_ids],
            "created_at": user.created_at,
        }

    # ------------------------------------------------------------------
    # CREATE USER
    # ------------------------------------------------------------------

    async def create_user(self, user_data: dict) -> dict:
        """
        Register a new user account.

        Steps:
          1. Check email uniqueness
          2. Hash the submitted password before storage
          3. Assign OWNER to the first user, otherwise FULFILLMENT_STAFF
          4. Save user with ACTIVE status for self-registration
          5. Return an access token and safe user response

        Args:
            user_data: Dict from UserCreate schema.

        Returns:
            dict: access token and safe user details.

        Raises:
            HTTPException 409: email already registered
            HTTPException 500: DB error or email sending failed
        """
        try:
            logging.info("Executing UserController.create_user")

            # 1. Email uniqueness check
            existing = await self.crud_user.get_by_email(email=user_data["email"])
            if existing:
                logging.warning("Duplicate registration rejected")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists.",
                )

            hashed = encrypt_password(user_data["password"])

            existing_owner = await self.crud_user.get_by_role(role=UserRole.OWNER)
            assigned_role = (
                UserRole.FULFILLMENT_STAFF if existing_owner else UserRole.OWNER
            )
            db_user = await self.crud_user.create(
                obj_in={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "email": user_data["email"],
                    "mobile_number": user_data.get("mobile_number"),
                    "hashed_password": hashed,
                    "role": assigned_role,
                    "status": UserStatus.ACTIVE,
                },
            )

            access_token = signJWT(user_role=db_user.role, id=str(db_user.id))
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": str(db_user.id),
                    "first_name": db_user.first_name,
                    "last_name": db_user.last_name,
                    "email": db_user.email,
                    "mobile_number": db_user.mobile_number,
                    "role": db_user.role,
                    "status": db_user.status,
                    "warehouse_ids": [
                        str(warehouse_id) for warehouse_id in db_user.warehouse_ids
                    ],
                    "created_at": db_user.created_at,
                },
            }

        except HTTPException:
            raise
        except DuplicateKeyError:
            logging.warning("Duplicate registration rejected by database")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )
        except Exception as error:
            logging.error(f"UserController.create_user error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the user.",
            )

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------

    async def login_user(self, email: str, password: str) -> dict:
        """
        Authenticate user with email + password.

        Steps:
          1. Look up user by email
          2. Verify the bcrypt hash matches the supplied password
          3. Check account status is ACTIVE
          4. Return access token

        Args:
            email: User email address.
            password: Plain-text password supplied by the user.

        Returns:
            dict: JWT access token and safe user profile.

        Raises:
            HTTPException 401: Invalid credentials.
            HTTPException 403: Account is not active.
            HTTPException 500: Unexpected authentication failure.
        """
        try:
            logging.info("Executing UserController.login_user")

            user = await self.crud_user.get_by_email(email=email)
            if not user or not verify_password(password, user.hashed_password):
                logging.warning("Invalid login credentials rejected")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )

            if user.status != UserStatus.ACTIVE:
                logging.warning(f"Inactive user login rejected: {user.id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is {user.status}. Please verify your email.",
                )

            access_token = signJWT(user_role=user.role, id=str(user.id))

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": str(user.id),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "mobile_number": user.mobile_number,
                    "role": user.role,
                    "status": user.status,
                    "warehouse_ids": [
                        str(warehouse_id) for warehouse_id in user.warehouse_ids
                    ],
                    "created_at": user.created_at,
                },
            }

        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"UserController.login_user error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed due to an internal error.",
            )

    # ------------------------------------------------------------------
    # GET PROFILE
    # ------------------------------------------------------------------

    async def get_user_profile(self, user_id: str) -> dict:
        """
        Fetch the authenticated user's profile.

        Args:
            user_id: ObjectId string from the decoded JWT

        Returns:
            dict: Safe user profile response payload.

        Raises:
            HTTPException 404: User not found.
            HTTPException 500: Unexpected profile lookup failure.
        """
        try:
            logging.info("Executing UserController.get_user_profile")
            user = await self.crud_user.get_by_id(id=user_id)
            if not user:
                logging.warning(f"User profile not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found.",
                )
            return self._safe_user_response(user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"UserController.get_user_profile error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user profile.",
            )

    async def list_users(self) -> list[dict]:
        """
        List all user accounts for OWNER administration.

        Returns:
            list[dict]: Safe user response payloads.

        Raises:
            HTTPException 500: Unexpected lookup failure.
        """
        try:
            logging.info("Executing UserController.list_users")
            users = await self.crud_user.list_users()
            return [self._safe_user_response(user) for user in users]
        except Exception as error:
            logging.error(f"UserController.list_users error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch users.",
            )

    async def provision_user(self, user_data: dict) -> dict:
        """
        Create an employee account through OWNER-controlled provisioning.

        Args:
            user_data: Validated user provisioning payload.

        Returns:
            dict: Safe created user response payload.

        Raises:
            HTTPException 400: Invalid role or warehouse assignment.
            HTTPException 404: Warehouse not found.
            HTTPException 409: Email already exists.
            HTTPException 500: Unexpected persistence failure.
        """
        try:
            logging.info("Executing UserController.provision_user")

            role = user_data["role"]
            if role == UserRole.OWNER:
                logging.warning("OWNER provisioning through /v1/users rejected")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Owner accounts cannot be created through this form.",
                )

            existing = await self.crud_user.get_by_email(email=user_data["email"])
            if existing:
                logging.warning("Duplicate employee email rejected")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists.",
                )

            warehouse_ids = await self._validate_warehouse_ids(
                warehouse_ids=user_data.get("warehouse_ids", [])
            )

            db_user = await self.crud_user.create(
                obj_in={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "email": user_data["email"],
                    "mobile_number": user_data.get("mobile_number"),
                    "hashed_password": encrypt_password(user_data["password"]),
                    "role": role,
                    "status": UserStatus.ACTIVE,
                    "warehouse_ids": warehouse_ids,
                }
            )
            return self._safe_user_response(db_user)
        except HTTPException:
            raise
        except DuplicateKeyError:
            logging.warning("Duplicate employee email rejected by database")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )
        except Exception as error:
            logging.error(f"UserController.provision_user error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user.",
            )

    async def _validate_warehouse_ids(self, warehouse_ids: list[str]) -> list[ObjectId]:
        """
        Validate warehouse scope references for an employee account.

        Args:
            warehouse_ids: Warehouse ObjectId strings from the provisioning payload.

        Returns:
            list[ObjectId]: Validated active warehouse ObjectIds.

        Raises:
            HTTPException 400: Invalid ObjectId or inactive warehouse.
            HTTPException 404: Warehouse not found.
        """
        validated_ids: list[ObjectId] = []
        for warehouse_id in warehouse_ids:
            try:
                object_id = ObjectId(warehouse_id)
            except Exception:
                logging.warning("Invalid warehouse id rejected during user provisioning")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid warehouse assignment.",
                )

            warehouse = await self.crud_warehouse.get_by_id(id=str(object_id))
            if not warehouse:
                logging.warning(f"Provisioning warehouse not found: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found.",
                )
            if warehouse.status != WarehouseStatus.ACTIVE:
                logging.warning(f"Inactive warehouse assignment rejected: {warehouse_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Warehouse assignment must be active.",
                )
            validated_ids.append(object_id)
        return validated_ids
