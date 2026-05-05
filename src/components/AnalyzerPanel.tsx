import { useState } from "react";
import { Loader2, Link2, FileText, Network, Cpu, Sparkles } from "lucide-react";
import { api, type AnalysisResult } from "@/lib/api";
import { history } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ResultCard } from "./ResultCard";
import { cn } from "@/lib/utils";

type Mode = "url" | "cti" | "ip" | "device";

const modes: { id: Mode; label: string; icon: typeof Link2; hint: string }[] = [
  { id: "url", label: "URL", icon: Link2, hint: "Phishing & malicious URL detection" },
  { id: "cti", label: "CTI Report", icon: FileText, hint: "NLP analysis of threat reports" },
  { id: "ip", label: "IP Address", icon: Network, hint: "Reputation & geolocation" },
  { id: "device", label: "Device", icon: Cpu, hint: "Endpoint posture risk" },
];

const samples: Record<Mode, string> = {
  url: "http://secure-login-update.bank-verify.zip/account?id=8273",
  cti: "Threat actor APT-29 deployed a new ransomware variant exploiting CVE-2024-1234. C2 traffic observed to 185.220.101.45 and login.update-microsoft-secure.top. SHA256 hash a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890.",
  ip: "185.220.101.45",
  device: "",
};

export function AnalyzerPanel() {
  const [mode, setMode] = useState<Mode>("url");
  const [text, setText] = useState("");
  const [device, setDevice] = useState({ os: "", lastSeen: "", openPorts: "", software: "" });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const run = async () => {
    console.log("1. Button was clicked!");
    console.log("2. The input we are analyzing is:", mode === "device" ? device : text);
    
    setLoading(true);
    
    try {
      console.log("3. Attempting to fetch from backend...");
      let r: AnalysisResult;
      
      if (mode === "url") {
        r = await api.analyzeUrl(text);
      } else if (mode === "cti") {
        r = await api.analyzeCTI(text);
      } else if (mode === "ip") {
        r = await api.analyzeIP(text);
      } else {
        r = await api.analyzeDevice(device);
      }
      
      console.log("4. Backend replied with:", r);
      history.add(r);
      setResult(r);
    } catch (error) {
      console.error("Uh oh, the fetch failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const canRun = mode === "device" ? !!device.os : text.trim().length > 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {modes.map(m => {
          const active = mode === m.id;
          const Icon = m.icon;
          return (
            <button key={m.id} onClick={() => { setMode(m.id); setResult(null); }}
              className={cn(
                "group relative overflow-hidden rounded-lg border p-4 text-left transition-all",
                active
                  ? "border-primary bg-primary/10 glow-primary"
                  : "border-border/60 bg-card/40 hover:border-primary/40 hover:bg-card/60"
              )}>
              <Icon className={cn("mb-2 h-5 w-5", active ? "text-primary" : "text-muted-foreground")} />
              <div className="font-display text-sm font-bold">{m.label}</div>
              <div className="mt-0.5 text-[11px] text-muted-foreground">{m.hint}</div>
            </button>
          );
        })}
      </div>

      <div className="relative overflow-hidden rounded-xl border border-border/60 bg-card/60 p-5 backdrop-blur-sm">
        {loading && <div className="scan-line absolute inset-0" />}
        {mode === "device" ? (
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Operating System">
              <Input placeholder="e.g. Windows 10, Ubuntu 22.04" value={device.os}
                onChange={e => setDevice({ ...device, os: e.target.value })} />
            </Field>
            <Field label="Last Seen (date)">
              <Input type="date" value={device.lastSeen}
                onChange={e => setDevice({ ...device, lastSeen: e.target.value })} />
            </Field>
            <Field label="Open Ports (comma-separated)">
              <Input placeholder="22, 80, 443, 3389" value={device.openPorts}
                onChange={e => setDevice({ ...device, openPorts: e.target.value })} />
            </Field>
            <Field label="Installed Software">
              <Input placeholder="Chrome 120, Java 7, Office 2016" value={device.software}
                onChange={e => setDevice({ ...device, software: e.target.value })} />
            </Field>
          </div>
        ) : mode === "cti" ? (
          <Textarea
            value={text} onChange={e => setText(e.target.value)} rows={6}
            placeholder="Paste a threat intelligence report, IOCs, or unstructured analyst notes..."
            className="resize-none border-border bg-background/50 font-mono text-sm"
          />
        ) : (
          <Input
            value={text} onChange={e => setText(e.target.value)}
            placeholder={mode === "url" ? "https://example.com/path" : "8.8.8.8"}
            className="h-12 border-border bg-background/50 font-mono text-sm"
          />
        )}

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={() => mode === "device"
              ? setDevice({ os: "Windows 7", lastSeen: "2024-01-15", openPorts: "445, 3389, 23", software: "Java 7, Adobe Reader 9" })
              : setText(samples[mode])}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary">
            <Sparkles className="h-3.5 w-3.5" /> Load sample
          </button>
          <Button onClick={run} disabled={!canRun || loading} size="lg"
            className="bg-gradient-to-r from-primary to-blue-500 font-bold text-primary-foreground hover:opacity-90">
            {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing</> : "Run Analysis →"}
          </Button>
        </div>
      </div>

      {result && <ResultCard result={result} />}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{label}</div>
      {children}
    </label>
  );
}
