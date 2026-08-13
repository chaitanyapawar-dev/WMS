# Whitfield Fulfillment SOP

## Purpose

Move customer orders through reservation, picking, packing, and shipment while preserving accurate inventory records.

## Applies To

OWNER, MANAGER, and FULFILLMENT_STAFF working in an authorized warehouse.

## Procedure

1. Create an order in NEW status for the correct seller and warehouse.
2. Reserve inventory before picking. Reservation moves the order to RESERVED when stock is available.
3. Start picking, then record items as picked.
4. Pack the order after picking is complete and create shipment details when required.
5. Mark the order READY_TO_SHIP after it is packed and shipment information is valid.
6. Ship the order only after final verification of the order, quantities, and shipment details.

## Important Rules

- The order flow is NEW, RESERVED, PICKING, PICKED, PACKED, READY_TO_SHIP, then SHIPPED.
- Reservation increases reserved quantity and reduces available quantity; it does not reduce on-hand quantity.
- Shipping reduces on-hand quantity and releases the reserved quantity.
- Do not skip order status transitions or ship an order twice.

## Escalation And Restrictions

FULFILLMENT_STAFF may perform fulfillment operations only for assigned warehouses. Escalate stock shortages, seller mismatches, or shipment discrepancies to a MANAGER or OWNER.
