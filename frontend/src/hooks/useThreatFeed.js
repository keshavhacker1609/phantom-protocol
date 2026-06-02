import { useState, useEffect, useCallback, useRef } from "react";
import { dashboardApi, threatsApi, meshApi } from "../utils/api";
import { useWebSocket } from "./useWebSocket";

export function useThreatFeed() {
  const [stats, setStats] = useState(null);
  const [attacks, setAttacks] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [meshIntel, setMeshIntel] = useState([]);
  const [meshStatus, setMeshStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const { connected, lastEvent, events } = useWebSocket();
  const intervalRef = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [statsRes, attacksRes, profilesRes, sessionsRes, intelRes, meshRes] =
        await Promise.allSettled([
          dashboardApi.getStats(),
          threatsApi.getFeed(50),
          threatsApi.getProfiles(20),
          dashboardApi.getSessions(),
          meshApi.getIntel(20),
          meshApi.getStatus(),
        ]);

      if (statsRes.status === "fulfilled") setStats(statsRes.value.data);
      if (attacksRes.status === "fulfilled") setAttacks(attacksRes.value.data.attacks || []);
      if (profilesRes.status === "fulfilled") setProfiles(profilesRes.value.data.profiles || []);
      if (sessionsRes.status === "fulfilled") setSessions(sessionsRes.value.data.sessions || []);
      if (intelRes.status === "fulfilled") setMeshIntel(intelRes.value.data.intel || []);
      if (meshRes.status === "fulfilled") setMeshStatus(meshRes.value.data);
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    intervalRef.current = setInterval(fetchAll, 8000);
    return () => clearInterval(intervalRef.current);
  }, [fetchAll]);

  useEffect(() => {
    if (!lastEvent) return;

    if (lastEvent.type === "attack_detected") {
      setStats((prev) => prev ? {
        ...prev,
        attacks_intercepted_today: (prev.attacks_intercepted_today || 0) + 1,
        active_phantom_sessions: (prev.active_phantom_sessions || 0) + 1,
      } : prev);

      setAttacks((prev) => [{
        id: `live-${Date.now()}`,
        session_id: lastEvent.session_id,
        attack_type: lastEvent.attack_type,
        severity: lastEvent.severity,
        confidence: lastEvent.confidence,
        is_phantom_active: lastEvent.phantom_active,
        created_at: lastEvent.timestamp,
        node_id: lastEvent.node_id,
      }, ...prev].slice(0, 100));
    }

    if (lastEvent.type === "mesh_intel_received") {
      setMeshIntel((prev) => [{
        threat_id: lastEvent.threat_id,
        attack_type: lastEvent.attack_type,
        sophistication_level: lastEvent.sophistication,
        affected_nodes: lastEvent.affected_nodes,
        pre_warned_minutes_ago: lastEvent.pre_warned_minutes_ago,
        timestamp: lastEvent.timestamp,
      }, ...prev].slice(0, 50));
    }
  }, [lastEvent]);

  return {
    stats,
    attacks,
    profiles,
    sessions,
    meshIntel,
    meshStatus,
    loading,
    wsConnected: connected,
    refresh: fetchAll,
  };
}
