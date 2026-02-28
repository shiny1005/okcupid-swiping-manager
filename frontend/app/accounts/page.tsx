"use client";

import { useEffect, useState } from "react";
import {
  Account,
  AccountStatus,
  BulkActionType,
  Job,
  LogEntry,
} from "@/components/dashboard/types";
import { AccountsTable } from "@/components/dashboard/AccountsTable";
import { AccountLogsDrawer } from "@/components/dashboard/AccountLogsDrawer";
import { AccountProfileDrawer } from "@/components/dashboard/AccountProfileDrawer";
import { AddAccountDialog } from "@/components/dashboard/AddAccountDialog";
import {
  autoSwipeProfilesForAccounts,
  getProfileInfo,
  fetchAccounts,
  fetchJobs,
  fetchLogs,
  startAiChatForAccounts,
  createAccount,
  getAccountForEdit,
  updateAccount,
  deleteAccount,
  type ProfileSummary,
} from "@/lib/automationClient";
import { useRealtimeEvents } from "@/lib/useRealtimeEvents";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountIds, setSelectedAccountIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [jobs, setJobs] = useState<Job[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [selectedAccountForLogs, setSelectedAccountForLogs] =
    useState<Account | null>(null);
  const [profileAccount, setProfileAccount] = useState<Account | null>(null);
  const [profileData, setProfileData] = useState<ProfileSummary | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editAccountId, setEditAccountId] = useState<string | null>(null);
  const [editInitialValues, setEditInitialValues] = useState<{
    name: string;
    authenticationToken?: string;
    cookie?: string;
    proxyType?: string;
    proxyHost?: string;
    proxyPort?: number;
    proxyUsername?: string;
    proxyPassword?: string;
  } | null>(null);
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [accountsData, jobsData, logsData] = await Promise.all([
        fetchAccounts(),
        fetchJobs(),
        fetchLogs(),
      ]);
      setAccounts(accountsData);
      setJobs(jobsData);
      setLogs(logsData);
      setLoadError(null);
    } catch (error) {
      console.error(error);
      setLoadError("Failed to load data from backend.");
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  useRealtimeEvents({
    onLog: (log) => {
      setLogs((prev) => [log, ...prev].slice(0, 200));
    },
    onProfileUpdate: (accountId) => {
      if (profileAccount?.id === accountId) {
        getProfileInfo(accountId)
          .then(setProfileData)
          .catch(() => {});
      }
    },
  });

  const toggleAccountSelection = (id: string) => {
    setSelectedAccountIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelectedAccountIds((prev) => {
      if (prev.size === accounts.length) {
        return new Set();
      }
      return new Set(accounts.map((a) => a.id));
    });
  };

  const [autoChatRunningIds, setAutoChatRunningIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [autoSwipeRunningIds, setAutoSwipeRunningIds] = useState<Set<string>>(
    () => new Set(),
  );

  const handleAutoChatToggle = async (account: Account) => {
    const id = account.id;
    if (autoChatRunningIds.has(id)) {
      setAutoChatRunningIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      return;
    }
    setAutoChatRunningIds((prev) => new Set(prev).add(id));
    try {
      await startAiChatForAccounts([id]);
      setJobs((prev) => [
        {
          id: `job-${prev.length + 1}`,
          accountId: id,
          type: "Start AI Auto Chat",
          status: "running",
          attempts: 0,
          createdAt: new Date().toISOString(),
        },
        ...prev,
      ]);
      await loadData();
    } catch (error) {
      console.error(error);
      alert("Failed to start AI auto chat for this account.");
    } finally {
      setAutoChatRunningIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleAutoSwipeToggle = async (account: Account) => {
    const id = account.id;
    if (autoSwipeRunningIds.has(id)) {
      setAutoSwipeRunningIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      return;
    }
    setAutoSwipeRunningIds((prev) => new Set(prev).add(id));
    try {
      const result = await autoSwipeProfilesForAccounts([id], 50);
      if (result && result.summary) {
        const parts: string[] = [];
        for (const [dir, s] of Object.entries(result.summary)) {
          parts.push(
            `${dir}: swiped=${s.swiped}, skipped=${s.skipped}, errors=${s.errors}`,
          );
        }
        if (parts.length > 0) {
          alert(`Auto swipe completed for ${account.name}.\n${parts.join("\n")}`);
        }
      }
      setJobs((prev) => [
        {
          id: `job-${prev.length + 1}`,
          accountId: id,
          type: "Auto Swipe",
          status: "running",
          attempts: 0,
          createdAt: new Date().toISOString(),
        },
        ...prev,
      ]);
      await loadData();
    } catch (error) {
      console.error(error);
      alert("Failed to start auto swipe for this account.");
    } finally {
      setAutoSwipeRunningIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleBulkAction = (action: BulkActionType) => {
    if (selectedAccountIds.size === 0) return;

    const affectedIds = Array.from(selectedAccountIds);

    if (action === "pause_selected" || action === "activate_selected") {
      const status: AccountStatus =
        action === "pause_selected" ? "paused" : "active";
      setAccounts((prev) =>
        prev.map((acc) =>
          affectedIds.includes(acc.id)
            ? {
                ...acc,
                status,
              }
            : acc,
        ),
      );
    }

    const jobTypeMap: Record<BulkActionType, string> = {
      start_ai_chat: "Bulk: Start AI Auto Chat",
      swipe_50: "Bulk: Swipe 50 Profiles",
      update_bio: "Bulk: Update Bio",
      pause_selected: "Bulk: Pause Accounts",
      activate_selected: "Bulk: Activate Accounts",
      send_campaign: "Bulk: Send Campaign",
    };

    (async () => {
      try {
        if (action === "start_ai_chat") {
          await startAiChatForAccounts(affectedIds);
        } else if (action === "swipe_50") {
          await autoSwipeProfilesForAccounts(affectedIds, 50);
        }

        await loadData();
        setJobs((prev) => [
          {
            id: `job-${prev.length + 1}`,
            accountId: undefined,
            type: jobTypeMap[action],
            status: "pending",
            attempts: 0,
            createdAt: new Date().toISOString(),
          },
          ...prev,
        ]);
      } catch (error) {
        console.error(error);
        alert("Bulk action failed. See console for details.");
      }
    })();
  };

  const handleViewProfile = async (account: Account) => {
    setSelectedAccountForLogs(null);
    setProfileAccount(account);
    setProfileLoading(true);
    setProfileError(null);
    try {
      const result = await getProfileInfo(account.id);
      setProfileData(result);
    } catch (error) {
      console.error(error);
      setProfileError("Failed to load profile from backend.");
      setProfileData(null);
    } finally {
      setProfileLoading(false);
    }
  };

  const handleOpenLogs = (account: Account) => {
    setProfileAccount(null);
    setProfileData(null);
    setProfileError(null);
    setProfileLoading(false);
    setSelectedAccountForLogs(account);
  };

  const handleAddAccountClick = () => {
    setAddError(null);
    setAddOpen(true);
  };

  const handleAddAccountSubmit = async (values: {
    name: string;
    authenticationToken: string;
    cookie: string;
    proxyType?: string;
    proxyHost?: string;
    proxyPort?: number;
    proxyUsername?: string;
    proxyPassword?: string;
  }) => {
    if (!values.proxyType?.trim() || !values.proxyHost?.trim() || values.proxyPort == null || values.proxyPort <= 0) {
      setAddError("Proxy type, host, and port are required.");
      return;
    }
    setAddLoading(true);
    setAddError(null);
    try {
      const created = await createAccount({
        name: values.name,
        authenticationToken: values.authenticationToken,
        cookie: values.cookie,
        proxyType: values.proxyType.trim(),
        proxyHost: values.proxyHost.trim(),
        proxyPort: values.proxyPort,
        proxyUsername: values.proxyUsername,
        proxyPassword: values.proxyPassword,
      });
      setAccounts((prev) => [...prev, created]);
      setAddOpen(false);
    } catch (error) {
      console.error(error);
      setAddError("Failed to create account.");
    } finally {
      setAddLoading(false);
    }
  };

  const handleEditClick = async (account: Account) => {
    setEditError(null);
    setEditAccountId(account.id);
    try {
      const data = await getAccountForEdit(account.id);
      setEditInitialValues({
        name: data.name,
        authenticationToken: data.authenticationToken,
        cookie: data.cookie,
        proxyType: data.proxy?.type,
        proxyHost: data.proxy?.host,
        proxyPort: data.proxy?.port,
        proxyUsername: data.proxy?.username,
        proxyPassword: data.proxy?.password,
      });
      setEditOpen(true);
    } catch (error) {
      console.error(error);
      setEditError("Failed to load account for editing.");
    }
  };

  const handleEditSubmit = async (values: {
    name: string;
    authenticationToken: string;
    cookie: string;
    proxyType?: string;
    proxyHost?: string;
    proxyPort?: number;
    proxyUsername?: string;
    proxyPassword?: string;
  }) => {
    if (!editAccountId) return;
    if (!values.proxyType?.trim() || !values.proxyHost?.trim() || values.proxyPort == null || values.proxyPort <= 0) {
      setEditError("Proxy type, host, and port are required.");
      return;
    }
    setEditLoading(true);
    setEditError(null);
    try {
      const updated = await updateAccount(editAccountId, {
        name: values.name,
        authenticationToken: values.authenticationToken || undefined,
        cookie: values.cookie || undefined,
        proxyType: values.proxyType.trim(),
        proxyHost: values.proxyHost.trim(),
        proxyPort: values.proxyPort,
        proxyUsername: values.proxyUsername,
        proxyPassword: values.proxyPassword,
      });
      setAccounts((prev) =>
        prev.map((a) => (a.id === editAccountId ? updated : a)),
      );
      setEditOpen(false);
      setEditAccountId(null);
      setEditInitialValues(null);
    } catch (error) {
      console.error(error);
      setEditError("Failed to update account.");
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteClick = async (account: Account) => {
    if (
      !confirm(
        `Delete account "${account.name}"? This cannot be undone.`,
      )
    )
      return;
    try {
      await deleteAccount(account.id);
      setAccounts((prev) => prev.filter((a) => a.id !== account.id));
      setSelectedAccountIds((prev) => {
        const next = new Set(prev);
        next.delete(account.id);
        return next;
      });
      if (selectedAccountForLogs?.id === account.id)
        setSelectedAccountForLogs(null);
      if (profileAccount?.id === account.id) setProfileAccount(null);
    } catch (error) {
      console.error(error);
      alert("Failed to delete account.");
    }
  };

  return (
    <main className="flex w-full flex-col gap-6">
      <section>
        <h2 className="text-sm font-semibold">Accounts</h2>
        <p className="mt-1 text-xs text-zinc-500">
          Add new accounts, assign proxies, and control automation per account.
        </p>
        {loadError && (
          <p className="mt-1 text-[11px] text-rose-500">{loadError}</p>
        )}
      </section>

      <section className="w-full">
        <AccountsTable
          accounts={accounts}
          selectedAccountIds={selectedAccountIds}
          onToggleSelectAll={toggleSelectAll}
          onToggleSelect={toggleAccountSelection}
          autoChatRunningIds={autoChatRunningIds}
          autoSwipeRunningIds={autoSwipeRunningIds}
          onAutoChatToggle={handleAutoChatToggle}
          onAutoSwipeToggle={handleAutoSwipeToggle}
          onBulkAction={handleBulkAction}
          onOpenLogs={handleOpenLogs}
          onViewProfile={handleViewProfile}
          onEdit={handleEditClick}
          onDelete={handleDeleteClick}
          onAddAccount={handleAddAccountClick}
        />
      </section>

      <AccountLogsDrawer
        account={selectedAccountForLogs}
        logs={logs}
        onClose={() => setSelectedAccountForLogs(null)}
      />

      <AccountProfileDrawer
        account={profileAccount}
        profile={profileData}
        loading={profileLoading}
        error={profileError}
        onClose={() => {
          setProfileAccount(null);
          setProfileData(null);
          setProfileError(null);
          setProfileLoading(false);
        }}
      />

      <AddAccountDialog
        open={addOpen}
        loading={addLoading}
        error={addError}
        onClose={() => {
          if (addLoading) return;
          setAddOpen(false);
          setAddError(null);
        }}
        onSubmit={handleAddAccountSubmit}
      />

      <AddAccountDialog
        open={editOpen}
        loading={editLoading}
        error={editError}
        onClose={() => {
          if (editLoading) return;
          setEditOpen(false);
          setEditAccountId(null);
          setEditInitialValues(null);
          setEditError(null);
        }}
        onSubmit={handleEditSubmit}
        editMode
        initialValues={editInitialValues ?? undefined}
      />
    </main>
  );
}

