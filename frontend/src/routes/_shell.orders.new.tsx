import { createFileRoute } from "@tanstack/react-router";
import { NewOrderPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/orders/new")({
  head: () => ({
    meta: [
      { title: "New order — Whitfield Fulfillment WMS" },
      { name: "description", content: "Create an outbound order and reserve stock against it." },
      { property: "og:title", content: "New order — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Create an outbound order and reserve stock against it." },
    ],
  }),
  component: NewOrderPage,
});
