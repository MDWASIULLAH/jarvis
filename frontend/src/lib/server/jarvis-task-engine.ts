type TaskStatus = "waiting_approval" | "queued" | "running" | "completed" | "failed" | "cancelled";
type RiskLevel = "low" | "medium" | "high" | "critical";

type TaskRecord = {
  id: string;
  user_id?: string | null;
  session_id?: string | null;
  prompt: string;
  status: TaskStatus;
  plan: {
    id: string;
    intent: string;
    summary: string;
    risk: RiskLevel;
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
  created_at: string;
  updated_at: string;
};

const globalTaskStore = globalThis as typeof globalThis & {
  __jarvisTasks?: Map<string, TaskRecord>;
};

export const taskStore = globalTaskStore.__jarvisTasks ?? new Map<string, TaskRecord>();
globalTaskStore.__jarvisTasks = taskStore;

export async function createJarvisTask(prompt: string, userId?: string | null) {
  const cleanPrompt = prompt.trim();
  const plan = planTask(cleanPrompt);
  const now = new Date().toISOString();
  const task: TaskRecord = {
    id: `task_${crypto.randomUUID().replaceAll("-", "").slice(0, 16)}`,
    user_id: userId ?? null,
    prompt: cleanPrompt,
    status: plan.requires_approval ? "waiting_approval" : "completed",
    plan,
    result: plan.requires_approval ? null : await answerTask(cleanPrompt, plan.intent),
    created_at: now,
    updated_at: now,
  };
  taskStore.set(task.id, task);
  return task;
}

export async function approveJarvisTask(taskId: string, approved: boolean) {
  const task = taskStore.get(taskId);
  if (!task) return null;
  return approveJarvisTaskSnapshot(task, approved);
}

export async function approveJarvisTaskSnapshot(task: TaskRecord, approved: boolean) {
  if (!approved) {
    task.status = "cancelled";
    task.updated_at = new Date().toISOString();
    task.result = {
      status: "cancelled",
      answer: "Cancelled. Jarvis did not run the action.",
    };
    return task;
  }

  task.status = "completed";
  task.updated_at = new Date().toISOString();
  task.result = await approvedActionResult(task.prompt, task.plan.intent);
  return task;
}

export function getJarvisTask(taskId: string) {
  return taskStore.get(taskId) ?? null;
}

function planTask(prompt: string): TaskRecord["plan"] {
  const lower = prompt.toLowerCase();
  const intent = detectIntent(lower);
  const needsApproval = ["send_email", "deploy", "terminal", "desktop", "browser_action"].includes(intent);
  const risk: RiskLevel = intent === "deploy" ? "critical" : needsApproval ? "high" : "low";

  return {
    id: `plan_${crypto.randomUUID().replaceAll("-", "").slice(0, 12)}`,
    intent,
    summary: planSummary(intent, prompt),
    risk,
    requires_approval: needsApproval,
    steps: planSteps(intent),
    actions: [{ type: `${intent}.run`, label: planSummary(intent, prompt), target: extractUrl(prompt) }],
  };
}

function detectIntent(lower: string) {
  if (lower.includes("send email") || lower.includes("send mail") || lower.includes("message ")) return "send_email";
  if (lower.includes("draft email") || lower.includes("write email") || lower.includes("email to")) return "draft_email";
  if (lower.includes("deploy") || lower.includes("vercel")) return "deploy";
  if (lower.includes("terminal") || lower.includes("command") || lower.includes("powershell")) return "terminal";
  if (lower.includes("open vs code") || lower.includes("open vscode") || lower.includes("open calculator")) return "desktop";
  if (lower.includes("open youtube") || lower.includes("scroll") || lower.includes("click")) return "browser_action";
  if (lower.includes("search") || lower.includes("news") || lower.includes("latest")) return "search";
  if (lower.includes("read ") && extractUrl(lower)) return "read_link";
  if (lower.includes("code") || lower.includes("react") || lower.includes("python") || lower.includes("html")) return "code";
  return "answer";
}

function planSummary(intent: string, prompt: string) {
  const labels: Record<string, string> = {
    search: "Search and summarize live information",
    read_link: "Read and summarize the link",
    code: "Generate complete code",
    draft_email: "Draft a complete message",
    send_email: "Prepare message for approval before sending",
    deploy: "Prepare deployment workflow for approval",
    terminal: "Prepare terminal workflow for approval",
    desktop: "Request optional desktop connector approval",
    browser_action: "Prepare browser automation for approval",
    answer: "Answer directly",
  };
  return labels[intent] ?? `Handle: ${prompt}`;
}

function planSteps(intent: string) {
  const common = {
    search: ["Search open web sources.", "Extract key facts.", "Return a structured answer with source links."],
    read_link: ["Fetch the page.", "Remove boilerplate.", "Summarize direct answer first."],
    code: ["Infer language and framework.", "Write complete runnable code.", "Add usage notes."],
    draft_email: ["Understand the purpose.", "Write a complete subject and body.", "Do not send without permission."],
    send_email: ["Prepare recipient, subject, and body.", "Show approval card.", "Send only after approval."],
    deploy: ["Inspect deployment intent.", "Prepare command and risk summary.", "Deploy only after approval."],
    terminal: ["Prepare a safe command plan.", "Show risk before execution.", "Run only through an approved backend or connector."],
    desktop: ["Prepare desktop connector request.", "Ask approval.", "Run only on the user's installed connector."],
    browser_action: ["Create an isolated browser task.", "Ask approval.", "Stream progress during automation."],
    answer: ["Understand the question.", "Answer directly.", "Add short details if useful."],
  };
  return common[intent as keyof typeof common] ?? common.answer;
}

async function answerTask(prompt: string, intent: string) {
  if (intent === "search") return await searchAnswer(prompt);
  if (intent === "code") return codeAnswer(prompt);
  if (intent === "draft_email") return emailDraftAnswer(prompt);
  if (intent === "read_link") return readLinkAnswer(prompt);
  return directAnswer(prompt);
}

async function approvedActionResult(prompt: string, intent: string) {
  if (intent === "send_email") {
    return {
      status: "completed",
      answer:
        "Approval received.\n\nJarvis prepared the email workflow. Actual sending needs a configured server mail provider such as Resend, SMTP, or Supabase Edge Function. No email was sent yet because no sending provider is connected in this Vercel app.",
      technical_details: { next_step: "Configure a backend-only email provider, then connect the send_email action." },
    };
  }

  return {
    status: "completed",
    answer:
      `Approval received for: ${prompt}\n\nThis Vercel app can run web-safe cloud tasks now. Direct laptop actions still need the optional hybrid connector because a website cannot open private Windows apps by itself.`,
    technical_details: { intent },
  };
}

async function searchAnswer(prompt: string) {
  const query = normalizeSearchQuery(prompt);
  const news = await fetchNews(query);
  if (news.length) {
    return {
      status: "completed",
      answer: `Here are the latest results for ${query}:\n\n${news
        .map((item, index) => `${index + 1}. ${item.title}\n   ${item.summary}`)
        .join("\n\n")}`,
      sources: news.map(({ title, url }) => ({ title, url })),
      technical_details: { provider: "Google News RSS fallback", query },
    };
  }

  return {
    status: "completed",
    answer:
      `I could not fetch live headlines from the serverless search fallback right now.\n\nOpen this source search instead: https://www.google.com/search?q=${encodeURIComponent(
        query,
      )}`,
    sources: [{ title: `Search ${query}`, url: `https://www.google.com/search?q=${encodeURIComponent(query)}` }],
  };
}

function codeAnswer(prompt: string) {
  const lower = prompt.toLowerCase();
  if (lower.includes("python") && lower.includes("calculator")) {
    return {
      status: "completed",
      answer:
        "Here is a complete runnable Python calculator:\n\n```python\nimport tkinter as tk\n\nclass Calculator(tk.Tk):\n    def __init__(self):\n        super().__init__()\n        self.title('Calculator')\n        self.resizable(False, False)\n        self.expression = tk.StringVar(value='0')\n        tk.Entry(self, textvariable=self.expression, justify='right', font=('Segoe UI', 22), width=18).grid(row=0, column=0, columnspan=4, padx=8, pady=8)\n        buttons = [\n            ('7',1,0),('8',1,1),('9',1,2),('/',1,3),\n            ('4',2,0),('5',2,1),('6',2,2),('*',2,3),\n            ('1',3,0),('2',3,1),('3',3,2),('-',3,3),\n            ('0',4,0),('.',4,1),('C',4,2),('+',4,3),('=',5,0)\n        ]\n        for text, row, col in buttons:\n            span = 4 if text == '=' else 1\n            tk.Button(self, text=text, width=5, height=2, font=('Segoe UI', 14), command=lambda v=text: self.press(v)).grid(row=row, column=col, columnspan=span, padx=4, pady=4, sticky='ew')\n\n    def press(self, value):\n        current = self.expression.get()\n        if value == 'C':\n            self.expression.set('0')\n        elif value == '=':\n            if set(current) <= set('0123456789+-*/(). '):\n                try:\n                    self.expression.set(str(eval(current, {'__builtins__': {}}, {})))\n                except Exception:\n                    self.expression.set('Error')\n        else:\n            self.expression.set(value if current in {'0', 'Error'} else current + value)\n\nif __name__ == '__main__':\n    Calculator().mainloop()\n```\n\nRun it with `python calculator.py`.",
    };
  }

  if (lower.includes("react")) {
    return {
      status: "completed",
      answer:
        "Here is a clean React dashboard component:\n\n```tsx\nconst cards = [\n  { label: 'Revenue', value: '$48.2K' },\n  { label: 'Active users', value: '12,840' },\n  { label: 'Conversion', value: '8.4%' },\n];\n\nexport default function Dashboard() {\n  return (\n    <main className=\"min-h-screen bg-slate-50 p-6 text-slate-950\">\n      <section className=\"mx-auto grid max-w-6xl gap-6\">\n        <header>\n          <h1 className=\"text-3xl font-bold\">Business Dashboard</h1>\n          <p className=\"text-slate-600\">Live overview of core metrics.</p>\n        </header>\n        <div className=\"grid gap-4 md:grid-cols-3\">\n          {cards.map((card) => (\n            <article key={card.label} className=\"rounded-xl border bg-white p-5 shadow-sm\">\n              <p className=\"text-sm font-medium text-slate-500\">{card.label}</p>\n              <strong className=\"mt-2 block text-3xl\">{card.value}</strong>\n            </article>\n          ))}\n        </div>\n      </section>\n    </main>\n  );\n}\n```\n\nUse it in a Next.js page or React app and replace the demo metrics with live data.",
    };
  }

  return {
    status: "completed",
    answer:
      "I can write the code, but I need the target language or framework for the best result.\n\nExample prompts:\n- write Python code for a calculator\n- write HTML CSS JavaScript website for name fixer\n- create React dashboard with charts\n- create Next.js login page with Supabase",
  };
}

function emailDraftAnswer(prompt: string) {
  return {
    status: "completed",
    answer:
      "Subject: Request for Leave\n\nDear Teacher,\n\nI hope you are doing well. I am writing to request leave because I am unable to attend class on the required date. I will make sure to complete any missed work and collect the notes from my classmates.\n\nPlease grant me leave for this period.\n\nThank you for your understanding.\n\nSincerely,\nYour Name\n\nJarvis has drafted this only. It has not been sent.",
    technical_details: { prompt },
  };
}

function readLinkAnswer(prompt: string) {
  const url = extractUrl(prompt);
  return {
    status: "completed",
    answer: url
      ? `I can read this link through the cloud extraction worker: ${url}\n\nThe lightweight Vercel route received the task. For full page extraction, connect the Docker backend/worker because Playwright browser sessions need a worker host.`
      : "Please paste the link you want Jarvis to read.",
    sources: url ? [{ title: url, url }] : [],
  };
}

function directAnswer(prompt: string) {
  const lower = prompt.toLowerCase();
  if (lower.includes("your name") || lower.includes("who are you") || lower.includes("what is your name")) {
    return {
      status: "completed",
      answer:
        "My name is Jarvis.\n\nI am your cloud AI agent interface for answering questions, searching news, writing code, drafting messages, and preparing approved automation workflows.",
    };
  }

  if (lower.includes("kiit")) {
    return {
      status: "completed",
      answer:
        "KIIT University is a private deemed-to-be university in Bhubaneswar, Odisha, India.\n\nIt is known for engineering, computer science, management, law, biotechnology, medical sciences, and other professional programs. The broader KIIT group also includes KISS, a major institute focused on education for tribal students.\n\nFor admissions, fees, rankings, and current notices, Jarvis should use live search because those details change often.",
      sources: [{ title: "KIIT University official website", url: "https://kiit.ac.in/" }],
    };
  }

  if (lower.includes("what can you do") || lower.includes("help")) {
    return {
      status: "completed",
      answer:
        "I can help with questions, live news search, code writing, email drafts, reading links, deployment plans, and approval-first automation.\n\nFor safe cloud tasks I can answer directly from this website. For private laptop control, like opening VS Code or Calculator, Jarvis needs the optional desktop connector because browsers cannot control your computer directly without a local agent.",
    };
  }

  return {
    status: "completed",
    answer:
      `Direct answer:\nI understood your request: "${prompt}".\n\nShort explanation:\nThe Vercel web agent is now handling prompts through its built-in task API. For deeper reasoning, connect an OpenAI-compatible or local model endpoint in the backend environment.`,
  };
}

async function fetchNews(query: string) {
  try {
    const url = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=en-US&gl=US&ceid=US:en`;
    const response = await fetch(url, { next: { revalidate: 300 } });
    if (!response.ok) return [];
    const xml = await response.text();
    return parseRss(xml).slice(0, 6);
  } catch {
    return [];
  }
}

function parseRss(xml: string) {
  const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)];
  return items.map((match) => {
    const block = match[1];
    return {
      title: decodeXml(extractTag(block, "title")),
      url: decodeXml(extractTag(block, "link")),
      summary: stripHtml(decodeXml(extractTag(block, "description"))),
    };
  });
}

function extractTag(block: string, tag: string) {
  const match = block.match(new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`));
  return match ? match[1].replace(/^<!\[CDATA\[/, "").replace(/\]\]>$/, "") : "";
}

function decodeXml(value: string) {
  return value
    .replaceAll("&amp;", "&")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"')
    .replaceAll("&#39;", "'");
}

function stripHtml(value: string) {
  return value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function normalizeSearchQuery(prompt: string) {
  return prompt
    .replace(/^search\s+/i, "")
    .replace(/^tell me\s+/i, "")
    .trim();
}

function extractUrl(prompt: string) {
  return prompt.match(/https?:\/\/[^\s)>\"]+/i)?.[0] ?? null;
}
