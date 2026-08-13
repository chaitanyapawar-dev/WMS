import { createFileRoute } from "@tanstack/react-router";
import { InventoryPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/inventory")({
  head: () => ({
    meta: [
      { title: "Inventory — Whitfield Fulfillment WMS" },
      { name: "description", content: "Stock positions by product, seller and warehouse with adjustments." },
      { property: "og:title", content: "Inventory — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Stock positions by product, seller and warehouse with adjustments." },
    ],
  }),
  component: InventoryPage,
});
