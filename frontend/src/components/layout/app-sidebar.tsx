import { Link, useRouterState } from "@tanstack/react-router";
import { ChevronsLeft, ChevronsRight, LogOut, MoreHorizontal, Settings, User as UserIcon, Warehouse } from "lucide-react";
import { BrandLockup } from "@/components/layout/brand";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth/auth-context";
import { ROLE_LABELS, navigationForRole } from "@/lib/constants/navigation";
import { cn } from "@/lib/utils";
import { initials } from "@/lib/utils/format";
import { useWarehouseScope } from "@/lib/warehouse-scope";

export function AppSidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const { user, signOut } = useAuth();
  const { scopeLabel } = useWarehouseScope();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  if (!user) return null;
  const sections = navigationForRole(user.role);

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200 lg:flex",
        collapsed ? "w-[76px]" : "w-[256px]",
      )}
    >
      <div className={cn("flex h-16 items-center border-b border-sidebar-border px-4", collapsed && "justify-center px-0")}>
        <BrandLockup compact={collapsed} />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Main">
        {sections.map((section) => (
          <div key={section.title} className="mb-5">
            {!collapsed && (
              <p className="px-2 pb-2 text-[10.5px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
                {section.title}
              </p>
            )}
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname === item.to || pathname.startsWith(`${item.to}/`);
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "relative flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors duration-150",
                        active
                          ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                          : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground",
                        collapsed && "justify-center px-0",
                      )}
                    >
                      {active && (
                        <span className="grad-brand absolute top-1.5 bottom-1.5 -left-3 w-[3px] rounded-r-full" aria-hidden />
                      )}
                      <item.icon className="size-[18px] shrink-0" aria-hidden />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        {!collapsed && (
          <div className="mb-2 flex items-center gap-2 rounded-lg bg-sidebar-accent/40 px-2.5 py-2 text-xs text-muted-foreground">
            <Warehouse className="size-3.5" aria-hidden />
            <span className="truncate">{scopeLabel}</span>
          </div>
        )}
        <DropdownMenu>
          <DropdownMenuTrigger
            className={cn(
              "flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left transition-colors hover:bg-sidebar-accent/60",
              collapsed && "justify-center px-0",
            )}
          >
            <span className="grid size-8 shrink-0 place-items-center rounded-full border border-border bg-surface-elevated text-xs font-semibold">
              {initials(user.first_name, user.last_name)}
            </span>
            {!collapsed && (
              <>
                <span className="min-w-0 flex-1 leading-tight">
                  <span className="block truncate text-[13px] font-medium">
                    {user.first_name} {user.last_name}
                  </span>
                  <span className="block text-[11px] tracking-wide text-muted-foreground uppercase">
                    {ROLE_LABELS[user.role]}
                  </span>
                </span>
                <MoreHorizontal className="size-4 text-muted-foreground" aria-hidden />
              </>
            )}
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-52">
            <DropdownMenuItem asChild>
              <Link to="/settings">
                <UserIcon className="size-4" aria-hidden /> Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/settings">
                <Settings className="size-4" aria-hidden /> Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={signOut} className="text-destructive focus:text-destructive">
              <LogOut className="size-4" aria-hidden /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <button
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-sidebar-border px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-sidebar-accent/60 hover:text-foreground"
        >
          {collapsed ? <ChevronsRight className="size-4" aria-hidden /> : <ChevronsLeft className="size-4" aria-hidden />}
          {!collapsed && "Collapse"}
        </button>
      </div>
    </aside>
  );
}
