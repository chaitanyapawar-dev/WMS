from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from core.apis.routes.audit_router import audit_router
from core.apis.routes.ai_router import ai_router
from core.apis.routes.auth_router import auth_router
from core.apis.routes.inventory_router import inventory_router
from core.apis.routes.order_router import order_router
from core.apis.routes.product_router import product_router
from core.apis.routes.receipt_router import receipt_router
from core.apis.routes.seller_router import seller_router
from core.apis.routes.user_router import user_router
from core.apis.routes.warehouse_router import warehouse_router
from core.apis.routes.voice_router import voice_router
from core.database.database import close_mongo_connection, connect_to_mongo
from commons.auth import validate_jwt_configuration
from core import logger

logging = logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown resources.

    Connects to MongoDB and initializes indexes before the API accepts traffic,
    then closes the shared MongoDB client during shutdown.

    Args:
        app: FastAPI application instance.

    Raises:
        Exception: If MongoDB startup initialization fails.
    """
    try:
        logging.info("Executing FastAPI lifespan startup")
        validate_jwt_configuration()
        await connect_to_mongo()
        yield
    except Exception as error:
        logging.error(f"Error during FastAPI lifespan startup: {error}")
        raise
    finally:
        logging.info("Executing FastAPI lifespan shutdown")
        await close_mongo_connection()

# Step 1:
# Create the FastAPI application object.
# This is the central app instance where middleware, routers, and docs are registered.
app = FastAPI(
    title="Whitfield Warehouse Management System",
    version="0.1.0",
    description="Backend API for Whitfield Fulfillment warehouse operations.",
    redoc_url="/documentation",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def log_request_validation_error(request: Request, error: RequestValidationError) -> Response:
    """Log safe metadata when a request is rejected before reaching a route handler.

    Args:
        request: Incoming request rejected by FastAPI validation.
        error: Validation details supplied by FastAPI.

    Returns:
        Response: FastAPI's standard validation response without request-body logging.
    """
    if request.url.path == "/v1/voice/interpret":
        invalid_fields = [
            ".".join(str(part) for part in issue.get("loc", ()))
            for issue in error.errors()
        ]
        logging.warning(
            "Voice request validation rejected before route execution "
            f"method={request.method} fields={invalid_fields}"
        )
    return await request_validation_exception_handler(request, error)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """
    Add baseline security headers to each HTTP response.

    Args:
        request: Incoming FastAPI request object.
        call_next: Next ASGI handler in the middleware chain.

    Returns:
        Response: HTTP response with security headers applied.
    """
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self)"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Server"] = "Custom Server"

    return response


@app.get("/set-cookie")
def set_cookie(response: Response):
    """
    Set a secure demonstration cookie.

    Args:
        response: FastAPI response object used to attach the cookie.
    """
    response.set_cookie(
        key="session",
        value="value",
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=1800,
    )


# Configure robust CORS middleware for cross-origin requests from Vercel & local development
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Step 7:
# Register feature routers with tags so endpoints are grouped clearly in Swagger/ReDoc.
app.include_router(auth_router, tags=["Authentication"])
app.include_router(user_router, tags=["User Profile"])
app.include_router(warehouse_router, tags=["Warehouses"])
app.include_router(seller_router, tags=["Sellers"])
app.include_router(product_router, tags=["Products"])
app.include_router(receipt_router, tags=["Receiving"])
app.include_router(inventory_router, tags=["Inventory"])
app.include_router(audit_router, tags=["Audit Logs"])
app.include_router(order_router, tags=["Fulfillment"])
app.include_router(ai_router, tags=["AI Assistant"])
app.include_router(voice_router, tags=["Receiving Voice"])


@app.get("/")
def ping():
    """
    Return a simple API health response.

    Returns:
        dict: Health-check payload.
    """
    # Step 8:
    # Simple root route used to confirm that the API server is running.
    return {"response": "Whitfield WMS API is running"}


def custom_openapi():
    """
    Generate and cache the customized OpenAPI schema.

    Returns:
        dict: OpenAPI schema for the registered API routes.
    """
    # Step 9:
    # Reuse the generated schema if it was already created earlier.
    if app.openapi_schema:
        return app.openapi_schema

    # Step 10:
    # Generate a custom OpenAPI schema using the app's routes and metadata.
    openapi_schema = get_openapi(
        title="Whitfield Warehouse Management System",
        version="0.1.0",
        description="Backend API for Whitfield Fulfillment warehouse operations.",
        routes=app.routes,
    )

    # Step 11:
    # Store the schema on the app so it does not need to be rebuilt every time.
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Step 12:
# Replace FastAPI's default OpenAPI generator with our custom function.
app.openapi = custom_openapi
