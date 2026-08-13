"""
database.py — MongoDB connection management using Motor (async) + ODMantic (ODM).

Concepts taught here:
    - Singleton pattern for database clients
    - Async MongoDB with Motor
    - ODMantic AIOEngine for type-safe queries
    - Simple configuration using one MongoDB URL and one database name
    - Shared engine access via get_engine() inside the CRUD layer
"""

import os
import logging
from datetime import datetime, timezone
from motor import motor_asyncio, core
from odmantic import AIOEngine
from pymongo.driver_info import DriverInfo
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Set up basic logging so connection events are visible in the console.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DriverInfo helps MongoDB identify which application is making the connection.
DRIVER_INFO = DriverInfo(name="fastapi-tutorial", version="0.1.0")

# Read the MongoDB settings once from environment variables.
# These values are then reused throughout this file.
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "WMS")


class _MongoClientSingleton:
    """
    Singleton that holds the async Motor client and the ODMantic engine.

    Why a singleton?
    MongoDB connections are expensive to create. We create ONE connection pool
    at startup and reuse it across every request — this is the industry standard.
    """

    mongo_client: Optional[motor_asyncio.AsyncIOMotorClient] = None
    engine: Optional[AIOEngine] = None

    def __new__(cls):
        """
        Create or return the shared MongoDB client singleton.

        Reuses one Motor connection pool and ODMantic engine for all CRUD calls.

        Returns:
            _MongoClientSingleton: Shared Mongo client and ODMantic engine holder.
        """
        # Step 1:
        # Check whether we already created the singleton instance earlier.
        # If it already exists, we reuse it instead of creating a new connection.
        if not hasattr(cls, "instance"):
            # Step 2:
            # Create the singleton object for the first time.
            cls.instance = super(_MongoClientSingleton, cls).__new__(cls)

            # Keep the tutorial simple: one connection string and one database name.
            mongodb_uri = MONGODB_URL
            database_name = DATABASE_NAME

            # Step 3:
            # Create the async MongoDB client.
            # Motor manages the connection pool for us under the hood.
            cls.instance.mongo_client = motor_asyncio.AsyncIOMotorClient(
                mongodb_uri, driver=DRIVER_INFO
            )

            # Step 4:
            # Wrap the Motor client with ODMantic's engine.
            # This is what the CRUD layer uses for model-based queries.
            cls.instance.engine = AIOEngine(
                client=cls.instance.mongo_client, database=database_name
            )

            # Step 5:
            # Log the database name so developers can confirm the connection target.
            logger.info(f"MongoDB singleton initialised | DB: {database_name}")

        # Step 6:
        # Always return the same singleton instance.
        return cls.instance


def MongoDatabase() -> core.AgnosticDatabase:
    """
    Return the raw Motor database object.
    Use this when you need to run raw MongoDB queries (aggregations, etc.).
    """
    # Step 1: get the singleton client.
    # Step 2: select the configured database from that client.
    return _MongoClientSingleton().mongo_client[DATABASE_NAME]


def get_engine() -> AIOEngine:
    """
    Return the ODMantic AIOEngine instance.
    CRUD classes import this function directly so the router and controller
    layers do not need to receive a database dependency.
    """
    # Return the ODMantic engine stored inside the singleton.
    return _MongoClientSingleton().engine


async def ping():
    """Verify the MongoDB connection is alive."""
    # Run MongoDB's built-in ping command.
    # If this fails, the application should treat the database as unavailable.
    await MongoDatabase().command("ping")
    logger.info("MongoDB ping successful")


async def init_database_indexes():
    """
    Create or verify ODMantic-managed database indexes.

    Ensures model-level constraints such as unique user email are enforced by MongoDB.

    Raises:
        Exception: If index creation fails.
    """
    try:
        from core.models.audit_model import AuditLog
        from core.models.inventory_model import Inventory
        from core.models.movement_model import InventoryMovement
        from core.models.order_model import Order
        from core.models.product_model import Product
        from core.models.receipt_model import Receipt
        from core.models.seller_model import Seller
        from core.models.shipment_model import Shipment
        from core.models.user_model import User
        from core.models.warehouse_model import Warehouse

        logger.info("Initialising MongoDB indexes")
        await get_engine().configure_database(
            [User, Warehouse, Seller, Product, Receipt, Inventory, InventoryMovement, AuditLog, Order, Shipment]
        )

        # Create unique partial indexes for receipt tracking and ticket numbers
        db = MongoDatabase()
        try:
            await db["receipts"].drop_index("idx_receipt_seller_warehouse_tracking_unique")
        except Exception:
            pass
        try:
            await db["receipts"].drop_index("idx_receipt_warehouse_ticket_unique")
        except Exception:
            pass

        await db["receipts"].create_index(
            [("seller_id", 1), ("warehouse_id", 1), ("tracking_number", 1)],
            unique=True,
            partialFilterExpression={"tracking_number": {"$type": "string"}},
            name="idx_receipt_seller_warehouse_tracking_unique",
        )
        await db["receipts"].create_index(
            [("warehouse_id", 1), ("ticket_number", 1)],
            unique=True,
            partialFilterExpression={"ticket_number": {"$type": "string"}},
            name="idx_receipt_warehouse_ticket_unique",
        )
        logger.info("MongoDB indexes initialised")
    except Exception as error:
        logger.error(f"Error initialising MongoDB indexes: {error}")
        raise


async def seed_default_warehouses():
    """
    Seed required Whitfield default warehouses.

    Ensures Reno, Nevada and Columbus, Ohio warehouses exist without creating
    duplicate records when startup runs repeatedly.

    Raises:
        Exception: If warehouse seeding fails.
    """
    try:
        from core.cruds.warehouse_crud import CRUDWarehouse

        logger.info("Seeding default warehouses")
        crud_warehouse = CRUDWarehouse()
        default_warehouses = [
            {
                "name": "Reno Warehouse",
                "code": "RNO",
                "city": "Reno",
                "state": "Nevada",
            },
            {
                "name": "Columbus Warehouse",
                "code": "CMH",
                "city": "Columbus",
                "state": "Ohio",
            },
        ]
        for warehouse_data in default_warehouses:
            existing = await crud_warehouse.get_by_code(code=warehouse_data["code"])
            if not existing:
                await crud_warehouse.create(obj_in=warehouse_data)
                logger.info(f"Default warehouse seeded: {warehouse_data['code']}")
        logger.info("Default warehouse seeding complete")
    except Exception as error:
        logger.error(f"Error seeding default warehouses: {error}")
        raise


async def seed_demo_user_accounts():
    """
    Seed local demonstration accounts with valid bcrypt password hashes.

    The seven fixed `@whitfield.com` demo identities are development fixtures
    used by the frontend quick-login panel. Existing matching demo accounts are
    updated for role, active status, warehouse scope, and demo password hash so
    stale tutorial hashes cannot break login.

    Raises:
        Exception: If demo account seeding fails.
    """
    enabled = os.getenv("ENABLE_DEMO_ACCOUNTS", "true").lower() in {"1", "true", "yes"}
    if not enabled:
        logger.info("Demo account seeding skipped")
        return

    try:
        from commons.auth import encrypt_password

        logger.info("Seeding local demo user accounts")
        db = MongoDatabase()
        users_collection = db["users"]
        warehouses_collection = db["warehouses"]
        now = datetime.now(timezone.utc)
        reno = await warehouses_collection.find_one({"code": "RNO"})
        columbus = await warehouses_collection.find_one({"code": "CMH"})
        reno_scope = [reno["_id"]] if reno else []
        columbus_scope = [columbus["_id"]] if columbus else []
        demo_password_hash = encrypt_password("whitfield")
        demo_users = [
            {
                "first_name": "Whitfield",
                "last_name": "Owner",
                "email": "owner@whitfield.com",
                "role": "OWNER",
                "warehouse_ids": [],
            },
            {
                "first_name": "Reno",
                "last_name": "Manager",
                "email": "manager.reno@whitfield.com",
                "role": "MANAGER",
                "warehouse_ids": reno_scope,
            },
            {
                "first_name": "Columbus",
                "last_name": "Manager",
                "email": "manager.columbus@whitfield.com",
                "role": "MANAGER",
                "warehouse_ids": columbus_scope,
            },
            {
                "first_name": "Reno",
                "last_name": "Receiving",
                "email": "receiving.reno@whitfield.com",
                "role": "RECEIVING_STAFF",
                "warehouse_ids": reno_scope,
            },
            {
                "first_name": "Columbus",
                "last_name": "Receiving",
                "email": "receiving.columbus@whitfield.com",
                "role": "RECEIVING_STAFF",
                "warehouse_ids": columbus_scope,
            },
            {
                "first_name": "Reno",
                "last_name": "Fulfillment",
                "email": "fulfillment.reno@whitfield.com",
                "role": "FULFILLMENT_STAFF",
                "warehouse_ids": reno_scope,
            },
            {
                "first_name": "Columbus",
                "last_name": "Fulfillment",
                "email": "fulfillment.columbus@whitfield.com",
                "role": "FULFILLMENT_STAFF",
                "warehouse_ids": columbus_scope,
            },
        ]

        for demo_user in demo_users:
            await users_collection.update_one(
                {"email": demo_user["email"]},
                {
                    "$set": {
                        **demo_user,
                        "hashed_password": demo_password_hash,
                        "status": "ACTIVE",
                        "updated_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
            logger.info(f"Demo user ensured: {demo_user['email']}")
        logger.info("Local demo user accounts seeded")
    except Exception as error:
        logger.error(f"Error seeding demo user accounts: {error}")
        raise


async def migrate_legacy_user_roles():
    """
    Migrate tutorial user documents to WMS auth fields.

    Converts legacy ADMIN users to OWNER and legacy USER users to
    FULFILLMENT_STAFF, and adds missing warehouse scope arrays so existing
    prototype data remains loadable.

    Raises:
        Exception: If the migration update fails.
    """
    try:
        logger.info("Migrating legacy user roles")
        users_collection = MongoDatabase()["users"]
        warehouse_scope_result = await users_collection.update_many(
            {"warehouse_ids": {"$exists": False}},
            {"$set": {"warehouse_ids": []}},
        )
        superadmin_result = await users_collection.update_many(
            {"user_role": {"$in": ["SUPERADMIN", "ADMIN"]}},
            {"$set": {"role": "OWNER"}},
        )
        legacy_manager_result = await users_collection.update_many(
            {"user_role": "MANAGER", "role": {"$ne": "OWNER"}},
            {"$set": {"role": "MANAGER"}},
        )
        admin_result = await users_collection.update_many(
            {"role": "ADMIN"},
            {"$set": {"role": "OWNER"}},
        )
        user_result = await users_collection.update_many(
            {"role": "USER"},
            {"$set": {"role": "FULFILLMENT_STAFF"}},
        )
        missing_role_result = await users_collection.update_many(
            {"role": {"$exists": False}},
            {"$set": {"role": "FULFILLMENT_STAFF"}},
        )
        logger.info(
            "Legacy user auth migration complete | "
            f"warehouse_ids:{warehouse_scope_result.modified_count} "
            f"superadmin:{superadmin_result.modified_count} "
            f"legacy_manager:{legacy_manager_result.modified_count} "
            f"ADMIN:{admin_result.modified_count} USER:{user_result.modified_count}"
            f" missing_role:{missing_role_result.modified_count}"
        )
    except Exception as error:
        logger.error(f"Error migrating legacy user roles: {error}")
        raise


async def connect_to_mongo():
    """
    Called during application startup (lifespan).
    Initialises the singleton and verifies connectivity.
    """
    logger.info("Connecting to MongoDB...")

    # Step 1: create the singleton if it does not already exist.
    _MongoClientSingleton()

    # Step 2: confirm that the database is reachable.
    await ping()

    # Step 3: migrate legacy role values before ODMantic model use.
    await migrate_legacy_user_roles()

    # Step 4: ensure model indexes exist before serving requests.
    await init_database_indexes()

    # Step 5: seed required master data.
    await seed_default_warehouses()

    # Step 6: seed local demo accounts with valid hashes.
    await seed_demo_user_accounts()

    # Step 7: log success so startup flow is easy to trace.
    logger.info("MongoDB connection established")


async def close_mongo_connection():
    """
    Called during application shutdown (lifespan).
    Closes the Motor client to release all connection pool resources.
    """
    # Step 1: fetch the same singleton instance used during startup.
    singleton = _MongoClientSingleton()

    # Step 2: close the MongoDB client only if it exists.
    if singleton.mongo_client:
        singleton.mongo_client.close()

        # Step 3: log shutdown completion for easier debugging.
        logger.info("MongoDB connection closed")
