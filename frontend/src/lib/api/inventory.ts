import type { InventoryRecord, Movement } from "@/types";
import { http } from "./client";
import {
  type BackendInventory,
  type BackendMovement,
  cleanParams,
  nameMap,
  objectMap,
  toInventoryRecord,
  toMovement,
} from "./adapters";
import { list as listProducts } from "./products";
import { list as listSellers } from "./sellers";
import { list as listWarehouses } from "./warehouses";

export interface InventoryFilters {
  search?: string;
  warehouse_id?: string;
  seller_id?: string;
  availability?: string;
}

/** GET /v1/inventory */
export async function list(filters: InventoryFilters = {}): Promise<InventoryRecord[]> {
  const all = await liveInventory(filters);
  const activeFilters = cleanParams(filters);
  const q = (filters.search ?? "").toLowerCase();
  return all.filter((i) => {
    const matchesQuery =
      !q || i.product_name.toLowerCase().includes(q) || i.sku.toLowerCase().includes(q) || i.upc.includes(q);
    const matchesWarehouse = !activeFilters.warehouse_id || i.warehouse_id === activeFilters.warehouse_id;
    const matchesSeller = !activeFilters.seller_id || i.seller_id === activeFilters.seller_id;
    const availability = filters.availability ?? "ALL";
    const matchesAvailability =
      availability === "ALL" ||
      (availability === "IN_STOCK" && i.available > 0) ||
      (availability === "LOW" &&
        i.low_stock_threshold > 0 &&
        i.available <= i.low_stock_threshold) ||
      (availability === "NONE" && i.available <= 0) ||
      (availability === "DAMAGED" && i.damaged > 0);
    return matchesQuery && matchesWarehouse && matchesSeller && matchesAvailability;
  });
}

/** GET /v1/inventory/{inventory_id} */
export async function get(inventoryId: string): Promise<InventoryRecord> {
  return toInventoryRecord((await http.get<BackendInventory>(`/inventory/${inventoryId}`)).data, ...(await inventoryLookups()));
}

export interface AdjustPayload {
  delta: number;
  reason: string;
}

/** POST /v1/inventory/{inventory_id}/adjust */
export async function adjust(inventoryId: string, payload: AdjustPayload): Promise<InventoryRecord> {
  return toInventoryRecord(
    (await http.post<BackendInventory>(`/inventory/${inventoryId}/adjust`, payload)).data,
    ...(await inventoryLookups()),
  );
}

/** GET /v1/inventory/{inventory_id}/movements */
export async function movements(inventoryId: string): Promise<Movement[]> {
  return (await http.get<BackendMovement[]>(`/inventory/${inventoryId}/movements`)).data.map(toMovement);
}

async function liveInventory(filters: InventoryFilters): Promise<InventoryRecord[]> {
  const params = cleanParams({
    warehouse_id: filters.warehouse_id,
    seller_id: filters.seller_id,
  });
  const [inventory, lookups] = await Promise.all([http.get<BackendInventory[]>("/inventory", { params }), inventoryLookups()]);
  return inventory.data.map((record) => toInventoryRecord(record, ...lookups));
}

async function inventoryLookups() {
  const [products, sellers, warehouses] = await Promise.all([listProducts(), listSellers(), listWarehouses()]);
  return [objectMap(products), nameMap(sellers), nameMap(warehouses)] as const;
}
