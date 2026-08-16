import React from "react";
import { AlertTriangle, CheckCircle, ChevronRight, XCircle, Info, ShieldCheck, Search, Database, Activity, GitBranch, Beaker, FileSearch, Network, Server, Play } from "lucide-react";

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-surface-elevated bg-surface/50 backdrop-blur-sm ${className}`}>
      {children}
    </div>
  );
}

export function SectionHeader({ title, icon: Icon, description }: { title: string; icon?: React.ElementType; description?: string }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.2em] text-text-secondary">
        {Icon && <Icon className="h-4 w-4 text-brand" />}
        {title}
      </div>
      {description && <p className="mt-1 text-sm text-text-secondary">{description}</p>}
    </div>
  );
}

export function DisplayValue({ label, value, delta, previous, isPositive = false }: { label: string; value: string | React.ReactNode; delta?: string; previous?: string; isPositive?: boolean }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-text-secondary mb-1">{label}</span>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-xl font-semibold text-text-primary">{value}</span>
        {delta && (
          <span className={`font-mono text-xs ${isPositive ? 'text-status-green' : 'text-status-amber'}`}>
            {delta}
          </span>
        )}
      </div>
      {previous && <span className="font-mono text-[10px] text-text-secondary mt-1">prev: {previous}</span>}
    </div>
  );
}

export function DiffBlock({ diff }: { diff: string }) {
  return (
    <pre className="overflow-x-auto rounded-lg border border-surface-elevated bg-background p-4 font-mono text-xs leading-relaxed">
      <code>
        {diff.split("\n").map((line, i) => {
          let color = "text-text-secondary";
          let bg = "bg-transparent";
          if (line.startsWith("+")) {
            color = "text-status-green";
            bg = "bg-status-green/10";
          } else if (line.startsWith("-")) {
            color = "text-status-red";
            bg = "bg-status-red/10";
          } else if (line.startsWith("@@")) {
            color = "text-brand opacity-80";
          }
          return (
            <div key={i} className={`px-2 ${bg} ${color}`}>
              {line}
            </div>
          );
        })}
      </code>
    </pre>
  );
}

export function StatusIndicator({ status, label }: { status: "pass" | "fail" | "pending"; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded bg-background/50 px-3 py-1.5 border border-surface-elevated">
      {status === "pass" && <CheckCircle className="h-4 w-4 text-status-green" />}
      {status === "fail" && <XCircle className="h-4 w-4 text-status-red" />}
      {status === "pending" && <div className="h-4 w-4 rounded-full border-2 border-brand border-t-transparent animate-spin" />}
      <span className="text-xs font-medium text-text-primary">{label}</span>
    </div>
  );
}
