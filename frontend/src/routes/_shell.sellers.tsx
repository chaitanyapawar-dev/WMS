import { createFileRoute } from "@tanstack/react-router";
import { SellersPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/sellers")({
  head: () => ({
    meta: [
      { title: "Sellers — Whitfield Fulfillment WMS" },
      { name: "description", content: "Brands storing inventory with Whitfield Fulfillment." },
      { property: "og:title", content: "Sellers — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Brands storing inventory with Whitfield Fulfillment." },
    ],
  }),
  component: SellersPage,
});
