import { createFileRoute } from "@tanstack/react-router";
import { DashboardPage } from "@/features/dashboard/dashboard-page";

export const Route = createFileRoute("/_shell/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Whitfield Fulfillment WMS" },
      { name: "description", content: "Live warehouse operations: stock health, receiving queue, open orders and recent activity across Whitfield." },
      { property: "og:title", content: "Dashboard — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Live stock, receiving and fulfillment status across Whitfield." },
    ],
  }),
  component: DashboardPage,
});
