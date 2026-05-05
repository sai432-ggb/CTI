// Lightweight client-side heuristic analyzers — simulate the CTI-NLP backend
// so the dashboard works end-to-end without a server.

export type Severity = "low" | "medium" | "high" | "critical";

export interface AnalysisResult {
  id: string;
  type: "url" | "cti" | "ip" | "device";
  input: string;
  score: number; // 0-100
  severity: Severity;
  verdict: string;
  indicators: string[];
  iocs: { type: string; value: string }[];
  mitre?: { id: string; name: string }[];
  recommendations: string[];
  timestamp: number;
}

const sevFromScore = (s: number): Severity =>
  s >= 80 ? "critical" : s >= 60 ? "high" : s >= 35 ? "medium" : "low";

const uid = () => Math.random().toString(36).slice(2, 10);

const SUSPICIOUS_TLDS = [".zip", ".xyz", ".top", ".click", ".country", ".gq", ".tk", ".ml"];
const PHISH_KEYWORDS = ["login", "verify", "secure", "account", "update", "bank", "wallet", "free", "gift", "bonus", "confirm"];
const MAL_KEYWORDS = ["ransomware", "trojan", "exploit", "c2", "command and control", "botnet", "payload", "dropper", "rat", "keylogger", "phishing", "apt", "zero-day", "cve-"];

export function analyzeUrl(raw: string): AnalysisResult {
  const url = raw.trim();
  let score = 0;
  const indicators: string[] = [];
  const iocs: AnalysisResult["iocs"] = [];

  try {
    const u = new URL(url.startsWith("http") ? url : `http://${url}`);
    iocs.push({ type: "domain", value: u.hostname });

    if (u.protocol !== "https:") { score += 15; indicators.push("Non-HTTPS protocol"); }
    if (/\d+\.\d+\.\d+\.\d+/.test(u.hostname)) { score += 30; indicators.push("Raw IP used as host"); iocs.push({ type: "ipv4", value: u.hostname }); }
    if (u.hostname.split(".").length >= 4) { score += 10; indicators.push("Excessive subdomains"); }
    if (u.hostname.length > 30) { score += 10; indicators.push("Unusually long domain"); }
    if (SUSPICIOUS_TLDS.some(t => u.hostname.endsWith(t))) { score += 25; indicators.push("Suspicious TLD"); }
    if (/[0-9]/.test(u.hostname.replace(/\./g, ""))) { score += 5; indicators.push("Digits in hostname"); }
    if (/-{2,}|xn--/i.test(u.hostname)) { score += 15; indicators.push("Punycode / hyphen abuse"); }
    const lower = url.toLowerCase();
    const hits = PHISH_KEYWORDS.filter(k => lower.includes(k));
    if (hits.length) { score += Math.min(35, hits.length * 12); indicators.push(`Phishing keywords: ${hits.join(", ")}`); }
    if (u.search.length > 80) { score += 10; indicators.push("Suspicious query string length"); }
  } catch {
    score = 50;
    indicators.push("Malformed URL");
  }

  score = Math.min(100, score);
  const severity = sevFromScore(score);
  return {
    id: uid(), type: "url", input: url, score, severity,
    verdict: severity === "low" ? "Likely benign" : severity === "medium" ? "Suspicious — investigate" : severity === "high" ? "Likely malicious" : "Confirmed malicious pattern",
    indicators, iocs,
    mitre: severity !== "low" ? [{ id: "T1566.002", name: "Phishing: Spearphishing Link" }] : [],
    recommendations: severity === "low"
      ? ["Continue monitoring", "No action required"]
      : ["Block at perimeter / DNS sinkhole", "Notify affected users", "Add domain to blocklist", "Check proxy logs for hits"],
    timestamp: Date.now(),
  };
}

export function analyzeCti(text: string): AnalysisResult {
  const lower = text.toLowerCase();
  let score = 10;
  const indicators: string[] = [];
  const iocs: AnalysisResult["iocs"] = [];

  // Extract IOCs
  const ipRe = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g;
  const domRe = /\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b/gi;
  const hashRe = /\b[a-f0-9]{32,64}\b/gi;
  const cveRe = /CVE-\d{4}-\d{4,7}/gi;
  text.match(ipRe)?.forEach(v => iocs.push({ type: "ipv4", value: v }));
  text.match(domRe)?.forEach(v => iocs.push({ type: "domain", value: v }));
  text.match(hashRe)?.forEach(v => iocs.push({ type: "hash", value: v }));
  text.match(cveRe)?.forEach(v => iocs.push({ type: "cve", value: v.toUpperCase() }));

  const hits = MAL_KEYWORDS.filter(k => lower.includes(k));
  score += hits.length * 10;
  if (hits.length) indicators.push(`Threat keywords: ${hits.slice(0, 6).join(", ")}`);
  if (iocs.length) indicators.push(`${iocs.length} IOC(s) extracted`);
  score += Math.min(30, iocs.length * 5);

  const mitre: AnalysisResult["mitre"] = [];
  if (lower.includes("phishing")) mitre.push({ id: "T1566", name: "Phishing" });
  if (lower.includes("ransomware")) mitre.push({ id: "T1486", name: "Data Encrypted for Impact" });
  if (lower.includes("c2") || lower.includes("command and control")) mitre.push({ id: "T1071", name: "Application Layer Protocol" });
  if (lower.includes("exploit") || /cve-/i.test(lower)) mitre.push({ id: "T1190", name: "Exploit Public-Facing Application" });
  if (lower.includes("keylogger")) mitre.push({ id: "T1056.001", name: "Input Capture: Keylogging" });

  score = Math.min(100, score);
  const severity = sevFromScore(score);
  return {
    id: uid(), type: "cti", input: text.slice(0, 240), score, severity,
    verdict: hits.length > 3 ? "High-confidence threat report" : hits.length ? "Threat indicators detected" : "Informational",
    indicators, iocs, mitre,
    recommendations: ["Ingest IOCs into SIEM", "Pivot on extracted indicators", "Correlate with internal telemetry", "Brief response team"],
    timestamp: Date.now(),
  };
}

export function analyzeIp(ip: string): AnalysisResult {
  const parts = ip.split(".").map(Number);
  let score = 0;
  const indicators: string[] = [];
  const iocs: AnalysisResult["iocs"] = [{ type: "ipv4", value: ip }];

  if (parts.length !== 4 || parts.some(p => isNaN(p) || p < 0 || p > 255)) {
    return { id: uid(), type: "ip", input: ip, score: 50, severity: "medium",
      verdict: "Invalid IPv4", indicators: ["Malformed IP"], iocs, recommendations: ["Re-check input"], timestamp: Date.now() };
  }
  const [a, b] = parts;
  const isPrivate = a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || a === 127;
  if (isPrivate) {
    indicators.push("RFC1918 private / loopback range");
    score = 5;
  } else {
    // Pseudo-deterministic "reputation" from IP
    const seed = parts.reduce((s, p, i) => s + p * (i + 7), 0);
    score = (seed * 17) % 100;
    if (score > 60) indicators.push("Listed on simulated threat feeds");
    if (score > 40) indicators.push("Recent scanning activity observed");
    if (a === 1 || a === 8) indicators.push("ASN: large public network");
    indicators.push(`Geo (sim): ${["US", "RU", "CN", "DE", "BR", "IN", "NL"][seed % 7]}`);
  }
  const severity = sevFromScore(score);
  return {
    id: uid(), type: "ip", input: ip, score, severity,
    verdict: isPrivate ? "Private address — no external risk" : severity === "low" ? "Clean reputation" : `Reputation: ${severity}`,
    indicators, iocs,
    mitre: score > 60 ? [{ id: "T1071", name: "Application Layer Protocol" }] : [],
    recommendations: score > 60 ? ["Block at firewall", "Search SIEM for connections", "Add to threat intel watchlist"] : ["Monitor for anomalies"],
    timestamp: Date.now(),
  };
}

export function analyzeDevice(input: { os: string; lastSeen: string; openPorts: string; software: string }): AnalysisResult {
  let score = 0;
  const indicators: string[] = [];
  const ports = input.openPorts.split(/[,\s]+/).map(p => parseInt(p)).filter(p => !isNaN(p));
  const risky = [21, 23, 135, 139, 445, 3389, 5900].filter(p => ports.includes(p));
  if (risky.length) { score += risky.length * 12; indicators.push(`Risky open ports: ${risky.join(", ")}`); }
  if (/windows xp|windows 7|server 2008/i.test(input.os)) { score += 35; indicators.push("End-of-life operating system"); }
  if (/android [1-9](\.|$)/i.test(input.os)) { score += 25; indicators.push("Outdated mobile OS"); }
  const days = (Date.now() - new Date(input.lastSeen).getTime()) / 86400000;
  if (!isNaN(days) && days > 30) { score += 15; indicators.push(`No check-in for ${Math.round(days)} days`); }
  if (/flash|java 6|java 7|adobe reader 9/i.test(input.software)) { score += 25; indicators.push("Vulnerable software detected"); }
  if (!indicators.length) indicators.push("No anomalies detected in posture");

  score = Math.min(100, score);
  const severity = sevFromScore(score);
  return {
    id: uid(), type: "device", input: `${input.os} • ports: ${input.openPorts || "none"}`,
    score, severity,
    verdict: severity === "low" ? "Healthy posture" : severity === "medium" ? "Posture needs review" : "Device at risk",
    indicators, iocs: [],
    mitre: severity !== "low" ? [{ id: "T1190", name: "Exploit Public-Facing Application" }] : [],
    recommendations: severity === "low"
      ? ["Continue routine patching"]
      : ["Patch / upgrade OS immediately", "Close unnecessary ports", "Isolate from sensitive segments", "Enforce EDR coverage"],
    timestamp: Date.now(),
  };
}
