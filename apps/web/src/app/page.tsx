"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, ChevronRight, Plus, Server, Activity, Database, Search, Cpu } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary, Scenario } from "@/lib/types";
import { SeverityBadge, StatusBadge } from "@/components/Badges";
import { Card, SectionHeader } from "@/components/UI";

export default function Home() {
  const router = useRouter();
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const loadData = async () => {
    try {
      setError(null);
      const [incList, scenList] = await Promise.all([
        api.getIncidents(),
        api.getScenarios().catch(() => [])
      ]);
      setIncidents(incList);
      setScenarios(scenList);
      if (scenList.length > 0) {
        setSelectedScenarioId(scenList[0].id);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load data.");
    }
  };

  useEffect(() => { void loadData(); }, []);

  const createDemo = async () => {
    setCreating(true);
    try {
      const created = await api.createDemoIncident(selectedScenarioId || undefined);
      router.push(`/incidents/${created.id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create the demo incident.");
      setCreating(false);
    }
  };

  return (
    <main className="mx-auto w-full max-w-[1400px] p-6 lg:p-8 animate-in fade-in duration-300">
      
      {/* Top Hero Layout */}
      <div className="mb-6 rounded-lg border border-surface-elevated bg-surface p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="h-1.5 w-1.5 rounded-full bg-status-green shadow-[0_0_4px_currentColor]" />
            <span className="font-mono text-[10px] uppercase tracking-wider text-status-green">System Online</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">AI Incident Command</h1>
          <p className="text-[13px] text-text-secondary mt-1">Experiment-backed reasoning & deterministic resolution.</p>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
          {scenarios.length > 0 ? (
            <div className="relative flex-1 md:w-64">
              <select
                value={selectedScenarioId}
                onChange={(e) => setSelectedScenarioId(e.target.value)}
                className="w-full appearance-none rounded border border-surface-elevated bg-background px-3 py-1.5 text-[13px] text-text-primary outline-none transition-colors focus:border-brand"
              >
                {scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2">
                <ChevronRight className="h-3 w-3 text-text-secondary rotate-90" />
              </div>
            </div>
          ) : (
            <div className="h-8 w-48 animate-pulse rounded bg-surface-elevated" />
          )}
          <button 
            onClick={() => void createDemo()} 
            disabled={creating} 
            className="shrink-0 flex items-center gap-1.5 rounded bg-white px-3 py-1.5 text-[13px] font-semibold text-black transition-colors hover:bg-gray-200 disabled:opacity-50"
          >
            <Plus className="h-3.5 w-3.5" /> 
            {creating ? "Bootstrapping..." : "Run Demo"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 flex items-center gap-2 rounded border border-status-red/30 bg-status-red/10 p-3 text-[13px] text-status-red">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Grid Dashboard */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card className="p-4 border-surface-elevated/50 bg-background/50">
          <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">Active Incidents</span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{incidents.length}</span>
          </div>
        </Card>
        <Card className="p-4 border-surface-elevated/50 bg-background/50">
          <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">System Reasoner</span>
          <div className="mt-1 flex items-center gap-2">
            <Cpu className="h-4 w-4 text-brand" />
            <span className="text-sm font-semibold text-white">Hybrid Engine</span>
          </div>
        </Card>
      </div>

      {/* Investigations List */}
      <section>
        <SectionHeader title="Active Investigations" />
        <div className="grid gap-2">
          {incidents.map((incident) => (
            <Link href={`/incidents/${incident.id}`} key={incident.id} className="group block">
              <Card className="flex items-center gap-4 p-3 transition-colors hover:border-surface-elevated hover:bg-surface-elevated/30">
                <div className="shrink-0">
                  <SeverityBadge severity={incident.severity} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <h3 className="truncate text-sm font-semibold text-text-primary group-hover:text-white transition-colors">{incident.title}</h3>
                    <StatusBadge status={incident.status} />
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-4 font-mono text-[11px] text-text-secondary">
                    <span className="flex items-center gap-1"><Server className="h-3 w-3" />{incident.service}</span>
                    <span className="text-surface-elevated">•</span>
                    <span className="flex items-center gap-1"><Search className="h-3 w-3" />{incident.hypothesis_count} hypotheses</span>
                    <span className="text-surface-elevated">•</span>
                    <span className="flex items-center gap-1"><Database className="h-3 w-3" />{incident.evidence_count} evidence</span>
                  </div>
                </div>
                
                <div className="hidden flex-col items-end gap-1 md:flex">
                  <span className="rounded px-1.5 py-0.5 font-mono text-[9px] uppercase text-text-secondary border border-surface-elevated bg-background">
                    {incident.reasoning_mode === "live_model" ? "Live Mode" : "Deterministic Mode"}
                  </span>
                </div>
                
                <div className="shrink-0 pl-2">
                  <ChevronRight className="h-4 w-4 text-text-secondary transition-transform group-hover:translate-x-0.5 group-hover:text-white" />
                </div>
              </Card>
            </Link>
          ))}
          
          {!error && incidents.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-surface-elevated py-12 text-center">
              <Search className="mb-2 h-5 w-5 text-text-secondary opacity-50" />
              <p className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">No active incidents</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
