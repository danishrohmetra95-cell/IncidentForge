"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Archive, ArrowUpRight, CheckCircle2, FlaskConical, Target, Database } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary } from "@/lib/types";
import { SeverityBadge } from "@/components/Badges";
import { Card } from "@/components/UI";

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
    <main className="mx-auto w-full max-w-[1400px] p-6 lg:p-8 animate-in fade-in duration-300">
      
      {/* Hero Card */}
      <Card className="mb-6 p-5 border-brand/20 bg-brand/5 flex flex-col md:flex-row justify-between md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Database className="h-4 w-4 text-brand" />
            <span className="font-mono text-[10px] uppercase tracking-wider text-brand">Institutional Memory</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Verified Records</h1>
          <p className="mt-1 text-[13px] text-brand/80 max-w-xl">
            Verified incidents become reusable evidence for the deterministic AI.
          </p>
        </div>
      </Card>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full flex flex-col items-center justify-center rounded-lg border border-surface-elevated py-16 text-text-secondary">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-brand border-t-transparent mb-3" />
            <p className="font-mono text-[11px] uppercase tracking-wider">Synchronizing archives...</p>
          </div>
        ) : (
          records.map((record) => (
            <Link href={`/incidents/${record.incident.id}`} key={record.incident.id} className="group block h-full">
              <Card className="p-4 h-full flex flex-col transition-all duration-300 hover:border-brand/30 hover:bg-surface-elevated/20 hover:shadow-lg hover:shadow-brand/5">
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <SeverityBadge severity={record.incident.severity} />
                      <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">{record.incident.service}</span>
                      {record.incident.service.toLowerCase().includes("amazon.in") && (
                        <span className="rounded bg-brand/20 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-brand border border-brand/30 font-bold">
                          DEMO RECORD
                        </span>
                      )}
                      {record.similarity !== undefined && (
                        <span className="rounded bg-brand/10 px-1.5 py-0.5 font-mono text-[9px] uppercase text-brand border border-brand/20">
                          {Math.round(record.similarity * 100)}% Match
                        </span>
                      )}
                    </div>
                    <h2 className="text-[15px] font-bold text-white truncate transition-colors group-hover:text-brand">{record.incident.title}</h2>
                  </div>
                  <ArrowUpRight className="h-4 w-4 shrink-0 text-text-secondary transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-brand" />
                </div>
                
                <div className="mt-auto space-y-3">
                  <div>
                    <div className="flex items-center gap-1.5 mb-1 font-mono text-[9px] uppercase tracking-wider text-text-secondary">
                      <Target className="h-3 w-3 text-brand" /> Verified Root Cause
                    </div>
                    <p className="text-[12px] font-medium text-white line-clamp-2">{record.rootCause}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3 pt-3 border-t border-surface-elevated/50">
                    <div>
                      <div className="flex items-center gap-1.5 mb-1 font-mono text-[9px] uppercase tracking-wider text-text-secondary">
                        <FlaskConical className="h-3 w-3 text-status-amber" /> Intervention
                      </div>
                      <p className="text-[11px] text-white truncate">{record.intervention}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 mb-1 font-mono text-[9px] uppercase tracking-wider text-text-secondary">
                        <CheckCircle2 className="h-3 w-3 text-status-green" /> Remediation
                      </div>
                      <p className="text-[11px] text-text-secondary truncate">{record.remediation}</p>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ))
        )}
        
        {!loading && records.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center rounded-lg border border-dashed border-surface-elevated py-16 text-center">
            <Archive className="mx-auto mb-3 h-6 w-6 text-text-secondary opacity-50" />
            <p className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">{message}</p>
          </div>
        )}
      </div>
    </main>
  );
}
