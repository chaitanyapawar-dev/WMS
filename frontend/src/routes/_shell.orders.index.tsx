import { createFileRoute } from "@tanstack/react-router";
import { OrdersPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/orders/")({
  head: () => ({
    meta: [
      { title: "Orders — Whitfield Fulfillment WMS" },
      { name: "description", content: "Outbound orders from reservation through shipment." },
      { property: "og:title", content: "Orders — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Outbound orders from reservation through shipment." },
    ],
  }),
  component: OrdersPage,
});
