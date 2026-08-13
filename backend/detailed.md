# Whitfield WMS — Phase 4 to Phase 6 Execution Plan

> **Today’s scope:** Implement only Phase 4, Phase 5, and Phase 6.
> Do not start frontend, dashboard UI, AI, RAG, voice, CLI, MCP, deployment, or later-phase work.

## Agent Work Loop

Use these statuses only:

```text
NOT STARTED
IN PROGRESS
BLOCKED
COMPLETED
```

For each task:

```text
Find first task not COMPLETED
→ Check dependencies
→ Mark IN PROGRESS
→ Inspect existing code
→ Implement
→ Run verification
→ If criteria pass, mark COMPLETED
→ Otherwise fix/retest or mark BLOCKED with exact reason
→ Continue to next eligible task
```

Rules:
- Follow `.codex/skills/eigi-backend-standards`.
- Preserve Phase 1–3 working behavior.
- Keep routes thin.
- Put business orchestration in controllers/services.
- Put MongoDB operations in CRUD/database layers.
- Add docstrings/logging to every function/method touched.
- Never expose secrets or internal exception strings.
- Enforce backend RBAC and warehouse scope.
- Do not mark a task complete just because files exist.
- Stop after Phase 6 verification.

---

# 3. TODAY'S EXECUTION BOUNDARY

The agent is authorized to implement:

```
```

```
Phase 4 — Receiving & Inventory
Phase 5 — Inventory Ledger & Audit
Phase 6 — Orders & Fulfillment
```

The agent must stop after Phase 6.

The following are explicitly locked today:

```
```

```
Phase 7 — Dashboard & Frontend Integration   → DEFERRED
Phase 8 — AI Operational Assistant           → DEFERRED
Phase 9 — Voice-Assisted Operations          → DEFERRED
Phase 10 — Final Hardening & Demo            → DEFERRED
```

---

# 4. Phase 4 — Receiving & Inventory

## Phase Goal

Replace the inbound Excel workflow with a safe receiving workflow that:

-  identifies the seller and warehouse, 
-  identifies the physical shipment by tracking/ticket, 
-  supports UPC scanning, 
-  records good and damaged quantity separately, 
-  updates real inventory, 
-  prevents the same shipment from being received twice, 
-  maintains warehouse/seller/product isolation, 
-  is safe under retries. 

**Phase Status: COMPLETED**

---

## P4-T01 — Receipt Domain Model

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create the receipt persistence model representing a physical inbound shipment.

Recommended fields:

```
```

```
id
receipt_number
seller_id
warehouse_id
tracking_number
ticket_number
status
items[]
idempotency_key (optional but recommended)
created_by
created_at
updated_at
completed_by
completed_at
```

Receipt status:

```
```

```
DRAFT
IN_PROGRESS
COMPLETED
CANCELLED
```

Receipt item:

```
```

```
product_id
upc
received_qty
good_qty
damaged_qty
```

### Business Rules

-  A receipt belongs to exactly one seller and one warehouse. 
-  At least one physical shipment identifier must be present: 
  - `tracking_number`, OR 
  - `ticket_number`. 
- `received_qty = good_qty + damaged_qty`. 
-  Quantities cannot be negative. 
-  Completed receipts cannot be edited as normal receiving work. 
-  Receipt numbers must be unique. 

### Eligibility Criteria

-  Phase 3 Seller, Product, Warehouse models exist. 
-  Existing ODMantic/MongoDB model conventions inspected. 

### Acceptance Criteria

-  Receipt status enum implemented. 
-  Receipt item embedded model/schema implemented. 
-  Receipt model implemented. 
-  Timestamps follow existing project convention. 
-  Seller/warehouse/product IDs use the repo's established ID representation. 
-  Validation prevents negative quantities. 
-  Validation enforces `received = good + damaged`. 
-  Eigi docstrings/logging standards followed where functions are added. 

### Expected Files

Examples only; follow existing naming:

```
```

```
core/models/receipt_model.py
core/apis/schemas/requests/receipt_requests.py
core/apis/schemas/responses/receipt_responses.py
```

---

## P4-T02 — Receipt Database Indexes and Duplicate Shipment Identity

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create database-level protections for receipt identity.

A user retry must not cause the same physical shipment to affect stock twice.

### Business Rules

Prefer unique/partial indexes that prevent duplicate completed/active physical receipts within the appropriate scope.

Recommended identity scopes:

```
```

```
seller_id + warehouse_id + tracking_number
```

and/or:

```
```

```
warehouse_id + ticket_number
```

If fields are optional, use partial/sparse indexes appropriately.

### Important Distinction

Two problems must remain conceptually separate:

1. **Physical duplicate protection** 
   -  Same shipment/tracking/ticket cannot be received twice. 
2. **Technical idempotency** 
   -  Retrying the same API request cannot apply inventory twice. 

### Eligibility Criteria

-  P4-T01 completed. 

### Acceptance Criteria

-  Duplicate tracking/ticket conflict is enforced at DB/business layer. 
-  Duplicate conflicts return `409`. 
-  Empty/null optional identifiers do not accidentally collide. 
-  Receipt number uniqueness enforced. 
-  Index initialization follows the existing startup database/index pattern. 

---

## P4-T03 — Inventory Snapshot Model

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create the current inventory snapshot model.

Recommended fields:

```
```

```
id
warehouse_id
seller_id
product_id
on_hand
reserved
damaged
low_stock_threshold
version
created_at
updated_at
```

Derived value:

```
```

```
available = on_hand - reserved
```

Do not store `available` unless there is a strong existing repository reason.

### Core Invariants

```
```

```
on_hand >= 0
reserved >= 0
damaged >= 0
reserved <= on_hand
available >= 0
```

### Unique Inventory Scope

Exactly one inventory snapshot should exist for:

```
```

```
warehouse_id + seller_id + product_id
```

### Eligibility Criteria

-  Phase 3 Product/Seller/Warehouse models available. 

### Acceptance Criteria

-  Inventory model implemented. 
-  Unique compound index implemented. 
-  Quantity defaults are zero. 
-  Derived available quantity is exposed safely in response schema. 
-  Invariants are validated where relevant. 
-  No API exposes a generic unrestricted quantity edit. 

---

## P4-T04 — Inventory CRUD Foundation

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create persistence operations required by receiving.

Required capabilities:

-  Get inventory by warehouse/seller/product. 
-  List/filter inventory. 
-  Create inventory snapshot when product is first received. 
-  Increment good stock. 
-  Increment damaged stock separately. 
-  Support safe conditional/atomic updates where required. 

### Business Rule

Good received quantity increases:

```
```

```
on_hand
```

Damaged received quantity increases:

```
```

```
damaged
```

Damaged quantity must NOT automatically become sellable `on_hand`.

### Eligibility Criteria

-  P4-T03 completed. 

### Acceptance Criteria

-  CRUD contains DB operations; route/controller does not perform raw Mongo updates. 
-  New inventory snapshot can be safely upserted. 
-  Concurrent upsert does not create duplicate scope records. 
-  Good/damaged quantities update the correct fields. 
-  Mongo errors are logged without exposing secrets. 

---

## P4-T05 — Create Receipt Workflow

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Implement receipt creation.

Required API:

```
```

```
POST /v1/receipts
```

Suggested request:

```
```

```
{
  "seller_id": "...",
  "warehouse_id": "...",
  "tracking_number": "...",
  "ticket_number": "..."
}
```

### Authorization

- `OWNER` — allowed. 
- `MANAGER` — allowed within permitted scope. 
- `RECEIVING_STAFF` — allowed within permitted warehouse scope. 
- `FULFILLMENT_STAFF` — not allowed to create receiving work. 

### Business Rules

-  Seller must exist and be active. 
-  Warehouse must exist and be accessible to current user. 
-  Physical shipment identity must not already exist. 
-  Generate unique human-readable receipt number. 
-  Initial status should follow existing workflow (`DRAFT` or `IN_PROGRESS`). 

### Acceptance Criteria

-  Route implemented. 
-  Controller owns validation/orchestration. 
-  CRUD owns persistence. 
-  Warehouse scope enforced server-side. 
-  Duplicate physical receipt returns `409`. 
-  Missing seller/warehouse returns meaningful error. 
-  Response is safe and typed. 

---

## P4-T06 — UPC-Based Receipt Item Entry

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Allow receiving staff to add/update receipt lines by UPC/product.

Required API:

```
```

```
POST /v1/receipts/{receipt_id}/items
```

Suggested request:

```
```

```
{
  "upc": "194253397168",
  "good_qty": 24,
  "damaged_qty": 3
}
```

The backend should resolve the UPC to the Product.

### Business Rules

-  Product must exist. 
-  Product must belong to the receipt's seller. 
-  Receipt must not be `COMPLETED` or `CANCELLED`. 
-  Quantities must be >= 0. 
-  At least one of good/damaged must be > 0 for a meaningful line. 
- `received_qty = good_qty + damaged_qty`. 

### Authorization

Same receiving permissions as P4-T05.

### Acceptance Criteria

-  UPC resolves through existing Product domain. 
-  Wrong-seller UPC is rejected. 
-  Item is added or intentionally updated using a consistent rule. 
-  Completed receipts cannot be changed. 
-  Response shows computed received quantity. 

---

## P4-T07 — Receipt Read APIs

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Implement read operations required by UI/demo.

Required APIs:

```
```

```
GET /v1/receipts
GET /v1/receipts/{receipt_id}
```

Recommended filters:

```
```

```
warehouse_id
seller_id
status
tracking_number
```

### Authorization

-  OWNER — all. 
-  MANAGER — allowed warehouses. 
-  RECEIVING\_STAFF — allowed warehouses. 
-  FULFILLMENT\_STAFF — read-only only if current project policy permits; otherwise deny. 

### Acceptance Criteria

-  List route works. 
-  Detail route works. 
-  Warehouse isolation enforced. 
-  Useful filters supported. 
-  Unknown receipt returns `404`. 

---

## P4-T08 — Complete Receipt and Apply Inventory Exactly Once

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Implement the critical inbound operation.

Required API:

```
```

```
POST /v1/receipts/{receipt_id}/complete
```

### Required Behavior

For every receipt line:

```
```

```
inventory.on_hand += good_qty
inventory.damaged += damaged_qty
```

Then:

```
```

```
receipt.status = COMPLETED
completed_by = current_user
completed_at = now
```

### Critical Guarantees

1.  A completed receipt can affect inventory only once. 
2.  Replaying the complete request must NOT increment stock again. 
3.  Duplicate physical shipment must remain blocked. 
4.  Inventory must remain scoped to seller + warehouse + product. 
5.  A receipt with no valid items cannot be completed. 

### Atomicity Strategy

Use the strongest strategy supported by the current MongoDB environment:

**Preferred:** MongoDB transaction when the deployment supports sessions/transactions.

**If transactions are unavailable:** implement a safe idempotent completion design and document the limitation. Do not silently pretend a multi-document operation is transactional.

At minimum:

-  claim/check receipt state safely, 
-  prevent second completion, 
-  use atomic inventory updates/upserts, 
-  never return success after only partially processing without recording the failure state. 

Do not introduce a fragile read-check-write sequence that allows simple request replay to double stock.

### Eligibility Criteria

-  P4-T01 through P4-T07 completed. 

### Acceptance Criteria

-  First completion updates inventory correctly. 
-  Second completion attempt returns conflict/idempotent safe result without changing inventory. 
-  Good and damaged stock separated. 
-  Completion metadata recorded. 
-  Empty receipt completion rejected. 
-  Unauthorized warehouse/user rejected. 
-  Failure is logged and does not leak internals. 

---

## P4-T09 — Inventory Read APIs

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Expose current stock state for operations.

Required APIs:

```
```

```
GET /v1/inventory
GET /v1/inventory/{inventory_id}
```

Recommended filters:

```
```

```
warehouse_id
seller_id
product_id
upc
```

Response should clearly include:

```
```

```
on_hand
reserved
available
damaged
```

### Authorization

All authenticated WMS roles may read inventory within allowed warehouse scope.

### Acceptance Criteria

-  Inventory list works. 
-  Inventory detail works. 
-  Filters work. 
- `available = on_hand - reserved`. 
-  Warehouse scope enforced. 
-  No direct generic inventory quantity PATCH exists. 

---

## P4-T10 — Phase 4 Integration Verification

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Verify the full inbound story before Phase 5.

### Required Demo Data

Use at least:

```
```

```
Warehouse: Reno
Seller: existing demo seller
Product: existing UPC product
```

### Required Scenario

```
```

```
Create receipt
→ add UPC item
→ 24 good / 3 damaged
→ complete receipt
→ inventory shows +24 on_hand and +3 damaged
→ replay complete request
→ inventory does NOT change again
```

### Acceptance Criteria

-  Scenario passes end-to-end. 
-  Duplicate tracking/ticket is rejected. 
-  Wrong warehouse user gets `403`. 
-  Wrong seller/product relation is rejected. 
-  Existing Phase 3 routes still work. 
-  No password/hash/secret leaks in responses. 

### Phase Completion Rule

Phase 4 becomes `COMPLETED` only when all `MUST HAVE` P4 tasks pass.

---

# 5. Phase 5 — Inventory Ledger & Audit

## Phase Goal

Make every meaningful inventory change explainable and controlled.

The system must answer:

> "Who changed this quantity, why, when, and because of which receipt/order/adjustment?"

**Phase Status: COMPLETED**

---

## P5-T01 — Inventory Movement Model

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create an append-only inventory movement record.

Recommended fields:

```
```

```
id
warehouse_id
seller_id
product_id
inventory_id
movement_type
quantity
previous_on_hand
new_on_hand
previous_reserved
new_reserved
previous_damaged
new_damaged
reference_type
reference_id
reason
performed_by
created_at
```

Initial movement types:

```
```

```
RECEIVED
DAMAGED_RECEIVED
ADJUSTMENT_INCREASE
ADJUSTMENT_DECREASE
```

Phase 6 will extend with:

```
```

```
RESERVED
RESERVATION_RELEASED
SHIPPED
```

### Acceptance Criteria

-  Model implemented. 
-  Movement type enum implemented. 
-  Movement is append-oriented. 
-  Reference can point to receipt/order/adjustment. 
-  Actor and timestamp recorded. 

---

## P5-T02 — Audit Log Model

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create a separate security/business audit trail.

Recommended fields:

```
```

```
id
user_id
user_role
warehouse_id
action
entity_type
entity_id
old_value / old_state
new_value / new_state
reason
ip_address (if safely available)
created_at
```

Important distinction:

```
```

```
InventoryMovement = how stock changed
AuditLog         = who performed sensitive business/system action
```

### Acceptance Criteria

-  Audit model implemented. 
-  Sensitive fields/secrets are not copied into audit payloads. 
-  Audit records are not editable through normal application APIs. 
-  No delete audit endpoint is created. 

---

## P5-T03 — Movement and Audit CRUD

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Implement persistence operations for append-only movement and audit records.

### Acceptance Criteria

-  Create movement operation exists. 
-  List/filter movement operation exists. 
-  Create audit event operation exists. 
-  List/filter audit operation exists. 
-  Normal application routes cannot update/delete history. 
-  CRUD follows Eigi conventions. 

---

## P5-T04 — Wire Receipt Completion Into Movement Ledger

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Every receipt completion inventory mutation must create corresponding movement records.

Example:

```
```

```
Receipt REC-1001
Product A
good = 24
damaged = 3
```

Expected movements:

```
```

```
RECEIVED          +24
DAMAGED_RECEIVED   +3
```

Both should reference:

```
```

```
reference_type = RECEIPT
reference_id = receipt_id
```

### Consistency Requirement

If Mongo transactions are supported, inventory update + movement creation should be in the same transaction.

If not supported, implement the safest available ordering/idempotency approach and document the limitation.

### Acceptance Criteria

-  Receipt stock update creates movement history. 
-  Replay of receipt completion does not duplicate movements. 
-  Movement values correspond to actual resulting inventory. 
-  Actor is the completing user. 

---

## P5-T05 — Wire Sensitive Actions Into Audit Log

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required Initial Audit Events

At minimum:

```
```

```
RECEIPT_CREATED
RECEIPT_ITEM_ADDED_OR_UPDATED
RECEIPT_COMPLETED
INVENTORY_ADJUSTED
```

### Acceptance Criteria

-  Sensitive events generate audit records. 
-  Audit actor matches authenticated user. 
-  Warehouse/entity IDs are stored. 
-  Raw JWT/password/secret data is never stored. 

---

## P5-T06 — Controlled Inventory Adjustment Workflow

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create a controlled correction workflow.

Required API:

```
```

```
POST /v1/inventory/{inventory_id}/adjust
```

Suggested request:

```
```

```
{
  "delta": -2,
  "reason": "Cycle count correction"
}
```

### Critical Rule

Do NOT implement:

```
```

```
PATCH inventory quantity = arbitrary absolute value
```

Use:

```
```

```
delta + required reason
```

### Authorization

Allowed:

```
```

```
OWNER
MANAGER
```

Denied:

```
```

```
RECEIVING_STAFF
FULFILLMENT_STAFF
```

### Business Rules

-  Reason required. 
-  Resulting `on_hand` cannot become negative. 
-  Resulting `on_hand` cannot fall below `reserved`. 
-  Adjustment must create: 
  -  inventory movement, 
  -  audit log. 

### Acceptance Criteria

-  Controlled adjustment endpoint exists. 
-  Staff roles receive `403`. 
-  Negative/invalid result returns conflict/validation error. 
-  Movement created. 
-  Audit created. 
-  No direct unrestricted quantity edit route exists. 

---

## P5-T07 — Inventory Movement Read API

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required API

```
```

```
GET /v1/inventory/{inventory_id}/movements
```

Optional useful filters:

```
```

```
movement_type
date_from
date_to
```

### Authorization

Authenticated users may read movement history only for inventory in their allowed warehouse scope, unless policy restricts staff further.

### Acceptance Criteria

-  History is chronological/predictable. 
-  Receipt reference is visible. 
-  Actor and timestamp visible. 
-  Warehouse scope enforced. 

---

## P5-T08 — Audit Log Read API

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required API

```
```

```
GET /v1/audit-logs
```

Recommended filters:

```
```

```
warehouse_id
user_id
action
entity_type
entity_id
```

### Authorization

Recommended:

```
```

```
OWNER
MANAGER
```

### Acceptance Criteria

-  Owner/manager can query audit history. 
-  Lower roles are rejected if policy restricts access. 
-  Audit records cannot be modified/deleted via API. 
-  Pagination or reasonable result limiting exists. 

---

## P5-T09 — Phase 5 Traceability Verification

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required Scenario

```
```

```
Receive 24 good / 3 damaged
→ inspect current inventory
→ inspect movement history
→ perform manager adjustment -2 with reason
→ inspect movement history again
→ inspect audit history
```

Expected explanation:

```
```

```
Why quantity changed?
Who did it?
When?
Which receipt/adjustment caused it?
What was the reason?
```

### Acceptance Criteria

-  Every tested stock mutation is explainable. 
-  Receipt replay does not duplicate history. 
-  Unauthorized adjustment is `403`. 
-  Invalid adjustment cannot violate inventory invariants. 

### Phase Completion Rule

Phase 5 becomes `COMPLETED` only when every `MUST HAVE` task passes.

---

# 6. Phase 6 — Orders & Fulfillment

## Phase Goal

Replace the outbound Excel workflow with a safe order/fulfillment process that prevents overselling and double shipping.

The most important guarantee is:

> One physical unit can never be promised to two orders at the same time.

**Phase Status: COMPLETED**

---

## P6-T01 — Order Domain Model

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create the Order model.

Recommended fields:

```
```

```
id
order_number
seller_id
warehouse_id
items[]
status
created_by
created_at
updated_at
reserved_at
picked_at
packed_at
shipped_at
cancelled_at
```

Order item:

```
```

```
product_id
sku
quantity
reserved_quantity
picked_quantity
```

Order status:

```
```

```
NEW
RESERVED
PICKING
PICKED
PACKED
READY_TO_SHIP
SHIPPED
CANCELLED
```

### Business Rules

-  Order belongs to one seller and one warehouse. 
-  Order item product must belong to that seller. 
-  Quantity > 0. 
-  Order number unique. 
-  Shipped order cannot be modified as normal open order. 

### Acceptance Criteria

-  Order/status/item models implemented. 
-  Request/response schemas implemented. 
-  Quantity validation implemented. 
-  Unique order number enforced. 

---

## P6-T02 — Order CRUD and Read APIs

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required APIs

```
```

```
POST /v1/orders
GET /v1/orders
GET /v1/orders/{order_id}
```

Recommended filters:

```
```

```
warehouse_id
seller_id
status
order_number
```

### Authorization

Recommended:

-  OWNER — all. 
-  MANAGER — allowed warehouse. 
-  FULFILLMENT\_STAFF — create/read within warehouse if operationally appropriate. 
-  RECEIVING\_STAFF — read-only or denied based on current policy. 

### Acceptance Criteria

-  Order create works. 
-  Product/seller relationship validated. 
-  Warehouse scope enforced. 
-  List/detail work. 
-  Invalid IDs return meaningful errors. 

---

## P6-T03 — Atomic Single-Item Inventory Reservation Primitive

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Implement the critical database operation that reserves stock only when enough is available.

DO NOT implement:

```
```

```
inventory = await get_inventory(...)
if inventory.on_hand - inventory.reserved >= qty:
    inventory.reserved += qty
    await save(inventory)
```

That read-check-write is vulnerable to concurrency.

Use one conditional atomic MongoDB update.

Conceptually:

```
```

```
match inventory scope
AND
(on_hand - reserved) >= requested
THEN
reserved += requested
```

A lower-level PyMongo operation is acceptable and preferred when ODMantic cannot express the atomic condition safely.

### Acceptance Criteria

-  Reservation condition is enforced inside the database update. 
-  Successful reservation increments `reserved`. 
-  Insufficient stock produces no increment. 
-  Failure returns a domain-safe `409`. 
- `reserved <= on_hand` always remains true. 

---

## P6-T04 — Multi-Line Order Reservation Workflow

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required API

```
```

```
POST /v1/orders/{order_id}/reserve
```

### Required Behavior

For each line:

```
```

```
available = on_hand - reserved
available must be >= requested
```

Then reserve.

### Multi-Line Consistency

Preferred:

-  MongoDB transaction when supported. 

If transactions are unavailable:

-  use atomic reservation per item, 
-  track successful reservations, 
-  compensate/release previously reserved lines if a later line fails, 
-  return a clear failure, 
-  do not leave the order marked `RESERVED` after partial failure. 

### Critical Guarantee

No product may be oversold under concurrent reservation requests.

### Acceptance Criteria

-  NEW order can reserve. 
-  Successful order becomes `RESERVED`. 
-  Inventory reserved quantities increase. 
-  Insufficient stock returns `409`. 
-  Failed multi-line reservation does not leave a logically completed partial reservation. 
-  Replaying reservation on already reserved order does not double reserve. 
-  Movement `RESERVED` is created. 
-  Audit event created. 

---

## P6-T05 — Overselling Concurrency Verification

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required Test Scenario

Prepare:

```
```

```
available inventory = 9
```

Create:

```
```

```
Order A requests 9
Order B requests 9
```

Execute reservation as close to concurrently as practical.

Expected:

```
```

```
ONE succeeds
ONE fails with 409
final reserved = 9
available = 0
```

Never:

```
```

```
reserved = 18
```

### Acceptance Criteria

-  Concurrent test executed. 
-  Exactly one reservation succeeds. 
-  Final inventory invariant holds. 
-  Evidence recorded in this task. 

This is a flagship demo scenario.

---

## P6-T06 — Picking Workflow

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required APIs

```
```

```
POST /v1/orders/{order_id}/start-picking
POST /v1/orders/{order_id}/picked
```

### Allowed Transitions

```
```

```
RESERVED → PICKING → PICKED
```

### Authorization

Recommended:

```
```

```
OWNER
MANAGER
FULFILLMENT_STAFF
```

within warehouse scope.

### Acceptance Criteria

-  Invalid status transition rejected. 
-  Warehouse access enforced. 
-  Picking timestamps recorded. 
-  Audit events recorded. 

---

## P6-T07 — Packing Workflow

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required API

```
```

```
POST /v1/orders/{order_id}/packed
```

Allowed transition:

```
```

```
PICKED → PACKED
```

### Acceptance Criteria

-  Only valid prior state can be packed. 
- `packed_at` recorded. 
-  Audit event recorded. 

---

## P6-T08 — Shipment Domain

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Task Description

Create shipment data associated with an order.

Recommended fields:

```
```

```
id
order_id
warehouse_id
carrier
tracking_number
weight
length
width
height
label_reference
status
created_at
updated_at
shipped_at
```

Shipment status may be simple:

```
```

```
READY
SHIPPED
```

### Business Rules

-  One active shipment per order for MVP unless existing design requires otherwise. 
-  Tracking number should not accidentally duplicate another active shipment. 
-  Weight/dimensions must be non-negative. 

### Acceptance Criteria

-  Shipment model implemented. 
-  Shipment schemas implemented. 
-  Shipment persistence implemented. 
-  Order relationship enforced. 

---

## P6-T09 — Prepare Shipment / Ready-to-Ship Workflow

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required API

Either:

```
```

```
POST /v1/orders/{order_id}/shipment
```

or equivalent existing route style.

Input example:

```
```

```
{
  "carrier": "UPS",
  "tracking_number": "1Z123...",
  "weight": 2.4,
  "length": 40,
  "width": 30,
  "height": 18,
  "label_reference": "demo-label"
}
```

Expected order transition:

```
```

```
PACKED → READY_TO_SHIP
```

### Acceptance Criteria

-  Package information validated. 
-  Shipment record created. 
-  Order becomes ready to ship. 
-  Audit event recorded. 
-  No external carrier API required today. 

---

## P6-T10 — Ship Order Exactly Once

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required API

```
```

```
POST /v1/orders/{order_id}/ship
```

### Inventory Effect

For each reserved item:

```
```

```
on_hand -= quantity
reserved -= quantity
```

Result must maintain:

```
```

```
on_hand >= 0
reserved >= 0
reserved <= on_hand
```

### Critical Guarantees

-  Only a properly prepared order can ship. 
-  Same order cannot ship twice. 
-  Shipping reduces both `on_hand` and `reserved`. 
-  Movement `SHIPPED` created. 
-  Audit event created. 
-  Shipment and order shipped timestamps recorded. 

### Atomicity

Use transaction where available.

If not available, implement safe state claiming + atomic line updates + clear failure handling. Do not allow a second request to decrement inventory twice.

### Acceptance Criteria

-  First ship succeeds. 
-  Second ship attempt does not mutate inventory. 
-  Inventory quantities correct. 
-  Order becomes `SHIPPED`. 
-  Shipment becomes `SHIPPED`. 
-  Movements created exactly once. 
-  Audit created. 
-  Unauthorized user/warehouse rejected. 

---

## P6-T11 — Reservation Release / Order Cancellation

**Priority:** SHOULD HAVE
 **Status:** COMPLETED

### Required API

```
```

```
POST /v1/orders/{order_id}/cancel
```

### Business Rules

If an order is reserved but not shipped:

```
```

```
reserved -= reserved_quantity
```

Create:

```
```

```
RESERVATION_RELEASED
```

movement.

Do not cancel an already shipped order using this workflow.

### Acceptance Criteria

-  Cancellation releases reservation. 
-  Available stock increases correctly. 
-  Reserved never becomes negative. 
-  Movement and audit records created. 
-  Shipped order cancellation rejected. 

If deadline pressure is severe, implement after all other Phase 6 `MUST HAVE` tasks.

---

## P6-T12 — Phase 6 End-to-End Fulfillment Verification

**Priority:** MUST HAVE
 **Status:** COMPLETED

### Required Scenario A — Successful Fulfillment

```
```

```
Inventory available
→ create order
→ reserve
→ start picking
→ picked
→ packed
→ create shipment
→ ready to ship
→ ship
→ inventory on_hand decreases
→ inventory reserved decreases
→ movement/audit history explains everything
```

### Required Scenario B — Oversell Protection

```
```

```
available = 9
two orders request 9
→ one succeeds
→ one gets 409
→ final reserved = 9
```

### Required Scenario C — Double Ship Protection

```
```

```
ship order once
→ inventory decreases

ship same order again
→ blocked
→ inventory unchanged
```

### Required Scenario D — Authorization

```
```

```
user from unauthorized warehouse
→ operation rejected with 403
```

### Acceptance Criteria

-  Scenario A passes. 
-  Scenario B passes. 
-  Scenario C passes. 
-  Scenario D passes. 
-  Existing receiving/inventory flows still work. 
-  No direct arbitrary inventory-edit route exists. 
-  Every inventory mutation tested has movement history. 
-  Sensitive actions tested have audit history. 

### Phase Completion Rule

Phase 6 becomes `COMPLETED` only when all `MUST HAVE` tasks pass.

---

# 7. STOP CONDITION FOR TODAY

After Phase 6 verification:

1.  Update the Overall Progress table. 
2.  Record any unresolved blockers. 
3.  Produce a concise completion report. 
4.  STOP. 

Do **not** begin frontend, dashboard UI, Gemini, RAG, voice, CLI, MCP, final deployment, or broad polish today.

Expected stop state:

```
```

```
Phase 4 → COMPLETED
Phase 5 → COMPLETED
Phase 6 → COMPLETED
Phase 7 → DEFERRED
Phase 8 → DEFERRED
Phase 9 → DEFERRED
Phase 10 → DEFERRED
```

---

# Agent Working Memory

## Final Autonomous Execution Summary (Phases 4–6)

### Phase 4 — Receiving & Inventory (`COMPLETED`)
- **Models & Indexes:** Implemented `Receipt` and `Inventory` domain models with unique compound indexes (`seller_id + warehouse_id + tracking_number` & `warehouse_id + ticket_number`) using `partialFilterExpression={"tracking_number": {"$type": "string"}}` to avoid null-value collisions.
- **Workflows:** Implemented `POST /v1/receipts`, `POST /v1/receipts/{receipt_id}/items`, `GET /v1/receipts`, `GET /v1/receipts/{receipt_id}`, `POST /v1/receipts/{receipt_id}/complete`, `GET /v1/inventory`, and `GET /v1/inventory/{inventory_id}`.
- **Idempotency & Resilience:** `complete_receipt` uses atomic state transition (`DRAFT -> COMPLETED`) with standalone MongoDB fallback to ensure completion retries return the completed receipt without double-incrementing stock.

### Phase 5 — Inventory Ledger & Audit (`COMPLETED`)
- **Models & CRUD:** Created append-only `InventoryMovement` model (`collection: inventory_movements`) and security/business `AuditLog` model (`collection: audit_logs`). Implemented `CRUDMovement` and `CRUDAudit`.
- **Integrations:** Receipt completion automatically records `RECEIVED` (+good_qty) and `DAMAGED_RECEIVED` (+damaged_qty) movements, plus `RECEIPT_COMPLETED` audit log events.
- **Controlled Adjustments:** Implemented `POST /v1/inventory/{inventory_id}/adjust` (OWNER/MANAGER only) requiring non-zero delta and operational reason, generating `ADJUSTMENT_INCREASE`/`ADJUSTMENT_DECREASE` movements and `INVENTORY_ADJUSTED` audit logs.
- **Read APIs:** Implemented `GET /v1/inventory/{inventory_id}/movements` and `GET /v1/audit-logs` with role/warehouse scope authorization.

### Phase 6 — Orders & Fulfillment (`COMPLETED`)
- **Models & CRUD:** Created `Order` and `Shipment` domain models, `CRUDOrder`, and `CRUDShipment`. Registered collections in `database.py`.
- **Atomic Reservation Primitive:** Implemented `reserve_inventory_stock` in `CRUDInventory` executing conditional MongoDB `$expr: {"$gte": [{"$subtract": ["$on_hand", "$reserved"]}, quantity]}` to guarantee no overselling under concurrent requests.
- **Fulfillment Lifecycle:** Implemented `POST /v1/orders`, `GET /v1/orders`, `POST /v1/orders/{order_id}/reserve`, `POST /v1/orders/{order_id}/start-picking`, `POST /v1/orders/{order_id}/picked`, `POST /v1/orders/{order_id}/packed`, `POST /v1/orders/{order_id}/shipment`, `POST /v1/orders/{order_id}/ship`, and `POST /v1/orders/{order_id}/cancel`.
- **Concurrency & Cancellation:** Verified under concurrent multi-order reservation tests (`asyncio.gather`) that exactly one order succeeds and the second is rejected with 409 Conflict. Canceling an order releases reserved stock and records `RESERVATION_RELEASED` movements.

All Phase 4, Phase 5, and Phase 6 tasks are fully implemented, verified, and passing! The defined execution boundary for today is complete.