"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Account,
  Job,
  LogEntry,
} from "@/components/dashboard/types";
import { AccountsTable } from "@/components/dashboard/AccountsTable";
import { JobQueue } from "@/components/dashboard/JobQueue";
import { AccountAnalytics } from "@/components/dashboard/AccountAnalytics";
import { LogsOverview } from "@/components/dashboard/LogsOverview";
import {
  fetchAccounts,
  fetchJobs,
  fetchLogs,
} from "@/lib/automationClient";
import { useRealtimeEvents } from "@/lib/useRealtimeEvents";

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [accountsData, jobsData, logsData] = await Promise.all([
          fetchAccounts(),
          fetchJobs(),
          fetchLogs(),
        ]);
        if (cancelled) return;
        setAccounts(accountsData);
        setJobs(jobsData);
        setLogs(logsData);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setLoadError("Failed to load data from backend.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
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

  const globalAnalytics = useMemo(() => {
    const totalActions = accounts.reduce(
      (sum, acc) => sum + acc.actionsToday,
      0,
    );
    const avgSuccess =
      accounts.length > 0
        ? accounts.reduce((sum, acc) => sum + acc.successRate, 0) /
          accounts.length
        : 0;
    const avgFailure =
      accounts.length > 0
        ? accounts.reduce((sum, acc) => sum + acc.failureRate, 0) /
          accounts.length
        : 0;
    const activeAccounts = accounts.filter((a) => a.status === "active").length;

    return {
      totalActions,
      avgSuccess,
      avgFailure,
      activeAccounts,
      totalAccounts: accounts.length,
    };
  }, [accounts]);

  return (
    <main className="flex flex-col gap-6">
      {loadError && (
        <p className="text-xs text-rose-500">{loadError}</p>
      )}

      {/* Top summary & global controls */}
      <section className="grid gap-4 md:grid-cols-5">
        <div className="col-span-3 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
            <p className="text-xs font-medium text-zinc-500">
              Total Actions Today
            </p>
            <p className="mt-2 text-2xl font-semibold">
              {globalAnalytics.totalActions}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Across {globalAnalytics.totalAccounts} accounts
            </p>
          </div>
          <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
            <p className="text-xs font-medium text-zinc-500">
              Active Accounts
            </p>
            <p className="mt-2 text-2xl font-semibold">
              {globalAnalytics.activeAccounts}
            </p>
            <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
              Global success {(globalAnalytics.avgSuccess * 100).toFixed(0)}%
            </p>
          </div>
          <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
            <p className="text-xs font-medium text-zinc-500">Failure Rate</p>
            <p className="mt-2 text-2xl font-semibold text-rose-500">
              {(globalAnalytics.avgFailure * 100).toFixed(0)}%
            </p>
            <p className="mt-1 text-xs text-rose-500 dark:text-rose-400">
              Watch blocks / errors
            </p>
          </div>
        </div>

        <div className="col-span-2 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
          <p className="text-xs font-medium text-zinc-500">
            Automation
          </p>
          <p className="mt-2 text-[11px] text-zinc-500">
            Use the Accounts or Jobs page to run actions and change settings.
          </p>
        </div>
      </section>

      {/* Accounts table (read-only) */}
      <section className="w-full">
        <AccountsTable accounts={accounts} readOnly />
      </section>

      {/* Jobs & analytics / logs overview */}
      <section className="grid gap-4 lg:grid-cols-3">
        <JobQueue jobs={jobs} readOnly />
        <AccountAnalytics accounts={accounts} />
        <LogsOverview logs={logs} />
      </section>

    </main>
  );
}
