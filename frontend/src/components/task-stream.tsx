"use client";

import { ExternalLink, Loader2 } from "lucide-react";

import { ApprovalCard } from "@/components/approval-card";
import { Badge } from "@/components/ui/badge";
import type { TaskRecord } from "@/lib/api";

type TaskStreamProps = {
  tasks: TaskRecord[];
  onApprove: (taskId: string, approved: boolean) => void;
  onPrompt: (prompt: string) => void;
};

export function TaskStream({ tasks, onApprove, onPrompt }: TaskStreamProps) {
  if (!tasks.length) {
    return (
      <div className="mx-auto grid max-w-4xl gap-5 px-4 py-10 text-center">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-[#07080a] text-3xl font-black text-white">J</div>
        <div>
          <h1 className="text-3xl font-black tracking-normal sm:text-4xl">How can I help?</h1>
          <p className="mx-auto mt-3 max-w-2xl text-base leading-7 text-[#5c6067]">
            Ask naturally. Jarvis can answer questions, search live information, write code, create browser sessions,
            draft messages, and plan deployments with approval.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {["Search latest AI news", "Write a React dashboard", "Read a GitHub repo", "Create a deployment plan"].map((item) => (
            <button
              key={item}
              onClick={() => onPrompt(item)}
              className="rounded-2xl border border-[#dfe2e7] bg-white p-4 text-left font-semibold transition hover:border-[#0f9f7a] hover:bg-[#f6fffb]"
            >
              {item}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto grid w-full max-w-4xl gap-8 px-4 py-8">
      {tasks.map((task) => (
        <article key={task.id} className="grid gap-4">
          <div className="justify-self-end rounded-3xl bg-[#f0f1f3] px-5 py-3 text-lg">{task.prompt}</div>
          <div className="grid grid-cols-[44px_1fr] gap-4">
            <div className="grid h-11 w-11 place-items-center rounded-full bg-[#07080a] font-black text-white">J</div>
            <div className="grid gap-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={task.status === "failed" ? "danger" : task.status === "completed" ? "success" : "neutral"}>
                  {task.status.replace("_", " ")}
                </Badge>
                <Badge tone={task.plan.risk === "high" || task.plan.risk === "critical" ? "danger" : "neutral"}>
                  {task.plan.intent}
                </Badge>
              </div>

              {task.status === "waiting_approval" ? (
                <ApprovalCard task={task} onApprove={(approved) => onApprove(task.id, approved)} />
              ) : null}

              {task.status === "queued" || task.status === "running" ? (
                <div className="flex items-center gap-3 rounded-2xl border border-[#dfe2e7] bg-white p-4 text-[#5c6067]">
                  <Loader2 className="animate-spin" size={19} />
                  Jarvis is working through the plan.
                </div>
              ) : null}

              {task.error ? <div className="rounded-2xl bg-[#fff1f1] p-4 font-semibold text-[#a01818]">{task.error}</div> : null}

              {task.result?.answer ? (
                <section className="grid gap-4 rounded-2xl border border-[#dfe2e7] bg-white p-5 leading-8 shadow-sm">
                  <div className="whitespace-pre-wrap text-[17px]">{task.result.answer}</div>
                  {task.result.sources?.length ? (
                    <div className="grid gap-2 border-t border-[#dfe2e7] pt-4">
                      <div className="text-sm font-black uppercase tracking-wide text-[#5c6067]">Sources</div>
                      {task.result.sources.map((source) => (
                        <a
                          key={source.url}
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-2 text-sm font-semibold text-[#08765a] hover:underline"
                        >
                          <ExternalLink size={16} />
                          {source.title || source.url}
                        </a>
                      ))}
                    </div>
                  ) : null}
                  {task.result.technical_details && Object.keys(task.result.technical_details).length ? (
                    <details className="rounded-xl bg-[#f7f8fa] p-3 text-sm">
                      <summary className="cursor-pointer font-bold">Technical details</summary>
                      <pre className="mt-3 overflow-auto whitespace-pre-wrap font-mono text-xs">
                        {JSON.stringify(task.result.technical_details, null, 2)}
                      </pre>
                    </details>
                  ) : null}
                </section>
              ) : null}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
