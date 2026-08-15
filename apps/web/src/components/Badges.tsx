import { cn } from "@/lib/utils";

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    CREATED: "bg-text-secondary/10 text-text-secondary border-text-secondary/20",
    FAILED: "bg-status-red/10 text-status-red border-status-red/20",
    RESOLVED: "bg-status-green/10 text-status-green border-status-green/20",
    active: "bg-brand/10 text-brand border-brand/20",
  };

  return (
    <span className={cn("px-2 py-1 text-xs font-medium uppercase tracking-wider rounded border", colors[status] || colors.active)}>
      {status}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    SEV_1: "bg-status-red text-background",
    SEV_2: "bg-status-amber text-background",
    SEV_3: "bg-status-blue text-background",
    SEV_4: "bg-surface-elevated text-text-primary border border-surface",
  };

  return (
    <span className={cn("px-2 py-1 text-xs font-bold rounded", colors[severity] || colors.SEV_4)}>
      {severity}
    </span>
  );
}

export function VerificationBadge({ result }: { result: 'VERIFIED' | 'REJECTED' | 'INCONCLUSIVE' }) {
  const colors = {
    VERIFIED: "bg-status-green text-background",
    REJECTED: "bg-status-red text-background",
    INCONCLUSIVE: "bg-status-amber text-background",
  };

  return (
    <div className={cn("px-3 py-1.5 text-sm font-bold uppercase tracking-widest rounded inline-flex items-center", colors[result])}>
      {result}
    </div>
  );
}
