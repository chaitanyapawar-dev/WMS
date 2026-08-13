import { createFileRoute } from "@tanstack/react-router";
import { AuditPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/audit")({
  head: () => ({
    meta: [
      { title: "Audit log — Whitfield Fulfillment WMS" },
      { name: "description", content: "Every operational action, attributed and timestamped." },
      { property: "og:title", content: "Audit log — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Every operational action, attributed and timestamped." },
    ],
  }),
  component: AuditPage,
});
