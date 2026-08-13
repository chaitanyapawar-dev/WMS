import { ClipboardList, PackageOpen, ShieldCheck, Truck, type LucideIcon } from "lucide-react";

export interface DemoAccount {
  label: string;
  description: string;
  email: string;
  password: string;
  icon: LucideIcon;
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    label: "Owner",
    description: "Full system access",
    email: "owner@whitfield.com",
    password: "whitfield",
    icon: ShieldCheck,
  },
  {
    label: "Manager",
    description: "Warehouse operations",
    email: "manager@whitfield.com",
    password: "whitfield",
    icon: ClipboardList,
  },
  {
    label: "Receiving Staff",
    description: "Inbound receiving",
    email: "receiving@whitfield.com",
    password: "whitfield",
    icon: PackageOpen,
  },
  {
    label: "Fulfillment Staff",
    description: "Outbound operations",
    email: "fulfillment@whitfield.com",
    password: "whitfield",
    icon: Truck,
  },
];
