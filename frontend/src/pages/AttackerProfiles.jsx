import { useState, useEffect } from "react";
import { threatsApi } from "../utils/api";
import { getSophisticationColor, getAttackColor } from "../utils/threatColors";
import { User, Target, Brain, ChevronDown, ChevronUp } from "lucide-react";

function ProfileCard({ profile }) {
  const [expanded, setExpanded] = useState(false);
  const sophColor = getSophisticationColor(profile.sophistication_level);
  const typeColor = getAttackColor(profile.attack_type);

  return (
    <div className="panel overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`text-xs px-2 py-0.5 rounded border ${sophColor.bg} ${sophColor.text} border-current/30`}>
                {sophColor.label}
              </span>
              <span className={`text-xs ${typeColor.text}`}>
                {typeColor.icon} {typeColor.label}
              </span>
              {profile.was_deceived && (
                <span className="text-xs bg-purple-900/30 border border-purple-800/50 text-purple-400 px-2 py-0.5 rounded">
                  👻 DECEIVED
                </span>
              )}
            </div>
            <div className="flex items-start gap-2">
              <Target size={14} className="text-red-400 mt-0.5 shrink-0" />
              <span className="text-sm font-semibold text-phantom-text">
                {profile.primary_intent}
              </span>
            </div>
          </div>
          <div className="text-right shrink-0">
            <div className="text-xs text-phantom-muted">{profile.turns_in_deception} turns deceived</div>
            <div className="text-xs text-green-400 font-mono">{(profile.confidence_score * 100).toFixed(0)}% conf</div>
            {expanded ? <ChevronUp size={14} className="text-phantom-muted ml-auto mt-1" /> : <ChevronDown size={14} className="text-phantom-muted ml-auto mt-1" />}
          </div>
        </div>

        {profile.target_assets?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {profile.target_assets.map((asset, i) => (
              <span key={i} className="text-xs bg-red-900/20 border border-red-900/30 text-red-400 px-2 py-0.5 rounded-full">
                {asset}
              </span>
            ))}
          </div>
        )}
      </div>

      {expanded && (
        <div className="border-t border-phantom-border px-4 pb-4 pt-3">
          {profile.attack_methodology && (
            <div className="mb-3">
              <div className="flex items-center gap-1.5 mb-1">
                <Brain size={12} className="text-phantom-muted" />
                <span className="text-xs text-phantom-muted uppercase tracking-wider">Methodology</span>
              </div>
              <p className="text-xs text-phantom-text-dim">{profile.attack_methodology}</p>
            </div>
          )}

          {profile.attack_steps?.length > 0 && (
            <div>
              <div className="text-xs text-phantom-muted uppercase tracking-wider mb-2">Attack Steps</div>
              <div className="space-y-1">
                {profile.attack_steps.map((step, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-xs text-red-500 font-mono w-4 shrink-0">{i + 1}.</span>
                    <span className="text-xs text-phantom-text-dim">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-3 pt-3 border-t border-phantom-border/30">
            <div className="text-xs text-phantom-muted">
              Profile ID: <span className="text-phantom-text-dim font-mono">{profile.profile_id}</span>
            </div>
            <div className="text-xs text-phantom-muted mt-0.5">
              Session: <span className="font-mono text-purple-400">{profile.session_id?.slice(-12)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AttackerProfiles() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");

  useEffect(() => {
    threatsApi.getProfiles(50)
      .then(r => setProfiles(r.data.profiles || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const levels = ["ALL", "NATION_STATE", "ADVANCED", "INTERMEDIATE", "SCRIPT_KIDDIE"];
  const filtered = filter === "ALL" ? profiles : profiles.filter(p => p.sophistication_level === filter);

  return (
    <div className="flex flex-col h-full gap-4 overflow-hidden">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-base font-bold text-phantom-text">Attacker Intent Profiles</h2>
          <p className="text-xs text-phantom-muted">{profiles.length} profiles extracted from deception sessions</p>
        </div>
        <div className="flex gap-2">
          {levels.map(l => (
            <button
              key={l}
              onClick={() => setFilter(l)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${
                filter === l
                  ? "border-cyan-600 bg-cyan-900/30 text-cyan-400"
                  : "border-phantom-border text-phantom-muted hover:border-phantom-text/30"
              }`}
            >
              {l.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {loading ? (
          Array(5).fill(0).map((_, i) => (
            <div key={i} className="panel h-24 animate-pulse bg-phantom-surface/50" />
          ))
        ) : filtered.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-phantom-text-dim text-sm">
            No profiles found for this filter
          </div>
        ) : (
          filtered.map((p, i) => <ProfileCard key={p.id || i} profile={p} />)
        )}
      </div>
    </div>
  );
}
