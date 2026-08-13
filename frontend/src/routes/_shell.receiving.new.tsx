import { createFileRoute } from "@tanstack/react-router";
import { NewReceiptPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/receiving/new")({
  head: () => ({
    meta: [
      { title: "New receipt — Whitfield Fulfillment WMS" },
      { name: "description", content: "Create an inbound receipt against a seller and warehouse." },
      { property: "og:title", content: "New receipt — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Create an inbound receipt against a seller and warehouse." },
    ],
  }),
  component: NewReceiptPage,
});
