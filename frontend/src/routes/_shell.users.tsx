import { createFileRoute } from "@tanstack/react-router";
import { UsersPage } from "@/features/shared/resource-pages";

export const Route = createFileRoute("/_shell/users")({
  head: () => ({
    meta: [
      { title: "Users — Whitfield Fulfillment WMS" },
      { name: "description", content: "Team members, roles and warehouse access." },
      { property: "og:title", content: "Users — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Team members, roles and warehouse access." },
    ],
  }),
  component: UsersPage,
});
