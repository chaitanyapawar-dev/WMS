# Whitfield CLI

## Overview

`python -m whitfield_cli` is a small HTTP client for the existing Whitfield WMS FastAPI backend. It does not connect to MongoDB or implement warehouse business rules locally.

For a complete copy-paste PowerShell verification walkthrough, see [CLI_TESTING_GUIDE.md](CLI_TESTING_GUIDE.md).

## Architecture

CLI -> FastAPI -> JWT authentication -> RBAC and warehouse scope -> existing WMS controllers/services -> MongoDB.

## Setup

```powershell
cd D:\WMS\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m whitfield_cli --help
```

## Configuration

`WHITFIELD_API_URL` defaults to `http://127.0.0.1:8000`. Override it with the root `--api-url` option. `WHITFIELD_TOKEN` is supported for automation; otherwise successful `auth login` stores only an access token in `%LOCALAPPDATA%\Whitfield\cli-session.json`.

## Authentication

```powershell
python -m whitfield_cli auth login
python -m whitfield_cli auth whoami
python -m whitfield_cli auth status
python -m whitfield_cli auth logout
```

Passwords are prompted hidden, never printed, and never stored. Normal output never prints a JWT.

## Commands

```text
warehouses list|show
sellers list|show
products list|show|lookup --upc UPC
inventory list|get --warehouse RENO (--upc UPC | --sku SKU | --product VALUE)
inventory movements INVENTORY_ID
receipts list|show|create|add-item|complete
orders list|show|create|reserve|start-picking|mark-picked|pack|shipment|ship
audit recent
users list|create
```

Only existing API routes are exposed. There is no arbitrary database command or inventory overwrite command.

## Role Permissions And Warehouse Scope

The backend, not the CLI, decides identity, role, active status, and warehouse scope. A local token/session or a supplied object ID cannot elevate privileges. Receiving staff remain unable to run fulfillment mutations; fulfillment staff remain unable to receive inventory; non-Owners remain unable to list or create users.

## JSON Mode

Major read commands accept `--json` after the command. JSON mode writes only JSON to stdout, making PowerShell pipelines safe:

```powershell
$result = python -m whitfield_cli inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json
$result.available
```

## Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | Unexpected application error |
| 2 | Invalid CLI input or declined confirmation |
| 3 | Unauthenticated / expired session |
| 4 | Unauthorized |
| 5 | Not found |
| 6 | Business conflict |
| 7 | Validation failure |
| 8 | Backend unavailable or timeout |

## Receiving Example

```powershell
python -m whitfield_cli receipts create --warehouse Reno --seller SEL01 --tracking CLI-TEST-RECEIPT-001
python -m whitfield_cli receipts add-item RECEIPT_ID --upc 194253397168 --good 2 --damaged 1
python -m whitfield_cli receipts complete RECEIPT_ID --yes
```

Completion is confirmed interactively unless `--yes` is supplied. FastAPI remains responsible for duplicate tracking, seller/UPC matching, stock updates, and idempotency.

## Fulfillment Example

```powershell
python -m whitfield_cli orders create --warehouse Reno --seller SEL01 --sku WIDGET-A --quantity 1 --order-number CLI-TEST-ORDER-001
python -m whitfield_cli orders reserve ORDER_ID
python -m whitfield_cli orders start-picking ORDER_ID
python -m whitfield_cli orders mark-picked ORDER_ID
python -m whitfield_cli orders pack ORDER_ID
python -m whitfield_cli orders shipment ORDER_ID --carrier UPS --tracking CLI-TEST-SHIP-001
python -m whitfield_cli orders ship ORDER_ID --yes
```

## Security

The CLI uses HTTPX only. It contains no `pymongo`, `motor`, `odmantic`, or Mongo client imports. It never accepts role or warehouse-scope override flags. It does not initialize Gemini, ChromaDB, or the Phase 9 RAG index.

## Troubleshooting

Run `python -m whitfield_cli health` first. Use `--api-url` for a non-default local server. A `403` is a backend authorization result; do not work around it in local CLI state.
