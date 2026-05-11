import { API_BASE_URL } from "@/services/api";
import type {
  AuditResult,
  ChatRequest,
  ChatStreamPhase,
  Citation,
} from "@/types/api";

export interface ChatStreamHandlers {
  onSession?: (data: { session_id: string }) => void;
  onStatus?: (data: { phase: ChatStreamPhase }) => void;
  onMessage?: (data: { content: string }) => void;
  onDone?: (data: {
    status: string;
    session_id: string;
    citations: Citation[];
    audit: AuditResult;
    reasoning_summary: string;
  }) => void;
  onError?: (data: { message: string; code?: string }) => void;
}

function parseSseBlock(block: string): { event: string; data: string } | null {
  const lines = block.replace(/\r\n/g, "\n").split("\n");
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }
  if (!dataLines.length) {
    return null;
  }
  return { event, data: dataLines.join("\n") };
}

function extractCompleteBlocks(buffer: string): { blocks: string[]; rest: string } {
  const normalized = buffer.replace(/\r\n/g, "\n");
  const parts = normalized.split("\n\n");
  const rest = parts.pop() ?? "";
  const blocks = parts.filter((p) => p.trim().length > 0);
  return { blocks, rest };
}

function dispatchEvent(
  event: string,
  rawData: string,
  handlers: ChatStreamHandlers,
): boolean {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawData) as unknown;
  } catch {
    handlers.onError?.({
      message: "Malformed server event.",
      code: "sse_parse_error",
    });
    return true;
  }

  if (event === "session" && parsed && typeof parsed === "object") {
    const sid = (parsed as { session_id?: unknown }).session_id;
    if (typeof sid === "string") {
      handlers.onSession?.({ session_id: sid });
    }
    return false;
  }

  if (event === "status" && parsed && typeof parsed === "object") {
    const phase = (parsed as { phase?: unknown }).phase;
    if (phase === "searching" || phase === "answering") {
      handlers.onStatus?.({ phase });
    }
    return false;
  }

  if (event === "message" && parsed && typeof parsed === "object") {
    const content = (parsed as { content?: unknown }).content;
    if (typeof content === "string" && content.length > 0) {
      handlers.onMessage?.({ content });
    }
    return false;
  }

  if (event === "done" && parsed && typeof parsed === "object") {
    const o = parsed as Record<string, unknown>;
    const status = o.status;
    const session_id = o.session_id;
    const citations = o.citations;
    const audit = o.audit;
    const reasoning_summary = o.reasoning_summary;
    if (
      typeof status === "string" &&
      typeof session_id === "string" &&
      Array.isArray(citations) &&
      audit &&
      typeof audit === "object" &&
      typeof reasoning_summary === "string"
    ) {
      handlers.onDone?.({
        status,
        session_id,
        citations: citations as Citation[],
        audit: audit as AuditResult,
        reasoning_summary,
      });
    }
    return true;
  }

  if (event === "error" && parsed && typeof parsed === "object") {
    const message = (parsed as { message?: unknown }).message;
    const code = (parsed as { code?: unknown }).code;
    handlers.onError?.({
      message: typeof message === "string" ? message : "Stream error.",
      code: typeof code === "string" ? code : undefined,
    });
    return true;
  }

  return false;
}

/**
 * POST /chat/stream and consume SSE until `done` or `error`, or body ends.
 */
export async function streamInvestigation(
  payload: ChatRequest,
  handlers: ChatStreamHandlers,
  init?: RequestInit,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...init?.headers,
    },
    body: JSON.stringify(payload),
    cache: "no-store",
    ...init,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    const text = await response.text();
    if (text) {
      try {
        const body = JSON.parse(text) as { error?: { message?: string } };
        const m = body?.error?.message;
        if (typeof m === "string") {
          message = m;
        }
      } catch {
        message = text.slice(0, 200);
      }
    }
    throw new Error(message);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body.");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;

  const processBuffer = (): void => {
    const { blocks, rest } = extractCompleteBlocks(buffer);
    buffer = rest;
    for (const block of blocks) {
      const parsed = parseSseBlock(block);
      if (!parsed) {
        continue;
      }
      const stop = dispatchEvent(parsed.event, parsed.data, handlers);
      if (stop) {
        finished = true;
        return;
      }
    }
  };

  while (!finished) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    processBuffer();
    if (finished) {
      await reader.cancel().catch(() => undefined);
      break;
    }
  }
  buffer += decoder.decode();
  processBuffer();

  if (!finished) {
    handlers.onError?.({
      message: "Stream ended unexpectedly.",
      code: "sse_incomplete",
    });
  }
}
