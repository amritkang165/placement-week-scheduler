import { NavLink, Route, Routes } from "react-router-dom";
import {
  Bell,
  CalendarDays,
  Database,
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

const NAV = [
  { to: "/", label: "Board", icon: LineChart },
  { to: "/schedule", label: "Schedule", icon: CalendarDays },
  { to: "/replan", label: "Disruptions", icon: Zap },
  { to: "/analytics", label: "Analytics", icon: LineChart },
  { to: "/entities", label: "Entities", icon: Users },
  { to: "/add-data", label: "Add Data", icon: Database },
];

export default function App() {
  const { theme, toggle } = useTheme();
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── Top bar ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b-2 border-foreground bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <div className="flex items-center gap-3">
            <span className="flex h-9 items-center border-2 border-foreground bg-accent px-2 font-display text-lg leading-none text-accent-foreground shadow-hard-sm">
              PW
            </span>
            <div className="leading-tight">
              <p className="font-display text-lg uppercase leading-none">Placement Week</p>
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                Coordinators’ board
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggle}
              aria-label="Toggle theme"
              className="flex h-10 w-10 items-center justify-center border-2 border-foreground bg-card shadow-hard-sm transition-transform hover:-translate-y-0.5"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <button
              aria-label="Notifications"
              className="relative flex h-10 w-10 items-center justify-center border-2 border-foreground bg-card shadow-hard-sm transition-transform hover:-translate-y-0.5"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute right-1 top-1 h-2 w-2 border border-foreground bg-destructive" />
            </button>
          </div>
        </div>
        {/* nav */}
        <nav className="mx-auto max-w-6xl overflow-x-auto px-5">
          <div className="flex gap-2 py-2">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 whitespace-nowrap border-2 border-foreground px-3 py-1.5 font-mono text-xs font-bold uppercase tracking-wide transition-all",
                    isActive
                      ? "bg-foreground text-background shadow-hard-sm"
                      : "bg-card text-foreground hover:-translate-y-0.5 hover:bg-accent hover:text-accent-foreground",
                  )
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8 md:py-10">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/replan" element={<Replan />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/entities" element={<Entities />} />
          <Route path="/add-data" element={<AddData />} />
        </Routes>
      </main>

      <footer className="mx-auto max-w-6xl border-t-2 border-foreground px-5 py-6 font-mono text-xs uppercase tracking-widest text-muted-foreground">
        CP-SAT · FastAPI · React — all systems go
      </footer>
    </div>
  );
}
