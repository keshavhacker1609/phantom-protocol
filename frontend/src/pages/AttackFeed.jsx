import { useState, useEffect } from "react";
import { threatsApi } from "../utils/api";
import { getSeverityColor, getAttackColor } from "../utils/threatColors";
import { AlertTriangle, Ghost } from "lucide-react";

function AttackDetail({ attack, expanded, onClick }) {
  const sev = getSeverityColor(attack.severity);
  const type = getAttackColor(attack.attack_type);

  return (
    <div
      className={`border rounded-lg overflow-hidden cursor-pointer transition-all ${sev.border} bg-phantom-surface hover:bg-white/[0.02]`}
      onClick={onClick}
    >
      <div className="flex items-center gap-3 p-3">
        <span className="w-2.5 h-2.5 rounded-full shrink-0 animate-pulse" style={{ backgroundColor: sev.dot }} />
        <span className={`text-xs font-semibold shrink-0 ${type.text}`}>{type.icon} {type.label}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded ${sev.bg} ${sev.text} border ${sev.border} shrink-0`}>{attack.severity}</span>
        {attack.is_phantom_active && (
          <span className="text-xs text-purple-400 shrink-0">👻 Phantom</span>
        )}
        <span className="text-xs text-phantom-text-dim truncate flex-1">{attack.anonymized_input || "—"}</span>
        <span className="text-xs text-phantom-text-dim shrink-0 font-mono">
          {attack.confidence ? `${(attack.confidence * 100).toFixed(0)}%` : "—"}
        </span>
        <span className="text-xs text-phantom-text-dim shrink-0">
          {attack.created_at ? new Date(attack.created_at).toLocaleTimeString() : "—"}
        </span>
      </div>

      {expanded && (
        <div className="border-t border-phantom-border/30 p-3 bg-phantom-bg/50 space-y-2">
          <div>
            <span className="text-xs text-phantom-muted">Session: </span>
            <code className="text-xs text-purple-300 font-mono">{attack.session_id}</code>
          </div>
          {attack.attacker_intent && (
            <div>
              <span className="text-xs text-phantom-muted">Intent: </span>
              <span className="text-xs text-phantom-text">{attack.attacker_intent}</span>
            </div>
          )}
          {attack.anonymized_input && (
            <div>
              <span className="text-xs text-phantom-muted block mb-1">Attacker Input:</span>
              <code className="text-xs text-red-300 bg-red-900/10 border border-red-900/20 rounded p-2 block">
                {attack.anonymized_input}
              </code>
            </div>
          )}
          {attack.phantom_response && (
            <div>
              <span className="text-xs text-phantom-muted block mb-1">Phantom Response Served:</span>
              <code className="text-xs text-purple-300 bg-purple-900/10 border border-purple-900/20 rounded p-2 block">
                {attack.phantom_response}
              </code>
            </div>
          )}
          {attack.node_id && (
            <div className="text-xs text-phantom-muted">
              Node: <span className="text-cyan-400 font-mono">{attack.node_id}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AttackFeed() {
  const [attacks, setAttacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [severityFilter, setSeverityFilter] = useState("ALL");

  useEffect(() => {
    const fetch = () => {
      threatsApi.getFeed(100)
        .then(r => setAttacks(r.data.attacks || []))
        .catch(console.error)
        .finally(() => setLoading(false));
    };
    fetch();
    const interval = setInterval(fetch, 5000);
    return () => clearInterval(interval);
  }, []);

  const severities = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"];
  const filtered = severityFilter === "ALL" ? attacks : attacks.filter(a => a.severity === severityFilter);

  return (
    <div className="flex flex-col h-full gap-4 overflow-hidden">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-base font-bold text-phantom-text flex items-center gap-2">
            <AlertTriangle size={16} className="text-red-400" />
            Live Attack Feed
          </h2>
          <p className="text-xs text-phantom-muted">{attacks.length} attacks intercepted · All diverted to phantom mode</p>
        </div>
        <div className="flex gap-2">
          {severities.map(s => {
            const col = getSeverityColor(s);
            return (
              <button
                key={s}
                onClick={() => setSeverityFilter(s)}
                className={`text-xs px-2 py-1 rounded border transition-colors ${
                  severityFilter === s
                    ? `${s === "ALL" ? "border-cyan-600 bg-cyan-900/30 text-cyan-400" : `${col.border} ${col.bg} ${col.text}`}`
                    : "border-phantom-border text-phantom-muted hover:border-phantom-text/30"
                }`}
              >
                {s}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {loading ? (
          Array(5).fill(0).map((_, i) => (
            <div key={i} className="panel h-14 animate-pulse bg-phantom-surface/50 rounded-lg" />
          ))
        ) : filtered.map((attack, i) => (
          <AttackDetail
            key={attack.id || i}
            attack={attack}
            expanded={expanded === (attack.id || i)}
            onClick={() => setExpanded(expanded === (attack.id || i) ? null : (attack.id || i))}
          />
        ))}
      </div>
    </div>
  );
}
