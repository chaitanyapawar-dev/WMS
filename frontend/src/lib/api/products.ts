import type { Product } from "@/types";
import { http } from "./client";
import { type BackendProduct, cleanParams, nameMap, toProduct } from "./adapters";
import { list as listSellers } from "./sellers";

export interface ProductFilters {
  search?: string;
  seller_id?: string;
  status?: string;
}

/** GET /v1/products */
export async function list(filters: ProductFilters = {}): Promise<Product[]> {
  const all = await liveProducts();
  const activeFilters = cleanParams(filters);
  const q = (filters.search ?? "").toLowerCase();
  return all.filter((p) => {
    const matchesQuery =
      !q || p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q) || p.upc.includes(q);
    const matchesSeller = !activeFilters.seller_id || p.seller_id === activeFilters.seller_id;
    const matchesStatus = !activeFilters.status || p.status === activeFilters.status;
    return matchesQuery && matchesSeller && matchesStatus;
  });
}

/** GET /v1/products/upc/{upc} */
export async function getByUpc(upc: string): Promise<Product> {
  const sellerNames = nameMap(await listSellers());
  return toProduct((await http.get<BackendProduct>(`/products/upc/${encodeURIComponent(upc)}`)).data, sellerNames);
}

/** GET /v1/products/{product_id} */
export async function get(productId: string): Promise<Product> {
  const sellerNames = nameMap(await listSellers());
  return toProduct((await http.get<BackendProduct>(`/products/${productId}`)).data, sellerNames);
}

export interface CreateProductPayload {
  seller_id: string;
  name: string;
  sku: string;
  upc: string;
  description?: string;
}

/** POST /v1/products */
export async function create(payload: CreateProductPayload): Promise<Product> {
  const sellerNames = nameMap(await listSellers());
  return toProduct((await http.post<BackendProduct>("/products", payload)).data, sellerNames);
}

/** PATCH /v1/products/{product_id}/status */
export async function setStatus(productId: string, status: Product["status"]): Promise<Product> {
  const sellerNames = nameMap(await listSellers());
  return toProduct((await http.patch<BackendProduct>(`/products/${productId}/status`, { status })).data, sellerNames);
}

async function liveProducts(): Promise<Product[]> {
  const [products, sellers] = await Promise.all([http.get<BackendProduct[]>("/products"), listSellers()]);
  const sellerNames = nameMap(sellers);
  return products.data.map((product) => toProduct(product, sellerNames));
}
