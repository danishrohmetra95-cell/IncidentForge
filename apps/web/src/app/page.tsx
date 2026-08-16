
"use client";

import Link from "next/link";
import { Search, Menu, Play } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white flex flex-col relative overflow-hidden font-sans">
      {/* Topographic Background */}
      <div className="absolute inset-0 z-0 pointer-events-none flex items-center justify-center opacity-80">
        <svg viewBox="0 0 1000 1000" className="w-[150%] h-[150%] max-w-none opacity-80" preserveAspectRatio="xMidYMid slice">
          <defs>
            <linearGradient id="topo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4f46e5" /> {/* Indigo */}
              <stop offset="50%" stopColor="#a855f7" /> {/* Purple */}
              <stop offset="100%" stopColor="#3b82f6" /> {/* Blue */}
            </linearGradient>
          </defs>
          <g fill="none" stroke="url(#topo-grad)" strokeWidth="2" className="opacity-60">
            <path d="M 400,500 C 400,300 600,200 700,400 C 800,600 600,700 400,500 Z" transform="scale(0.2) translate(1600, 1600)" />
            <path d="M 350,500 C 350,250 650,150 750,400 C 850,650 650,750 350,500 Z" transform="scale(0.35) translate(600, 600)" />
            <path d="M 300,500 C 300,200 700,100 800,400 C 900,700 700,800 300,500 Z" transform="scale(0.5) translate(300, 300)" />
            <path d="M 250,500 C 250,150 750,50 850,400 C 950,750 750,850 250,500 Z" transform="scale(0.65) translate(130, 130)" />
            <path d="M 200,500 C 200,100 800,0 900,400 C 1000,800 800,900 200,500 Z" transform="scale(0.8) translate(30, 30)" />
            <path d="M 150,500 C 150,50 850,-50 950,400 C 1050,850 850,950 150,500 Z" transform="scale(0.95) translate(-30, -30)" />
            <path d="M 100,500 C 100,0 900,-100 1000,400 C 1100,900 900,1000 100,500 Z" transform="scale(1.1) translate(-80, -80)" />
            <path d="M 50,500 C 50,-50 950,-150 1050,400 C 1150,950 950,1050 50,500 Z" transform="scale(1.25) translate(-120, -120)" />
            <path d="M 0,500 C 0,-100 1000,-200 1100,400 C 1200,1000 1000,1100 0,500 Z" transform="scale(1.4) translate(-160, -160)" />
            
            {/* Right side waves */}
            <path d="M 800,700 C 700,900 900,1000 1100,800 C 1300,600 1000,500 800,700 Z" transform="scale(0.4) translate(800, -200)" />
            <path d="M 750,700 C 600,950 950,1050 1150,800 C 1350,550 1050,450 750,700 Z" transform="scale(0.6) translate(400, -100)" />
            <path d="M 700,700 C 500,1000 1000,1100 1200,800 C 1400,500 1100,400 700,700 Z" transform="scale(0.8) translate(150, 0)" />
            <path d="M 650,700 C 400,1050 1050,1150 1250,800 C 1450,450 1150,350 650,700 Z" transform="scale(1.0) translate(0, 50)" />
            <path d="M 600,700 C 300,1100 1100,1200 1300,800 C 1500,400 1200,300 600,700 Z" transform="scale(1.2) translate(-100, 100)" />
          </g>
        </svg>
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-[1600px] mx-auto w-full">
        <div className="flex items-center gap-3">
          <div className="flex items-center">
            {/* Logo Icon similar to the reference */}
            <div className="flex">
              <div className="w-0 h-0 border-t-8 border-b-8 border-r-[12px] border-transparent border-r-white mr-[-4px] z-10"></div>
              <div className="w-8 h-8 rounded-full border-4 border-white"></div>
            </div>
          </div>
          <div className="font-bold text-lg leading-tight uppercase tracking-wider">
            Incident<br />Forge
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-10 text-xs font-bold tracking-widest uppercase">
          <Link href="#" className="hover:text-blue-400 transition-colors">About</Link>
          <Link href="#" className="hover:text-blue-400 transition-colors">Download</Link>
          <Link href="#" className="hover:text-blue-400 transition-colors">Pricing</Link>
          <Link href="#" className="hover:text-blue-400 transition-colors">Features</Link>
          <Link href="#" className="hover:text-blue-400 transition-colors">Contact</Link>
        </div>

        <div className="flex items-center gap-6">
          <Link href="/command-center" className="hidden md:block bg-[#4f46e5] hover:bg-[#4338ca] text-white text-xs font-bold tracking-widest uppercase px-8 py-3 rounded-full transition-colors">
            Sign In
          </Link>
          <button className="p-2">
            <Menu className="w-6 h-6" />
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col md:flex-row items-center justify-between px-8 lg:px-24 max-w-[1600px] mx-auto w-full">
        
        {/* Left Side */}
        <div className="flex-1 w-full max-w-2xl mt-12 md:mt-0">
          <h1 className="text-7xl lg:text-8xl xl:text-[120px] font-bold tracking-tight mb-8 leading-none">
            Welcome.
          </h1>
          
          <div className="relative mb-12 max-w-lg">
            <input 
              type="text" 
              className="w-full bg-transparent border-2 border-white/80 rounded-full py-4 px-6 text-white placeholder-white/50 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder=""
            />
            <button className="absolute right-4 top-1/2 -translate-y-1/2 p-2">
              <Search className="w-6 h-6" />
            </button>
          </div>

          <div className="flex items-center gap-6">
            <Link 
              href="/command-center" 
              className="bg-[#0ea5e9] hover:bg-[#0284c7] text-white text-xs font-bold tracking-widest uppercase px-8 py-3 rounded-full transition-colors"
            >
              Enter Command Center
            </Link>
            <Link 
              href="/applications/connect" 
              className="bg-transparent border border-white/60 hover:border-white text-white text-xs tracking-widest px-8 py-3 rounded-full transition-colors"
            >
              see more
            </Link>
          </div>
        </div>

        {/* Right Side */}
        <div className="flex-1 w-full max-w-md mt-24 md:mt-0 flex flex-col items-start md:items-end text-left md:text-right">
          <div className="mb-6 flex justify-end w-full">
            {/* Decorative Icon matching reference */}
            <div className="flex items-center">
              <div className="w-0 h-0 border-t-[12px] border-b-[12px] border-l-[20px] border-transparent border-l-[#3b82f6] opacity-80"></div>
              <div className="w-12 h-12 rounded-full border-2 border-[#a855f7] ml-2 opacity-80"></div>
            </div>
          </div>
          
          <h2 className="text-4xl lg:text-5xl font-medium mb-6 tracking-tight w-full">
            Landing page.
          </h2>
          
          <p className="text-white/60 text-sm leading-relaxed max-w-sm w-full font-light">
            IncidentForge is an AI-native incident investigation and remediation platform. 
            Observe telemetry, hypothesize root causes, challenge with adversarial critique, 
            run controlled experiments, and verify fixes deterministically.
          </p>
        </div>
      </main>

      {/* Bottom decorative element */}
      <div className="relative z-10 w-full flex justify-center pb-8">
        <div className="w-4 h-8 rounded-full border border-white/30 flex items-start justify-center p-1">
          <div className="w-1 h-2 bg-[#3b82f6] rounded-full animate-bounce"></div>
        </div>
      </div>
    </div>
  );
}
