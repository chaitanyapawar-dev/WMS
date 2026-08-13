import { Link, useRouterState } from "@tanstack/react-router";
import { Bell, ChevronDown, Menu, Moon, Search, Sun } from "lucide-react";
import { BrandLockup } from "@/components/layout/brand";
import { AssistantDrawer } from "@/features/ai/assistant-drawer";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { NAV_SECTIONS, navigationForRole } from "@/lib/constants/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { initials } from "@/lib/utils/format";
import { useWarehouseScope } from "@/lib/warehouse-scope";

function useBreadcrumb() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const item = NAV_SECTIONS.flatMap((s) => s.items).find(
    (i) => pathname === i.to || pathname.startsWith(`${i.to}/`),
  );
  const isDetail = item ? pathname !== item.to : false;
  return { label: item?.label ?? "Whitfield", to: item?.to, isDetail };
}

export function AppTopbar({ onOpenMobileNav }: { onOpenMobileNav: () => void }) {
  const { user, signOut } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { warehouses, scopeId, setScopeId, canSwitch, scopeLabel } = useWarehouseScope();
  const crumb = useBreadcrumb();

  if (!user) return null;

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-xl lg:px-6">
      <button
        type="button"
        onClick={onOpenMobileNav}
        aria-label="Open navigation"
        className="rounded-lg p-2 hover:bg-accent lg:hidden"
      >
        <Menu className="size-5" aria-hidden />
      </button>
      <div className="lg:hidden">
        <BrandLockup compact />
      </div>

      <nav aria-label="Breadcrumb" className="hidden min-w-0 items-center gap-2 text-sm lg:flex">
        <span className="text-muted-foreground">Whitfield</span>
        <span className="text-muted-foreground/50">/</span>
        <span className="truncate font-medium">{crumb.label}</span>
        {crumb.isDetail && (
          <>
            <span className="text-muted-foreground/50">/</span>
            <span className="text-muted-foreground">Detail</span>
          </>
        )}
      </nav>

      <div className="ml-auto flex items-center gap-2">
        <div className="relative hidden md:block">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            type="search"
            placeholder="Search orders, receipts, SKU…"
            aria-label="Global search"
            className="h-9 w-[260px] rounded-xl pl-9"
          />
        </div>

        <AssistantDrawer />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="h-9 gap-1.5 rounded-xl"
              disabled={!canSwitch && warehouses.length <= 1}
            >
              {scopeLabel}
              <ChevronDown className="size-3.5 opacity-70" aria-hidden />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Warehouse scope</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {user.role === "OWNER" && (
              <DropdownMenuItem onSelect={() => setScopeId("ALL")}>
                All Warehouses
                {scopeId === "ALL" && <span className="ml-auto text-primary">●</span>}
              </DropdownMenuItem>
            )}
            {warehouses.map((w) => (
              <DropdownMenuItem key={w.id} onSelect={() => setScopeId(w.id)}>
                {w.city}, {w.state}
                {scopeId === w.id && <span className="ml-auto text-primary">●</span>}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="ghost"
          size="icon"
          className="size-9 rounded-xl"
          aria-label="Notifications"
        >
          <Bell className="size-[18px]" aria-hidden />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="size-9 rounded-xl"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? <Sun className="size-[18px]" aria-hidden /> : <Moon className="size-[18px]" aria-hidden />}
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger
            aria-label="Account menu"
            className="grid size-9 place-items-center rounded-full border border-border bg-surface-elevated text-xs font-semibold"
          >
            {initials(user.first_name, user.last_name)}
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <span className="block text-sm font-medium">
                {user.first_name} {user.last_name}
              </span>
              <span className="block text-xs text-muted-foreground">{user.email}</span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/settings">Settings</Link>
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={signOut} className="text-destructive focus:text-destructive">
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

export function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user } = useAuth();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  if (!user || !open) return null;

  return (
    <div className="fixed inset-0 z-40 lg:hidden">
      <button type="button" aria-label="Close navigation" className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="absolute inset-y-0 left-0 w-[264px] overflow-y-auto border-r border-sidebar-border bg-sidebar p-4">
        <BrandLockup />
        <nav className="mt-6" aria-label="Mobile">
          {navigationForRole(user.role).map((section) => (
            <div key={section.title} className="mb-5">
              <p className="px-2 pb-2 text-[10.5px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
                {section.title}
              </p>
              {section.items.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm",
                    pathname.startsWith(item.to)
                      ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  <item.icon className="size-[18px]" aria-hidden />
                  {item.label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
      </div>
    </div>
  );
}
