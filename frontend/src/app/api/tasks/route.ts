import { NextRequest, NextResponse } from "next/server";

import { createJarvisTask } from "@/lib/server/jarvis-task-engine";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const prompt = String(body.prompt ?? "").trim();
    if (!prompt) {
      return NextResponse.json({ error: "Prompt is required." }, { status: 400 });
    }
    const task = await createJarvisTask(prompt, body.user_id ?? null);
    return NextResponse.json(task);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Jarvis task failed." },
      { status: 500 },
    );
  }
}
