import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET() {
  return NextResponse.json({
    ok: true,
    name: "Jarvis Vercel Core",
    mode: "built-in serverless fallback",
  });
}
