import { createFileRoute } from "@tanstack/react-router";
import { useHistory } from "@/lib/store";
import { useMemo } from "react";
import { Shield, AlertTriangle, Target, Activity } from "lucide-react";
import type { Severity } from "@/lib/analyzers";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — CTI-NLP" }] }),
  component: Dashboard,
});

function Dashboard() {
  const items = useHistory();

  const stats = useMemo(() => {
    const total = items.length;
    const bySev: Record<Severity, number> = { low: 0, medium: 0, high: 0, critical: 0 };
    const byType: Record<string, number> = { url: 0, cti: 0, ip: 0, device: 0 };
    let totalScore = 0;
    items.forEach(i => { bySev[i.severity]++; byType[i.type]++; totalScore += i.score; });
    return { total, bySev, byType, avg: total ? Math.round(totalScore / total) : 0 };
  }, [items]);

  const recent = items.slice(0, 14).reverse();
  const max = Math.max(100, ...recent.map(r => r.score));

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-3xl font-bold">Threat Console</h1>
        <p className="text-sm text-muted-foreground">Aggregate metrics across all analyses.</p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Total scans" value={stats.total} icon={<Shield className="h-4 w-4" />} accent="primary" />
        <Kpi label="Avg risk" value={stats.avg} icon={<Activity className="h-4 w-4" />} accent="blue" />
        <Kpi label="High + critical" value={stats.bySev.high + stats.bySev.critical} icon={<AlertTriangle className="h-4 w-4" />} accent="critical" />
        <Kpi label="IOCs extracted" value={items.reduce((s, i) => s + i.iocs.length, 0)} icon={<Target className="h-4 w-4" />} accent="accent" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Severity distribution" className="lg:col-span-1">
          <div className="space-y-3">
            {(Object.keys(stats.bySev) as Severity[]).map(s => {
              const pct = stats.total ? (stats.bySev[s] / stats.total) * 100 : 0;
              const colorMap = { low: "bg-success", medium: "bg-warning", high: "bg-destructive", critical: "bg-critical" };
              return (
                <div key={s}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="font-bold uppercase tracking-wider">{s}</span>
                    <span className="text-muted-foreground">{stats.bySev[s]}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-secondary">
                    <div className={`h-full ${colorMap[s]} transition-all`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <Card title="Risk score timeline" className="lg:col-span-2">
          {recent.length === 0 ? (
            <Empty>Run analyses to populate the timeline.</Empty>
          ) : (
            <div className="flex h-48 items-end gap-1">
              {recent.map(r => {
                const color = r.severity === "critical" || r.severity === "high"
                  ? "from-destructive to-red-500" : "from-primary to-blue-500";
                return (
                  <div key={r.id} className="group relative flex-1">
                    <div className={`w-full rounded-t bg-gradient-to-t ${color} transition-all hover:opacity-80`}
                      style={{ height: `${(r.score / max) * 100}%`, minHeight: "4px" }} />
                    <div className="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 rounded bg-popover px-2 py-1 text-[10px] opacity-0 shadow-md group-hover:opacity-100">
                      {r.score} · {r.type}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        <Card title="By analyzer type" className="lg:col-span-3">
          <div className="grid gap-3 sm:grid-cols-4">
            {Object.entries(stats.byType).map(([k, v]) => (
              <div key={k} className="rounded-lg border border-border/60 bg-secondary/30 p-4">
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{k}</div>
                <div className="font-display text-3xl font-bold">{v}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

const accentMap: Record<string, string> = {
  primary: "bg-primary/15 text-primary",
  blue: "bg-blue-500/15 text-blue-500",
  critical: "bg-red-500/15 text-red-500",
  accent: "bg-accent/15 text-accent",
};
function Kpi({ label, value, icon, accent }: { label: string; value: number; icon: React.ReactNode; accent: string }) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-border/60 bg-card/60 p-5 backdrop-blur-sm">
      <div className={`absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-md ${accentMap[accent]}`}>{icon}</div>
      <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="mt-2 font-display text-4xl font-bold">{value}</div>
    </div>
  );
}

function Card({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-border/60 bg-card/60 p-5 backdrop-blur-sm ${className}`}>
      <h3 className="mb-4 font-display text-sm font-bold uppercase tracking-widest text-muted-foreground">{title}</h3>
      {children}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <div className="grid h-32 place-items-center text-sm text-muted-foreground">{children}</div>;
}
