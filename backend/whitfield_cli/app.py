"""Typer command tree for the HTTP-only Whitfield WMS CLI."""

import getpass
import os
import re
import sys
from typing import Any, Optional

import typer

from whitfield_cli import __version__
from whitfield_cli.client import APIClient, CLIError
from whitfield_cli.output import emit, error
from whitfield_cli.session import clear_token, load_token, save_token

app = typer.Typer(help="Secure HTTP client for Whitfield WMS.", no_args_is_help=True)
auth_app = typer.Typer(help="Authenticate with Whitfield WMS.")
warehouses_app = typer.Typer(help="Read authorized warehouse records.")
sellers_app = typer.Typer(help="Read seller master data.")
products_app = typer.Typer(help="Read product master data.")
inventory_app = typer.Typer(help="Read inventory and controlled movement data.")
receipts_app = typer.Typer(help="Use receiving workflow endpoints.")
orders_app = typer.Typer(help="Use fulfillment workflow endpoints.")
audit_app = typer.Typer(help="Read authorized audit records.")
users_app = typer.Typer(help="Use Owner-only employee provisioning endpoints.")

app.add_typer(auth_app, name="auth")
app.add_typer(warehouses_app, name="warehouses")
app.add_typer(sellers_app, name="sellers")
app.add_typer(products_app, name="products")
app.add_typer(inventory_app, name="inventory")
app.add_typer(receipts_app, name="receipts")
app.add_typer(orders_app, name="orders")
app.add_typer(audit_app, name="audit")
app.add_typer(users_app, name="users")


def _default_api_url() -> str:
    """Return the configurable local-development FastAPI base URL.

    Returns:
        str: API URL from environment or a local default.
    """
    return os.getenv("WHITFIELD_API_URL", "http://127.0.0.1:8000")


@app.callback()
def root(
    ctx: typer.Context,
    api_url: str = typer.Option(_default_api_url(), "--api-url", help="Whitfield FastAPI base URL."),
    as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout."),
    timeout: float = typer.Option(15.0, min=1.0, max=60.0, help="HTTP timeout in seconds."),
) -> None:
    """Initialize command context from safe client configuration.

    Args:
        ctx: Typer context shared with subcommands.
        api_url: FastAPI base URL; never used as an authorization override.
        as_json: Whether read responses use JSON-only stdout.
        timeout: Bounded HTTP request timeout.
    """
    token, token_source = load_token()
    ctx.obj = {"client": APIClient(api_url=api_url, token=token, timeout=timeout), "json": as_json, "token_source": token_source}


def _state(ctx: typer.Context) -> dict[str, Any]:
    """Return the initialized global CLI state.

    Args:
        ctx: Current Typer command context.

    Returns:
        dict[str, Any]: Shared client, JSON preference, and token source.
    """
    return ctx.find_root().obj


def _client(ctx: typer.Context) -> APIClient:
    """Return the configured HTTP-only FastAPI client.

    Args:
        ctx: Current Typer command context.

    Returns:
        APIClient: Shared authenticated API client.
    """
    return _state(ctx)["client"]


def _output(ctx: typer.Context, value: Any, as_json: bool | None = None) -> None:
    """Emit a command result using the global JSON preference.

    Args:
        ctx: Current Typer command context.
        value: JSON-compatible FastAPI response.
        as_json: Optional command-level JSON override.
    """
    emit(value, _state(ctx)["json"] if as_json is None else as_json)


def _fail(error_value: CLIError) -> None:
    """Write a normalized error and terminate with its documented exit code.

    Args:
        error_value: Safe error returned by the CLI HTTP client.
    """
    error(str(error_value))
    raise typer.Exit(error_value.exit_code)


def _resolve(ctx: typer.Context, endpoint: str, value: str, *, code_key: str, name_key: str = "name") -> str:
    """Resolve an ID, code, or name through an authorized master-data endpoint.

    Args:
        ctx: Current Typer command context.
        endpoint: Collection route used for lookup.
        value: User-provided ID, code, or name.
        code_key: Response field used for code matching.
        name_key: Response field used for name matching.

    Returns:
        str: Backend object ID.

    Raises:
        typer.Exit: When no authorized record matches.
    """
    if re.fullmatch(r"[0-9a-fA-F]{24}", value.strip()):
        return value.strip()
    try:
        rows = _client(ctx).request("GET", endpoint)
    except CLIError as error_value:
        _fail(error_value)
    query = value.strip().lower()
    for row in rows:
        candidates = (str(row.get("id", "")).lower(), str(row.get(code_key, "")).lower(), str(row.get(name_key, "")).lower(), str(row.get("city", "")).lower())
        if query in candidates or any(query in candidate for candidate in candidates if candidate):
            return str(row["id"])
    _fail(CLIError(f"Not found: {value}", 5))
    raise AssertionError("unreachable")


def _confirm(action: str, yes: bool) -> None:
    """Require affirmative consent before a high-impact mutation.

    Args:
        action: Human-readable mutation description.
        yes: Explicit non-interactive confirmation flag.

    Raises:
        typer.Exit: If the action is declined or lacks `--yes` in non-interactive mode.
    """
    if yes:
        return
    if not sys.stdin.isatty():
        error(f"Confirmation required for {action}. Re-run with --yes.")
        raise typer.Exit(2)
    if not typer.confirm(f"Proceed to {action}?", default=False):
        error("Operation cancelled.")
        raise typer.Exit(2)


@app.command()
def version() -> None:
    """Print the CLI version without calling the backend."""
    print(f"Whitfield CLI {__version__}")


@app.command()
def health(ctx: typer.Context) -> None:
    """Check backend availability through the public FastAPI health route.

    Args:
        ctx: Current Typer command context.
    """
    try:
        _output(ctx, _client(ctx).request("GET", "/", authenticated=False))
    except CLIError as error_value:
        _fail(error_value)


@auth_app.command("login")
def login(ctx: typer.Context, email: Optional[str] = typer.Option(None, prompt=True, help="WMS account email.")) -> None:
    """Authenticate with FastAPI and save only the returned access token.

    Args:
        ctx: Current Typer command context.
        email: Account email, prompted when omitted.
    """
    password = getpass.getpass("Password: ")
    try:
        response = _client(ctx).request("POST", "/v1/auth/login", payload={"email": email, "password": password}, authenticated=False)
        save_token(str(response["access_token"]))
        _state(ctx)["client"].token = str(response["access_token"])
        _output(ctx, {"authenticated": True, "user": response.get("user", {})})
    except CLIError as error_value:
        _fail(error_value)


@auth_app.command("logout")
def logout(ctx: typer.Context) -> None:
    """Remove the local session token without attempting server-side token mutation.

    Args:
        ctx: Current Typer command context.
    """
    clear_token()
    _state(ctx)["client"].token = None
    _output(ctx, {"authenticated": False})


@auth_app.command("status")
def auth_status(ctx: typer.Context) -> None:
    """Report token presence without displaying its value.

    Args:
        ctx: Current Typer command context.
    """
    state = _state(ctx)
    _output(ctx, {"authenticated": bool(state["client"].token), "token_source": state["token_source"]})


@auth_app.command("whoami")
def whoami(ctx: typer.Context, as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """Display backend-derived identity, role, status, and warehouse scope.

    Args:
        ctx: Current Typer command context.
        as_json: Whether stdout must contain JSON only.
    """
    try:
        _output(ctx, _client(ctx).request("GET", "/v1/auth/me"), as_json)
    except CLIError as error_value:
        _fail(error_value)


def _read_commands(group: typer.Typer, endpoint: str, singular: str, code_key: str) -> None:
    """Register standard list and show commands for an authorized collection.

    Args:
        group: Typer subapplication receiving commands.
        endpoint: Existing FastAPI collection endpoint.
        singular: Resource label for command help.
        code_key: Resource code field for identifier resolution.
    """
    @group.command("list")
    def list_records(ctx: typer.Context, as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
        """List records visible to the authenticated backend user.

        Args:
            ctx: Current Typer command context.
            as_json: Whether stdout must contain JSON only.
        """
        try:
            _output(ctx, _client(ctx).request("GET", endpoint), as_json)
        except CLIError as error_value:
            _fail(error_value)

    @group.command("show")
    def show_record(ctx: typer.Context, identifier: str, as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
        """Show one record after resolving an authorized identifier.

        Args:
            ctx: Current Typer command context.
            identifier: Resource ID, code, or name.
            as_json: Whether stdout must contain JSON only.
        """
        resource_id = _resolve(ctx, endpoint, identifier, code_key=code_key)
        try:
            _output(ctx, _client(ctx).request("GET", f"{endpoint}/{resource_id}"), as_json)
        except CLIError as error_value:
            _fail(error_value)


_read_commands(warehouses_app, "/v1/warehouses", "warehouse", "code")
_read_commands(sellers_app, "/v1/sellers", "seller", "seller_code")
_read_commands(products_app, "/v1/products", "product", "sku")


@products_app.command("lookup")
def product_lookup(ctx: typer.Context, upc: str = typer.Option(..., "--upc", min=1), as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """Look up one product by UPC through the existing FastAPI scanner endpoint.

    Args:
        ctx: Current Typer command context.
        upc: Product barcode value.
        as_json: Whether stdout must contain JSON only.
    """
    try:
        _output(ctx, _client(ctx).request("GET", f"/v1/products/upc/{upc}"), as_json)
    except CLIError as error_value:
        _fail(error_value)


@inventory_app.command("list")
def inventory_list(ctx: typer.Context, warehouse: Optional[str] = typer.Option(None), seller: Optional[str] = typer.Option(None), product: Optional[str] = typer.Option(None), as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """List authorized inventory snapshots with optional human identifier filters.

    Args:
        ctx: Current Typer command context.
        warehouse: Optional warehouse ID, code, or name.
        seller: Optional seller ID, code, or name.
        product: Optional product ID, SKU, or name.
        as_json: Whether stdout must contain JSON only.
    """
    params = {"warehouse_id": _resolve(ctx, "/v1/warehouses", warehouse, code_key="code") if warehouse else None, "seller_id": _resolve(ctx, "/v1/sellers", seller, code_key="seller_code") if seller else None, "product_id": _resolve(ctx, "/v1/products", product, code_key="sku") if product else None}
    try:
        _output(ctx, _client(ctx).request("GET", "/v1/inventory", params=params), as_json)
    except CLIError as error_value:
        _fail(error_value)


@inventory_app.command("get")
def inventory_get(ctx: typer.Context, warehouse: str = typer.Option(...), upc: Optional[str] = typer.Option(None), sku: Optional[str] = typer.Option(None), product: Optional[str] = typer.Option(None), as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """Get inventory for one product and one authorized warehouse.

    Args:
        ctx: Current Typer command context.
        warehouse: Warehouse ID, code, or name.
        upc: Optional product UPC.
        sku: Optional product SKU.
        product: Optional product ID or name.
        as_json: Whether stdout must contain JSON only.
    """
    supplied = [value for value in (upc, sku, product) if value]
    if len(supplied) != 1:
        error("Provide exactly one of --upc, --sku, or --product.")
        raise typer.Exit(2)
    product_id = _client(ctx).request("GET", f"/v1/products/upc/{upc}")["id"] if upc else _resolve(ctx, "/v1/products", supplied[0], code_key="sku")
    warehouse_id = _resolve(ctx, "/v1/warehouses", warehouse, code_key="code")
    try:
        records = _client(ctx).request("GET", "/v1/inventory", params={"warehouse_id": warehouse_id, "product_id": product_id})
        if not records:
            _fail(CLIError("Not found: no inventory snapshot for the requested product and warehouse.", 5))
        for record in records:
            if record["available"] != record["on_hand"] - record["reserved"]:
                _fail(CLIError("Backend inventory inconsistency: available does not equal on_hand minus reserved.", 1))
        _output(ctx, records[0] if len(records) == 1 else records, as_json)
    except CLIError as error_value:
        _fail(error_value)


@inventory_app.command("movements")
def inventory_movements(ctx: typer.Context, inventory_id: str, movement_type: Optional[str] = typer.Option(None), as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """List movement history for an authorized inventory snapshot.

    Args:
        ctx: Current Typer command context.
        inventory_id: Inventory snapshot ID.
        movement_type: Optional backend movement type filter.
        as_json: Whether stdout must contain JSON only.
    """
    try:
        _output(ctx, _client(ctx).request("GET", f"/v1/inventory/{inventory_id}/movements", params={"movement_type": movement_type}), as_json)
    except CLIError as error_value:
        _fail(error_value)


@receipts_app.command("list")
def receipts_list(ctx: typer.Context, warehouse: Optional[str] = typer.Option(None), seller: Optional[str] = typer.Option(None), status: Optional[str] = typer.Option(None), tracking: Optional[str] = typer.Option(None), as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """List receipt records visible to the authenticated WMS user.

    Args:
        ctx: Current Typer command context.
        warehouse: Optional warehouse ID, code, or name.
        seller: Optional seller ID, code, or name.
        status: Optional backend receipt status.
        tracking: Optional shipment tracking number.
        as_json: Whether stdout must contain JSON only.
    """
    params = {"warehouse_id": _resolve(ctx, "/v1/warehouses", warehouse, code_key="code") if warehouse else None, "seller_id": _resolve(ctx, "/v1/sellers", seller, code_key="seller_code") if seller else None, "status": status, "tracking_number": tracking}
    try:
        _output(ctx, _client(ctx).request("GET", "/v1/receipts", params=params), as_json)
    except CLIError as error_value:
        _fail(error_value)


@receipts_app.command("show")
def receipt_show(ctx: typer.Context, receipt_id: str, as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """Show one receipt using its backend ID.

    Args:
        ctx: Current Typer command context.
        receipt_id: Receipt ObjectId string.
        as_json: Whether stdout must contain JSON only.
    """
    try:
        _output(ctx, _client(ctx).request("GET", f"/v1/receipts/{receipt_id}"), as_json)
    except CLIError as error_value:
        _fail(error_value)


@receipts_app.command("create")
def receipt_create(ctx: typer.Context, warehouse: str = typer.Option(...), seller: str = typer.Option(...), tracking: Optional[str] = typer.Option(None), ticket: Optional[str] = typer.Option(None), idempotency_key: Optional[str] = typer.Option(None)) -> None:
    """Create an inbound receipt through the existing receiving workflow API.

    Args:
        ctx: Current Typer command context.
        warehouse: Warehouse ID, code, or name.
        seller: Seller ID, code, or name.
        tracking: Optional physical shipment tracking number.
        ticket: Optional internal or vendor ticket number.
        idempotency_key: Optional backend idempotency key.
    """
    if not tracking and not ticket:
        error("Provide --tracking or --ticket.")
        raise typer.Exit(2)
    payload = {"warehouse_id": _resolve(ctx, "/v1/warehouses", warehouse, code_key="code"), "seller_id": _resolve(ctx, "/v1/sellers", seller, code_key="seller_code"), "tracking_number": tracking, "ticket_number": ticket, "idempotency_key": idempotency_key}
    try:
        _output(ctx, _client(ctx).request("POST", "/v1/receipts", payload=payload))
    except CLIError as error_value:
        _fail(error_value)


@receipts_app.command("add-item")
def receipt_add_item(ctx: typer.Context, receipt_id: str, upc: str = typer.Option(...), good: int = typer.Option(0, min=0), damaged: int = typer.Option(0, min=0)) -> None:
    """Add an item by UPC with client-side quantity guards and backend validation.

    Args:
        ctx: Current Typer command context.
        receipt_id: Receipt ObjectId string.
        upc: Registered product UPC.
        good: Whole good quantity greater than or equal to zero.
        damaged: Whole damaged quantity greater than or equal to zero.
    """
    if good + damaged <= 0:
        error("At least one unit must be received.")
        raise typer.Exit(2)
    try:
        _output(ctx, _client(ctx).request("POST", f"/v1/receipts/{receipt_id}/items", payload={"upc": upc, "good_qty": good, "damaged_qty": damaged}))
    except CLIError as error_value:
        _fail(error_value)


@receipts_app.command("complete")
def receipt_complete(ctx: typer.Context, receipt_id: str, yes: bool = typer.Option(False, "--yes", help="Confirm inventory-affecting completion.")) -> None:
    """Complete a receipt after explicit confirmation.

    Args:
        ctx: Current Typer command context.
        receipt_id: Receipt ObjectId string.
        yes: Explicit non-interactive confirmation.
    """
    _confirm("complete this receipt and apply inventory", yes)
    try:
        _output(ctx, _client(ctx).request("POST", f"/v1/receipts/{receipt_id}/complete"))
    except CLIError as error_value:
        _fail(error_value)


@orders_app.command("list")
def orders_list(ctx: typer.Context, warehouse: Optional[str] = typer.Option(None), seller: Optional[str] = typer.Option(None), status: Optional[str] = typer.Option(None), order_number: Optional[str] = typer.Option(None), as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """List authorized order records using supported backend filters.

    Args:
        ctx: Current Typer command context.
        warehouse: Optional warehouse ID, code, or name.
        seller: Optional seller ID, code, or name.
        status: Optional backend order status.
        order_number: Optional order number filter.
        as_json: Whether stdout must contain JSON only.
    """
    params = {"warehouse_id": _resolve(ctx, "/v1/warehouses", warehouse, code_key="code") if warehouse else None, "seller_id": _resolve(ctx, "/v1/sellers", seller, code_key="seller_code") if seller else None, "status": status, "order_number": order_number}
    try:
        _output(ctx, _client(ctx).request("GET", "/v1/orders", params=params), as_json)
    except CLIError as error_value:
        _fail(error_value)


@orders_app.command("show")
def order_show(ctx: typer.Context, order_id: str, as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """Show one order using its backend ID.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
        as_json: Whether stdout must contain JSON only.
    """
    try:
        _output(ctx, _client(ctx).request("GET", f"/v1/orders/{order_id}"), as_json)
    except CLIError as error_value:
        _fail(error_value)


@orders_app.command("create")
def order_create(ctx: typer.Context, warehouse: str = typer.Option(...), seller: str = typer.Option(...), sku: str = typer.Option(...), quantity: int = typer.Option(..., min=1), order_number: Optional[str] = typer.Option(None), idempotency_key: Optional[str] = typer.Option(None)) -> None:
    """Create a single-line order through the existing order API.

    Args:
        ctx: Current Typer command context.
        warehouse: Warehouse ID, code, or name.
        seller: Seller ID, code, or name.
        sku: Product SKU for the order line.
        quantity: Positive whole order quantity.
        order_number: Optional custom order reference.
        idempotency_key: Optional backend idempotency key.
    """
    payload = {"warehouse_id": _resolve(ctx, "/v1/warehouses", warehouse, code_key="code"), "seller_id": _resolve(ctx, "/v1/sellers", seller, code_key="seller_code"), "order_number": order_number, "items": [{"sku": sku, "quantity": quantity}], "idempotency_key": idempotency_key}
    try:
        _output(ctx, _client(ctx).request("POST", "/v1/orders", payload=payload))
    except CLIError as error_value:
        _fail(error_value)


def _order_transition(ctx: typer.Context, order_id: str, suffix: str) -> None:
    """Call one existing order transition endpoint without local state decisions.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
        suffix: Existing FastAPI route suffix.
    """
    try:
        _output(ctx, _client(ctx).request("POST", f"/v1/orders/{order_id}/{suffix}"))
    except CLIError as error_value:
        _fail(error_value)


@orders_app.command("reserve")
def order_reserve(ctx: typer.Context, order_id: str) -> None:
    """Reserve stock for an order through backend oversell protection.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
    """
    _order_transition(ctx, order_id, "reserve")


@orders_app.command("start-picking")
def order_start_picking(ctx: typer.Context, order_id: str) -> None:
    """Transition an order from RESERVED to PICKING through FastAPI.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
    """
    _order_transition(ctx, order_id, "start-picking")


@orders_app.command("mark-picked")
def order_mark_picked(ctx: typer.Context, order_id: str) -> None:
    """Transition an order from PICKING to PICKED through FastAPI.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
    """
    _order_transition(ctx, order_id, "picked")


@orders_app.command("pack")
def order_pack(ctx: typer.Context, order_id: str) -> None:
    """Transition an order from PICKED to PACKED through FastAPI.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
    """
    _order_transition(ctx, order_id, "packed")


@orders_app.command("shipment")
def order_shipment(ctx: typer.Context, order_id: str, carrier: str = typer.Option(...), tracking: str = typer.Option(...), weight: float = typer.Option(0.0, min=0.0), length: float = typer.Option(0.0, min=0.0), width: float = typer.Option(0.0, min=0.0), height: float = typer.Option(0.0, min=0.0), label_reference: Optional[str] = typer.Option(None)) -> None:
    """Prepare shipment details and transition a packed order through FastAPI.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
        carrier: Carrier name.
        tracking: Carrier tracking number.
        weight: Package weight in pounds.
        length: Package length in inches.
        width: Package width in inches.
        height: Package height in inches.
        label_reference: Optional carrier label reference.
    """
    payload = {"carrier": carrier, "tracking_number": tracking, "weight": weight, "length": length, "width": width, "height": height, "label_reference": label_reference}
    try:
        _output(ctx, _client(ctx).request("POST", f"/v1/orders/{order_id}/shipment", payload=payload))
    except CLIError as error_value:
        _fail(error_value)


@orders_app.command("ship")
def order_ship(ctx: typer.Context, order_id: str, yes: bool = typer.Option(False, "--yes", help="Confirm inventory-affecting shipping.")) -> None:
    """Ship a ready order after explicit confirmation.

    Args:
        ctx: Current Typer command context.
        order_id: Order ObjectId string.
        yes: Explicit non-interactive confirmation.
    """
    _confirm("ship this order and decrement inventory", yes)
    _order_transition(ctx, order_id, "ship")


@audit_app.command("recent")
def audit_recent(ctx: typer.Context, warehouse: Optional[str] = typer.Option(None), action: Optional[str] = typer.Option(None), entity_type: Optional[str] = typer.Option(None), entity_id: Optional[str] = typer.Option(None), as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """List audit records allowed by the existing backend role policy.

    Args:
        ctx: Current Typer command context.
        warehouse: Optional warehouse ID, code, or name.
        action: Optional audit action filter.
        entity_type: Optional entity type filter.
        entity_id: Optional entity ID filter.
        as_json: Whether stdout must contain JSON only.
    """
    params = {"warehouse_id": _resolve(ctx, "/v1/warehouses", warehouse, code_key="code") if warehouse else None, "action": action, "entity_type": entity_type, "entity_id": entity_id}
    try:
        _output(ctx, _client(ctx).request("GET", "/v1/audit-logs", params=params), as_json)
    except CLIError as error_value:
        _fail(error_value)


@users_app.command("list")
def users_list(ctx: typer.Context, as_json: bool = typer.Option(False, "--json", help="Write JSON only to stdout.")) -> None:
    """List employee accounts through the Owner-only FastAPI endpoint.

    Args:
        ctx: Current Typer command context.
        as_json: Whether stdout must contain JSON only.
    """
    try:
        _output(ctx, _client(ctx).request("GET", "/v1/users"), as_json)
    except CLIError as error_value:
        _fail(error_value)


@users_app.command("create")
def users_create(ctx: typer.Context, first_name: str = typer.Option(...), last_name: str = typer.Option(...), email: str = typer.Option(...), role: str = typer.Option(...), warehouse: list[str] = typer.Option([], "--warehouse"), mobile: Optional[str] = typer.Option(None)) -> None:
    """Provision an employee with a hidden temporary password through FastAPI.

    Args:
        ctx: Current Typer command context.
        first_name: Employee first name.
        last_name: Employee last name.
        email: Employee login email.
        role: Existing WMS role value.
        warehouse: One or more warehouse ID, code, or name values.
        mobile: Optional employee mobile number.
    """
    password = getpass.getpass("Temporary password: ")
    payload = {"first_name": first_name, "last_name": last_name, "email": email, "password": password, "role": role, "warehouse_ids": [_resolve(ctx, "/v1/warehouses", value, code_key="code") for value in warehouse], "mobile_number": mobile}
    try:
        _output(ctx, _client(ctx).request("POST", "/v1/users", payload=payload))
    except CLIError as error_value:
        _fail(error_value)


def run() -> None:
    """Run the Typer application for packaging or test harness callers."""
    app()
