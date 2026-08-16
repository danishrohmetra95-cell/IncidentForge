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
    : "bg-brand animate-pulse";

  return (
    <aside className="w-64 bg-background border-r border-surface-elevated flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.5)] z-10 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-brand/5 to-transparent pointer-events-none" />
      <div className="h-20 flex items-center px-6 border-b border-surface-elevated/50 relative">
        <ShieldAlert className="w-6 h-6 text-brand mr-3 drop-shadow-[0_0_8px_rgba(255,165,0,0.5)]" />
        <span className="font-extrabold tracking-widest text-white text-lg uppercase font-mono">IncidentForge</span>
      </div>
      <nav className="flex-1 py-8 px-4 space-y-3 relative z-10">
        <Link href="/" className={cn("group flex items-center px-4 py-3 text-sm font-semibold rounded-lg transition-all duration-300", pathname === "/" || pathname.startsWith("/incidents") ? "text-white bg-surface shadow-md border border-surface-elevated" : "text-text-secondary hover:text-white hover:bg-surface/50 border border-transparent")}>
          <Activity className={cn("w-5 h-5 mr-3 transition-transform group-hover:scale-110", pathname === "/" || pathname.startsWith("/incidents") ? "text-brand" : "")} />
          Incidents
        </Link>
        <Link href="/memory" className={cn("group flex items-center px-4 py-3 text-sm font-semibold rounded-lg transition-all duration-300", pathname === "/memory" ? "text-white bg-surface shadow-md border border-surface-elevated" : "text-text-secondary hover:text-white hover:bg-surface/50 border border-transparent")}>
          <Brain className={cn("w-5 h-5 mr-3 transition-transform group-hover:scale-110", pathname === "/memory" ? "text-brand" : "")} />
          Memory
        </Link>
      </nav>
      <div className="p-6 border-t border-surface-elevated/50 bg-surface/30 backdrop-blur-md relative z-10">
        <div className="flex items-center mb-3">
          <Cpu className="w-4 h-4 text-brand mr-2 opacity-80" />
          <span className="text-[10px] font-mono font-bold tracking-[0.15em] text-text-secondary uppercase">{modeLabel}</span>
        </div>
        <div className="flex items-center bg-background/50 rounded-full px-3 py-1.5 border border-surface-elevated w-fit">
          <div className={cn("w-2 h-2 rounded-full mr-2 shadow-[0_0_8px_currentColor]", modeIndicatorClass)} />
          <span className="text-[10px] font-mono font-bold tracking-wider text-text-primary">
            {online ? "SYSTEM ONLINE" : "SYSTEM OFFLINE"}
          </span>
        </div>
      </div>
    </aside>
  );
}
