"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Archive, ArrowUpRight } from "lucide-react";

import { api } from "@/lib/api";
import { IncidentSummary } from "@/lib/types";

type MemoryItem = { incident: IncidentSummary; rootCause: string; intervention: string; remediation: string };

export default function MemoryPage() {
  const [records, setRecords] = useState<MemoryItem[]>([]);
  const [message, setMessage] = useState("Loading verified incident memory…");

  useEffect(() => {
    void (async () => {
      try {
        const incidents = await api.getIncidents();
        const resolved = incidents.filter((incident) => incident.status === "RESOLVED");
        const memories = await Promise.all(resolved.map(async (incident) => ({ incident, result: await api.getMemory(incident.id) })));
        setRecords(memories.flatMap(({ incident, result }) => result.memory ? [{ incident, rootCause: result.memory.root_cause, intervention: result.memory.verified_intervention, remediation: result.memory.remediation_summary }] : []));
        setMessage("No verified incidents have been stored yet.");
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Unable to retrieve incident memory.");
      }
    })();
  }, []);

  return <main className="mx-auto max-w-5xl p-6 md:p-10"><p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">IncidentForge / memory</p><h1 className="mt-2 text-3xl font-bold">Verified institutional memory</h1><p className="mt-3 max-w-2xl text-sm text-text-secondary">Only incidents that passed deterministic verification and remediation replay are retained here. Historical records are evidence, never an automatic diagnosis.</p><div className="mt-8 space-y-4">{records.map((record) => <Link href={`/incidents/${record.incident.id}`} key={record.incident.id} className="block rounded border border-surface-elevated bg-surface p-5 transition hover:bg-surface-elevated/40"><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-xs uppercase text-brand">{record.incident.service} · {record.intervention}</p><h2 className="mt-2 font-semibold">{record.incident.title}</h2><p className="mt-3 text-sm text-text-secondary"><span className="text-text-primary">Verified root cause:</span> {record.rootCause}</p><p className="mt-1 text-sm text-text-secondary">{record.remediation}</p></div><ArrowUpRight className="h-5 w-5 shrink-0 text-brand" /></div></Link>)}{records.length === 0 && <div className="rounded border border-dashed border-surface-elevated p-10 text-center text-sm text-text-secondary"><Archive className="mx-auto mb-3 h-5 w-5" />{message}</div>}</div></main>;
}
