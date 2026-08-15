"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import { api } from "@/lib/api";
import { CounterfactualResult } from "@/lib/types";

export default function CounterfactualPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<CounterfactualResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setData(await api.getCounterfactual(params.id));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load counterfactual data.");
    }
  }, [params.id]);

  useEffect(() => { void loadData(); }, [loadData]);

  if (error) return <main className="p-8 text-sm text-status-red">{error}</main>;
  if (!data) return <main className="p-8 font-mono text-sm text-text-secondary animate-pulse">Loading counterfactual analysis…</main>;

  const chartData = [
    {
      name: "Failed Requests",
      "Actual Outcome": data.actual_failed_requests,
      "Counterfactual (No Intervention)": data.counterfactual_failed_requests,
    }
  ];

  return (
    <main className="mx-auto max-w-5xl p-6 md:p-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">IncidentForge / counterfactual analysis</p>
          <h1 className="mt-2 text-3xl font-bold">Counterfactual Outcome</h1>
          <p className="mt-2 text-sm text-text-secondary">Scenario: {data.scenario_label}</p>
        </div>
        <Link href={`/incidents/${params.id}`} className="text-sm text-brand hover:underline">Command center</Link>
      </div>

      <div className="grid gap-6 md:grid-cols-3 mb-10">
        <div className="rounded border border-surface-elevated bg-surface p-6">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Actual Failures</h3>
          <p className="mt-2 text-3xl font-bold text-status-red">{data.actual_failed_requests}</p>
        </div>
        <div className="rounded border border-surface-elevated bg-surface p-6">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary">Counterfactual Failures</h3>
          <p className="mt-2 text-3xl font-bold text-text-primary">{data.counterfactual_failed_requests}</p>
        </div>
        <div className="rounded border border-status-green/30 bg-status-green/10 p-6">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-status-green">Avoided Failures</h3>
          <p className="mt-2 text-3xl font-bold text-status-green">{data.estimated_avoided_failures}</p>
        </div>
      </div>

      <div className="rounded border border-surface-elevated bg-surface p-6 mb-10">
        <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary mb-6">Outcome Comparison</h3>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3241" />
              <XAxis dataKey="name" stroke="#a0aabf" fontSize={12} />
              <YAxis stroke="#a0aabf" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1c212b', borderColor: '#2a3241', color: '#fff' }} />
              <Legend />
              <Bar dataKey="Actual Outcome" fill="#ef4444" />
              <Bar dataKey="Counterfactual (No Intervention)" fill="#a0aabf" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded border border-surface-elevated bg-surface p-6">
        <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-text-secondary mb-2">Intervention Offset</h3>
        <p className="text-sm font-medium mb-4">{data.intervention_time_offset_seconds} seconds after incident start</p>
        <p className="text-sm text-text-secondary">{data.note}</p>
      </div>
    </main>
  );
}
