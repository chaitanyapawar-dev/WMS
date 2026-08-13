import type {
  AuditLog,
  EntityStatus,
  InventoryRecord,
  Movement,
  MovementType,
  Order,
  Product,
  Receipt,
  ReceiptItem,
  Role,
  Seller,
  Shipment,
  User,
  Warehouse,
} from "@/types";

export interface BackendUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  mobile_number?: string | null;
  role: string;
  status: string;
  warehouse_ids?: string[];
}

export interface BackendWarehouse {
  id: string;
  name: string;
  code: string;
  city: string;
  state: string;
  status: string;
}

export interface BackendSeller {
  id: string;
  name: string;
  seller_code: string;
  email: string;
  phone?: string | null;
  status: string;
  created_at: string;
}

export interface BackendProduct {
  id: string;
  seller_id: string;
  name: string;
  sku: string;
  upc: string;
  description?: string | null;
  status: string;
  created_at: string;
}

export interface BackendReceiptItem {
  product_id: string;
  upc: string;
  received_qty: number;
  good_qty: number;
  damaged_qty: number;
}

export interface BackendReceipt {
  id: string;
  receipt_number: string;
  seller_id: string;
  warehouse_id: string;
  tracking_number?: string | null;
  ticket_number?: string | null;
  status: string;
  items?: BackendReceiptItem[];
  created_by: string;
  created_at: string;
}

export interface BackendInventory {
  id: string;
  product_id: string;
  seller_id: string;
  warehouse_id: string;
  on_hand: number;
  reserved: number;
  available?: number;
  damaged: number;
  low_stock_threshold?: number;
}

export interface BackendMovement {
  id: string;
  inventory_id: string;
  movement_type: string;
  quantity: number;
  previous_on_hand: number;
  new_on_hand: number;
  previous_reserved: number;
  new_reserved: number;
  previous_damaged: number;
  new_damaged: number;
  reference_type: string;
  reference_id: string;
  performed_by: string;
  reason?: string | null;
  created_at: string;
}

export interface BackendOrderItem {
  product_id: string;
  sku: string;
  quantity: number;
  reserved_quantity: number;
  picked_quantity: number;
}

export interface BackendOrder {
  id: string;
  order_number: string;
  seller_id: string;
  warehouse_id: string;
  items?: BackendOrderItem[];
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  reserved_at?: string | null;
  picked_at?: string | null;
  packed_at?: string | null;
  shipped_at?: string | null;
  cancelled_at?: string | null;
}

export interface BackendShipment {
  id: string;
  order_id: string;
  carrier: string;
  tracking_number: string;
  weight: number;
  length: number;
  width: number;
  height: number;
  label_reference?: string | null;
}

export interface BackendAuditLog {
  id: string;
  user_id: string;
  user_role: string;
  warehouse_id?: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  old_state?: Record<string, unknown> | null;
  new_state?: Record<string, unknown> | null;
  reason?: string | null;
  created_at: string;
}

function toStatus(status: string): EntityStatus {
  return status === "ACTIVE" ? "ACTIVE" : "INACTIVE";
}

function lookupName(id: string, values: Map<string, string>, fallback: string) {
  return values.get(id) ?? fallback;
}

export function cleanParams<T extends Record<string, unknown>>(filters: T): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== "" && value !== "ALL"),
  );
}

export function toUser(raw: BackendUser): User {
  return {
    id: raw.id,
    first_name: raw.first_name,
    last_name: raw.last_name,
    email: raw.email,
    role: raw.role as Role,
    status: toStatus(raw.status),
    warehouse_ids: raw.warehouse_ids ?? [],
  };
}

export function toWarehouse(raw: BackendWarehouse): Warehouse {
  return {
    id: raw.id,
    name: raw.name,
    code: raw.code,
    city: raw.city,
    state: raw.state,
    status: toStatus(raw.status),
  };
}

export function toSeller(raw: BackendSeller): Seller {
  return {
    id: raw.id,
    name: raw.name,
    code: raw.seller_code,
    email: raw.email,
    phone: raw.phone ?? "",
    status: toStatus(raw.status),
    created_at: raw.created_at,
  };
}

export function toProduct(raw: BackendProduct, sellerNames = new Map<string, string>()): Product {
  return {
    id: raw.id,
    name: raw.name,
    sku: raw.sku,
    upc: raw.upc,
    seller_id: raw.seller_id,
    seller_name: lookupName(raw.seller_id, sellerNames, "Unknown seller"),
    description: raw.description ?? undefined,
    status: toStatus(raw.status),
    created_at: raw.created_at,
  };
}

export function toReceipt(
  raw: BackendReceipt,
  sellerNames = new Map<string, string>(),
  warehouseNames = new Map<string, string>(),
  products = new Map<string, Product>(),
): Receipt {
  return {
    id: raw.id,
    reference: raw.receipt_number,
    seller_id: raw.seller_id,
    seller_name: lookupName(raw.seller_id, sellerNames, "Unknown seller"),
    warehouse_id: raw.warehouse_id,
    warehouse_name: lookupName(raw.warehouse_id, warehouseNames, "Unknown warehouse"),
    tracking_number: raw.tracking_number ?? undefined,
    ticket_number: raw.ticket_number ?? undefined,
    status: raw.status as Receipt["status"],
    items: (raw.items ?? []).map((item) => toReceiptItem(item, products)),
    created_at: raw.created_at,
    created_by: raw.created_by,
  };
}

function toReceiptItem(raw: BackendReceiptItem, products: Map<string, Product>): ReceiptItem {
  const product = products.get(raw.product_id);
  return {
    id: raw.product_id,
    product_id: raw.product_id,
    product_name: product?.name ?? "Unknown product",
    sku: product?.sku ?? raw.upc,
    upc: raw.upc,
    good_quantity: raw.good_qty,
    damaged_quantity: raw.damaged_qty,
  };
}

export function toInventoryRecord(
  raw: BackendInventory,
  productMap = new Map<string, Product>(),
  sellerNames = new Map<string, string>(),
  warehouseNames = new Map<string, string>(),
): InventoryRecord {
  const product = productMap.get(raw.product_id);
  return {
    id: raw.id,
    product_id: raw.product_id,
    product_name: product?.name ?? "Unknown product",
    sku: product?.sku ?? "",
    upc: product?.upc ?? "",
    seller_id: raw.seller_id,
    seller_name: lookupName(raw.seller_id, sellerNames, "Unknown seller"),
    warehouse_id: raw.warehouse_id,
    warehouse_name: lookupName(raw.warehouse_id, warehouseNames, "Unknown warehouse"),
    on_hand: raw.on_hand,
    reserved: raw.reserved,
    available: raw.available ?? raw.on_hand - raw.reserved,
    damaged: raw.damaged,
    low_stock_threshold: raw.low_stock_threshold ?? 0,
  };
}

export function toMovement(raw: BackendMovement): Movement {
  const type = toMovementType(raw.movement_type);
  const quantityPair = movementQuantityPair(raw);
  return {
    id: raw.id,
    inventory_id: raw.inventory_id,
    type,
    quantity: raw.quantity,
    before: quantityPair.before,
    after: quantityPair.after,
    reference: `${raw.reference_type} ${raw.reference_id}`,
    performed_by: raw.performed_by,
    reason: raw.reason ?? undefined,
    created_at: raw.created_at,
  };
}

function toMovementType(type: string): MovementType {
  if (type === "DAMAGED_RECEIVED") return "DAMAGED";
  if (type === "RESERVATION_RELEASED") return "RELEASED";
  return type as MovementType;
}

function movementQuantityPair(raw: BackendMovement) {
  if (raw.movement_type === "RESERVED" || raw.movement_type === "RESERVATION_RELEASED") {
    return { before: raw.previous_reserved, after: raw.new_reserved };
  }
  if (raw.movement_type === "DAMAGED_RECEIVED") {
    return { before: raw.previous_damaged, after: raw.new_damaged };
  }
  return { before: raw.previous_on_hand, after: raw.new_on_hand };
}

export function toOrder(
  raw: BackendOrder,
  sellerNames = new Map<string, string>(),
  warehouseNames = new Map<string, string>(),
  products = new Map<string, Product>(),
  shipment?: Shipment,
): Order {
  return {
    id: raw.id,
    reference: raw.order_number,
    seller_id: raw.seller_id,
    seller_name: lookupName(raw.seller_id, sellerNames, "Unknown seller"),
    warehouse_id: raw.warehouse_id,
    warehouse_name: lookupName(raw.warehouse_id, warehouseNames, "Unknown warehouse"),
    status: raw.status as Order["status"],
    items: (raw.items ?? []).map((item) => {
      const product = products.get(item.product_id);
      return {
        product_id: item.product_id,
        product_name: product?.name ?? "Unknown product",
        sku: item.sku,
        ordered_quantity: item.quantity,
        reserved_quantity: item.reserved_quantity,
        picked_quantity: item.picked_quantity,
      };
    }),
    shipment,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
    created_by: raw.created_by,
    timeline: orderTimeline(raw),
  };
}

function orderTimeline(raw: BackendOrder): Order["timeline"] {
  const values: Order["timeline"] = [{ status: "CREATED", at: raw.created_at, by: raw.created_by }];
  if (raw.reserved_at) values.push({ status: "RESERVED", at: raw.reserved_at, by: raw.created_by });
  if (raw.picked_at) values.push({ status: "PICKED", at: raw.picked_at, by: raw.created_by });
  if (raw.packed_at) values.push({ status: "PACKED", at: raw.packed_at, by: raw.created_by });
  if (raw.shipped_at) values.push({ status: "SHIPPED", at: raw.shipped_at, by: raw.created_by });
  if (raw.cancelled_at) values.push({ status: "CANCELLED", at: raw.cancelled_at, by: raw.created_by });
  return values;
}

export function toShipment(raw: BackendShipment): Shipment {
  return {
    carrier: raw.carrier,
    tracking_number: raw.tracking_number,
    weight_kg: raw.weight,
    length_cm: raw.length,
    width_cm: raw.width,
    height_cm: raw.height,
    label_reference: raw.label_reference ?? undefined,
  };
}

export function toAuditLog(raw: BackendAuditLog, warehouseNames = new Map<string, string>()): AuditLog {
  return {
    id: raw.id,
    actor_id: raw.user_id,
    action: raw.action,
    entity: raw.entity_type,
    entity_reference: raw.entity_id,
    user_name: raw.user_id,
    role: raw.user_role as Role,
    warehouse_name: raw.warehouse_id ? lookupName(raw.warehouse_id, warehouseNames, "Unknown warehouse") : "System",
    created_at: raw.created_at,
    details: auditDetails(raw),
  };
}

function auditDetails(raw: BackendAuditLog): Record<string, string | number> {
  const details: Record<string, string | number> = {};
  if (raw.reason) details.reason = raw.reason;
  for (const [prefix, value] of [
    ["old", raw.old_state],
    ["new", raw.new_state],
  ] as const) {
    Object.entries(value ?? {}).forEach(([key, entry]) => {
      details[`${prefix}_${key}`] =
        typeof entry === "string" || typeof entry === "number" ? entry : JSON.stringify(entry);
    });
  }
  return details;
}

export function nameMap<T extends { id: string; name: string }>(values: T[]) {
  return new Map(values.map((value) => [value.id, value.name]));
}

export function objectMap<T extends { id: string }>(values: T[]) {
  return new Map(values.map((value) => [value.id, value]));
}
