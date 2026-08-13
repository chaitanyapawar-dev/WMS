export type Role = "OWNER" | "MANAGER" | "RECEIVING_STAFF" | "FULFILLMENT_STAFF";

export type EntityStatus = "ACTIVE" | "INACTIVE";

export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
  status: EntityStatus;
  warehouse_ids: string[];
}

export interface Warehouse {
  id: string;
  name: string;
  code: string;
  city: string;
  state: string;
  status: EntityStatus;
}

export interface Seller {
  id: string;
  name: string;
  code: string;
  email: string;
  phone: string;
  status: EntityStatus;
  created_at: string;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  upc: string;
  seller_id: string;
  seller_name: string;
  description?: string | undefined;
  status: EntityStatus;
  created_at: string;
}

export type ReceiptStatus = "DRAFT" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";

export interface ReceiptItem {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  upc: string;
  good_quantity: number;
  damaged_quantity: number;
}

export interface Receipt {
  id: string;
  reference: string;
  seller_id: string;
  seller_name: string;
  warehouse_id: string;
  warehouse_name: string;
  tracking_number?: string | undefined;
  ticket_number?: string | undefined;
  status: ReceiptStatus;
  items: ReceiptItem[];
  created_at: string;
  created_by: string;
}

export interface InventoryRecord {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  upc: string;
  seller_id: string;
  seller_name: string;
  warehouse_id: string;
  warehouse_name: string;
  on_hand: number;
  reserved: number;
  available: number;
  damaged: number;
  low_stock_threshold: number;
}

export type MovementType =
  | "RECEIVED"
  | "ADJUSTMENT_INCREASE"
  | "ADJUSTMENT_DECREASE"
  | "RESERVED"
  | "RELEASED"
  | "SHIPPED"
  | "DAMAGED";

export interface Movement {
  id: string;
  inventory_id: string;
  type: MovementType;
  quantity: number;
  before: number;
  after: number;
  reference?: string | undefined;
  performed_by: string;
  reason?: string | undefined;
  created_at: string;
}

export type OrderStatus =
  | "NEW"
  | "RESERVED"
  | "PICKING"
  | "PICKED"
  | "PACKED"
  | "READY_TO_SHIP"
  | "SHIPPED"
  | "CANCELLED";

export interface OrderItem {
  product_id: string;
  product_name: string;
  sku: string;
  ordered_quantity: number;
  reserved_quantity: number;
  picked_quantity: number;
}

export interface Shipment {
  carrier: string;
  tracking_number: string;
  weight_kg: number;
  length_cm: number;
  width_cm: number;
  height_cm: number;
  label_reference?: string | undefined;
}

export interface Order {
  id: string;
  reference: string;
  seller_id: string;
  seller_name: string;
  warehouse_id: string;
  warehouse_name: string;
  status: OrderStatus;
  items: OrderItem[];
  shipment?: Shipment | undefined;
  created_at: string;
  updated_at: string;
  created_by: string;
  timeline: { status: OrderStatus | "CREATED"; at: string; by: string }[];
}

export interface AuditLog {
  id: string;
  actor_id: string;
  action: string;
  entity: string;
  entity_reference: string;
  user_name: string;
  role: Role;
  warehouse_name: string;
  created_at: string;
  details: Record<string, string | number>;
}

export interface Paginated<T> {
  items: T[];
  total: number;
}
