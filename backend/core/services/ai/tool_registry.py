"""Approved read-only WMS tools for Gemini orchestration.

Gemini receives only these bounded capabilities. Tool handlers use the trusted
current user and existing WMS controllers; they never accept identity or scope
from model-supplied arguments.
"""

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from commons.auth import can_access_warehouse
from core import logger
from core.controllers.inventory_controller import InventoryController
from core.controllers.order_controller import OrderController
from core.controllers.product_controller import ProductController
from core.controllers.receipt_controller import ReceiptController
from core.controllers.warehouse_controller import WarehouseController
from core.cruds.seller_crud import CRUDSeller
from core.cruds.warehouse_crud import CRUDWarehouse
from core.models.user_model import User, UserRole

logging = logger(__name__)
MAX_RESULTS = 20
MAX_ACTIVITY_RESULTS = 10


class ToolExecutionError(Exception):
    """Represent a safe domain result from an approved WMS tool."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Store a safe error status and message for orchestration.

        Args:
            status_code: HTTP-compatible status code.
            detail: Client-safe tool error explanation.
        """
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True)
class ToolContext:
    """Carry server-derived user identity into every tool execution.

    Values are built only from the authenticated database user, never Gemini arguments.
    """

    current_user: User
    request_id: str


class InventoryToolInput(BaseModel):
    """Validate optional inventory product and warehouse filters."""

    product: Optional[str] = Field(None, max_length=128)
    warehouse: Optional[str] = Field(None, max_length=128)


class ProductToolInput(BaseModel):
    """Validate a product UPC, SKU, or name lookup query."""

    query: str = Field(..., min_length=1, max_length=128)


class ReceiptToolInput(BaseModel):
    """Validate bounded receipt list filters."""

    warehouse: Optional[str] = Field(None, max_length=128)
    status: Optional[str] = Field(None, max_length=32)
    reference: Optional[str] = Field(None, max_length=64)
    seller: Optional[str] = Field(None, max_length=128)


class OrderToolInput(BaseModel):
    """Validate bounded order list filters."""

    warehouse: Optional[str] = Field(None, max_length=128)
    status: Optional[str] = Field(None, max_length=32)
    reference: Optional[str] = Field(None, max_length=64)


class SummaryToolInput(BaseModel):
    """Validate an optional warehouse summary filter."""

    warehouse: Optional[str] = Field(None, max_length=128)


class ActivityToolInput(BaseModel):
    """Validate optional recent-activity filters."""

    warehouse: Optional[str] = Field(None, max_length=128)
    reference: Optional[str] = Field(None, max_length=64)


ToolHandler = Callable[[ToolContext, BaseModel], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ApprovedTool:
    """Define one allowlisted Gemini capability and its input contract."""

    name: str
    description: str
    input_model: type[BaseModel]
    handler: ToolHandler
    allowed_roles: tuple[UserRole, ...]


class ToolRegistry:
    """Execute only approved, read-only warehouse information tools.

    Tool names, schemas, roles, and handlers are fixed by server-side code.
    """

    def __init__(self) -> None:
        """Initialize explicit allowlisted tool definitions.

        No runtime registration or model-defined tool behavior is supported.
        """
        logging.info("Executing ToolRegistry.__init__")
        all_roles = tuple(UserRole)
        self._tools = {
            "get_inventory": ApprovedTool("get_inventory", "Get live inventory for a product in an authorized warehouse.", InventoryToolInput, self.get_inventory, all_roles),
            "lookup_product": ApprovedTool("lookup_product", "Look up a product by UPC, SKU, or name.", ProductToolInput, self.lookup_product, all_roles),
            "list_receipts": ApprovedTool("list_receipts", "List authorized receipt records with optional filters.", ReceiptToolInput, self.list_receipts, all_roles),
            "list_orders": ApprovedTool("list_orders", "List authorized order and fulfillment records with optional filters.", OrderToolInput, self.list_orders, all_roles),
            "get_operational_summary": ApprovedTool("get_operational_summary", "Compute live inventory, receipt, and order metrics for an authorized warehouse.", SummaryToolInput, self.get_operational_summary, all_roles),
            "get_recent_activity": ApprovedTool("get_recent_activity", "List authorized recent operational audit activity.", ActivityToolInput, self.get_recent_activity, (UserRole.OWNER, UserRole.MANAGER)),
        }

    def definitions(self) -> list[dict[str, Any]]:
        """Return provider-neutral function declarations for the approved tools.

        Returns:
            list[dict[str, Any]]: JSON-schema function definitions with no handlers or secrets.
        """
        logging.info("Executing ToolRegistry.definitions")
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters_json_schema": tool.input_model.model_json_schema(),
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Validate and execute one allowlisted tool with trusted user context.

        Args:
            name: Fixed server allowlist tool name requested by Gemini.
            arguments: Model-supplied business filters only.
            context: Server-derived authenticated user identity and request ID.

        Returns:
            dict[str, Any]: Bounded structured WMS facts.

        Raises:
            ToolExecutionError: If the tool is unknown, denied, or invalid.
        """
        logging.info("Executing ToolRegistry.execute")
        tool = self._tools.get(name)
        if not tool:
            logging.warning(f"Unknown AI tool rejected: {name}")
            raise ToolExecutionError(status.HTTP_400_BAD_REQUEST, "Requested assistant capability is not available")
        if context.current_user.role not in tool.allowed_roles:
            logging.warning(f"AI tool access denied for user {context.current_user.id}: {name}")
            raise ToolExecutionError(status.HTTP_403_FORBIDDEN, "You do not have permission to use that assistant capability")
        try:
            payload = tool.input_model.model_validate(arguments)
            result = await tool.handler(context, payload)
            logging.info(f"AI tool completed: {name} request={context.request_id}")
            return result
        except ToolExecutionError:
            raise
        except HTTPException as error:
            logging.warning(f"AI tool domain rejection: {name} status={error.status_code}")
            raise ToolExecutionError(error.status_code, str(error.detail)) from error
        except Exception as error:
            logging.error(f"Error in ToolRegistry.execute for {name}: {error}")
            raise ToolExecutionError(status.HTTP_500_INTERNAL_SERVER_ERROR, "Unable to retrieve warehouse information") from error

    async def _resolve_warehouse(self, value: Optional[str], context: ToolContext) -> Optional[dict[str, str]]:
        """Resolve an optional warehouse name, code, or ID and enforce server scope.

        Args:
            value: Model-supplied warehouse label or ObjectId string.
            context: Trusted authenticated user context.

        Returns:
            Optional[dict[str, str]]: Authorized warehouse identity, or None when unspecified.

        Raises:
            ToolExecutionError: If the warehouse is absent or outside user scope.
        """
        if not value:
            return None
        query = value.strip().lower()
        warehouses = await CRUDWarehouse().get_all()
        warehouse = next((item for item in warehouses if query in {str(item.id).lower(), item.code.lower(), item.name.lower(), item.city.lower()}), None)
        if not warehouse:
            raise ToolExecutionError(status.HTTP_404_NOT_FOUND, "Warehouse not found")
        if not can_access_warehouse(context.current_user, warehouse.id):
            logging.warning(f"AI warehouse access denied for user {context.current_user.id}: {warehouse.id}")
            raise ToolExecutionError(status.HTTP_403_FORBIDDEN, "You don't have access to this warehouse")
        return {"id": str(warehouse.id), "name": warehouse.name, "code": warehouse.code, "city": warehouse.city, "state": warehouse.state}

    async def _product_matches(self, query: Optional[str]) -> list[dict[str, Any]]:
        """Return product records matching a UPC, SKU, or case-insensitive name.

        Args:
            query: Optional product search value.

        Returns:
            list[dict[str, Any]]: Bounded safe product records.
        """
        products = await ProductController().list_products()
        if not query:
            return products[:MAX_RESULTS]
        normalized = query.strip().lower()
        return [product for product in products if normalized in {product["upc"].lower(), product["sku"].lower()} or normalized in product["name"].lower()][:MAX_RESULTS]

    @staticmethod
    def _enum_value(value: Any) -> str:
        """Return a serializable enum value without enum class-name formatting.

        Args:
            value: Enum or scalar value returned by an existing response model.

        Returns:
            str: Underlying enum value or scalar string.
        """
        return str(getattr(value, "value", value))

    async def get_inventory(self, context: ToolContext, payload: InventoryToolInput) -> dict[str, Any]:
        """Get bounded live inventory facts using the existing inventory controller.

        Args:
            context: Trusted authenticated user context.
            payload: Validated optional product and warehouse filters.

        Returns:
            dict[str, Any]: Inventory facts with product and warehouse labels.

        Raises:
            ToolExecutionError: If the requested product cannot be found.
        """
        logging.info("Executing ToolRegistry.get_inventory")
        warehouse = await self._resolve_warehouse(payload.warehouse, context)
        products = await self._product_matches(payload.product)
        if payload.product and not products:
            raise ToolExecutionError(status.HTTP_404_NOT_FOUND, "Product not found")
        records = []
        for product in products:
            snapshots = await InventoryController().list_inventory(warehouse_id=warehouse["id"] if warehouse else None, seller_id=None, product_id=product["id"], current_user=context.current_user)
            for snapshot in snapshots:
                records.append({
                    "product": product["name"], "sku": product["sku"], "upc": product["upc"],
                    "warehouse_id": snapshot.warehouse_id, "on_hand": snapshot.on_hand, "reserved": snapshot.reserved,
                    "available": snapshot.available, "damaged": snapshot.damaged,
                })
        warehouse_names = {item["id"]: item for item in await WarehouseController().list_warehouses(context.current_user)}
        for record in records:
            label = warehouse_names.get(record["warehouse_id"])
            record["warehouse"] = label["name"] if label else record["warehouse_id"]
            del record["warehouse_id"]
        return {"records": records[:MAX_RESULTS], "count": min(len(records), MAX_RESULTS), "limited": len(records) > MAX_RESULTS}

    async def lookup_product(self, context: ToolContext, payload: ProductToolInput) -> dict[str, Any]:
        """Look up products and sellers using existing product/seller WMS logic.

        Args:
            context: Trusted authenticated user context.
            payload: Validated UPC, SKU, or product-name query.

        Returns:
            dict[str, Any]: Bounded safe product identity records.

        Raises:
            ToolExecutionError: If no product matches the query.
        """
        logging.info("Executing ToolRegistry.lookup_product")
        products = await self._product_matches(payload.query)
        if not products:
            raise ToolExecutionError(status.HTTP_404_NOT_FOUND, "Product not found")
        seller_crud = CRUDSeller()
        records = []
        for product in products:
            seller = await seller_crud.get_by_id(id=product["seller_id"])
            records.append({"product": product["name"], "sku": product["sku"], "upc": product["upc"], "seller": seller.name if seller else "Unknown seller", "status": self._enum_value(product["status"])})
        return {"records": records, "count": len(records), "limited": False}

    async def list_receipts(self, context: ToolContext, payload: ReceiptToolInput) -> dict[str, Any]:
        """List authorized receipt records through the existing receipt controller.

        Args:
            context: Trusted authenticated user context.
            payload: Validated receipt filters.

        Returns:
            dict[str, Any]: Bounded receipt records and count.
        """
        logging.info("Executing ToolRegistry.list_receipts")
        warehouse = await self._resolve_warehouse(payload.warehouse, context)
        seller_id = None
        if payload.seller:
            seller_query = payload.seller.strip().lower()
            seller = next((item for item in await CRUDSeller().get_all() if seller_query in {str(item.id).lower(), item.seller_code.lower()} or seller_query in item.name.lower()), None)
            if not seller:
                raise ToolExecutionError(status.HTTP_404_NOT_FOUND, "Seller not found")
            seller_id = str(seller.id)
        receipts = await ReceiptController().list_receipts(warehouse_id=warehouse["id"] if warehouse else None, seller_id=seller_id, status_param=payload.status, tracking_number=None, current_user=context.current_user)
        reference = payload.reference.lower() if payload.reference else None
        rows = [item for item in receipts if not reference or reference in item.receipt_number.lower()]
        return {"records": [{"reference": item.receipt_number, "warehouse_id": item.warehouse_id, "seller_id": item.seller_id, "status": self._enum_value(item.status), "tracking_number": item.tracking_number, "ticket_number": item.ticket_number, "item_count": len(item.items), "created_at": item.created_at.isoformat()} for item in rows[:MAX_RESULTS]], "count": min(len(rows), MAX_RESULTS), "limited": len(rows) > MAX_RESULTS}

    async def list_orders(self, context: ToolContext, payload: OrderToolInput) -> dict[str, Any]:
        """List authorized order records through the existing order controller.

        Args:
            context: Trusted authenticated user context.
            payload: Validated order filters.

        Returns:
            dict[str, Any]: Bounded order and fulfillment facts.
        """
        logging.info("Executing ToolRegistry.list_orders")
        warehouse = await self._resolve_warehouse(payload.warehouse, context)
        orders = await OrderController().list_orders(warehouse_id=warehouse["id"] if warehouse else None, seller_id=None, status_filter=payload.status, order_number=payload.reference, current_user=context.current_user)
        return {"records": [{"reference": item.order_number, "warehouse_id": item.warehouse_id, "seller_id": item.seller_id, "status": self._enum_value(item.status), "item_count": len(item.items), "created_at": item.created_at.isoformat()} for item in orders[:MAX_RESULTS]], "count": min(len(orders), MAX_RESULTS), "limited": len(orders) > MAX_RESULTS}

    async def get_operational_summary(self, context: ToolContext, payload: SummaryToolInput) -> dict[str, Any]:
        """Compute deterministic dashboard-aligned operations metrics.

        Args:
            context: Trusted authenticated user context.
            payload: Validated optional warehouse filter.

        Returns:
            dict[str, Any]: Deterministic stock, receipt, and order metrics.
        """
        logging.info("Executing ToolRegistry.get_operational_summary")
        warehouse = await self._resolve_warehouse(payload.warehouse, context)
        warehouse_id = warehouse["id"] if warehouse else None
        inventory = await InventoryController().list_inventory(warehouse_id=warehouse_id, seller_id=None, product_id=None, current_user=context.current_user)
        receipts = await ReceiptController().list_receipts(warehouse_id=warehouse_id, seller_id=None, status_param=None, tracking_number=None, current_user=context.current_user)
        orders = await OrderController().list_orders(warehouse_id=warehouse_id, seller_id=None, status_filter=None, order_number=None, current_user=context.current_user)
        status_counts = {state: sum(1 for item in orders if self._enum_value(item.status) == state) for state in ("NEW", "RESERVED", "PICKING", "PICKED", "PACKED", "READY_TO_SHIP")}
        return {"warehouse": warehouse["name"] if warehouse else "All authorized warehouses", "total_on_hand": sum(item.on_hand for item in inventory), "available": sum(item.available for item in inventory), "reserved": sum(item.reserved for item in inventory), "damaged": sum(item.damaged for item in inventory), "pending_receipts": sum(1 for item in receipts if self._enum_value(item.status) in {"DRAFT", "IN_PROGRESS"}), "open_orders": sum(1 for item in orders if self._enum_value(item.status) not in {"SHIPPED", "CANCELLED"}), "orders_to_pick": status_counts["RESERVED"], "picking": status_counts["PICKING"], "ready_to_pack": status_counts["PICKED"], "ready_to_ship": status_counts["READY_TO_SHIP"]}

    async def get_recent_activity(self, context: ToolContext, payload: ActivityToolInput) -> dict[str, Any]:
        """List authorized audit activity using the existing audit controller policy.

        Args:
            context: Trusted authenticated user context.
            payload: Validated optional activity filters.

        Returns:
            dict[str, Any]: Newest-first bounded audit records.
        """
        logging.info("Executing ToolRegistry.get_recent_activity")
        warehouse = await self._resolve_warehouse(payload.warehouse, context)
        audits = await InventoryController().list_audits(warehouse_id=warehouse["id"] if warehouse else None, user_id=None, action=None, entity_type=None, entity_id=payload.reference, current_user=context.current_user)
        records = sorted(audits, key=lambda item: item.created_at, reverse=True)[:MAX_ACTIVITY_RESULTS]
        return {"records": [{"action": item.action, "entity_type": item.entity_type, "entity_id": item.entity_id, "warehouse_id": item.warehouse_id, "created_at": item.created_at.isoformat()} for item in records], "count": len(records), "limited": len(audits) > MAX_ACTIVITY_RESULTS}
