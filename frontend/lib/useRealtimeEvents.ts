"use client";

import { useEffect, useRef, useCallback } from "react";
import type { LogEntry } from "@/components/dashboard/types";

const WS_BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL && process.env.NEXT_PUBLIC_BACKEND_URL !== ""
    ? process.env.NEXT_PUBLIC_BACKEND_URL
    : "http://localhost:8000";

function getWsUrl(): string {
  const url = new URL(WS_BASE);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return `${url.origin}/ws`;
}

export type RealtimeEvent =
  | { type: "log"; payload: LogEntry }
  | { type: "profile_update"; payload: { accountId: string } };

export type RealtimeEventHandlers = {
  onLog?: (log: LogEntry) => void;
  onProfileUpdate?: (accountId: string) => void;
};

export function useRealtimeEvents(handlers: RealtimeEventHandlers): void {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const onMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data) as RealtimeEvent;
      if (data.type === "log" && data.payload) {
        handlersRef.current.onLog?.(data.payload as LogEntry);
      } else if (data.type === "profile_update" && data.payload?.accountId) {
        handlersRef.current.onProfileUpdate?.(data.payload.accountId);
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  useEffect(() => {
    const url = getWsUrl();
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      try {
        ws = new WebSocket(url);
        ws.onmessage = onMessage;
        ws.onclose = () => {
          ws = null;
          reconnectTimeout = setTimeout(connect, 3000);
        };
        ws.onerror = () => {
          ws?.close();
        };
      } catch {
        reconnectTimeout = setTimeout(connect, 3000);
      }
    }

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, [onMessage]);
}
