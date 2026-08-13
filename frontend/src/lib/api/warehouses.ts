import type { Warehouse } from "@/types";
import { http } from "./client";
import { type BackendWarehouse, toWarehouse } from "./adapters";

/** GET /v1/warehouses */
export async function list(): Promise<Warehouse[]> {
  return (await http.get<BackendWarehouse[]>("/warehouses")).data.map(toWarehouse);
}

/** GET /v1/warehouses/{warehouse_id} */
export async function get(warehouseId: string): Promise<Warehouse> {
  return toWarehouse((await http.get<BackendWarehouse>(`/warehouses/${warehouseId}`)).data);
}
