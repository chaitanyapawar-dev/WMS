import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  Boxes,
  CheckCircle2,
  ClipboardList,
  History,
  PackageOpen,
  ShieldAlert,
  ShoppingCart,
  Store,
  Truck,
} from "lucide-react";
import { KpiCard } from "@/components/data-display/kpi-card";
import { StatusBadge } from "@/components/data-display/status-badge";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  FULFILLMENT_QUEUE_STATUSES,
  OPEN_RECEIPT_STATUSES,
  inventoryMetrics,
  orderMetrics,
  receiptMetrics,
  warehouseRecords,
} from "@/features/dashboard/dashboard-metrics";
import { auditApi, inventoryApi, ordersApi, receiptsApi, usersApi } from "@/lib/api";
import { errorMessage } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { formatNumber, formatRelative, greeting, humanize } from "@/lib/utils/format";
import { useWarehouseScope } from "@/lib/warehouse-scope";
import type { AuditLog, InventoryRecord, Order, Receipt, Role, User, Warehouse } from "@/types";

export function DashboardPage() {
  const { user } = useAuth();
  const { warehouseFilter, scopeLabel, warehouses } = useWarehouseScope();
  const role = user?.role;
  const isExec = role === "OWNER" || role === "MANAGER";
  const filters = { warehouse_id: warehouseFilter };

  const inventory = useQuery({
    queryKey: ["inventory", filters],
    queryFn: () => inventoryApi.list(filters),
  });
  const orders = useQuery({
    queryKey: ["orders", filters],
    queryFn: () => ordersApi.list(filters),
  });
  const receipts = useQuery({
    queryKey: ["receipts", filters],
    queryFn: () => receiptsApi.list(filters),
  });
  const audit = useQuery({
    queryKey: ["audit-logs", { warehouse_id: warehouseFilter }],
    queryFn: () => auditApi.list({ warehouse_id: warehouseFilter }),
    enabled: isExec,
  });
  const users = useQuery({
    queryKey: ["users"],
    queryFn: usersApi.list,
    enabled: role === "OWNER",
  });

  if (!user) return null;

  const inv = inventory.data ?? [];
  const ord = orders.data ?? [];
  const rec = receipts.data ?? [];
  const stock = inventoryMetrics(inv);
  const orderCounts = orderMetrics(ord);
  const receiptCounts = receiptMetrics(rec);
  const loading = inventory.isLoading || orders.isLoading || receipts.isLoading;
  const dataError = inventory.error ?? orders.error ?? receipts.error;
  const visibleWarehouses = warehouseFilter
    ? warehouses.filter((warehouse) => warehouse.id === warehouseFilter)
    : warehouses;

  const headerTitle =
    role === "OWNER"
      ? `${greeting()}, ${user.first_name}`
      : role === "MANAGER"
        ? "Operations Overview"
        : role === "RECEIVING_STAFF"
          ? "Receiving"
          : "Fulfillment";
  const headerDescription =
    role === "OWNER" ? `Live operational totals for ${scopeLabel.toLowerCase()}.` : scopeLabel;

  if (dataError) {
    return (
      <div className="space-y-6">
        <PageHeader title={headerTitle} description={headerDescription} />
        <section className="surface-card border-destructive/30 p-5">
          <h2 className="text-base font-semibold">Dashboard data unavailable</h2>
          <p className="mt-1 text-sm text-muted-foreground">{errorMessage(dataError)}</p>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={headerTitle}
        description={headerDescription}
        actions={
          role === "RECEIVING_STAFF" ? (
            <Button asChild className="grad-brand rounded-xl text-white">
              <Link to="/receiving/new">New Receipt</Link>
            </Button>
          ) : undefined
        }
      />

      {role === "OWNER" && (
        <section className="grain surface-card relative overflow-hidden p-6">
          <div className="glow-hero pointer-events-none absolute inset-0" aria-hidden />
          <div className="grain-overlay opacity-[0.07]" aria-hidden />
          <div className="relative flex flex-wrap items-end justify-between gap-6">
            <div>
              <h2 className="text-lg font-semibold">Operations Overview</h2>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">
                Live status from the warehouse master records in this scope.
              </p>
            </div>
            <div className="flex flex-wrap gap-4">
              {visibleWarehouses.map((warehouse) => {
                const active = warehouse.status === "ACTIVE";
                return (
                  <span key={warehouse.id} className="flex items-center gap-2 text-sm">
                    <span
                      className={`size-1.5 rounded-full ${active ? "bg-success" : "bg-destructive"}`}
                      aria-hidden
                    />
                    {warehouse.city} {active ? "Operational" : "Inactive"}
                  </span>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {role === "OWNER" ? (
        <OwnerMetrics
          stock={stock}
          orders={orderCounts}
          receipts={receiptCounts}
          loading={loading}
        />
      ) : role === "MANAGER" ? (
        <ManagerMetrics
          stock={stock}
          orders={orderCounts}
          receipts={receiptCounts}
          loading={loading}
        />
      ) : role === "RECEIVING_STAFF" ? (
        <ReceivingMetrics receipts={receiptCounts} loading={loading} />
      ) : (
        <FulfillmentMetrics orders={orderCounts} loading={loading} />
      )}

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        {isExec ? (
          <WarehouseOverview
            warehouses={visibleWarehouses}
            allAccessibleWarehouses={warehouses}
            inventory={inv}
            orders={ord}
            receipts={rec}
          />
        ) : (
          <NeedsAttention role={role} orders={ord} receipts={rec} inventory={inv} />
        )}

        <div className="space-y-4">
          {isExec ? (
            <RecentActivity
              logs={audit.data ?? []}
              users={users.data ?? []}
              loading={audit.isLoading}
              error={audit.error}
            />
          ) : null}
          <QuickActions role={role} />
        </div>
      </div>
    </div>
  );
}

function OwnerMetrics({
  stock,
  orders,
  receipts,
  loading,
}: {
  stock: ReturnType<typeof inventoryMetrics>;
  orders: ReturnType<typeof orderMetrics>;
  receipts: ReturnType<typeof receiptMetrics>;
  loading: boolean;
}) {
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Total On Hand"
          value={stock.onHand}
          icon={Boxes}
          loading={loading}
          hint="Current inventory"
        />
        <KpiCard
          label="Available Stock"
          value={stock.available}
          icon={CheckCircle2}
          tone="success"
          loading={loading}
          hint="On hand minus reserved"
        />
        <KpiCard
          label="Reserved Stock"
          value={stock.reserved}
          icon={ShieldAlert}
          tone="warning"
          loading={loading}
          hint="Committed to open orders"
        />
        <KpiCard
          label="Damaged Stock"
          value={stock.damaged}
          icon={AlertTriangle}
          tone="danger"
          loading={loading}
          hint="Recorded damaged units"
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Pending Receipts"
          value={receipts.pending}
          icon={PackageOpen}
          tone="info"
          loading={loading}
          hint="Draft or in progress"
          to="/receiving"
        />
        <KpiCard
          label="Open Orders"
          value={orders.open}
          icon={ShoppingCart}
          loading={loading}
          hint="Not shipped or cancelled"
          to="/orders"
        />
        <KpiCard
          label="Ready to Ship"
          value={orders.readyToShip}
          icon={Truck}
          tone="brand"
          loading={loading}
          hint="Shipment prepared"
          to="/fulfillment"
        />
        <KpiCard
          label="Shipped Orders"
          value={orders.shipped}
          icon={CheckCircle2}
          tone="success"
          loading={loading}
          hint="All shipped orders"
          to="/orders"
        />
      </div>
    </>
  );
}

function ManagerMetrics({
  stock,
  orders,
  receipts,
  loading,
}: {
  stock: ReturnType<typeof inventoryMetrics>;
  orders: ReturnType<typeof orderMetrics>;
  receipts: ReturnType<typeof receiptMetrics>;
  loading: boolean;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="Pending Receipts"
        value={receipts.pending}
        icon={PackageOpen}
        tone="info"
        loading={loading}
        hint="Draft or in progress"
        to="/receiving"
      />
      <KpiCard
        label="Orders Awaiting Pick"
        value={orders.toPick}
        icon={ClipboardList}
        tone="warning"
        loading={loading}
        hint="Reserved orders"
        to="/fulfillment"
      />
      <KpiCard
        label="Orders Awaiting Pack"
        value={orders.readyToPack}
        icon={PackageOpen}
        loading={loading}
        hint="Picked orders"
        to="/fulfillment"
      />
      <KpiCard
        label="Ready to Ship"
        value={orders.readyToShip}
        icon={Truck}
        tone="brand"
        loading={loading}
        hint="Shipment prepared"
        to="/fulfillment"
      />
      <KpiCard
        label="Available Inventory"
        value={stock.available}
        icon={CheckCircle2}
        tone="success"
        loading={loading}
        hint="Sellable units"
      />
      <KpiCard
        label="Reserved Inventory"
        value={stock.reserved}
        icon={ShieldAlert}
        tone="warning"
        loading={loading}
        hint="Committed units"
      />
      <KpiCard
        label="Damaged Inventory"
        value={stock.damaged}
        icon={AlertTriangle}
        tone="danger"
        loading={loading}
        hint="Recorded damaged units"
      />
    </div>
  );
}

function ReceivingMetrics({
  receipts,
  loading,
}: {
  receipts: ReturnType<typeof receiptMetrics>;
  loading: boolean;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="Active Receipts"
        value={receipts.pending}
        icon={PackageOpen}
        tone="info"
        loading={loading}
        hint="Draft or in progress"
        to="/receiving"
      />
      <KpiCard
        label="Completed Receipts"
        value={receipts.completed}
        icon={CheckCircle2}
        tone="success"
        loading={loading}
        hint="All completed receipts"
      />
      <KpiCard
        label="Units Received"
        value={receipts.unitsReceived}
        icon={Boxes}
        loading={loading}
        hint="Good and damaged completed units"
      />
      <KpiCard
        label="Damaged Units"
        value={receipts.damagedUnits}
        icon={AlertTriangle}
        tone="danger"
        loading={loading}
        hint="Completed receipt damage"
      />
    </div>
  );
}

function FulfillmentMetrics({
  orders,
  loading,
}: {
  orders: ReturnType<typeof orderMetrics>;
  loading: boolean;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="Orders to Pick"
        value={orders.toPick}
        icon={ClipboardList}
        tone="warning"
        loading={loading}
        hint="Reserved and waiting"
        to="/fulfillment"
      />
      <KpiCard
        label="Picking"
        value={orders.picking}
        icon={Boxes}
        tone="info"
        loading={loading}
        hint="Picking in progress"
        to="/fulfillment"
      />
      <KpiCard
        label="Ready to Pack"
        value={orders.readyToPack}
        icon={PackageOpen}
        loading={loading}
        hint="Picked orders"
        to="/fulfillment"
      />
      <KpiCard
        label="Ready to Ship"
        value={orders.readyToShip}
        icon={Truck}
        tone="brand"
        loading={loading}
        hint="Shipment prepared"
        to="/fulfillment"
      />
    </div>
  );
}

function WarehouseOverview({
  warehouses,
  allAccessibleWarehouses,
  inventory,
  orders,
  receipts,
}: {
  warehouses: Warehouse[];
  allAccessibleWarehouses: Warehouse[];
  inventory: InventoryRecord[];
  orders: Order[];
  receipts: Receipt[];
}) {
  const first = warehouses[0]?.id ?? "";
  const knownWarehouseIds = new Set(allAccessibleWarehouses.map((warehouse) => warehouse.id));
  const unresolvedInventory = inventory.filter(
    (record) => !knownWarehouseIds.has(record.warehouse_id),
  );
  const unresolvedOnHand = inventoryMetrics(unresolvedInventory).onHand;

  return (
    <section className="surface-card p-5">
      <h2 className="text-base font-semibold">Warehouse Overview</h2>
      {warehouses.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">
          No warehouse records are available in this scope.
        </p>
      ) : (
        <Tabs key={first} defaultValue={first} className="mt-4">
          <TabsList className="rounded-xl">
            {warehouses.map((warehouse) => (
              <TabsTrigger key={warehouse.id} value={warehouse.id} className="rounded-lg">
                {warehouse.city}
              </TabsTrigger>
            ))}
          </TabsList>
          {warehouses.map((warehouse) => {
            const warehouseInventory = warehouseRecords(inventory, warehouse.id);
            const warehouseOrders = warehouseRecords(orders, warehouse.id);
            const warehouseReceipts = warehouseRecords(receipts, warehouse.id);
            const stock = inventoryMetrics(warehouseInventory);
            const orderCounts = orderMetrics(warehouseOrders);
            const receiptCounts = receiptMetrics(warehouseReceipts);
            const rows = [
              ["On Hand", stock.onHand],
              ["Reserved", stock.reserved],
              ["Damaged", stock.damaged],
              ["Open Receipts", receiptCounts.pending],
              ["Open Orders", orderCounts.open],
              ["Ready to Ship", orderCounts.readyToShip],
            ] as [string, number][];
            const max = Math.max(...rows.map(([, value]) => value), 1);

            return (
              <TabsContent key={warehouse.id} value={warehouse.id} className="mt-4 space-y-3">
                <p className="text-xs text-muted-foreground">
                  {warehouse.name} · {warehouse.status === "ACTIVE" ? "Operational" : "Inactive"}
                </p>
                {rows.map(([label, value]) => (
                  <div key={label} className="grid grid-cols-[140px_1fr_64px] items-center gap-3">
                    <span className="text-sm text-muted-foreground">{label}</span>
                    <span className="h-2 overflow-hidden rounded-full bg-muted">
                      <span
                        className="grad-brand block h-full rounded-full"
                        style={{ width: `${(value / max) * 100}%` }}
                      />
                    </span>
                    <span className="num text-right text-sm font-medium">
                      {formatNumber(value)}
                    </span>
                  </div>
                ))}
              </TabsContent>
            );
          })}
        </Tabs>
      )}
      {unresolvedOnHand > 0 ? (
        <p className="mt-4 text-xs text-muted-foreground">
          {formatNumber(unresolvedOnHand)} on-hand units reference warehouse records that are no
          longer available.
        </p>
      ) : null}
    </section>
  );
}

function NeedsAttention({
  role,
  orders,
  receipts,
  inventory,
}: {
  role: Role;
  orders: Order[];
  receipts: Receipt[];
  inventory: InventoryRecord[];
}) {
  const receivingItems = [
    ...receipts
      .filter((receipt) => OPEN_RECEIPT_STATUSES.includes(receipt.status))
      .map((receipt) => ({
        id: receipt.id,
        tone: "warning" as const,
        title: `${receipt.reference} awaiting completion`,
        meta: `${receipt.seller_name} · ${receipt.warehouse_name}`,
      })),
    ...inventory
      .filter(
        (record) =>
          record.low_stock_threshold > 0 && record.available <= record.low_stock_threshold,
      )
      .map((record) => ({
        id: record.id,
        tone: "danger" as const,
        title: `${record.product_name} is at or below its stock threshold`,
        meta: `${record.available} available · threshold ${record.low_stock_threshold} · ${record.warehouse_name}`,
      })),
  ];
  const fulfillmentItems = orders
    .filter((order) => FULFILLMENT_QUEUE_STATUSES.includes(order.status))
    .sort((left, right) => Date.parse(left.created_at) - Date.parse(right.created_at))
    .map((order) => ({
      id: order.id,
      tone: order.status === "READY_TO_SHIP" ? ("warning" as const) : ("info" as const),
      title: `${order.reference} · ${humanize(order.status)}`,
      meta: `${order.seller_name} · ${order.warehouse_name}`,
    }));
  const items = (role === "RECEIVING_STAFF" ? receivingItems : fulfillmentItems).slice(0, 8);

  return (
    <section className="surface-card p-5">
      <h2 className="text-base font-semibold">Needs Attention</h2>
      <ul className="mt-4 divide-y divide-border">
        {items.map((item) => (
          <li
            key={`${item.id}-${item.title}`}
            className="flex items-center justify-between gap-3 py-3"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{item.title}</p>
              <p className="truncate text-xs text-muted-foreground">{item.meta}</p>
            </div>
            <StatusBadge
              status={
                item.tone === "danger" ? "Urgent" : item.tone === "warning" ? "Attention" : "Info"
              }
              tone={item.tone}
            />
          </li>
        ))}
        {items.length === 0 ? (
          <li className="py-6 text-sm text-muted-foreground">Nothing needs attention right now.</li>
        ) : null}
      </ul>
    </section>
  );
}

function RecentActivity({
  logs,
  users,
  loading,
  error,
}: {
  logs: AuditLog[];
  users: User[];
  loading: boolean;
  error: Error | null;
}) {
  const userById = new Map(users.map((user) => [user.id, `${user.first_name} ${user.last_name}`]));

  return (
    <section className="surface-card p-5">
      <h2 className="text-base font-semibold">Recent Activity</h2>
      <ul className="mt-4 space-y-4">
        {logs.slice(0, 5).map((log) => {
          const actor = userById.get(log.actor_id) ?? `User ${log.actor_id.slice(-6)}`;
          return (
            <li key={log.id} className="flex gap-3">
              <span className="mt-1 size-1.5 shrink-0 rounded-full bg-primary" aria-hidden />
              <div className="min-w-0">
                <p className="text-sm font-medium">
                  {humanize(log.action)} · {log.entity_reference}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {actor} · {log.warehouse_name}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {formatRelative(log.created_at)}
                </p>
              </div>
            </li>
          );
        })}
        {loading ? (
          <li className="text-sm text-muted-foreground">Loading recent activity…</li>
        ) : null}
        {error ? (
          <li className="text-sm text-muted-foreground">Recent activity is unavailable.</li>
        ) : null}
        {!loading && !error && logs.length === 0 ? (
          <li className="text-sm text-muted-foreground">No recent activity yet.</li>
        ) : null}
      </ul>
    </section>
  );
}

function QuickActions({ role }: { role: Role }) {
  const actions = [
    {
      label: "New Receipt",
      to: "/receiving/new",
      icon: PackageOpen,
      roles: ["OWNER", "MANAGER", "RECEIVING_STAFF"],
    },
    {
      label: "New Order",
      to: "/orders/new",
      icon: ShoppingCart,
      roles: ["OWNER", "MANAGER", "FULFILLMENT_STAFF"],
    },
    { label: "Sellers", to: "/sellers", icon: Store, roles: ["OWNER", "MANAGER"] },
    {
      label: "Products",
      to: "/products",
      icon: ClipboardList,
      roles: ["OWNER", "MANAGER", "RECEIVING_STAFF", "FULFILLMENT_STAFF"],
    },
    { label: "Audit Log", to: "/audit", icon: History, roles: ["OWNER", "MANAGER"] },
  ] satisfies { label: string; to: string; icon: typeof PackageOpen; roles: Role[] }[];

  return (
    <section className="surface-card p-5">
      <h2 className="text-base font-semibold">Quick actions</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {actions
          .filter((action) => action.roles.includes(role))
          .map((action) => (
            <Button key={action.to} asChild variant="outline" size="sm" className="rounded-xl">
              <Link to={action.to}>
                <action.icon className="size-4" aria-hidden />
                {action.label}
              </Link>
            </Button>
          ))}
      </div>
    </section>
  );
}
