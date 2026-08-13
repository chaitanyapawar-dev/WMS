import { createFileRoute } from "@tanstack/react-router";
import { ReceivingPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/receiving/")({
  head: () => ({
    meta: [
      { title: "Receiving — Whitfield Fulfillment WMS" },
      { name: "description", content: "Log inbound shipments, scan UPCs and complete receipts into warehouse stock." },
      { property: "og:title", content: "Receiving — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Log inbound shipments, scan UPCs and complete receipts into warehouse stock." },
    ],
  }),
  component: ReceivingPage,
});
