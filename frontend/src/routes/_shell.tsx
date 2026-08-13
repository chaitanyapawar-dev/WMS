import { Outlet, createFileRoute, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { AppTopbar, MobileNav } from "@/components/layout/app-topbar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth/auth-context";
import { ROUTE_ROLES } from "@/lib/constants/navigation";
import { cn } from "@/lib/utils";
import { WarehouseScopeProvider } from "@/lib/warehouse-scope";

export const Route = createFileRoute("/_shell")({
  component: ShellLayout,
});

/** Authenticated shell. Frontend guarding is UX only — the API is authoritative. */
function ShellLayout() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [collapsed, setCollapsed] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) navigate({ to: "/login", replace: true });
  }, [isLoading, isAuthenticated, navigate]);

  useEffect(() => {
    if (!user) return;
    const match = Object.entries(ROUTE_ROLES).find(([to]) => pathname === to || pathname.startsWith(`${to}/`));
    if (match && !match[1].includes(user.role)) navigate({ to: "/dashboard", replace: true });
  }, [pathname, user, navigate]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <div className="w-full max-w-md space-y-3">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    );
  }

  return (
    <WarehouseScopeProvider>
      <div className="min-h-screen bg-background">
        <AppSidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
        <MobileNav open={mobileNav} onClose={() => setMobileNav(false)} />
        <div className={cn("transition-[padding] duration-200", collapsed ? "lg:pl-[76px]" : "lg:pl-[256px]")}>
          <AppTopbar onOpenMobileNav={() => setMobileNav(true)} />
          <main className="mx-auto w-full max-w-[1500px] px-4 py-6 lg:px-8 lg:py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </WarehouseScopeProvider>
  );
}
