import { Link } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatNumber } from "@/lib/utils/format";

export interface KpiCardProps {
  label: string;
  value: number | null | undefined;
  icon: LucideIcon;
  hint?: string;
  tone?: "brand" | "success" | "warning" | "danger" | "info";
  loading?: boolean;
  to?: string;
  search?: Record<string, string>;
  featured?: boolean;
}

const TONE_ICON: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  brand: "bg-primary/12 text-primary",
  success: "bg-success/12 text-success",
  warning: "bg-warning/12 text-warning",
  danger: "bg-destructive/12 text-destructive",
  info: "bg-info/12 text-info",
};

export function KpiCard({
  label,
  value,
  icon: Icon,
  hint,
  tone = "brand",
  loading,
  to,
  search,
  featured,
}: KpiCardProps) {
  const content = (
    <div
      className={cn(
        "surface-card group relative overflow-hidden p-4 transition-all duration-200",
        to && "hover:border-border-strong hover:-translate-y-0.5",
        featured && "glow-hero",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-[13px] font-medium text-muted-foreground">{label}</p>
        <span className={cn("grid size-8 place-items-center rounded-lg", TONE_ICON[tone])}>
          <Icon className="size-4" aria-hidden />
        </span>
      </div>
      {loading ? (
        <Skeleton className="mt-3 h-8 w-24" />
      ) : (
        <p className="num mt-2 text-[30px] leading-none font-semibold tracking-tight">
          {formatNumber(value)}
        </p>
      )}
      <p className="mt-2 text-xs text-muted-foreground">{loading ? <Skeleton className="h-3 w-28" /> : hint}</p>
    </div>
  );

  if (!to) return content;
  return (
    <Link to={to} search={search ?? {}} className="block rounded-2xl focus-visible:outline-none">
      {content}
    </Link>
  );
}
