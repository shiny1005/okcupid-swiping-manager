"use client";

import { useEffect, useState } from "react";
import { Job } from "@/components/dashboard/types";
import { JobQueue } from "@/components/dashboard/JobQueue";
import { fetchJobs } from "@/lib/automationClient";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const jobsData = await fetchJobs();
        if (cancelled) return;
        setJobs(jobsData);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setLoadError("Failed to load jobs from backend.");
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleRetryFailed = () => {
    setJobs((prev) =>
      prev.map((job) =>
        job.status === "failed"
          ? {
              ...job,
              status: "pending",
              attempts: job.attempts + 1,
            }
          : job,
      ),
    );
  };

  return (
    <main className="flex flex-col gap-6">
      <section>
        <h2 className="text-sm font-semibold">Jobs & Queue</h2>
        <p className="mt-1 text-xs text-zinc-500">
          Inspect running, pending, completed, and failed automation jobs.
        </p>
        {loadError && (
          <p className="mt-1 text-[11px] text-rose-500">{loadError}</p>
        )}
      </section>

      <section>
        <JobQueue jobs={jobs} onRetryFailed={handleRetryFailed} />
      </section>
    </main>
  );
}

