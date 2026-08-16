"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, ChevronRight, Server, Database, Search, Cpu, ShieldCheck, Beaker, Network, GitBranch, Target, FlaskConical, CheckCircle2, ShieldAlert, Activity } from "lucide-react";
import { ReactFlow, Background, Controls, Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import { api } from "@/lib/api";
import { IncidentSummary, Scenario, IncidentDetail, CounterfactualResult } from "@/lib/types";
import { SeverityBadge, StatusBadge } from "@/components/Badges";
import { Card, SectionHeader, DisplayValue } from "@/components/UI";

export default function Home() {
  const router = useRouter();
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const [activeIncident, setActiveIncident] = useState<IncidentDetail | null>(null);
  const [counterfactual, setCounterfactual] = useState<CounterfactualResult | null>(null);

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
      
      if (incList.length > 0) {
        const latestId = incList[0].id;
        const detail = await api.getIncident(latestId);
        setActiveIncident(detail);
        
        if (detail.experiments && detail.experiments.length > 0) {
          try {
            const cf = await api.getCounterfactual(latestId);
            setCounterfactual(cf);
          } catch {
            setCounterfactual(null);
          }
        }
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

  const renderCockpit = () => {
    if (!activeIncident) return null;

    const observation = activeIncident.observations.at(-1);
    const verification = activeIncident.verifications.at(-1);
    const experiment = activeIncident.experiments.at(-1);
    const remediation = activeIncident.remediation;
    const currentMetrics = observation?.post_intervention ?? observation?.baseline;
    const sortedHypotheses = [...activeIncident.hypotheses].sort((a, b) => b.score - a.score);
    const leadingHypothesis = sortedHypotheses[0];
    const alternativeHypotheses = sortedHypotheses.slice(1, 3);
    const critic = activeIncident.critiques?.find(c => c.hypothesis_id === leadingHypothesis?.id) || activeIncident.critiques?.at(-1);

    const isResolved = activeIncident.status === "RESOLVED";

    // React Flow Config
    const flowNodes: Node[] = [
      { id: 'hyp', position: { x: 50, y: 0 }, data: { label: 'Hypothesis' }, style: { background: 'rgba(28, 33, 43, 0.9)', color: '#a0aabf', border: '1px solid rgba(76, 86, 106, 0.5)', borderRadius: '6px', fontSize: '10px', padding: '6px 12px', width: 120, textAlign: 'center' } },
      { id: 'crit', position: { x: 50, y: 80 }, data: { label: 'Critic Challenge' }, style: { background: 'rgba(208, 135, 112, 0.05)', color: '#d08770', border: '1px solid rgba(208, 135, 112, 0.3)', borderRadius: '6px', fontSize: '10px', padding: '6px 12px', width: 120, textAlign: 'center' } },
      { id: 'intv', position: { x: 50, y: 160 }, data: { label: experiment?.intervention.type || 'Intervention' }, style: { background: 'rgba(232, 169, 21, 0.1)', color: '#e8a915', border: '1px solid rgba(232, 169, 21, 0.4)', fontWeight: 'bold', borderRadius: '6px', fontSize: '10px', padding: '8px 12px', width: 120, textAlign: 'center', boxShadow: '0 0 16px rgba(232, 169, 21, 0.15) inset' } },
      { id: 'verif', position: { x: 50, y: 240 }, data: { label: verification?.outcome || 'Pending' }, style: { background: verification?.outcome === 'VERIFIED' ? 'rgba(163, 190, 140, 0.15)' : 'rgba(28, 33, 43, 0.9)', color: verification?.outcome === 'VERIFIED' ? '#a3be8c' : '#fff', border: verification?.outcome === 'VERIFIED' ? '1px solid rgba(163, 190, 140, 0.5)' : '1px solid rgba(76, 86, 106, 0.5)', borderRadius: '6px', fontSize: '10px', padding: '6px 12px', width: 120, textAlign: 'center', fontWeight: 'bold', boxShadow: verification?.outcome === 'VERIFIED' ? '0 0 16px rgba(163, 190, 140, 0.1) inset' : 'none' } }
    ];
    const flowEdges: Edge[] = [
      { id: 'e1', source: 'hyp', target: 'crit', animated: true, style: { stroke: 'rgba(208, 135, 112, 0.5)', strokeWidth: 1.5 } },
      { id: 'e2', source: 'crit', target: 'intv', animated: true, style: { stroke: 'rgba(232, 169, 21, 0.5)', strokeWidth: 1.5 } },
      { id: 'e3', source: 'intv', target: 'verif', animated: experiment?.status === 'executed', style: { stroke: experiment?.status === 'executed' ? 'rgba(163, 190, 140, 0.5)' : 'rgba(76, 86, 106, 0.5)', strokeWidth: 1.5 } }
    ];

    const chartData = verification ? verification.conditions.map(c => ({
      name: c.metric,
      Baseline: c.baseline_value,
      Observed: c.observed_value
    })) : [];

    return (
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        
        {/* HERO COMPOSITION */}
        <div className="relative overflow-hidden rounded-2xl border border-surface-elevated/70 bg-gradient-to-br from-surface to-[#0f1219] p-6 shadow-xl">
          <div className="absolute top-0 right-0 w-[600px] h-full bg-gradient-to-l from-brand/5 to-transparent pointer-events-none" />
          
          <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 relative z-10">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-3">
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-brand border border-brand/20 bg-brand/5 px-2 py-0.5 rounded">IncidentForge Core</span>
                <StatusBadge status={activeIncident.status} />
                <SeverityBadge severity={activeIncident.severity} />
                <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">{activeIncident.reasoning_mode === "live_model" ? "Live AI" : "Deterministic"}</span>
              </div>
              <Link href={`/incidents/${activeIncident.id}`}>
                <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight hover:text-brand transition-colors line-clamp-1">{activeIncident.title}</h1>
              </Link>
              <div className="mt-2 text-sm text-text-secondary flex items-center gap-2">
                <Server className="h-4 w-4" /> {activeIncident.service}
                <span className="opacity-50">|</span>
                <span className="font-mono text-[11px]">{activeIncident.id}</span>
              </div>
            </div>

            {currentMetrics && (
              <div className="flex flex-wrap items-center gap-6 xl:gap-8 bg-surface-elevated/20 px-6 py-4 rounded-xl border border-surface-elevated/40 backdrop-blur-md">
                <div className="flex flex-col">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary mb-1">P95 Latency</span>
                  <span className="font-mono text-2xl font-bold text-white leading-none">{currentMetrics.p95_latency.toFixed(0)} <span className="text-[12px] text-text-secondary font-normal">ms</span></span>
                </div>
                <div className="w-px h-8 bg-surface-elevated/50" />
                <div className="flex flex-col">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary mb-1">Error Rate</span>
                  <span className="font-mono text-2xl font-bold text-white leading-none">{(currentMetrics.error_rate * 100).toFixed(1)}<span className="text-[12px] text-text-secondary font-normal">%</span></span>
                </div>
                <div className="w-px h-8 bg-surface-elevated/50 hidden sm:block" />
                <div className="flex flex-col hidden sm:flex">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary mb-1">DB Conns</span>
                  <span className="font-mono text-2xl font-bold text-white leading-none">{currentMetrics.db_connections.toFixed(0)}</span>
                </div>
              </div>
            )}

            <div className="flex items-center gap-3 shrink-0">
              {scenarios.length > 0 && (
                <div className="relative">
                  <select
                    value={selectedScenarioId}
                    onChange={(e) => setSelectedScenarioId(e.target.value)}
                    className="w-48 appearance-none rounded-md border border-surface-elevated/70 bg-[#151923] px-3 py-2 text-[12px] text-text-primary outline-none focus:border-brand shadow-inner"
                  >
                    {scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
                  </select>
                  <ChevronRight className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-text-secondary rotate-90" />
                </div>
              )}
              <button 
                onClick={() => void createDemo()} 
                disabled={creating} 
                className="flex items-center gap-1.5 rounded-md bg-brand px-4 py-2 text-[12px] font-bold text-background transition-all hover:bg-brand/90 disabled:opacity-50 shadow-[0_0_15px_rgba(245,158,11,0.3)]"
              >
                {creating ? "Bootstrapping..." : "Run Demo"}
              </button>
            </div>
          </div>
        </div>

        {/* ASYMMETRIC GRID: Reasoning (40%) | Proof (35%) | Context (25%) */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-[1.2fr_1.1fr_0.8fr]">
          
          {/* COLUMN 1: REASONING (Hypotheses + Critic) */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between px-1">
              <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-text-secondary">AI Reasoning Engine</span>
            </div>
            
            {/* Leading Hypothesis Hero */}
            {leadingHypothesis ? (
              <div className={`relative overflow-hidden rounded-xl border p-5 transition-all ${leadingHypothesis.status === 'VERIFIED' ? 'border-status-green/40 bg-status-green/5 shadow-[0_0_30px_rgba(34,197,94,0.08)]' : 'border-brand/30 bg-brand/5 shadow-[0_0_30px_rgba(245,158,11,0.05)]'}`}>
                <div className="flex justify-between items-start mb-3">
                  <span className={`font-mono text-[14px] font-bold ${leadingHypothesis.status === 'VERIFIED' ? 'text-status-green' : 'text-brand'}`}>#1 LEADING HYPOTHESIS</span>
                  <span className={`font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${leadingHypothesis.status === 'VERIFIED' ? 'bg-status-green/20 text-status-green border-status-green/30' : 'bg-brand/10 text-brand border-brand/20'}`}>
                    {leadingHypothesis.status}
                  </span>
                </div>
                
                <h2 className="text-[18px] md:text-[20px] font-bold text-white leading-tight mb-5">{leadingHypothesis.statement}</h2>
                
                <div className="space-y-1">
                  <div className="flex justify-between items-end mb-1">
                    <span className="font-mono text-[10px] text-text-secondary uppercase tracking-wider">Confidence Score</span>
                    <span className={`font-mono text-[18px] font-bold ${leadingHypothesis.status === 'VERIFIED' ? 'text-status-green' : 'text-white'}`}>{Math.round(leadingHypothesis.score * 100)}%</span>
                  </div>
                  <div className="h-2 w-full bg-[#151923] rounded-full overflow-hidden border border-surface-elevated/50">
                    <div 
                      className={`h-full transition-all duration-1000 ${leadingHypothesis.status === 'VERIFIED' ? 'bg-status-green shadow-[0_0_8px_rgba(34,197,94,0.8)]' : 'bg-brand shadow-[0_0_8px_rgba(245,158,11,0.8)]'}`} 
                      style={{ width: `${Math.max(2, leadingHypothesis.score * 100)}%` }} 
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-surface-elevated p-8 text-center text-text-secondary text-[12px]">Analyzing evidence...</div>
            )}

            {/* Adversarial Critic */}
            {critic && (
              <div className="rounded-xl border border-status-amber/20 bg-[#1e1a12] p-4 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-status-amber/50" />
                <div className="flex items-center gap-2 mb-2">
                  <ShieldAlert className="h-4 w-4 text-status-amber" />
                  <span className="font-mono text-[10px] uppercase tracking-wider text-status-amber">Adversarial Critic</span>
                </div>
                <p className="text-[12px] text-text-primary leading-relaxed mb-3">{critic.objections}</p>
                <div className="bg-[#15120d] rounded px-3 py-2 border border-status-amber/10">
                  <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-1 block">Falsification Criterion</span>
                  <p className="text-[11px] text-status-amber/80 font-mono">{critic.falsification_criteria[0]}</p>
                </div>
              </div>
            )}

            {/* Alternative Hypotheses */}
            {alternativeHypotheses.length > 0 && (
              <div className="flex flex-col gap-2 mt-2">
                <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-text-secondary pl-1">Alternatives</span>
                {alternativeHypotheses.map((h, i) => (
                  <div key={h.id} className="flex items-center justify-between rounded-lg border border-surface-elevated/50 bg-surface/30 px-3 py-2">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="font-mono text-[10px] text-text-secondary font-bold">#{i + 2}</span>
                      <span className="text-[12px] text-text-secondary truncate">{h.statement}</span>
                    </div>
                    <span className="font-mono text-[11px] text-text-primary pl-3">{Math.round(h.score * 100)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* COLUMN 2: CAUSAL EXPERIMENT & PROOF */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between px-1">
              <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-text-secondary">Causal Experiment</span>
            </div>
            
            <div className="flex-1 rounded-xl border border-surface-elevated/70 bg-gradient-to-b from-surface to-[#0d1117] flex flex-col overflow-hidden">
              {experiment ? (
                <>
                  <div className="p-4 border-b border-surface-elevated/50 flex justify-between items-start bg-surface-elevated/10">
                    <div>
                      <h3 className="text-[14px] font-bold text-white mb-0.5">{experiment.intervention.type}</h3>
                      <span className="font-mono text-[10px] uppercase text-text-secondary">{experiment.status}</span>
                    </div>
                    {verification?.outcome === 'VERIFIED' && (
                      <div className="flex items-center gap-1.5 px-2 py-1 bg-status-green/10 border border-status-green/30 rounded text-status-green font-mono text-[10px] font-bold">
                        <CheckCircle2 className="h-3.5 w-3.5" /> VERIFIED
                      </div>
                    )}
                  </div>
                  
                  {/* Integrated React Flow & Telemetry */}
                  <div className="flex-1 flex flex-col p-4 gap-6">
                    <div className="h-[280px] w-full rounded border border-surface-elevated/30 bg-[#0b0e14] relative shadow-inner">
                      <ReactFlow nodes={flowNodes} edges={flowEdges} fitView attributionPosition="bottom-right" panOnDrag={false} zoomOnScroll={false}>
                        <Background color="#2a3241" gap={12} size={1} />
                      </ReactFlow>
                    </div>

                    {verification && chartData.length > 0 && (
                      <div className="space-y-4">
                        <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary block border-b border-surface-elevated/50 pb-2">Telemetry Validation</span>
                        
                        <div className="grid grid-cols-2 gap-4">
                          {chartData.map(d => {
                            const diff = d.Observed - d.Baseline;
                            const pct = (diff / d.Baseline) * 100;
                            const isReduction = diff < 0;
                            return (
                              <div key={d.name} className="flex flex-col">
                                <span className="font-mono text-[9px] text-text-secondary mb-1">{d.name}</span>
                                <div className="flex items-end justify-between mb-1.5">
                                  <div className="flex flex-col">
                                    <span className="text-[10px] text-text-secondary">Before</span>
                                    <span className="font-mono text-[12px] text-text-primary">{d.Baseline.toFixed(1)}</span>
                                  </div>
                                  <ChevronRight className="h-3 w-3 text-surface-elevated mb-1" />
                                  <div className="flex flex-col text-right">
                                    <span className="text-[10px] text-text-secondary">After</span>
                                    <span className="font-mono text-[12px] text-white font-bold">{d.Observed.toFixed(1)}</span>
                                  </div>
                                </div>
                                <div className="h-1.5 w-full bg-[#151923] rounded-full overflow-hidden flex">
                                  <div className="bg-surface-elevated h-full" style={{ width: '50%' }} />
                                  <div className={`${isReduction ? 'bg-status-green' : 'bg-status-red'} h-full transition-all`} style={{ width: `${Math.min(50, (d.Observed / d.Baseline) * 50)}%` }} />
                                </div>
                                <span className={`text-right font-mono text-[9px] mt-1 font-bold ${isReduction ? 'text-status-green' : 'text-status-red'}`}>
                                  {pct > 0 ? '+' : ''}{pct.toFixed(1)}%
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-text-secondary text-[12px] font-mono p-8">Awaiting experiment design...</div>
              )}
            </div>
          </div>

          {/* COLUMN 3: OPERATIONAL CONTEXT */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between px-1">
              <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-text-secondary">Live Context</span>
            </div>

            {/* Compact Evidence */}
            <div className="rounded-xl border border-surface-elevated/50 bg-surface/30 p-4">
              <div className="flex items-center gap-2 mb-3">
                <Search className="h-3.5 w-3.5 text-text-secondary" />
                <span className="font-mono text-[10px] uppercase tracking-wider text-text-primary">Evidence Context</span>
              </div>
              <div className="space-y-2">
                {activeIncident.evidence.slice(0, 3).map(e => (
                  <div key={e.id} className="text-[11px] border-l-2 border-brand/30 pl-2 py-0.5">
                    <span className="text-white block leading-snug">{e.observation}</span>
                    <span className="text-text-secondary font-mono text-[9px] mt-0.5 block">{Math.round(e.strength * 100)}% conf</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Compact Timeline */}
            <div className="flex-1 rounded-xl border border-surface-elevated/50 bg-surface/30 p-4 overflow-y-auto min-h-[200px]">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-3.5 w-3.5 text-text-secondary" />
                <span className="font-mono text-[10px] uppercase tracking-wider text-text-primary">Activity Stream</span>
              </div>
              <div className="space-y-4">
                {activeIncident.timeline.slice(-6).map(evt => (
                  <div key={evt.id} className="flex gap-3 relative">
                    <div className="w-px h-full bg-surface-elevated/50 absolute left-[3px] top-3" />
                    <div className="h-1.5 w-1.5 rounded-full bg-brand shrink-0 mt-1.5 relative z-10 shadow-[0_0_4px_rgba(245,158,11,0.5)]" />
                    <div>
                      <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary block mb-0.5">{evt.event_type}</span>
                      <span className="text-[11px] text-text-primary">{evt.title}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* PROOF STRIP (Impact Summary) */}
        {isResolved && (
          <div className="mt-4 rounded-xl border border-status-green/20 bg-gradient-to-r from-status-green/10 via-surface to-surface p-6 shadow-inner">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="md:col-span-1">
                <span className="font-mono text-[10px] uppercase tracking-wider text-status-green mb-1 block">Avoided Failures</span>
                <span className="text-4xl font-extrabold text-status-green tracking-tight leading-none drop-shadow-[0_0_12px_rgba(34,197,94,0.2)]">
                  {counterfactual ? `+${counterfactual.estimated_avoided_failures.toLocaleString()}` : '...'}
                </span>
              </div>
              
              <div className="md:col-span-3 grid grid-cols-3 gap-6 border-l border-status-green/10 pl-6">
                <div>
                  <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-1.5 flex items-center gap-1.5"><Target className="h-3 w-3 text-status-green" /> Verified Root Cause</span>
                  <span className="text-[13px] font-medium text-white line-clamp-2 leading-snug">{leadingHypothesis?.statement}</span>
                </div>
                <div>
                  <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-1.5 flex items-center gap-1.5"><FlaskConical className="h-3 w-3 text-brand" /> Validated Intervention</span>
                  <span className="text-[13px] font-medium text-white truncate">{experiment?.intervention.type}</span>
                </div>
                <div>
                  <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-1.5 flex items-center gap-1.5"><CheckCircle2 className="h-3 w-3 text-status-green" /> Applied Remediation</span>
                  <span className="text-[13px] font-medium text-white truncate">{remediation?.title}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <main className="mx-auto w-full max-w-[1400px] p-6 lg:p-8">
      {error && (
        <div className="mb-6 flex items-center gap-2 rounded border border-status-red/30 bg-status-red/10 p-3 text-[13px] text-status-red">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Primary Cockpit */}
      {!error && (activeIncident ? renderCockpit() : (
        <div className="mb-10 bg-gradient-to-br from-surface to-background p-12 rounded-2xl border border-surface-elevated flex flex-col items-center justify-center text-center shadow-2xl">
          <ShieldCheck className="h-10 w-10 text-status-green mb-5 drop-shadow-[0_0_12px_rgba(34,197,94,0.5)]" />
          <h1 className="text-3xl font-extrabold text-white tracking-tight mb-3">System Healthy</h1>
          <p className="text-[14px] text-text-secondary max-w-md mb-8 leading-relaxed">No active incidents. The AI hybrid engine is monitoring operational telemetry.</p>
          <div className="flex items-center gap-3 bg-surface-elevated/20 p-2 rounded-lg border border-surface-elevated/50 backdrop-blur-sm">
            {scenarios.length > 0 && (
              <select
                value={selectedScenarioId}
                onChange={(e) => setSelectedScenarioId(e.target.value)}
                className="w-56 appearance-none rounded-md bg-[#151923] px-3 py-2 text-[13px] text-text-primary outline-none focus:border-brand"
              >
                {scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
              </select>
            )}
            <button 
              onClick={() => void createDemo()} 
              disabled={creating} 
              className="rounded-md bg-brand px-5 py-2 text-[13px] font-bold text-background transition-all hover:bg-brand/90 disabled:opacity-50 shadow-[0_0_15px_rgba(245,158,11,0.3)]"
            >
              {creating ? "Bootstrapping..." : "Run Deterministic Demo"}
            </button>
          </div>
        </div>
      ))}

      {/* Recent Investigations (Secondary) */}
      <section className="mt-12 pt-8 border-t border-surface-elevated/30">
        <div className="mb-4 flex items-center gap-2">
          <Database className="h-4 w-4 text-text-secondary" />
          <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-text-secondary">Recent Investigations</span>
        </div>
        
        <div className="grid gap-2">
          {incidents.slice(1).map((incident) => (
            <Link href={`/incidents/${incident.id}`} key={incident.id} className="group block">
              <div className="flex items-center gap-4 p-3 rounded-lg border border-surface-elevated/40 bg-surface/20 transition-all hover:bg-surface/50 hover:border-surface-elevated">
                <SeverityBadge severity={incident.severity} />
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="truncate text-[13px] font-semibold text-text-primary group-hover:text-white transition-colors">{incident.title}</h3>
                    <StatusBadge status={incident.status} />
                  </div>
                  <div className="flex flex-wrap items-center gap-4 font-mono text-[10px] text-text-secondary">
                    <span className="flex items-center gap-1"><Server className="h-3 w-3" />{incident.service}</span>
                    <span className="flex items-center gap-1"><Search className="h-3 w-3" />{incident.hypothesis_count} hyp</span>
                    <span className="flex items-center gap-1"><Database className="h-3 w-3" />{incident.evidence_count} evi</span>
                  </div>
                </div>
                
                <span className="hidden md:block rounded px-2 py-1 font-mono text-[9px] uppercase text-text-secondary border border-surface-elevated/50 bg-[#151923]">
                  {incident.reasoning_mode === "live_model" ? "Live AI" : "Deterministic"}
                </span>
                <ChevronRight className="h-4 w-4 text-text-secondary transition-transform group-hover:translate-x-1 group-hover:text-white" />
              </div>
            </Link>
          ))}
          
          {(!incidents || incidents.length <= 1) && (
            <div className="text-center py-8 text-text-secondary text-[12px] font-mono uppercase tracking-wider">
              No historical records
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
