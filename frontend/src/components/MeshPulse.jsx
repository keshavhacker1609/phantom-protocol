import { Zap, Shield, Globe } from "lucide-react";

function formatAge(ts) {
  if (!ts) return "";
  const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function IntelCard({ intel }) {
  const preWarn = intel.pre_warned_minutes_ago;
  const isPreWarn = preWarn > 0;

  return (
    <div className={`border rounded-lg p-3 ${isPreWarn ? "border-cyan-800/50 bg-cyan-900/10" : "border-phantom-border bg-phantom-surface"}`}>
      <div className="flex items-start gap-2 mb-1">
        {isPreWarn ? (
          <Zap size={12} className="text-cyan-400 shrink-0 mt-0.5" />
        ) : (
          <Globe size={12} className="text-purple-400 shrink-0 mt-0.5" />
        )}
        <div className="flex-1 min-w-0">
          {isPreWarn && (
            <div className="text-xs text-cyan-400 font-semibold mb-0.5">
              ⚡ Pre-warned {preWarn}m before arrival
            </div>
          )}
          <div className="text-xs text-phantom-text-dim">
            <span className="text-phantom-text">{intel.attack_type?.replace(/_/g, " ")}</span>
            {intel.target_asset_type && (
              <span className="text-phantom-text-dim"> → {intel.target_asset_type}</span>
            )}
          </div>
          {intel.sophistication_level && (
            <div className="text-xs text-phantom-muted mt-0.5">
              {intel.sophistication_level} • {intel.affected_nodes || 1} node{(intel.affected_nodes || 1) !== 1 ? "s" : ""} affected
            </div>
          )}
        </div>
        <span className="text-xs text-phantom-text-dim shrink-0">{formatAge(intel.timestamp)}</span>
      </div>
    </div>
  );
}

export default function MeshPulse({ meshIntel = [], meshStatus }) {
  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={14} className="text-cyan-400 animate-pulse" />
          <span className="text-xs font-semibold text-phantom-text uppercase tracking-wider">
            Pre-emptive Warnings
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${meshStatus?.status === "CONNECTED" ? "bg-cyan-400" : "bg-red-400"} animate-pulse`} />
          <span className="text-xs text-phantom-text-dim">
            {meshStatus?.status || "CONNECTING"}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {meshIntel.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-phantom-text-dim text-xs gap-2">
            <Globe size={20} className="text-phantom-border" />
            <span>Monitoring mesh network...</span>
          </div>
        ) : (
          meshIntel.map((intel, i) => (
            <IntelCard key={intel.threat_id || i} intel={intel} />
          ))
        )}
      </div>
    </div>
  );
}
