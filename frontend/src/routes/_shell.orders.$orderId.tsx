import { createFileRoute } from "@tanstack/react-router";
import { OrderDetailPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/orders/$orderId")({
  head: () => ({
    meta: [
      { title: "Order detail — Whitfield Fulfillment WMS" },
      { name: "description", content: "Order lines, fulfillment timeline and shipment details." },
      { property: "og:title", content: "Order detail — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Order lines, fulfillment timeline and shipment details." },
    ],
  }),
  component: OrderDetailPage,
});
