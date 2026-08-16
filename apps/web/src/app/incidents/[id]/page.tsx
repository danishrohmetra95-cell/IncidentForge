"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { Activity, Beaker, ChevronDown, ChevronUp, Database, FileSearch, GitBranch, Network, ShieldCheck, Server, AlertTriangle, ArrowRight, CheckCircle2, XCircle } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentDetail, TelemetrySnapshot } from "@/lib/types";
import { SeverityBadge, StatusBadge, VerificationBadge } from "@/components/Badges";
import { Card, SectionHeader, DisplayValue, DiffBlock } from "@/components/UI";

const metricCards: Array<{ key: keyof TelemetrySnapshot; label: string; format: (value: number) => string }> = [
  { key: "p95_latency", label: "P95 latency", format: (value) => `${value.toFixed(1)} ms` },
  { key: "error_rate", label: "Error rate", format: (value) => `${(value * 100).toFixed(1)}%` },
  { key: "db_connections", label: "DB connections", format: (value) => value.toFixed(0) },
  { key: "db_utilization", label: "DB util", format: (value) => `${(value * 100).toFixed(1)}%` },
  { key: "cache_hit_rate", label: "Cache hit", format: (value) => `${(value * 100).toFixed(1)}%` },
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

  if (error) return <main className="p-8 text-sm text-status-red flex items-center gap-2"><AlertTriangle className="h-4 w-4" />{error}</main>;
  if (!incident) return (
    <main className="flex h-[50vh] items-center justify-center p-8">
      <div className="flex flex-col items-center gap-4 text-text-secondary">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
        <p className="font-mono text-sm uppercase tracking-wider">Synchronizing state...</p>
      </div>
    </main>
  );

  const observation = incident.observations.at(-1);
  const verification = incident.verifications.at(-1);
  const currentMetrics = observation?.post_intervention ?? observation?.baseline;
  const baselineMetrics = observation?.baseline;
  const experiment = incident.experiments.at(-1);
  const remediation = incident.remediation;
  const critic = incident.critiques?.at(-1);

  const evidenceToShow = evidenceExpanded ? incident.evidence : incident.evidence.slice(0, 4);

  // Sorting hypotheses
  const sortedHypotheses = [...incident.hypotheses].sort((a, b) => b.score - a.score);

  return (
    <main className="mx-auto max-w-7xl p-6 md:p-8 animate-in fade-in duration-500">
      <header className="mb-8">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-start">
          <div className="flex-1">
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <span className="rounded-sm border border-brand/20 bg-brand/5 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-brand shadow-inner">
                {incident.reasoning_mode === "live_model" ? "Live Model Reasoning" : "Deterministic Fallback"}
              </span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white md:text-4xl">{incident.title}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-text-secondary">{incident.description}</p>
            <div className="mt-4 flex items-center gap-4 font-mono text-xs text-text-secondary">
              <span className="flex items-center gap-1.5"><Server className="h-3.5 w-3.5" />{incident.service}</span>
              <span className="text-surface-elevated">•</span>
              <span>ID: {incident.id}</span>
            </div>
          </div>
          <div className="flex shrink-0 flex-col gap-3">
            {experiment && (
              <Link href={`/incidents/${incident.id}/experiment`} className="group flex items-center justify-center gap-2 rounded-md bg-surface-elevated px-4 py-2.5 text-sm font-semibold text-white shadow-sm ring-1 ring-inset ring-white/10 transition-all hover:bg-surface-elevated/80">
                <Beaker className="h-4 w-4 text-brand" />
                Experiment Lab
                <ArrowRight className="h-4 w-4 text-text-secondary transition-transform group-hover:translate-x-1" />
              </Link>
            )}
            {incident.experiments && incident.experiments.length > 0 && (
              <Link href={`/incidents/${incident.id}/counterfactual`} className="group flex items-center justify-center gap-2 rounded-md bg-surface-elevated px-4 py-2.5 text-sm font-semibold text-white shadow-sm ring-1 ring-inset ring-white/10 transition-all hover:bg-surface-elevated/80">
                <GitBranch className="h-4 w-4 text-brand" />
                Counterfactuals
                <ArrowRight className="h-4 w-4 text-text-secondary transition-transform group-hover:translate-x-1" />
              </Link>
            )}
          </div>
        </div>
      </header>

      <div className="grid gap-8 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-8">
          
          {/* HYPOTHESES */}
          <section>
            <SectionHeader title="Competing Hypotheses" icon={Network} description="Ranked causal proposals based on initial evidence and symptoms." />
            <div className="grid gap-4">
              {sortedHypotheses.map((hypothesis, index) => {
                const isLeading = index === 0;
                const isVerified = hypothesis.status === "VERIFIED";
                const isRejected = hypothesis.status === "REJECTED";
                return (
                  <Card key={hypothesis.id} className={`p-5 transition-all duration-300 ${isVerified ? 'border-status-green/50 bg-status-green/5' : isLeading ? 'border-brand/30 bg-brand/5 shadow-lg shadow-brand/5' : ''}`}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded bg-background font-mono text-sm font-bold shadow-inner ${isVerified ? 'text-status-green' : isLeading ? 'text-brand' : 'text-text-secondary'}`}>
                          #{index + 1}
                        </span>
                        <div>
                          <h2 className="text-base font-semibold text-white">{hypothesis.statement}</h2>
                          <div className="mt-2 flex items-center gap-3 font-mono text-xs">
                            <span className={`rounded-sm px-1.5 py-0.5 font-bold ${isVerified ? 'bg-status-green/20 text-status-green' : isRejected ? 'bg-status-red/20 text-status-red' : 'bg-surface-elevated text-text-secondary'}`}>
                              {hypothesis.status}
                            </span>
                            <span className="text-text-secondary">•</span>
                            <span className="text-text-secondary">{hypothesis.supporting_evidence.length} evidence sources</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`font-mono text-xl font-bold ${isVerified ? 'text-status-green' : isLeading ? 'text-brand' : 'text-text-primary'}`}>
                          {Math.round(hypothesis.score * 100)}%
                        </span>
                      </div>
                    </div>
                    <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-background shadow-inner">
                      <div 
                        className={`h-full transition-all duration-1000 ease-out ${isVerified ? 'bg-status-green' : isLeading ? 'bg-brand' : 'bg-text-secondary'}`} 
                        style={{ width: `${Math.max(2, hypothesis.score * 100)}%` }} 
                      />
                    </div>
                  </Card>
                );
              })}
            </div>
          </section>

          {/* CRITIC CHALLENGE */}
          {critic && (
            <section className="relative">
              <div className="absolute -left-[1.2rem] top-8 bottom-0 w-px bg-surface-elevated" />
              <SectionHeader title="Adversarial Critic" icon={ShieldCheck} description="Automated falsification challenge to the leading hypothesis." />
              <Card className="border-status-amber/20 bg-status-amber/5 p-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-mono text-[10px] uppercase tracking-wider text-status-amber mb-1">Objection</h4>
                    <p className="text-sm text-text-primary leading-relaxed">{critic.objections}</p>
                  </div>
                  <div>
                    <h4 className="font-mono text-[10px] uppercase tracking-wider text-status-amber mb-1">Falsification Criteria</h4>
                    <p className="text-sm font-medium text-text-primary leading-relaxed border-l-2 border-status-amber/50 pl-3 py-1 bg-status-amber/5">{critic.falsification_criteria}</p>
                  </div>
                </div>
              </Card>
            </section>
          )}

          {/* VERIFICATION & REMEDIATION */}
          {(verification || remediation) && (
            <section>
              <SectionHeader title="Verification & Resolution" icon={CheckCircle2} />
              <div className="space-y-4">
                {verification && (
                  <Card className={`p-6 ${verification.outcome === 'VERIFIED' ? 'border-status-green/30 bg-status-green/5' : 'border-status-red/30 bg-status-red/5'}`}>
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {verification.outcome === 'VERIFIED' ? <CheckCircle2 className="h-6 w-6 text-status-green" /> : <XCircle className="h-6 w-6 text-status-red" />}
                        <h3 className="text-lg font-bold text-white">{verification.outcome}</h3>
                      </div>
                    </div>
                    <p className="text-sm text-text-primary mb-6 leading-relaxed">{verification.explanation}</p>
                    
                    {verification.conditions && verification.conditions.length > 0 && (
                      <div className="grid gap-3 sm:grid-cols-2">
                        {verification.conditions.map((cond, i) => (
                          <div key={i} className="rounded border border-surface-elevated bg-background/50 p-3">
                            <div className="flex items-start justify-between gap-2">
                              <span className="font-mono text-xs text-text-secondary">{cond.metric}</span>
                              <span className={`font-mono text-[10px] uppercase font-bold ${cond.passed ? 'text-status-green' : 'text-status-red'}`}>
                                {cond.passed ? 'PASS' : 'FAIL'}
                              </span>
                            </div>
                            <div className="mt-2 font-mono text-sm">
                              {cond.observed_value?.toFixed(1)} {cond.passed ? <span className="text-status-green">✓</span> : <span className="text-status-red">✗</span>}
                            </div>
                            <div className="mt-1 font-mono text-[10px] text-text-secondary">Expected: {cond.expected}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                )}

                {remediation && (
                  <Card className="p-6 border-status-blue/30 bg-status-blue/5">
                    <h3 className="text-lg font-bold text-white mb-2">Remediation Applied</h3>
                    <p className="text-sm text-text-primary mb-4">{remediation.title}</p>
                    
                    {remediation.diff && (
                      <div className="mb-4">
                        <DiffBlock diff={remediation.diff} />
                      </div>
                    )}

                    {remediation.validation_status === "VALIDATED" && (
                      <div className="rounded border border-status-green/20 bg-status-green/10 p-3 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-status-green" />
                        <span className="text-sm font-medium text-status-green">{remediation.validation_detail || "Post-fix metrics within healthy baseline"}</span>
                      </div>
                    )}
                  </Card>
                )}
              </div>
            </section>
          )}

          {/* TELEMETRY */}
          <section>
            <SectionHeader title="Observed Telemetry" icon={Activity} description="Live state of the digital twin during experimentation." />
            {!currentMetrics ? (
               <div className="rounded border border-surface-elevated border-dashed p-8 text-center text-sm text-text-secondary">
                 Collecting evidence and telemetry...
               </div>
            ) : (
              <Card className="p-5">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                  {metricCards.map(({ key, label, format }) => {
                    const current = currentMetrics[key];
                    const baseline = baselineMetrics?.[key];
                    let deltaStr;
                    let isPositive = false;
                    
                    if (baseline !== undefined && baseline !== 0) {
                      const diff = current - baseline;
                      const pct = (diff / baseline) * 100;
                      // Determine if it's "good" based on common sense (lower latency/errors is good)
                      isPositive = (key === 'cache_hit_rate' ? diff > 0 : diff < 0);
                      if (Math.abs(pct) > 0.1) {
                        deltaStr = `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`;
                      }
                    }

                    return (
                      <div key={key} className="rounded border border-surface-elevated bg-background/50 p-3 shadow-inner">
                        <DisplayValue 
                          label={label} 
                          value={format(current)} 
                          delta={deltaStr} 
                          previous={baseline ? format(baseline) : undefined}
                          isPositive={isPositive}
                        />
                      </div>
                    );
                  })}
                </div>
              </Card>
            )}
          </section>

        </div>

        {/* SIDEBAR */}
        <aside className="space-y-6">
          <section>
            <SectionHeader title="Evidence" icon={FileSearch} />
            <div className="space-y-3">
              {evidenceToShow.map((evidence) => (
                <Card key={evidence.id} className="p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-mono text-[10px] uppercase tracking-wider text-brand">{evidence.type}</span>
                    <span className="font-mono text-[10px] text-text-secondary">{Math.round(evidence.strength * 100)}% str</span>
                  </div>
                  <p className="text-sm text-text-primary leading-relaxed">{evidence.observation}</p>
                </Card>
              ))}
            </div>
            {incident.evidence.length > 4 && (
              <button 
                onClick={() => setEvidenceExpanded(!evidenceExpanded)} 
                className="mt-4 flex w-full items-center justify-center gap-2 rounded border border-surface-elevated py-2 text-xs font-semibold text-text-secondary transition-colors hover:bg-surface-elevated hover:text-white"
              >
                {evidenceExpanded ? <><ChevronUp className="h-4 w-4" /> Show less</> : <><ChevronDown className="h-4 w-4" /> Show {incident.evidence.length - 4} more</>}
              </button>
            )}
          </section>

          <section className="pt-4 border-t border-surface-elevated">
            <SectionHeader title="Audit Timeline" icon={Database} />
            <div className="relative space-y-4 before:absolute before:inset-0 before:ml-2 before:w-px before:bg-surface-elevated">
              {incident.timeline.map((event) => (
                <div key={event.id} className="relative pl-6">
                  <div className="absolute left-0 top-1.5 h-4 w-4 rounded-full border-4 border-background bg-surface-elevated" />
                  <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-brand">{event.event_type}</div>
                  <p className="text-sm font-medium text-white">{event.title}</p>
                  {event.description && <p className="mt-1 text-xs text-text-secondary leading-relaxed">{event.description}</p>}
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
