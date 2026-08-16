"use client";

import Link from "next/link";
import { ArrowRight, ShieldAlert, Activity, GitBranch, ShieldCheck, Beaker, CheckCircle2 } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#080b10] text-white flex flex-col relative overflow-hidden font-sans selection:bg-brand/30 selection:text-brand">
      
      {/* Abstract Background Grid & Traces */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-20" style={{
        backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
        backgroundPosition: 'center center'
      }}>
        {/* Subtle glowing orb */}
        <div className="absolute top-1/4 left-1/2 w-[800px] h-[800px] -translate-x-1/2 -translate-y-1/2 bg-brand/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-status-blue/5 rounded-full blur-[100px]" />
      </div>

      {/* Top Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-[1600px] mx-auto w-full animate-fade-in-up opacity-0-init">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-surface-elevated border border-surface-elevated/50 shadow-lg">
            <ShieldAlert className="w-5 h-5 text-brand" />
          </div>
          <span className="font-bold text-lg tracking-tight uppercase">IncidentForge</span>
        </div>

        <div className="hidden lg:flex items-center gap-8 text-[11px] font-mono tracking-widest uppercase text-white/50">
          <Link href="#" className="hover:text-white transition-colors">Product</Link>
          <Link href="#" className="hover:text-white transition-colors">How it works</Link>
          <Link href="/applications/connect" className="hover:text-white transition-colors">Live Connector</Link>
          <Link href="/memory" className="hover:text-white transition-colors">Memory</Link>
        </div>

        <Link 
          href="/command-center" 
          className="group flex items-center gap-2 text-xs font-bold tracking-widest uppercase text-brand hover:text-white transition-colors"
        >
          Open Command Center <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </nav>

      {/* Main Hero */}
      <main className="relative z-10 flex-1 flex flex-col lg:flex-row items-center px-8 lg:px-24 max-w-[1600px] mx-auto w-full">
        
        {/* Left Copy */}
        <div className="flex-1 max-w-2xl pt-12 pb-24 lg:py-0">
          <div className="animate-fade-in-up delay-200 opacity-0-init">
            <h1 className="text-5xl lg:text-7xl font-bold tracking-tighter leading-[1.05] mb-8 text-transparent bg-clip-text bg-gradient-to-br from-white via-white to-white/40">
              AI investigates incidents.<br/>
              Then proves the cause.
            </h1>
            
            <p className="text-lg lg:text-xl text-white/60 font-light leading-relaxed max-w-xl mb-12">
              IncidentForge observes telemetry, generates competing hypotheses, 
              challenges them adversarially, runs controlled experiments, 
              and verifies the root cause before remediation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-6 animate-fade-in-up delay-300 opacity-0-init">
            <Link 
              href="/command-center" 
              className="group relative px-8 py-4 bg-white text-black font-bold text-sm tracking-widest uppercase rounded flex items-center gap-3 overflow-hidden shadow-[0_0_40px_rgba(255,255,255,0.1)] hover:shadow-[0_0_40px_rgba(255,255,255,0.2)] transition-all"
            >
              <div className="absolute inset-0 bg-brand translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
              <span className="relative group-hover:text-black transition-colors delay-75">Enter Command Center</span>
              <ArrowRight className="w-4 h-4 relative transition-transform group-hover:translate-x-1 group-hover:text-black delay-75" />
            </Link>
            
            <Link 
              href="/command-center" 
              className="group px-8 py-4 bg-transparent border border-white/20 hover:border-white/50 text-white font-bold text-sm tracking-widest uppercase rounded transition-colors flex items-center gap-3"
            >
              Watch the investigation
            </Link>
          </div>
        </div>

        {/* Right Causal Visualization */}
        <div className="flex-1 relative hidden lg:flex items-center justify-center w-full h-[600px] animate-fade-in delay-500 opacity-0-init">
          <div className="relative w-full max-w-[600px] h-full">
            
            {/* SVG Connectors & Particles */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" viewBox="0 0 600 600">
              <defs>
                <linearGradient id="line-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.1)" />
                  <stop offset="100%" stopColor="rgba(255,255,255,0.1)" />
                </linearGradient>
                <filter id="glow-particle">
                  <feGaussianBlur stdDeviation="2" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              {/* Central vertical spine */}
              <path d="M 300,100 L 300,500" stroke="url(#line-grad)" strokeWidth="1.5" strokeDasharray="4 4" />
              
              {/* Branch to Critic */}
              <path d="M 300,300 L 450,300" stroke="url(#line-grad)" strokeWidth="1.5" strokeDasharray="4 4" />

              {/* Pulse Animation */}
              <circle r="3" fill="#e8a915" filter="url(#glow-particle)">
                <animateMotion dur="4s" repeatCount="indefinite" path="M 300,100 L 300,200 L 300,300 L 450,300 L 300,300 L 300,400 L 300,500" />
              </circle>
            </svg>

            {/* Nodes */}
            <div className="absolute inset-0 flex flex-col items-center justify-between py-10 z-10">
              
              {/* 1. OBSERVE */}
              <div className="relative group">
                <div className="absolute inset-0 bg-status-blue/20 blur-xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity" />
                <div className="w-14 h-14 bg-surface border border-status-blue/30 rounded-xl flex items-center justify-center relative shadow-lg shadow-black/50">
                  <Activity className="w-6 h-6 text-status-blue" />
                </div>
                <div className="absolute top-1/2 -translate-y-1/2 right-20 w-32 text-right">
                  <div className="font-mono text-[10px] uppercase tracking-widest text-white/50 mb-1">Phase 1</div>
                  <div className="font-bold text-sm tracking-wider text-white">OBSERVE</div>
                </div>
              </div>

              {/* 2. HYPOTHESIZE */}
              <div className="relative group mt-8">
                <div className="absolute inset-0 bg-brand/10 blur-xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity" />
                <div className="w-14 h-14 bg-surface border border-white/10 rounded-xl flex items-center justify-center relative shadow-lg shadow-black/50">
                  <GitBranch className="w-6 h-6 text-white/70" />
                </div>
                <div className="absolute top-1/2 -translate-y-1/2 left-20 w-32 text-left">
                  <div className="font-mono text-[10px] uppercase tracking-widest text-brand mb-1">Phase 2</div>
                  <div className="font-bold text-sm tracking-wider text-white">HYPOTHESIZE</div>
                </div>
              </div>

              {/* 3. CRITIQUE (Branching right) */}
              <div className="relative group w-full flex justify-center mt-8">
                <div className="relative translate-x-[150px]">
                  <div className="absolute inset-0 bg-status-red/10 blur-xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity" />
                  <div className="w-14 h-14 bg-surface border border-status-red/30 rounded-xl flex items-center justify-center relative shadow-lg shadow-black/50">
                    <ShieldCheck className="w-6 h-6 text-status-red/80" />
                  </div>
                  <div className="absolute top-1/2 -translate-y-1/2 left-20 w-32 text-left">
                    <div className="font-mono text-[10px] uppercase tracking-widest text-status-red/60 mb-1">Adversarial</div>
                    <div className="font-bold text-sm tracking-wider text-white">CRITIQUE</div>
                  </div>
                </div>
              </div>

              {/* 4. EXPERIMENT */}
              <div className="relative group mt-8">
                <div className="absolute inset-0 bg-brand/20 blur-xl rounded-full opacity-50 animate-pulse" />
                <div className="w-14 h-14 bg-surface border border-brand/40 rounded-xl flex items-center justify-center relative shadow-[0_0_30px_rgba(232,169,21,0.2)]">
                  <Beaker className="w-6 h-6 text-brand" />
                </div>
                <div className="absolute top-1/2 -translate-y-1/2 right-20 w-32 text-right">
                  <div className="font-mono text-[10px] uppercase tracking-widest text-brand mb-1">Execution</div>
                  <div className="font-bold text-sm tracking-wider text-brand">EXPERIMENT</div>
                </div>
              </div>

              {/* 5. VERIFY */}
              <div className="relative group mt-8">
                <div className="absolute inset-0 bg-status-green/20 blur-xl rounded-full opacity-50 group-hover:opacity-100 transition-opacity" />
                <div className="w-14 h-14 bg-surface border border-status-green/40 rounded-xl flex items-center justify-center relative shadow-[0_0_30px_rgba(163,190,140,0.15)]">
                  <CheckCircle2 className="w-6 h-6 text-status-green" />
                </div>
                <div className="absolute top-1/2 -translate-y-1/2 left-20 w-32 text-left">
                  <div className="font-mono text-[10px] uppercase tracking-widest text-status-green mb-1">Deterministic</div>
                  <div className="font-bold text-sm tracking-wider text-white">VERIFY</div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </main>

      {/* Bottom Status Bar */}
      <footer className="relative z-10 border-t border-white/5 bg-black/50 backdrop-blur-md animate-fade-in delay-500 opacity-0-init">
        <div className="max-w-[1600px] mx-auto w-full px-8 py-4 flex flex-wrap items-center justify-between gap-6 font-mono text-[10px] uppercase tracking-widest text-white/40">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-status-green animate-pulse" />
              System Online
            </div>
            <div className="hidden md:flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-brand animate-pulse" />
              Deterministic Engine Ready
            </div>
            <div className="hidden md:flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-status-blue animate-pulse" />
              Live Connector Ready
            </div>
          </div>
          <div className="flex items-center gap-4 text-white/30">
            IncidentForge Architecture v2.0
          </div>
        </div>
      </footer>
    </div>
  );
}
