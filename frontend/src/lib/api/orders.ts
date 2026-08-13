import type { Order, Shipment } from "@/types";
import { http } from "./client";
import {
  type BackendOrder,
  type BackendShipment,
  cleanParams,
  nameMap,
  objectMap,
  toOrder,
  toShipment,
} from "./adapters";
import { list as listProducts } from "./products";
import { list as listSellers } from "./sellers";
import { list as listWarehouses } from "./warehouses";

export interface OrderFilters {
  search?: string;
  warehouse_id?: string;
  seller_id?: string;
  status?: string;
}

const shipmentCache = new Map<string, Shipment>();

/** GET /v1/orders */
export async function list(filters: OrderFilters = {}): Promise<Order[]> {
  const all = await liveOrders(filters);
  const activeFilters = cleanParams(filters);
  const q = (filters.search ?? "").toLowerCase();
  return all.filter((o) => {
    const matchesQuery = !q || o.reference.toLowerCase().includes(q) || o.seller_name.toLowerCase().includes(q);
    const matchesWarehouse = !activeFilters.warehouse_id || o.warehouse_id === activeFilters.warehouse_id;
    const matchesSeller = !activeFilters.seller_id || o.seller_id === activeFilters.seller_id;
    const matchesStatus = !activeFilters.status || o.status === activeFilters.status;
    return matchesQuery && matchesWarehouse && matchesSeller && matchesStatus;
  });
}

/** GET /v1/orders/{order_id} */
export async function get(orderId: string): Promise<Order> {
  return toOrder((await http.get<BackendOrder>(`/orders/${orderId}`)).data, ...(await orderLookups()), shipmentCache.get(orderId));
}

export interface CreateOrderPayload {
  seller_id: string;
  warehouse_id: string;
  items: { product_id: string; quantity: number }[];
}

/** POST /v1/orders */
export async function create(payload: CreateOrderPayload): Promise<Order> {
  const products = await listProducts({ seller_id: payload.seller_id });
  const productsById = objectMap(products);
  const request = {
    seller_id: payload.seller_id,
    warehouse_id: payload.warehouse_id,
    items: payload.items.map((item) => ({
      sku: productsById.get(item.product_id)?.sku ?? item.product_id,
      quantity: item.quantity,
    })),
  };
  return toOrder((await http.post<BackendOrder>("/orders", request)).data, ...(await orderLookups()));
}

export type OrderAction = "reserve" | "start-picking" | "picked" | "packed" | "ship" | "cancel";

/** POST /v1/orders/{order_id}/{action} - backend owns every state transition. */
export async function transition(orderId: string, action: OrderAction): Promise<Order> {
  return toOrder(
    (await http.post<BackendOrder>(`/orders/${orderId}/${action}`, {})).data,
    ...(await orderLookups()),
    shipmentCache.get(orderId),
  );
}

/** POST /v1/orders/{order_id}/shipment */
export async function createShipment(orderId: string, shipment: Shipment): Promise<Shipment> {
  const request = {
    carrier: shipment.carrier,
    tracking_number: shipment.tracking_number,
    weight: shipment.weight_kg,
    length: shipment.length_cm,
    width: shipment.width_cm,
    height: shipment.height_cm,
    label_reference: shipment.label_reference,
  };
  const created = toShipment((await http.post<BackendShipment>(`/orders/${orderId}/shipment`, request)).data);
  shipmentCache.set(orderId, created);
  return created;
}

async function liveOrders(filters: OrderFilters): Promise<Order[]> {
  const params = cleanParams({
    warehouse_id: filters.warehouse_id,
    seller_id: filters.seller_id,
    status: filters.status,
  });
  const [orders, lookups] = await Promise.all([http.get<BackendOrder[]>("/orders", { params }), orderLookups()]);
  return orders.data.map((order) => toOrder(order, ...lookups, shipmentCache.get(order.id)));
}

async function orderLookups() {
  const [sellers, warehouses, products] = await Promise.all([listSellers(), listWarehouses(), listProducts()]);
  return [nameMap(sellers), nameMap(warehouses), objectMap(products)] as const;
}
