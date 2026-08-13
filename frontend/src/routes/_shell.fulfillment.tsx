import { createFileRoute } from "@tanstack/react-router";
import { OrdersPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/fulfillment")({
  head: () => ({
    meta: [
      { title: "Fulfillment — Whitfield Fulfillment WMS" },
      { name: "description", content: "Pick, pack and ship queue for reserved orders across Whitfield warehouses." },
      { property: "og:title", content: "Fulfillment — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Pick, pack and ship queue for reserved orders." },
    ],
  }),
  component: () => <OrdersPage fulfillmentMode />,
});
