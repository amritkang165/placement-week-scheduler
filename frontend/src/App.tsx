import { NavLink, Route, Routes } from "react-router-dom";
import { Moon, Sun } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Schedule from "./pages/Schedule";
import Replan from "./pages/Replan";
import Analytics from "./pages/Analytics";
import Entities from "./pages/Entities";
import AddData from "./pages/AddData";
import { cn } from "./lib/utils";
import { useTheme } from "./lib/theme";

const NAV = [
  { to: "/", label: "Board", end: true },
  { to: "/schedule", label: "Schedule" },
  { to: "/replan", label: "Disruptions" },
  { to: "/analytics", label: "Analytics" },
  { to: "/entities", label: "Entities" },
  { to: "/add-data", label: "Add Data" },
];

export default function App() {
  const { theme, toggle } = useTheme();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-baseline gap-6">
            <span className="display text-xl">Placement Week</span>
          </div>
          <nav className="hidden items-center gap-7 md:flex">
            {NAV.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    "label-mono transition-colors",
                    isActive ? "text-foreground underline underline-offset-8 decoration-accent decoration-2" : "hover:text-foreground",
                  )
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <button
              onClick={toggle}
              aria-label="Toggle theme"
              className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-muted"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12 md:py-16">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/replan" element={<Replan />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/entities" element={<Entities />} />
          <Route path="/add-data" element={<AddData />} />
        </Routes>
      </main>

      <footer className="mx-auto max-w-6xl border-t border-border px-6 py-8">
        <p className="label-mono">CP-SAT · FastAPI · React</p>
      </footer>
    </div>
  );
}
