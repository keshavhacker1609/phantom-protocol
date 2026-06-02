import { Shield, AlertTriangle, Globe, Zap, Eye, TrendingUp } from "lucide-react";

const Card = ({ icon: Icon, label, value, color, subtitle }) => (
  <div className="panel p-4 flex items-start gap-3">
    <div className={`p-2 rounded-lg bg-${color}-900/30 border border-${color}-800/50`}>
      <Icon size={18} className={`text-${color}-400`} />
    </div>
    <div className="flex-1 min-w-0">
      <div className="text-xs text-phantom-text-dim uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-2xl font-bold text-${color}-400 font-mono`}>{value}</div>
      {subtitle && <div className="text-xs text-phantom-text-dim mt-0.5">{subtitle}</div>}
    </div>
  </div>
);

export default function StatCards({ stats }) {
  const v = (n, fallback = 0) => (n ?? fallback).toLocaleString();
  const pct = (n) => n != null ? `${(n * 100).toFixed(1)}%` : "—";

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      <Card icon={AlertTriangle} label="Attacks Today" value={v(stats?.attacks_intercepted_today)} color="red" subtitle="Intercepted" />
      <Card icon={Eye} label="Phantom Sessions" value={v(stats?.active_phantom_sessions)} color="purple" subtitle="Active deceptions" />
      <Card icon={Globe} label="Mesh Nodes" value={v(stats?.mesh_nodes_connected)} color="cyan" subtitle="Connected peers" />
      <Card icon={Zap} label="Warnings Sent" value={v(stats?.preemptive_warnings_sent)} color="orange" subtitle="To network" />
      <Card icon={Shield} label="Warnings Rcvd" value={v(stats?.preemptive_warnings_received)} color="cyan" subtitle="Pre-emptive" />
      <Card icon={TrendingUp} label="Deception Rate" value={pct(stats?.deception_success_rate)} color="green" subtitle="Success" />
    </div>
  );
}
