"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import {
  Bot,
  Code2,
  History,
  LogOut,
  Menu,
  Newspaper,
  Search,
  Settings2,
  Shield,
  Terminal,
  Trash2,
} from "lucide-react";

import { AuthGate } from "@/components/auth-gate";
import { JarvisLogo } from "@/components/jarvis-logo";
import { TaskComposer } from "@/components/task-composer";
import { TaskStream } from "@/components/task-stream";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { approveTask, createTask, taskSocketUrl, type TaskRecord } from "@/lib/api";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

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
  const supabase = getSupabaseBrowserClient();

  async function submitPrompt(prompt: string) {
    setNotice("");
    try {
      const task = await createTask(prompt, userId, accessToken);
      setTasks((current) => [task, ...current]);
      watchTask(task.id);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Jarvis backend is not reachable.");
    }
  }

  async function handleApprove(taskId: string, approved: boolean) {
    try {
      const task = await approveTask(taskId, approved, accessToken);
      setTasks((current) => current.map((item) => (item.id === taskId ? task : item)));
      if (approved) watchTask(taskId);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Approval failed.");
    }
  }

  function watchTask(taskId: string) {
    const socket = new WebSocket(taskSocketUrl(taskId));
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
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const response = await fetch(`${base.replace(/\/$/, "")}/api/tasks/${taskId}`);
    if (!response.ok) return;
    const task = (await response.json()) as TaskRecord;
    setTasks((current) => current.map((item) => (item.id === taskId ? task : item)));
  }

  async function signOut() {
    if (supabase) await supabase.auth.signOut();
    window.location.reload();
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#f7f8fa] text-[#111113]">
      <aside
        className={cn(
          "jarvis-scroll fixed inset-y-0 left-0 z-30 flex w-[320px] shrink-0 flex-col overflow-y-auto border-r border-[#dfe2e7] bg-[#fbfbfc] p-4 transition-transform lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between gap-3">
          <JarvisLogo />
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar">
            <Menu size={22} />
          </Button>
        </div>

        <nav className="mt-6 grid gap-2 text-lg">
          <SidebarButton icon={<Bot size={24} />} label="New task" onClick={() => setTasks([])} active />
          <SidebarButton icon={<Search size={24} />} label="Search web" onClick={() => submitPrompt("search latest AI news")} />
          <SidebarButton icon={<Settings2 size={24} />} label="Settings" onClick={() => setNotice("Settings are managed through Supabase and backend environment variables.")} />
          <SidebarButton icon={<Terminal size={24} />} label="Terminal" onClick={() => submitPrompt("prepare a safe terminal workflow")} />
        </nav>

        <div className="mt-8 grid gap-3">
          <p className="px-3 text-sm font-black uppercase tracking-wide text-[#4e535a]">Tools</p>
          <SidebarButton icon={<Newspaper size={22} />} label="Daily briefing" onClick={() => submitPrompt("business news, sports news, and AI news today")} />
          <SidebarButton icon={<Code2 size={22} />} label="Code writer" onClick={() => submitPrompt("write production-ready React code")} />
          <SidebarButton icon={<History size={22} />} label="Agent tasks" onClick={() => setNotice("Task history is stored per user session.")} />
          <SidebarButton icon={<Shield size={22} />} label="Security" onClick={() => setNotice("High security mode is active. Sensitive actions require approval.")} />
        </div>

        <div className="mt-8 grid min-h-[180px] gap-3">
          <div className="flex items-center justify-between px-3">
            <p className="text-sm font-black uppercase tracking-wide text-[#4e535a]">History</p>
            <Button variant="ghost" size="icon" onClick={() => setTasks([])} aria-label="Clear history">
              <Trash2 size={18} />
            </Button>
          </div>
          <div className="grid gap-1">
            {tasks.length ? (
              tasks.map((task) => (
                <button
                  key={task.id}
                  className="truncate rounded-xl px-3 py-2 text-left text-sm text-[#45494f] hover:bg-[#f0f1f3]"
                  title={task.prompt}
                >
                  {task.prompt}
                </button>
              ))
            ) : (
              <p className="px-3 py-2 text-sm text-[#7d8188]">No tasks yet</p>
            )}
          </div>
        </div>

        <div className="mt-auto pt-6">
          <Separator className="mb-4" />
          <button
            className="flex w-full items-center gap-3 rounded-2xl bg-white p-3 text-left shadow-sm"
            onClick={signOut}
          >
            <span className="grid h-11 w-11 place-items-center rounded-full bg-[#0f9f7a] font-black text-white">
              {userEmail.slice(0, 2).toUpperCase()}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate font-black">{userEmail}</span>
              <span className="block text-sm text-[#6b7078]">Cloud workspace</span>
            </span>
            <LogOut size={19} />
          </button>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-[74px] shrink-0 items-center justify-between border-b border-[#dfe2e7] bg-white px-4 sm:px-8">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar">
              <Menu size={24} />
            </Button>
            <h1 className="text-3xl font-black tracking-normal">Jarvis</h1>
            <Badge>JS 1</Badge>
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

        <section className="jarvis-scroll min-h-0 flex-1 overflow-y-auto">
          <TaskStream tasks={tasks} onApprove={handleApprove} />
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
  onClick,
}: {
  icon: ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex min-h-14 items-center gap-4 rounded-2xl px-4 text-left font-semibold text-[#42464d] transition hover:bg-[#f0f1f3]",
        active && "bg-[#ededf2] text-[#111113]",
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
