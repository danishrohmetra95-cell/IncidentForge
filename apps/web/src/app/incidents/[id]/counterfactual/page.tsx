"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { GitBranch, ShieldCheck, ArrowLeft, ShieldAlert, Activity } from "lucide-react";

import { api } from "@/lib/api";
import { CounterfactualResult } from "@/lib/types";
import { Card, SectionHeader } from "@/components/UI";

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

  if (error) return <main className="p-8 text-[13px] text-status-red flex items-center gap-2"><ShieldAlert className="h-4 w-4" />{error}</main>;
  if (!data) return (
    <main className="flex h-[50vh] items-center justify-center p-8">
      <div className="flex items-center gap-3 text-text-secondary">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
        <span className="font-mono text-[11px] uppercase tracking-wider">Simulating counterfactual timeline...</span>
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
    <main className="mx-auto w-full max-w-[1400px] p-6 lg:p-8 animate-in fade-in duration-300">
      <header className="mb-6">
        <div className="mb-4">
          <Link href={`/incidents/${params.id}`} className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-text-secondary hover:text-white transition-colors">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Command Center
          </Link>
        </div>
        <Card className="p-5 flex flex-col md:flex-row justify-between md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <GitBranch className="h-4 w-4 text-brand" />
              <span className="font-mono text-[10px] uppercase tracking-wider text-brand">Counterfactual Outcome</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">{data.scenario_label}</h1>
          </div>
        </Card>
      </header>

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Card className="p-5 border-status-red/20 bg-background/50">
          <SectionHeader title="Actual Failures" />
          <div className="mt-1 text-3xl font-extrabold text-status-red">
            {data.actual_failed_requests.toLocaleString()}
          </div>
        </Card>
        <Card className="p-5 border-surface-elevated bg-background/50">
          <SectionHeader title="Counterfactual Failures" />
          <div className="mt-1 text-3xl font-extrabold text-white">
            {data.counterfactual_failed_requests.toLocaleString()}
          </div>
        </Card>
        <Card className="p-5 border-status-green/30 bg-status-green/5 shadow-[0_0_16px_rgba(34,197,94,0.05)]">
          <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-status-green mb-3">
            <ShieldCheck className="h-3.5 w-3.5" /> Avoided Failures
          </div>
          <div className="mt-1 text-4xl font-extrabold text-status-green tracking-tight">
            {data.estimated_avoided_failures.toLocaleString()}
          </div>
        </Card>
      </div>

      <Card className="p-5 mb-6">
        <div className="h-[260px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3241" horizontal={false} />
              <XAxis type="number" stroke="#a0aabf" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis dataKey="name" type="category" stroke="#a0aabf" fontSize={11} tickLine={false} axisLine={false} width={120} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1c212b', borderColor: '#2a3241', color: '#fff', borderRadius: '6px', fontSize: '12px' }} 
                cursor={{ fill: '#2a3241', opacity: 0.3 }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Bar dataKey="Actual Outcome" fill="#ef4444" radius={[0, 4, 4, 0]} barSize={32} />
              <Bar dataKey="Counterfactual (No Intervention)" fill="#3b4252" radius={[0, 4, 4, 0]} barSize={32} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-4 bg-background/50 border-surface-elevated">
          <SectionHeader title="Intervention Offset" icon={Activity} />
          <p className="text-[13px] font-medium text-white">{data.intervention_time_offset_seconds} seconds after incident start</p>
        </Card>
        <Card className="p-4 bg-brand/5 border-brand/20">
          <SectionHeader title="Interpretation" icon={GitBranch} />
          <p className="text-[12px] text-brand leading-relaxed">{data.note}</p>
        </Card>
      </div>
    </main>
  );
}
