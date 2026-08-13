import { createFileRoute } from "@tanstack/react-router";
import { Moon, Sun } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/auth-context";
import { ROLE_LABELS } from "@/lib/constants/navigation";
import { useTheme } from "@/lib/theme";
import { LIVE_API } from "@/lib/api/client";

export const Route = createFileRoute("/_shell/settings")({
  head: () => ({
    meta: [
      { title: "Settings — Whitfield Fulfillment WMS" },
      { name: "description", content: "Manage your Whitfield workspace profile, appearance and connection settings." },
      { property: "og:title", content: "Settings — Whitfield Fulfillment WMS" },
      { property: "og:description", content: "Manage your Whitfield workspace profile and appearance." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  if (!user) return null;

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Workspace preferences and account information." />

      <section className="surface-card p-5">
        <h2 className="text-lg font-semibold">Profile</h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Name", `${user.first_name} ${user.last_name}`],
            ["Email", user.email],
            ["Role", ROLE_LABELS[user.role]],
            ["Status", user.status],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs text-muted-foreground">{label}</dt>
              <dd className="mt-1 text-sm font-medium">{value}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-xs text-muted-foreground">
          Role and warehouse access are assigned by an owner through the backend.
        </p>
      </section>

      <section className="surface-card flex flex-wrap items-center justify-between gap-4 p-5">
        <div>
          <h2 className="text-lg font-semibold">Appearance</h2>
          <p className="mt-1 text-sm text-muted-foreground">Whitfield ships a dark operations theme and a light theme.</p>
        </div>
        <Button variant="outline" onClick={toggleTheme} className="gap-2">
          {theme === "dark" ? <Sun className="size-4" aria-hidden /> : <Moon className="size-4" aria-hidden />}
          Switch to {theme === "dark" ? "light" : "dark"} mode
        </Button>
      </section>

      <section className="surface-card p-5">
        <h2 className="text-lg font-semibold">API connection</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {LIVE_API
            ? "Live Backend Connected"
            : "VITE_API_BASE_URL is not configured. Requests use same-origin /v1 and surface backend errors."}
        </p>
      </section>
    </div>
  );
}
