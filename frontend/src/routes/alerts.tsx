import { createFileRoute, Link } from "@tanstack/react-router";
import { useHistory } from "@/lib/store";
import { SeverityBadge } from "@/components/SeverityBadge";
import { AlertTriangle, ShieldAlert } from "lucide-react";

export const Route = createFileRoute("/alerts")({
  head: () => ({ meta: [{ title: "Alerts — CTI-NLP" }] }),
  component: Alerts,
});

function Alerts() {
  const items = useHistory().filter(i => i.severity === "high" || i.severity === "critical");

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold">Active Alerts</h1>
          <p className="text-sm text-muted-foreground">{items.length} high-severity event(s) requiring action.</p>
        </div>
        <ShieldAlert className="h-8 w-8 text-destructive" />
      </header>

      {items.length === 0 ? (
        <div className="grid place-items-center rounded-xl border border-dashed border-border/60 bg-card/30 p-16 text-center">
          <div className="grid h-14 w-14 place-items-center rounded-full bg-success/15 text-success">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <h2 className="mt-4 font-display text-lg font-bold">All clear</h2>
          <p className="mt-1 text-sm text-muted-foreground">No high or critical alerts detected.</p>
          <Link to="/" className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-bold text-primary-foreground">Run analysis</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(r => (
            <div key={r.id} className={`relative overflow-hidden rounded-xl border bg-card/60 p-5 backdrop-blur-sm ${
              r.severity === "critical" ? "border-critical/50 glow-threat" : "border-destructive/40"
            }`}>
              <div className="flex items-start gap-4">
                <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${
                  r.severity === "critical" ? "bg-critical/15 text-critical" : "bg-destructive/15 text-destructive"
                }`}>
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <SeverityBadge severity={r.severity} />
                    <span className="text-[10px] uppercase tracking-widest text-muted-foreground">{r.type}</span>
                    <span className="text-[10px] text-muted-foreground">{new Date(r.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="mt-1 font-display text-base font-bold">{r.verdict}</div>
                  <div className="mt-0.5 truncate font-mono text-xs text-muted-foreground">{r.input}</div>
                  {r.indicators[0] && <div className="mt-2 text-sm text-muted-foreground">→ {r.indicators[0]}</div>}
                </div>
                <div className="text-right">
                  <div className="font-display text-2xl font-bold">{r.score}</div>
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">risk</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
