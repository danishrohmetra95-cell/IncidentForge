"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Archive, ArrowUpRight, CheckCircle2, FlaskConical, Target, Database } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary } from "@/lib/types";
import { SeverityBadge } from "@/components/Badges";
import { Card, SectionHeader } from "@/components/UI";

type MemoryItem = { 
  incident: IncidentSummary; 
  rootCause: string; 
  intervention: string; 
  remediation: string;
  similarity?: number;
};

export default function MemoryPage() {
  const [records, setRecords] = useState<MemoryItem[]>([]);
  const [message, setMessage] = useState("Loading verified incident memory...");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        const incidents = await api.getIncidents();
        const resolved = incidents.filter((incident) => incident.status === "RESOLVED");
        const memories = await Promise.all(resolved.map(async (incident) => ({ incident, result: await api.getMemory(incident.id) })));
        setRecords(memories.flatMap(({ incident, result }) => result.memory ? [{ 
          incident, 
          rootCause: result.memory.root_cause, 
          intervention: result.memory.verified_intervention, 
          remediation: result.memory.remediation_summary,
          similarity: result.memory.similarity
        }] : []));
        setMessage("No verified incidents have been stored yet.");
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Unable to retrieve incident memory.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <main className="mx-auto max-w-6xl p-6 md:p-12 animate-in fade-in duration-500">
      <header className="mb-12">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-brand">
          <Database className="h-3 w-3" />
          Institutional Memory
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">Verified Records</h1>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-text-secondary">
          Only incidents that passed deterministic verification and remediation replay are retained here. 
          Historical records act as context evidence for AI, never as an automatic diagnosis.
        </p>
      </header>
      
      <div className="grid gap-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-surface-elevated py-20 text-text-secondary">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent mb-4" />
            <p className="font-mono text-sm uppercase tracking-wider">Synchronizing archives...</p>
          </div>
        ) : (
          records.map((record) => (
            <Link href={`/incidents/${record.incident.id}`} key={record.incident.id} className="group block">
              <Card className="p-6 transition-all duration-300 hover:border-brand/30 hover:shadow-lg hover:shadow-brand/5">
                <div className="flex items-start justify-between gap-4 mb-6">
                  <div>
                    <div className="flex flex-wrap items-center gap-3 mb-3">
                      <SeverityBadge severity={record.incident.severity} />
                      <span className="font-mono text-xs uppercase tracking-wider text-text-secondary">{record.incident.service}</span>
                      {record.similarity !== undefined && (
                        <span className="rounded bg-brand/10 px-2 py-0.5 font-mono text-[10px] uppercase text-brand border border-brand/20">
                          {Math.round(record.similarity * 100)}% Match
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl font-bold text-white transition-colors group-hover:text-brand">{record.incident.title}</h2>
                  </div>
                  <ArrowUpRight className="h-5 w-5 shrink-0 text-surface-elevated transition-colors group-hover:text-brand" />
                </div>
                
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded border border-surface-elevated bg-background/50 p-4 shadow-inner">
                    <div className="flex items-center gap-2 mb-3 font-mono text-[10px] uppercase tracking-wider text-text-secondary"><Target className="h-4 w-4 text-brand" /> Verified Root Cause</div>
                    <p className="text-sm font-medium text-white">{record.rootCause}</p>
                  </div>
                  <div className="rounded border border-surface-elevated bg-background/50 p-4 shadow-inner">
                    <div className="flex items-center gap-2 mb-3 font-mono text-[10px] uppercase tracking-wider text-text-secondary"><FlaskConical className="h-4 w-4 text-status-amber" /> Validated Intervention</div>
                    <p className="text-sm font-medium text-white">{record.intervention}</p>
                  </div>
                  <div className="rounded border border-surface-elevated bg-background/50 p-4 shadow-inner">
                    <div className="flex items-center gap-2 mb-3 font-mono text-[10px] uppercase tracking-wider text-text-secondary"><CheckCircle2 className="h-4 w-4 text-status-green" /> Applied Remediation</div>
                    <p className="text-sm font-medium text-text-primary">{record.remediation}</p>
                  </div>
                </div>
              </Card>
            </Link>
          ))
        )}
        
        {!loading && records.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-surface-elevated py-20 text-center">
            <Archive className="mx-auto mb-4 h-8 w-8 text-surface-elevated" />
            <p className="font-mono text-sm uppercase tracking-wider text-text-secondary">{message}</p>
          </div>
        )}
      </div>
    </main>
  );
}
