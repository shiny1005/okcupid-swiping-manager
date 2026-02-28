import { Account, Job, LogEntry, RateConfig } from "@/components/dashboard/types";

/** Backend API base URL (no trailing slash). Set NEXT_PUBLIC_BACKEND_URL or defaults to http://localhost:8000 */
function getApiBase(): string {
  const raw =
    typeof process.env.NEXT_PUBLIC_BACKEND_URL === "string" &&
    process.env.NEXT_PUBLIC_BACKEND_URL.trim() !== ""
      ? process.env.NEXT_PUBLIC_BACKEND_URL.trim()
      : "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

const API_BASE = getApiBase();

async function postJson<TResponse = unknown>(
  path: string,
  body: unknown,
): Promise<TResponse> {
  const url = path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Request failed (${res.status} ${res.statusText})${text ? `: ${text}` : ""}`,
    );
  }

  try {
    return (await res.json()) as TResponse;
  } catch {
    return undefined as TResponse;
  }
}

async function getJson<TResponse = unknown>(path: string): Promise<TResponse> {
  const url = path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
  const res = await fetch(url, {
    method: "GET",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Request failed (${res.status} ${res.statusText})${text ? `: ${text}` : ""}`,
    );
  }

  return (await res.json()) as TResponse;
}

async function putJson<TResponse = unknown>(
  path: string,
  body: unknown,
): Promise<TResponse> {
  const url = path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
  const res = await fetch(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Request failed (${res.status} ${res.statusText})${text ? `: ${text}` : ""}`,
    );
  }

  try {
    return (await res.json()) as TResponse;
  } catch {
    return undefined as TResponse;
  }
}

async function deleteRequest(path: string): Promise<void> {
  const url = path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`;
  const res = await fetch(url, {
    method: "DELETE",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Request failed (${res.status} ${res.statusText})${text ? `: ${text}` : ""}`,
    );
  }
}

// High-level automation actions

export async function startAiChatForAccounts(accountIds: string[]) {
  if (accountIds.length === 0) return;
  await postJson("/api/automation/ai-auto-chat", { accountIds });
}

export type AutoSwipeSummary = {
  swiped: number;
  skipped: number;
  errors: number;
  results: unknown[];
};

export type AutoSwipeResponse = {
  status: string;
  summary: Record<string, AutoSwipeSummary>;
};

export async function autoSwipeProfilesForAccounts(
  accountIds: string[],
  count: number,
): Promise<AutoSwipeResponse | undefined> {
  if (accountIds.length === 0 || count <= 0) return undefined;
  return postJson<AutoSwipeResponse>("/api/automation/auto-swipe", {
    accountIds,
    count,
  });
}

export type ProfileSummary = {
  accountId: string;
  settings?: {
    id?: string;
    birthdate?: { year?: number; month?: number; day?: number };
    unitPreference?: string;
    emailAddress?: string;
    realname?: string;
    displayname?: string;
    phoneNumber?: string;
    userLocation?: {
      id?: string;
      countryCode?: string;
      stateCode?: string;
      fullName?: string;
      publicName?: string;
    };
  } & Record<string, unknown>;
  bio?: {
    text?: string;
    avatar_url?: string;
  } & Record<string, unknown>;
};

export async function getProfileInfo(
  accountId: string,
): Promise<ProfileSummary> {
  return getJson<ProfileSummary>(
    `/api/profiles/${encodeURIComponent(accountId)}`,
  );
}

export async function updateProfileBio(accountId: string, bio: string) {
  await postJson("/api/profile/update-bio", { accountId, bio });
}

export async function updateProfileRealname(
  accountId: string,
  realname: string,
) {
  await postJson("/api/profile/update-realname", { accountId, realname });
}

// Data fetching helpers

export async function fetchAccounts(): Promise<Account[]> {
  return getJson<Account[]>("/api/accounts");
}

export async function fetchJobs(): Promise<Job[]> {
  return getJson<Job[]>("/api/jobs");
}

export async function fetchLogs(): Promise<LogEntry[]> {
  return getJson<LogEntry[]>("/api/logs");
}

/** Config used by backend and example scripts (no secrets). Shown on Logs page. */
export type EffectiveConfig = {
  sample_json_loaded: boolean;
  api: Record<string, string>;
  graphql: Record<string, string>;
  auth_header_keys: string[];
  general_settings: {
    swipe: Record<string, unknown>;
    auto_chat: Record<string, unknown>;
  };
  openai: { hasKey: boolean; model: string | null };
  accounts_count: number;
};

export async function fetchEffectiveConfig(): Promise<EffectiveConfig> {
  return getJson<EffectiveConfig>("/api/effective-config");
}

export async function fetchRateConfig(): Promise<RateConfig> {
  return getJson<RateConfig>("/api/rate-config");
}

export async function updateRateConfig(config: RateConfig): Promise<void> {
  await postJson("/api/rate-config", config);
}

// OpenAI configuration

export type OpenAIConfigSummary = {
  hasKey: boolean;
  maskedKey: string | null;
  model: string | null;
};

export async function fetchOpenAIConfig(): Promise<OpenAIConfigSummary> {
  return getJson<OpenAIConfigSummary>("/api/openai-config");
}

export async function updateOpenAIConfig(
  apiKey?: string,
  model?: string,
): Promise<void> {
  const body: { apiKey?: string; model?: string } = {};
  if (apiKey !== undefined && apiKey.trim()) body.apiKey = apiKey.trim();
  if (model !== undefined && model.trim()) body.model = model.trim();
  await postJson("/api/openai-config", body);
}

// General settings (swipe + auto_chat)

export type SwipeSettings = {
  directions: string[];
  like_percentage: number;
  max_swipes: number;
  delay_seconds: number;
};

export type AutoChatSettings = {
  funnel: string;
  poll_seconds: number;
  cta_min_msgs: number;
  cta_max_msgs: number;
  delay_chat_part_min: number;
  delay_chat_part_max: number;
};

export type GeneralSettings = {
  swipe: SwipeSettings;
  auto_chat: AutoChatSettings;
};

export async function fetchGeneralSettings(): Promise<GeneralSettings> {
  return getJson<GeneralSettings>("/api/general-settings");
}

export async function updateGeneralSettings(
  settings: GeneralSettings,
): Promise<void> {
  await postJson("/api/general-settings", settings);
}

// Account management

export type AccountForEdit = {
  id: string;
  name: string;
  proxy?: {
    type?: string;
    host?: string;
    port?: number;
    username?: string;
    password?: string;
  };
  hasAuth: boolean;
  authenticationToken?: string;
  cookie?: string;
};

export async function getAccountForEdit(
  accountId: string,
): Promise<AccountForEdit> {
  return getJson<AccountForEdit>(`/api/accounts/${encodeURIComponent(accountId)}`);
}

export async function createAccount(params: {
  name: string;
  authenticationToken: string;
  cookie: string;
  proxyType: string;
  proxyHost: string;
  proxyPort: number;
  proxyUsername?: string;
  proxyPassword?: string;
}): Promise<Account> {
  return postJson<Account>("/api/accounts", {
    name: params.name,
    authentication_token: params.authenticationToken,
    cookie: params.cookie,
    proxy: {
      type: params.proxyType || "socks5",
      host: params.proxyHost,
      port: params.proxyPort,
      username: params.proxyUsername,
      password: params.proxyPassword,
    },
  });
}

export async function updateAccount(
  accountId: string,
  params: {
    name?: string;
    authenticationToken?: string;
    cookie?: string;
    proxyType: string;
    proxyHost: string;
    proxyPort: number;
    proxyUsername?: string;
    proxyPassword?: string;
  },
): Promise<Account> {
  const body: {
    name?: string;
    authentication_token?: string;
    cookie?: string;
    proxy: object;
  } = {
    proxy: {
      type: params.proxyType || "socks5",
      host: params.proxyHost,
      port: params.proxyPort,
      username: params.proxyUsername,
      password: params.proxyPassword,
    },
  };
  if (params.name !== undefined) body.name = params.name;
  if (params.authenticationToken !== undefined)
    body.authentication_token = params.authenticationToken;
  if (params.cookie !== undefined) body.cookie = params.cookie;
  return putJson<Account>(
    `/api/accounts/${encodeURIComponent(accountId)}`,
    body,
  );
}

export async function deleteAccount(accountId: string): Promise<void> {
  await deleteRequest(`/api/accounts/${encodeURIComponent(accountId)}`);
}


