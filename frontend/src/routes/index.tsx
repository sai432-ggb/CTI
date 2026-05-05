import { createFileRoute } from "@tanstack/react-router";
import { AnalyzerPanel } from "@/components/AnalyzerPanel";
import { Activity, ShieldCheck, Zap } from "lucide-react";

export const Route = createFileRoute("/")({ component: Index });

function Index() {
  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-2xl border border-border/60 bg-card/40 p-8 backdrop-blur-sm md:p-12">
        <div className="absolute inset-0 grid-bg opacity-40" />
        <div className="absolute right-0 top-0 h-64 w-64 rounded-full bg-primary/20 blur-3xl" />
        <div className="absolute -bottom-10 left-10 h-48 w-48 rounded-full bg-accent/20 blur-3xl" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-primary">
            <span className="pulse-glow h-1.5 w-1.5 rounded-full bg-primary" /> NLP Engine v2.0 · Live
          </div>
          <h1 className="mt-4 font-display text-4xl font-bold leading-tight md:text-6xl">
            Decode threats with<br />
            <span className="text-blue-500">cyber-native intelligence</span>
          </h1>
          <p className="mt-4 max-w-2xl text-base text-muted-foreground md:text-lg">
            Multi-modal analysis of URLs, threat reports, IPs and devices — IOC extraction,
            MITRE ATT&CK mapping and risk scoring in one console.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <Stat icon={<Zap className="h-3.5 w-3.5" />}>4 analyzer modes</Stat>
            <Stat icon={<Activity className="h-3.5 w-3.5" />}>Real-time scoring</Stat>
            <Stat icon={<ShieldCheck className="h-3.5 w-3.5" />}>MITRE ATT&CK mapped</Stat>
          </div>
        </div>
      </section>

      <AnalyzerPanel />
    </div>
  );
}

function Stat({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-secondary/40 px-3 py-1 text-xs">
      <span className="text-primary">{icon}</span>{children}
    </div>
  );
}
