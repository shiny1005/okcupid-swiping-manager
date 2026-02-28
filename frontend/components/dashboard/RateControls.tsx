import { RateConfig } from "@/components/dashboard/types";

type Props = {
  rateConfig: RateConfig;
  onChange?: <K extends keyof RateConfig>(
    key: K,
    value: RateConfig[K],
  ) => void;
  readOnly?: boolean;
};

export function RateControls({
  rateConfig,
  onChange,
  readOnly = false,
}: Props) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
        <h2 className="text-sm font-semibold">Rate & Safety</h2>
        <p className="mt-1 text-[11px] text-zinc-500">
          {readOnly
            ? "Current limits (edit on Safety page)."
            : "All automation commands in this panel respect these limits."}
        </p>
        <div className="mt-3 space-y-3 text-xs">
          <div className="flex items-center justify-between gap-3">
            <label className="text-zinc-600 dark:text-zinc-300">
              Max actions / hour
            </label>
            {readOnly ? (
              <span className="text-zinc-800 dark:text-zinc-200">
                {rateConfig.maxActionsPerHour}
              </span>
            ) : (
              <input
                type="number"
                value={rateConfig.maxActionsPerHour}
                onChange={(e) =>
                  onChange?.("maxActionsPerHour", Number(e.target.value) || 0)
                }
                className="w-24 rounded-md border border-zinc-200 bg-transparent px-2 py-1 text-right text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
              />
            )}
          </div>
          <div className="flex items-center justify-between gap-3">
            <label className="text-zinc-600 dark:text-zinc-300">
              Delay range (ms)
            </label>
            {readOnly ? (
              <span className="text-zinc-800 dark:text-zinc-200">
                {rateConfig.delayMinMs} – {rateConfig.delayMaxMs}
              </span>
            ) : (
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  value={rateConfig.delayMinMs}
                  onChange={(e) =>
                    onChange?.("delayMinMs", Number(e.target.value) || 0)
                  }
                  className="w-20 rounded-md border border-zinc-200 bg-transparent px-2 py-1 text-right text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                />
                <span className="text-[11px] text-zinc-400">to</span>
                <input
                  type="number"
                  value={rateConfig.delayMaxMs}
                  onChange={(e) =>
                    onChange?.("delayMaxMs", Number(e.target.value) || 0)
                  }
                  className="w-20 rounded-md border border-zinc-200 bg-transparent px-2 py-1 text-right text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                />
              </div>
            )}
          </div>
          <div className="flex items-center justify-between gap-3">
            <label className="text-zinc-600 dark:text-zinc-300">
              Randomization
            </label>
            {readOnly ? (
              <span className="text-zinc-800 dark:text-zinc-200">
                {rateConfig.randomizationEnabled ? "Enabled" : "Disabled"}
              </span>
            ) : (
              <button
                onClick={() =>
                  onChange?.(
                    "randomizationEnabled",
                    !rateConfig.randomizationEnabled,
                  )
                }
                className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-medium ${
                  rateConfig.randomizationEnabled
                    ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-900"
                    : "bg-zinc-100 text-zinc-600 ring-1 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-300 dark:ring-zinc-700"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    rateConfig.randomizationEnabled
                      ? "bg-emerald-500"
                      : "bg-zinc-400"
                  }`}
                />
                {rateConfig.randomizationEnabled ? "Enabled" : "Disabled"}
              </button>
            )}
          </div>
          <div className="flex items-center justify-between gap-3">
            <label className="text-zinc-600 dark:text-zinc-300">
              Retry limit
            </label>
            {readOnly ? (
              <span className="text-zinc-800 dark:text-zinc-200">
                {rateConfig.retryLimit}
              </span>
            ) : (
              <input
                type="number"
                value={rateConfig.retryLimit}
                onChange={(e) =>
                  onChange?.("retryLimit", Number(e.target.value) || 0)
                }
                className="w-24 rounded-md border border-zinc-200 bg-transparent px-2 py-1 text-right text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
              />
            )}
          </div>
        </div>
        {!readOnly && (
          <p className="mt-3 text-[11px] text-zinc-500">
            Backend should enforce these limits on every job.
          </p>
        )}
      </div>
    </div>
  );
}

