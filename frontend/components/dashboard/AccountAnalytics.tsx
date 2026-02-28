import { Account } from "@/components/dashboard/types";

type Props = {
  accounts: Account[];
};

export function AccountAnalytics({ accounts }: Props) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
      <h2 className="text-sm font-semibold">Account Analytics</h2>
      <p className="mt-1 text-[11px] text-zinc-500">
        Per-account action volume and health.
      </p>
      <div className="mt-3 space-y-3">
        {accounts.map((account) => (
          <div key={account.id} className="space-y-1 text-xs">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium">{account.name}</p>
              <p className="text-[11px] text-zinc-500">
                {account.actionsToday} actions
              </p>
            </div>
            <div className="flex h-2.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-900">
              <div
                className="bg-emerald-500"
                style={{
                  width: `${account.successRate * 100}%`,
                }}
              />
              <div
                className="bg-rose-500"
                style={{
                  width: `${account.failureRate * 100}%`,
                }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-zinc-500">
              <span>
                Success {(account.successRate * 100).toFixed(0)}
                %
              </span>
              <span>
                Failure {(account.failureRate * 100).toFixed(0)}
                %
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

