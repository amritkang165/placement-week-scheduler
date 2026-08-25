import { NavLink, Route, Routes } from "react-router-dom";
import {
  Bell,
  CalendarDays,
  Database,
  LayoutDashboard,
  LineChart,
  Moon,
  Sun,
  Users,
  Zap,
} from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Schedule from "./pages/Schedule";
import Replan from "./pages/Replan";
import Analytics from "./pages/Analytics";
import Entities from "./pages/Entities";
import AddData from "./pages/AddData";
import { cn } from "./lib/utils";
import { useTheme } from "./lib/theme";

const GROUPS: { label: string; items: { to: string; label: string; icon: any; end?: boolean }[] }[] = [
  {
    label: "Overview",
    items: [
      { to: "/", label: "Board", icon: LayoutDashboard, end: true },
      { to: "/schedule", label: "Schedule", icon: CalendarDays },
    ],
  },
  {
    label: "Operate",
    items: [
      { to: "/replan", label: "Disruptions", icon: Zap },
      { to: "/analytics", label: "Analytics", icon: LineChart },
    ],
  },
  {
    label: "Data",
    items: [
      { to: "/entities", label: "Entities", icon: Users },
      { to: "/add-data", label: "Add Data", icon: Database },
    ],
  },
];

function TrafficLights() {
  return (
    <div className="flex items-center gap-2">
      {["#ff5f57", "#febc2e", "#28c840"].map((c) => (
        <span key={c} className="h-3 w-3 rounded-full" style={{ background: c }} />
      ))}
    </div>
  );
}

export default function App() {
  const { theme, toggle } = useTheme();
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* ── Window toolbar ───────────────────────────────────── */}
      <header className="frosted sticky top-0 z-30 flex h-12 items-center justify-between border-b border-border px-4">
        <div className="w-40">
          <TrafficLights />
        </div>
        <div className="text-sm font-medium text-muted-foreground">Placement Week</div>
        <div className="flex w-40 items-center justify-end gap-1.5">
          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className="flex h-7 w-7 items-center justify-center rounded-md text-foreground hover:bg-muted"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button
            aria-label="Notifications"
            className="relative flex h-7 w-7 items-center justify-center rounded-md text-foreground hover:bg-muted"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-destructive" />
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        {/* ── Sidebar ────────────────────────────────────────── */}
        <aside className="frosted sticky top-12 h-[calc(100vh-3rem)] w-60 shrink-0 border-r border-border px-3 py-4">
          <nav className="flex flex-col gap-5">
            {GROUPS.map((g) => (
              <div key={g.label}>
                <p className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  {g.label}
                </p>
                <div className="flex flex-col gap-0.5">
                  {g.items.map(({ to, label, icon: Icon, end }) => (
                    <NavLink
                      key={to}
                      to={to}
                      end={end}
                      className={({ isActive }) =>
                        cn(
                          "flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-[13px] font-medium text-foreground transition-colors",
                          isActive
                            ? "bg-primary/10 text-primary"
                            : "text-foreground hover:bg-muted",
                        )
                      }
                    >
                      <Icon className="h-4 w-4 opacity-80" />
                      {label}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>
          <div className="absolute inset-x-3 bottom-4 rounded-lg border border-border bg-muted/60 px-3 py-2.5 text-[11px] leading-relaxed text-muted-foreground">
            <p className="font-medium text-foreground">CP-SAT engine</p>
            <p>FastAPI · React</p>
          </div>
        </aside>

        {/* ── Content ────────────────────────────────────────── */}
        <main className="flex-1 overflow-x-hidden px-6 py-6 md:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/replan" element={<Replan />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/entities" element={<Entities />} />
            <Route path="/add-data" element={<AddData />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
