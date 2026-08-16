"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, ChevronRight, Plus, Server, Activity, Database, GitBranch, TerminalSquare, Search } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary, Scenario } from "@/lib/types";
import { SeverityBadge, StatusBadge } from "@/components/Badges";
import { Card } from "@/components/UI";

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
    <main className="mx-auto max-w-6xl p-6 md:p-12 animate-in fade-in duration-500">
      <section className="mb-16 flex flex-col justify-between gap-8 md:flex-row md:items-end">
        <div className="max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-brand">
            <div className="h-1.5 w-1.5 rounded-full bg-brand animate-pulse" />
            System Online
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white md:text-5xl">AI Incident Command</h1>
          <p className="mt-4 text-base leading-relaxed text-text-secondary">
            Deterministic verification for LLM reasoning. AI proposes hypotheses, 
            an adversarial critic challenges them, and the digital twin mathematically verifies 
            the root cause before applying remediation.
          </p>
        </div>
        
        <Card className="flex flex-col gap-4 p-5 md:min-w-[320px] shadow-2xl shadow-brand/5">
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-text-secondary">
            <TerminalSquare className="h-4 w-4" /> Initialize Scenario
          </div>
          {scenarios.length > 0 ? (
            <select
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(e.target.value)}
              className="w-full rounded-md border border-surface-elevated bg-background px-3 py-2.5 text-sm text-text-primary shadow-inner outline-none transition-colors focus:border-brand"
            >
              {scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
            </select>
          ) : (
            <div className="h-10 w-full animate-pulse rounded bg-surface-elevated/50" />
          )}
          <button 
            onClick={() => void createDemo()} 
            disabled={creating} 
            className="group relative inline-flex w-full items-center justify-center overflow-hidden rounded-md bg-brand px-4 py-2.5 text-sm font-bold text-background transition-all hover:bg-brand/90 disabled:opacity-50"
          >
            <span className="relative z-10 flex items-center gap-2">
              <Plus className="h-4 w-4" /> 
              {creating ? "Bootstrapping simulation..." : "Run deterministic demo"}
            </span>
            <div className="absolute inset-0 z-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] transition-transform duration-1000 group-hover:translate-x-[100%]" />
          </button>
        </Card>
      </section>

      {error && (
        <div className="mb-8 flex items-center gap-3 rounded-lg border border-status-red/30 bg-status-red/10 p-4 text-sm text-status-red shadow-lg shadow-status-red/5">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <div className="mb-6 flex items-center justify-between">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-secondary">Active Investigations</h2>
        <div className="flex items-center gap-2 font-mono text-xs text-text-secondary">
          <Activity className="h-4 w-4" /> {incidents.length} total
        </div>
      </div>

      <div className="grid gap-3">
        {incidents.map((incident) => (
          <Link href={`/incidents/${incident.id}`} key={incident.id} className="group block">
            <Card className="grid items-center gap-4 p-5 transition-all duration-300 hover:border-brand/30 hover:bg-surface-elevated hover:shadow-lg hover:shadow-brand/5 md:grid-cols-[1fr_auto_auto]">
              <div className="min-w-0">
                <div className="mb-2 flex flex-wrap items-center gap-3">
                  <SeverityBadge severity={incident.severity} />
                  <h3 className="truncate text-lg font-semibold text-text-primary group-hover:text-white transition-colors">{incident.title}</h3>
                </div>
                <div className="flex flex-wrap items-center gap-4 font-mono text-xs text-text-secondary">
                  <span className="flex items-center gap-1.5"><Server className="h-3.5 w-3.5" />{incident.service}</span>
                  <span className="text-surface-elevated">•</span>
                  <span className="flex items-center gap-1.5"><Search className="h-3.5 w-3.5" />{incident.hypothesis_count} hypotheses</span>
                  <span className="text-surface-elevated">•</span>
                  <span className="flex items-center gap-1.5"><Database className="h-3.5 w-3.5" />{incident.evidence_count} evidence</span>
                </div>
              </div>
              
              <div className="hidden flex-col items-end gap-2 md:flex">
                <span className="rounded border border-surface-elevated bg-background/50 px-2 py-1 font-mono text-[10px] uppercase text-text-secondary shadow-inner">
                  {incident.reasoning_mode === "live_model" ? "Live Model" : "Deterministic Fallback"}
                </span>
              </div>
              
              <div className="flex items-center gap-4">
                <StatusBadge status={incident.status} />
                <ChevronRight className="h-5 w-5 text-text-secondary transition-transform group-hover:translate-x-1 group-hover:text-brand" />
              </div>
            </Card>
          </Link>
        ))}
        {!error && incidents.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-surface-elevated py-20 text-center">
            <Search className="mb-4 h-8 w-8 text-surface-elevated" />
            <p className="font-mono text-sm uppercase tracking-wider text-text-secondary">No active incidents</p>
          </div>
        )}
      </div>
    </main>
  );
}
