"use client";

import { AlertTriangle, Check, Shield, X } from "lucide-react";

import type { TaskRecord } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type ApprovalCardProps = {
  task: TaskRecord;
  onApprove: (approved: boolean) => void;
};

export function ApprovalCard({ task, onApprove }: ApprovalCardProps) {
  const tone = task.plan.risk === "critical" || task.plan.risk === "high" ? "danger" : "warning";

  return (
    <section className="grid gap-4 rounded-2xl border border-[#dfe2e7] bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-[#08765a]">
            <Shield size={18} />
            Approval required
          </div>
          <h3 className="mt-2 text-xl font-black tracking-normal">{task.plan.summary}</h3>
        </div>
        <Badge tone={tone}>{task.plan.risk} risk</Badge>
      </div>

      <div className="grid gap-2">
        {task.plan.steps.map((step, index) => (
          <div key={step} className="flex gap-3 rounded-xl bg-[#f7f8fa] p-3 text-sm">
            <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white font-black">{index + 1}</span>
            <span className="leading-6">{step}</span>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-[#f0d09b] bg-[#fff7e6] p-3 text-sm leading-6 text-[#6e4a00]">
        <div className="flex items-center gap-2 font-bold">
          <AlertTriangle size={17} />
          Jarvis will not execute this action until you approve it.
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button onClick={() => onApprove(true)}>
          <Check size={18} />
          Approve
        </Button>
        <Button variant="outline" onClick={() => onApprove(false)}>
          <X size={18} />
          Cancel
        </Button>
      </div>
    </section>
  );
}
