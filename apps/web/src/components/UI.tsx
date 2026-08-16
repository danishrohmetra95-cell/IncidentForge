import React from "react";
import { AlertTriangle, CheckCircle, ChevronRight, XCircle, Info, ShieldCheck, Search, Database, Activity, GitBranch, Beaker, FileSearch, Network, Server, Play } from "lucide-react";

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg border border-surface-elevated bg-surface/50 ${className}`}>
      {children}
    </div>
  );
}

export function SectionHeader({ title, icon: Icon, description }: { title: string; icon?: React.ElementType; description?: string }) {
  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-text-secondary">
        {Icon && <Icon className="h-3.5 w-3.5 text-text-primary" />}
        {title}
      </div>
      {description && <p className="mt-1 text-[13px] text-text-secondary leading-relaxed">{description}</p>}
    </div>
  );
}

export function DisplayValue({ label, value, delta, previous, isPositive = false }: { label: string; value: string | React.ReactNode; delta?: string; previous?: string; isPositive?: boolean }) {
  return (
    <div className="flex flex-col">
      <span className="text-[11px] font-mono uppercase tracking-wider text-text-secondary mb-1">{label}</span>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-lg font-semibold text-text-primary">{value}</span>
        {delta && (
          <span className={`font-mono text-[11px] ${isPositive ? 'text-status-green' : 'text-status-amber'}`}>
            {delta}
          </span>
        )}
      </div>
      {previous && <span className="font-mono text-[10px] text-text-secondary mt-0.5">prev: {previous}</span>}
    </div>
  );
}

export function DiffBlock({ diff }: { diff: string }) {
  return (
    <pre className="overflow-x-auto rounded-md border border-surface-elevated bg-background p-3 font-mono text-[11px] leading-relaxed">
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
    <div className="flex items-center gap-2 rounded bg-surface px-2.5 py-1 border border-surface-elevated">
      {status === "pass" && <CheckCircle className="h-3.5 w-3.5 text-status-green" />}
      {status === "fail" && <XCircle className="h-3.5 w-3.5 text-status-red" />}
      {status === "pending" && <div className="h-3.5 w-3.5 rounded-full border-2 border-brand border-t-transparent animate-spin" />}
      <span className="text-[11px] font-medium text-text-primary">{label}</span>
    </div>
  );
}
