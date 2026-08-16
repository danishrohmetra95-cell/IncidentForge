"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { 
  Activity, ArrowRight, ShieldCheck, AlertTriangle, XCircle, 
  Globe, Server, Shield, Clock, Plus, ArrowLeft
} from "lucide-react";
import Link from "next/link";
import { Card, SectionHeader, DisplayValue } from "@/components/UI";
import * as api from "@/lib/api";

interface ObservationResult {
  id: string;
  application_url: string;
  observed_at: string;
  http_status: number | null;
  availability: number | null;
  p50_latency: number | null;
  p95_latency: number | null;
  error_rate: number | null;
  tls_valid: boolean | null;
  status: "HEALTHY" | "DEGRADED" | "UNAVAILABLE";
  error_message: string | null;
  latency_samples: number[];
}

export default function ConnectApplicationPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ObservationResult | null>(null);
  const [creating, setCreating] = useState(false);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    // basic format check
    let target = url;
    if (!target.startsWith("http")) {
      target = `https://${target}`;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await fetch("http://localhost:8000/api/applications/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: target })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Connection failed");
      }
      
      const data = await response.json();
      setResult(data.observation);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateIncident = async () => {
    if (!result) return;
    setCreating(true);
    try {
      const response = await fetch(`http://localhost:8000/api/applications/${result.id}/create-incident`, {
        method: "POST"
      });
      
      if (!response.ok) {
        throw new Error("Failed to create incident");
      }
      
      const data = await response.json();
      router.push(`/incidents/${data.incident_id}`);
    } catch (err: any) {
      setError(err.message);
      setCreating(false);
    }
  };

  const StatusIcon = result?.status === "HEALTHY" ? ShieldCheck :
                     result?.status === "DEGRADED" ? AlertTriangle : XCircle;
                     
  const statusColor = result?.status === "HEALTHY" ? "text-status-green" :
                      result?.status === "DEGRADED" ? "text-status-amber" : "text-status-red";

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex-none p-6 border-b border-surface-elevated bg-surface/50">
        <div className="flex items-center gap-2 mb-1">
          <Activity className="h-4 w-4 text-brand" />
          <span className="font-mono text-[10px] uppercase tracking-wider text-brand">Live Application Connector</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Connect Application</h1>
        <p className="text-sm text-text-secondary mt-1">Perform read-only external health observation and create incidents from live telemetry.</p>
      </header>

      <div className="flex-1 overflow-y-auto p-6 max-w-4xl">
        <form onSubmit={handleConnect} className="mb-8">
          <Card className="p-6">
            <label className="block text-sm font-medium text-white mb-2">Application URL</label>
            <div className="flex gap-4">
              <input 
                type="text" 
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="flex-1 bg-surface border border-surface-elevated rounded px-4 py-2 text-white focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand font-mono text-sm"
              />
              <button 
                type="submit" 
                disabled={loading || !url}
                className="bg-brand text-background px-6 py-2 rounded font-bold hover:bg-brand/90 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? "Connecting..." : "Check Application"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
            {error && (
              <div className="mt-4 p-3 bg-status-red/10 border border-status-red/20 rounded text-status-red text-sm flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}
            <div className="mt-4 text-[11px] font-mono flex items-center justify-between">
              <div className="flex gap-6 text-text-secondary">
                <div className="flex items-center gap-1.5"><Shield className="w-3 h-3" /> SSRF Protected</div>
                <div className="flex items-center gap-1.5"><Globe className="w-3 h-3" /> HTTP/HTTPS Only</div>
                <div className="flex items-center gap-1.5"><Activity className="w-3 h-3" /> Read-Only Probes</div>
              </div>
              {url.toLowerCase().includes("amazon.in") ? (
                <div className="flex items-center gap-1.5 text-brand bg-brand/10 px-2 py-1 rounded uppercase tracking-wider font-bold">
                  Mode: SIMULATED DEMO
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-status-blue bg-status-blue/10 px-2 py-1 rounded uppercase tracking-wider font-bold">
                  Mode: LIVE CONNECTOR
                </div>
              )}
            </div>
          </Card>
        </form>

        {result && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <Card className="p-6 bg-surface/50 border-surface-elevated">
              <div className="flex items-start justify-between mb-8">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h2 className="text-xl font-bold text-white">{result.application_url}</h2>
                    {result.error_message === "SIMULATED LIVE DEMO" && (
                      <span className="bg-brand/20 text-brand text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-brand/30">
                        DEMO RECORD
                      </span>
                    )}
                  </div>
                  {result.error_message === "SIMULATED LIVE DEMO" && (
                    <div className="text-xs text-brand/80 font-mono mb-2 uppercase">
                      AMAZON DEMO TARGET — SIMULATED LIVE OBSERVATION
                    </div>
                  )}
                  <div className={`flex items-center gap-2 font-mono text-sm ${statusColor}`}>
                    <StatusIcon className="w-4 h-4" />
                    {result.status === "HEALTHY" ? "HEALTHY — NO DEGRADATION DETECTED" : result.status}
                  </div>
                </div>
                {result.status !== "HEALTHY" && (
                  <button
                    onClick={handleCreateIncident}
                    disabled={creating}
                    className="bg-surface border border-surface-elevated hover:bg-surface-elevated text-white px-4 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    {creating ? "Creating..." : "Create Investigation"}
                  </button>
                )}
              </div>

              {result.status === "HEALTHY" && (
                <div className="mb-6 p-4 bg-status-green/5 border border-status-green/20 rounded-md">
                  <p className="text-sm text-status-green font-medium">External telemetry does not indicate an incident.</p>
                  <p className="text-[12px] text-text-secondary mt-1">
                    The application is responding normally. No causal AI investigation is required.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <DisplayValue label="HTTP Status" value={result.http_status ? String(result.http_status) : "N/A"} />
                <DisplayValue label="Availability" value={result.availability !== null ? `${(result.availability * 100).toFixed(1)}%` : "N/A"} />
                <DisplayValue label="P95 Latency" value={result.p95_latency ? `${result.p95_latency.toFixed(0)} ms` : "N/A"} />
                <DisplayValue label="Error Rate" value={result.error_rate !== null ? `${(result.error_rate * 100).toFixed(1)}%` : "N/A"} />
              </div>

              {result.error_message === "SIMULATED LIVE DEMO" ? (
                <div className="p-3 bg-brand/10 border border-brand/20 rounded text-sm text-brand flex items-start gap-2">
                  <Activity className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <p><strong>Presentation fixture:</strong> values are simulated for demonstration. This will run the offline Demo Live Investigation.</p>
                </div>
              ) : result.error_message && (
                <div className="p-3 bg-surface border border-surface-elevated rounded text-sm text-text-secondary">
                  <strong>Error:</strong> {result.error_message}
                </div>
              )}

              <div className="flex items-center gap-6 mt-6 pt-6 border-t border-surface-elevated text-xs text-text-secondary font-mono">
                <span className="flex items-center gap-1">
                  <Shield className="w-3.5 h-3.5" /> 
                  TLS: {result.tls_valid ? "VALID" : result.tls_valid === false ? "FAILED" : "N/A"}
                </span>
                <span className="flex items-center gap-1">
                  <Server className="w-3.5 h-3.5" /> 
                  Observation window: 5s
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> 
                  {new Date(result.observed_at).toLocaleTimeString()}
                </span>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
