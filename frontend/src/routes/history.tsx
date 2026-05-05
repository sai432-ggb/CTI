import { createFileRoute } from "@tanstack/react-router";
import { useHistory, history } from "@/lib/store";
import { SeverityBadge } from "@/components/SeverityBadge";
import { Trash2, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/history")({
  head: () => ({ meta: [{ title: "History — CTI-NLP" }] }),
  component: History,
});

function History() {
  const items = useHistory();

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(items, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `cti-nlp-history-${Date.now()}.json`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">Analysis History</h1>
          <p className="text-sm text-muted-foreground">{items.length} entries · stored locally.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={exportJson} disabled={!items.length}>
            <Download className="mr-1.5 h-3.5 w-3.5" /> Export
          </Button>
          <Button variant="outline" size="sm" onClick={() => history.clear()} disabled={!items.length}>
            <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Clear
          </Button>
        </div>
      </header>

      {items.length === 0 ? (
        <div className="grid place-items-center rounded-xl border border-dashed border-border/60 bg-card/30 p-16 text-center text-sm text-muted-foreground">
          No history yet. Run an analysis from the home page.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border/60 bg-card/60 backdrop-blur-sm">
          <table className="w-full text-sm">
            <thead className="bg-secondary/40 text-[10px] uppercase tracking-widest text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left">When</th>
                <th className="px-4 py-3 text-left">Type</th>
                <th className="px-4 py-3 text-left">Input</th>
                <th className="px-4 py-3 text-left">Verdict</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3 text-left">Severity</th>
              </tr>
            </thead>
            <tbody>
              {items.map(r => (
                <tr key={r.id} className="border-t border-border/40 hover:bg-secondary/20">
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{new Date(r.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-3 text-xs uppercase tracking-wider text-blue-500">{r.type}</td>
                  <td className="max-w-xs truncate px-4 py-3 font-mono text-xs">{r.input}</td>
                  <td className="px-4 py-3">{r.verdict}</td>
                  <td className="px-4 py-3 text-right font-display font-bold">{r.score}</td>
                  <td className="px-4 py-3"><SeverityBadge severity={r.severity} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
