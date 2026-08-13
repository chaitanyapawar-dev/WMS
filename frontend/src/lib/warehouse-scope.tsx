import { useQuery } from "@tanstack/react-query";
import { createContext, use, useEffect, useMemo, useState, type ReactNode } from "react";
import { warehousesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/auth-context";
import type { Warehouse } from "@/types";

interface ScopeValue {
  warehouses: Warehouse[];
  /** "ALL" is only available to roles allowed to see every facility. */
  scopeId: string;
  setScopeId: (id: string) => void;
  canSwitch: boolean;
  scopeLabel: string;
  /** Filter value to pass to the API — undefined means "no warehouse filter". */
  warehouseFilter: string | undefined;
}

const ScopeContext = createContext<ScopeValue | null>(null);

export function WarehouseScopeProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const { data } = useQuery({ queryKey: ["warehouses"], queryFn: warehousesApi.list });

  const warehouses = useMemo(() => {
    const all = data ?? [];
    if (!user) return [];
    if (user.role === "OWNER") return all;
    return all.filter((w) => user.warehouse_ids.includes(w.id));
  }, [data, user]);

  const canSwitch = (user?.role === "OWNER" || (user?.warehouse_ids.length ?? 0) > 1) ?? false;
  const [scopeId, setScopeId] = useState<string>("ALL");

  useEffect(() => {
    if (!user) return;
    if (user.role === "OWNER") setScopeId("ALL");
    else setScopeId(user.warehouse_ids[0] ?? "ALL");
  }, [user]);

  const value = useMemo<ScopeValue>(() => {
    const active = warehouses.find((w) => w.id === scopeId);
    return {
      warehouses,
      scopeId,
      setScopeId,
      canSwitch,
      scopeLabel: active ? `${active.city}, ${active.state}` : "All Warehouses",
      warehouseFilter: scopeId === "ALL" ? undefined : scopeId,
    };
  }, [warehouses, scopeId, canSwitch]);

  return <ScopeContext value={value}>{children}</ScopeContext>;
}

export function useWarehouseScope() {
  const context = use(ScopeContext);
  if (!context) throw new Error("useWarehouseScope must be used inside <WarehouseScopeProvider>");
  return context;
}
