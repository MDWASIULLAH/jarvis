import * as React from "react";

import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-16 w-full resize-none rounded-2xl border border-[#dfe2e7] bg-white px-4 py-3 text-base outline-none transition placeholder:text-[#7d8188] focus:border-[#0f9f7a] focus:ring-4 focus:ring-[#0f9f7a]/10",
        className,
      )}
      {...props}
    />
  );
}
