# Receiving Verification

## Original 404

Failing endpoint: `POST /v1/receipts/{receipt_id}/items`

Request:

```json
{"upc":"999999999999","good_qty":2,"damaged_qty":1}
```

Response:

```text
404 {"detail":"Product with UPC '999999999999' not found"}
```

Root cause: the test UPC was not registered in the product catalog. The frontend request shape was correct.

Bug or expected behavior: expected strict product validation, not a backend integration bug. The frontend now maps this response to an actionable product-not-found message instead of displaying raw Axios text.

## Valid UPC

Product: Widget A (`6a7cc6cdab995f0726c16b22`)

Seller: Acme Corp (`6a7cc6cdab995f0726c16b21`)

UPC: `194253397168`

Result: PASS. A Reno receipt for the matching seller accepted `good_qty=2` and `damaged_qty=1` and returned HTTP 200 with one receipt line totaling 3 units.

## Invalid UPC

Backend result: HTTP 404 with `Product with UPC '<upc>' not found`.

Frontend UX: normalized to `Product not found for this UPC. Check the barcode or ask a manager to add the product first.`

Result: PASS after the frontend error mapping. Unknown products are not created automatically.

## Receipt Completion

Good: 2

Damaged: 1

Inventory before: on-hand 113, damaged 15, available 113.

Inventory after: on-hand 115, damaged 16, available 115.

Result: PASS. Good and damaged quantities remain separate. A completed receipt rejected another item with HTTP 409.

## Dashboard Refresh

Before: dashboard inventory queries are keyed by `inventory` and scoped filters.

After: receipt mutations invalidate `receipt`, `receipts`, `inventory`, and `audit-logs`; dashboard inventory queries therefore refetch through the shared `inventory` query prefix.

Hard reload required: NO by query design. A browser click-through was not executed because no controllable browser session was available in this environment.

## Failure Modes

Unknown UPC: PASS, HTTP 404 with strict validation and friendly frontend mapping.

Wrong seller: PASS, backend rejects the product/receipt seller mismatch with HTTP 400.

Negative qty: PASS, HTTP 422.

Zero qty: PASS, HTTP 422.

Decimal qty: PASS, HTTP 422.

Completed receipt: PASS, HTTP 409.

Unauthorized warehouse: PASS, HTTP 403.

Fulfillment staff create receipt: PASS, HTTP 403.

Receiving staff Reno receipt: PASS.

Duplicate product behavior: the CRUD layer updates the existing UPC line rather than creating a duplicate line.

## Build

`npm run build`: PASS.

## Remaining MVP blockers

- Browser-based dashboard refresh and visual receiving smoke test remain to be run in a controllable browser session.
- No inactive product was present in the live catalog test set; the current receiving controller does not add a separate inactive-product rejection beyond the existing product lookup/seller checks.
