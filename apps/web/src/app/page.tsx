"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, ChevronRight, Plus, Server, Activity, Database, Search, Cpu, ShieldCheck, Beaker, Network, GitBranch, ArrowUpRight, Target, FlaskConical, CheckCircle2, ShieldAlert } from "lucide-react";
import { ReactFlow, Background, Controls, Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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
      
      // Load cockpit for the most recent incident
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
    const sortedHypotheses = [...activeIncident.hypotheses].sort((a, b) => b.score - a.score).slice(0, 3);

    // Lifecycle state checks
    const hasEvidence = activeIncident.evidence.length > 0;
    const hasCritic = activeIncident.critiques && activeIncident.critiques.length > 0;
    const hasExperiment = activeIncident.experiments && activeIncident.experiments.length > 0;
    const hasVerification = activeIncident.verifications && activeIncident.verifications.length > 0;
    const isResolved = activeIncident.status === "RESOLVED";

    // Flow for Experiment Preview
    const targetHypothesis = experiment ? activeIncident.hypotheses.find(h => h.id === experiment.target_hypothesis) : null;
    const flowNodes: Node[] = [
      { id: 'hyp', position: { x: 50, y: 50 }, data: { label: 'Hypothesis' }, style: { background: '#2a3241', color: '#fff', border: '1px solid #4c566a', borderRadius: '4px', fontSize: '10px' } },
      { id: 'intv', position: { x: 200, y: 50 }, data: { label: experiment?.intervention.type || 'Intervention' }, style: { background: '#e8a915', color: '#1c212b', border: 'none', fontWeight: 'bold', borderRadius: '4px', fontSize: '10px' } },
      { id: 'verif', type: 'output', position: { x: 350, y: 50 }, data: { label: verification?.outcome || 'Pending' }, style: { background: verification?.outcome === 'VERIFIED' ? '#a3be8c' : '#2a3241', color: verification?.outcome === 'VERIFIED' ? '#1c212b' : '#fff', border: '1px solid #4c566a', borderRadius: '4px', fontSize: '10px' } }
    ];
    const flowEdges: Edge[] = [
      { id: 'e1', source: 'hyp', target: 'intv', animated: true, style: { stroke: '#4c566a' } },
      { id: 'e2', source: 'intv', target: 'verif', animated: experiment?.status === 'executed', style: { stroke: '#4c566a' } }
    ];

    const chartData = verification ? verification.conditions.slice(0, 3).map(c => ({
      name: c.metric,
      Baseline: c.baseline_value,
      Observed: c.observed_value
    })) : [];

    return (
      <div className="mb-10 space-y-4">
        {/* 1. INCIDENT HERO */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-surface p-5 rounded-lg border border-surface-elevated">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <SeverityBadge severity={activeIncident.severity} />
              <StatusBadge status={activeIncident.status} />
              <span className="font-mono text-[10px] uppercase text-text-secondary border border-surface-elevated px-2 py-0.5 rounded bg-background">
                {activeIncident.reasoning_mode === "live_model" ? "Live AI" : "Deterministic"}
              </span>
            </div>
            <Link href={`/incidents/${activeIncident.id}`}>
              <h1 className="text-xl font-bold text-white tracking-tight hover:text-brand transition-colors truncate">{activeIncident.title}</h1>
            </Link>
            <div className="mt-2 flex items-center gap-4">
              {currentMetrics && (
                <div className="flex items-center gap-4">
                  <DisplayValue label="P95" value={`${currentMetrics.p95_latency.toFixed(0)} ms`} />
                  <DisplayValue label="Errors" value={`${(currentMetrics.error_rate * 100).toFixed(1)}%`} />
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-3 shrink-0">
            {scenarios.length > 0 && (
              <div className="relative">
                <select
                  value={selectedScenarioId}
                  onChange={(e) => setSelectedScenarioId(e.target.value)}
                  className="w-48 appearance-none rounded border border-surface-elevated bg-background px-3 py-1.5 text-[12px] text-text-primary outline-none focus:border-brand"
                >
                  {scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
                </select>
                <ChevronRight className="pointer-events-none absolute right-2 top-2 h-3 w-3 text-text-secondary rotate-90" />
              </div>
            )}
            <button 
              onClick={() => void createDemo()} 
              disabled={creating} 
              className="flex items-center gap-1.5 rounded bg-brand px-3 py-1.5 text-[12px] font-bold text-background transition-colors hover:bg-brand/90 disabled:opacity-50"
            >
              {creating ? "Bootstrapping..." : "New Demo"}
            </button>
          </div>
        </div>

        {/* 3. INVESTIGATION STATE (Lifecycle Strip) */}
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-text-secondary bg-background/50 border border-surface-elevated rounded p-3 overflow-x-auto">
          <span className="text-brand shrink-0">LIFECYCLE:</span>
          <div className="flex items-center gap-2 shrink-0">
            {hasEvidence ? <CheckCircle2 className="h-3 w-3 text-status-green" /> : <div className="h-3 w-3 rounded-full border border-surface-elevated" />}
            <span className={hasEvidence ? "text-white" : ""}>Evidence</span>
          </div>
          <ChevronRight className="h-3 w-3 shrink-0" />
          <div className="flex items-center gap-2 shrink-0">
            {hasCritic ? <CheckCircle2 className="h-3 w-3 text-status-green" /> : <div className="h-3 w-3 rounded-full border border-surface-elevated" />}
            <span className={hasCritic ? "text-white" : ""}>Critic</span>
          </div>
          <ChevronRight className="h-3 w-3 shrink-0" />
          <div className="flex items-center gap-2 shrink-0">
            {hasExperiment ? <CheckCircle2 className="h-3 w-3 text-status-green" /> : <div className="h-3 w-3 rounded-full border border-surface-elevated" />}
            <span className={hasExperiment ? "text-white" : ""}>Experiment</span>
          </div>
          <ChevronRight className="h-3 w-3 shrink-0" />
          <div className="flex items-center gap-2 shrink-0">
            {hasVerification ? (verification?.outcome === 'VERIFIED' ? <CheckCircle2 className="h-3 w-3 text-status-green" /> : <ShieldAlert className="h-3 w-3 text-status-red" />) : <div className="h-3 w-3 rounded-full border border-surface-elevated" />}
            <span className={hasVerification ? "text-white" : ""}>Verification</span>
          </div>
          <ChevronRight className="h-3 w-3 shrink-0" />
          <div className="flex items-center gap-2 shrink-0">
            {isResolved ? <CheckCircle2 className="h-3 w-3 text-status-green" /> : <div className="h-3 w-3 rounded-full border border-surface-elevated" />}
            <span className={isResolved ? "text-white" : ""}>Resolved</span>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_1.5fr]">
          {/* 2. COMPETING HYPOTHESES */}
          <Card className="p-4 bg-background/50 border-surface-elevated">
            <SectionHeader title="Competing Hypotheses" icon={Network} />
            <div className="space-y-3">
              {sortedHypotheses.map((h, i) => {
                const isVerified = h.status === "VERIFIED";
                const isLeading = i === 0;
                return (
                  <div key={h.id} className={`p-2 rounded border ${isVerified ? 'border-status-green/30 bg-status-green/5' : isLeading ? 'border-brand/30 bg-brand/5' : 'border-surface-elevated bg-background/30'}`}>
                    <div className="flex justify-between items-start mb-1.5">
                      <span className={`font-mono text-[10px] font-bold ${isVerified ? 'text-status-green' : isLeading ? 'text-brand' : 'text-text-secondary'}`}>#{i + 1}</span>
                      <span className={`font-mono text-[9px] uppercase ${isVerified ? 'text-status-green' : isLeading ? 'text-brand' : 'text-text-secondary'}`}>{h.status}</span>
                    </div>
                    <p className="text-[12px] text-white line-clamp-2 mb-2 leading-tight">{h.statement}</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1 bg-surface-elevated rounded-full overflow-hidden">
                        <div className={`h-full ${isVerified ? 'bg-status-green' : isLeading ? 'bg-brand' : 'bg-text-secondary'}`} style={{ width: `${Math.max(2, h.score * 100)}%` }} />
                      </div>
                      <span className="font-mono text-[9px] font-bold text-text-primary">{Math.round(h.score * 100)}%</span>
                    </div>
                  </div>
                );
              })}
              {sortedHypotheses.length === 0 && (
                <div className="text-[11px] text-text-secondary p-4 border border-dashed border-surface-elevated rounded text-center">Collecting evidence...</div>
              )}
            </div>
          </Card>

          {/* 4. EXPERIMENT PREVIEW */}
          <div className="space-y-4 flex flex-col">
            <Card className="p-4 bg-background/50 border-surface-elevated flex-1 flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <SectionHeader title="Experiment Preview" icon={Beaker} />
                <Link href={`/incidents/${activeIncident.id}/experiment`} className="text-[10px] font-mono text-brand uppercase hover:underline flex items-center gap-1">Open Lab <ArrowUpRight className="h-3 w-3" /></Link>
              </div>
              
              {!experiment ? (
                <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-surface-elevated rounded text-[11px] text-text-secondary">
                  Awaiting hypothesis validation...
                </div>
              ) : (
                <div className="flex-1 grid grid-cols-2 gap-4">
                  <div className="border border-surface-elevated rounded bg-surface/30 relative overflow-hidden h-full min-h-[120px]">
                    <ReactFlow nodes={flowNodes} edges={flowEdges} fitView attributionPosition="bottom-left">
                      <Background color="#2a3241" gap={10} size={1} />
                      <Controls showInteractive={false} className="opacity-0" />
                    </ReactFlow>
                  </div>
                  
                  {verification && verification.conditions.length > 0 && (
                    <div className="border border-surface-elevated rounded bg-surface/30 p-2">
                      <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary block mb-2">Telemetry Shift</span>
                      <div className="h-[100px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="2 2" stroke="#2a3241" vertical={false} />
                            <XAxis dataKey="name" stroke="#a0aabf" fontSize={9} tickLine={false} axisLine={false} />
                            <Tooltip contentStyle={{ backgroundColor: '#1c212b', borderColor: '#2a3241', fontSize: '10px' }} cursor={{fill: '#2a3241', opacity: 0.4}} />
                            <Bar dataKey="Baseline" fill="#4c566a" radius={[2, 2, 0, 0]} maxBarSize={20} />
                            <Bar dataKey="Observed" fill="#e8a915" radius={[2, 2, 0, 0]} maxBarSize={20} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>

            {/* 5. PROOF STRIP */}
            {isResolved && (
              <Card className="p-3 border-status-green/30 bg-status-green/5 grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px]">
                <div>
                  <div className="flex items-center gap-1 font-mono uppercase text-text-secondary mb-1"><Target className="h-3 w-3 text-brand" /> Root Cause</div>
                  <p className="text-white font-medium line-clamp-1">{targetHypothesis?.statement || 'Verified'}</p>
                </div>
                <div>
                  <div className="flex items-center gap-1 font-mono uppercase text-text-secondary mb-1"><FlaskConical className="h-3 w-3 text-status-amber" /> Intervention</div>
                  <p className="text-white font-medium truncate">{experiment?.intervention.type}</p>
                </div>
                <div>
                  <div className="flex items-center gap-1 font-mono uppercase text-text-secondary mb-1"><CheckCircle2 className="h-3 w-3 text-status-green" /> Remediation</div>
                  <p className="text-white font-medium truncate">{remediation?.title}</p>
                </div>
                <div>
                  <div className="flex items-center gap-1 font-mono uppercase text-text-secondary mb-1"><GitBranch className="h-3 w-3 text-status-green" /> Avoided Failures</div>
                  <p className="text-status-green font-bold text-[14px] leading-none">{counterfactual ? `+${counterfactual.estimated_avoided_failures.toLocaleString()}` : 'Calculating...'}</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <main className="mx-auto w-full max-w-[1400px] p-6 lg:p-8 animate-in fade-in duration-300">
      
      {error && (
        <div className="mb-6 flex items-center gap-2 rounded border border-status-red/30 bg-status-red/10 p-3 text-[13px] text-status-red">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Primary Investigation Experience */}
      {!error && (activeIncident ? renderCockpit() : (
        <div className="mb-10 bg-surface p-8 rounded-lg border border-surface-elevated flex flex-col items-center justify-center text-center">
          <ShieldCheck className="h-8 w-8 text-status-green mb-4" />
          <h1 className="text-2xl font-bold text-white tracking-tight mb-2">System Healthy</h1>
          <p className="text-[13px] text-text-secondary max-w-md mb-6">No active incidents. The AI hybrid engine is monitoring telemetry.</p>
          <div className="flex items-center gap-3">
            {scenarios.length > 0 && (
              <select
                value={selectedScenarioId}
                onChange={(e) => setSelectedScenarioId(e.target.value)}
                className="w-48 appearance-none rounded border border-surface-elevated bg-background px-3 py-2 text-[12px] text-text-primary outline-none focus:border-brand"
              >
                {scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
              </select>
            )}
            <button 
              onClick={() => void createDemo()} 
              disabled={creating} 
              className="rounded bg-brand px-4 py-2 text-[12px] font-bold text-background transition-colors hover:bg-brand/90 disabled:opacity-50"
            >
              {creating ? "Bootstrapping..." : "Run Deterministic Demo"}
            </button>
          </div>
        </div>
      ))}

      {/* Incident List */}
      <section>
        <SectionHeader title="Recent Investigations" />
        <div className="grid gap-2">
          {incidents.map((incident) => (
            <Link href={`/incidents/${incident.id}`} key={incident.id} className="group block">
              <Card className="flex items-center gap-4 p-3 transition-colors hover:border-surface-elevated hover:bg-surface-elevated/30 border-surface-elevated/50 bg-background/30">
                <div className="shrink-0">
                  <SeverityBadge severity={incident.severity} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <h3 className="truncate text-[13px] font-semibold text-text-primary group-hover:text-white transition-colors">{incident.title}</h3>
                    <StatusBadge status={incident.status} />
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-4 font-mono text-[10px] text-text-secondary">
                    <span className="flex items-center gap-1"><Server className="h-3 w-3" />{incident.service}</span>
                    <span className="text-surface-elevated">•</span>
                    <span className="flex items-center gap-1"><Search className="h-3 w-3" />{incident.hypothesis_count} hypotheses</span>
                    <span className="text-surface-elevated">•</span>
                    <span className="flex items-center gap-1"><Database className="h-3 w-3" />{incident.evidence_count} evidence</span>
                  </div>
                </div>
                
                <div className="hidden flex-col items-end gap-1 md:flex">
                  <span className="rounded px-1.5 py-0.5 font-mono text-[9px] uppercase text-text-secondary border border-surface-elevated bg-background">
                    {incident.reasoning_mode === "live_model" ? "Live AI" : "Deterministic"}
                  </span>
                </div>
                
                <div className="shrink-0 pl-2">
                  <ChevronRight className="h-4 w-4 text-text-secondary transition-transform group-hover:translate-x-0.5 group-hover:text-white" />
                </div>
              </Card>
            </Link>
          ))}
          
          {!error && incidents.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-surface-elevated py-12 text-center bg-background/30">
              <Search className="mb-2 h-5 w-5 text-text-secondary opacity-50" />
              <p className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">No historical records</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
