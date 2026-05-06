"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { Shield } from "lucide-react";

import { JarvisLogo } from "@/components/jarvis-logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

type AuthGateProps = {
  children: (session: Session | null) => ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const supabase = getSupabaseBrowserClient();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(Boolean(supabase));
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState("");
  const [demo, setDemo] = useState(false);

  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });
    return () => data.subscription.unsubscribe();
  }, [supabase]);

  async function submit() {
    if (!supabase) {
      setNotice("Supabase public env values are missing.");
      return;
    }
    setNotice("");
    const result =
      mode === "login"
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password });
    if (result.error) {
      setNotice(result.error.message);
      return;
    }
    if (mode === "signup") {
      setNotice("Account created. Check email confirmation if Supabase requires it.");
    }
  }

  async function loginWithGoogle() {
    if (!supabase) {
      setNotice("Supabase public env values are missing.");
      return;
    }
    const redirectTo = typeof window !== "undefined" ? window.location.origin : undefined;
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo },
    });
    if (error) setNotice(error.message);
  }

  if (loading) {
    return <div className="grid min-h-screen place-items-center text-lg font-semibold">Loading Jarvis...</div>;
  }

  if (session || demo) {
    return children(session);
  }

  return (
    <main
      className="min-h-screen overflow-y-auto px-4 py-10"
      style={{ background: "radial-gradient(circle at 50% 0%, #e8fbf5, transparent 36%), #f7f8fa" }}
    >
      <section className="mx-auto grid w-full max-w-[720px] gap-8 rounded-[28px] border border-[#dfe2e7] bg-white p-6 shadow-2xl shadow-[#0b5b4717] sm:p-10">
        <div className="flex items-center justify-between gap-4">
          <JarvisLogo />
          <span className="inline-flex items-center gap-2 rounded-full border border-[#a6e5d7] bg-[#e9fbf6] px-4 py-2 text-sm font-bold text-[#08765a]">
            <Shield size={18} />
            Secure access
          </span>
        </div>

        <div>
          <h1 className="text-4xl font-black tracking-normal sm:text-5xl">Sign in to Jarvis</h1>
          <p className="mt-4 max-w-xl text-lg leading-8 text-[#5c6067]">
            Use the Vercel web agent, keep approvals inside Jarvis, and connect cloud workers for browser automation.
          </p>
        </div>

        <div className="grid gap-4">
          <div className="grid grid-cols-2 rounded-2xl bg-[#f0f1f3] p-1">
            <Button variant={mode === "login" ? "outline" : "ghost"} onClick={() => setMode("login")}>
              Log in
            </Button>
            <Button variant={mode === "signup" ? "outline" : "ghost"} onClick={() => setMode("signup")}>
              Sign up
            </Button>
          </div>

          <label className="grid gap-2 font-bold">
            Email
            <Input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" />
          </label>
          <label className="grid gap-2 font-bold">
            Password
            <Input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              placeholder="At least 6 characters"
            />
          </label>

          <Button className="h-14 text-lg" onClick={submit}>
            {mode === "login" ? "Log in" : "Create account"}
          </Button>

          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 text-sm font-bold text-[#6b7078]">
            <div className="h-px bg-[#dfe2e7]" />
            or
            <div className="h-px bg-[#dfe2e7]" />
          </div>

          <Button variant="outline" className="h-14 text-base" onClick={loginWithGoogle}>
            Continue with Google
          </Button>

          {!supabase ? (
            <Button variant="secondary" className="h-12" onClick={() => setDemo(true)}>
              Continue in local demo mode
            </Button>
          ) : null}

          {notice ? <p className="rounded-xl bg-[#fff7e6] p-3 text-sm font-semibold text-[#805200]">{notice}</p> : null}
        </div>
      </section>
    </main>
  );
}
