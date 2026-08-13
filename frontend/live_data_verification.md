# Whitfield WMS Live Data Verification

## Role Model

```text
OWNER: PASS
MANAGER: PASS
RECEIVING_STAFF: PASS
FULFILLMENT_STAFF: PASS
Unexpected roles found: NO
```

The backend enum and frontend `Role` type contain exactly these four values.

## Demo Accounts

```text
owner@whitfield.com: OWNER, login 200, /auth/me 200
manager@whitfield.com: MANAGER, login 200, /auth/me 200
receiving@whitfield.com: RECEIVING_STAFF, login 200, /auth/me 200
fulfillment@whitfield.com: FULFILLMENT_STAFF, login 200, /auth/me 200
```

Owner has unrestricted warehouse access. Manager, Receiving Staff, and Fulfillment Staff are scoped to the persisted Reno warehouse ID.

## Live Dataset

```text
Warehouses: 2
Users: 12
Sellers: 9
Products: 9
Inventory records: 8
Receipts: 14
Orders: 8
Audit logs: 67
```

These are the final counts returned by authenticated live API requests on 2026-08-13.

## Owner Dashboard Verification

| Metric | API Expected | Dashboard Calculation | Result |
|---|---:|---:|---|
| Total On Hand | 180 | 180 | PASS |
| Available | 171 | 171 | PASS |
| Reserved | 9 | 9 | PASS |
| Damaged | 22 | 22 | PASS |
| Pending Receipts | 3 | 3 | PASS |
| Open Orders | 3 | 3 | PASS |
| Ready to Ship | 0 | 0 | PASS |
| Shipped Orders | 4 | 4 | PASS |

Expected values were independently calculated from the JSON returned by `/v1/inventory`, `/v1/receipts`, and `/v1/orders`. The dashboard uses the same explicit status sets and arithmetic in `dashboard-metrics.ts`.

## Reno Dashboard Verification

| Metric | API Expected | Dashboard Calculation | Result |
|---|---:|---:|---|
| Total On Hand | 130 | 130 | PASS |
| Available | 130 | 130 | PASS |
| Reserved | 0 | 0 | PASS |
| Damaged | 18 | 18 | PASS |
| Pending Receipts | 3 | 3 | PASS |
| Open Orders | 1 | 1 | PASS |
| Ready to Ship | 0 | 0 | PASS |
| Shipped Orders | 2 | 2 | PASS |

## Columbus Dashboard Verification

| Metric | API Expected | Dashboard Calculation | Result |
|---|---:|---:|---|
| Total On Hand | 26 | 26 | PASS |
| Available | 17 | 17 | PASS |
| Reserved | 9 | 9 | PASS |
| Damaged | 1 | 1 | PASS |
| Pending Receipts | 0 | 0 | PASS |
| Open Orders | 2 | 2 | PASS |
| Ready to Ship | 0 | 0 | PASS |
| Shipped Orders | 2 | 2 | PASS |

One inventory record containing 24 on-hand and 3 damaged units references a warehouse ID absent from `/v1/warehouses`. Owner all-warehouse totals retain this real record, and the dashboard displays a data-integrity note rather than assigning it to Reno or Columbus.

## Receiving Dashboard Verification

Reno-scoped Receiving Staff values:

| Metric | API Expected | Dashboard Calculation | Result |
|---|---:|---:|---|
| Active Receipts | 3 | 3 | PASS |
| Completed Receipts | 6 | 6 | PASS |
| Units Received | 162 | 162 | PASS |
| Damaged Units | 18 | 18 | PASS |

Units Received is the sum of good and damaged quantities on completed receipts only.

## Fulfillment Dashboard Verification

Reno-scoped Fulfillment Staff values:

| Metric | API Expected | Dashboard Calculation | Result |
|---|---:|---:|---|
| Orders to Pick | 0 | 0 | PASS |
| Picking | 0 | 0 | PASS |
| Ready to Pack | 0 | 0 | PASS |
| Ready to Ship | 0 | 0 | PASS |

## Fake Data Audit

```text
Hardcoded operational KPI values found: NO
Hardcoded operational records found: NO
Demo API fallback reachable in live mode: NO
Fake trend percentages remaining: NO
Fake sparklines remaining: NO
Fake recent activity remaining: NO
```

`src/lib/api/demo-backend.ts` was removed. Every operational API module now calls FastAPI directly and propagates failures.

## Data Refresh Verification

```text
Receipt completion updates dashboard: NOT TESTED
Reservation updates dashboard: NOT TESTED
Shipping updates dashboard: NOT TESTED
Inventory adjustment updates dashboard: NOT TESTED
Audit activity updates: NOT TESTED
```

The relevant TanStack Query prefixes (`receipts`, `inventory`, `orders`, and `audit-logs`) are invalidated after each mutation, and backend state changes were verified. Browser-level no-hard-reload behavior was not executed because no browser connector was available in this session.

## Role UI Verification

```text
OWNER: Static navigation and build PASS; browser click-through not tested
MANAGER: Static navigation and build PASS; browser click-through not tested
RECEIVING_STAFF: Static navigation and build PASS; browser click-through not tested
FULFILLMENT_STAFF: Static navigation and build PASS; browser click-through not tested
```

Backend authorization results:

```text
OWNER POST /v1/users: 201
MANAGER POST /v1/users: 403
RECEIVING_STAFF POST /v1/receipts in Reno: 201
FULFILLMENT_STAFF POST /v1/receipts: 403
RECEIVING_STAFF POST /v1/orders: 403
FULFILLMENT_STAFF outbound workflow probe: 404 for missing order, proving role authorization passed
RECEIVING_STAFF GET Columbus inventory: 403
```

## Build

```text
npm run build: PASS
Focused ESLint for dashboard metrics, dashboard page, and login form: PASS
Full npm run lint: FAIL due repository-wide CRLF/Prettier line-ending errors, including untouched files
```

## Remaining MVP Blockers

```text
Browser-only visual and no-hard-reload mutation verification remains outstanding because the browser connector was unavailable.
MongoDB contains one inventory record with a missing warehouse master reference; the UI reports it truthfully, but the underlying data should be reconciled before production delivery.
```
