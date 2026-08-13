import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { BrandMark } from "@/components/layout/brand";
import { useAuth } from "@/lib/auth/auth-context";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Whitfield Fulfillment — Warehouse Management System" },
      { name: "description", content: "Whitfield Fulfillment WMS: receive, reserve, fulfill, ship and audit inventory across the Reno and Columbus warehouses." },
      { property: "og:title", content: "Whitfield Fulfillment — Warehouse Management System" },
      { property: "og:description", content: "Operations, without the spreadsheet chaos." },
    ],
  }),
  component: Index,
});

function Index() {
  const { isLoading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isLoading) return;
    navigate({ to: isAuthenticated ? "/dashboard" : "/login", replace: true });
  }, [isLoading, isAuthenticated, navigate]);

  return (
    <div className="atmosphere grid min-h-screen place-items-center">
      <div className="grain-overlay" aria-hidden />
      <div className="relative flex items-center gap-3 text-white">
        <BrandMark />
        <span className="text-sm font-medium">Loading Whitfield WMS…</span>
      </div>
    </div>
  );
}
