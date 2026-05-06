import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-12 w-full rounded-xl border border-[#dfe2e7] bg-white px-4 text-base outline-none transition placeholder:text-[#7d8188] focus:border-[#0f9f7a] focus:ring-4 focus:ring-[#0f9f7a]/10",
        className,
      )}
      {...props}
    />
  );
}
