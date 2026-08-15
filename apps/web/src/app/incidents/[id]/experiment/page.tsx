"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, FlaskConical, ShieldCheck } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ReactFlow, Controls, Background, MarkerType, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

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
  const [activeAction, setActiveAction] = useState<string | null>(null);
  
  const refresh = useCallback(async () => {
    try { setIncident(await api.getIncident(params.id)); setError(null); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load experiment."); }
  }, [params.id]);
  
  useEffect(() => { 
    void refresh(); 
    const es = api.subscribeToEvents(params.id, () => void refresh());
    return () => es.close();
  }, [params.id, refresh]);

  const runAction = async (action: string, operation: () => Promise<unknown>) => {
    setActiveAction(action);
    try {
      await operation();
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Experiment action failed.");
    } finally {
      setActiveAction(null);
    }
  };

  if (error) return <main className="p-8 text-sm text-status-red">{error}</main>;
  if (!incident) return <main className="p-8 font-mono text-sm text-text-secondary">Loading experiment artifacts…</main>;
  
  const experiments = incident.experiments;
  if (experiments.length === 0) return <main className="p-8"><Link className="text-brand underline" href={`/incidents/${params.id}`}>Return to the command center</Link><p className="mt-4 text-text-secondary">No backend experiment has been designed yet.</p></main>;

  return (
    <main className="mx-auto max-w-7xl p-6 md:p-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">IncidentForge / experiment lab</p>
          <h1 className="mt-2 text-3xl font-bold">Causal experiment record</h1>
        </div>
        <Link href={`/incidents/${params.id}`} className="text-sm text-brand hover:underline">Command center</Link>
      </div>

      <div className="space-y-12">
        {experiments.map((experiment, idx) => {
          const target = incident.hypotheses.find((h) => h.id === experiment.target_hypothesis);
          const critique = incident.critiques.find((c) => c.hypothesis_id === experiment.target_hypothesis);
          const observation = incident.observations.find((o) => o.experiment_id === experiment.id);
          const verification = incident.verifications.find((v) => v.experiment_id === experiment.id);
          
          const chartData = verification?.conditions.map(c => ({
            name: c.metric,
            Baseline: c.baseline_value,
            Observed: c.observed_value
          })) || [];

          const leadingHypothesis = target?.statement
            ? target.statement.length > 60 ? target.statement.slice(0, 57) + '…' : target.statement
            : 'HYPOTHESIS';
          const criticLabel = critique ? `${critique.objections.length} objection${critique.objections.length !== 1 ? 's' : ''}` : 'CRITIC OBJECTION';
          const interventionLabel = experiment.intervention.type || 'INTERVENTION';
          const expectedLabel = `${experiment.expected_conditions.length} expected condition${experiment.expected_conditions.length !== 1 ? 's' : ''}`;
          const baselineP95 = observation?.baseline?.p95_latency;
          const beforeLabel = baselineP95 != null ? `P95: ${baselineP95.toFixed(1)} ms` : 'BEFORE METRICS';
          const experimentLabel = experiment.status === 'validated' ? 'Ready to execute' : experiment.status;
          const afterP95 = observation?.post_intervention?.p95_latency;
          const afterLabel = afterP95 != null ? `P95: ${afterP95.toFixed(1)} ms` : 'AFTER METRICS';
          const verificationOutcome = verification?.outcome;
          const verificationLabel = verificationOutcome ?? 'VERIFICATION';
          const confidenceLabel = target ? `${Math.round(target.score * 100)}%` : 'CONFIDENCE UPDATE';

          const defaultNodeStyle = { background: '#1c212b', color: '#fff', border: '1px solid #2a3241' };
          const verificationNodeStyle = verificationOutcome === 'VERIFIED'
            ? { background: '#166534', color: '#fff', border: '1px solid #22c55e' }
            : verificationOutcome === 'REJECTED'
              ? { background: '#991b1b', color: '#fff', border: '1px solid #ef4444' }
              : verificationOutcome === 'INCONCLUSIVE'
                ? { background: '#92400e', color: '#fff', border: '1px solid #f59e0b' }
                : defaultNodeStyle;

          const flowNodes: Node[] = [
            { id: 'hyp', position: { x: 50, y: 50 }, data: { label: leadingHypothesis }, style: defaultNodeStyle },
            { id: 'crit', position: { x: 300, y: 50 }, data: { label: criticLabel }, style: defaultNodeStyle },
            { id: 'int', position: { x: 550, y: 50 }, data: { label: interventionLabel }, style: defaultNodeStyle },
            { id: 'exp', position: { x: 50, y: 150 }, data: { label: expectedLabel }, style: defaultNodeStyle },
            { id: 'bef', position: { x: 300, y: 150 }, data: { label: beforeLabel }, style: defaultNodeStyle },
            { id: 'run', position: { x: 550, y: 150 }, data: { label: experimentLabel }, style: defaultNodeStyle },
            { id: 'aft', position: { x: 50, y: 250 }, data: { label: afterLabel }, style: defaultNodeStyle },
            { id: 'ver', position: { x: 300, y: 250 }, data: { label: verificationLabel }, style: verificationNodeStyle },
            { id: 'conf', position: { x: 550, y: 250 }, data: { label: confidenceLabel }, style: defaultNodeStyle },
          ];

          const flowEdges: Edge[] = [
            { id: 'e1', source: 'hyp', target: 'crit', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
            { id: 'e2', source: 'crit', target: 'int', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
            { id: 'e3', source: 'int', target: 'exp', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
            { id: 'e4', source: 'exp', target: 'bef', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
            { id: 'e5', source: 'bef', target: 'run', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
            { id: 'e6', source: 'run', target: 'aft', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
            { id: 'e7', source: 'aft', target: 'ver', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
            { id: 'e8', source: 'ver', target: 'conf', animated: true, style: { stroke: '#e8a915' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#e8a915' } },
          ];

          return (
            <div key={experiment.id} className="border border-surface-elevated rounded-lg p-6 bg-surface mb-10">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-bold">Experiment {idx + 1}: {experiment.intervention.type}</h2>
                <div className="flex flex-wrap gap-2">
                  {!critique && (
                    <button
                      onClick={() => void runAction(`challenge-${experiment.id}`, () => api.challengeHypothesis(experiment.target_hypothesis))}
                      disabled={activeAction !== null}
                      className="rounded border border-brand px-3 py-2 text-xs font-bold text-brand disabled:opacity-50"
                    >
                      {activeAction === `challenge-${experiment.id}` ? "Challenging…" : "Run critic"}
                    </button>
                  )}
                  {experiment.status === "proposed" && (
                    <button
                      onClick={() => void runAction(`validate-${experiment.id}`, () => api.validateExperiment(experiment.id))}
                      disabled={activeAction !== null}
                      className="rounded border border-brand px-3 py-2 text-xs font-bold text-brand disabled:opacity-50"
                    >
                      {activeAction === `validate-${experiment.id}` ? "Validating…" : "Validate safety"}
                    </button>
                  )}
                  {experiment.status === "validated" && (
                    <button
                      onClick={() => void runAction(`execute-${experiment.id}`, () => api.executeExperiment(experiment.id))}
                      disabled={activeAction !== null}
                      className="rounded bg-brand px-3 py-2 text-xs font-bold text-background disabled:opacity-50"
                    >
                      {activeAction === `execute-${experiment.id}` ? "Executing…" : "Execute in Digital Twin"}
                    </button>
                  )}
                  {experiment.status === "rejected" && (
                    <button
                      onClick={() => void runAction(`redesign-${experiment.id}`, () => api.designExperiment(experiment.target_hypothesis))}
                      disabled={activeAction !== null}
                      className="rounded border border-brand px-3 py-2 text-xs font-bold text-brand disabled:opacity-50"
                    >
                      {activeAction === `redesign-${experiment.id}` ? "Designing…" : "Design replacement"}
                    </button>
                  )}
                </div>
              </div>
              
              <div className="h-80 w-full mb-8 border border-surface-elevated rounded">
                <ReactFlow nodes={flowNodes} edges={flowEdges} fitView>
                  <Background color="#2a3241" gap={16} />
                  <Controls />
                </ReactFlow>
              </div>

              <div className="grid gap-6 lg:grid-cols-2 mb-8">
                <article className="rounded border border-surface-elevated bg-background p-6">
                  <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Hypothesis & Critiques</h3>
                  <p className="mt-4 text-sm font-medium">{target?.statement}</p>
                  {critique && (
                    <div className="mt-4 space-y-2">
                      <p className="text-xs text-brand font-mono">OBJECTIONS:</p>
                      {critique.objections.map((obj, i) => <p key={i} className="text-sm text-text-secondary">- {obj}</p>)}
                      <p className="text-xs text-brand font-mono mt-4">FALSIFICATION CRITERIA:</p>
                      {critique.falsification_criteria.map((fc, i) => <p key={i} className="text-sm text-text-secondary">- {fc}</p>)}
                    </div>
                  )}
                </article>
                <article className="rounded border border-surface-elevated bg-background p-6">
                  <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Prediction contract</h3>
                  <div className="mt-4 space-y-3">
                    {experiment.expected_conditions.map((condition) => (
                      <div key={condition.metric} className="flex justify-between gap-4 rounded border border-surface-elevated p-3 text-sm">
                        <span>{condition.metric}</span>
                        <span className="font-mono text-brand">{condition.direction} ≥ {condition.threshold_percentage}%</span>
                      </div>
                    ))}
                  </div>
                </article>
              </div>

              {observation && verification && (
                <div className="mb-8 space-y-8">
                  <div className="rounded border border-surface-elevated bg-background p-6">
                    <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                      <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Metrics Comparison (Bar Chart)</h3>
                    </div>
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2a3241" />
                          <XAxis dataKey="name" stroke="#a0aabf" fontSize={12} />
                          <YAxis stroke="#a0aabf" fontSize={12} />
                          <Tooltip contentStyle={{ backgroundColor: '#1c212b', borderColor: '#2a3241', color: '#fff' }} />
                          <Legend />
                          <Bar dataKey="Baseline" fill="#a0aabf" />
                          <Bar dataKey="Observed" fill="#e8a915" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="rounded border border-surface-elevated bg-background p-6">
                    <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                      <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Detailed Metrics Table</h3>
                      <VerificationBadge result={verification.outcome} />
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[540px] text-left text-sm">
                        <thead className="border-b border-surface-elevated font-mono text-xs uppercase text-text-secondary">
                          <tr><th className="pb-3">Metric</th><th className="pb-3">Baseline</th><th className="pb-3">Observed</th><th className="pb-3">Expected</th><th className="pb-3">Result</th></tr>
                        </thead>
                        <tbody>
                          {verification.conditions.map((condition) => (
                            <tr key={condition.metric} className="border-b border-surface-elevated last:border-0">
                              <td className="py-3 font-mono">{condition.metric}</td>
                              <td className="py-3"><MetricValue metric={condition.metric} value={condition.baseline_value} /></td>
                              <td className="py-3"><MetricValue metric={condition.metric} value={condition.observed_value} /></td>
                              <td className="py-3 text-text-secondary">{condition.expected}</td>
                              <td className={`py-3 font-mono text-xs ${condition.passed ? "text-status-green" : "text-status-red"}`}>{condition.passed ? "PASS" : "FAIL"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <p className="mt-5 text-sm text-text-secondary">{verification.explanation}</p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {incident.remediation && (
        <section className="mt-8 rounded border border-status-green/30 bg-status-green/5 p-6">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-status-green">Remediation {incident.remediation.validation_status}</p>
          <h2 className="mt-2 text-xl font-bold">{incident.remediation.title}</h2>
          <p className="mt-2 text-sm text-text-secondary">{incident.remediation.description}</p>
          {incident.remediation.diff && <pre className="mt-4 overflow-x-auto rounded border border-surface-elevated bg-background p-4 text-xs text-text-secondary">{incident.remediation.diff}</pre>}
          {incident.remediation.validation_detail && <p className="mt-4 text-sm text-status-green">{incident.remediation.validation_detail}</p>}
        </section>
      )}
    </main>
  );
}
