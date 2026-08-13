import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "@tanstack/react-router";
import { Boxes, Eye, EyeOff, Inbox, Loader2, Package, ShoppingCart, UserPlus } from "lucide-react";
import { Fragment, useMemo, useState } from "react";
import { toast } from "sonner";
import { StatusBadge } from "@/components/data-display/status-badge";
import { EmptyState, TableSkeleton } from "@/components/feedback/states";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ReceivingVoiceEntry } from "@/features/receiving/receiving-voice-entry";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { auditApi, inventoryApi, ordersApi, productsApi, receiptsApi, sellersApi, usersApi, warehousesApi } from "@/lib/api";
import { errorMessage } from "@/lib/api/client";
import type { ReceivingVoicePreview } from "@/lib/api/voice";
import { ROLE_LABELS } from "@/lib/constants/navigation";
import { formatDateTime, formatNumber, humanize } from "@/lib/utils/format";
import { useWarehouseScope } from "@/lib/warehouse-scope";
import { useAuth } from "@/lib/auth/auth-context";
import type { Role } from "@/types";

function Surface({ children }: { children: React.ReactNode }) {
  return <div className="surface-card overflow-hidden">{children}</div>;
}

/** Validate receiving quantities before submitting a receipt line. */
function receivingQuantityError(goodValue: string, damagedValue: string): string | null {
  const values = [goodValue.trim(), damagedValue.trim()];
  if (values.some((value) => !/^\d+$/.test(value))) {
    return "Good and damaged quantities must be whole numbers of zero or greater.";
  }
  const total = Number(values[0]) + Number(values[1]);
  return total > 0 ? null : "Enter at least one good or damaged unit.";
}

/* ---------------------------------- Receiving --------------------------------- */

export function ReceivingPage() {
  const { warehouseFilter } = useWarehouseScope();
  const [query, setQuery] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["receipts", { warehouse_id: warehouseFilter }],
    queryFn: () => receiptsApi.list(warehouseFilter ? { warehouse_id: warehouseFilter } : {}),
  });
  const rows = (data ?? []).filter((r) =>
    `${r.reference} ${r.seller_name} ${r.tracking_number ?? ""}`.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Receiving"
        description="Inbound shipments logged against sellers and warehouses."
        actions={
          <Button asChild className="grad-brand rounded-xl text-white">
            <Link to="/receiving/new">New Receipt</Link>
          </Button>
        }
      />
      <Input placeholder="Search receipts…" value={query} onChange={(e) => setQuery(e.target.value)} className="h-10 max-w-sm rounded-xl" />
      <Surface>
        {isLoading ? (
          <TableSkeleton />
        ) : rows.length === 0 ? (
          <EmptyState icon={Inbox} title="No receipts" description="Create a receipt to start logging inbound stock." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Seller</TableHead>
                <TableHead>Warehouse</TableHead>
                <TableHead className="text-right">Units</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">
                    <Link to="/receiving/$receiptId" params={{ receiptId: r.id }} className="hover:underline">
                      {r.reference}
                    </Link>
                  </TableCell>
                  <TableCell>{r.seller_name}</TableCell>
                  <TableCell>{r.warehouse_name}</TableCell>
                  <TableCell className="num text-right">
                    {formatNumber(r.items.reduce((n, i) => n + i.good_quantity + i.damaged_quantity, 0))}
                  </TableCell>
                  <TableCell><StatusBadge status={r.status} /></TableCell>
                  <TableCell className="text-muted-foreground">{formatDateTime(r.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>
    </div>
  );
}

export function NewReceiptPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { warehouses } = useWarehouseScope();
  const sellers = useQuery({ queryKey: ["sellers"], queryFn: () => sellersApi.list() });
  const [form, setForm] = useState({ seller_id: "", warehouse_id: "", tracking_number: "", ticket_number: "" });

  const create = useMutation({
    mutationFn: () =>
      receiptsApi.create({
        seller_id: form.seller_id,
        warehouse_id: form.warehouse_id,
        tracking_number: form.tracking_number,
        ticket_number: form.ticket_number,
      }),
    onSuccess: (receipt) => {
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
      toast.success(`${receipt.reference} created`);
      navigate({ to: "/receiving/$receiptId", params: { receiptId: receipt.id } });
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="New Receipt" description="Log an inbound shipment, then scan items into it." />
      <form
        className="surface-card max-w-2xl space-y-4 p-5"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="seller">Seller</Label>
            <select
              id="seller"
              required
              value={form.seller_id}
              onChange={(e) => setForm({ ...form, seller_id: e.target.value })}
              className="h-11 w-full rounded-xl border border-input bg-transparent px-3 text-sm"
            >
              <option value="">Select seller</option>
              {(sellers.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="warehouse">Warehouse</Label>
            <select
              id="warehouse"
              required
              value={form.warehouse_id}
              onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}
              className="h-11 w-full rounded-xl border border-input bg-transparent px-3 text-sm"
            >
              <option value="">Select warehouse</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tracking">Tracking number</Label>
            <Input id="tracking" value={form.tracking_number} onChange={(e) => setForm({ ...form, tracking_number: e.target.value })} className="h-11 rounded-xl" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ticket">Ticket number</Label>
            <Input id="ticket" value={form.ticket_number} onChange={(e) => setForm({ ...form, ticket_number: e.target.value })} className="h-11 rounded-xl" />
          </div>
        </div>
        <div className="flex gap-2">
          <Button type="submit" disabled={create.isPending} className="grad-brand rounded-xl text-white">Create receipt</Button>
          <Button type="button" variant="ghost" className="rounded-xl" onClick={() => navigate({ to: "/receiving" })}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}

export function ReceiptDetailPage() {
  const { receiptId } = useParams({ from: "/_shell/receiving/$receiptId" });
  const queryClient = useQueryClient();
  const [scan, setScan] = useState({ upc: "", good_quantity: "1", damaged_quantity: "0" });
  const [voicePreview, setVoicePreview] = useState<ReceivingVoicePreview | null>(null);

  const { data: receipt, isLoading } = useQuery({ queryKey: ["receipt", receiptId], queryFn: () => receiptsApi.get(receiptId) });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["receipt", receiptId] });
    queryClient.invalidateQueries({ queryKey: ["receipts"] });
    queryClient.invalidateQueries({ queryKey: ["inventory"] });
    queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
  };

  const addItem = useMutation({
    mutationFn: (payload: { product_id: string; good_quantity: number; damaged_quantity: number }) =>
      receiptsApi.addItem(receiptId, {
        product_id: payload.product_id,
        good_quantity: payload.good_quantity,
        damaged_quantity: payload.damaged_quantity,
      }),
    onSuccess: () => {
      toast.success("Item scanned in");
      setScan({ upc: "", good_quantity: "1", damaged_quantity: "0" });
      setVoicePreview(null);
      invalidate();
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const submitItem = () => {
    const quantityError = receivingQuantityError(scan.good_quantity, scan.damaged_quantity);
    if (!scan.upc.trim()) {
      toast.error("Enter a registered product UPC before adding an item.");
      return;
    }
    if (quantityError) {
      toast.error(quantityError);
      return;
    }
    addItem.mutate({
      product_id: scan.upc.trim(),
      good_quantity: Number(scan.good_quantity) || 0,
      damaged_quantity: Number(scan.damaged_quantity) || 0,
    });
  };

  const confirmVoicePreview = () => {
    if (!voicePreview || voicePreview.intent.good_qty === null || voicePreview.intent.damaged_qty === null) return;
    addItem.mutate({
      product_id: voicePreview.context.upc,
      good_quantity: voicePreview.intent.good_qty,
      damaged_quantity: voicePreview.intent.damaged_qty,
    });
  };

  const complete = useMutation({
    mutationFn: () => receiptsApi.complete(receiptId),
    onSuccess: () => {
      toast.success("Receipt completed — inventory updated");
      invalidate();
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  if (isLoading || !receipt) return <TableSkeleton />;
  const open = receipt.status === "DRAFT" || receipt.status === "IN_PROGRESS";

  return (
    <div className="space-y-6">
      <PageHeader
        title={receipt.reference}
        description={`${receipt.seller_name} · ${receipt.warehouse_name}`}
        actions={
          open ? (
            <Button onClick={() => complete.mutate()} disabled={complete.isPending || receipt.items.length === 0} className="grad-brand rounded-xl text-white">
              Complete receipt
            </Button>
          ) : (
            <StatusBadge status={receipt.status} />
          )
        }
      />

      {open && (
        <form
          className="surface-card grid gap-4 p-5 sm:grid-cols-[1fr_130px_130px_auto] sm:items-end"
          onSubmit={(e) => {
            e.preventDefault();
            submitItem();
          }}
        >
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <Label htmlFor="upc">Scan UPC</Label>
              <Link to="/products" className="text-xs text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">
                Need a test UPC? View Products
              </Link>
            </div>
            <Input id="upc" autoFocus required value={scan.upc} onChange={(e) => setScan({ ...scan, upc: e.target.value })} placeholder="Scan or type UPC" className="num h-11 rounded-xl" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="good">Good</Label>
            <Input id="good" type="number" min="0" step="1" value={scan.good_quantity} onChange={(e) => setScan({ ...scan, good_quantity: e.target.value })} className="num h-11 rounded-xl" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="damaged">Damaged</Label>
            <Input id="damaged" type="number" min="0" step="1" value={scan.damaged_quantity} onChange={(e) => setScan({ ...scan, damaged_quantity: e.target.value })} className="num h-11 rounded-xl" />
          </div>
          <Button type="submit" disabled={addItem.isPending} className="h-11 rounded-xl">Add item</Button>
          <div className="sm:col-span-4 flex flex-wrap items-center gap-3 border-t border-border/70 pt-3">
            <ReceivingVoiceEntry receiptId={receiptId} upc={scan.upc} onPreview={setVoicePreview} />
            <span className="text-xs text-muted-foreground">Speak short quantities, then review before confirming.</span>
          </div>
          {voicePreview && (
            <div className="sm:col-span-4 grid gap-3 border-t border-border/70 pt-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">Voice transcript</p>
                  <p className="mt-1 text-xs text-muted-foreground">{voicePreview.context.product_name} · UPC {voicePreview.context.upc}</p>
                </div>
                <p className="max-w-md text-sm text-muted-foreground">I heard: “{voicePreview.transcript}”</p>
              </div>
              {voicePreview.requires_confirmation ? (
                <>
                  <div className="flex flex-wrap gap-3 text-sm">
                    <span className="rounded-md bg-emerald-500/10 px-3 py-1.5 text-emerald-700 dark:text-emerald-300">Good: {voicePreview.intent.good_qty}</span>
                    <span className="rounded-md bg-amber-500/10 px-3 py-1.5 text-amber-700 dark:text-amber-300">Damaged: {voicePreview.intent.damaged_qty}</span>
                  </div>
                  <div className="flex gap-2">
                    <Button type="button" variant="ghost" onClick={() => setVoicePreview(null)} className="rounded-lg">Cancel</Button>
                    <Button type="button" onClick={confirmVoicePreview} disabled={addItem.isPending} className="rounded-lg">Confirm item</Button>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {voicePreview.message || "Enter the quantities manually, then add the item."}
                </p>
              )}
            </div>
          )}
        </form>
      )}

      <Surface>
        {receipt.items.length === 0 ? (
          <EmptyState icon={Package} title="No items yet" description="Scan a UPC to add the first item to this receipt." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead>UPC</TableHead>
                <TableHead className="text-right">Good</TableHead>
                <TableHead className="text-right">Damaged</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {receipt.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.product_name}</TableCell>
                  <TableCell className="num text-muted-foreground">{item.sku}</TableCell>
                  <TableCell className="num text-muted-foreground">{item.upc}</TableCell>
                  <TableCell className="num text-right">{item.good_quantity}</TableCell>
                  <TableCell className="num text-right">{item.damaged_quantity}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>
    </div>
  );
}

/* ---------------------------------- Inventory --------------------------------- */

export function InventoryPage() {
  const { hasRole } = useAuth();
  const { warehouseFilter } = useWarehouseScope();
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [adjusting, setAdjusting] = useState<string | null>(null);
  const [adjust, setAdjust] = useState({ quantity: "0", reason: "" });
  const canAdjustInventory = hasRole(["OWNER", "MANAGER"]);

  const { data, isLoading } = useQuery({
    queryKey: ["inventory", { warehouse_id: warehouseFilter }],
    queryFn: () => inventoryApi.list(warehouseFilter ? { warehouse_id: warehouseFilter } : {}),
  });

  const rows = useMemo(
    () => (data ?? []).filter((i) => `${i.product_name} ${i.sku} ${i.upc} ${i.seller_name}`.toLowerCase().includes(query.toLowerCase())),
    [data, query],
  );

  const submitAdjust = useMutation({
    mutationFn: (inventoryId: string) =>
      inventoryApi.adjust(inventoryId, { delta: Number(adjust.quantity), reason: adjust.reason }),
    onSuccess: () => {
      toast.success("Inventory adjusted");
      setAdjusting(null);
      setAdjust({ quantity: "0", reason: "" });
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Inventory" description="Stock positions by product, seller and warehouse." />
      <Input placeholder="Search by product, SKU or UPC…" value={query} onChange={(e) => setQuery(e.target.value)} className="h-10 max-w-sm rounded-xl" />
      <Surface>
        {isLoading ? (
          <TableSkeleton />
        ) : rows.length === 0 ? (
          <EmptyState icon={Boxes} title="No inventory" description="Complete a receipt to bring stock into the warehouse." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Seller</TableHead>
                <TableHead>Warehouse</TableHead>
                <TableHead className="text-right">On hand</TableHead>
                <TableHead className="text-right">Reserved</TableHead>
                <TableHead className="text-right">Available</TableHead>
                <TableHead className="text-right">Damaged</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((i) => (
                <Fragment key={i.id}>
                  <TableRow>
                    <TableCell>
                      <p className="font-medium">{i.product_name}</p>
                      <p className="num text-xs text-muted-foreground">{i.sku}</p>
                    </TableCell>
                    <TableCell>{i.seller_name}</TableCell>
                    <TableCell>{i.warehouse_name}</TableCell>
                    <TableCell className="num text-right">{formatNumber(i.on_hand)}</TableCell>
                    <TableCell className="num text-right text-warning">{formatNumber(i.reserved)}</TableCell>
                    <TableCell className="num text-right text-success">{formatNumber(i.available)}</TableCell>
                    <TableCell className="num text-right text-destructive">{formatNumber(i.damaged)}</TableCell>
                    <TableCell className="text-right">
                      {canAdjustInventory ? (
                        <Button variant="outline" size="sm" className="rounded-lg" onClick={() => setAdjusting(adjusting === i.id ? null : i.id)}>
                          Adjust
                        </Button>
                      ) : null}
                    </TableCell>
                  </TableRow>
                  {canAdjustInventory && adjusting === i.id && (
                    <TableRow>
                      <TableCell colSpan={8}>
                        <form
                          className="flex flex-wrap items-end gap-3 py-1"
                          onSubmit={(e) => {
                            e.preventDefault();
                            submitAdjust.mutate(i.id);
                          }}
                        >
                          <div className="space-y-1.5">
                            <Label htmlFor={`qty-${i.id}`}>Quantity (+/-)</Label>
                            <Input id={`qty-${i.id}`} type="number" value={adjust.quantity} onChange={(e) => setAdjust({ ...adjust, quantity: e.target.value })} className="num h-10 w-32 rounded-xl" />
                          </div>
                          <div className="min-w-[240px] flex-1 space-y-1.5">
                            <Label htmlFor={`reason-${i.id}`}>Reason</Label>
                            <Input id={`reason-${i.id}`} required value={adjust.reason} onChange={(e) => setAdjust({ ...adjust, reason: e.target.value })} placeholder="Cycle count correction" className="h-10 rounded-xl" />
                          </div>
                          <Button type="submit" size="sm" className="h-10 rounded-xl" disabled={submitAdjust.isPending}>Save adjustment</Button>
                        </form>
                      </TableCell>
                    </TableRow>
                  )}
                </Fragment>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>
    </div>
  );
}

/* ----------------------------------- Orders ----------------------------------- */

type OrderAction = "reserve" | "start-picking" | "picked" | "packed" | "ship" | "cancel";

const ORDER_ACTIONS: Record<string, { action: OrderAction; label: string }[]> = {
  NEW: [{ action: "reserve", label: "Reserve stock" }, { action: "cancel", label: "Cancel" }],
  RESERVED: [{ action: "start-picking", label: "Start picking" }, { action: "cancel", label: "Cancel" }],
  PICKING: [{ action: "picked", label: "Complete picking" }],
  PICKED: [{ action: "packed", label: "Pack order" }],
};

export function OrdersPage({ fulfillmentMode = false }: { fulfillmentMode?: boolean }) {
  const { warehouseFilter } = useWarehouseScope();
  const [query, setQuery] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["orders", { warehouse_id: warehouseFilter }],
    queryFn: () => ordersApi.list(warehouseFilter ? { warehouse_id: warehouseFilter } : {}),
  });

  const rows = (data ?? [])
    .filter((o) => (fulfillmentMode ? !["NEW", "SHIPPED", "CANCELLED"].includes(o.status) : true))
    .filter((o) => `${o.reference} ${o.seller_name}`.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="space-y-6">
      <PageHeader
        title={fulfillmentMode ? "Fulfillment Queue" : "Orders"}
        description={fulfillmentMode ? "Reserved through ready-to-ship work in your warehouses." : "Outbound orders and their fulfillment state."}
        actions={
          fulfillmentMode ? undefined : (
            <Button asChild className="grad-brand rounded-xl text-white">
              <Link to="/orders/new">New Order</Link>
            </Button>
          )
        }
      />
      <Input placeholder="Search orders…" value={query} onChange={(e) => setQuery(e.target.value)} className="h-10 max-w-sm rounded-xl" />
      <Surface>
        {isLoading ? (
          <TableSkeleton />
        ) : rows.length === 0 ? (
          <EmptyState icon={ShoppingCart} title="No orders" description={fulfillmentMode ? "Nothing in the queue right now." : "Create an order to reserve stock."} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Seller</TableHead>
                <TableHead>Warehouse</TableHead>
                <TableHead className="text-right">Units</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((o) => (
                <TableRow key={o.id}>
                  <TableCell className="font-medium">
                    <Link to="/orders/$orderId" params={{ orderId: o.id }} className="hover:underline">{o.reference}</Link>
                  </TableCell>
                  <TableCell>{o.seller_name}</TableCell>
                  <TableCell>{o.warehouse_name}</TableCell>
                  <TableCell className="num text-right">{formatNumber(o.items.reduce((n, i) => n + i.ordered_quantity, 0))}</TableCell>
                  <TableCell><StatusBadge status={o.status} /></TableCell>
                  <TableCell className="text-muted-foreground">{formatDateTime(o.updated_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>
    </div>
  );
}

export function NewOrderPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { warehouses } = useWarehouseScope();
  const sellers = useQuery({ queryKey: ["sellers"], queryFn: () => sellersApi.list() });
  const [form, setForm] = useState({ seller_id: "", warehouse_id: "" });
  const products = useQuery({
    queryKey: ["products", form.seller_id],
    queryFn: () => productsApi.list({ seller_id: form.seller_id }),
    enabled: Boolean(form.seller_id),
  });
  const [lines, setLines] = useState<{ product_id: string; quantity: string }[]>([{ product_id: "", quantity: "1" }]);

  const create = useMutation({
    mutationFn: () =>
      ordersApi.create({
        seller_id: form.seller_id,
        warehouse_id: form.warehouse_id,
        items: lines.filter((l) => l.product_id).map((l) => ({ product_id: l.product_id, quantity: Number(l.quantity) || 0 })),
      }),
    onSuccess: (order) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
      toast.success(`${order.reference} created`);
      navigate({ to: "/orders/$orderId", params: { orderId: order.id } });
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="New Order" description="Create an outbound order and reserve stock against it." />
      <form
        className="surface-card max-w-3xl space-y-5 p-5"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="order-seller">Seller</Label>
            <select id="order-seller" required value={form.seller_id} onChange={(e) => setForm({ ...form, seller_id: e.target.value })} className="h-11 w-full rounded-xl border border-input bg-transparent px-3 text-sm">
              <option value="">Select seller</option>
              {(sellers.data ?? []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="order-warehouse">Warehouse</Label>
            <select id="order-warehouse" required value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })} className="h-11 w-full rounded-xl border border-input bg-transparent px-3 text-sm">
              <option value="">Select warehouse</option>
              {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </div>
        </div>

        <div className="space-y-3">
          <Label>Line items</Label>
          {lines.map((line, index) => (
            <div key={index} className="flex gap-3">
              <select
                value={line.product_id}
                onChange={(e) => setLines(lines.map((l, i) => (i === index ? { ...l, product_id: e.target.value } : l)))}
                className="h-11 flex-1 rounded-xl border border-input bg-transparent px-3 text-sm"
              >
                <option value="">Select product</option>
                {(products.data ?? []).map((p) => <option key={p.id} value={p.id}>{p.name} · {p.sku}</option>)}
              </select>
              <Input type="number" min="1" value={line.quantity} onChange={(e) => setLines(lines.map((l, i) => (i === index ? { ...l, quantity: e.target.value } : l)))} className="num h-11 w-28 rounded-xl" />
              <Button type="button" variant="ghost" className="h-11 rounded-xl" onClick={() => setLines(lines.filter((_, i) => i !== index))} disabled={lines.length === 1}>
                Remove
              </Button>
            </div>
          ))}
          <Button type="button" variant="outline" size="sm" className="rounded-xl" onClick={() => setLines([...lines, { product_id: "", quantity: "1" }])}>
            Add line
          </Button>
        </div>

        <div className="flex gap-2">
          <Button type="submit" disabled={create.isPending} className="grad-brand rounded-xl text-white">Create order</Button>
          <Button type="button" variant="ghost" className="rounded-xl" onClick={() => navigate({ to: "/orders" })}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}

export function OrderDetailPage() {
  const { orderId } = useParams({ from: "/_shell/orders/$orderId" });
  const queryClient = useQueryClient();
  const [shipment, setShipment] = useState({ carrier: "UPS", tracking_number: "", weight_kg: "1", length_cm: "30", width_cm: "20", height_cm: "15" });

  const { data: order, isLoading } = useQuery({ queryKey: ["order", orderId], queryFn: () => ordersApi.get(orderId) });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["order", orderId] });
    queryClient.invalidateQueries({ queryKey: ["orders"] });
    queryClient.invalidateQueries({ queryKey: ["inventory"] });
    queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
  };

  const transition = useMutation({
    mutationFn: (action: OrderAction) => ordersApi.transition(orderId, action),
    onSuccess: (updated) => {
      toast.success(`Order ${humanize(updated.status).toLowerCase()}`);
      invalidate();
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const createShipment = useMutation({
    mutationFn: () =>
      ordersApi.createShipment(orderId, {
        carrier: shipment.carrier,
        tracking_number: shipment.tracking_number,
        weight_kg: Number(shipment.weight_kg),
        length_cm: Number(shipment.length_cm),
        width_cm: Number(shipment.width_cm),
        height_cm: Number(shipment.height_cm),
      }),
    onSuccess: () => {
      toast.success("Shipment created");
      invalidate();
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  if (isLoading || !order) return <TableSkeleton />;
  const actions = ORDER_ACTIONS[order.status] ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={order.reference}
        description={`${order.seller_name} · ${order.warehouse_name}`}
        actions={
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={order.status} />
            {actions.map((a) => (
              <Button key={a.action} size="sm" variant={a.action === "cancel" ? "outline" : "default"} className="rounded-xl" disabled={transition.isPending} onClick={() => transition.mutate(a.action)}>
                {a.label}
              </Button>
            ))}
            {order.status === "READY_TO_SHIP" && (
              <Button size="sm" className="grad-brand rounded-xl text-white" disabled={transition.isPending} onClick={() => transition.mutate("ship")}>Mark shipped</Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <Surface>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead className="text-right">Ordered</TableHead>
                <TableHead className="text-right">Reserved</TableHead>
                <TableHead className="text-right">Picked</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {order.items.map((item) => (
                <TableRow key={item.product_id}>
                  <TableCell className="font-medium">{item.product_name}</TableCell>
                  <TableCell className="num text-muted-foreground">{item.sku}</TableCell>
                  <TableCell className="num text-right">{item.ordered_quantity}</TableCell>
                  <TableCell className="num text-right">{item.reserved_quantity}</TableCell>
                  <TableCell className="num text-right">{item.picked_quantity}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Surface>

        <div className="space-y-4">
          <section className="surface-card p-5">
            <h2 className="text-base font-semibold">Timeline</h2>
            <ol className="mt-4 space-y-4">
              {order.timeline.map((entry, index) => (
                <li key={`${entry.status}-${index}`} className="flex gap-3">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" aria-hidden />
                  <div>
                    <p className="text-sm font-medium">{humanize(entry.status)}</p>
                    <p className="text-xs text-muted-foreground">{entry.by} · {formatDateTime(entry.at)}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className="surface-card p-5">
            <h2 className="text-base font-semibold">Shipment</h2>
            {order.shipment ? (
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between"><dt className="text-muted-foreground">Carrier</dt><dd>{order.shipment.carrier}</dd></div>
                <div className="flex justify-between"><dt className="text-muted-foreground">Tracking</dt><dd className="num">{order.shipment.tracking_number}</dd></div>
                <div className="flex justify-between"><dt className="text-muted-foreground">Weight</dt><dd className="num">{order.shipment.weight_kg} kg</dd></div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Dimensions</dt>
                  <dd className="num">{order.shipment.length_cm}×{order.shipment.width_cm}×{order.shipment.height_cm} cm</dd>
                </div>
              </dl>
            ) : order.status === "PACKED" ? (
              <form
                className="mt-4 space-y-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  createShipment.mutate();
                }}
              >
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="carrier">Carrier</Label>
                    <Input id="carrier" value={shipment.carrier} onChange={(e) => setShipment({ ...shipment, carrier: e.target.value })} className="h-10 rounded-xl" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="tracking-number">Tracking</Label>
                    <Input id="tracking-number" required value={shipment.tracking_number} onChange={(e) => setShipment({ ...shipment, tracking_number: e.target.value })} className="num h-10 rounded-xl" />
                  </div>
                  {(["weight_kg", "length_cm", "width_cm", "height_cm"] as const).map((field) => (
                    <div key={field} className="space-y-1.5">
                      <Label htmlFor={field}>{humanize(field)}</Label>
                      <Input id={field} type="number" min="0" value={shipment[field]} onChange={(e) => setShipment({ ...shipment, [field]: e.target.value })} className="num h-10 rounded-xl" />
                    </div>
                  ))}
                </div>
                <Button type="submit" disabled={createShipment.isPending} className="w-full rounded-xl">Create shipment</Button>
              </form>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">Available once the order is packed.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------ Sellers / Products ---------------------------- */

export function SellersPage() {
  const { data, isLoading } = useQuery({ queryKey: ["sellers"], queryFn: () => sellersApi.list() });
  return (
    <div className="space-y-6">
      <PageHeader title="Sellers" description="Brands storing inventory with Whitfield." />
      <Surface>
        {isLoading ? <TableSkeleton /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Seller</TableHead><TableHead>Code</TableHead><TableHead>Email</TableHead><TableHead>Phone</TableHead><TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data ?? []).map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell className="num text-muted-foreground">{s.code}</TableCell>
                  <TableCell className="text-muted-foreground">{s.email}</TableCell>
                  <TableCell className="num text-muted-foreground">{s.phone}</TableCell>
                  <TableCell><StatusBadge status={s.status} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>
    </div>
  );
}

export function ProductsPage() {
  const [query, setQuery] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["products", ""], queryFn: () => productsApi.list() });
  const rows = (data ?? []).filter((p) => `${p.name} ${p.sku} ${p.upc} ${p.seller_name}`.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="space-y-6">
      <PageHeader title="Products" description="SKU and UPC catalog across every seller." />
      <Input placeholder="Search catalog…" value={query} onChange={(e) => setQuery(e.target.value)} className="h-10 max-w-sm rounded-xl" />
      <Surface>
        {isLoading ? <TableSkeleton /> : rows.length === 0 ? <EmptyState icon={Package} title="No products" description="No catalog entries match this search." /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead><TableHead>SKU</TableHead><TableHead>UPC</TableHead><TableHead>Seller</TableHead><TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell className="num text-muted-foreground">{p.sku}</TableCell>
                  <TableCell className="num text-muted-foreground">{p.upc}</TableCell>
                  <TableCell>{p.seller_name}</TableCell>
                  <TableCell><StatusBadge status={p.status} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>
    </div>
  );
}

/* --------------------------------- Users / Audit ------------------------------ */

export function UsersPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["users"], queryFn: () => usersApi.list() });
  const warehouses = useQuery({ queryKey: ["warehouses"], queryFn: warehousesApi.list });
  const [open, setOpen] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    role: "RECEIVING_STAFF" as Exclude<Role, "OWNER">,
    warehouse_ids: [] as string[],
  });

  const create = useMutation({
    mutationFn: () => usersApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast.success("User created successfully.");
      setOpen(false);
      setForm({
        first_name: "",
        last_name: "",
        email: "",
        password: "",
        role: "RECEIVING_STAFF",
        warehouse_ids: [],
      });
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  function update(key: keyof typeof form, value: string | string[]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function toggleWarehouse(warehouseId: string, checked: boolean) {
    setForm((prev) => ({
      ...prev,
      warehouse_ids: checked
        ? Array.from(new Set([...prev.warehouse_ids, warehouseId]))
        : prev.warehouse_ids.filter((id) => id !== warehouseId),
    }));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        description="Team members, roles and warehouse access."
        actions={
          <Button className="grad-brand rounded-xl text-white" onClick={() => setOpen(true)}>
            <UserPlus className="size-4" aria-hidden />
            Create User
          </Button>
        }
      />
      <Surface>
        {isLoading ? <TableSkeleton /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead><TableHead>Email</TableHead><TableHead>Role</TableHead><TableHead>Warehouses</TableHead><TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data ?? []).map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.first_name} {u.last_name}</TableCell>
                  <TableCell className="text-muted-foreground">{u.email}</TableCell>
                  <TableCell>{ROLE_LABELS[u.role]}</TableCell>
                  <TableCell className="num text-muted-foreground">{u.warehouse_ids.length || "All"}</TableCell>
                  <TableCell><StatusBadge status={u.status} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create User</DialogTitle>
            <DialogDescription>Provision an employee account with role and warehouse access.</DialogDescription>
          </DialogHeader>
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              create.mutate();
            }}
          >
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="user-first-name">First Name</Label>
                <Input id="user-first-name" required value={form.first_name} onChange={(e) => update("first_name", e.target.value)} className="h-10 rounded-xl" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="user-last-name">Last Name</Label>
                <Input id="user-last-name" required value={form.last_name} onChange={(e) => update("last_name", e.target.value)} className="h-10 rounded-xl" />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="user-email">Email</Label>
              <Input id="user-email" type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} className="h-10 rounded-xl" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="user-password">Temporary Password</Label>
              <div className="relative">
                <Input
                  id="user-password"
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={8}
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  className="h-10 rounded-xl pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute top-1/2 right-2 -translate-y-1/2 rounded-lg p-2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">Minimum 8 characters.</p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="user-role">Role</Label>
              <select
                id="user-role"
                value={form.role}
                onChange={(e) => update("role", e.target.value as Exclude<Role, "OWNER">)}
                className="h-10 w-full rounded-xl border border-input bg-transparent px-3 text-sm"
              >
                <option value="MANAGER">Manager</option>
                <option value="RECEIVING_STAFF">Receiving Staff</option>
                <option value="FULFILLMENT_STAFF">Fulfillment Staff</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label>Warehouse Access</Label>
              <div className="grid gap-2 rounded-xl border border-border/80 p-3">
                {(warehouses.data ?? []).map((warehouse) => (
                  <label key={warehouse.id} className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={form.warehouse_ids.includes(warehouse.id)}
                      onCheckedChange={(checked) => toggleWarehouse(warehouse.id, checked === true)}
                    />
                    <span>{warehouse.name}</span>
                    <span className="text-xs text-muted-foreground">{warehouse.city}, {warehouse.state}</span>
                  </label>
                ))}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="ghost" className="rounded-xl" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={create.isPending} className="grad-brand rounded-xl text-white">
                {create.isPending ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
                Create User
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function AuditPage() {
  const { data, isLoading } = useQuery({ queryKey: ["audit-logs", "all"], queryFn: () => auditApi.list() });
  return (
    <div className="space-y-6">
      <PageHeader title="Audit Log" description="Every operational action, attributed and timestamped." />
      <Surface>
        {isLoading ? <TableSkeleton /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Activity</TableHead><TableHead>Actor</TableHead><TableHead>Context</TableHead><TableHead className="text-right">When</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data ?? []).map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="min-w-[190px]">
                    <p className="font-medium">{humanize(log.action)}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{humanize(log.entity)}</p>
                  </TableCell>
                  <TableCell className="min-w-[150px]">
                    <p className="font-medium">{log.user_name}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{ROLE_LABELS[log.role]}</p>
                  </TableCell>
                  <TableCell className="min-w-[220px]">
                    <p className="num text-sm text-foreground">{log.entity_reference}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{log.warehouse_name}</p>
                  </TableCell>
                  <TableCell className="min-w-[170px] text-right text-sm text-muted-foreground">{formatDateTime(log.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Surface>
    </div>
  );
}
