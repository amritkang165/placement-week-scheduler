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
      <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <div className="flex items-baseline gap-3">
            <span className="font-display text-xl font-semibold tracking-tight">
              Placement Week
            </span>
            <span className="hidden text-sm text-muted-foreground sm:inline">
              Coordinators’ Board
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggle}
              aria-label="Toggle theme"
              className="flex h-9 w-9 items-center justify-center rounded-md border border-border text-foreground hover:bg-muted"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <button
              aria-label="Notifications"
              className="relative flex h-9 w-9 items-center justify-center rounded-md border border-border text-foreground hover:bg-muted"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-accent" />
            </button>
          </div>
        </div>
        {/* nav */}
        <nav className="mx-auto max-w-6xl overflow-x-auto px-5">
          <div className="flex gap-1">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground",
                    isActive
                      ? "border-accent text-foreground"
                      : "border-transparent",
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

      <footer className="mx-auto max-w-6xl px-5 pb-10 text-xs text-muted-foreground">
        CP-SAT · FastAPI · React
      </footer>
    </div>
  );
}
