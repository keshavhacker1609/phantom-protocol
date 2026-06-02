import { useState, useEffect } from "react";
import { dashboardApi } from "../utils/api";
import { Ghost, Clock, MessageSquare } from "lucide-react";
import { getAttackColor } from "../utils/threatColors";

function SessionDetail({ session }) {
  const typeColor = getAttackColor(session.attack_type);
  const conf = session.deception_confidence || 0.95;
  const confColor = conf > 0.85 ? "text-green-400" : conf > 0.7 ? "text-yellow-400" : "text-red-400";
  const statusColor = session.status === "ACTIVE" ? "bg-green-900/30 border-green-800 text-green-400"
    : session.status === "COMPLETED" ? "bg-blue-900/30 border-blue-800 text-blue-400"
    : "bg-gray-900/30 border-gray-700 text-gray-400";

  return (
    <div className="panel p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <Ghost size={16} className={session.status === "ACTIVE" ? "text-purple-400 animate-pulse" : "text-purple-800"} />
          <code className="text-xs text-purple-300 font-mono">{session.session_id}</code>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded border ${statusColor}`}>
            {session.status || "ACTIVE"}
          </span>
          <span className={`text-xs font-bold font-mono ${confColor}`}>
            {(conf * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <div className="text-xs text-phantom-muted mb-1">Attack Type</div>
          <div className={`text-sm ${typeColor.text}`}>{typeColor.icon} {typeColor.label}</div>
        </div>
        <div>
          <div className="text-xs text-phantom-muted mb-1">Turns Deceived</div>
          <div className="flex items-center gap-1 text-sm text-phantom-text">
            <MessageSquare size={12} className="text-phantom-muted" />
            {session.conversation_turns || 0}
          </div>
        </div>
        {session.primary_intent && (
          <div className="col-span-2">
            <div className="text-xs text-phantom-muted mb-1">Attacker's Goal</div>
            <div className="text-xs text-phantom-text bg-red-900/10 border border-red-900/20 rounded p-2">
              {session.primary_intent}
            </div>
          </div>
        )}
      </div>

      {session.target_assets?.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {session.target_assets.map((a, i) => (
            <span key={i} className="text-xs bg-red-900/20 border border-red-900/30 text-red-400 px-2 py-0.5 rounded-full">
              {a}
            </span>
          ))}
        </div>
      )}

      <div className="h-1.5 bg-phantom-border rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-purple-700 to-purple-400 rounded-full"
          style={{ width: `${conf * 100}%` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-phantom-muted">Deception integrity</span>
        <span className="text-xs text-phantom-text-dim flex items-center gap-1">
          <Clock size={10} />
          {session.started_at ? new Date(session.started_at).toLocaleTimeString() : "—"}
        </span>
      </div>
    </div>
  );
}

export default function PhantomSessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = () => {
      dashboardApi.getSessions()
        .then(r => setSessions(r.data.sessions || []))
        .catch(console.error)
        .finally(() => setLoading(false));
    };
    fetch();
    const interval = setInterval(fetch, 5000);
    return () => clearInterval(interval);
  }, []);

  const active = sessions.filter(s => s.status === "ACTIVE" || !s.status);
  const completed = sessions.filter(s => s.status === "COMPLETED");

  return (
    <div className="flex flex-col h-full gap-4 overflow-hidden">
      <div className="shrink-0">
        <h2 className="text-base font-bold text-phantom-text">Phantom Sessions</h2>
        <p className="text-xs text-phantom-muted">
          {active.length} active deceptions · {completed.length} completed · Attacker never knew
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {active.length > 0 && (
          <div>
            <div className="text-xs text-purple-400 uppercase tracking-wider mb-2 flex items-center gap-2">
              <Ghost size={12} className="animate-pulse" />
              Active Deceptions ({active.length})
            </div>
            <div className="space-y-3">
              {active.map((s, i) => <SessionDetail key={s.session_id || i} session={s} />)}
            </div>
          </div>
        )}

        {completed.length > 0 && (
          <div>
            <div className="text-xs text-phantom-muted uppercase tracking-wider mb-2">
              Completed Sessions ({completed.length})
            </div>
            <div className="space-y-3">
              {completed.map((s, i) => <SessionDetail key={s.session_id || i} session={s} />)}
            </div>
          </div>
        )}

        {loading && sessions.length === 0 && (
          Array(3).fill(0).map((_, i) => (
            <div key={i} className="panel h-32 animate-pulse bg-phantom-surface/50" />
          ))
        )}

        {!loading && sessions.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-phantom-text-dim gap-2">
            <Ghost size={32} className="text-purple-900" />
            <span className="text-sm">No phantom sessions yet</span>
            <span className="text-xs">Waiting for attackers...</span>
          </div>
        )}
      </div>
    </div>
  );
}
