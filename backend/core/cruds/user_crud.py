"""
user_crud.py — User-specific database operations, extending CRUDBase.

Pattern:
  CRUDBase provides generic get/create/update/delete.
  CRUDUser adds user-specific queries (get_by_email, etc.).
  Controllers call CRUDUser — they never touch the DB directly.

This separation of concerns keeps each layer testable in isolation.
"""

from core import logger
from core.cruds.base import CRUDBase
from core.models.user_model import User, UserRole, UserStatus
from core.apis.schemas.requests.user_request import UserCreate, UserUpdate
from odmantic import ObjectId
from datetime import datetime, timezone
from typing import Optional

logging = logger(__name__)


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        """
        Initialize the user CRUD helper.

        Binds the shared ODMantic engine to the User model.
        """
        super().__init__(model=User)

    async def get_by_email(self, *, email: str) -> Optional[User]:
        """
        Find a user by email address.
        Used for login, registration duplicate-check, and password reset.

        Args:
            email: Case-sensitive email address to look up

        Returns:
            User instance if found, None otherwise
        """
        try:
            logging.info("Executing CRUDUser.get_by_email")
            return await self.engine.find_one(User, User.email == email)
        except Exception as error:
            logging.error(f"CRUDUser.get_by_email error: {error}")
            raise

    async def get_by_id(self, *, id: str) -> Optional[User]:
        """
        Find a user by their ObjectId (as a string).

        Args:
            id: 24-char hex string ObjectId

        Returns:
            User instance if found, None otherwise
        """
        try:
            logging.info("Executing CRUDUser.get_by_id")
            try:
                object_id = ObjectId(id)
            except Exception:
                logging.warning("Invalid user ObjectId rejected")
                return None
            return await self.engine.find_one(User, User.id == object_id)
        except Exception as error:
            logging.error(f"CRUDUser.get_by_id error: {error}")
            raise

    async def get_by_role(self, *, role: UserRole) -> Optional[User]:
        """
        Find a user by role.

        Args:
            role: UserRole value to look up.

        Returns:
            User instance if found, None otherwise.
        """
        try:
            logging.info("Executing CRUDUser.get_by_role")
            return await self.engine.find_one(User, User.role == role)
        except Exception as error:
            logging.error(f"CRUDUser.get_by_role error: {error}")
            raise

    async def list_users(self) -> list[User]:
        """
        Return all user accounts sorted by creation date.

        Returns:
            list[User]: User records ordered newest first.
        """
        try:
            logging.info("Executing CRUDUser.list_users")
            users = await self.engine.find(User)
            return sorted(users, key=lambda user: user.created_at, reverse=True)
        except Exception as error:
            logging.error(f"CRUDUser.list_users error: {error}")
            raise

    async def create(self, *, obj_in: UserCreate) -> User:
        """
        Insert a new user document. The caller is responsible for hashing
        the password BEFORE passing it in — this method stores whatever
        hashed_password is given to it.

        Args:
            obj_in: UserCreate schema (must include hashed_password key in dict)

        Returns:
            Saved User instance with _id populated
        """
        try:
            logging.info("Executing CRUDUser.create")
            if isinstance(obj_in, dict):
                data = obj_in
            else:
                data = obj_in.model_dump()

            user = User(**data)
            return await self.engine.save(user)
        except Exception as error:
            logging.error(f"CRUDUser.create error: {error}")
            raise

    async def update_status(self, *, user: User, status: UserStatus) -> User:
        """
        Change the account status of an existing user (e.g., ACTIVE after email verification).

        Args:
            user: The User instance fetched from the DB
            status: New UserStatus value

        Returns:
            Updated User instance
        """
        try:
            logging.info("Executing CRUDUser.update_status")
            user.status = status
            user.updated_at = datetime.now(timezone.utc)
            return await self.engine.save(user)
        except Exception as error:
            logging.error(f"CRUDUser.update_status error: {error}")
            raise
