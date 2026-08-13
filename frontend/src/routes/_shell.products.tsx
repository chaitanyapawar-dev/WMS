import { createFileRoute } from "@tanstack/react-router";
import { ProductsPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/products")({
  head: () => ({
    meta: [
      { title: "Products — Whitfield Fulfillment WMS" },
      { name: "description", content: "SKU and UPC catalog across every Whitfield seller." },
      { property: "og:title", content: "Products — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "SKU and UPC catalog across every Whitfield seller." },
    ],
  }),
  component: ProductsPage,
});
