import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("grain relative overflow-hidden rounded-xl px-6 py-14 text-center", className)}>
      <div className="glow-hero pointer-events-none absolute inset-0 opacity-60" aria-hidden />
      <div className="grain-overlay opacity-[0.08]" aria-hidden />
      <div className="relative">
        <span className="mx-auto grid size-12 place-items-center rounded-2xl border border-border bg-surface-elevated text-primary">
          <Icon className="size-5" aria-hidden />
        </span>
        <h3 className="mt-4 text-base font-semibold">{title}</h3>
        <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>
        {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 6, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="divide-y divide-border">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex items-center gap-4 px-4 py-3.5">
          {Array.from({ length: cols }).map((__, colIndex) => (
            <Skeleton key={colIndex} className={cn("h-4 flex-1", colIndex === 0 && "max-w-[220px]")} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-8 text-center">
      <p className="text-sm font-medium text-destructive">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-accent"
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}
