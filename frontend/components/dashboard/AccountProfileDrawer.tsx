"use client";

import { useEffect, useState } from "react";
import { Account } from "@/components/dashboard/types";
import {
  type ProfileSummary,
  updateProfileBio,
  updateProfileRealname,
} from "@/lib/automationClient";

type Props = {
  account: Account | null;
  profile: ProfileSummary | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
};

export function AccountProfileDrawer({
  account,
  profile,
  loading,
  error,
  onClose,
}: Props) {
  if (!account) return null;

  const settings = profile?.settings ?? {};
  const bio = profile?.bio ?? {};

  const birthdate = settings?.birthdate;
  const birthdateStr =
    birthdate && (birthdate.year || birthdate.month || birthdate.day)
      ? `${birthdate.year ?? "YYYY"}-${String(birthdate.month ?? "MM").padStart(2, "0")}-${String(birthdate.day ?? "DD").padStart(2, "0")}`
      : "Unknown";

  const unitPreference = settings?.unitPreference ?? "Unknown";
  const emailAddress = settings?.emailAddress ?? "Unknown";
  const realname = settings?.realname ?? "Unknown";
  const displayname = settings?.displayname ?? "Unknown";
  const phoneNumber = settings?.phoneNumber ?? "Unknown";

  const userLocation = settings?.userLocation as
    | {
        id?: string;
        countryCode?: string;
        stateCode?: string;
        fullName?: string;
        publicName?: string;
      }
    | undefined;

  const locationLabel =
    userLocation?.fullName ||
    userLocation?.publicName ||
    [userLocation?.stateCode, userLocation?.countryCode]
      .filter(Boolean)
      .join(", ") ||
    "Unknown";

  const bioText = bio?.text ?? "";
  const avatarUrl = bio?.avatar_url ?? "";

  const [editingRealname, setEditingRealname] = useState(false);
  const [editingBio, setEditingBio] = useState(false);
  const [realnameInput, setRealnameInput] = useState(realname);
  const [bioInput, setBioInput] = useState(bioText);
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    setRealnameInput(realname);
    setBioInput(bioText);
    setEditingRealname(false);
    setEditingBio(false);
    setLocalError(null);
    setSaving(false);
  }, [realname, bioText, account?.id]);

  const handleSaveRealname = async () => {
    if (!account) return;
    const value = realnameInput.trim();
    if (!value) {
      setLocalError("Real name cannot be empty.");
      return;
    }
    setSaving(true);
    setLocalError(null);
    try {
      await updateProfileRealname(account.id, value);
      setEditingRealname(false);
    } catch (error) {
      console.error(error);
      setLocalError("Failed to update real name.");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveBio = async () => {
    if (!account) return;
    const value = bioInput.trim();
    setSaving(true);
    setLocalError(null);
    try {
      await updateProfileBio(account.id, value);
      setEditingBio(false);
    } catch (error) {
      console.error(error);
      setLocalError("Failed to update bio.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="profile-modal-title"
    >
      {/* Backdrop - click to close */}
      <button
        type="button"
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close modal"
      />
      {/* Modal content */}
      <div
        className="relative z-10 w-full max-w-lg rounded-2xl border border-zinc-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-950"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col gap-3 p-4 md:p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p id="profile-modal-title" className="text-sm font-semibold">
                Profile · {account.name}
              </p>
              <p className="text-[11px] text-zinc-500">
                OkCupid profile details and bio for this account.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setEditingRealname((v) => !v);
                  setLocalError(null);
                }}
                className="rounded-full border border-zinc-200 px-2.5 py-1 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
              >
                {editingRealname ? "Cancel name edit" : "Edit real name"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditingBio((v) => !v);
                  setLocalError(null);
                }}
                className="rounded-full border border-zinc-200 px-2.5 py-1 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
              >
                {editingBio ? "Cancel bio edit" : "Edit bio"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-zinc-200 px-3 py-1.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
              >
                Close
              </button>
            </div>
          </div>
          <div className="max-h-80 overflow-y-auto rounded-xl border border-zinc-100 bg-zinc-50/50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-900/50">
            {loading && (
              <p className="text-[11px] text-zinc-500">Loading profile…</p>
            )}
            {!loading && (error || localError) && (
              <p className="text-[11px] text-rose-500">
                {error || localError}
              </p>
            )}
            {!loading && !error && (
              <div className="space-y-3">
                {avatarUrl && (
                  <div className="flex justify-center">
                    <img
                      src={avatarUrl}
                      alt={`${displayname} avatar`}
                      className="h-24 w-24 rounded-full object-cover ring-2 ring-zinc-200 dark:ring-zinc-700"
                    />
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      ID
                    </p>
                    <p className="text-zinc-500">
                      {settings?.id ?? "Unknown"}
                    </p>
                  </div>
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      Display name
                    </p>
                    <p className="text-zinc-500">{displayname}</p>
                  </div>
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      Real name
                    </p>
                    {editingRealname ? (
                      <div className="mt-1 space-y-1">
                        <input
                          type="text"
                          value={realnameInput}
                          onChange={(e) => setRealnameInput(e.target.value)}
                          className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1 text-[11px] outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                        />
                        <button
                          type="button"
                          disabled={saving}
                          onClick={handleSaveRealname}
                          className="rounded-full bg-zinc-900 px-2.5 py-1 text-[11px] font-medium text-zinc-50 shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                        >
                          {saving ? "Saving..." : "Save name"}
                        </button>
                      </div>
                    ) : (
                      <p className="text-zinc-500">{realname}</p>
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      Birthdate
                    </p>
                    <p className="text-zinc-500">{birthdateStr}</p>
                  </div>
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      Unit preference
                    </p>
                    <p className="text-zinc-500">{unitPreference}</p>
                  </div>
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      Email
                    </p>
                    <p className="truncate text-zinc-500">{emailAddress}</p>
                  </div>
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      Phone
                    </p>
                    <p className="text-zinc-500">{phoneNumber}</p>
                  </div>
                  <div>
                    <p className="font-medium text-zinc-700 dark:text-zinc-100">
                      Location
                    </p>
                    <p className="text-zinc-500">{locationLabel}</p>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-[11px] font-medium text-zinc-700 dark:text-zinc-100">
                    Bio
                  </p>
                  {editingBio ? (
                    <div className="space-y-1">
                      <textarea
                        value={bioInput}
                        onChange={(e) => setBioInput(e.target.value)}
                        className="h-24 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1 text-[11px] outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                      />
                      <button
                        type="button"
                        disabled={saving}
                        onClick={handleSaveBio}
                        className="rounded-full bg-zinc-900 px-2.5 py-1 text-[11px] font-medium text-zinc-50 shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                      >
                        {saving ? "Saving..." : "Save bio"}
                      </button>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap text-[11px] text-zinc-500 dark:text-zinc-200">
                      {bioText || "No bio text found."}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
