"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { GitBranch, ShieldCheck, ArrowLeft, ArrowUpRight, ShieldAlert } from "lucide-react";

import { api } from "@/lib/api";
import { CounterfactualResult } from "@/lib/types";
import { Card, SectionHeader, DisplayValue } from "@/components/UI";

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

  if (error) return <main className="p-8 text-sm text-status-red flex items-center gap-2"><ShieldAlert className="h-4 w-4" />{error}</main>;
  if (!data) return (
    <main className="flex h-[50vh] items-center justify-center p-8">
      <div className="flex flex-col items-center gap-4 text-text-secondary">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
        <p className="font-mono text-sm uppercase tracking-wider">Simulating counterfactual timeline...</p>
      </div>
    </main>
  );

  const chartData = [
    {
      name: "Failed Requests",
      "Actual Outcome": data.actual_failed_requests,
      "Counterfactual (No Intervention)": data.counterfactual_failed_requests,
    }
  ];

  return (
    <main className="mx-auto max-w-6xl p-6 md:p-12 animate-in fade-in duration-500">
      <header className="mb-12">
        <div className="mb-8">
          <Link href={`/incidents/${params.id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary hover:text-white transition-colors">
            <ArrowLeft className="h-4 w-4" /> Back to Command Center
          </Link>
        </div>
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-brand">
          <GitBranch className="h-3 w-3" />
          Alternate Timeline
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">Counterfactual Analysis</h1>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-text-secondary">
          Scenario: {data.scenario_label}
        </p>
      </header>

      <div className="grid gap-6 md:grid-cols-3 mb-10">
        <Card className="p-6 border-status-red/20 shadow-inner">
          <SectionHeader title="Actual Failures" />
          <div className="mt-2 text-4xl font-extrabold text-status-red">
            {data.actual_failed_requests.toLocaleString()}
          </div>
        </Card>
        <Card className="p-6 border-surface-elevated shadow-inner">
          <SectionHeader title="Counterfactual Failures" />
          <div className="mt-2 text-4xl font-extrabold text-white">
            {data.counterfactual_failed_requests.toLocaleString()}
          </div>
        </Card>
        <Card className="p-6 border-status-green/30 bg-status-green/5 shadow-[0_0_24px_rgba(34,197,94,0.1)]">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.2em] text-status-green mb-4">
            <ShieldCheck className="h-4 w-4" /> Avoided Failures
          </div>
          <div className="mt-2 text-5xl font-extrabold text-status-green">
            {data.estimated_avoided_failures.toLocaleString()}
          </div>
        </Card>
      </div>

      <Card className="p-8 mb-10">
        <SectionHeader title="Outcome Comparison" description="Simulated failures with and without the verified remediation." />
        <div className="h-[400px] w-full mt-8">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3241" vertical={false} />
              <XAxis dataKey="name" stroke="#a0aabf" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#a0aabf" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1c212b', borderColor: '#2a3241', color: '#fff', borderRadius: '8px' }} 
                cursor={{ fill: '#2a3241', opacity: 0.4 }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Bar dataKey="Actual Outcome" fill="#ef4444" radius={[4, 4, 0, 0]} maxBarSize={100} />
              <Bar dataKey="Counterfactual (No Intervention)" fill="#3b4252" radius={[4, 4, 0, 0]} maxBarSize={100} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="p-6 border-brand/20 bg-brand/5">
        <div className="flex items-center justify-between gap-4 mb-4">
          <SectionHeader title="Simulation Context" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="font-mono text-[10px] uppercase tracking-wider text-text-secondary mb-1">Intervention Offset</h4>
            <p className="text-sm font-medium text-white">{data.intervention_time_offset_seconds} seconds after incident start</p>
          </div>
          <div>
            <h4 className="font-mono text-[10px] uppercase tracking-wider text-text-secondary mb-1">Disclaimer</h4>
            <p className="text-sm text-brand">{data.note}</p>
          </div>
        </div>
      </Card>
    </main>
  );
}
