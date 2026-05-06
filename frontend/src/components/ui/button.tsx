import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "ghost" | "outline" | "danger";
  size?: "default" | "sm" | "icon";
};

const variants = {
  default: "bg-[#0f9f7a] text-white hover:bg-[#0c8768]",
  secondary: "bg-[#f0f1f3] text-[#111113] hover:bg-[#e5e7eb]",
  ghost: "bg-transparent text-[#111113] hover:bg-[#f0f1f3]",
  outline: "border border-[#dfe2e7] bg-white text-[#111113] hover:bg-[#f7f8fa]",
  danger: "bg-[#c92323] text-white hover:bg-[#aa1d1d]",
};

const sizes = {
  default: "h-11 px-4 text-sm",
  sm: "h-9 px-3 text-sm",
  icon: "h-10 w-10 p-0",
};

export function Button({ className, variant = "default", size = "default", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0f9f7a] disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  );
}
