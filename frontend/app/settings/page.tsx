"use client";

import { useEffect, useState } from "react";
import {
  type GeneralSettings,
  fetchGeneralSettings,
  fetchOpenAIConfig,
  updateGeneralSettings,
  updateOpenAIConfig,
} from "@/lib/automationClient";

export default function SafetyPage() {
  const [loadError, setLoadError] = useState<string | null>(null);
  const [openAIHasKey, setOpenAIHasKey] = useState<boolean | null>(null);
  const [openAIMaskedKey, setOpenAIMaskedKey] = useState<string | null>(null);
  const [openAIModel, setOpenAIModel] = useState<string | null>(null);
  const [openAIKeyInput, setOpenAIKeyInput] = useState("");
  const [openAIModelInput, setOpenAIModelInput] = useState("");
  const [openAIError, setOpenAIError] = useState<string | null>(null);
  const [openAILoading, setOpenAILoading] = useState(false);
  const [generalSettings, setGeneralSettings] = useState<GeneralSettings | null>(
    null,
  );
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [generalSaving, setGeneralSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [openai, general] = await Promise.all([
          fetchOpenAIConfig(),
          fetchGeneralSettings(),
        ]);
        if (cancelled) return;
        setOpenAIHasKey(openai.hasKey);
        setOpenAIMaskedKey(openai.maskedKey ?? null);
        setOpenAIModel(openai.model ?? null);
        setOpenAIModelInput(openai.model?.trim() || "gpt-4o-mini");
        setGeneralSettings(general);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setLoadError("Failed to load safety config from backend.");
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleSaveOpenAI = () => {
    const hasKey = openAIKeyInput.trim().length > 0;
    const hasModel = openAIModelInput.trim().length > 0;
    if ((!hasKey && !hasModel) || openAILoading) return;
    if (hasKey && !hasModel) {
      setOpenAIError("Set a model when saving a new API key.");
      return;
    }
    setOpenAIError(null);
    setOpenAILoading(true);

    (async () => {
      try {
        await updateOpenAIConfig(
          hasKey ? openAIKeyInput.trim() : undefined,
          hasModel ? openAIModelInput.trim() : undefined,
        );
        const updated = await fetchOpenAIConfig();
        setOpenAIHasKey(updated.hasKey);
        setOpenAIMaskedKey(updated.maskedKey ?? null);
        setOpenAIModel(updated.model ?? null);
        setOpenAIModelInput(updated.model?.trim() || "gpt-4o-mini");
        if (hasKey) setOpenAIKeyInput("");
      } catch (error) {
        console.error(error);
        setOpenAIError("Failed to save OpenAI config.");
      } finally {
        setOpenAILoading(false);
      }
    })();
  };

  const handleGeneralChange = <
    K1 extends keyof GeneralSettings,
    K2 extends keyof GeneralSettings[K1],
  >(
    section: K1,
    key: K2,
    value: GeneralSettings[K1][K2],
  ) => {
    if (!generalSettings) return;
    setGeneralSettings({
      ...generalSettings,
      [section]: {
        ...generalSettings[section],
        [key]: value,
      },
    });
  };

  const handleSaveGeneralSettings = () => {
    if (!generalSettings || generalSaving) return;
    setGeneralError(null);
    setGeneralSaving(true);
    (async () => {
      try {
        await updateGeneralSettings(generalSettings);
      } catch (error) {
        console.error(error);
        setGeneralError("Failed to save general settings.");
      } finally {
        setGeneralSaving(false);
      }
    })();
  };

  return (
    <main className="flex w-full flex-col gap-6">
      <section>
        <h2 className="text-sm font-semibold">Settings</h2>
        <p className="mt-1 text-xs text-zinc-500">
          OpenAI API key, model, and general automation settings.
        </p>
      </section>

      <section className="w-full space-y-4">
        {loadError && (
          <p className="mb-2 text-[11px] text-rose-500">{loadError}</p>
        )}

        <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
          <h3 className="text-sm font-semibold">OpenAI API Key</h3>
          <p className="mt-1 text-[11px] text-zinc-500">
            Stored on the backend and used for AI auto chat. The full key is
            never returned to the frontend; enter a new key here to set or
            rotate it.
          </p>
          <div className="mt-3 space-y-2 text-xs">
            <div className="flex flex-col gap-1">
              <span className="text-[11px] text-zinc-500">
                Status:{" "}
                {openAIHasKey
                  ? "Key configured"
                  : openAIHasKey === false
                    ? "No key set"
                    : "Loading..."}
              </span>
              {openAIMaskedKey != null && (
                <span className="font-mono text-[11px] text-zinc-600 dark:text-zinc-400">
                  Key: {openAIMaskedKey}
                </span>
              )}
              {openAIModel != null && openAIModel.length > 0 && (
                <span className="text-[11px] text-zinc-600 dark:text-zinc-400">
                  Model: {openAIModel}
                </span>
              )}
            </div>
            <div className="space-y-1">
              <label className="block text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
                OpenAI API key
              </label>
              <input
                type="password"
                value={openAIKeyInput}
                onChange={(e) => setOpenAIKeyInput(e.target.value)}
                className="w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                placeholder="sk-... (leave blank to keep current)"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
                Model
              </label>
              <select
                value={openAIModelInput}
                onChange={(e) => setOpenAIModelInput(e.target.value)}
                className="w-full rounded-md border border-zinc-200  px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
              >
                <option value="gpt-4o-mini text-black">gpt-4o-mini</option>
                <option value="gpt-4o text-black">gpt-4o</option>
                <option value="gpt-4o-nano text-black ">gpt-4o-nano</option>
                <option value="gpt-4-turbo text-black ">gpt-4-turbo</option>
                <option value="gpt-3.5-turbo text-black ">gpt-3.5-turbo</option>
              </select>
            </div>
            {openAIError && (
              <p className="text-[11px] text-rose-500">{openAIError}</p>
            )}
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleSaveOpenAI}
                disabled={
                  openAILoading ||
                  (!openAIKeyInput.trim() && openAIModelInput.trim() === (openAIModel ?? "gpt-4o-mini"))
                }
                className="rounded-full bg-zinc-900 px-3 py-1.5 text-[11px] font-medium text-zinc-50 shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                {openAILoading ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>

        {generalSettings && (
          <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-zinc-100 dark:bg-zinc-950 dark:ring-zinc-900">
            <h3 className="text-sm font-semibold">General settings</h3>
            <p className="mt-1 text-[11px] text-zinc-500">
              Swipe and auto-chat defaults used by automation actions.
            </p>
            {generalError && (
              <p className="mt-2 text-[11px] text-rose-500">{generalError}</p>
            )}
            <div className="mt-4 space-y-6 text-xs">
              <div>
                <h4 className="mb-2 text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
                  Swipe
                </h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      Directions (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={generalSettings.swipe.directions.join(", ")}
                      onChange={(e) =>
                        handleGeneralChange(
                          "swipe",
                          "directions",
                          e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                      placeholder="pass, like"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      Like %
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={generalSettings.swipe.like_percentage}
                      onChange={(e) =>
                        handleGeneralChange(
                          "swipe",
                          "like_percentage",
                          parseInt(e.target.value, 10) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      Max swipes
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={generalSettings.swipe.max_swipes}
                      onChange={(e) =>
                        handleGeneralChange(
                          "swipe",
                          "max_swipes",
                          parseInt(e.target.value, 10) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      Delay (seconds)
                    </label>
                    <input
                      type="number"
                      min={0}
                      step={0.5}
                      value={generalSettings.swipe.delay_seconds}
                      onChange={(e) =>
                        handleGeneralChange(
                          "swipe",
                          "delay_seconds",
                          parseFloat(e.target.value) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                </div>
              </div>
              <div>
                <h4 className="mb-2 text-[11px] font-medium text-zinc-600 dark:text-zinc-300">
                  Auto chat
                </h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="sm:col-span-2">
                    <label className="block text-[11px] text-zinc-500">
                      Funnel
                    </label>
                    <input
                      type="text"
                      value={generalSettings.auto_chat.funnel}
                      onChange={(e) =>
                        handleGeneralChange(
                          "auto_chat",
                          "funnel",
                          e.target.value,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                      placeholder="e.g. justin_mccoy"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      Poll (seconds)
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={generalSettings.auto_chat.poll_seconds}
                      onChange={(e) =>
                        handleGeneralChange(
                          "auto_chat",
                          "poll_seconds",
                          parseInt(e.target.value, 10) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      CTA min messages
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={generalSettings.auto_chat.cta_min_msgs}
                      onChange={(e) =>
                        handleGeneralChange(
                          "auto_chat",
                          "cta_min_msgs",
                          parseInt(e.target.value, 10) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      CTA max messages
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={generalSettings.auto_chat.cta_max_msgs}
                      onChange={(e) =>
                        handleGeneralChange(
                          "auto_chat",
                          "cta_max_msgs",
                          parseInt(e.target.value, 10) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      Delay chat part min (s)
                    </label>
                    <input
                      type="number"
                      min={0}
                      step={0.1}
                      value={generalSettings.auto_chat.delay_chat_part_min}
                      onChange={(e) =>
                        handleGeneralChange(
                          "auto_chat",
                          "delay_chat_part_min",
                          parseFloat(e.target.value) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-zinc-500">
                      Delay chat part max (s)
                    </label>
                    <input
                      type="number"
                      min={0}
                      step={0.1}
                      value={generalSettings.auto_chat.delay_chat_part_max}
                      onChange={(e) =>
                        handleGeneralChange(
                          "auto_chat",
                          "delay_chat_part_max",
                          parseFloat(e.target.value) || 0,
                        )
                      }
                      className="mt-0.5 w-full rounded-md border border-zinc-200 bg-transparent px-2 py-1.5 text-xs outline-none focus:border-zinc-400 dark:border-zinc-700 dark:focus:border-zinc-500"
                    />
                  </div>
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={handleSaveGeneralSettings}
                  disabled={generalSaving}
                  className="rounded-full bg-zinc-900 px-3 py-1.5 text-[11px] font-medium text-zinc-50 shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  {generalSaving ? "Saving..." : "Save general settings"}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

