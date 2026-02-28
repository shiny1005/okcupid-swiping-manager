export type AccountStatus = "active" | "paused" | "error" | "pending";

export type SessionState =
  | "ok"
  | "expiring"
  | "expired"
  | "login_required"
  | "blocked";

export type Account = {
  id: string;
  name: string;
  proxy?: string;
  status: AccountStatus;
  lastActive: string;
  tokenExpiry: string;
  sessionState: SessionState;
  loginRequired: boolean;
  error?: string;
  actionsToday: number;
  successRate: number;
  failureRate: number;
  swipeLikes: number;
  swipePasses: number;
  swipeErrors: number;
  swipeLikeRate: number;
  swipePassRate: number;
  swipeErrorRate: number;
};

export type JobStatus = "running" | "pending" | "completed" | "failed";

export type Job = {
  id: string;
  accountId?: string;
  type: string;
  status: JobStatus;
  attempts: number;
  createdAt: string;
};

export type LogLevel = "info" | "warning" | "error";

export type LogEntry = {
  id: string;
  accountId: string;
  timestamp: string;
  level: LogLevel;
  source: "action" | "error" | "api" | "auto-swipe";
  message: string;
};

export type RateConfig = {
  maxActionsPerHour: number;
  delayMinMs: number;
  delayMaxMs: number;
  randomizationEnabled: boolean;
  retryLimit: number;
};

export type BulkActionType =
  | "start_ai_chat"
  | "swipe_50"
  | "update_bio"
  | "pause_selected"
  | "activate_selected"
  | "send_campaign";

