import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import AttackFeed from "./pages/AttackFeed";
import ThreatMesh from "./pages/ThreatMesh";
import AttackerProfiles from "./pages/AttackerProfiles";
import PhantomSessions from "./pages/PhantomSessions";
import { useWebSocket } from "./hooks/useWebSocket";
import { Shield, Radio, Globe, User, Ghost, Activity } from "lucide-react";

const navItems = [
  { to: "/", label: "War Room", icon: Activity },
  { to: "/attacks", label: "Attack Feed", icon: Radio },
  { to: "/mesh", label: "Threat Mesh", icon: Globe },
  { to: "/profiles", label: "Attacker Profiles", icon: User },
  { to: "/sessions", label: "Phantom Sessions", icon: Ghost },
];

function Sidebar({ wsConnected }) {
  return (
    <div className="w-48 shrink-0 flex flex-col border-r border-phantom-border bg-phantom-surface">
      <div className="p-4 border-b border-phantom-border">
        <div className="flex items-center gap-2 mb-1">
          <Shield size={16} className="text-red-400" />
          <span className="text-xs font-bold text-red-400 tracking-widest">PHANTOM</span>
        </div>
        <div className="text-xs text-phantom-muted tracking-wider">PROTOCOL v1.0</div>
        <div className="flex items-center gap-1.5 mt-2">
          <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? "bg-cyan-400 animate-pulse" : "bg-red-400"}`} />
          <span className="text-xs text-phantom-muted">{wsConnected ? "LIVE FEED" : "RECONNECTING"}</span>
        </div>
      </div>

      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-all ${
                isActive
                  ? "bg-red-900/20 border border-red-900/30 text-red-400"
                  : "text-phantom-muted hover:text-phantom-text hover:bg-white/[0.03]"
              }`
            }
          >
            <Icon size={14} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-phantom-border">
        <div className="text-xs text-phantom-muted text-center">
          <div className="text-green-400 font-bold mb-0.5">SYSTEM SECURE</div>
          <div>All threats diverted</div>
        </div>
      </div>
    </div>
  );
}

function AppContent() {
  const { wsConnected, lastEvent } = useWebSocket();
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    if (!lastEvent) return;
    if (lastEvent.type === "attack_detected") {
      setAlert({
        type: "attack",
        message: `⚡ ${lastEvent.attack_type?.replace(/_/g, " ")} intercepted → Phantom Mode activated`,
        severity: lastEvent.severity,
      });
      const t = setTimeout(() => setAlert(null), 4000);
      return () => clearTimeout(t);
    }
  }, [lastEvent]);

  return (
    <div className="flex h-screen bg-phantom-bg overflow-hidden">
      <div className="scanline" />
      <Sidebar wsConnected={wsConnected} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {alert && (
          <div className={`shrink-0 px-4 py-2 text-xs font-semibold flex items-center gap-2 animate-pulse ${
            alert.severity === "CRITICAL" ? "bg-red-900/40 border-b border-red-800 text-red-300"
            : alert.severity === "HIGH" ? "bg-orange-900/40 border-b border-orange-800 text-orange-300"
            : "bg-yellow-900/30 border-b border-yellow-800 text-yellow-300"
          }`}>
            <span>{alert.message}</span>
          </div>
        )}

        <main className="flex-1 overflow-hidden p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/attacks" element={<AttackFeed />} />
            <Route path="/mesh" element={<ThreatMesh />} />
            <Route path="/profiles" element={<AttackerProfiles />} />
            <Route path="/sessions" element={<PhantomSessions />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
