import { Warehouse } from "lucide-react";
import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "grad-brand grid size-9 shrink-0 place-items-center rounded-[11px] text-sm font-bold text-white shadow-[0_4px_14px_-4px_rgba(79,70,229,0.7)]",
        className,
      )}
      aria-hidden
    >
      <Warehouse className="size-[19px]" strokeWidth={2.25} />
    </span>
  );
}

export function BrandLockup({ compact }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <BrandMark />
      {!compact && (
        <span className="leading-tight">
          <span className="block text-sm font-semibold tracking-tight">Whitfield</span>
          <span className="block text-[11px] tracking-wide text-muted-foreground uppercase">Fulfillment</span>
        </span>
      )}
    </div>
  );
}
