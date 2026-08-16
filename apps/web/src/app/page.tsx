"use client";

import Link from "next/link";
import { ShieldAlert, ArrowRight, Activity, Beaker, CheckCircle2 } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#080b10] text-white flex flex-col relative overflow-hidden font-sans selection:bg-brand/30 selection:text-brand">
      
      {/* Background glow & gradients */}
      <div className="absolute top-0 right-0 w-3/4 h-screen bg-gradient-to-bl from-brand/5 via-brand/[0.02] to-transparent rounded-bl-full opacity-60 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-1/2 h-1/2 bg-gradient-to-tr from-brand/[0.03] to-transparent rounded-tr-full opacity-50 pointer-events-none" />

      {/* Top Header */}
      <header className="p-8 flex items-center justify-between relative z-10 animate-fade-in-up opacity-0-init">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded flex items-center justify-center bg-brand/10 border border-brand/20 shadow-[0_0_15px_rgba(232,169,21,0.15)]">
            <ShieldAlert className="w-5 h-5 text-brand" />
          </div>
          <span className="font-bold text-xl tracking-tight text-white/90">IncidentForge</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:flex-row relative z-10 max-w-[1440px] w-full mx-auto">
        
        {/* Left Column - Copy & CTA */}
        <div className="flex-1 flex flex-col justify-center px-8 lg:px-16 xl:px-24 pt-12 pb-24 lg:py-0">
          
          <div className="mb-6 animate-fade-in-up delay-200 opacity-0-init">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/10 mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-brand animate-pulse" />
              <span className="text-[10px] uppercase tracking-widest font-mono text-white/60">IncidentForge Core</span>
            </div>
            
            <h1 className="text-5xl lg:text-6xl xl:text-7xl font-bold tracking-tighter leading-[1.1] mb-6 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60">
              AI that investigates incidents.<br/>
              Then proves the cause.
            </h1>
            
            <p className="text-lg lg:text-xl text-white/40 tracking-wide font-light max-w-xl">
              Observe. Hypothesize. Challenge. Experiment. Verify.
            </p>
          </div>

          <div className="space-y-6 mt-10 animate-fade-in-up delay-300 opacity-0-init">
            <div className="flex flex-wrap items-center gap-6">
              <Link 
                href="/command-center" 
                className="group relative px-8 py-4 bg-brand text-[#080b10] font-bold text-sm tracking-wide rounded hover:bg-brand/90 transition-all duration-300 overflow-hidden flex items-center gap-3 shadow-[0_0_30px_rgba(232,169,21,0.2)]"
              >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
                <span className="relative">Enter Command Center</span>
                <ArrowRight className="w-4 h-4 relative transition-transform group-hover:translate-x-1" />
              </Link>
              
              <Link 
                href="/applications/connect" 
                className="text-sm font-medium text-white/50 hover:text-white transition-colors tracking-wide"
              >
                View Live Application Connector
              </Link>
            </div>
            
            <div className="flex items-center gap-3 text-[10px] font-mono uppercase tracking-widest text-white/30 pt-4">
              <Activity className="w-3 h-3 text-brand/50" />
              Deterministic Verification Engine • System Online
            </div>
          </div>
          
          {/* Bottom Indicators */}
          <div className="mt-auto pt-24 grid grid-cols-1 md:grid-cols-3 gap-8 animate-fade-in delay-500 opacity-0-init">
            <div className="border-t border-white/10 pt-4">
              <div className="text-[10px] font-mono text-brand mb-2">01 / OBSERVE</div>
              <div className="text-sm text-white/70">Live application telemetry</div>
            </div>
            <div className="border-t border-white/10 pt-4">
              <div className="text-[10px] font-mono text-brand mb-2">02 / REASON</div>
              <div className="text-sm text-white/70">Competing hypotheses + adversarial critique</div>
            </div>
            <div className="border-t border-white/10 pt-4">
              <div className="text-[10px] font-mono text-brand mb-2">03 / PROVE</div>
              <div className="text-sm text-white/70">Controlled experiments + deterministic verification</div>
            </div>
          </div>

        </div>

        {/* Right Column - Visual Abstract */}
        <div className="flex-1 relative hidden lg:flex items-center justify-center opacity-0 animate-fade-in delay-500 opacity-0-init">
          <div className="absolute inset-0 flex items-center justify-center">
            
            {/* The Graph */}
            <div className="relative w-full max-w-[500px] aspect-square">
              
              {/* Edges */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 500 500">
                <defs>
                  <linearGradient id="edge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="rgba(255,255,255,0.05)" />
                    <stop offset="50%" stopColor="rgba(232,169,21,0.2)" />
                    <stop offset="100%" stopColor="rgba(255,255,255,0.05)" />
                  </linearGradient>
                  
                  {/* Glowing dot moving along path */}
                  <filter id="glow">
                    <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                
                <path id="path1" d="M 100,150 C 200,150 250,250 350,250" fill="none" stroke="url(#edge-grad)" strokeWidth="1.5" />
                <path id="path2" d="M 100,350 C 200,350 250,250 350,250" fill="none" stroke="url(#edge-grad)" strokeWidth="1.5" />
                <path id="path3" d="M 350,250 C 400,250 420,150 450,150" fill="none" stroke="url(#edge-grad)" strokeWidth="1.5" />
                
                {/* Animated Pulses */}
                <circle r="3" fill="#e8a915" filter="url(#glow)">
                  <animateMotion dur="4s" repeatCount="indefinite" path="M 100,150 C 200,150 250,250 350,250" />
                  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="4s" repeatCount="indefinite" />
                </circle>
                
                <circle r="3" fill="#e8a915" filter="url(#glow)">
                  <animateMotion dur="5s" repeatCount="indefinite" path="M 100,350 C 200,350 250,250 350,250" begin="2s" />
                  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="5s" repeatCount="indefinite" begin="2s" />
                </circle>

                <circle r="3" fill="#a3be8c" filter="url(#glow)">
                  <animateMotion dur="3s" repeatCount="indefinite" path="M 350,250 C 400,250 420,150 450,150" begin="1s" />
                  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="3s" repeatCount="indefinite" begin="1s" />
                </circle>
              </svg>

              {/* Nodes */}
              {/* Observe */}
              <div className="absolute top-[130px] left-[60px] flex items-center justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-brand/20 blur-md rounded-full animate-pulse" />
                  <div className="w-10 h-10 bg-[#121620] border border-white/10 rounded-xl flex items-center justify-center relative z-10 shadow-lg shadow-black/50">
                    <Activity className="w-4 h-4 text-white/50" />
                  </div>
                  <div className="absolute top-12 left-1/2 -translate-x-1/2 font-mono text-[9px] uppercase tracking-widest text-white/40">Observe</div>
                </div>
              </div>

              {/* Critic */}
              <div className="absolute top-[330px] left-[60px] flex items-center justify-center">
                <div className="relative">
                  <div className="w-10 h-10 bg-[#121620] border border-white/10 rounded-xl flex items-center justify-center relative z-10 shadow-lg shadow-black/50">
                    <ShieldAlert className="w-4 h-4 text-white/30" />
                  </div>
                  <div className="absolute top-12 left-1/2 -translate-x-1/2 font-mono text-[9px] uppercase tracking-widest text-white/40">Critique</div>
                </div>
              </div>

              {/* Hypothesize */}
              <div className="absolute top-[230px] left-[330px] flex items-center justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-brand/10 blur-sm rounded-full" />
                  <div className="w-10 h-10 bg-[#121620] border border-brand/30 rounded-xl flex items-center justify-center relative z-10 shadow-[0_0_20px_rgba(232,169,21,0.15)]">
                    <Beaker className="w-4 h-4 text-brand" />
                  </div>
                  <div className="absolute top-12 left-1/2 -translate-x-1/2 font-mono text-[9px] uppercase tracking-widest text-brand/80">Experiment</div>
                </div>
              </div>

              {/* Verify */}
              <div className="absolute top-[130px] left-[430px] flex items-center justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-[#a3be8c]/20 blur-md rounded-full" />
                  <div className="w-10 h-10 bg-[#121620] border border-[#a3be8c]/40 rounded-xl flex items-center justify-center relative z-10 shadow-[0_0_20px_rgba(163,190,140,0.1)]">
                    <CheckCircle2 className="w-4 h-4 text-[#a3be8c]" />
                  </div>
                  <div className="absolute top-12 left-1/2 -translate-x-1/2 font-mono text-[9px] uppercase tracking-widest text-[#a3be8c]/80">Verify</div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
