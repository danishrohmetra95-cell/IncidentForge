"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, ChevronRight, Server, Database, Search, Cpu, ShieldCheck, Beaker, Network, GitBranch, Target, FlaskConical, CheckCircle2, ShieldAlert, Activity, ArrowRight, Play, Globe, FileText } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary, IncidentDetail } from "@/lib/types";
import { SeverityBadge, StatusBadge } from "@/components/Badges";
import { Card } from "@/components/UI";
import { cn } from "@/lib/utils";

export default function CommandCenter() {
  const router = useRouter();
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [featuredIncident, setFeaturedIncident] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const incList = await api.getIncidents();
        setIncidents(incList);
        
        // Find best deterministic incident (exclude Amazon Live Connector)
        const deterministic = incList.filter(i => !i.title.toLowerCase().includes("amazon") && !i.title.toLowerCase().includes("live application"));
        
        if (deterministic.length > 0) {
          // Prefer resolved high severity
          const best = deterministic.sort((a, b) => {
            if (a.status === "RESOLVED" && b.status !== "RESOLVED") return -1;
            if (b.status === "RESOLVED" && a.status !== "RESOLVED") return 1;
            return 0;
          })[0];
          
          const detail = await api.getIncident(best.id);
          setFeaturedIncident(detail);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  // KPIs
  const totalCount = incidents.length;
  const resolvedCount = incidents.filter(i => i.status === "RESOLVED").length;
  const hypothesisCount = incidents.reduce((sum, i) => sum + i.hypothesis_count, 0);
  const evidenceCount = incidents.reduce((sum, i) => sum + i.evidence_count, 0);

  const recentIncidents = [...incidents].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 6);

  const getModeBadge = (inc: IncidentSummary) => {
    if (inc.title.toLowerCase().includes("amazon") || inc.title.toLowerCase().includes("simulated live")) {
      return <span className="bg-brand/10 text-brand border border-brand/20 px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-widest whitespace-nowrap">SIMULATED LIVE DEMO</span>;
    }
    if (inc.reasoning_mode === "live_model") {
      return <span className="bg-status-blue/10 text-status-blue border border-status-blue/20 px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-widest whitespace-nowrap">LIVE APPLICATION</span>;
    }
    return <span className="bg-white/5 text-text-secondary border border-white/10 px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-widest whitespace-nowrap">DETERMINISTIC</span>;
  };

  return (
    <div className="flex-1 p-8 lg:p-12 overflow-y-auto bg-background min-h-screen">
      <div className="max-w-[1400px] mx-auto space-y-12">
        
        {/* HERO / HEADER */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-surface-elevated/50 pb-8">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-brand/10 border border-brand/20 rounded-lg flex items-center justify-center">
                <ShieldAlert className="w-5 h-5 text-brand" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">IncidentForge Command Center</h1>
                <p className="text-text-secondary text-sm mt-1">AI that investigates incidents — then proves the cause.</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 bg-surface border border-surface-elevated rounded-full px-4 py-2">
            <span className="w-2 h-2 rounded-full bg-status-green animate-pulse" />
            <span className="text-[10px] font-mono uppercase tracking-widest text-status-green font-bold">System Online</span>
          </div>
        </header>

        {/* AI REASONING PIPELINE VISUALIZATION */}
        <section className="bg-surface border border-surface-elevated/50 rounded-xl p-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-brand/5 via-transparent to-status-green/5 pointer-events-none" />
          <h2 className="text-[10px] font-mono uppercase tracking-widest text-text-secondary mb-6">Core Reasoning Engine</h2>
          <div className="flex flex-wrap items-center justify-between gap-4 relative z-10">
            <PipelineNode icon={Activity} label="OBSERVE" color="blue" />
            <PipelineArrow />
            <PipelineNode icon={GitBranch} label="HYPOTHESIZE" color="white" />
            <PipelineArrow />
            <PipelineNode icon={ShieldCheck} label="CRITIQUE" color="red" />
            <PipelineArrow />
            <PipelineNode icon={Beaker} label="EXPERIMENT" color="brand" />
            <PipelineArrow />
            <PipelineNode icon={CheckCircle2} label="VERIFY" color="green" />
            <PipelineArrow />
            <PipelineNode icon={Target} label="REMEDIATE" color="blue" />
          </div>
        </section>

        {/* KPI ROW */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard label="TOTAL INVESTIGATIONS" value={totalCount} />
          <KpiCard label="VERIFIED ROOT CAUSES" value={resolvedCount} />
          <KpiCard label="HYPOTHESES GENERATED" value={hypothesisCount} />
          <KpiCard label="EVIDENCE CAPTURED" value={evidenceCount} />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          {/* MAIN COLUMN: RECENT INVESTIGATIONS */}
          <div className="xl:col-span-2 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold tracking-wide text-white flex items-center gap-2">
                <Server className="w-5 h-5 text-text-secondary" />
                RECENT INVESTIGATIONS
              </h2>
            </div>
            
            <div className="space-y-3">
              {loading ? (
                <div className="h-32 bg-surface animate-pulse rounded-xl border border-surface-elevated" />
              ) : recentIncidents.map(inc => (
                <Link key={inc.id} href={`/incidents/${inc.id}`} className="block">
                  <div className="bg-surface border border-surface-elevated/50 hover:border-brand/50 hover:bg-surface-elevated/30 transition-all rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 group">
                    
                    <div className="flex items-start gap-4">
                      <SeverityBadge severity={inc.severity} />
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-semibold text-white group-hover:text-brand transition-colors line-clamp-1">{inc.title}</h3>
                          {getModeBadge(inc)}
                        </div>
                        <div className="flex flex-wrap items-center gap-4 text-xs text-text-secondary">
                          <span className="flex items-center gap-1"><Cpu className="w-3 h-3" /> {inc.service}</span>
                          <span className="flex items-center gap-1"><GitBranch className="w-3 h-3 text-brand/70" /> {inc.hypothesis_count} Hypotheses</span>
                          <span className="flex items-center gap-1"><FileText className="w-3 h-3 text-status-blue/70" /> {inc.evidence_count} Evidence</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6 mt-4 md:mt-0 md:pl-4">
                      <StatusBadge status={inc.status} />
                      <ChevronRight className="w-5 h-5 text-text-secondary group-hover:text-white transition-colors flex-shrink-0" />
                    </div>
                  </div>
                </Link>
              ))}
              {recentIncidents.length === 0 && !loading && (
                <div className="p-12 flex flex-col items-center justify-center text-center border border-dashed border-surface-elevated rounded-xl">
                  <Search className="w-8 h-8 text-text-secondary mb-4 opacity-50" />
                  <p className="text-white font-medium mb-2">No investigations yet</p>
                  <p className="text-sm text-text-secondary mb-6">Connect a live application or run a deterministic demo.</p>
                  <Link 
                    href="/applications/connect"
                    className="bg-brand text-black font-bold text-xs tracking-widest uppercase px-6 py-2.5 rounded hover:bg-brand/90 transition-colors"
                  >
                    Connect Application
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN: FEATURED & LIVE CONNECTOR */}
          <div className="space-y-8">
            
            {/* LIVE APPLICATION CONNECTOR CTA */}
            <div className="bg-gradient-to-b from-[#0e1628] to-surface border border-status-blue/30 rounded-xl p-6 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-status-blue/10 blur-[50px] rounded-full group-hover:bg-status-blue/20 transition-colors" />
              <div className="flex items-center gap-3 mb-4 relative z-10">
                <Globe className="w-5 h-5 text-status-blue" />
                <h2 className="text-sm font-bold tracking-widest uppercase text-white">Live Application</h2>
              </div>
              <p className="text-text-secondary text-sm mb-6 relative z-10">
                Connect a real external application and observe its health through the IncidentForge deterministic reasoning engine.
              </p>
              <Link 
                href="/applications/connect" 
                className="inline-flex items-center justify-center w-full gap-2 bg-status-blue hover:bg-blue-500 text-white font-bold text-xs tracking-widest uppercase px-6 py-3 rounded-lg transition-colors shadow-[0_0_20px_rgba(59,130,246,0.15)] relative z-10"
              >
                Connect Application <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* FEATURED INVESTIGATION */}
            {featuredIncident && (
              <div className="bg-surface border border-surface-elevated/50 rounded-xl p-6 flex flex-col h-[320px]">
                <h2 className="text-[10px] font-mono uppercase tracking-widest text-brand mb-4">Featured Investigation</h2>
                <div className="mb-4">
                  <h3 className="text-lg font-bold text-white mb-2 leading-tight line-clamp-2">{featuredIncident.title}</h3>
                  <div className="flex items-center gap-2 mb-4">
                    <SeverityBadge severity={featuredIncident.severity} />
                    <StatusBadge status={featuredIncident.status} />
                  </div>
                </div>
                
                <div className="bg-background/50 rounded-lg p-4 border border-surface-elevated/50 mb-auto">
                  <div className="text-[10px] font-mono uppercase text-text-secondary mb-1">Leading Root Cause</div>
                  <p className="text-sm text-white/90 line-clamp-2">
                    {featuredIncident.hypotheses.sort((a,b) => b.score - a.score)[0]?.statement || "Hypothesis generation in progress..."}
                  </p>
                </div>
                
                <Link 
                  href={`/incidents/${featuredIncident.id}`}
                  className="mt-6 inline-flex items-center justify-center w-full gap-2 border border-white/10 hover:border-white/30 bg-surface-elevated/30 hover:bg-surface-elevated/50 text-white font-bold text-xs tracking-widest uppercase px-6 py-3 rounded-lg transition-all"
                >
                  View Investigation <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}

// Subcomponents

function KpiCard({ label, value }: { label: string, value: number }) {
  return (
    <div className="bg-surface border border-surface-elevated/50 rounded-xl p-5 flex flex-col justify-between h-28">
      <h3 className="text-[10px] font-mono uppercase tracking-widest text-text-secondary">{label}</h3>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
}

function PipelineNode({ icon: Icon, label, color }: { icon: any, label: string, color: 'brand'|'green'|'red'|'blue'|'white' }) {
  const colorStyles = {
    brand: "text-brand border-brand/30 bg-brand/5 shadow-[0_0_15px_rgba(232,169,21,0.1)]",
    green: "text-status-green border-status-green/30 bg-status-green/5 shadow-[0_0_15px_rgba(163,190,140,0.1)]",
    red: "text-status-red border-status-red/30 bg-status-red/5",
    blue: "text-status-blue border-status-blue/30 bg-status-blue/5",
    white: "text-white border-white/10 bg-white/5"
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={cn("w-10 h-10 rounded-lg border flex items-center justify-center", colorStyles[color])}>
        <Icon className="w-5 h-5" />
      </div>
      <span className="text-[9px] font-mono uppercase tracking-widest text-text-secondary">{label}</span>
    </div>
  );
}

function PipelineArrow() {
  return <div className="h-px flex-1 bg-surface-elevated relative min-w-[20px]" />;
}
