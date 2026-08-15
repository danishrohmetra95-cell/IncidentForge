"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Activity, Beaker, Database, FileSearch, GitBranch, Network, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentDetail, TelemetrySnapshot } from "@/lib/types";
import { SeverityBadge, StatusBadge, VerificationBadge } from "@/components/Badges";

const metricCards: Array<{ key: keyof TelemetrySnapshot; label: string; format: (value: number) => string }> = [
  { key: "p95_latency", label: "P95 latency", format: (value) => `${value.toFixed(1)} ms` },
  { key: "error_rate", label: "Error rate", format: (value) => `${(value * 100).toFixed(1)}%` },
  { key: "db_connections", label: "DB connections", format: (value) => value.toFixed(0) },
  { key: "db_utilization", label: "DB utilization", format: (value) => `${(value * 100).toFixed(1)}%` },
  { key: "cache_hit_rate", label: "Cache hit rate", format: (value) => `${(value * 100).toFixed(1)}%` },
  { key: "cpu", label: "CPU", format: (value) => `${(value * 100).toFixed(1)}%` },
];

export default function IncidentCommandCenter({ params }: { params: { id: string } }) {
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [evidenceExpanded, setEvidenceExpanded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setIncident(await api.getIncident(params.id));
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load incident.");
    }
  }, [params.id]);

  useEffect(() => { 
    void refresh(); 
    const es = api.subscribeToEvents(params.id, () => {
      void refresh();
    });
    return () => es.close();
  }, [params.id, refresh]);

  if (error) return <main className="p-8 text-sm text-status-red">{error}</main>;
  if (!incident) return <main className="p-8 font-mono text-sm text-text-secondary animate-pulse">Loading investigation artifacts…</main>;

  const observation = incident.observations.at(-1);
  const verification = incident.verifications.at(-1);
  const currentMetrics = observation?.post_intervention ?? observation?.baseline;
  const experiment = incident.experiments.at(-1);

  const evidenceToShow = evidenceExpanded ? incident.evidence : incident.evidence.slice(0, 5);

  return (
    <main className="mx-auto max-w-7xl p-6 md:p-10">
      <header className="mb-8 border-b border-surface-elevated pb-6">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
          <div>
            <div className="mb-3 flex flex-wrap items-center gap-3"><SeverityBadge severity={incident.severity} /><StatusBadge status={incident.status} /><span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">{incident.reasoning_mode === "live_model" ? "Live model proposals" : "Deterministic demo proposals"}</span></div>
            <h1 className="text-3xl font-bold">{incident.title}</h1>
            <p className="mt-2 max-w-3xl text-sm text-text-secondary">{incident.description}</p>
            <p className="mt-4 font-mono text-xs text-text-secondary">{incident.service} · {incident.id}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            {experiment && <Link href={`/incidents/${incident.id}/experiment`} className="inline-flex items-center rounded bg-brand px-4 py-2.5 text-sm font-bold text-background hover:bg-brand/90"><Beaker className="mr-2 h-4 w-4" />Open Experiment Lab</Link>}
            {incident.experiments && incident.experiments.length > 0 && <Link href={`/incidents/${incident.id}/counterfactual`} className="inline-flex items-center rounded bg-brand px-4 py-2.5 text-sm font-bold text-background hover:bg-brand/90"><GitBranch className="mr-2 h-4 w-4" />Counterfactual Analysis</Link>}
          </div>
        </div>
      </header>

      {!currentMetrics && <div className="mb-8 rounded border border-brand/30 bg-brand/10 p-4 text-sm text-text-secondary">The backend is collecting evidence and will publish telemetry after its registered experiment runs.</div>}
      {currentMetrics && <section className="mb-8"><div className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-text-secondary"><Activity className="h-4 w-4 text-brand" />Observed simulator metrics</div><div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">{metricCards.map(({ key, label, format }) => <div key={key} className="rounded border border-surface-elevated bg-surface p-4"><p className="text-xs text-text-secondary">{label}</p><p className="mt-1 font-mono text-lg font-semibold">{format(currentMetrics[key])}</p></div>)}</div></section>}

      <div className="grid gap-8 lg:grid-cols-[1.5fr_1fr]">
        <section>
          <div className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-text-secondary"><Network className="h-4 w-4 text-brand" />Competing hypotheses</div>
          <div className="space-y-3">
            {incident.hypotheses.map((hypothesis) => <article key={hypothesis.id} className="rounded border border-surface-elevated bg-surface p-5"><div className="flex items-start justify-between gap-4"><h2 className="font-semibold">{hypothesis.statement}</h2><span className="shrink-0 font-mono text-sm text-brand">{Math.round(hypothesis.score * 100)}%</span></div><div className="mt-3 h-1.5 overflow-hidden rounded bg-background"><div className="h-full bg-brand" style={{ width: `${hypothesis.score * 100}%` }} /></div><div className="mt-3 flex flex-wrap gap-2 text-xs text-text-secondary"><span>{hypothesis.status}</span><span>·</span><span>{hypothesis.supporting_evidence.length} linked evidence items</span></div></article>)}
          </div>
        </section>

        <aside className="space-y-6">
          <section>
            <div className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-text-secondary"><FileSearch className="h-4 w-4 text-brand" />Evidence</div>
            <div className="space-y-2">
              {evidenceToShow.map((evidence) => <article key={evidence.id} className="rounded border border-surface-elevated bg-surface p-3"><p className="mb-1 font-mono text-[10px] uppercase text-brand">{evidence.type} · strength {Math.round(evidence.strength * 100)}%</p><p className="text-sm text-text-secondary">{evidence.observation}</p></article>)}
            </div>
            {incident.evidence.length > 5 && (
              <button onClick={() => setEvidenceExpanded(!evidenceExpanded)} className="mt-3 flex items-center gap-1 text-xs text-text-secondary hover:text-text-primary transition">
                {evidenceExpanded ? <><ChevronUp className="h-3 w-3" /> Show less</> : <><ChevronDown className="h-3 w-3" /> Show {incident.evidence.length - 5} more evidence items</>}
              </button>
            )}
          </section>
          {verification && <section className="rounded border border-surface-elevated bg-surface p-5"><div className="mb-3 flex items-center justify-between"><div className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-text-secondary"><ShieldCheck className="h-4 w-4 text-brand" />Deterministic verdict</div><VerificationBadge result={verification.outcome} /></div><p className="text-sm text-text-secondary">{verification.explanation}</p></section>}
        </aside>
      </div>

      <section className="mt-10"><div className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-text-secondary"><Database className="h-4 w-4 text-brand" />Audit timeline</div><div className="space-y-2">{incident.timeline.map((event) => <article key={event.id} className="grid gap-2 rounded border border-surface-elevated bg-surface px-4 py-3 md:grid-cols-[12rem_1fr]"><span className="font-mono text-xs text-brand">{event.event_type}</span><div><p className="text-sm font-medium">{event.title}</p>{event.description && <p className="mt-1 text-sm text-text-secondary">{event.description}</p>}</div></article>)}</div></section>
    </main>
  );
}
