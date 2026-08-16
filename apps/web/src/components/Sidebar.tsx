"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Brain, ShieldAlert, Cpu, Database, Server, Globe } from "lucide-react";
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
    : "bg-brand animate-pulse";

  if (pathname === "/") return null;

  return (
    <aside className="w-[240px] shrink-0 bg-surface/80 backdrop-blur border-r border-surface-elevated/50 flex flex-col z-10 relative">
      <div className="h-14 flex items-center px-5 border-b border-surface-elevated/50">
        <ShieldAlert className="w-5 h-5 text-brand mr-2" />
        <span className="font-semibold tracking-wide text-white text-sm">IncidentForge</span>
      </div>
      
      <div className="flex-1 flex flex-col gap-6 py-5 px-3 overflow-y-auto">
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-brand mb-2">Deterministic Demo</p>
          <Link href="/command-center" className={cn("group flex items-center px-3 py-2 text-sm rounded-md transition-colors", pathname === "/command-center" || (pathname.startsWith("/incidents") && !pathname.includes("/applications")) ? "text-white bg-surface-elevated/80 shadow-sm" : "text-text-secondary hover:text-white hover:bg-surface-elevated/40")}>
            <Activity className={cn("w-4 h-4 mr-3 transition-transform group-hover:scale-110", pathname === "/command-center" || (pathname.startsWith("/incidents") && !pathname.includes("/applications")) ? "text-brand" : "")} />
            Command Center
          </Link>
          <Link href="/memory" className={cn("group flex items-center px-3 py-2 text-sm rounded-md transition-colors", pathname === "/memory" ? "text-white bg-surface-elevated/80 shadow-sm" : "text-text-secondary hover:text-white hover:bg-surface-elevated/40")}>
            <Brain className={cn("w-4 h-4 mr-3 transition-transform group-hover:scale-110", pathname === "/memory" ? "text-brand" : "")} />
            Institutional Memory
          </Link>
        </div>

        <div className="space-y-1">
          <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-brand mb-2">Live Application</p>
          <Link href="/applications/connect" className={cn("group flex items-center px-3 py-2 text-sm rounded-md transition-colors", pathname === "/applications/connect" ? "text-white bg-surface-elevated/80 shadow-sm" : "text-text-secondary hover:text-white hover:bg-surface-elevated/40")}>
            <Globe className={cn("w-4 h-4 mr-3 transition-transform group-hover:scale-110", pathname === "/applications/connect" ? "text-brand" : "")} />
            Connect Application
          </Link>
        </div>

        <div className="space-y-1">
          <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-text-secondary mb-2">Observability</p>
          <div className="group flex items-center px-3 py-2 text-sm rounded-md text-text-secondary/50 cursor-not-allowed">
            <Server className="w-4 h-4 mr-3" />
            Services <span className="ml-auto text-[9px] uppercase">Coming Soon</span>
          </div>
          <div className="group flex items-center px-3 py-2 text-sm rounded-md text-text-secondary/50 cursor-not-allowed">
            <Database className="w-4 h-4 mr-3" />
            Telemetry <span className="ml-auto text-[9px] uppercase">Coming Soon</span>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-surface-elevated/50 bg-background/50 backdrop-blur-sm mt-auto">
        <p className="px-2 text-[10px] font-mono uppercase tracking-wider text-text-secondary mb-2">System Status</p>
        <div className="flex flex-col gap-2">
          <div className="flex items-center px-2">
            <div className={cn("w-1.5 h-1.5 rounded-full mr-2 shadow-[0_0_4px_currentColor]", modeIndicatorClass)} />
            <span className="text-[11px] font-medium text-text-primary">
              {online ? "Gateway Online" : "Gateway Offline"}
            </span>
          </div>
          <div className="flex items-center px-2">
            <Cpu className="w-3.5 h-3.5 text-text-secondary mr-2" />
            <span className="text-[10px] font-mono text-text-secondary">{modeLabel}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
