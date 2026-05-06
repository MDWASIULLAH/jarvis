"use client";

import { FormEvent, useState } from "react";
import { ArrowUp, Mic, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type TaskComposerProps = {
  disabled?: boolean;
  onSubmit: (prompt: string) => Promise<void>;
};

export function TaskComposer({ disabled, onSubmit }: TaskComposerProps) {
  const [prompt, setPrompt] = useState("");
  const [sending, setSending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value || sending) return;
    setSending(true);
    try {
      await onSubmit(value);
      setPrompt("");
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto w-full max-w-4xl px-4 pb-5">
      <div className="flex items-end gap-2 rounded-[28px] border border-[#dfe2e7] bg-white p-2 shadow-2xl shadow-[#11111312]">
        <Button type="button" variant="ghost" size="icon" aria-label="Open tools">
          <Plus size={22} />
        </Button>
        <Textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
          placeholder="Ask Jarvis to search, code, automate, read, draft, deploy..."
          className="max-h-40 min-h-12 border-0 px-2 py-3 shadow-none focus:ring-0"
          disabled={disabled || sending}
        />
        <Button type="button" variant="ghost" size="icon" aria-label="Voice control">
          <Mic size={21} />
        </Button>
        <Button type="submit" size="icon" disabled={disabled || sending || !prompt.trim()} aria-label="Send">
          <ArrowUp size={21} />
        </Button>
      </div>
      <p className="mt-2 text-center text-xs text-[#7d8188]">
        Jarvis asks before sending, deploying, editing files, or running automation.
      </p>
    </form>
  );
}
