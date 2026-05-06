"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import {
  Bell,
  Bot,
  ChevronDown,
  CircleUser,
  Code2,
  Database,
  Grid3X3,
  History,
  KeyRound,
  LogOut,
  Menu,
  Newspaper,
  Power,
  Search,
  Settings2,
  Shield,
  SlidersHorizontal,
  Terminal,
  Trash2,
  X,
} from "lucide-react";

import { AuthGate } from "@/components/auth-gate";
import { JarvisLogo } from "@/components/jarvis-logo";
import { TaskComposer } from "@/components/task-composer";
import { TaskStream } from "@/components/task-stream";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { approveTask, createTask, getTask, taskSocketUrl, type TaskRecord } from "@/lib/api";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

type ViewMode = "chat" | "settings" | "terminal" | "rag" | "security";
type SettingsTab = "General" | "Notifications" | "Personalization" | "Apps" | "Data controls" | "Security" | "Account";

export function JarvisShell() {
  return (
    <AuthGate>
      {(session) => (
        <JarvisWorkspace
          userEmail={session?.user.email ?? "Demo user"}
          userId={session?.user.id}
          accessToken={session?.access_token}
        />
      )}
    </AuthGate>
  );
}

function JarvisWorkspace({
  userEmail,
  userId,
  accessToken,
}: {
  userEmail: string;
  userId?: string;
  accessToken?: string;
}) {
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notice, setNotice] = useState("");
  const [view, setView] = useState<ViewMode>("chat");
  const [settingsTab, setSettingsTab] = useState<SettingsTab>("General");
  const [terminalCommand, setTerminalCommand] = useState("");
  const supabase = getSupabaseBrowserClient();

  async function submitPrompt(prompt: string) {
    setNotice("");
    setView("chat");
    try {
      const task = await createTask(prompt, userId, accessToken);
      setTasks((current) => [task, ...current]);
      watchTask(task.id, task.status);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Jarvis could not complete the request.");
    }
  }

  async function handleApprove(taskId: string, approved: boolean) {
    try {
      const currentTask = tasks.find((item) => item.id === taskId);
      if (approved && currentTask && /youtube|shorts/i.test(currentTask.prompt)) {
        window.open("https://www.youtube.com/shorts", "_blank", "noopener,noreferrer");
      }
      const task = await approveTask(taskId, approved, accessToken, currentTask);
      setTasks((current) => current.map((item) => (item.id === taskId ? task : item)));
      if (approved) watchTask(taskId, task.status);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Approval failed.");
    }
  }

  function watchTask(taskId: string, status?: TaskRecord["status"]) {
    if (status === "completed" || status === "failed" || status === "cancelled" || status === "waiting_approval") {
      return;
    }

    const socketUrl = taskSocketUrl(taskId);
    if (!socketUrl) {
      window.setTimeout(() => fetchTask(taskId), 650);
      return;
    }

    const socket = new WebSocket(socketUrl);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "snapshot" && payload.task) {
        setTasks((current) => current.map((item) => (item.id === taskId ? payload.task : item)));
      }
      if (payload.type === "completed" || payload.type === "failed" || payload.type === "status") {
        fetchTask(taskId);
      }
    };
    socket.onerror = () => socket.close();
  }

  async function fetchTask(taskId: string) {
    try {
      const task = await getTask(taskId, accessToken);
      setTasks((current) => current.map((item) => (item.id === taskId ? task : item)));
      watchTask(taskId, task.status);
    } catch {
      return;
    }
  }

  async function signOut() {
    if (supabase) await supabase.auth.signOut();
    window.location.reload();
  }

  async function runTerminalTask() {
    const command = terminalCommand.trim();
    if (!command) return;
    setTerminalCommand("");
    await submitPrompt(`terminal ${command}`);
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#ffffff] text-[#111113]">
      <aside
        className={cn(
          "jarvis-scroll fixed inset-y-0 left-0 z-30 flex w-[354px] shrink-0 flex-col overflow-y-auto border-r border-[#dfe2e7] bg-[#f7f7f8] px-4 py-5 transition-transform lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="mb-5 flex items-center justify-between gap-3">
          <button
            className="rounded-full"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label="Toggle sidebar"
            type="button"
          >
            <JarvisLogo className="h-14 w-14" />
          </button>
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar">
            <Menu size={24} />
          </Button>
        </div>

        <nav className="grid gap-2 text-lg">
          <SidebarButton icon={<Bot size={25} />} label="New chat" onClick={() => { setTasks([]); setView("chat"); }} active={view === "chat"} />
          <SidebarButton icon={<Search size={25} />} label="Search web" onClick={() => submitPrompt("search latest AI news")} />
          <SidebarButton icon={<SlidersHorizontal size={25} />} label="Settings" onClick={() => setView("settings")} active={view === "settings"} />
          <SidebarButton icon={<Terminal size={25} />} label="Terminal" onClick={() => setView("terminal")} active={view === "terminal"} />
        </nav>

        <div className="mt-8 grid gap-3">
          <p className="px-3 text-sm font-black uppercase tracking-wide text-[#4b4f56]">Tools</p>
          <SidebarButton icon={<Newspaper size={23} />} label="Daily briefing" onClick={() => submitPrompt("business news, sports news, and AI news today")} compact />
          <SidebarButton icon={<Code2 size={23} />} label="Code writer" onClick={() => submitPrompt("write production-ready code")} compact />
          <SidebarButton icon={<Database size={23} />} label="RAG memory" onClick={() => setView("rag")} active={view === "rag"} compact />
          <SidebarButton icon={<Shield size={23} />} label="Security" onClick={() => setView("security")} active={view === "security"} compact />
        </div>

        <div className="mt-8 grid min-h-[160px] gap-3">
          <div className="flex items-center justify-between px-3">
            <p className="text-sm font-black uppercase tracking-wide text-[#4b4f56]">History</p>
            <Button variant="ghost" size="icon" onClick={() => setTasks([])} aria-label="Clear history">
              <Trash2 size={18} />
            </Button>
          </div>
          <div className="grid gap-1">
            {tasks.length ? (
              tasks.slice(0, 10).map((task) => (
                <button
                  key={task.id}
                  className="truncate rounded-xl px-3 py-2 text-left text-sm text-[#45494f] hover:bg-[#ececf1]"
                  title={task.prompt}
                  onClick={() => setView("chat")}
                >
                  {task.prompt}
                </button>
              ))
            ) : (
              <p className="px-3 py-2 text-sm text-[#7d8188]">No history yet</p>
            )}
          </div>
        </div>

        <div className="mt-auto grid gap-3 pt-5">
          <SidebarButton
            icon={<Power size={24} />}
            label="Shutdown"
            danger
            onClick={() => submitPrompt("prepare shutdown request")}
          />
          <button
            className="flex w-full items-center gap-3 rounded-2xl bg-[#ececf1] p-3 text-left"
            onClick={signOut}
            type="button"
          >
            <span className="grid h-11 w-11 place-items-center rounded-full bg-[#10a37f] font-black text-white">
              {userEmail.slice(0, 2).toUpperCase()}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate font-black">Jarvis Cloud</span>
              <span className="block truncate text-sm text-[#6b7078]">{userEmail}</span>
            </span>
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      {sidebarOpen ? (
        <button
          className="fixed inset-0 z-20 bg-black/20 lg:hidden"
          aria-label="Close sidebar overlay"
          onClick={() => setSidebarOpen(false)}
          type="button"
        />
      ) : null}

      <main className="flex min-w-0 flex-1 flex-col bg-white">
        <header className="flex h-[74px] shrink-0 items-center justify-between border-b border-[#dfe2e7] bg-white px-4 sm:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar">
              <Menu size={26} />
            </Button>
            <button className="flex items-center gap-2" type="button" onClick={() => setView("chat")}>
              <h1 className="truncate text-3xl font-black tracking-normal">Jarvis</h1>
              <Badge>JS 1</Badge>
              <ChevronDown size={22} className="text-[#62666d]" />
            </button>
          </div>
          <div className="hidden items-center gap-2 sm:flex">
            <Badge tone="success">Cloud Core</Badge>
            <Badge tone="warning">Approval first</Badge>
          </div>
        </header>

        {notice ? (
          <div className="border-b border-[#dfe2e7] bg-[#fff7e6] px-4 py-3 text-sm font-semibold text-[#6e4a00] sm:px-8">
            {notice}
          </div>
        ) : null}

        <section className="jarvis-scroll min-h-0 flex-1 overflow-y-auto bg-white">
          {view === "chat" ? <TaskStream tasks={tasks} onApprove={handleApprove} onPrompt={submitPrompt} /> : null}
          {view === "settings" ? (
            <SettingsView
              activeTab={settingsTab}
              onTab={setSettingsTab}
              onClose={() => setView("chat")}
              onPrompt={submitPrompt}
              userEmail={userEmail}
            />
          ) : null}
          {view === "terminal" ? (
            <TerminalView
              command={terminalCommand}
              onCommand={setTerminalCommand}
              onRun={runTerminalTask}
              onClose={() => setView("chat")}
            />
          ) : null}
          {view === "rag" ? <RagView onPrompt={submitPrompt} onClose={() => setView("chat")} /> : null}
          {view === "security" ? <SecurityView onClose={() => setView("chat")} /> : null}
        </section>

        <TaskComposer onSubmit={submitPrompt} />
      </main>
    </div>
  );
}

function SidebarButton({
  icon,
  label,
  active,
  compact,
  danger,
  onClick,
}: {
  icon: ReactNode;
  label: string;
  active?: boolean;
  compact?: boolean;
  danger?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex min-h-14 items-center gap-4 rounded-2xl px-4 text-left font-medium text-[#2f3339] transition hover:bg-[#ececf1]",
        compact && "min-h-12 text-base text-[#5b5f66]",
        active && "bg-[#ececf1] text-[#111113]",
        danger && "text-[#e11919] hover:bg-[#fff1f1]",
      )}
      type="button"
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function SettingsView({
  activeTab,
  onTab,
  onClose,
  onPrompt,
  userEmail,
}: {
  activeTab: SettingsTab;
  onTab: (tab: SettingsTab) => void;
  onClose: () => void;
  onPrompt: (prompt: string) => void;
  userEmail: string;
}) {
  const tabs: Array<{ label: SettingsTab; icon: ReactNode }> = [
    { label: "General", icon: <Settings2 size={21} /> },
    { label: "Notifications", icon: <Bell size={21} /> },
    { label: "Personalization", icon: <History size={21} /> },
    { label: "Apps", icon: <Grid3X3 size={21} /> },
    { label: "Data controls", icon: <Database size={21} /> },
    { label: "Security", icon: <Shield size={21} /> },
    { label: "Account", icon: <CircleUser size={21} /> },
  ];

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-6 px-4 py-8 lg:grid-cols-[250px_minmax(0,1fr)]">
      <aside className="grid content-start gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.label}
            className={cn(
              "flex min-h-12 items-center gap-3 rounded-xl px-4 text-left font-semibold hover:bg-[#f5f5f5]",
              activeTab === tab.label && "bg-[#f5f5f5]",
            )}
            onClick={() => onTab(tab.label)}
            type="button"
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </aside>

      <div className="min-w-0">
        <div className="sticky top-0 z-10 grid grid-cols-[44px_1fr] items-center border-b border-[#dfe2e7] bg-white/95 py-4 backdrop-blur">
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close settings">
            <X size={22} />
          </Button>
          <h2 className="text-center text-2xl font-semibold">{activeTab}</h2>
        </div>

        {activeTab === "General" ? <GeneralSettings onPrompt={onPrompt} /> : null}
        {activeTab === "Notifications" ? <SimpleSettings title="Notifications" copy="Cloud notifications are ready for Supabase Realtime events, task updates, and briefing alerts." /> : null}
        {activeTab === "Personalization" ? <SimpleSettings title="Personalization" copy="Jarvis keeps the old assistant behavior: direct answers first, approval before action, concise structure, and optional RAG memory." /> : null}
        {activeTab === "Apps" ? <SimpleSettings title="Apps" copy="Cloud-safe apps run in browser sessions. Private laptop apps require the optional Local Core connector." /> : null}
        {activeTab === "Data controls" ? <DataSettings onPrompt={onPrompt} /> : null}
        {activeTab === "Security" ? <SecuritySettings /> : null}
        {activeTab === "Account" ? <AccountSettings userEmail={userEmail} /> : null}
      </div>
    </div>
  );
}

function GeneralSettings({ onPrompt }: { onPrompt: (prompt: string) => void }) {
  return (
    <div className="grid gap-5 pt-5">
      <section className="flex items-center justify-between gap-4 rounded-2xl border border-[#a6e5d7] bg-[#effbf8] p-5">
        <div>
          <p className="text-sm font-black uppercase tracking-wide text-[#6b7078]">Settings</p>
          <h3 className="text-2xl font-black tracking-normal">Security First Control</h3>
          <p className="mt-2 max-w-xl leading-7 text-[#5c6067]">
            Every sensitive cloud action goes through approval, backend-only secrets, and high security defaults.
          </p>
        </div>
        <Badge tone="success" className="gap-2">
          <Shield size={16} />
          HIGH
        </Badge>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <SettingsCard title="Security" icon={<Shield size={20} className="text-[#10a37f]" />}>
          <SwitchLine label="Email approval" checked />
          <SwitchLine label="Share approval" checked />
          <SwitchLine label="Terminal approval" checked />
          <SwitchLine label="Deployment approval" checked />
        </SettingsCard>

        <SettingsCard title="Brain" icon={<Bot size={20} className="text-[#10a37f]" />}>
          <div className="flex flex-wrap gap-2">
            <Badge>Typo fix</Badge>
            <Badge>Local templates</Badge>
            <Badge>RAG memory</Badge>
          </div>
          <SwitchLine label="Default cloud model" checked />
          <SwitchLine label="Context repair" checked />
          <Button onClick={() => onPrompt("train model")} className="mt-2">
            Test Brain
          </Button>
        </SettingsCard>

        <SettingsCard title="Optional API" icon={<KeyRound size={20} className="text-[#10a37f]" />}>
          <SwitchLine label="Use custom API" />
          <Input placeholder="OpenAI-compatible API key" type="password" />
          <Input placeholder="API endpoint" />
          <Input placeholder="Model name" />
          <Button variant="outline">Save API settings</Button>
        </SettingsCard>

        <SettingsCard title="Daily Briefing" icon={<Newspaper size={20} className="text-[#10a37f]" />}>
          <SwitchLine label="Important news" checked />
          <Input placeholder="WhatsApp number with country code" />
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => onPrompt("business news, sports news, and AI news today")}>Get Briefing</Button>
            <Button variant="outline" onClick={() => onPrompt("share daily briefing to whatsapp")}>Share WhatsApp</Button>
          </div>
        </SettingsCard>
      </div>
    </div>
  );
}

function DataSettings({ onPrompt }: { onPrompt: (prompt: string) => void }) {
  return (
    <div className="grid gap-4 pt-5">
      <SettingsCard title="RAG Memory" icon={<Database size={20} className="text-[#10a37f]" />}>
        <Input placeholder="Link to learn from" />
        <Textarea placeholder="Paste text Jarvis should learn" className="min-h-28" />
        <Input placeholder="Dataset path, URL, or Kaggle slug" />
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => onPrompt("train model")}>Train Model</Button>
          <Button variant="outline" onClick={() => onPrompt("skill status")}>Skill Status</Button>
        </div>
      </SettingsCard>
    </div>
  );
}

function SecuritySettings() {
  return (
    <div className="grid gap-4 pt-5">
      <SettingsCard title="Secure your Jarvis" icon={<Shield size={20} className="text-[#10a37f]" />}>
        <p className="leading-7 text-[#5c6067]">
          High security stays enabled. Sending, sharing, shutdown, terminal commands, deployments, and browser automation ask permission first.
        </p>
        <SwitchLine label="Approval-first protection" checked />
        <SwitchLine label="Backend-only secrets" checked />
        <SwitchLine label="No frontend API keys" checked />
        <SwitchLine label="Action logging ready" checked />
      </SettingsCard>
    </div>
  );
}

function AccountSettings({ userEmail }: { userEmail: string }) {
  return (
    <div className="grid gap-4 pt-5">
      <SettingsCard title="Account" icon={<CircleUser size={20} className="text-[#10a37f]" />}>
        <div className="flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-[#10a37f] font-black text-white">
            {userEmail.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <strong className="block">Jarvis User</strong>
            <span className="text-sm text-[#6b7078]">{userEmail}</span>
          </div>
        </div>
        <SwitchLine label="Cloud workspace" checked />
      </SettingsCard>
    </div>
  );
}

function SimpleSettings({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="grid gap-4 pt-5">
      <SettingsCard title={title} icon={<Settings2 size={20} className="text-[#10a37f]" />}>
        <p className="leading-7 text-[#5c6067]">{copy}</p>
      </SettingsCard>
    </div>
  );
}

function TerminalView({
  command,
  onCommand,
  onRun,
  onClose,
}: {
  command: string;
  onCommand: (value: string) => void;
  onRun: () => void;
  onClose: () => void;
}) {
  return (
    <div className="mx-auto grid w-full max-w-5xl gap-5 px-4 py-8">
      <section className="flex items-center justify-between gap-4 rounded-2xl border border-[#dfe2e7] bg-[#effbf8] p-5">
        <div>
          <p className="text-sm font-black uppercase tracking-wide text-[#6b7078]">Cloud Terminal</p>
          <h2 className="text-2xl font-black tracking-normal">Approval-first command runner</h2>
          <p className="mt-2 max-w-2xl leading-7 text-[#5c6067]">
            Hosted Jarvis prepares terminal workflows safely. Actual laptop commands need Local Core; cloud commands need a worker sandbox.
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X size={22} />
        </Button>
      </section>
      <div className="rounded-2xl border border-[#dfe2e7] bg-[#10141d] p-4 text-white">
        <div className="mb-4 font-mono text-sm text-[#a7f3d0]">jarvis-cloud $ waiting for approved command</div>
        <div className="flex gap-2">
          <Input
            value={command}
            onChange={(event) => onCommand(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") onRun();
            }}
            placeholder="Example: npm run build"
            className="border-[#2d3442] bg-[#171c28] text-white placeholder:text-[#8b93a3]"
          />
          <Button onClick={onRun}>Run</Button>
        </div>
      </div>
    </div>
  );
}

function RagView({ onPrompt, onClose }: { onPrompt: (prompt: string) => void; onClose: () => void }) {
  return (
    <div className="mx-auto grid w-full max-w-5xl gap-5 px-4 py-8">
      <section className="flex items-center justify-between gap-4 rounded-2xl border border-[#dfe2e7] bg-white p-5">
        <div>
          <p className="text-sm font-black uppercase tracking-wide text-[#6b7078]">RAG Memory</p>
          <h2 className="text-2xl font-black tracking-normal">Teach Jarvis with links, text, and datasets</h2>
          <p className="mt-2 max-w-2xl leading-7 text-[#5c6067]">
            Cloud mode stores knowledge through backend APIs. Local mode can still use the older `jarvis_data` memory.
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X size={22} />
        </Button>
      </section>
      <DataSettings onPrompt={onPrompt} />
    </div>
  );
}

function SecurityView({ onClose }: { onClose: () => void }) {
  return (
    <div className="mx-auto grid w-full max-w-5xl gap-5 px-4 py-8">
      <section className="flex items-center justify-between gap-4 rounded-2xl border border-[#a6e5d7] bg-[#effbf8] p-5">
        <div>
          <p className="text-sm font-black uppercase tracking-wide text-[#08765a]">Security</p>
          <h2 className="text-2xl font-black tracking-normal">HIGH security is always on</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X size={22} />
        </Button>
      </section>
      <SecuritySettings />
    </div>
  );
}

function SettingsCard({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return (
    <article className="grid content-start gap-4 rounded-2xl border border-[#dfe2e7] bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2 text-lg font-black">
        {icon}
        <span>{title}</span>
      </div>
      {children}
    </article>
  );
}

function SwitchLine({ label, checked }: { label: string; checked?: boolean }) {
  return (
    <div className="flex min-h-9 items-center justify-between gap-4 rounded-xl bg-[#f7f7f8] px-3 py-2">
      <span className="text-sm font-semibold text-[#555a62]">{label}</span>
      <span className={cn("grid h-5 w-5 place-items-center rounded border", checked ? "border-[#10a37f] bg-[#10a37f]" : "border-[#b9bdc5] bg-white")}>
        {checked ? <span className="h-2 w-2 rounded-full bg-white" /> : null}
      </span>
    </div>
  );
}
