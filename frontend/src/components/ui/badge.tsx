import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "success" | "warning" | "danger";
};

const tones = {
  neutral: "border-[#dfe2e7] bg-white text-[#54575c]",
  success: "border-[#a6e5d7] bg-[#e9fbf6] text-[#08765a]",
  warning: "border-[#f0d09b] bg-[#fff7e6] text-[#9a650b]",
  danger: "border-[#efb5b5] bg-[#fff1f1] text-[#a01818]",
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-bold", tones[tone], className)}
      {...props}
    />
  );
}
