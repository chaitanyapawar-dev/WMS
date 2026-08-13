import type { Receipt } from "@/types";
import { http } from "./client";
import { type BackendReceipt, cleanParams, nameMap, objectMap, toReceipt } from "./adapters";
import { list as listProducts } from "./products";
import { list as listSellers } from "./sellers";
import { list as listWarehouses } from "./warehouses";

export interface ReceiptFilters {
  search?: string;
  warehouse_id?: string;
  status?: string;
}

/** GET /v1/receipts */
export async function list(filters: ReceiptFilters = {}): Promise<Receipt[]> {
  const all = await liveReceipts(filters);
  const activeFilters = cleanParams(filters);
  const q = (filters.search ?? "").toLowerCase();
  return all.filter((r) => {
    const matchesQuery =
      !q ||
      r.reference.toLowerCase().includes(q) ||
      r.seller_name.toLowerCase().includes(q) ||
      (r.tracking_number ?? "").toLowerCase().includes(q) ||
      (r.ticket_number ?? "").toLowerCase().includes(q);
    const matchesWarehouse = !activeFilters.warehouse_id || r.warehouse_id === activeFilters.warehouse_id;
    const matchesStatus = !activeFilters.status || r.status === activeFilters.status;
    return matchesQuery && matchesWarehouse && matchesStatus;
  });
}

/** GET /v1/receipts/{receipt_id} */
export async function get(receiptId: string): Promise<Receipt> {
  return toReceipt((await http.get<BackendReceipt>(`/receipts/${receiptId}`)).data, ...(await receiptLookups()));
}

export interface CreateReceiptPayload {
  seller_id: string;
  warehouse_id: string;
  tracking_number?: string;
  ticket_number?: string;
}

/** POST /v1/receipts */
export async function create(payload: CreateReceiptPayload): Promise<Receipt> {
  const request = {
    seller_id: payload.seller_id,
    warehouse_id: payload.warehouse_id,
    tracking_number: payload.tracking_number || undefined,
    ticket_number: payload.ticket_number || undefined,
  };
  return toReceipt((await http.post<BackendReceipt>("/receipts", request)).data, ...(await receiptLookups()));
}

export interface AddItemPayload {
  product_id: string;
  good_quantity: number;
  damaged_quantity: number;
}

/** POST /v1/receipts/{receipt_id}/items */
export async function addItem(receiptId: string, payload: AddItemPayload): Promise<Receipt> {
  const request = {
    upc: payload.product_id,
    good_qty: payload.good_quantity,
    damaged_qty: payload.damaged_quantity,
  };
  return toReceipt((await http.post<BackendReceipt>(`/receipts/${receiptId}/items`, request)).data, ...(await receiptLookups()));
}

/** POST /v1/receipts/{receipt_id}/complete */
export async function complete(receiptId: string): Promise<Receipt> {
  return toReceipt((await http.post<BackendReceipt>(`/receipts/${receiptId}/complete`, {})).data, ...(await receiptLookups()));
}

async function liveReceipts(filters: ReceiptFilters): Promise<Receipt[]> {
  const params = cleanParams({
    warehouse_id: filters.warehouse_id,
    status: filters.status,
  });
  const [receipts, lookups] = await Promise.all([http.get<BackendReceipt[]>("/receipts", { params }), receiptLookups()]);
  return receipts.data.map((receipt) => toReceipt(receipt, ...lookups));
}

async function receiptLookups() {
  const [sellers, warehouses, products] = await Promise.all([listSellers(), listWarehouses(), listProducts()]);
  return [nameMap(sellers), nameMap(warehouses), objectMap(products)] as const;
}
