# Whitfield WMS — Phase 10 Detailed Implementation Plan
## Secure RBAC-Aware CLI / Programmable Operations Interface

**Project:** Whitfield Fulfillment Warehouse Management System  
**Phase:** 10 — CLI / Programmable Operations Interface  
**Scope:** Functional MVP  
**Primary Goal:** Add a secure command-line interface over the existing Whitfield WMS FastAPI backend so humans and automation scripts can perform approved warehouse operations without bypassing JWT authentication, RBAC, warehouse scope, business rules, idempotency, inventory invariants, or auditability.

---

# 1. Phase Order

```text
Phase 1–7   Core WMS                         ✅
Phase 8     AI Operational Assistant         ✅ functional MVP
Phase 9     RAG / SOP Assistant              ✅ MVP COMPLETE & FROZEN
Phase 10    CLI / Programmable Operations    ← THIS PHASE
Phase 11    Voice Prototype
Phase 12    Final Demo Hardening
```

Do not begin Phase 11 automatically.

---

# 2. CLI Architecture

The CLI is **not another backend**. It is another client of the existing WMS.

```text
Human / PowerShell / Automation Script
                ↓
          Whitfield CLI
                ↓
         Authenticated HTTP
                ↓
         Existing FastAPI
                ↓
      JWT Authentication
                ↓
      RBAC + Warehouse Scope
                ↓
    Existing Controllers / Services
                ↓
              MongoDB
                ↓
      Audit + Inventory Movements
```

Forbidden:

```text
CLI → MongoDB directly
CLI → ODMantic directly
CLI → PyMongo directly
CLI reimplements stock math
CLI trusts local role as authority
CLI trusts local warehouse scope
CLI adds arbitrary database shell
CLI adds raw inventory overwrite
```

FastAPI remains the authority.

---

# 3. Non-Negotiable Security Rules

## 3.1 Exactly Four Roles

```text
OWNER
MANAGER
RECEIVING_STAFF
FULFILLMENT_STAFF
```

Do not add ADMIN, SUPERADMIN, RECEIVING_MANAGER, or other public roles.

## 3.2 Backend-Enforced Identity

The CLI may display role/scope from `/auth/me`, but local values are informational only.

A local file saying:

```text
role=OWNER
```

must never grant Owner authority.

## 3.3 Backend-Enforced Warehouse Scope

A Reno Receiving Staff user running:

```text
whitfield inventory list --warehouse Columbus
```

must be denied by the backend.

## 3.4 No Arbitrary Inventory Patch

Do not add:

```text
inventory set
inventory overwrite
inventory patch
```

Inventory changes happen only through existing approved workflows such as:

```text
receipt completion
reservation
shipping
controlled adjustment endpoint if one already exists
```

If a safe adjustment endpoint does not already exist, do not invent one for the CLI.

## 3.5 No Arbitrary Database Commands

Never expose:

```text
db query
mongo
shell
exec
raw-query
run-python
```

## 3.6 Secrets

Never print/store plaintext passwords, JWT signing secrets, Mongo URI, Gemini key, or another user's token.

## 3.7 Auditability

All CLI mutations must call existing backend endpoints so existing audit and movement records remain authoritative.

---

# 4. CLI UX Goal

The CLI should support human use and scripts:

```text
whitfield auth whoami

whitfield products lookup --upc 194253397168

whitfield inventory get --upc 194253397168 --warehouse Reno

whitfield receipts list --status PENDING

whitfield orders list --status READY_TO_SHIP

whitfield orders list --status READY_TO_SHIP --json
```

Machine-readable output and predictable exit codes are required.

---

# 5. MVP Scope

## In Scope

- CLI package and entry point
- API base URL configuration
- login/logout/status/whoami
- warehouse/seller/product discovery
- UPC lookup
- inventory reads
- receipt reads
- order reads
- inventory movement reads where existing API supports them
- audit reads where authorized
- receiving workflow commands mapped to existing APIs
- fulfillment workflow commands mapped to existing APIs
- Owner user management mapped to existing APIs
- JSON output
- human-readable output
- predictable exit codes
- safe confirmations for high-impact mutations
- RBAC and warehouse-scope acceptance tests
- duplicate-receipt/double-ship/oversell regression
- CLI documentation
- final verification report

## Out of Scope

- direct DB access
- generic admin shell
- new business rules
- new warehouse workflow engine
- cron/scheduler platform
- CSV bulk-import platform
- voice
- Deepgram
- Twilio
- MCP
- carrier API expansion
- returns
- robotics/RFID
- production SSO
- multi-agent automation

---

# 6. Recommended Technology

Before adding dependencies, inspect `backend/requirements.txt`.

Prefer a small Python CLI using existing packages. A suitable MVP is:

```text
Typer
HTTPX
Rich (optional)
```

If Click/Requests are already installed and cleaner for the repo, reuse them.

Do not globally upgrade unrelated packages.

---

# 7. Recommended Structure

Adapt to the repository.

```text
backend/
├── whitfield_cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── config.py
│   ├── client.py
│   ├── auth.py
│   ├── output.py
│   ├── errors.py
│   └── commands/
│       ├── auth_commands.py
│       ├── warehouses.py
│       ├── sellers.py
│       ├── products.py
│       ├── inventory.py
│       ├── receipts.py
│       ├── orders.py
│       ├── fulfillment.py
│       ├── audit.py
│       └── users.py
└── tests/
    └── cli/
```

Do not create unnecessary files.

Minimum invocation:

```powershell
cd D:\WMSackend
.\.venv\Scripts\python.exe -m whitfield_cli --help
```

A global `whitfield` console script is optional.

---

# 8. Configuration

Use a configurable backend URL such as:

```text
WHITFIELD_API_URL=http://127.0.0.1:8000
```

Allow a CLI override:

```text
--api-url
```

Do not hard-code production addresses.

Recommended global options:

```text
--api-url
--json
--verbose
--quiet
--no-color
--timeout
```

Do not provide authority overrides such as:

```text
--role OWNER
--force-role
--warehouse-scope
```

---

# 9. Authentication

Inspect the real Phase 2 auth routes before implementing.

Required commands:

```text
whitfield auth login
whitfield auth logout
whitfield auth status
whitfield auth whoami
```

The CLI must use the existing login and `/me` contract.

`whoami` should display backend-returned:

```text
name/email
role
active status
authorized warehouses
```

Never store the password.

Token persistence hierarchy:

```text
1. existing safe OS keyring if already available
2. WHITFIELD_TOKEN environment variable
3. user-local session file containing only the access/session token
```

If a session file is needed, use a user directory such as:

```text
%LOCALAPPDATA%\Whitfield\cli-session.json
```

Never put the token in the repository.

---

# 10. Scriptability

All major read commands must support JSON.

Example:

```powershell
$result = .\.venv\Scripts\python.exe -m whitfield_cli `
  inventory get `
  --upc 194253397168 `
  --warehouse Reno `
  --json | ConvertFrom-Json

$result.available
```

In JSON mode:

```text
stdout = valid JSON only
stderr = warnings/errors
```

Do not mix banners into JSON output.

---

# 11. Exit Codes

Use consistent non-zero exits.

Recommended:

```text
0 success
1 generic application error
2 invalid CLI input
3 unauthenticated / 401
4 unauthorized / 403
5 not found / 404
6 conflict / 409
7 validation / 422
8 backend unavailable / timeout
```

Document the actual final mapping in `CLI.md`.

---

# 12. Friendly Error Handling

Examples:

```text
403
→ Access denied: your account is not authorized for Columbus Warehouse.
```

```text
404 unknown UPC
→ Product not found for UPC 999999999999.
```

```text
409 insufficient inventory
→ Order cannot be reserved: insufficient available inventory.
```

Normal mode must not dump stack traces.

Verbose mode may show safe endpoint/status/request ID, never secrets.

---

# 13. Target RBAC Command Matrix

This is a UX target only. Backend authorization remains authoritative.

| Capability | OWNER | MANAGER | RECEIVING_STAFF | FULFILLMENT_STAFF |
|---|---|---|---|---|
| whoami | yes | yes | yes | yes |
| product lookup | yes | yes | yes | yes |
| inventory read | global/current policy | scoped | scoped | scoped |
| receipt read | yes | scoped | scoped | current policy |
| receipt mutations | yes | current policy | scoped | no |
| order read | yes | scoped | current policy | scoped |
| order/fulfillment mutations | yes | current policy | no | scoped |
| audit | yes | current policy | no | no |
| user administration | yes | no | no | no |
| controlled inventory adjustment | only if existing API | only if existing API | no | no |

Never use this table as the security boundary.

---

# 14. Target Command Tree

During P10-T01 remove commands whose backend API does not exist.

```text
whitfield
├── version
├── health
├── auth
│   ├── login
│   ├── logout
│   ├── status
│   └── whoami
├── warehouses
│   ├── list
│   └── show
├── sellers
│   ├── list
│   └── show
├── products
│   ├── list
│   ├── show
│   └── lookup
├── inventory
│   ├── list
│   └── get
├── movements
│   └── list
├── receipts
│   ├── list
│   ├── show
│   ├── create
│   ├── add-item
│   └── complete
├── orders
│   ├── list
│   ├── show
│   ├── create
│   ├── reserve
│   ├── start-picking
│   ├── mark-picked
│   ├── pack
│   └── ship
├── shipments
│   └── create
├── audit
│   └── recent
└── users
    ├── list
    ├── show
    ├── create
    ├── set-role
    ├── set-warehouses
    └── deactivate
```

Do not invent endpoints merely to make this tree complete.

---

# 15. Read Command Requirements

## Warehouses

```text
warehouses list
warehouses show
```

## Sellers

```text
sellers list
sellers show
```

## Products

```text
products list
products show
products lookup --upc
```

Known demo UPC:

```text
194253397168
```

Use live backend truth.

## Inventory

```text
inventory list
inventory get --product/--sku/--upc --warehouse
```

Display current:

```text
warehouse
seller
product
SKU
UPC
on_hand
reserved
available
damaged
```

## Receipts

```text
receipts list
receipts show
```

Map only supported filters.

## Orders

```text
orders list
orders show
```

Map supported status/warehouse/seller filters.

## Movements

Only if existing API exists:

```text
movements list
```

## Audit

Only if existing API exists:

```text
audit recent
```

---

# 16. Receiving Workflow Commands

Expose only existing receipt APIs.

Potential commands:

```text
receipts create
receipts add-item
receipts complete
```

The agent must inspect actual request schemas.

Do not guess API field names.

Example desired UX:

```powershell
whitfield receipts create `
  --warehouse Reno `
  --seller SEL01 `
  --tracking CLI-TEST-RECEIPT-001
```

Add item:

```powershell
whitfield receipts add-item RECEIPT_ID `
  --upc 194253397168 `
  --good 2 `
  --damaged 1
```

Client validation:

```text
good integer >= 0
damaged integer >= 0
good + damaged > 0
```

Backend must still reject:

```text
unknown UPC
wrong seller
completed receipt
unauthorized warehouse
duplicate tracking
Fulfillment Staff receiving mutation
```

---

# 17. Receipt Completion Safety

`receipts complete` changes inventory.

Interactive default:

```text
Proceed? [y/N]
```

Automation:

```text
--yes
```

If non-interactive and `--yes` is absent, fail safely.

Retrying receipt completion must not apply stock twice.

The backend's idempotency remains authoritative.

---

# 18. Fulfillment Workflow Commands

Expose actual existing endpoints for:

```text
orders create
orders reserve
orders start-picking
orders mark-picked
orders pack
shipments create
orders ship
```

Preserve:

```text
NEW
→ RESERVED
→ PICKING
→ PICKED
→ PACKED
→ READY_TO_SHIP
→ SHIPPED
```

Inventory behavior must remain:

```text
reserve:
on_hand unchanged
reserved increases
available decreases

ship:
on_hand decreases
reserved decreases
```

Do not implement inventory math in the CLI.

---

# 19. Shipping Safety

Shipping is high-impact.

Use confirmation or:

```text
--yes
```

Double ship must not cause a second stock decrement.

Invalid transitions must return friendly conflicts.

---

# 20. Owner User Administration

Expose only if actual backend routes exist.

Potential:

```text
users list
users show
users create
users set-role
users set-warehouses
users deactivate
```

Public signup remains disabled.

Non-Owner attempts must be rejected by backend.

Password input, if required:

```text
hidden prompt
never persisted
never logged
```

---

# 21. Controlled Inventory Adjustment

Only expose if a secure existing endpoint already exists.

If exposed, require:

```text
OWNER/MANAGER according to actual policy
delta
mandatory reason
backend audit
before/delta/after
warehouse scope
```

If no such endpoint exists:

```text
DO NOT IMPLEMENT inventory adjust
```

---

# 22. Confirmation Policy

Require confirmation for high-impact actions such as:

```text
complete receipt
ship order
deactivate user
role change
warehouse scope expansion
inventory adjustment
```

Optional `--dry-run` is useful if easy, but must not block MVP.

---

# 23. Retry Policy

Safe GET requests may retry transient failures conservatively.

Do not blindly retry mutation commands.

Never automatically retry:

```text
receipt create
receipt add-item
order create
shipment create
user create
```

unless the backend operation is explicitly idempotent and verified.

---

# 24. Performance / Independence

Normal CLI commands must not initialize:

```text
Gemini
SentenceTransformers
ChromaDB
RAG index
```

The CLI should work even when AI quota is exhausted.

Explicitly verify:

```text
Gemini unavailable
→ inventory/receipts/orders CLI still works
```

---

# 25. Task Status System

Use:

```text
NOT STARTED
IN PROGRESS
BLOCKED
COMPLETED
```

Completion requires:

```text
implementation
+
success criteria
+
verification evidence
```

---

# 26. Phase 10 Task Summary

| ID | Task | Status |
|---|---|---|
| P10-T01 | CLI discovery, OpenAPI audit, architecture decision | COMPLETED |
| P10-T02 | CLI foundation, config, HTTP client, output, errors | COMPLETED |
| P10-T03 | Authentication/session commands | COMPLETED |
| P10-T04 | Warehouse, seller, product discovery commands | COMPLETED |
| P10-T05 | Inventory and movement read commands | COMPLETED |
| P10-T06 | Receipt read + receiving workflow commands | COMPLETED |
| P10-T07 | Order / fulfillment read + workflow commands | COMPLETED |
| P10-T08 | Audit and Owner user-management commands | COMPLETED |
| P10-T09 | JSON output, exit codes, confirmations, scripting UX | COMPLETED |
| P10-T10 | RBAC + warehouse-scope acceptance matrix | COMPLETED |
| P10-T11 | Idempotency, oversell, double-ship, failure tests | COMPLETED |
| P10-T12 | CLI documentation and demo scripts | COMPLETED |
| P10-T13 | Full CLI acceptance + WMS regression | COMPLETED |
| P10-T14 | Final report and Phase 10 freeze | COMPLETED |

---

# 27. P10-T01 — Discovery and OpenAPI Audit

**Status:** COMPLETED  
**Depends On:** None

Before writing CLI code, inspect:

```text
OpenAPI
auth routes
warehouse routes
seller routes
product routes
inventory routes
receipt routes
order routes
shipment routes
movement routes
audit routes
user routes
requirements.txt
RBAC guards
warehouse guards
error response format
```

Record:

```text
Backend prefix:
Login endpoint:
Whoami endpoint:
JWT transport:
Warehouse endpoints:
Seller endpoints:
Product endpoints:
Inventory endpoints:
Receipt endpoints:
Order endpoints:
Shipment endpoints:
Movement endpoints:
Audit endpoints:
User endpoints:
Controlled adjustment endpoint:
```

If absent:

```text
NOT AVAILABLE
```

Do not invent it.

Success:

```text
actual APIs mapped
unsupported commands removed
CLI → HTTP → FastAPI confirmed
security design recorded
```

---

# 28. P10-T02 — CLI Foundation

**Status:** COMPLETED  
**Depends On:** P10-T01

Implement:

```text
root CLI app
config
HTTP client
output formatter
error mapper
```

Base commands:

```text
--help
version
health
```

Verify:

```text
python -m whitfield_cli --help
python -m whitfield_cli version
python -m whitfield_cli health
backend unavailable case
```

---

# 29. P10-T03 — Authentication

**Status:** COMPLETED  
**Depends On:** P10-T02

Implement:

```text
auth login
auth logout
auth status
auth whoami
```

Test all four roles.

Verify:

```text
backend identity shown correctly
backend role shown correctly
backend warehouse scope shown correctly
invalid/expired session handled
no password storage
token not printed
```

---

# 30. P10-T04 — Warehouses, Sellers, Products

**Status:** COMPLETED  
**Depends On:** P10-T03

Implement according to actual APIs:

```text
warehouses list/show
sellers list/show
products list/show/lookup
```

Mandatory demo:

```text
products lookup --upc 194253397168
```

Test valid/invalid UPC and scope-sensitive warehouse discovery.

---

# 31. P10-T05 — Inventory + Movements

**Status:** COMPLETED  
**Depends On:** P10-T04

Implement:

```text
inventory list
inventory get
movements list   # only if route exists
```

Compare CLI result with direct API truth.

For Widget A / Reno fetch current values:

```text
on_hand
reserved
available
damaged
```

Verify:

```text
available = on_hand - reserved
```

RBAC:

```text
Receiving Reno     PASS
Receiving Columbus DENIED
Fulfillment scoped PASS
```

---

# 32. P10-T06 — Receiving CLI

**Status:** COMPLETED  
**Depends On:** P10-T05

Implement actual supported commands:

```text
receipts list
receipts show
receipts create
receipts add-item
receipts complete
```

Test:

```text
valid receipt
unknown UPC
wrong seller
negative qty
decimal qty
zero total qty
completed receipt
unauthorized warehouse
Fulfillment Staff mutation attempt
duplicate tracking
```

For completion verify inventory before/after.

Retry completion and prove no duplicate stock.

---

# 33. P10-T07 — Fulfillment CLI

**Status:** COMPLETED  
**Depends On:** P10-T05

Implement actual supported commands:

```text
orders list
orders show
orders create
orders reserve
orders start-picking
orders mark-picked
orders pack
shipments create
orders ship
```

Run one safe lifecycle:

```text
create
reserve
start picking
picked
pack
shipment
ship
```

Verify backend state and inventory effects.

Test invalid transition and oversell.

Retry ship and prove no double decrement.

---

# 34. P10-T08 — Audit + Users

**Status:** COMPLETED  
**Depends On:** P10-T03

Implement where actual APIs exist:

```text
audit recent

users list
users show
users create
users set-role
users set-warehouses
users deactivate
```

Authorization tests:

```text
OWNER user administration PASS
MANAGER according to actual policy
RECEIVING denied
FULFILLMENT denied
```

Never add public signup.

---

# 35. P10-T09 — Automation Ergonomics

**Status:** COMPLETED  
**Depends On:** P10-T04..P10-T08 as applicable

Complete:

```text
--json
exit codes
confirmation
--yes
safe non-interactive behavior
friendly errors
```

Verify JSON with PowerShell `ConvertFrom-Json`.

Verify non-zero exit for:

```text
401
403
404
409
422
backend unavailable
```

---

# 36. P10-T10 — RBAC + Scope Matrix

**Status:** COMPLETED  
**Depends On:** P10-T06, P10-T07, P10-T08

## OWNER

Verify appropriate global/current-policy reads and writes.

## MANAGER

Verify assigned warehouse operations and unauthorized warehouse denial.

## RECEIVING_STAFF

Required:

```text
Reno inventory                PASS
Reno receipts                 PASS
create/add/complete receipt   PASS
Columbus inventory            DENIED
Columbus receipts             DENIED
fulfillment mutation          DENIED
user administration          DENIED
privileged audit              DENIED if current policy
```

## FULFILLMENT_STAFF

Required:

```text
Reno inventory                  PASS
Reno orders                     PASS
approved fulfillment mutations  PASS
Columbus order                  DENIED
receiving mutation              DENIED
user administration            DENIED
privileged audit                DENIED if current policy
```

## Local Role Spoof Test

Use a real Receiving Staff token.

Modify local cached metadata to:

```text
role=OWNER
warehouse=Columbus
```

Attempt Owner/Columbus actions.

Expected:

```text
DENIED
```

This proves local CLI state is not authority.

---

# 37. P10-T11 — Idempotency / Failure Tests

**Status:** COMPLETED  
**Depends On:** P10-T06, P10-T07

Required:

## Duplicate Receipt Completion

```text
complete eligible receipt
record inventory
retry completion
no second increment
```

## Double Ship

```text
ship eligible order
record inventory
retry ship
no second decrement
```

## Oversell

```text
reserve quantity > available
409/friendly denial
no negative stock
```

## Invalid Transition

Examples:

```text
pack NEW order
ship NEW order
complete completed receipt
```

## Backend Down

Use invalid API URL or controlled server stop.

Expected:

```text
bounded timeout
friendly error
non-zero exit
```

---

# 38. P10-T12 — Documentation + Demo

**Status:** NOT STARTED  
**Depends On:** P10-T09

Create:

```text
backend/CLI.md
```

Required sections:

```text
Overview
Architecture
Installation
Configuration
Authentication
Role behavior
Command reference
JSON mode
Exit codes
Receiving workflow
Fulfillment workflow
Security
Troubleshooting
```

Optionally create:

```text
scripts/demo_cli.ps1
```

No credentials in scripts.

Safe demo sequence:

```text
auth whoami
products lookup --upc 194253397168
inventory get --upc 194253397168 --warehouse Reno
receipts list --status PENDING
orders list --status READY_TO_SHIP --json
```

---

# 39. P10-T13 — Final CLI Acceptance + Regression

**Status:** COMPLETED  
**Depends On:** P10-T10, P10-T11, P10-T12

Verify:

```text
CLI startup
help
health
auth
read commands
approved receiving commands
approved fulfillment commands
JSON
exit codes
confirmations
RBAC
warehouse scope
idempotency
oversell protection
backend audit
```

Core regression smoke test:

```text
Auth
Dashboard
Inventory
Products
Receiving UI
Orders UI
Fulfillment UI
Audit UI
Users UI
Phase 8 AI
Phase 9 RAG
```

CLI must not break existing interfaces.

---

# 40. P10-T14 — Final Report and Freeze

**Status:** COMPLETED  
**Depends On:** P10-T13

Create:

```text
frontend/phase10_cli_verification.md
```

Required sections:

```text
Overall Status
CLI Architecture
Authentication
Implemented Command Tree
RBAC Matrix
Warehouse Scope Matrix
Product / Inventory Verification
Receiving Workflow
Fulfillment Workflow
JSON / Scripting
Exit Codes
Confirmation Safety
Duplicate Receipt Protection
Oversell Protection
Double Ship Protection
Failure Handling
No Direct DB Verification
Core WMS Regression
Phase 8 AI Regression
Phase 9 RAG Regression
Files Changed
Known Limitations
Remaining Blockers
```

When all acceptance criteria pass:

```text
Phase 10 — CLI / Programmable Operations Interface ✅ MVP COMPLETE & FROZEN
```

Then STOP.

---

# 41. Mandatory Security Acceptance Tests

## Test A — Warehouse Escape

```text
User: RECEIVING_STAFF / Reno
Command: inventory list --warehouse Columbus
Expected: DENIED
```

## Test B — Receiving User Tries Fulfillment Mutation

```text
orders reserve <order>
Expected: DENIED
```

## Test C — Fulfillment User Tries Receiving Mutation

```text
receipts complete <receipt>
Expected: DENIED
```

## Test D — Non-Owner User Administration

```text
users create ...
Expected: DENIED
```

## Test E — Local Role Spoof

Edit local metadata to OWNER while keeping Receiving Staff JWT.

Expected:

```text
Owner-only operation DENIED
```

## Test F — No Direct Database

Search CLI package.

Required:

```text
PyMongo direct CLI usage   NONE
Motor direct CLI usage     NONE
ODMantic direct CLI usage  NONE
```

All WMS data comes through HTTP FastAPI calls.

---

# 42. Mandatory Operational Acceptance Tests

## Receiving

```text
create receipt
add registered UPC
complete
inventory updates once
movement/audit exists
retry complete
no duplicate update
```

## Outbound

```text
create
reserve
pick
pack
create shipment
ship
inventory transitions correctly
movement/audit exists
retry ship
no duplicate decrement
```

## Oversell

```text
reserve impossible quantity
→ denied
```

---

# 43. Test Data

Use recognizable safe test references:

```text
CLI-TEST-RECEIPT-...
CLI-TEST-ORDER-...
CLI-TEST-SHIP-...
```

Do not directly delete MongoDB records for cleanup.

Use existing APIs if cleanup is supported, otherwise document created test data.

---

# 44. Source of Truth

Never use old inventory numbers as expected truth.

Always:

```text
fetch current API
→ run CLI
→ compare
```

This is mandatory for inventory/order/receipt verification.

---

# 45. AI / RAG Independence

CLI deterministic commands must not depend on:

```text
Gemini quota
Gemini API availability
RAG vector store availability
```

Verify normal CLI operations still work if the AI provider is unavailable.

Optional `ai ask` support can be added only after core CLI is complete and must not block Phase 10.

---

# 46. Phase 10 Exit Criteria

Required:

```text
CLI package                               PASS
help/version/health                       PASS
authentication                            PASS
whoami                                    PASS
product lookup                            PASS
inventory lookup                          PASS
receipt reads                             PASS
order reads                               PASS
receiving commands                        PASS where APIs exist
fulfillment commands                      PASS where APIs exist
audit command                             PASS where API exists
Owner user commands                       PASS where APIs exist
JSON output                               PASS
exit codes                                PASS
confirmation safety                       PASS
backend authority                         PASS
warehouse scope                           PASS
local role spoof denied                   PASS
no direct database access                 PASS
duplicate receipt protection preserved   PASS
oversell protection preserved             PASS
double ship protection preserved         PASS
backend unavailable handling              PASS
core WMS regression                       PASS
Phase 8 AI regression                     PASS
Phase 9 RAG regression                    PASS
CLI.md                                    CREATED
phase10_cli_verification.md               CREATED
```

---

# 47. Final Demo

A concise Phase 10 demo:

### 1. Identity

```text
whitfield auth whoami
```

### 2. UPC lookup

```text
whitfield products lookup --upc 194253397168
```

### 3. Current inventory

```text
whitfield inventory get --upc 194253397168 --warehouse Reno
```

### 4. RBAC denial

As Reno Receiving Staff:

```text
whitfield inventory list --warehouse Columbus
```

Expected:

```text
Access denied
```

### 5. Scriptability

```text
whitfield orders list --status READY_TO_SHIP --json
```

### 6. One operational transition

Perform one safe receiving or fulfillment action through the CLI and show the same state reflected in the web WMS.

This proves CLI and web use the same trusted backend.

---

# 48. Agent Working Memory

## Current Position

```text
Current Task: Phase 10 Freeze
Current Status: Phase 10 — CLI / Programmable Operations Interface ✅ MVP COMPLETE & FROZEN
Next Eligible Task: None. Phase 11 requires explicit authorization.
```

## Architecture Decisions

```text
- CLI → FastAPI HTTP only.
- No direct MongoDB access.
- Backend JWT/RBAC/warehouse scope is authoritative.
- Exactly four user roles.
- Existing business rules are reused.
- No arbitrary inventory patch.
- No arbitrary DB command.
- JSON + exit codes make the CLI scriptable.
- High-impact operations require confirmation.
- AI/RAG outages must not affect deterministic CLI commands.
- Voice moves to Phase 11.
```

## Implemented Files

```text
`whitfield_cli/__init__.py`, `__main__.py`, `app.py`, `client.py`, `session.py`,
`output.py`, and `CLI.md`.
```

## Verification Evidence

```text
1. OpenAPI audit: all CLI routes map to existing `/v1` FastAPI endpoints. No direct database path exists.
2. CLI foundation: `.venv\\Scripts\\python.exe -m whitfield_cli --help`, `version`, and `health` PASS.
3. Owner reads: `auth whoami`, UPC lookup, warehouses, sellers, and Widget A/Reno inventory JSON PASS.
4. Inventory invariant: live Widget A/Reno reports on_hand 114, reserved 3, available 111, damaged 17; invariant PASS.
5. Error UX: unknown UPC exits 5; unavailable API exits 8; no raw traceback.
6. Backend RBAC through CLI: Fulfillment receipt completion and non-Owner user list return exit 4; Columbus inventory returns backend 403/exit 4.
7. Static safety scan: no CLI imports or calls for pymongo, motor, odmantic, MongoClient, arbitrary database commands, or inventory overwrite commands.
8. PowerShell JSON pipeline: `inventory get --upc 194253397168 --warehouse Reno --json | ConvertFrom-Json` PASS with available 111.
9. Receiving CLI flow: `CLI-TEST-RECEIPT-1786639714` moved Widget A/Reno from on_hand/damaged 114/17 to 116/18; duplicate completion left 116/18 unchanged.
10. Fulfillment CLI flow: `CLI-TEST-ORDER-1786639751` moved Widget A/Reno from 116/3/113 before reservation to 116/4/112 after reservation and 115/3/112 after shipment; duplicate shipping left values unchanged.
11. Oversell: fresh CLI test order reservation exited 6 (409 conflict), with Widget A/Reno inventory unchanged. Non-interactive ship without `--yes` did not execute.
```

## Known Blockers

```text
None. Interactive hidden-password behavior remains a manual real-TTY acceptance note only; implementation and all other Phase 10 criteria are verified.
```

## Next Action

```text
Phase 10 is complete and frozen. STOP. Do not begin Phase 11.
```

---

# 49. Autonomous Agent Prompt Template

```text
You are implementing Whitfield WMS Phase 10 —
Secure RBAC-Aware CLI / Programmable Operations Interface.

Project root:
D:\WMS

Authoritative plan:
D:\WMSackend\implementationphase10.md

Before modifying code:
1. Read implementationphase10.md completely.
2. Inspect current FastAPI OpenAPI and relevant routes.
3. Inspect JWT auth, RBAC guards, warehouse-scope guards.
4. Inspect backend requirements.
5. Mark P10-T01 IN PROGRESS.

Rules:
- CLI communicates with FastAPI over HTTP.
- Never connect the CLI directly to MongoDB.
- Never create a second backend.
- Never trust local role/warehouse metadata as authority.
- Exactly four roles:
  OWNER, MANAGER, RECEIVING_STAFF, FULFILLMENT_STAFF.
- Map commands only to actual existing APIs.
- Do not invent endpoints just to complete the command tree.
- Do not create arbitrary inventory overwrite commands.
- Do not create arbitrary DB/query commands.
- Preserve backend audit/idempotency/business rules.
- High-impact commands require confirmation or --yes.
- JSON output must be machine-readable.
- Errors must return useful non-zero exit codes.
- Do not expose secrets.
- Do not implement Voice/Deepgram/Twilio.
- Do not modify Phase 8/9 except regression-only fixes.
- Update implementationphase10.md after every task.
- Verify before marking COMPLETED.
- Continue autonomously through eligible tasks.
- Stop after P10-T14 or a genuine blocker.

Main success condition:

Whitfield has a secure, scriptable CLI over the existing FastAPI WMS,
with backend-enforced authentication, RBAC, warehouse isolation,
business rules, inventory invariants, idempotency, and auditability.

Begin with P10-T01.
```

---

# 50. Stop Boundary

After:

```text
Phase 10 — CLI / Programmable Operations Interface ✅ MVP COMPLETE & FROZEN
```

STOP.

Do not begin:

```text
Phase 11 — Voice Prototype
```

until explicitly instructed.
