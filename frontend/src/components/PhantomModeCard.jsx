import { Ghost, Clock, Target } from "lucide-react";

function formatAge(dateStr) {
  if (!dateStr) return "just now";
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function SessionCard({ session }) {
  const conf = session.deception_confidence || 0.95;
  const confColor = conf > 0.85 ? "text-green-400" : conf > 0.7 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="border border-purple-800/40 rounded-lg p-3 bg-purple-900/10 hover:bg-purple-900/15 transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <Ghost size={14} className="text-purple-400 animate-pulse" />
          <span className="text-xs font-mono text-purple-300">{session.session_id?.slice(-8) || "—"}</span>
        </div>
        <span className={`text-xs font-bold ${confColor}`}>{(conf * 100).toFixed(0)}%</span>
      </div>

      <div className="space-y-1">
        {session.attack_type && (
          <div className="text-xs text-phantom-text-dim">
            <span className="text-phantom-muted">Type: </span>
            <span className="text-orange-400">{session.attack_type.replace("_", " ")}</span>
          </div>
        )}
        {session.primary_intent && (
          <div className="text-xs text-phantom-text-dim truncate">
            <span className="text-phantom-muted">Intent: </span>
            <span className="text-phantom-text">{session.primary_intent}</span>
          </div>
        )}
        <div className="flex items-center gap-3 text-xs text-phantom-text-dim">
          <span className="flex items-center gap-1">
            <Clock size={10} />
            {formatAge(session.started_at)}
          </span>
          <span>{session.conversation_turns || 0} turns</span>
        </div>
      </div>

      <div className="mt-2">
        <div className="h-1 bg-phantom-border rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-600 to-purple-400 rounded-full transition-all duration-500"
            style={{ width: `${conf * 100}%` }}
          />
        </div>
        <div className="text-xs text-phantom-muted mt-0.5">Deception integrity</div>
      </div>
    </div>
  );
}

export default function PhantomModeCard({ sessions }) {
  const activeSessions = (sessions || []).filter(s => s.status === "ACTIVE" || !s.status);

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Ghost size={14} className="text-purple-400 animate-pulse" />
          <span className="text-xs font-semibold text-phantom-text uppercase tracking-wider">Active Phantom Sessions</span>
        </div>
        <span className="text-xs bg-purple-900/30 border border-purple-800/50 text-purple-400 px-2 py-0.5 rounded-full">
          {activeSessions.length} ACTIVE
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {activeSessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-phantom-text-dim text-xs gap-2">
            <Ghost size={24} className="text-purple-800" />
            <span>No active deceptions</span>
          </div>
        ) : (
          activeSessions.map((s, i) => (
            <SessionCard key={s.session_id || i} session={s} />
          ))
        )}
      </div>
    </div>
  );
}
