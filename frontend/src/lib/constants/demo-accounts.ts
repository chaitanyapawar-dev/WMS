import { ClipboardList, PackageOpen, ShieldCheck, Truck, type LucideIcon } from "lucide-react";

export interface DemoAccount {
  label: string;
  description: string;
  warehouse: "Reno" | "Columbus" | null;
  email: string;
  password: string;
  icon: LucideIcon;
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    label: "Owner",
    description: "Full system access",
    warehouse: null,
    email: "owner@whitfield.com",
    password: "whitfield",
    icon: ShieldCheck,
  },
  {
    label: "Manager",
    description: "Warehouse operations",
    warehouse: "Reno",
    email: "manager.reno@whitfield.com",
    password: "whitfield",
    icon: ClipboardList,
  },
  {
    label: "Manager",
    description: "Warehouse operations",
    warehouse: "Columbus",
    email: "manager.columbus@whitfield.com",
    password: "whitfield",
    icon: ClipboardList,
  },
  {
    label: "Receiving Staff",
    description: "Inbound receiving",
    warehouse: "Reno",
    email: "receiving.reno@whitfield.com",
    password: "whitfield",
    icon: PackageOpen,
  },
  {
    label: "Receiving Staff",
    description: "Inbound receiving",
    warehouse: "Columbus",
    email: "receiving.columbus@whitfield.com",
    password: "whitfield",
    icon: PackageOpen,
  },
  {
    label: "Fulfillment Staff",
    description: "Outbound operations",
    warehouse: "Reno",
    email: "fulfillment.reno@whitfield.com",
    password: "whitfield",
    icon: Truck,
  },
  {
    label: "Fulfillment Staff",
    description: "Outbound operations",
    warehouse: "Columbus",
    email: "fulfillment.columbus@whitfield.com",
    password: "whitfield",
    icon: Truck,
  },
];
