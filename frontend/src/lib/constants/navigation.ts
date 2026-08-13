import {
  Boxes,
  ClipboardList,
  History,
  LayoutDashboard,
  PackageOpen,
  Settings,
  ShoppingCart,
  Store,
  Truck,
  Users,
  Warehouse,
  type LucideIcon,
} from "lucide-react";
import type { Role } from "@/types";

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  roles: Role[];
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

const ALL: Role[] = ["OWNER", "MANAGER", "RECEIVING_STAFF", "FULFILLMENT_STAFF"];

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "Overview",
    items: [{ label: "Dashboard", to: "/dashboard", icon: LayoutDashboard, roles: ALL }],
  },
  {
    title: "Operations",
    items: [
      { label: "Receiving", to: "/receiving", icon: PackageOpen, roles: ["OWNER", "MANAGER", "RECEIVING_STAFF"] },
      { label: "Inventory", to: "/inventory", icon: Boxes, roles: ALL },
      { label: "Orders", to: "/orders", icon: ShoppingCart, roles: ["OWNER", "MANAGER", "FULFILLMENT_STAFF"] },
      { label: "Fulfillment", to: "/fulfillment", icon: Truck, roles: ["OWNER", "MANAGER", "FULFILLMENT_STAFF"] },
    ],
  },
  {
    title: "Catalog",
    items: [
      { label: "Sellers", to: "/sellers", icon: Store, roles: ["OWNER", "MANAGER"] },
      { label: "Products", to: "/products", icon: ClipboardList, roles: ALL },
    ],
  },
  {
    title: "Management",
    items: [
      { label: "Audit Logs", to: "/audit", icon: History, roles: ["OWNER", "MANAGER"] },
      { label: "Users", to: "/users", icon: Users, roles: ["OWNER"] },
    ],
  },
  {
    title: "System",
    items: [
      { label: "Warehouses", to: "/warehouses", icon: Warehouse, roles: ["OWNER", "MANAGER"] },
      { label: "Settings", to: "/settings", icon: Settings, roles: ALL },
    ],
  },
];

export const ROLE_LABELS: Record<Role, string> = {
  OWNER: "Owner",
  MANAGER: "Manager",
  RECEIVING_STAFF: "Receiving Staff",
  FULFILLMENT_STAFF: "Fulfillment Staff",
};

export function navigationForRole(role: Role): NavSection[] {
  return NAV_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter((item) => item.roles.includes(role)),
  })).filter((section) => section.items.length > 0);
}

/** UX-level route access. The backend remains authoritative. */
export const ROUTE_ROLES: Record<string, Role[]> = Object.fromEntries(
  NAV_SECTIONS.flatMap((s) => s.items.map((i) => [i.to, i.roles])),
);
