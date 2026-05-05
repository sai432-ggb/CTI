import { Link, useLocation } from "@tanstack/react-router";
import { Shield, Activity, History, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", label: "Analyze", icon: Shield },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/alerts", label: "Alerts", icon: Activity },
  { to: "/history", label: "History", icon: History },
] as const;

export function Header() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="relative grid h-9 w-9 place-items-center rounded-md bg-gradient-to-br from-primary to-blue-500 text-primary-foreground glow-primary">
            <Shield className="h-5 w-5" strokeWidth={2.5} />
          </div>
          <div className="leading-tight">
            <div className="font-display text-sm font-bold tracking-tight">CTI<span className="text-primary">·</span>NLP</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Threat Intelligence</div>
          </div>
        </Link>
        <nav className="hidden items-center gap-1 rounded-full border border-border/60 bg-card/40 p-1 md:flex">
          {links.map(({ to, label, icon: Icon }) => {
            const active = pathname === to;
            return (
              <Link key={to} to={to}
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors",
                  active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                )}>
                <Icon className="h-3.5 w-3.5" /> {label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 rounded-full border border-success/30 bg-success/10 px-3 py-1 text-xs text-success sm:flex">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-success" />
            </span>
            ENGINE LIVE
          </div>
        </div>
      </div>
      <nav className="flex border-t border-border/40 md:hidden">
        {links.map(({ to, label, icon: Icon }) => {
          const active = pathname === to;
          return (
            <Link key={to} to={to}
              className={cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px]",
                active ? "text-primary" : "text-muted-foreground")}>
              <Icon className="h-4 w-4" /> {label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
