"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ReactFlow, Background, Controls, Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ArrowLeft, Beaker, CheckCircle2, ShieldAlert, FileText, FlaskConical, Target, Database } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentDetail } from "@/lib/types";
import { VerificationBadge } from "@/components/Badges";
import { Card, SectionHeader, DiffBlock } from "@/components/UI";

function MetricValue({ metric, value }: { metric: string; value: number }) {
  if (metric === "error_rate" || metric === "cache_hit_rate" || metric === "cpu" || metric === "db_utilization") return <span>{(value * 100).toFixed(1)}%</span>;
  if (metric === "p95_latency") return <span>{value.toFixed(1)} ms</span>;
  return <span>{value.toFixed(0)}</span>;
}

export default function ExperimentLab({ params }: { params: { id: string } }) {
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIncident(await api.getIncident(params.id));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load incident.");
    }
  }, [params.id]);

  useEffect(() => {
    void loadData();
    const es = api.subscribeToEvents(params.id, () => void loadData());
    return () => es.close();
  }, [params.id, loadData]);

  const runAction = async (key: string, fn: () => Promise<unknown>) => {
    setActiveAction(key);
    try { await fn(); await loadData(); }
    catch (err) { alert(err instanceof Error ? err.message : "Action failed"); }
    finally { setActiveAction(null); }
  };

  if (error) return <main className="p-8 text-[13px] text-status-red flex items-center gap-2"><ShieldAlert className="h-4 w-4" />{error}</main>;
  if (!incident) return (
    <main className="flex h-[50vh] items-center justify-center p-8">
      <div className="flex items-center gap-3 text-text-secondary">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
        <span className="font-mono text-[11px] uppercase tracking-wider">Loading Experiment Lab...</span>
      </div>
    </main>
  );

  return (
    <main className="mx-auto w-full max-w-[1400px] p-6 lg:p-8 animate-in fade-in duration-300">
      <header className="mb-6">
        <div className="mb-4">
          <Link href={`/incidents/${params.id}`} className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-text-secondary hover:text-white transition-colors">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Command Center
          </Link>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <Beaker className="h-4 w-4 text-brand" />
          <span className="font-mono text-[10px] uppercase tracking-wider text-brand">Digital Twin Operations</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Experiment Lab</h1>
      </header>

      {!incident.experiments || incident.experiments.length === 0 ? (
        <Card className="p-12 text-center text-[13px] text-text-secondary flex flex-col items-center">
          <FlaskConical className="h-8 w-8 mb-3 opacity-50" />
          No experiments have been designed for this incident yet.
        </Card>
      ) : (
        <div className="space-y-6">
          {incident.experiments.map((experiment, idx) => {
            const target = incident.hypotheses.find(h => h.id === experiment.target_hypothesis);
            const critique = incident.critiques?.find(c => c.hypothesis_id === experiment.target_hypothesis);
            const observation = incident.observations.find(o => o.experiment_id === experiment.id);
            const verification = incident.verifications.find(v => v.experiment_id === experiment.id);

            const flowNodes: Node[] = [
              { id: 'hyp', type: 'default', position: { x: 50, y: 50 }, draggable: false, connectable: false, selectable: false, data: { label: 'Hypothesis' }, style: { background: 'rgba(42, 50, 65, 0.9)', color: '#a0aabf', border: '1px solid rgba(76, 86, 106, 0.5)', borderRadius: '8px', fontSize: '11px', padding: '8px 12px', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' } },
              { id: 'crit', type: 'default', position: { x: 50, y: 130 }, draggable: false, connectable: false, selectable: false, data: { label: 'Critic' }, style: { background: 'rgba(42, 50, 65, 0.9)', color: '#d08770', border: '1px solid rgba(208, 135, 112, 0.4)', borderRadius: '8px', fontSize: '11px', padding: '8px 12px', boxShadow: '0 0 12px rgba(208, 135, 112, 0.1) inset' } },
              { id: 'intv', type: 'default', position: { x: 250, y: 50 }, draggable: false, connectable: false, selectable: false, data: { label: 'Intervention' }, style: { background: 'rgba(232, 169, 21, 0.1)', color: '#e8a915', border: '1px solid rgba(232, 169, 21, 0.3)', fontWeight: 'bold', borderRadius: '8px', fontSize: '11px', padding: '8px 12px', boxShadow: '0 0 16px rgba(232, 169, 21, 0.1) inset' } },
              { id: 'verif', type: 'default', position: { x: 250, y: 160 }, draggable: false, connectable: false, selectable: false, data: { label: verification?.outcome || 'Pending' }, style: { background: verification?.outcome === 'VERIFIED' ? 'rgba(163, 190, 140, 0.15)' : 'rgba(42, 50, 65, 0.9)', color: verification?.outcome === 'VERIFIED' ? '#a3be8c' : '#fff', border: verification?.outcome === 'VERIFIED' ? '1px solid rgba(163, 190, 140, 0.4)' : '1px solid rgba(76, 86, 106, 0.5)', borderRadius: '8px', fontSize: '11px', padding: '8px 12px', boxShadow: verification?.outcome === 'VERIFIED' ? '0 0 16px rgba(163, 190, 140, 0.15) inset, 0 4px 12px rgba(0,0,0,0.2)' : '0 4px 12px rgba(0,0,0,0.2)' } }
            ];
            const flowEdges: Edge[] = [
              { id: 'e1', source: 'hyp', target: 'crit', animated: true, style: { stroke: 'rgba(208, 135, 112, 0.6)', strokeWidth: 1.5 } },
              { id: 'e2', source: 'hyp', target: 'intv', style: { stroke: 'rgba(76, 86, 106, 0.8)', strokeWidth: 1.5 } },
              { id: 'e3', source: 'intv', target: 'verif', animated: experiment.status === 'executed', style: { stroke: experiment.status === 'executed' ? 'rgba(232, 169, 21, 0.6)' : 'rgba(76, 86, 106, 0.8)', strokeWidth: 1.5 } }
            ];

            const chartData = verification ? verification.conditions.map(c => ({
              name: c.metric,
              Baseline: c.baseline_value,
              Observed: c.observed_value
            })) : [];

            return (
              <div key={experiment.id} className="space-y-6">
                
                {/* Hero Card */}
                <Card className="p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-surface-elevated">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center h-8 w-8 rounded bg-surface-elevated font-mono text-[12px] text-text-secondary font-bold">
                      {idx + 1}
                    </div>
                    <div>
                      <h2 className="text-[15px] font-bold text-white">{experiment.intervention.type}</h2>
                      <p className="text-[11px] font-mono text-text-secondary mt-0.5">Target: {experiment.target_hypothesis}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] uppercase text-text-secondary border border-surface-elevated px-2 py-1 rounded bg-background">
                      {experiment.status}
                    </span>
                    {experiment.status === "designed" && (
                      <button onClick={() => void runAction(`validate-${experiment.id}`, () => api.validateExperiment(experiment.id))} disabled={activeAction !== null} className="rounded bg-brand px-3 py-1.5 text-[11px] font-bold text-background hover:bg-brand/90 transition-colors disabled:opacity-50">
                        {activeAction === `validate-${experiment.id}` ? "Validating..." : "Validate Safety"}
                      </button>
                    )}
                    {experiment.status === "validated" && (
                      <button onClick={() => void runAction(`execute-${experiment.id}`, () => api.executeExperiment(experiment.id))} disabled={activeAction !== null} className="rounded bg-brand px-3 py-1.5 text-[11px] font-bold text-background hover:bg-brand/90 transition-colors disabled:opacity-50">
                        {activeAction === `execute-${experiment.id}` ? "Executing..." : "Execute in Digital Twin"}
                      </button>
                    )}
                    {experiment.status === "rejected" && (
                      <button onClick={() => void runAction(`redesign-${experiment.id}`, () => api.designExperiment(experiment.target_hypothesis))} disabled={activeAction !== null} className="rounded border border-surface-elevated px-3 py-1.5 text-[11px] font-bold text-text-primary hover:bg-surface-elevated/50 transition-colors disabled:opacity-50">
                        {activeAction === `redesign-${experiment.id}` ? "Designing..." : "Design Replacement"}
                      </button>
                    )}
                  </div>
                </Card>

                {/* 2-Column Reasoning Graph & Summary */}
                <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr] items-stretch">
                  <Card className="h-full min-h-[320px] overflow-hidden p-0 relative border-surface-elevated flex flex-col">
                    <div className="absolute top-3 left-3 z-10 font-mono text-[9px] uppercase tracking-wider text-text-secondary bg-background/80 px-2 py-1 rounded">Reasoning Graph</div>
                    <div className="flex-1 w-full h-full relative">
                      <ReactFlow 
                        nodes={flowNodes} 
                        edges={flowEdges} 
                        fitView 
                        attributionPosition="bottom-right"
                        nodesDraggable={false}
                        nodesConnectable={false}
                        elementsSelectable={false}
                        nodesFocusable={false}
                        edgesFocusable={false}
                        edgesReconnectable={false}
                      >
                        <Background color="#2a3241" gap={16} size={1} />
                        <Controls showInteractive={false} className="opacity-50" />
                      </ReactFlow>
                    </div>
                  </Card>
                  
                  <Card className="h-full min-h-[320px] p-5 bg-background/50 border-surface-elevated flex flex-col">
                    <SectionHeader title="Experiment Summary" icon={FileText} />
                    <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2">
                      <div>
                        <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-1.5 block">Hypothesis</span>
                        <p className="text-[13px] font-medium text-text-primary leading-snug bg-surface/30 p-2.5 rounded border border-surface-elevated">{target?.statement}</p>
                      </div>
                      <div>
                        <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-1.5 block">Falsification Check</span>
                        <p className="text-[12px] text-text-primary leading-snug bg-surface/30 p-2.5 rounded border border-surface-elevated border-l-status-amber/50">{critique?.falsification_criteria[0] || "No criteria available"}</p>
                      </div>
                      <div>
                        <span className="font-mono text-[9px] uppercase tracking-wider text-brand mb-1.5 block">Expected Conditions</span>
                        <div className="space-y-1.5">
                          {experiment.expected_conditions.map(cond => (
                            <div key={cond.metric} className="flex justify-between items-center text-[11px] font-mono bg-surface/50 px-2.5 py-1.5 rounded border border-surface-elevated">
                              <span className="text-text-secondary">{cond.metric}</span>
                              <span className="text-white bg-surface-elevated/40 px-1.5 py-0.5 rounded">{cond.direction} {cond.threshold_percentage}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>

                {/* Telemetry Charts */}
                {observation && verification && (
                  <div className="space-y-6">
                    <Card className="p-4 bg-background/50 border-surface-elevated">
                      <SectionHeader title="Before / After Telemetry" icon={Target} />
                      <div className="h-[200px] w-full mt-4">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#2a3241" vertical={false} />
                            <XAxis dataKey="name" stroke="#a0aabf" fontSize={10} tickLine={false} axisLine={false} />
                            <YAxis stroke="#a0aabf" fontSize={10} tickLine={false} axisLine={false} width={40} />
                            <Tooltip contentStyle={{ backgroundColor: '#1c212b', borderColor: '#2a3241', color: '#fff', fontSize: '11px', borderRadius: '4px' }} cursor={{fill: '#2a3241', opacity: 0.4}} />
                            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                            <Bar dataKey="Baseline" fill="#4c566a" radius={[2, 2, 0, 0]} maxBarSize={60} />
                            <Bar dataKey="Observed" fill="#e8a915" radius={[2, 2, 0, 0]} maxBarSize={60} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </Card>

                    <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
                      <Card className="p-4 bg-background/50 border-surface-elevated">
                        <div className="flex items-center justify-between mb-4">
                          <SectionHeader title="Detailed Metrics" icon={Database} />
                          <VerificationBadge result={verification.outcome} />
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-[12px]">
                            <thead className="border-b border-surface-elevated font-mono text-[9px] uppercase text-text-secondary">
                              <tr>
                                <th className="pb-2 font-medium">Metric</th>
                                <th className="pb-2 font-medium">Baseline</th>
                                <th className="pb-2 font-medium">Observed</th>
                                <th className="pb-2 font-medium">Expected</th>
                                <th className="pb-2 font-medium">Result</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-elevated">
                              {verification.conditions.map((condition) => (
                                <tr key={condition.metric}>
                                  <td className="py-2 font-mono text-text-primary">{condition.metric}</td>
                                  <td className="py-2"><MetricValue metric={condition.metric} value={condition.baseline_value} /></td>
                                  <td className="py-2"><MetricValue metric={condition.metric} value={condition.observed_value} /></td>
                                  <td className="py-2 text-text-secondary font-mono text-[10px]">{condition.expected}</td>
                                  <td className={`py-2 font-mono text-[10px] font-bold ${condition.passed ? "text-status-green" : "text-status-red"}`}>
                                    {condition.passed ? "PASS" : "FAIL"}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <p className="mt-4 text-[12px] text-text-secondary leading-relaxed bg-surface p-2.5 rounded border border-surface-elevated">
                          {verification.explanation}
                        </p>
                      </Card>

                      {incident.remediation && (
                        <Card className="p-4 border-status-green/30 bg-status-green/5">
                          <SectionHeader title="Remediation Validated" icon={CheckCircle2} />
                          <h3 className="text-[14px] font-bold text-white mb-1.5">{incident.remediation.title}</h3>
                          <p className="text-[12px] text-text-secondary mb-4 leading-relaxed">{incident.remediation.description}</p>
                          {incident.remediation.diff && (
                            <div className="mb-4">
                              <DiffBlock diff={incident.remediation.diff} />
                            </div>
                          )}
                          <div className="flex items-center gap-1.5 font-medium text-[11px] text-status-green">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            {incident.remediation.validation_detail}
                          </div>
                        </Card>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}
