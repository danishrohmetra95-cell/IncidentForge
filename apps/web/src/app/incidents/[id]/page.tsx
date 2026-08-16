"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { Activity, Beaker, ChevronDown, ChevronUp, Database, FileSearch, GitBranch, Network, ShieldCheck, Server, AlertTriangle, ArrowRight, CheckCircle2, XCircle, FlaskConical, Play, Target } from "lucide-react";
import { ReactFlow, Background, Controls, Node, Edge, ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

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

const parseLiveEvidence = (text: string) => {
  const data: Record<string, string> = {};
  text.split('\n').forEach(line => {
    const [key, ...rest] = line.split(':');
    if (key && rest.length > 0) {
      data[key.trim()] = rest.join(':').trim();
    }
  });
  return data;
};

export default function IncidentCommandCenter({ params }: { params: { id: string } }) {
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [evidenceExpanded, setEvidenceExpanded] = useState(false);
  const [activeAction, setActiveAction] = useState<string | null>(null);

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
    const es = api.subscribeToEvents(params.id, () => void refresh());
    return () => es.close();
  }, [params.id, refresh]);

  const runAction = async (actionName: string, actionFn: () => Promise<any>) => {
    setActiveAction(actionName);
    try {
      await actionFn();
      await refresh();
    } catch (err: any) {
      setError(err.message || "Action failed");
    } finally {
      setActiveAction(null);
    }
  };

  if (error) return <main className="p-8 text-sm text-status-red flex items-center gap-2"><AlertTriangle className="h-4 w-4" />{error}</main>;
  if (!incident) return (
    <main className="flex h-[50vh] items-center justify-center p-8">
      <div className="flex items-center gap-3 text-text-secondary">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
        <span className="font-mono text-[11px] uppercase tracking-wider">Synchronizing state...</span>
      </div>
    </main>
  );

  const isLiveMode = incident.reasoning_mode === "live_model";
  const liveEvidenceItem = incident.evidence.find(e => e.source === "ApplicationConnector");
  const parsedLive = liveEvidenceItem ? parseLiveEvidence(liveEvidenceItem.observation) : null;

  const observation = incident.observations?.at(-1);
  const currentMetrics = observation?.post_intervention ?? observation?.baseline;
  const baselineMetrics = observation?.baseline;

  const hasMetrics = !!currentMetrics;
  
  const sortedHypotheses = [...(incident.hypotheses || [])].sort((a, b) => b.score - a.score);
  const leadingHypothesis = sortedHypotheses[0];
  const critic = leadingHypothesis ? incident.critiques?.find(c => c.hypothesis_id === leadingHypothesis.id) : null;
  const experiment = leadingHypothesis ? incident.experiments?.find(e => e.target_hypothesis === leadingHypothesis.id) : null;
  const verification = experiment ? incident.verifications?.find(v => v.experiment_id === experiment.id) : null;
  const remediation = incident.remediation;

  // React Flow logic
  let flowNodes: Node[] = [];
  let flowEdges: Edge[] = [];
  if (experiment) {
    flowNodes = [
      { id: 'hyp', type: 'default', position: { x: 50, y: 50 }, draggable: false, connectable: false, selectable: false, data: { label: 'Hypothesis' }, style: { background: 'rgba(42, 50, 65, 0.9)', color: '#a0aabf', border: '1px solid rgba(76, 86, 106, 0.5)', borderRadius: '8px', fontSize: '11px', padding: '8px 12px' } },
      { id: 'crit', type: 'default', position: { x: 50, y: 130 }, draggable: false, connectable: false, selectable: false, data: { label: 'Critic' }, style: { background: 'rgba(42, 50, 65, 0.9)', color: '#d08770', border: '1px solid rgba(208, 135, 112, 0.4)', borderRadius: '8px', fontSize: '11px', padding: '8px 12px' } },
      { id: 'intv', type: 'default', position: { x: 250, y: 50 }, draggable: false, connectable: false, selectable: false, data: { label: 'Intervention' }, style: { background: 'rgba(232, 169, 21, 0.1)', color: '#e8a915', border: '1px solid rgba(232, 169, 21, 0.3)', fontWeight: 'bold', borderRadius: '8px', fontSize: '11px', padding: '8px 12px' } },
      { id: 'verif', type: 'default', position: { x: 250, y: 160 }, draggable: false, connectable: false, selectable: false, data: { label: verification?.outcome || 'Pending' }, style: { background: verification?.outcome === 'VERIFIED' ? 'rgba(163, 190, 140, 0.15)' : 'rgba(42, 50, 65, 0.9)', color: verification?.outcome === 'VERIFIED' ? '#a3be8c' : '#fff', border: verification?.outcome === 'VERIFIED' ? '1px solid rgba(163, 190, 140, 0.4)' : '1px solid rgba(76, 86, 106, 0.5)', borderRadius: '8px', fontSize: '11px', padding: '8px 12px' } }
    ];
    flowEdges = [
      { id: 'e1', source: 'hyp', target: 'crit', animated: true, style: { stroke: 'rgba(208, 135, 112, 0.6)', strokeWidth: 1.5 } },
      { id: 'e2', source: 'hyp', target: 'intv', style: { stroke: 'rgba(76, 86, 106, 0.8)', strokeWidth: 1.5 } },
      { id: 'e3', source: 'intv', target: 'verif', animated: experiment.status === 'executed', style: { stroke: experiment.status === 'executed' ? 'rgba(232, 169, 21, 0.6)' : 'rgba(76, 86, 106, 0.8)', strokeWidth: 1.5 } }
    ];
  }

  const evidenceList = incident.evidence || [];
  const evidenceToShow = evidenceExpanded ? evidenceList : evidenceList.slice(0, 4);
  const healthStatusStr = parsedLive?.['Status']?.replace('HealthStatus.', '');
  const isHealthy = isLiveMode && healthStatusStr === "HEALTHY";
  const timelineEvents = incident.timeline || [];

  return (
    <main className="p-8 max-w-[1600px] mx-auto min-h-screen">
      
      {/* 1. HERO / INCIDENT HEADER */}
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4 rounded-xl bg-surface/50 border border-surface-elevated p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
          <Activity className="w-64 h-64" />
        </div>
        <div className="relative z-10 flex gap-6 w-full">
          <div className="flex flex-col items-center justify-center min-w-[80px] pr-6 border-r border-surface-elevated/50">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${
              incident.status === "RESOLVED" || isHealthy ? "bg-status-green/10 text-status-green border border-status-green/20 shadow-[0_0_20px_rgba(34,197,94,0.1)]" : 
              incident.severity === "SEV_1" || incident.severity === "SEV_2" ? "bg-status-red/10 text-status-red border border-status-red/20 shadow-[0_0_20px_rgba(239,68,68,0.1)]" :
              "bg-status-amber/10 text-status-amber border border-status-amber/20 shadow-[0_0_20px_rgba(245,158,11,0.1)]"
            }`}>
              <Activity className="w-8 h-8 animate-pulse" />
            </div>
            <SeverityBadge severity={incident.severity} />
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary bg-background px-2 py-1 rounded border border-surface-elevated">
                {incident.id}
              </span>
              {isLiveMode && (
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-brand bg-brand/10 px-2 py-1 rounded border border-brand/20">
                  LIVE APPLICATION
                </span>
              )}
              {isLiveMode && healthStatusStr && (
                <span className={`font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded border ${
                  healthStatusStr === 'HEALTHY' ? 'bg-status-green/10 text-status-green border-status-green/20' : 
                  healthStatusStr === 'UNAVAILABLE' ? 'bg-status-red/10 text-status-red border-status-red/20' : 'bg-status-amber/10 text-status-amber border-status-amber/20'
                }`}>
                  {healthStatusStr}
                </span>
              )}
              {!isLiveMode && <StatusBadge status={incident.status} />}
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight mb-2 flex items-center gap-3">
              {incident.title}
            </h1>
            <p className="text-sm text-text-secondary max-w-3xl leading-relaxed">
              {incident.description}
            </p>
          </div>
        </div>
      </header>

      {/* 2. LIVE TELEMETRY GRID */}
      {isLiveMode && parsedLive ? (
        <div className="mb-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <Card className="p-3 bg-background/50 border-surface-elevated">
             <DisplayValue label="HTTP Status" value={parsedLive['HTTP Status'] || 'N/A'} />
          </Card>
          <Card className="p-3 bg-background/50 border-surface-elevated">
             <DisplayValue label="Availability" value={parsedLive['Availability'] || 'N/A'} />
          </Card>
          <Card className="p-3 bg-background/50 border-surface-elevated">
             <DisplayValue label="P95 Latency" value={parsedLive['P95 Latency'] || 'N/A'} />
          </Card>
          <Card className="p-3 bg-background/50 border-surface-elevated">
             <DisplayValue label="Error Rate" value={parsedLive['Error Rate'] || 'N/A'} />
          </Card>
          <Card className="p-3 bg-background/50 border-surface-elevated">
             <DisplayValue label="TLS" value={parsedLive['TLS Valid'] === "True" ? "VALID" : parsedLive['TLS Valid'] === "False" ? "FAILED" : "N/A"} />
          </Card>
          <Card className="p-3 bg-background/50 border-surface-elevated">
             <DisplayValue label="Observation Window" value="5s" />
          </Card>
        </div>
      ) : !isLiveMode && !hasMetrics ? (
        <div className="mb-6 flex h-32 items-center justify-center rounded-lg border border-dashed border-surface-elevated bg-surface/30 font-mono text-xs text-text-secondary">
          Awaiting telemetry snapshot...
        </div>
      ) : !isLiveMode && hasMetrics ? (
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
                <DisplayValue label={label} value={format(current)} delta={deltaStr} isPositive={isPositive} />
              </Card>
            );
          })}
        </div>
      ) : null}

      {/* 3-COLUMN LAYOUT */}
      <div className="grid gap-6 lg:grid-cols-[1.2fr_1.1fr_0.8fr]">
        
        {/* LEFT: AI REASONING ENGINE */}
        <div className="space-y-6">
          <section>
            <SectionHeader title="Competing Hypotheses" icon={Network} />
            
            {sortedHypotheses.length === 0 ? (
              <Card className="p-6 bg-background/30 border-dashed text-center flex flex-col items-center">
                <Network className="h-8 w-8 text-text-secondary opacity-50 mb-3" />
                {isHealthy ? (
                  <>
                    <h3 className="text-sm font-bold text-status-green mb-1">HEALTHY / NO DEGRADATION DETECTED</h3>
                    <p className="text-[12px] text-text-secondary">
                      Live external telemetry indicates the application is healthy. No causal investigation is required.
                    </p>
                  </>
                ) : incident.status === "RESOLVED" && isLiveMode ? (
                  <>
                    <h3 className="text-sm font-bold text-status-amber mb-1">INCONCLUSIVE INVESTIGATION</h3>
                    <p className="text-[12px] text-text-secondary">
                      No causal hypothesis could be established from external HTTP telemetry alone.
                    </p>
                  </>
                ) : (
                  <>
                    <h3 className="text-sm font-bold text-white mb-1">AWAITING CAUSAL INVESTIGATION</h3>
                    <p className="text-[12px] text-text-secondary mb-4">
                      {isLiveMode ? "Live telemetry has been collected. No causal hypotheses have been generated yet." : "No hypotheses have been proposed for this incident yet."}
                    </p>
                    {incident.status === "CREATED" && (
                      <button onClick={() => void runAction('start', () => api.startInvestigation(incident.id))} disabled={activeAction === 'start'} className="bg-brand text-background px-4 py-2 rounded text-sm font-bold hover:bg-brand/90 transition-colors disabled:opacity-50 flex items-center gap-2">
                        <Play className="w-4 h-4" />
                        {activeAction === 'start' ? "Starting..." : "Start Investigation"}
                      </button>
                    )}
                    {incident.status === "CREATED" && isLiveMode && (
                      <p className="text-[10px] text-text-secondary mt-3">This creates an investigation from observed evidence. No causal root cause is assumed.</p>
                    )}
                  </>
                )}
              </Card>
            ) : (
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
                              <div className={`h-full ${isVerified ? 'bg-status-green' : isLeading ? 'bg-brand' : 'bg-text-secondary'}`} style={{ width: `${Math.max(2, hypothesis.score * 100)}%` }} />
                            </div>
                            <span className={`w-8 text-right font-bold ${isVerified ? 'text-status-green' : isLeading ? 'text-brand' : 'text-text-primary'}`}>
                              {Math.round(hypothesis.score * 100)}%
                            </span>
                            <span className="text-surface-elevated">?</span>
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
            )}
          </section>

          <section>
            <SectionHeader title="Adversarial Critic" icon={ShieldCheck} />
            {critic ? (
              <Card className="border-status-amber/20 bg-status-amber/5 p-4 flex gap-3">
                <ShieldCheck className="h-4 w-4 text-status-amber shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-mono text-[10px] uppercase tracking-wider text-status-amber mb-1">Objection</h4>
                  <p className="text-[13px] text-text-primary leading-relaxed mb-3">{critic.objections}</p>
                  <div className="border-l-2 border-status-amber/30 pl-3">
                    <span className="block font-mono text-[9px] uppercase tracking-wider text-text-secondary mb-0.5">Falsification Criteria</span>
                    <p className="text-[12px] text-text-primary">{critic.falsification_criteria}</p>
                  </div>
                </div>
              </Card>
            ) : (
              <Card className="p-4 bg-background/30 border-dashed text-center flex flex-col items-center">
                 <ShieldCheck className="h-6 w-6 text-text-secondary opacity-30 mb-2" />
                 <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">CRITIC PENDING</span>
              </Card>
            )}
          </section>

          {remediation && (
            <section>
              <SectionHeader title="Remediation" icon={GitBranch} />
              <Card className="p-4 border-status-blue/20 bg-status-blue/5">
                <span className="font-mono text-[10px] uppercase tracking-wider text-status-blue mb-1 block">Remediation Generated</span>
                <p className="text-[13px] font-medium text-white mb-3">{remediation.title}</p>
                {remediation.diff && <DiffBlock diff={remediation.diff} />}
              </Card>
            </section>
          )}
        </div>

        {/* CENTER: CAUSAL EXPERIMENT */}
        <div className="space-y-6">
          <section>
            <SectionHeader title="Causal Experiment" icon={FlaskConical} />
            {experiment ? (
              <div className="space-y-3">
                <Card className="h-[250px] overflow-hidden p-0 relative border-surface-elevated flex flex-col">
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
                    />
                  </div>
                </Card>
                <Card className="p-4 bg-background/50">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-brand mb-2">Intervention</div>
                  <div className="font-mono text-[11px] text-text-primary bg-surface p-2 rounded border border-surface-elevated">
                    <span className="text-status-blue">{experiment.intervention.type}</span>: {experiment.intervention.target}
                  </div>
                </Card>
              </div>
            ) : (
              <Card className="p-6 bg-background/30 border-dashed text-center flex flex-col items-center">
                <FlaskConical className="h-8 w-8 text-text-secondary opacity-50 mb-3" />
                <h3 className="text-sm font-bold text-white mb-1">CAUSAL EXPERIMENT</h3>
                <p className="text-[12px] text-text-secondary">No controlled experiment available.</p>
                {isLiveMode && (
                  <p className="text-[11px] text-status-amber mt-3 bg-status-amber/10 p-2 rounded border border-status-amber/20">External HTTP observations alone cannot establish an internal root cause.</p>
                )}
              </Card>
            )}
          </section>

          <section>
            <SectionHeader title="Verification & Resolution" icon={CheckCircle2} />
            {verification ? (
              <Card className={`p-4 ${verification.outcome === 'VERIFIED' ? 'border-status-green/30 bg-status-green/5' : verification.outcome === 'REJECTED' ? 'border-status-red/30 bg-status-red/5' : 'border-status-amber/30 bg-status-amber/5'}`}>
                <div className="flex items-center gap-2 mb-2">
                  {verification.outcome === 'VERIFIED' ? <CheckCircle2 className="h-4 w-4 text-status-green" /> : verification.outcome === 'REJECTED' ? <XCircle className="h-4 w-4 text-status-red" /> : <AlertTriangle className="h-4 w-4 text-status-amber" />}
                  <span className={`font-mono text-[11px] font-bold uppercase ${verification.outcome === 'VERIFIED' ? 'text-status-green' : verification.outcome === 'REJECTED' ? 'text-status-red' : 'text-status-amber'}`}>{verification.outcome}</span>
                </div>
                <p className="text-[13px] text-text-primary mb-4">{verification.explanation}</p>
                
                {verification.conditions && verification.conditions.length > 0 && (
                  <div className="grid grid-cols-1 gap-2">
                    {verification.conditions.map((cond, i) => (
                      <div key={i} className="flex items-center justify-between rounded bg-background/50 px-3 py-2 border border-surface-elevated">
                        <span className="font-mono text-[11px] text-text-secondary">{cond.metric}</span>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-[12px] text-white">{cond.observed_value?.toFixed(1)}</span>
                          {cond.passed ? <CheckCircle2 className="h-4 w-4 text-status-green" /> : <XCircle className="h-4 w-4 text-status-red" />}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            ) : (
              <Card className="p-4 bg-background/30 border-dashed text-center flex flex-col items-center">
                 <Target className="h-6 w-6 text-text-secondary opacity-30 mb-2" />
                 <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">VERIFICATION PENDING</span>
                 <p className="text-[11px] text-text-secondary mt-2">No causal experiment has been completed yet.</p>
              </Card>
            )}
          </section>

          <section>
            <SectionHeader title="Counterfactual Analysis" icon={Activity} />
            <Card className="p-4 bg-background/30 border-dashed text-center flex flex-col items-center">
               <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary mb-1">COUNTERFACTUAL ANALYSIS</span>
               <p className="text-[11px] text-text-secondary">Available after a validated intervention.</p>
            </Card>
          </section>

        </div>

        {/* RIGHT: LIVE CONTEXT */}
        <div className="space-y-6">
          
          {isLiveMode && parsedLive && (
             <section>
                <SectionHeader title="Live Observation" icon={Activity} />
                <Card className="p-4 bg-background/50 mb-3 border-status-blue/20">
                   <div className="font-mono text-[10px] uppercase tracking-wider text-status-blue mb-3">Diagnostic Summary</div>
                   <p className="text-[12px] text-white leading-relaxed mb-4">
                     Application reachable. HTTP {parsedLive['HTTP Status']}. {parsedLive['Error Rate']} probe failures. P95 latency {parsedLive['P95 Latency']}. TLS {parsedLive['TLS Valid'] === 'True' ? 'valid' : 'invalid'}.
                   </p>
                   {healthStatusStr && (
                     <div className="border-t border-surface-elevated pt-3 mt-3">
                       <span className={`font-mono text-[11px] font-bold uppercase ${healthStatusStr === 'HEALTHY' ? 'text-status-green' : healthStatusStr === 'UNAVAILABLE' ? 'text-status-red' : 'text-status-amber'}`}>{healthStatusStr}</span>
                       <p className="text-[11px] text-text-secondary mt-1">
                         {healthStatusStr === 'HEALTHY' ? 'No active degradation detected during the observation window.' : 'Elevated degradation or errors were observed during the measurement window.'}
                       </p>
                     </div>
                   )}
                </Card>
             </section>
          )}

          <section>
            <SectionHeader title="Evidence Context" icon={FileSearch} />
            <div className="space-y-2">
              {isLiveMode && parsedLive ? (
                <>
                  <Card className="p-3 bg-background/50 flex justify-between items-center">
                    <span className="font-mono text-[9px] uppercase text-text-secondary">METRIC <br/><span className="text-white text-[11px]">HTTP status</span></span>
                    <span className="font-mono text-[12px] text-brand">{parsedLive['HTTP Status']}</span>
                  </Card>
                  <Card className="p-3 bg-background/50 flex justify-between items-center">
                    <span className="font-mono text-[9px] uppercase text-text-secondary">METRIC <br/><span className="text-white text-[11px]">Availability</span></span>
                    <span className="font-mono text-[12px] text-brand">{parsedLive['Availability']}</span>
                  </Card>
                  <Card className="p-3 bg-background/50 flex justify-between items-center">
                    <span className="font-mono text-[9px] uppercase text-text-secondary">METRIC <br/><span className="text-white text-[11px]">P95 latency</span></span>
                    <span className="font-mono text-[12px] text-brand">{parsedLive['P95 Latency']}</span>
                  </Card>
                  <Card className="p-3 bg-background/50 flex justify-between items-center">
                    <span className="font-mono text-[9px] uppercase text-text-secondary">METRIC <br/><span className="text-white text-[11px]">Error rate</span></span>
                    <span className="font-mono text-[12px] text-brand">{parsedLive['Error Rate']}</span>
                  </Card>
                  <Card className="p-3 bg-background/50 flex justify-between items-center">
                    <span className="font-mono text-[9px] uppercase text-text-secondary">SECURITY <br/><span className="text-white text-[11px]">TLS status</span></span>
                    <span className="font-mono text-[12px] text-brand">{parsedLive['TLS Valid'] === 'True' ? 'Valid' : 'Failed'}</span>
                  </Card>
                </>
              ) : (
                evidenceToShow.map((evidence) => (
                  <Card key={evidence.id} className="p-3 bg-background/50">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-[9px] uppercase tracking-wider text-brand">{evidence.type}</span>
                      <span className="font-mono text-[9px] text-text-secondary">{Math.round(evidence.strength * 100)}% conf</span>
                    </div>
                    <p className="text-[12px] text-text-primary leading-snug">{evidence.observation}</p>
                  </Card>
                ))
              )}
            </div>
            {!isLiveMode && evidenceList.length > 4 && (
              <button 
                onClick={() => setEvidenceExpanded(!evidenceExpanded)} 
                className="mt-2 w-full rounded border border-surface-elevated py-1.5 text-[11px] font-medium text-text-secondary hover:bg-surface-elevated/50 hover:text-white transition-colors"
              >
                {evidenceExpanded ? "Show less" : `+ ${evidenceList.length - 4} more`}
              </button>
            )}
          </section>

          <section>
            <SectionHeader title="Activity Stream" icon={Database} />
            <Card className="p-4 bg-background/50">
              <div className="space-y-4">
                {timelineEvents.length === 0 ? (
                  <span className="text-[12px] text-text-secondary font-mono">No activity recorded.</span>
                ) : (
                  timelineEvents.map((event, idx) => (
                    <div key={event.id} className="relative flex gap-4 text-[12px]">
                      {idx !== timelineEvents.length - 1 && (
                        <div className="absolute top-4 bottom-[-16px] left-[3px] w-[1px] bg-surface-elevated" />
                      )}
                      <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand relative z-10 ring-2 ring-background" />
                      <div>
                        <span className="font-mono text-[9px] uppercase tracking-wider text-text-secondary block mb-0.5">{event.event_type}</span>
                        <span className="text-text-primary">{event.title}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </section>
        </div>

      </div>
    </main>
  );
}
