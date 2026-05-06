import { cn } from "@/lib/utils";

export function JarvisLogo({ className }: { className?: string }) {
  return (
    <div className={cn("relative grid h-12 w-12 place-items-center rounded-full bg-[#07080a] shadow-lg", className)}>
      <div
        className="absolute inset-0 rounded-full p-[3px]"
        style={{ background: "conic-gradient(from 130deg, #0f9f7a, #35bdf4, #07080a, #0f9f7a)" }}
      >
        <div className="h-full w-full rounded-full bg-[#07080a]" />
      </div>
      <div className="absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full bg-[#0f9f7a] ring-4 ring-[#dff7f0]" />
      <span className="relative text-xl font-black tracking-normal text-white">J</span>
    </div>
  );
}
