"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { ArrowDown, CheckCircle2, CircleAlert, FlaskConical, ShieldCheck } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentDetail } from "@/lib/types";
import { VerificationBadge } from "@/components/Badges";

function MetricValue({ value, metric }: { value: number; metric: string }) {
  const percentage = ["error_rate", "db_utilization", "cache_hit_rate", "cpu", "memory"].includes(metric);
  return <span className="font-mono">{percentage ? `${(value * 100).toFixed(1)}%` : value.toFixed(metric.includes("latency") ? 1 : 0)}</span>;
}

export default function ExperimentLab({ params }: { params: { id: string } }) {
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const refresh = useCallback(async () => {
    try { setIncident(await api.getIncident(params.id)); setError(null); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load experiment."); }
  }, [params.id]);
  useEffect(() => { void refresh(); }, [refresh]);

  if (error) return <main className="p-8 text-sm text-status-red">{error}</main>;
  if (!incident) return <main className="p-8 font-mono text-sm text-text-secondary">Loading experiment artifacts…</main>;
  const experiment = incident.experiments.at(-1);
  if (!experiment) return <main className="p-8"><Link className="text-brand underline" href={`/incidents/${params.id}`}>Return to the command center</Link><p className="mt-4 text-text-secondary">No backend experiment has been designed yet.</p></main>;
  const target = incident.hypotheses.find((hypothesis) => hypothesis.id === experiment.target_hypothesis);
  const critique = incident.critiques.find((item) => item.hypothesis_id === experiment.target_hypothesis);
  const observation = incident.observations.find((item) => item.experiment_id === experiment.id);
  const verification = incident.verifications.find((item) => item.experiment_id === experiment.id);

  return <main className="mx-auto max-w-6xl p-6 md:p-10">
    <div className="mb-8 flex items-center justify-between"><div><p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">IncidentForge / experiment lab</p><h1 className="mt-2 text-3xl font-bold">Causal experiment record</h1></div><Link href={`/incidents/${params.id}`} className="text-sm text-brand hover:underline">Command center</Link></div>

    <section className="grid gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] md:items-stretch">
      <Stage title="Hypothesis" icon={<CircleAlert className="h-4 w-4" />}><p>{target?.statement ?? "Unknown hypothesis"}</p></Stage><ArrowDown className="m-auto h-5 w-5 rotate-[-90deg] text-brand" />
      <Stage title="Adversarial critic" icon={<ShieldCheck className="h-4 w-4" />}><p>{critique?.objections[0] ?? "Critique pending"}</p></Stage><ArrowDown className="m-auto h-5 w-5 rotate-[-90deg] text-brand" />
      <Stage title="Registered intervention" icon={<FlaskConical className="h-4 w-4" />}><p className="font-mono text-brand">{experiment.intervention.type}</p><p className="mt-1 text-xs text-text-secondary">Target: {experiment.intervention.target}</p></Stage><ArrowDown className="m-auto h-5 w-5 rotate-[-90deg] text-brand" />
      <Stage title="Verifier" icon={<CheckCircle2 className="h-4 w-4" />}><p>{verification ? <VerificationBadge result={verification.outcome} /> : "Awaiting observation"}</p></Stage>
    </section>

    <section className="mt-8 grid gap-6 lg:grid-cols-2">
      <article className="rounded border border-surface-elevated bg-surface p-6"><h2 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Prediction contract</h2><div className="mt-4 space-y-3">{experiment.expected_conditions.map((condition) => <div key={condition.metric} className="flex justify-between gap-4 rounded border border-surface-elevated p-3 text-sm"><span>{condition.metric}</span><span className="font-mono text-brand">{condition.direction} ≥ {condition.threshold_percentage}%</span></div>)}</div><p className="mt-4 text-sm text-text-secondary">Controls: request load is held by the scenario; observation window: {experiment.observation_window_seconds}s.</p></article>
      <article className="rounded border border-surface-elevated bg-surface p-6"><h2 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Falsification condition</h2><p className="mt-4 text-sm text-text-secondary">{critique?.falsification_criteria[0] ?? "No critique is available."}</p><h3 className="mt-6 font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Alternative explanation</h3><p className="mt-3 text-sm text-text-secondary">{critique?.alternatives[0] ?? "No alternative was recorded."}</p></article>
    </section>

    {observation && verification && <section className="mt-8 rounded border border-surface-elevated bg-surface p-6"><div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Measured before / after</h2><VerificationBadge result={verification.outcome} /></div><div className="overflow-x-auto"><table className="w-full min-w-[540px] text-left text-sm"><thead className="border-b border-surface-elevated font-mono text-xs uppercase text-text-secondary"><tr><th className="pb-3">Metric</th><th className="pb-3">Baseline</th><th className="pb-3">Observed</th><th className="pb-3">Expected</th><th className="pb-3">Result</th></tr></thead><tbody>{verification.conditions.map((condition) => <tr key={condition.metric} className="border-b border-surface-elevated last:border-0"><td className="py-3 font-mono">{condition.metric}</td><td className="py-3"><MetricValue metric={condition.metric} value={condition.baseline_value} /></td><td className="py-3"><MetricValue metric={condition.metric} value={condition.observed_value} /></td><td className="py-3 text-text-secondary">{condition.expected}</td><td className={`py-3 font-mono text-xs ${condition.passed ? "text-status-green" : "text-status-red"}`}>{condition.passed ? "PASS" : "FAIL"}</td></tr>)}</tbody></table></div><p className="mt-5 text-sm text-text-secondary">{verification.explanation}</p></section>}

    {incident.remediation && <section className="mt-8 rounded border border-status-green/30 bg-status-green/5 p-6"><p className="font-mono text-xs uppercase tracking-[0.18em] text-status-green">Post-fix replay {incident.remediation.validation_status}</p><h2 className="mt-2 text-xl font-bold">{incident.remediation.title}</h2><p className="mt-2 text-sm text-text-secondary">{incident.remediation.description}</p>{incident.remediation.diff && <pre className="mt-4 overflow-x-auto rounded border border-surface-elevated bg-background p-4 text-xs text-text-secondary">{incident.remediation.diff}</pre>}</section>}
  </main>;
}

function Stage({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return <article className="min-h-36 rounded border border-surface-elevated bg-surface p-4"><div className="mb-3 flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-brand">{icon}{title}</div><div className="text-sm text-text-secondary">{children}</div></article>;
}
