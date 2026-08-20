import { useEffect, useRef } from 'react';

/**
 * Connect to a Django Channels WebSocket with JWT auth.
 * @param {string|null} path e.g. "tickets/14/" or "notifications/". Pass null to skip.
 * @param {(data: object) => void} onMessage handler for each parsed JSON message
 */
export default function useWebSocket(path, onMessage) {
  const socketRef = useRef(null);
  const handlerRef = useRef(onMessage);
  const reconnectTimerRef = useRef(null);
  const shouldReconnectRef = useRef(true);

  // Keep the latest handler without re-connecting
  useEffect(() => {
    handlerRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    if (!path) return;

    shouldReconnectRef.current = true;

    const connect = () => {
      const token = localStorage.getItem('access');
      if (!token) return;

      // ws:// for http, wss:// for https
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      // Backend runs on 8000
      const url = `${proto}//${host}:8000/ws/${path}?token=${encodeURIComponent(token)}`;

      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] connected:', path);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handlerRef.current?.(data);
        } catch (err) {
          console.warn('[WS] bad JSON', err);
        }
      };

      ws.onclose = (event) => {
        console.log('[WS] closed:', path, event.code);
        socketRef.current = null;
        // Auto-reconnect (unless we intentionally closed or auth failed)
        if (shouldReconnectRef.current && event.code !== 4001) {
          reconnectTimerRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = (err) => {
        console.warn('[WS] error:', err);
      };
    };

    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [path]);
}