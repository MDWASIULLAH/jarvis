import { NextResponse } from "next/server";

import { approveJarvisTask, approveJarvisTaskSnapshot } from "@/lib/server/jarvis-task-engine";

export const runtime = "nodejs";

export async function POST(request: Request, { params }: { params: Promise<{ taskId: string }> }) {
  const { taskId } = await params;
  const body = await request.json().catch(() => ({ approved: true }));
  const task =
    (await approveJarvisTask(taskId, body.approved !== false)) ??
    (body.task ? await approveJarvisTaskSnapshot(body.task, body.approved !== false) : null);
  if (!task) {
    return NextResponse.json({ error: "Task not found." }, { status: 404 });
  }
  return NextResponse.json(task);
}
