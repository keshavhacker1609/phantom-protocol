import StatCards from "../components/StatCards";
import AttackTimeline from "../components/AttackTimeline";
import ThreatMap from "../components/ThreatMap";
import PhantomModeCard from "../components/PhantomModeCard";
import MeshPulse from "../components/MeshPulse";
import TrustScoreGauge from "../components/TrustScoreGauge";
import { useThreatFeed } from "../hooks/useThreatFeed";

export default function Dashboard() {
  const { stats, attacks, sessions, meshIntel, meshStatus, loading, wsConnected } = useThreatFeed();

  return (
    <div className="flex flex-col gap-3 h-full overflow-hidden">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-bold text-phantom-text tracking-wider">
            <span className="text-red-400 animate-glow-red">PHANTOM</span>
            <span className="text-phantom-text-dim"> PROTOCOL</span>
            <span className="text-xs text-phantom-muted ml-3 font-normal">WAR ROOM</span>
          </h1>
          <p className="text-xs text-phantom-muted">Every attacker thinks they succeeded. None of them did.</p>
        </div>
        <div className="flex items-center gap-4">
          <TrustScoreGauge score={stats?.deception_success_rate || 0.973} label="Deception Rate" />
          <div className="text-right">
            <div className="flex items-center gap-1.5 justify-end mb-1">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? "bg-cyan-400 animate-pulse" : "bg-red-400"}`} />
              <span className="text-xs text-phantom-text-dim">
                {wsConnected ? "LIVE" : "RECONNECTING"}
              </span>
            </div>
            <div className="text-xs text-phantom-muted">
              Node: <span className="text-cyan-400 font-mono">{stats?.node_id?.slice(-8) || "—"}</span>
            </div>
            <div className="text-xs text-phantom-muted">
              Status: <span className="text-green-400">{stats?.status || "OPERATIONAL"}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="shrink-0">
        <StatCards stats={stats} />
      </div>

      <div className="flex gap-3 flex-1 min-h-0">
        <div className="flex flex-col gap-3 w-72 shrink-0">
          <div className="flex-1 min-h-0">
            <PhantomModeCard sessions={sessions} />
          </div>
          <div className="flex-1 min-h-0">
            <MeshPulse meshIntel={meshIntel} meshStatus={meshStatus} />
          </div>
        </div>

        <div className="flex flex-col gap-3 flex-1 min-w-0">
          <div className="h-52 shrink-0">
            <ThreatMap attacks={attacks} meshStatus={meshStatus} />
          </div>
          <div className="flex-1 min-h-0">
            <AttackTimeline attacks={attacks} />
          </div>
        </div>
      </div>
    </div>
  );
}
