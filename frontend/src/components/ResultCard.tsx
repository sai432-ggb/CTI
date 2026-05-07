import type { AnalysisResult } from "@/lib/api";
import { SeverityBadge } from "./SeverityBadge";
import { Shield, AlertTriangle, Target, FileWarning, Cpu } from "lucide-react";

const typeIcon = { url: Shield, cti: FileWarning, ip: Target, device: Cpu } as const;
const typeLabel = { url: "URL", cti: "CTI Report", ip: "IP Address", device: "Device" };

export function ResultCard({ result }: { result: any }) {
  // Handle new backend structure
  const isBackendData = result.target && result.analysis_type && result.result_data;
  
  let analysisType, score, severity, verdict, input;
  
  if (isBackendData) {
    // New backend structure
    analysisType = result.analysis_type;
    input = result.target;
    score = Math.round(result.result_data.confidence * 100);
    severity = result.result_data.is_malicious ? "high" : "low";
    verdict = result.result_data.reason || (result.result_data.is_malicious ? "Threat detected" : "No threat detected");
  } else {
    // Legacy mock structure
    analysisType = result.type;
    input = result.input;
    score = result.score;
    severity = result.severity;
    verdict = result.verdict;
  }
  
  const Icon = typeIcon[analysisType as keyof typeof typeIcon] || Shield;
  const typeLabelText = typeLabel[analysisType as keyof typeof typeLabel] || "Analysis";
  
  return (
    <div className="relative overflow-hidden rounded-xl border border-border/60 bg-card/60 p-6 backdrop-blur-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-secondary text-primary">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{typeLabelText} • Analysis Result</div>
            <div className="font-display text-lg font-bold">{verdict}</div>
            <div className="mt-0.5 max-w-md truncate text-xs text-muted-foreground">{input}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="font-display text-3xl font-bold">{score}</div>
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Confidence Score</div>
          <SeverityBadge severity={severity} className="mt-1" />
        </div>
      </div>

      <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${score}%`,
            background: severity === "critical" || severity === "high"
              ? "#ef4444" : "#10b981",
          }}
        />
      </div>

      <div className="mt-6">
        {isBackendData ? (
          <Section icon={<AlertTriangle className="h-3.5 w-3.5" />} title="Analysis Details">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Malicious:</span>
                <span className={result.result_data.is_malicious ? "text-red-500" : "text-green-500"}>
                  {result.result_data.is_malicious ? "Yes" : "No"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Confidence:</span>
                <span>{(result.result_data.confidence * 100).toFixed(1)}%</span>
              </div>
            </div>
          </Section>
        ) : (
          <div className="space-y-4">
            {result.indicators && result.indicators.length > 0 && (
              <Section icon={<AlertTriangle className="h-3.5 w-3.5" />} title="Indicators">
                <ul className="space-y-1.5 text-sm">
                  {result.indicators.map((i: string, idx: number) => (
                    <li key={idx} className="flex gap-2 text-muted-foreground">
                      <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-primary" />{i}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {result.recommendations && result.recommendations.length > 0 && (
              <Section icon={<Target className="h-3.5 w-3.5" />} title="Recommendations">
                <ul className="space-y-1.5 text-sm">
                  {result.recommendations.map((r: string, i: number) => (
                    <li key={i} className="flex gap-2 text-muted-foreground">
                      <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-blue-500" />{r}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {result.iocs && result.iocs.length > 0 && (
              <Section title="Extracted IOCs">
                <div className="flex flex-wrap gap-1.5">
                  {result.iocs.map((ioc: any, i: number) => (
                    <span key={i} className="rounded-md border border-border bg-secondary/60 px-2 py-1 font-mono text-[11px]">
                      <span className="text-blue-500">{ioc.type}</span>
                      <span className="px-1 text-muted-foreground">›</span>
                      {ioc.value}
                    </span>
                  ))}
                </div>
              </Section>
            )}

            {result.mitre && result.mitre.length > 0 && (
              <Section title="MITRE ATT&CK">
                <div className="flex flex-wrap gap-1.5">
                  {result.mitre.map((m: any) => (
                    <span key={m.id} className="rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-[11px] text-blue-700">
                      <span className="font-mono font-bold">{m.id}</span> · {m.name}
                    </span>
                  ))}
                </div>
              </Section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ icon, title, children }: { icon?: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
        {icon}{title}
      </div>
      {children}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <div className="text-sm text-muted-foreground">{children}</div>;
}
