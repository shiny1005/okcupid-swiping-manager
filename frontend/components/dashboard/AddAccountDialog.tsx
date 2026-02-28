"use client";

import { FormEvent, useEffect, useState } from "react";

export type AccountFormValues = {
  name: string;
  authenticationToken: string;
  cookie: string;
  proxyType?: string;
  proxyHost?: string;
  proxyPort?: number;
  proxyUsername?: string;
  proxyPassword?: string;
};

type Props = {
  open: boolean;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: AccountFormValues) => void;
  editMode?: boolean;
  initialValues?: Partial<AccountFormValues>;
};

export function AddAccountDialog({
  open,
  loading,
  error,
  onClose,
  onSubmit,
  editMode = false,
  initialValues,
}: Props) {
  const [name, setName] = useState("");
  const [authenticationToken, setAuthenticationToken] = useState("");
  const [cookie, setCookie] = useState("");
  const [proxyType, setProxyType] = useState("");
  const [proxyHost, setProxyHost] = useState("");
  const [proxyPort, setProxyPort] = useState("");
  const [proxyUsername, setProxyUsername] = useState("");
  const [proxyPassword, setProxyPassword] = useState("");

  useEffect(() => {
    if (open && initialValues) {
      setName(initialValues.name ?? "");
      setAuthenticationToken(initialValues.authenticationToken ?? "");
      setCookie(initialValues.cookie ?? "");
      setProxyType(initialValues.proxyType ?? "");
      setProxyHost(initialValues.proxyHost ?? "");
      setProxyPort(initialValues.proxyPort?.toString() ?? "");
      setProxyUsername(initialValues.proxyUsername ?? "");
      setProxyPassword(initialValues.proxyPassword ?? "");
    } else if (open && !editMode) {
      setName("");
      setAuthenticationToken("");
      setCookie("");
      setProxyType("");
      setProxyHost("");
      setProxyPort("");
      setProxyUsername("");
      setProxyPassword("");
    }
  }, [open, editMode, initialValues]);

  if (!open) return null;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim() || loading) return;
    if (!editMode && (!authenticationToken.trim() || !cookie.trim())) return;
    const portNum = proxyPort ? Number(proxyPort) : undefined;
    if (!proxyType.trim() || !proxyHost.trim() || !portNum || portNum <= 0) {
      return;
    }
    onSubmit({
      name: name.trim(),
      authenticationToken: authenticationToken.trim(),
      cookie: cookie.trim(),
      proxyType: proxyType.trim() || "socks5",
      proxyHost: proxyHost.trim(),
      proxyPort: portNum,
      proxyUsername: proxyUsername || undefined,
      proxyPassword: proxyPassword || undefined,
    });
  };

  const resetAndClose = () => {
    setName("");
    setAuthenticationToken("");
    setCookie("");
    setProxyType("");
    setProxyHost("");
    setProxyPort("");
    setProxyUsername("");
    setProxyPassword("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/40 px-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl ring-1 ring-zinc-200 dark:bg-zinc-950 dark:ring-zinc-800">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold">
              {editMode ? "Edit Account" : "Add Account"}
            </h2>
            <p className="mt-1 text-[11px] text-zinc-500">
              {editMode
                ? "Update name, token, cookie, or proxy. Leave token and cookie blank to keep current."
                : "Provide the authentication token and cookie for this account. They will be sent to the backend and stored in MongoDB."}
            </p>
          </div>
          <button
            type="button"
            onClick={resetAndClose}
            className="rounded-full border border-zinc-200 px-2.5 py-1 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            Close
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3 text-xs">
          <div className="space-y-1">
            <label className="block text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
              Account name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
              placeholder="e.g. Account A"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="block text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
              Authentication token
            </label>
            <textarea
              value={authenticationToken}
              onChange={(e) => setAuthenticationToken(e.target.value)}
              className="h-16 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
              placeholder={
                editMode ? "Leave blank to keep current" : "Paste auth token here"
              }
              required={!editMode}
            />
          </div>

          <div className="mt-3 space-y-2 rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
              Proxy (required)
            </p>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="block text-[11px] text-zinc-500">
                  Type <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={proxyType}
                  onChange={(e) => setProxyType(e.target.value)}
                  className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                  placeholder="e.g. socks5, http"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="block text-[11px] text-zinc-500">
                  Host <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={proxyHost}
                  onChange={(e) => setProxyHost(e.target.value)}
                  className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                  placeholder="proxy.example.com"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="block text-[11px] text-zinc-500">
                  Port <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  value={proxyPort}
                  onChange={(e) => setProxyPort(e.target.value)}
                  className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                  placeholder="1080"
                  min={1}
                  max={65535}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="block text-[11px] text-zinc-500">
                  Username
                </label>
                <input
                  type="text"
                  value={proxyUsername}
                  onChange={(e) => setProxyUsername(e.target.value)}
                  className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                  placeholder="optional"
                />
              </div>
              <div className="space-y-1 col-span-2">
                <label className="block text-[11px] text-zinc-500">
                  Password
                </label>
                <input
                type="text"
                  value={proxyPassword}
                  onChange={(e) => setProxyPassword(e.target.value)}
                  className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                placeholder="optional"
                />
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
              Cookie
            </label>
            <textarea
              value={cookie}
              onChange={(e) => setCookie(e.target.value)}
              className="h-16 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
              placeholder={
                editMode ? "Leave blank to keep current" : "Paste cookie string here"
              }
              required={!editMode}
            />
          </div>

          {error && (
            <p className="text-[11px] text-rose-500">
              {error || "Failed to create account."}
            </p>
          )}

          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={resetAndClose}
              className="rounded-full border border-zinc-200 px-3 py-1.5 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-full bg-zinc-900 px-3 py-1.5 text-[11px] font-medium text-zinc-50 shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {loading
                ? "Saving..."
                : editMode
                  ? "Update account"
                  : "Save account"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

