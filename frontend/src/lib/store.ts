import { useSyncExternalStore } from "react";
import type { AnalysisResult } from "./analyzers";

const KEY = "cti_nlp_history_v1";

type Listener = () => void;
const listeners = new Set<Listener>();
let cache: AnalysisResult[] | null = null;

function read(): AnalysisResult[] {
  if (cache) return cache;
  if (typeof window === "undefined") return (cache = []);
  try {
    cache = JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch {
    cache = [];
  }
  return cache!;
}

function write(next: AnalysisResult[]) {
  cache = next;
  if (typeof window !== "undefined") {
    localStorage.setItem(KEY, JSON.stringify(next));
  }
  listeners.forEach(l => l());
}

export const history = {
  add(r: AnalysisResult) { write([r, ...read()].slice(0, 200)); },
  clear() { write([]); },
  all() { return read(); },
  subscribe(l: Listener) { listeners.add(l); return () => listeners.delete(l); },
};

export function useHistory(): AnalysisResult[] {
  return useSyncExternalStore(
    history.subscribe,
    () => read(),
    () => [],
  );
}
