import { LogEntry } from "@/components/dashboard/types";

type Props = {
  logs: LogEntry[];
};

export function LogsOverview({ logs }: Props) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
      <h2 className="text-sm font-semibold">Recent Logs</h2>
      <p className="mt-1 text-[11px] text-zinc-500">
        High-level view across all accounts.
      </p>
      <div className="mt-3 max-h-64 space-y-2 overflow-y-auto pr-1 text-xs">
        {logs.map((log) => (
          <div
            key={log.id}
            className="rounded-xl border border-zinc-100 bg-zinc-50 px-3 py-2 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-[11px] text-zinc-500">
                {log.timestamp}
              </span>
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  log.level === "info"
                    ? "bg-zinc-100 text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
                    : log.level === "warning"
                    ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-900"
                    : "bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900"
                }`}
              >
                {log.level.toUpperCase()}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-zinc-500">
              Account #{log.accountId} · {log.source}
            </p>
            <p className="mt-1 text-xs">{log.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

