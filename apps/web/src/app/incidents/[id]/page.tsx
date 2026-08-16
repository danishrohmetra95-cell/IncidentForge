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
      <div className="flex items-center gap-3 text-text-secondary">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
        <span className="font-mono text-[11px] uppercase tracking-wider">Synchronizing state...</span>
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
    <main className="mx-auto w-full max-w-[1400px] p-6 lg:p-8 animate-in fade-in duration-300">
      
      {/* Top Hero Card */}
      <Card className="mb-6 p-5">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <span className="font-mono text-[10px] uppercase text-text-secondary ml-1">
                {incident.reasoning_mode === "live_model" ? "Live Mode" : "Deterministic Mode"}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">{incident.title}</h1>
            <div className="mt-2 flex items-center gap-3 font-mono text-[11px] text-text-secondary">
              <span className="flex items-center gap-1"><Server className="h-3 w-3" />{incident.service}</span>
              <span className="text-surface-elevated">•</span>
              <span>ID: {incident.id}</span>
            </div>
          </div>
          
          <div className="flex flex-wrap items-start gap-2">
            {experiment && (
              <Link href={`/incidents/${incident.id}/experiment`} className="flex items-center gap-1.5 rounded bg-surface-elevated px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-surface-elevated/80 transition-colors">
                <Beaker className="h-3.5 w-3.5 text-brand" /> Experiment Lab
              </Link>
            )}
            {incident.experiments && incident.experiments.length > 0 && (
              <Link href={`/incidents/${incident.id}/counterfactual`} className="flex items-center gap-1.5 rounded bg-surface-elevated px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-surface-elevated/80 transition-colors">
                <GitBranch className="h-3.5 w-3.5 text-brand" /> Counterfactual
              </Link>
            )}
          </div>
        </div>
      </Card>

      {/* Telemetry Row */}
      {!currentMetrics ? (
        <div className="mb-6 rounded border border-surface-elevated border-dashed p-4 text-center text-[12px] text-text-secondary">
          Awaiting telemetry snapshot...
        </div>
      ) : (
        <div className="mb-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {metricCards.map(({ key, label, format }) => {
            const current = currentMetrics[key];
            const baseline = baselineMetrics?.[key];
            let deltaStr;
            let isPositive = false;
            
            if (baseline !== undefined && baseline !== 0) {
              const diff = current - baseline;
              const pct = (diff / baseline) * 100;
              isPositive = (key === 'cache_hit_rate' ? diff > 0 : diff < 0);
              if (Math.abs(pct) > 0.1) {
                deltaStr = `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`;
              }
            }

            return (
              <Card key={key} className="p-3 bg-background/50">
                <DisplayValue 
                  label={label} 
                  value={format(current)} 
                  delta={deltaStr} 
                  isPositive={isPositive}
                />
              </Card>
            );
          })}
        </div>
      )}

      {/* Main 2-Column Layout */}
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        
        {/* LEFT COLUMN: Reasoning */}
        <div className="space-y-6">
          
          <section>
            <SectionHeader title="Competing Hypotheses" icon={Network} />
            <div className="grid gap-3">
              {sortedHypotheses.map((hypothesis, index) => {
                const isLeading = index === 0;
                const isVerified = hypothesis.status === "VERIFIED";
                const isRejected = hypothesis.status === "REJECTED";
                
                return (
                  <Card key={hypothesis.id} className={`p-4 transition-all duration-300 ${isVerified ? 'border-status-green/30 bg-status-green/5 shadow-[0_0_12px_rgba(34,197,94,0.05)]' : isRejected ? 'opacity-60' : isLeading ? 'border-brand/30 bg-brand/5 shadow-[0_0_12px_rgba(245,158,11,0.05)]' : 'bg-background/30'}`}>
                    <div className="flex items-start gap-3">
                      <span className={`font-mono text-[11px] font-bold ${isVerified ? 'text-status-green' : isLeading ? 'text-brand' : 'text-text-secondary'}`}>
                        #{index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <h2 className="text-[14px] font-semibold text-text-primary mb-2 leading-tight">{hypothesis.statement}</h2>
                        <div className="flex items-center gap-3 font-mono text-[10px]">
                          <div className="flex-1 h-1 bg-surface-elevated rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${isVerified ? 'bg-status-green' : isLeading ? 'bg-brand' : 'bg-text-secondary'}`} 
                              style={{ width: `${Math.max(2, hypothesis.score * 100)}%` }} 
                            />
                          </div>
                          <span className={`w-8 text-right font-bold ${isVerified ? 'text-status-green' : isLeading ? 'text-brand' : 'text-text-primary'}`}>
                            {Math.round(hypothesis.score * 100)}%
                          </span>
                          <span className="text-surface-elevated">•</span>
                          <span className={`px-1.5 py-0.5 rounded font-bold uppercase ${isVerified ? 'bg-status-green/20 text-status-green' : isRejected ? 'bg-status-red/20 text-status-red' : 'bg-surface-elevated text-text-secondary'}`}>
                            {hypothesis.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          </section>

          {critic && (
            <section>
              <Card className="border-status-amber/20 bg-status-amber/5 p-4 flex gap-3">
                <ShieldCheck className="h-4 w-4 text-status-amber shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-mono text-[10px] uppercase tracking-wider text-status-amber mb-1">Adversarial Critic</h4>
                  <p className="text-[13px] text-text-primary leading-relaxed mb-3">{critic.objections}</p>
                  <div className="border-l-2 border-status-amber/30 pl-3">
                    <span className="block font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-0.5">Falsification Criteria</span>
                    <p className="text-[12px] text-text-primary">{critic.falsification_criteria}</p>
                  </div>
                </div>
              </Card>
            </section>
          )}

          {(verification || remediation) && (
            <section>
              <SectionHeader title="Verification & Resolution" icon={CheckCircle2} />
              <div className="space-y-3">
                {verification && (
                  <Card className={`p-4 ${verification.outcome === 'VERIFIED' ? 'border-status-green/30 bg-status-green/5' : 'border-status-red/30 bg-status-red/5'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      {verification.outcome === 'VERIFIED' ? <CheckCircle2 className="h-4 w-4 text-status-green" /> : <XCircle className="h-4 w-4 text-status-red" />}
                      <span className="font-mono text-[11px] font-bold uppercase">{verification.outcome}</span>
                    </div>
                    <p className="text-[13px] text-text-primary mb-4">{verification.explanation}</p>
                    
                    {verification.conditions && verification.conditions.length > 0 && (
                      <div className="grid grid-cols-2 gap-2">
                        {verification.conditions.map((cond, i) => (
                          <div key={i} className="flex items-center justify-between rounded bg-background/50 px-2 py-1.5 border border-surface-elevated">
                            <span className="font-mono text-[10px] text-text-secondary">{cond.metric}</span>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[11px]">{cond.observed_value?.toFixed(1)}</span>
                              {cond.passed ? <CheckCircle2 className="h-3 w-3 text-status-green" /> : <XCircle className="h-3 w-3 text-status-red" />}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                )}

                {remediation && (
                  <Card className="p-4 border-status-blue/20 bg-status-blue/5">
                    <span className="font-mono text-[10px] uppercase tracking-wider text-status-blue mb-1 block">Remediation Applied</span>
                    <p className="text-[13px] font-medium text-white mb-3">{remediation.title}</p>
                    {remediation.diff && <DiffBlock diff={remediation.diff} />}
                  </Card>
                )}
              </div>
            </section>
          )}

        </div>

        {/* RIGHT COLUMN: Evidence & Timeline */}
        <div className="space-y-6">
          <section>
            <SectionHeader title="Evidence Context" icon={FileSearch} />
            <div className="space-y-2">
              {evidenceToShow.map((evidence) => (
                <Card key={evidence.id} className="p-3 bg-background/50">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-[9px] uppercase tracking-wider text-brand">{evidence.type}</span>
                    <span className="font-mono text-[9px] text-text-secondary">{Math.round(evidence.strength * 100)}% conf</span>
                  </div>
                  <p className="text-[12px] text-text-primary leading-snug">{evidence.observation}</p>
                </Card>
              ))}
            </div>
            {incident.evidence.length > 4 && (
              <button 
                onClick={() => setEvidenceExpanded(!evidenceExpanded)} 
                className="mt-2 w-full rounded border border-surface-elevated py-1.5 text-[11px] font-medium text-text-secondary hover:bg-surface-elevated/50 hover:text-white transition-colors"
              >
                {evidenceExpanded ? "Show less" : `+ ${incident.evidence.length - 4} more`}
              </button>
            )}
          </section>

          <section>
            <SectionHeader title="Activity Feed" icon={Database} />
            <Card className="p-3 bg-background/50">
              <div className="space-y-3">
                {incident.timeline.map((event) => (
                  <div key={event.id} className="flex gap-3 text-[12px]">
                    <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                    <div>
                      <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary block mb-0.5">{event.event_type}</span>
                      <span className="text-text-primary">{event.title}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        </div>

      </div>
    </main>
  );
}
