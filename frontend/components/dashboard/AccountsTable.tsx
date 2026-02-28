import {
  Account,
  AccountStatus,
  BulkActionType,
  SessionState,
} from "@/components/dashboard/types";

type Props = {
  accounts: Account[];
  selectedAccountIds?: Set<string>;
  onToggleSelectAll?: () => void;
  onToggleSelect?: (id: string) => void;
  autoChatRunningIds?: Set<string>;
  autoSwipeRunningIds?: Set<string>;
  onAutoChatToggle?: (account: Account) => void;
  onAutoSwipeToggle?: (account: Account) => void;
  onBulkAction?: (action: BulkActionType) => void;
  onOpenLogs?: (account: Account) => void;
  onViewProfile?: (account: Account) => void;
  onEdit?: (account: Account) => void;
  onDelete?: (account: Account) => void;
  onAddAccount?: () => void;
  readOnly?: boolean;
};

const statusBadgeClasses: Record<AccountStatus, string> = {
  active:
    "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-900",
  paused:
    "bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-900",
  error:
    "bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900",
  pending:
    "bg-sky-50 text-sky-700 ring-1 ring-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:ring-sky-900",
};

const sessionBadgeClasses: Record<SessionState, string> = {
  ok: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-900",
  expiring:
    "bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-900",
  expired:
    "bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900",
  login_required:
    "bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900",
  blocked:
    "bg-red-50 text-red-700 ring-1 ring-red-200 dark:bg-red-950/40 dark:text-red-300 dark:ring-red-900",
};

export function AccountsTable({
  accounts,
  selectedAccountIds = new Set(),
  onToggleSelectAll,
  onToggleSelect,
  autoChatRunningIds = new Set(),
  autoSwipeRunningIds = new Set(),
  onAutoChatToggle,
  onAutoSwipeToggle,
  onBulkAction,
  onOpenLogs,
  onViewProfile,
  onEdit,
  onDelete,
  onAddAccount,
  readOnly = false,
}: Props) {
  return (
    <div className="w-full rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900 lg:col-span-2">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold">Accounts</h2>
          <p className="text-xs text-zinc-500">
            {readOnly
              ? "Account list (manage on Accounts page)."
              : "Add, manage, and monitor automation state."}
          </p>
        </div>
        {!readOnly && (
          <div className="flex items-center gap-2">
            <button
              className="rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
              type="button"
              onClick={onAddAccount}
            >
              Add Account
            </button>
          </div>
        )}
      </div>

      <div className="overflow-x-auto overflow-y-hidden rounded-xl border border-zinc-100 bg-zinc-50/70 dark:border-zinc-800 dark:bg-zinc-900/40">
        <table className="w-full min-w-[720px] border-collapse text-xs">
          <thead>
            <tr className="border-b border-zinc-100 bg-zinc-50 text-[11px] font-medium text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
              <th className="px-3 py-2 text-left">
                {readOnly ? (
                  "Account"
                ) : (
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      className="h-3.5 w-3.5 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900 dark:border-zinc-600 dark:bg-zinc-900"
                      checked={selectedAccountIds.size === accounts.length}
                      onChange={onToggleSelectAll}
                    />
                    <span>Account</span>
                  </div>
                )}
              </th>
              <th className="px-3 py-2 text-left">Proxy</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Token / Session</th>
              <th className="px-3 py-2 text-left">Today</th>
              {!readOnly && (
                <th className="px-3 py-2 text-right">Actions</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {accounts.map((account) => {
              const isSelected = selectedAccountIds.has(account.id);
              const isRunning =
                autoSwipeRunningIds.has(account.id) ||
                autoChatRunningIds.has(account.id);
              const tokenSoonExpiring =
                !["expired", "blocked"].includes(account.sessionState) &&
                account.sessionState !== "ok";

              return (
                <tr
                  key={account.id}
                  className="bg-white/70 text-xs transition hover:bg-zinc-50 dark:bg-black/40 dark:hover:bg-zinc-900/80"
                >
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      {!readOnly && (
                        <input
                          type="checkbox"
                          className="h-3.5 w-3.5 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900 dark:border-zinc-600 dark:bg-zinc-900"
                          checked={isSelected}
                          onChange={() => onToggleSelect?.(account.id)}
                        />
                      )}
                      <div>
                        <p className="font-medium">{account.name}</p>
                        <p className="text-[11px] text-zinc-500">
                          Last active {account.lastActive || "—"}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="max-w-0 truncate px-3 py-2 text-[11px] text-zinc-500">
                    {account.proxy ?? (
                      <span className="italic text-zinc-400">No proxy</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${
                        isRunning
                          ? statusBadgeClasses.active
                          : statusBadgeClasses[account.status]
                      }`}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-current" />
                      {isRunning && "Active"}
                      {!isRunning && account.status === "active" && "Active"}
                      {!isRunning && account.status === "paused" && "Paused"}
                      {!isRunning && account.status === "error" && "Error"}
                      {!isRunning && account.status === "pending" && "Pending"}
                    </span>
                    {account.error && (
                      <p className="mt-1 line-clamp-1 text-[11px] text-rose-500">
                        {account.error}
                      </p>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-1">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${sessionBadgeClasses[account.sessionState]}`}
                        >
                          {account.sessionState === "ok" && "Session OK"}
                          {account.sessionState === "expiring" &&
                            "Token expiring"}
                          {account.sessionState === "expired" && "Token expired"}
                          {account.sessionState === "login_required" &&
                            "Login required"}
                          {account.sessionState === "blocked" && "Blocked / 401"}
                        </span>
                        {account.loginRequired && (
                          <span className="inline-flex items-center rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-medium text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900">
                            Login required
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-zinc-500">
                        Expires {account.tokenExpiry}{" "}
                        {tokenSoonExpiring && (
                          <span className="font-medium text-amber-600 dark:text-amber-400">
                            · monitor
                          </span>
                        )}
                      </p>
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <p className="text-xs font-medium">
                      {account.swipeLikes +
                        account.swipePasses +
                        account.swipeErrors}{" "}
                      swipes
                    </p>
                    <div className="mt-1 space-y-0.5 text-[11px]">
                      <div className="flex flex-wrap items-center gap-1">
                        <span className="text-emerald-600 dark:text-emerald-400">
                          Like {(account.swipeLikeRate * 100).toFixed(0)}%
                        </span>
                        <span className="text-zinc-400">·</span>
                        <span className="text-zinc-500">
                          Pass {(account.swipePassRate * 100).toFixed(0)}%
                        </span>
                        <span className="text-zinc-400">·</span>
                        <span className="text-rose-500">
                          Fail {(account.swipeErrorRate * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-500">
                        Like {account.swipeLikes}, Pass {account.swipePasses}, Fail{" "}
                        {account.swipeErrors}
                      </p>
                    </div>
                  </td>
                  {!readOnly && (
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap justify-end gap-1">
                        {onAutoChatToggle && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              onAutoChatToggle(account);
                            }}
                            className={
                              autoChatRunningIds.has(account.id)
                                ? "rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-800 transition hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300"
                                : "rounded-full bg-zinc-900 px-2.5 py-1 text-[11px] font-medium text-zinc-50 transition hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                            }
                          >
                            {autoChatRunningIds.has(account.id)
                              ? "Stop Auto Chat"
                              : "Auto Chat"}
                          </button>
                        )}
                        {onAutoSwipeToggle && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              onAutoSwipeToggle(account);
                            }}
                            className={
                              autoSwipeRunningIds.has(account.id)
                                ? "rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-800 transition hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300"
                                : "rounded-full border border-zinc-200 px-2.5 py-1 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
                            }
                          >
                            {autoSwipeRunningIds.has(account.id)
                              ? "Stop Auto Swipe"
                              : "Auto Swipe"}
                          </button>
                        )}
                        {onViewProfile && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              onViewProfile(account);
                            }}
                            className="rounded-full border border-zinc-200 px-2 py-1 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
                          >
                            Profile
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            onOpenLogs?.(account);
                          }}
                          className="rounded-full border border-zinc-200 px-2 py-1 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
                        >
                          Logs
                        </button>
                        {onEdit && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              onEdit(account);
                            }}
                            className="rounded-full border border-zinc-200 px-2 py-1 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
                          >
                            Edit
                          </button>
                        )}
                        {onDelete && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              onDelete(account);
                            }}
                            className="rounded-full border border-rose-200 px-2 py-1 text-[11px] font-medium text-rose-600 transition hover:bg-rose-50 dark:border-rose-900 dark:text-rose-400 dark:hover:bg-rose-950/40"
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {!readOnly && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-[11px] text-zinc-500">
          <p>
            Selected accounts:{" "}
            <span className="font-medium">{selectedAccountIds.size}</span>
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => onBulkAction?.("start_ai_chat")}
              className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-200 dark:hover:bg-zinc-900"
            >
              Start AI Auto Chat (bulk)
            </button>
            <button
              onClick={() => onBulkAction?.("update_bio")}
              className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-200 dark:hover:bg-zinc-900"
            >
              Update Bio (bulk)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

