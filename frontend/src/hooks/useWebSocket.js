import { useEffect, useRef, useState, useCallback } from "react";
import { WS_URL } from "../utils/api";

export function useWebSocket() {
  const ws = useRef(null);
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const [events, setEvents] = useState([]);
  const reconnectTimer = useRef(null);
  const mounted = useRef(true);

  const connect = useCallback(() => {
    if (!mounted.current) return;
    try {
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        if (!mounted.current) return;
        setConnected(true);
        if (reconnectTimer.current) {
          clearTimeout(reconnectTimer.current);
          reconnectTimer.current = null;
        }
      };

      ws.current.onmessage = (evt) => {
        if (!mounted.current) return;
        try {
          const data = JSON.parse(evt.data);
          if (data.type === "heartbeat" || data.type === "connection_established") return;
          setLastEvent(data);
          setEvents((prev) => [data, ...prev].slice(0, 100));
        } catch (_) {}
      };

      ws.current.onclose = () => {
        if (!mounted.current) return;
        setConnected(false);
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.current.onerror = () => {
        if (!mounted.current) return;
        setConnected(false);
      };
    } catch (err) {
      console.error("WebSocket connection error:", err);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    connect();
    return () => {
      mounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (ws.current) ws.current.close();
    };
  }, [connect]);

  return { connected, lastEvent, events };
}
