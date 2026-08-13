import type { InventoryRecord, Order, Receipt } from "@/types";

export const OPEN_RECEIPT_STATUSES: Receipt["status"][] = ["DRAFT", "IN_PROGRESS"];
export const CLOSED_ORDER_STATUSES: Order["status"][] = ["SHIPPED", "CANCELLED"];
export const FULFILLMENT_QUEUE_STATUSES: Order["status"][] = [
  "RESERVED",
  "PICKING",
  "PICKED",
  "PACKED",
  "READY_TO_SHIP",
];

function sum(values: number[]) {
  return values.reduce((total, value) => total + value, 0);
}

/** Calculate current inventory totals from API-backed inventory records. */
export function inventoryMetrics(inventory: InventoryRecord[]) {
  return {
    onHand: sum(inventory.map((record) => record.on_hand)),
    available: sum(inventory.map((record) => record.available)),
    reserved: sum(inventory.map((record) => record.reserved)),
    damaged: sum(inventory.map((record) => record.damaged)),
  };
}

/** Calculate current receipt totals from API-backed receipt records. */
export function receiptMetrics(receipts: Receipt[]) {
  const completed = receipts.filter((receipt) => receipt.status === "COMPLETED");
  const completedItems = completed.flatMap((receipt) => receipt.items);

  return {
    pending: receipts.filter((receipt) => OPEN_RECEIPT_STATUSES.includes(receipt.status)).length,
    completed: completed.length,
    unitsReceived: sum(completedItems.map((item) => item.good_quantity + item.damaged_quantity)),
    damagedUnits: sum(completedItems.map((item) => item.damaged_quantity)),
  };
}

/** Calculate current order workflow totals from API-backed order records. */
export function orderMetrics(orders: Order[]) {
  const count = (...statuses: Order["status"][]) =>
    orders.filter((order) => statuses.includes(order.status)).length;

  return {
    open: orders.filter((order) => !CLOSED_ORDER_STATUSES.includes(order.status)).length,
    toPick: count("RESERVED"),
    picking: count("PICKING"),
    readyToPack: count("PICKED"),
    packed: count("PACKED"),
    readyToShip: count("READY_TO_SHIP"),
    shipped: count("SHIPPED"),
  };
}

/** Return records belonging to one warehouse for per-warehouse aggregation. */
export function warehouseRecords<T extends { warehouse_id: string }>(
  records: T[],
  warehouseId: string,
) {
  return records.filter((record) => record.warehouse_id === warehouseId);
}
