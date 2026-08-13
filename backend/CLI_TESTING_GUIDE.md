# Whitfield CLI Copy-Paste Test Guide

This guide tests every implemented Whitfield CLI command against the local FastAPI backend. Run it in a normal interactive PowerShell window so hidden password prompts work correctly.

## Before You Start

- Start the backend at `http://127.0.0.1:8000`.
- Use only local demo/test data. Receipt completion and order shipping intentionally change inventory.
- Never paste a password, JWT, MongoDB URI, or Gemini key into a command or script.
- The commands below use the current known catalog data: `Reno`, seller `SEL01`, SKU `WIDGET-A`, UPC `194253397168`.

```powershell
cd D:\WMS\backend
$Cli = ".\.venv\Scripts\python.exe"
& $Cli -m whitfield_cli health
& $Cli -m whitfield_cli version
& $Cli -m whitfield_cli --help
```

Expected: health, version, and help return exit code `0`.

## Authentication

Run each login command in an interactive terminal. The password prompt is hidden; type the password and press Enter. Do not put a password after the command.

```powershell
& $Cli -m whitfield_cli auth login --email owner@whitfield.com
& $Cli -m whitfield_cli auth status
& $Cli -m whitfield_cli auth whoami --json
& $Cli -m whitfield_cli auth logout
& $Cli -m whitfield_cli auth status
```

Repeat with the other demo roles when testing RBAC:

```powershell
& $Cli -m whitfield_cli auth login --email receiving@whitfield.com
& $Cli -m whitfield_cli auth whoami --json
& $Cli -m whitfield_cli auth logout

& $Cli -m whitfield_cli auth login --email fulfillment@whitfield.com
& $Cli -m whitfield_cli auth whoami --json
& $Cli -m whitfield_cli auth logout

& $Cli -m whitfield_cli auth login --email manager@whitfield.com
& $Cli -m whitfield_cli auth whoami --json
& $Cli -m whitfield_cli auth logout
```

Expected: no command prints a JWT. `auth status` reports only whether a token exists and its source.

## Login As Owner

Use Owner for master-data, audit, and user-management tests.

```powershell
& $Cli -m whitfield_cli auth login --email owner@whitfield.com
```

## Warehouses, Sellers, And Products

```powershell
& $Cli -m whitfield_cli warehouses list --json
& $Cli -m whitfield_cli warehouses show Reno --json
& $Cli -m whitfield_cli warehouses show Columbus --json

& $Cli -m whitfield_cli sellers list --json
& $Cli -m whitfield_cli sellers show SEL01 --json

& $Cli -m whitfield_cli products list --json
& $Cli -m whitfield_cli products show WIDGET-A --json
& $Cli -m whitfield_cli products lookup --upc 194253397168 --json
```

Unknown UPC test:

```powershell
& $Cli -m whitfield_cli products lookup --upc 999999999999
Write-Output "Exit code: $LASTEXITCODE"
```

Expected: friendly not-found response and exit code `5`.

## Inventory And Movements

This block is safe to paste. It captures the live Widget A / Reno inventory ID for the movement command.

```powershell
$WidgetInventory = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
$WidgetInventory
Write-Output "Available: $($WidgetInventory.available)"
Write-Output "Invariant: $($WidgetInventory.available -eq ($WidgetInventory.on_hand - $WidgetInventory.reserved))"

& $Cli -m whitfield_cli inventory list --warehouse Reno --json
& $Cli -m whitfield_cli inventory list --seller SEL01 --json
& $Cli -m whitfield_cli inventory list --product WIDGET-A --json
& $Cli -m whitfield_cli inventory get --sku WIDGET-A --warehouse Reno --json
& $Cli -m whitfield_cli inventory get --product 'Widget A' --warehouse Reno --json
& $Cli -m whitfield_cli inventory movements $WidgetInventory.id --json
```

Expected: `Invariant: True`.

## Receipt Read Commands

```powershell
& $Cli -m whitfield_cli receipts list --warehouse Reno --json
& $Cli -m whitfield_cli receipts list --status DRAFT --json
```

Choose an ID from the `receipts list` result, then run:

```powershell
$ReceiptId = "PASTE_RECEIPT_ID_HERE"
& $Cli -m whitfield_cli receipts show $ReceiptId --json
```

## Controlled Receiving Workflow

This workflow changes Widget A / Reno inventory. Use it only with `RECEIVING_STAFF` or an authorized Owner/Manager account. It creates a fresh `CLI-TEST-` receipt and adds 2 good plus 1 damaged unit.

```powershell
& $Cli -m whitfield_cli auth logout
& $Cli -m whitfield_cli auth login --email receiving@whitfield.com

$BeforeReceipt = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
$Timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$Tracking = "CLI-TEST-RECEIPT-$Timestamp"
$ReceiptOutput = & $Cli -m whitfield_cli receipts create --warehouse Reno --seller SEL01 --tracking $Tracking
$ReceiptOutput
$ReceiptId = ([regex]::Match(($ReceiptOutput -join "`n"), 'Id:\s*([0-9a-f]{24})')).Groups[1].Value
if (-not $ReceiptId) { throw "CLI did not return a receipt ID." }

& $Cli -m whitfield_cli receipts add-item $ReceiptId --upc 194253397168 --good 2 --damaged 1
& $Cli -m whitfield_cli receipts complete $ReceiptId --yes

$AfterReceipt = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
Write-Output "On hand delta: $($AfterReceipt.on_hand - $BeforeReceipt.on_hand)"
Write-Output "Damaged delta: $($AfterReceipt.damaged - $BeforeReceipt.damaged)"

# Idempotency check: this must not apply inventory a second time.
& $Cli -m whitfield_cli receipts complete $ReceiptId --yes
$AfterReceiptRetry = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
Write-Output "Retry unchanged: $($AfterReceiptRetry.on_hand -eq $AfterReceipt.on_hand -and $AfterReceiptRetry.damaged -eq $AfterReceipt.damaged)"
```

Expected: on-hand delta `2`, damaged delta `1`, and `Retry unchanged: True`.

### Receipt Validation And Authorization Checks

These are safe failed requests. They must not modify inventory.

```powershell
# Unknown UPC: backend should return a friendly 404/exit 5.
& $Cli -m whitfield_cli receipts add-item $ReceiptId --upc 999999999999 --good 1 --damaged 0
Write-Output "Unknown UPC exit: $LASTEXITCODE"

# CLI validation: no item can have zero total quantity.
& $Cli -m whitfield_cli receipts add-item $ReceiptId --upc 194253397168 --good 0 --damaged 0
Write-Output "Zero quantity exit: $LASTEXITCODE"

# Typer validation: negative and decimal values are rejected before a backend mutation.
& $Cli -m whitfield_cli receipts add-item $ReceiptId --upc 194253397168 --good -1 --damaged 0
Write-Output "Negative quantity exit: $LASTEXITCODE"
& $Cli -m whitfield_cli receipts add-item $ReceiptId --upc 194253397168 --good 1.5 --damaged 0
Write-Output "Decimal quantity exit: $LASTEXITCODE"

# Completed receipts cannot accept another item.
& $Cli -m whitfield_cli receipts add-item $ReceiptId --upc 194253397168 --good 1 --damaged 0
Write-Output "Completed receipt exit: $LASTEXITCODE"
```

To test a wrong seller, first create a receipt with a real seller other than `SEL01` from `sellers list`, then attempt to add Widget A. The backend should return a conflict/validation error and inventory must remain unchanged.

## Order Read Commands

```powershell
& $Cli -m whitfield_cli orders list --warehouse Reno --json
& $Cli -m whitfield_cli orders list --status READY_TO_SHIP --json
```

Choose an ID from the list if you want to inspect an existing order:

```powershell
$OrderId = "PASTE_ORDER_ID_HERE"
& $Cli -m whitfield_cli orders show $OrderId --json
```

## Controlled Fulfillment Workflow

This workflow ships one Widget A and changes inventory. Use `FULFILLMENT_STAFF`, Owner, or an authorized Manager.

```powershell
& $Cli -m whitfield_cli auth logout
& $Cli -m whitfield_cli auth login --email fulfillment@whitfield.com

$BeforeOrder = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
$Timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$OrderOutput = & $Cli -m whitfield_cli orders create --warehouse Reno --seller SEL01 --sku WIDGET-A --quantity 1 --order-number "CLI-TEST-ORDER-$Timestamp"
$OrderOutput
$OrderId = ([regex]::Match(($OrderOutput -join "`n"), 'Id:\s*([0-9a-f]{24})')).Groups[1].Value
if (-not $OrderId) { throw "CLI did not return an order ID." }

& $Cli -m whitfield_cli orders reserve $OrderId
$AfterReserve = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
Write-Output "Reserve on-hand unchanged: $($AfterReserve.on_hand -eq $BeforeOrder.on_hand)"
Write-Output "Reserve changed reserved by one: $($AfterReserve.reserved -eq ($BeforeOrder.reserved + 1))"

& $Cli -m whitfield_cli orders start-picking $OrderId
& $Cli -m whitfield_cli orders mark-picked $OrderId
& $Cli -m whitfield_cli orders pack $OrderId
& $Cli -m whitfield_cli orders shipment $OrderId --carrier UPS --tracking "CLI-TEST-SHIP-$Timestamp"
& $Cli -m whitfield_cli orders ship $OrderId --yes

$AfterShip = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
Write-Output "Ship on-hand changed by minus one: $($AfterShip.on_hand -eq ($BeforeOrder.on_hand - 1))"
Write-Output "Ship released reservation: $($AfterShip.reserved -eq $BeforeOrder.reserved)"

# Idempotency check: no second inventory decrement is allowed.
& $Cli -m whitfield_cli orders ship $OrderId --yes
$AfterShipRetry = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
Write-Output "Retry unchanged: $($AfterShipRetry.on_hand -eq $AfterShip.on_hand -and $AfterShipRetry.reserved -eq $AfterShip.reserved)"
```

Expected: reservation leaves on-hand unchanged, shipment decreases on-hand once, and `Retry unchanged: True`.

## Oversell And Invalid Transition Tests

```powershell
$CurrentInventory = & $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
$Timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$OversellOutput = & $Cli -m whitfield_cli orders create --warehouse Reno --seller SEL01 --sku WIDGET-A --quantity ($CurrentInventory.available + 1) --order-number "CLI-TEST-OVERSELL-$Timestamp"
$OversellOrderId = ([regex]::Match(($OversellOutput -join "`n"), 'Id:\s*([0-9a-f]{24})')).Groups[1].Value
& $Cli -m whitfield_cli orders reserve $OversellOrderId
Write-Output "Oversell reserve exit: $LASTEXITCODE"

# A NEW oversell order cannot be packed or shipped.
& $Cli -m whitfield_cli orders pack $OversellOrderId
Write-Output "Invalid pack exit: $LASTEXITCODE"
& $Cli -m whitfield_cli orders ship $OversellOrderId --yes
Write-Output "Invalid ship exit: $LASTEXITCODE"
```

Expected: oversell reservation returns conflict exit `6` and inventory does not become negative.

## Audit And Owner User Commands

Log back in as Owner first.

```powershell
& $Cli -m whitfield_cli auth logout
& $Cli -m whitfield_cli auth login --email owner@whitfield.com

& $Cli -m whitfield_cli audit recent --warehouse Reno --json
& $Cli -m whitfield_cli users list --json
```

`users create` asks for a hidden temporary password and creates a real employee account. Use a unique email and only run it when you intend to provision a local test employee:

```powershell
$Timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
& $Cli -m whitfield_cli users create --first-name CLI --last-name Test --email "cli.test.$Timestamp@whitfield.local" --role RECEIVING_STAFF --warehouse Reno
```

## RBAC And Warehouse Scope Tests

```powershell
# Receiving Staff can receive in Reno but cannot fulfill, view Columbus, or manage users.
& $Cli -m whitfield_cli auth logout
& $Cli -m whitfield_cli auth login --email receiving@whitfield.com
& $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json
& $Cli -m whitfield_cli inventory get --upc 194253397168 --warehouse 6a7cbff64102c0b300859ca4
& $Cli -m whitfield_cli orders reserve 000000000000000000000000
& $Cli -m whitfield_cli users list

# Fulfillment Staff can fulfill in Reno but cannot receive or manage users.
& $Cli -m whitfield_cli auth logout
& $Cli -m whitfield_cli auth login --email fulfillment@whitfield.com
& $Cli -m whitfield_cli orders list --warehouse Reno --json
& $Cli -m whitfield_cli receipts complete 000000000000000000000000 --yes
& $Cli -m whitfield_cli users list
```

Expected: backend denial is exit `4`. The Columbus ObjectId is used intentionally so the request reaches FastAPI; the backend remains the authority.

## Confirmation And Backend Failure Tests

```powershell
# Non-interactive confirmation guard: this must not ship an order without --yes.
& $Cli -m whitfield_cli orders ship 000000000000000000000000
Write-Output "No-confirmation exit: $LASTEXITCODE"

# Unavailable backend: friendly message and exit 8.
& $Cli -m whitfield_cli --api-url http://127.0.0.1:9999 health
Write-Output "Unavailable backend exit: $LASTEXITCODE"
```

## Final Logout

```powershell
& $Cli -m whitfield_cli auth logout
& $Cli -m whitfield_cli auth status
```

## Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 2 | Invalid CLI input or confirmation not granted |
| 3 | Missing or expired authentication |
| 4 | Backend authorization denied |
| 5 | Entity not found |
| 6 | Backend business conflict, including oversell |
| 7 | Backend request validation failure |
| 8 | Backend unavailable or timed out |

## Important Safety Notes

- The CLI has no `inventory set`, `inventory overwrite`, raw database, or role-override command.
- The backend enforces roles, warehouse scope, idempotency, inventory math, and audit trails.
- The local session file stores only a token; it does not store a role or warehouse scope that can elevate access.
- Do not run receipt completion or order shipping repeatedly unless you are deliberately testing backend idempotency.
