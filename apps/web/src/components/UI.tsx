import React from "react";
import { AlertTriangle, CheckCircle, ChevronRight, XCircle, Info, ShieldCheck, Search, Database, Activity, GitBranch, Beaker, FileSearch, Network, Server, Play } from "lucide-react";

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-xl border border-surface-elevated/70 bg-gradient-to-b from-surface/80 to-surface/40 backdrop-blur-md shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function SectionHeader({ title, icon: Icon, description }: { title: string; icon?: React.ElementType; description?: string }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.15em] text-text-secondary">
        {Icon && <Icon className="h-4 w-4 text-brand opacity-80" />}
        {title}
      </div>
      {description && <p className="mt-1 text-[13px] text-text-secondary leading-relaxed">{description}</p>}
    </div>
  );
}

export function DisplayValue({ label, value, delta, previous, isPositive = false }: { label: string; value: string | React.ReactNode; delta?: string; previous?: string; isPositive?: boolean }) {
  return (
    <div className="flex flex-col relative group">
      <span className="text-[10px] font-mono uppercase tracking-[0.1em] text-text-secondary mb-1 opacity-80">{label}</span>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[22px] font-bold text-white tracking-tight">{value}</span>
        {delta && (
          <span className={`font-mono text-[11px] font-semibold px-1.5 py-0.5 rounded ${isPositive ? 'bg-status-green/10 text-status-green' : 'bg-status-amber/10 text-status-amber'}`}>
            {delta}
          </span>
        )}
      </div>
      {previous && <span className="font-mono text-[10px] text-text-secondary mt-1 opacity-70">prev: {previous}</span>}
    </div>
  );
}

export function DiffBlock({ diff }: { diff: string }) {
  return (
    <pre className="overflow-x-auto rounded-lg border border-surface-elevated/50 bg-[#0d1117] p-4 shadow-inner font-mono text-[12px] leading-relaxed relative">
      <div className="absolute top-0 left-0 w-1 h-full bg-surface-elevated/30"></div>
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
            <div key={i} className={`px-3 py-0.5 -ml-4 ${bg} ${color}`}>
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
    <div className="flex items-center gap-2 rounded-md bg-surface/50 px-3 py-1.5 border border-surface-elevated/50 shadow-sm backdrop-blur-sm">
      {status === "pass" && <CheckCircle className="h-4 w-4 text-status-green drop-shadow-[0_0_4px_rgba(34,197,94,0.4)]" />}
      {status === "fail" && <XCircle className="h-4 w-4 text-status-red drop-shadow-[0_0_4px_rgba(239,68,68,0.4)]" />}
      {status === "pending" && <div className="h-3.5 w-3.5 rounded-full border-2 border-brand border-t-transparent animate-spin drop-shadow-[0_0_4px_rgba(245,158,11,0.4)]" />}
      <span className="text-[11px] font-mono tracking-wide uppercase text-white opacity-90">{label}</span>
    </div>
  );
}
