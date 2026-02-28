import { Account, LogEntry } from "@/components/dashboard/types";

type Props = {
  account: Account | null;
  logs: LogEntry[];
  onClose: () => void;
};

export function AccountLogsDrawer({ account, logs, onClose }: Props) {
  if (!account) return null;

  const accountLogs = logs.filter((log) => log.accountId === account.id);

  return (
    <div className="fixed inset-x-0 bottom-0 z-20 border-t border-zinc-200 bg-white/95 backdrop-blur dark:border-zinc-800 dark:bg-black/95">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-3 md:px-8">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold">Logs · {account.name}</p>
            <p className="text-[11px] text-zinc-500">
              Action, error, and API logs for this account.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full border border-zinc-200 px-3 py-1.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
          >
            Close
          </button>
        </div>
        <div className="max-h-56 overflow-y-auto pr-1 text-xs">
          {accountLogs.length === 0 ? (
            <p className="text-[11px] text-zinc-500">
              No logs for this account yet.
            </p>
          ) : (
            <div className="space-y-2">
              {accountLogs.map((log) => (
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
                    {log.source} log
                  </p>
                  <p className="mt-1 text-xs">{log.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

