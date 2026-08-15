"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Archive, ArrowUpRight, CheckCircle2, FlaskConical, Target } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary } from "@/lib/types";
import { SeverityBadge } from "@/components/Badges";

type MemoryItem = { 
  incident: IncidentSummary; 
  rootCause: string; 
  intervention: string; 
  remediation: string;
  similarity?: number;
};

export default function MemoryPage() {
  const [records, setRecords] = useState<MemoryItem[]>([]);
  const [message, setMessage] = useState("Loading verified incident memory…");

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
      }
    })();
  }, []);

  return (
    <main className="mx-auto max-w-5xl p-6 md:p-10">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">IncidentForge / memory</p>
      <h1 className="mt-2 text-3xl font-bold">Verified institutional memory</h1>
      <p className="mt-3 max-w-2xl text-sm text-text-secondary">Only incidents that passed deterministic verification and remediation replay are retained here. Historical records are evidence, never an automatic diagnosis.</p>
      
      <div className="mt-8 space-y-6">
        {records.map((record) => (
          <Link href={`/incidents/${record.incident.id}`} key={record.incident.id} className="block rounded-lg border border-surface-elevated bg-surface p-6 transition hover:bg-surface-elevated/40">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <SeverityBadge severity={record.incident.severity} />
                  <span className="font-mono text-xs uppercase text-text-secondary">{record.incident.service}</span>
                  {record.similarity !== undefined && (
                    <span className="rounded bg-brand/10 px-2 py-0.5 font-mono text-[10px] uppercase text-brand border border-brand/20">
                      {Math.round(record.similarity * 100)}% Match
                    </span>
                  )}
                </div>
                <h2 className="text-xl font-semibold">{record.incident.title}</h2>
              </div>
              <ArrowUpRight className="h-5 w-5 shrink-0 text-brand" />
            </div>
            
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded border border-surface-elevated bg-background p-4">
                <div className="flex items-center gap-2 mb-2 font-mono text-[10px] uppercase tracking-wider text-text-secondary"><Target className="h-3 w-3 text-brand" /> Verified Root Cause</div>
                <p className="text-sm font-medium">{record.rootCause}</p>
              </div>
              <div className="rounded border border-surface-elevated bg-background p-4">
                <div className="flex items-center gap-2 mb-2 font-mono text-[10px] uppercase tracking-wider text-text-secondary"><FlaskConical className="h-3 w-3 text-brand" /> Validated Intervention</div>
                <p className="text-sm font-medium">{record.intervention}</p>
              </div>
              <div className="rounded border border-surface-elevated bg-background p-4">
                <div className="flex items-center gap-2 mb-2 font-mono text-[10px] uppercase tracking-wider text-text-secondary"><CheckCircle2 className="h-3 w-3 text-brand" /> Applied Remediation</div>
                <p className="text-sm font-medium text-text-secondary">{record.remediation}</p>
              </div>
            </div>
          </Link>
        ))}
        
        {records.length === 0 && (
          <div className="rounded border border-dashed border-surface-elevated p-12 text-center text-sm text-text-secondary">
            <Archive className="mx-auto mb-4 h-6 w-6 text-text-secondary opacity-50" />
            {message}
          </div>
        )}
      </div>
    </main>
  );
}
