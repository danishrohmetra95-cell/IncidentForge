"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ChevronRight, Plus, Server } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary } from "@/lib/types";
import { SeverityBadge, StatusBadge } from "@/components/Badges";

export default function Home() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const loadIncidents = async () => {
    try {
      setError(null);
      setIncidents(await api.getIncidents());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load incidents.");
    }
  };

  useEffect(() => { void loadIncidents(); }, []);

  const createDemo = async () => {
    setCreating(true);
    try {
      const created = await api.createDemoIncident();
      window.location.assign(`/incidents/${created.id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create the demo incident.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <main className="mx-auto max-w-6xl p-6 md:p-10">
      <section className="mb-10 flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="mb-2 font-mono text-xs uppercase tracking-[0.24em] text-brand">IncidentForge / command center</p>
          <h1 className="text-3xl font-bold tracking-tight">Experiment-backed incident reasoning</h1>
          <p className="mt-3 max-w-2xl text-sm text-text-secondary">AI can propose an explanation; the simulator, safety gate, and deterministic verifier decide what is actually supported.</p>
        </div>
        <button onClick={() => void createDemo()} disabled={creating} className="inline-flex items-center justify-center rounded bg-brand px-4 py-2.5 text-sm font-bold text-background transition hover:bg-brand/90 disabled:opacity-50">
          <Plus className="mr-2 h-4 w-4" /> {creating ? "Starting investigation…" : "Run deterministic demo"}
        </button>
      </section>

      {error && <div className="mb-6 rounded border border-status-red/40 bg-status-red/10 p-4 text-sm text-status-red"><AlertTriangle className="mr-2 inline h-4 w-4" />{error}</div>}

      <section className="overflow-hidden rounded-lg border border-surface-elevated bg-surface">
        <div className="grid grid-cols-[1fr_auto_auto] gap-4 border-b border-surface-elevated px-5 py-3 font-mono text-xs uppercase tracking-wider text-text-secondary">
          <span>Incident</span><span className="hidden sm:block">Reasoning</span><span>Status</span>
        </div>
        {incidents.map((incident) => (
          <Link href={`/incidents/${incident.id}`} key={incident.id} className="grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b border-surface-elevated px-5 py-5 transition hover:bg-surface-elevated/40 last:border-0">
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-2"><SeverityBadge severity={incident.severity} /><h2 className="truncate font-semibold">{incident.title}</h2></div>
              <div className="flex items-center gap-2 font-mono text-xs text-text-secondary"><Server className="h-3.5 w-3.5" />{incident.service}<span>·</span><span>{incident.hypothesis_count} hypotheses / {incident.evidence_count} evidence</span></div>
            </div>
            <span className="hidden rounded border border-surface-elevated px-2 py-1 font-mono text-[10px] uppercase text-text-secondary sm:block">{incident.reasoning_mode === "live_model" ? "Live model" : "Deterministic demo"}</span>
            <div className="flex items-center gap-3"><StatusBadge status={incident.status} /><ChevronRight className="h-4 w-4 text-text-secondary" /></div>
          </Link>
        ))}
        {!error && incidents.length === 0 && <div className="p-12 text-center text-sm text-text-secondary">No incident investigations have been created yet.</div>}
      </section>
    </main>
  );
}
