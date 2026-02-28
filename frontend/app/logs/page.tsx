"use client";

import { useEffect, useState } from "react";
import { LogEntry } from "@/components/dashboard/types";
import { LogsOverview } from "@/components/dashboard/LogsOverview";
import { fetchLogs } from "@/lib/automationClient";
import { useRealtimeEvents } from "@/lib/useRealtimeEvents";

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const logsData = await fetchLogs();
        if (cancelled) return;
        setLogs(logsData);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setLoadError("Failed to load logs from backend.");
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  useRealtimeEvents({
    onLog: (log) => {
      setLogs((prev) => [log, ...prev].slice(0, 200));
    },
  });

  return (
    <main className="flex flex-col gap-6">
      <section>
        <h2 className="text-sm font-semibold">Logs</h2>
        <p className="mt-1 text-xs text-zinc-500">
          Browse high-level action, error, and API logs across all accounts.
        </p>
        {loadError && (
          <p className="mt-1 text-[11px] text-rose-500">{loadError}</p>
        )}
      </section>

      <section>
        <LogsOverview logs={logs} />
      </section>
    </main>
  );
}

