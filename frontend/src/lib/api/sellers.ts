import type { Seller } from "@/types";
import { http } from "./client";
import { type BackendSeller, cleanParams, toSeller } from "./adapters";

export interface SellerFilters {
  search?: string;
  status?: string;
}

/** GET /v1/sellers */
export async function list(filters: SellerFilters = {}): Promise<Seller[]> {
  const data = (await http.get<BackendSeller[]>("/sellers")).data.map(toSeller);
  const activeFilters = cleanParams(filters);
  return data.filter((s) => {
    const q = (filters.search ?? "").toLowerCase();
    const matchesQuery = !q || s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q);
    const matchesStatus = !activeFilters.status || s.status === activeFilters.status;
    return matchesQuery && matchesStatus;
  });
}

/** GET /v1/sellers/{seller_id} */
export async function get(sellerId: string): Promise<Seller> {
  return toSeller((await http.get<BackendSeller>(`/sellers/${sellerId}`)).data);
}

export interface CreateSellerPayload {
  name: string;
  code: string;
  email: string;
  phone: string;
}

/** POST /v1/sellers */
export async function create(payload: CreateSellerPayload): Promise<Seller> {
  const request = {
    name: payload.name,
    seller_code: payload.code,
    email: payload.email,
    phone: payload.phone || undefined,
  };
  return toSeller((await http.post<BackendSeller>("/sellers", request)).data);
}

/** PATCH /v1/sellers/{seller_id}/status */
export async function setStatus(sellerId: string, status: Seller["status"]): Promise<Seller> {
  return toSeller((await http.patch<BackendSeller>(`/sellers/${sellerId}/status`, { status })).data);
}
