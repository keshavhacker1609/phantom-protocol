import { useState, useEffect } from "react";
import { meshApi } from "../utils/api";
import ThreatMap from "../components/ThreatMap";
import { Globe, Zap, Shield } from "lucide-react";

function NodeCard({ node }) {
  const isSelf = node.is_self;
  const isActive = node.status === "ACTIVE";

  return (
    <div className={`border rounded-lg p-3 ${isSelf ? "border-cyan-700/60 bg-cyan-900/10" : isActive ? "border-phantom-border bg-phantom-surface" : "border-phantom-border/30 bg-phantom-bg opacity-60"}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isActive ? "bg-cyan-400 animate-pulse" : "bg-red-400"}`} />
          <code className="text-xs text-phantom-text font-mono">{node.id?.slice(-12)}</code>
          {isSelf && <span className="text-xs bg-cyan-900/30 border border-cyan-800/50 text-cyan-400 px-1.5 py-0.5 rounded-full">YOU</span>}
        </div>
        <span className={`text-xs ${isActive ? "text-green-400" : "text-red-400"}`}>{node.status}</span>
      </div>
      <div className="text-xs text-phantom-muted">{node.location}</div>
      <div className="text-xs text-phantom-text-dim mt-1">
        <Zap size={10} className="inline text-orange-400 mr-1" />
        {node.attacks_shared || 0} attacks shared
      </div>
    </div>
  );
}

export default function ThreatMesh() {
  const [nodes, setNodes] = useState([]);
  const [intel, setIntel] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      const [nodesRes, intelRes, statusRes] = await Promise.allSettled([
        meshApi.getNodes(),
        meshApi.getIntel(30),
        meshApi.getStatus(),
      ]);
      if (nodesRes.status === "fulfilled") setNodes(nodesRes.value.data.nodes || []);
      if (intelRes.status === "fulfilled") setIntel(intelRes.value.data.intel || []);
      if (statusRes.status === "fulfilled") setStatus(statusRes.value.data);
      setLoading(false);
    };
    fetch();
    const i = setInterval(fetch, 10000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="flex flex-col h-full gap-4 overflow-hidden">
      <div className="shrink-0 flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-phantom-text flex items-center gap-2">
            <Globe size={16} className="text-cyan-400" />
            Global Threat Mesh
          </h2>
          <p className="text-xs text-phantom-muted">
            {status?.connected_nodes || "—"} peers connected · Real-time threat intelligence sharing
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <div className="text-phantom-muted">Intel shared: <span className="text-orange-400">{status?.intel_shared || "—"}</span></div>
          <div className="text-phantom-muted">Intel received: <span className="text-cyan-400">{status?.intel_received || "—"}</span></div>
        </div>
      </div>

      <div className="h-64 shrink-0">
        <ThreatMap attacks={[]} meshStatus={status} />
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        <div className="w-64 shrink-0">
          <div className="text-xs text-phantom-muted uppercase tracking-wider mb-2 flex items-center gap-2">
            <Globe size={12} /> Network Nodes
          </div>
          <div className="space-y-2 overflow-y-auto" style={{ maxHeight: "300px" }}>
            {nodes.map((n, i) => <NodeCard key={n.id || i} node={n} />)}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="text-xs text-phantom-muted uppercase tracking-wider mb-2 flex items-center gap-2">
            <Shield size={12} className="text-cyan-400" /> Received Threat Intelligence
          </div>
          <div className="space-y-2 overflow-y-auto" style={{ maxHeight: "300px" }}>
            {intel.map((item, i) => (
              <div key={item.threat_id || i} className="panel p-3">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <span className="text-xs text-orange-400 font-semibold">
                      {item.attack_type?.replace(/_/g, " ")}
                    </span>
                    {item.pre_warned_minutes_ago > 0 && (
                      <span className="ml-2 text-xs bg-cyan-900/30 border border-cyan-800/50 text-cyan-400 px-1.5 py-0.5 rounded">
                        ⚡ +{item.pre_warned_minutes_ago}m warning
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-phantom-muted">
                    {item.affected_nodes || 1} node{(item.affected_nodes || 1) !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="text-xs text-phantom-text-dim">
                  Target: <span className="text-phantom-text">{item.target_asset_type || "Unknown"}</span>
                  {" · "}
                  <span className={item.sophistication_level === "NATION_STATE" ? "text-red-400" : item.sophistication_level === "ADVANCED" ? "text-orange-400" : "text-yellow-400"}>
                    {item.sophistication_level}
                  </span>
                </div>
                {item.pre_emptive_signatures?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {item.pre_emptive_signatures.slice(0, 3).map((sig, j) => (
                      <code key={j} className="text-xs bg-phantom-bg border border-phantom-border/50 text-phantom-muted px-1.5 py-0.5 rounded">
                        {sig}
                      </code>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
