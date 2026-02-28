import { Job } from "@/components/dashboard/types";

type Props = {
  jobs: Job[];
  onRetryFailed?: () => void;
  readOnly?: boolean;
};

export function JobQueue({ jobs, onRetryFailed, readOnly = false }: Props) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold">Job Queue</h2>
          <p className="text-[11px] text-zinc-500">
            Backend job status across all accounts.
          </p>
        </div>
        {!readOnly && onRetryFailed && (
          <button
            onClick={onRetryFailed}
            className="rounded-full border border-zinc-200 px-3 py-1.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
          >
            Retry Failed
          </button>
        )}
      </div>
      <div className="space-y-2">
        {jobs.map((job) => (
          <div
            key={job.id}
            className="rounded-xl border border-zinc-100 bg-zinc-50 px-3 py-2 text-xs dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium">{job.type}</p>
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  job.status === "running"
                    ? "bg-sky-50 text-sky-700 ring-1 ring-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:ring-sky-900"
                    : job.status === "pending"
                    ? "bg-zinc-100 text-zinc-700 ring-1 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-300 dark:ring-zinc-700"
                    : job.status === "completed"
                    ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-900"
                    : "bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900"
                }`}
              >
                {job.status}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between gap-3 text-[11px] text-zinc-500">
              <span>
                {job.accountId ? `Account #${job.accountId}` : "Bulk job"}
              </span>
              <span>
                {job.createdAt} · {job.attempts} attempt
                {job.attempts !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

