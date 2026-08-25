import { NavLink, Route, Routes } from "react-router-dom";
import {
  BarChart3,
  CalendarDays,
  Database,
  LayoutDashboard,
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

const NAV = [
  { to: "/", label: "Board", icon: LayoutDashboard, end: true },
  { to: "/schedule", label: "Schedule", icon: CalendarDays },
  { to: "/replan", label: "Disruptions", icon: Zap },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/entities", label: "Entities", icon: Users },
  { to: "/add-data", label: "Add data", icon: Database },
];

export default function App() {
  const { theme, toggle } = useTheme();
  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* ── Left rail ───────────────────────────────────────── */}
      <aside className="sticky top-0 flex h-screen w-16 shrink-0 flex-col items-center border-r border-border/60 bg-card/30 py-4 backdrop-blur">
        <div className="mb-6 flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground shadow-glow">
          PW
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              title={label}
              className={({ isActive }) =>
                cn(
                  "flex h-9 w-9 items-center justify-center rounded-lg transition-colors",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" strokeWidth={1.75} />
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto">
          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────── */}
      <div className="relative flex-1 overflow-x-hidden">
        <div className="dot-grid pointer-events-none absolute inset-x-0 top-0 h-64" />
        <div className="glow relative min-h-screen">
          <header className="sticky top-0 z-30 border-b border-border/60 bg-background/70 backdrop-blur-xl">
            <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
              <div className="flex items-baseline gap-3">
                <span className="text-[15px] font-semibold tracking-tight">Placement Week</span>
                <span className="hidden text-xs text-muted-foreground sm:inline">Coordinators’ board</span>
              </div>
            </div>
          </header>

          <main className="fade-in mx-auto max-w-6xl px-6 py-10 md:py-12">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/schedule" element={<Schedule />} />
              <Route path="/replan" element={<Replan />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/entities" element={<Entities />} />
              <Route path="/add-data" element={<AddData />} />
            </Routes>
          </main>

          <footer className="mx-auto max-w-6xl border-t border-border/60 px-6 py-8">
            <p className="text-xs text-muted-foreground">CP-SAT · FastAPI · React</p>
          </footer>
        </div>
      </div>
    </div>
  );
}
