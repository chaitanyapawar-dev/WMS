import type { AuditLog } from "@/types";
import { http } from "./client";
import { type BackendAuditLog, cleanParams, nameMap, toAuditLog } from "./adapters";
import { list as listUsers } from "./users";
import { list as listWarehouses } from "./warehouses";

export interface AuditFilters {
  search?: string;
  warehouse?: string;
  warehouse_id?: string;
  user?: string;
  action?: string;
  entity?: string;
}

/** GET /v1/audit-logs */
export async function list(filters: AuditFilters = {}): Promise<AuditLog[]> {
  const all = await liveAuditLogs(filters);
  const q = (filters.search ?? "").toLowerCase();
  return all.filter((log) => {
    const matchesQuery =
      !q || log.entity_reference.toLowerCase().includes(q) || log.user_name.toLowerCase().includes(q);
    const matchesAction = !filters.action || filters.action === "ALL" || log.action === filters.action;
    const matchesEntity = !filters.entity || filters.entity === "ALL" || log.entity === filters.entity;
    const matchesWarehouse =
      !filters.warehouse || filters.warehouse === "ALL" || log.warehouse_name === filters.warehouse;
    const matchesUser = !filters.user || filters.user === "ALL" || log.user_name === filters.user;
    return matchesQuery && matchesAction && matchesEntity && matchesWarehouse && matchesUser;
  }).sort((left, right) => Date.parse(right.created_at) - Date.parse(left.created_at));
}

async function liveAuditLogs(filters: AuditFilters): Promise<AuditLog[]> {
  const params = cleanParams({
    action: filters.action,
    entity_type: filters.entity,
    warehouse_id: filters.warehouse_id,
  });
  const [logs, warehouses, users] = await Promise.all([
    http.get<BackendAuditLog[]>("/audit-logs", { params }),
    listWarehouses(),
    listUsers().catch(() => []),
  ]);
  const userNames = new Map(users.map((user) => [user.id, `${user.first_name} ${user.last_name}`]));
  return logs.data.map((log) => ({
    ...toAuditLog(log, nameMap(warehouses)),
    user_name: userNames.get(log.user_id) ?? "System user",
  }));
}
