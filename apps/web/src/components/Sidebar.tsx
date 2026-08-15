"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Brain, ShieldAlert, Cpu } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type ReasoningMode = "live_model" | "deterministic_demo" | null;

export function Sidebar() {
  const pathname = usePathname();
  const [online, setOnline] = useState(false);
  const [reasoningMode, setReasoningMode] = useState<ReasoningMode>(null);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const h = await api.getHealth();
        if (mounted) {
          setOnline(h.status === "ok");
          setReasoningMode((h.reasoning_mode as ReasoningMode) ?? null);
        }
      } catch {
        if (mounted) {
          setOnline(false);
          setReasoningMode(null);
        }
      }
    };
    void check();
    const intv = setInterval(check, 5000);
    return () => { mounted = false; clearInterval(intv); };
  }, []);

  const modeLabel = !online
    ? "SYSTEM OFFLINE"
    : reasoningMode === "live_model"
      ? "Live Model"
      : reasoningMode === "deterministic_demo"
        ? "Deterministic Mode"
        : "Unknown Mode";

  const modeIndicatorClass = !online
    ? "bg-status-red"
    : reasoningMode === "live_model"
      ? "bg-status-blue animate-pulse"
      : "bg-status-amber animate-pulse";

  return (
    <aside className="w-64 bg-surface border-r border-surface-elevated flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-surface-elevated">
        <ShieldAlert className="w-6 h-6 text-brand mr-2" />
        <span className="font-bold tracking-tight text-lg">IncidentForge</span>
      </div>
      <nav className="flex-1 py-6 px-4 space-y-2">
        <Link href="/" className={cn("flex items-center px-4 py-2 text-sm font-medium rounded transition-colors", pathname === "/" || pathname.startsWith("/incidents") ? "text-text-primary bg-surface-elevated" : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated")}>
          <Activity className={cn("w-4 h-4 mr-3", pathname === "/" || pathname.startsWith("/incidents") ? "text-brand" : "")} />
          Incidents
        </Link>
        <Link href="/memory" className={cn("flex items-center px-4 py-2 text-sm font-medium rounded transition-colors", pathname === "/memory" ? "text-text-primary bg-surface-elevated" : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated")}>
          <Brain className={cn("w-4 h-4 mr-3", pathname === "/memory" ? "text-brand" : "")} />
          Memory
        </Link>
      </nav>
      <div className="p-4 border-t border-surface-elevated">
        <div className="flex items-center mb-2">
          <Cpu className="w-3 h-3 text-brand mr-2" />
          <span className="text-xs font-mono text-text-secondary uppercase">{modeLabel}</span>
        </div>
        <div className="flex items-center">
          <div className={cn("w-2 h-2 rounded-full mr-2", modeIndicatorClass)} />
          <span className="text-xs font-mono text-text-secondary">
            {online ? "SYSTEM ONLINE" : "SYSTEM OFFLINE"}
          </span>
        </div>
      </div>
    </aside>
  );
}
