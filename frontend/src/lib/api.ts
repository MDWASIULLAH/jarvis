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

const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export async function createTask(prompt: string, userId?: string, token?: string) {
  const response = await fetch(`${apiBase}/api/tasks`, {
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

export async function approveTask(taskId: string, approved: boolean, token?: string) {
  const response = await fetch(`${apiBase}/api/tasks/${taskId}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ approved }),
  });

  if (!response.ok) {
    throw new Error(`Approval failed with ${response.status}`);
  }

  return (await response.json()) as TaskRecord;
}

export function taskSocketUrl(taskId: string) {
  const socketBase = apiBase.replace(/^http/, "ws");
  return `${socketBase}/ws/tasks/${taskId}`;
}
