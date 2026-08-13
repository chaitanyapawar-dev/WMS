import { cn } from "@/lib/utils";
import { humanize } from "@/lib/utils/format";

type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "brand";

const TONES: Record<Tone, string> = {
  neutral: "bg-muted text-muted-foreground border-border",
  success: "bg-success/12 text-success border-success/25",
  warning: "bg-warning/12 text-warning border-warning/25",
  danger: "bg-destructive/12 text-destructive border-destructive/25",
  info: "bg-info/12 text-info border-info/25",
  brand: "bg-primary/12 text-primary border-primary/25",
};

const STATUS_TONES: Record<string, Tone> = {
  DRAFT: "neutral",
  IN_PROGRESS: "info",
  COMPLETED: "success",
  CANCELLED: "danger",
  NEW: "neutral",
  RESERVED: "warning",
  PICKING: "info",
  PICKED: "info",
  PACKED: "brand",
  READY_TO_SHIP: "brand",
  SHIPPED: "success",
  ACTIVE: "success",
  INACTIVE: "neutral",
  Healthy: "success",
  "Low stock": "warning",
  "No available stock": "danger",
  "Reserved heavy": "info",
  "Damaged stock": "danger",
};

export function StatusBadge({
  status,
  tone,
  className,
}: {
  status: string;
  tone?: Tone;
  className?: string;
}) {
  const resolved = tone ?? STATUS_TONES[status] ?? "neutral";
  const label = status === status.toUpperCase() ? humanize(status) : status;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        TONES[resolved],
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current opacity-70" aria-hidden />
      {label}
    </span>
  );
}
