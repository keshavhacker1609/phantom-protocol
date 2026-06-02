import { useState, useEffect } from "react";
import { getSeverityColor, getAttackColor } from "../utils/threatColors";

function formatTime(ts) {
  if (!ts) return "--:--:--";
  const d = new Date(ts);
  return d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function AttackRow({ attack, isNew }) {
  const sev = getSeverityColor(attack.severity);
  const type = getAttackColor(attack.attack_type);

  return (
    <div className={`flex items-center gap-3 px-3 py-2 border-b border-phantom-border/30 hover:bg-white/[0.02] transition-colors ${isNew ? "attack-row-enter" : ""}`}>
      <span className="text-xs text-phantom-text-dim w-20 shrink-0 font-mono">{formatTime(attack.created_at)}</span>
      <span className={`w-2 h-2 rounded-full shrink-0 animate-pulse`} style={{ backgroundColor: sev.dot }} />
      <span className={`text-xs font-medium w-32 shrink-0 ${type.text}`}>
        {type.icon} {type.label}
      </span>
      <span className={`text-xs px-1.5 py-0.5 rounded ${sev.bg} ${sev.text} ${sev.border} border shrink-0`}>
        {attack.severity}
      </span>
      {attack.is_phantom_active && (
        <span className="text-xs px-1.5 py-0.5 rounded bg-purple-900/30 border border-purple-800/50 text-purple-400 shrink-0">
          👻 PHANTOM
        </span>
      )}
      <span className="text-xs text-phantom-text-dim truncate flex-1">
        {attack.anonymized_input || attack.attacker_intent || "—"}
      </span>
      <span className="text-xs text-phantom-text-dim w-12 text-right shrink-0">
        {attack.confidence ? `${(attack.confidence * 100).toFixed(0)}%` : "—"}
      </span>
    </div>
  );
}

export default function AttackTimeline({ attacks }) {
  const [newIds, setNewIds] = useState(new Set());

  useEffect(() => {
    if (!attacks.length) return;
    const newestId = attacks[0]?.id;
    if (newestId) {
      setNewIds((prev) => new Set([...prev, newestId]));
      const timer = setTimeout(() => {
        setNewIds((prev) => {
          const next = new Set(prev);
          next.delete(newestId);
          return next;
        });
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [attacks[0]?.id]);

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
          <span className="text-xs font-semibold text-phantom-text uppercase tracking-wider">Live Attack Feed</span>
        </div>
        <span className="text-xs text-phantom-text-dim">{attacks.length} events</span>
      </div>

      <div className="flex items-center gap-3 px-3 py-1.5 border-b border-phantom-border/30 bg-phantom-bg/30">
        <span className="text-xs text-phantom-text-dim w-20">TIME</span>
        <span className="w-2" />
        <span className="text-xs text-phantom-text-dim w-32">TYPE</span>
        <span className="text-xs text-phantom-text-dim w-16">SEV</span>
        <span className="text-xs text-phantom-text-dim w-20">STATUS</span>
        <span className="text-xs text-phantom-text-dim flex-1">DETAILS</span>
        <span className="text-xs text-phantom-text-dim w-12 text-right">CONF</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {attacks.length === 0 ? (
          <div className="flex items-center justify-center h-full text-phantom-text-dim text-xs">
            Monitoring for attacks...
          </div>
        ) : (
          attacks.map((attack) => (
            <AttackRow key={attack.id} attack={attack} isNew={newIds.has(attack.id)} />
          ))
        )}
      </div>
    </div>
  );
}
