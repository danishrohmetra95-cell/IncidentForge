import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { Activity, Brain, ShieldAlert } from "lucide-react";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
  title: "IncidentForge | Command Center",
  description: "AI-native incident investigation and remediation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans bg-background text-text-primary h-screen flex overflow-hidden`}>
        <aside className="w-64 bg-surface border-r border-surface-elevated flex flex-col">
          <div className="h-16 flex items-center px-6 border-b border-surface-elevated">
            <ShieldAlert className="w-6 h-6 text-brand mr-2" />
            <span className="font-bold tracking-tight text-lg">IncidentForge</span>
          </div>
          <nav className="flex-1 py-6 px-4 space-y-2">
            <Link href="/" className="flex items-center px-4 py-2 text-sm font-medium rounded text-text-primary bg-surface-elevated">
              <Activity className="w-4 h-4 mr-3 text-brand" />
              Incidents
            </Link>
            <Link href="/memory" className="flex items-center px-4 py-2 text-sm font-medium rounded text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors">
              <Brain className="w-4 h-4 mr-3" />
              Memory
            </Link>
          </nav>
          <div className="p-4 border-t border-surface-elevated">
            <div className="flex items-center">
              <div className="w-2 h-2 rounded-full bg-status-green mr-2 animate-pulse"></div>
              <span className="text-xs font-mono text-text-secondary">SYSTEM ONLINE</span>
            </div>
          </div>
        </aside>
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
