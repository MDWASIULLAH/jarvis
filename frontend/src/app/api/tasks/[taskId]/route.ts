import { NextResponse } from "next/server";

import { getJarvisTask } from "@/lib/server/jarvis-task-engine";

export const runtime = "nodejs";

export async function GET(_request: Request, { params }: { params: Promise<{ taskId: string }> }) {
  const { taskId } = await params;
  const task = getJarvisTask(taskId);
  if (!task) {
    return NextResponse.json({ error: "Task not found." }, { status: 404 });
  }
  return NextResponse.json(task);
}
