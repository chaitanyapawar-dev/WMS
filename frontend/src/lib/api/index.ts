/**
 * Centralized typed API layer.
 *
 * Every module maps 1:1 to the FastAPI routes under /v1. Components never call
 * axios directly — they consume these functions through TanStack Query.
 */
export * as authApi from "./auth";
export * as warehousesApi from "./warehouses";
export * as sellersApi from "./sellers";
export * as productsApi from "./products";
export * as receiptsApi from "./receipts";
export * as inventoryApi from "./inventory";
export * as ordersApi from "./orders";
export * as auditApi from "./audit";
export * as usersApi from "./users";
export * as aiApi from "./ai";
export * as voiceApi from "./voice";
