export type TaskStatus =
  | "planned"
  | "waiting_approval"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type TaskRecord = {
  id: string;
  user_id?: string | null;
  session_id?: string | null;
  prompt: string;
  status: TaskStatus;
  plan: {
    intent: string;
    summary: string;
    risk: "low" | "medium" | "high" | "critical";
    requires_approval: boolean;
    steps: string[];
    actions: Array<{ type: string; label: string; target?: string | null; payload?: Record<string, unknown> }>;
  };
  result?: {
    answer?: string;
    status?: string;
    sources?: Array<{ title: string; url: string }>;
    technical_details?: Record<string, unknown>;
  } | null;
  error?: string | null;
};

const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

function getApiBase() {
  const raw = configuredApiBase ? configuredApiBase.replace(/\/$/, "") : "";
  if (typeof window === "undefined") return raw;

  const pageIsLocal = ["localhost", "127.0.0.1", "0.0.0.0"].includes(window.location.hostname);
  const targetIsLocal = /^https?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?/i.test(raw);
  if (!pageIsLocal && targetIsLocal) return "";

  return raw;
}

function apiPath(path: string) {
  return `${getApiBase()}${path}`;
}

export async function createTask(prompt: string, userId?: string, token?: string) {
  const response = await fetch(apiPath("/api/tasks"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ prompt, user_id: userId }),
  });

  if (!response.ok) {
    throw new Error(`Jarvis backend returned ${response.status}`);
  }

  return (await response.json()) as TaskRecord;
}

export async function approveTask(taskId: string, approved: boolean, token?: string, taskSnapshot?: TaskRecord) {
  const response = await fetch(apiPath(`/api/tasks/${taskId}/approve`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ approved, task: taskSnapshot }),
  });

  if (!response.ok) {
    throw new Error(`Approval failed with ${response.status}`);
  }

  return (await response.json()) as TaskRecord;
}

export function taskSocketUrl(taskId: string) {
  const apiBase = getApiBase();
  if (!apiBase) return null;
  const socketBase = apiBase.replace(/^http/, "ws");
  return `${socketBase}/ws/tasks/${taskId}`;
}

export async function getTask(taskId: string, token?: string) {
  const response = await fetch(apiPath(`/api/tasks/${taskId}`), {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Jarvis task lookup returned ${response.status}`);
  }

  return (await response.json()) as TaskRecord;
}
