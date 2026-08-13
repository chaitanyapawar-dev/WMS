import { createFileRoute } from "@tanstack/react-router";
import { ReceiptDetailPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/receiving/$receiptId")({
  head: () => ({
    meta: [
      { title: "Receipt detail — Whitfield Fulfillment WMS" },
      { name: "description", content: "Scan items into an open receipt and complete it into inventory." },
      { property: "og:title", content: "Receipt detail — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Scan items into an open receipt and complete it into inventory." },
    ],
  }),
  component: ReceiptDetailPage,
});
