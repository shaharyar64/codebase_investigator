"use client";

import * as React from "react";
import { BrainCircuit } from "lucide-react";

import { ChatPanel } from "@/components/chat/chat-panel";
import { RepositoryForm } from "@/components/repository/repository-form";
import { RepositoryStatus } from "@/components/repository/repository-status";
import { useChatStreamAbort } from "@/hooks/use-chat-stream";
import { useSubmitRepository } from "@/hooks/use-investigator-api";
import { getErrorMessage } from "@/lib/errors";
import { streamInvestigation } from "@/services/chat-stream";
import type { ChatMessage, Repository } from "@/types/api";

export default function Home() {
  const [repository, setRepository] = React.useState<Repository | null>(null);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [repositoryError, setRepositoryError] = React.useState<string | null>(null);
  const [chatError, setChatError] = React.useState<string | null>(null);

  const submitRepository = useSubmitRepository();
  const { refreshController } = useChatStreamAbort();
  const [isChatStreaming, setIsChatStreaming] = React.useState(false);

  async function handleRepositorySubmit(url: string) {
    setRepositoryError(null);
    setChatError(null);
    try {
      const nextRepository = await submitRepository.mutateAsync(url);
      setRepository(nextRepository);
      setSessionId(null);
      setMessages([]);
    } catch (error) {
      setRepositoryError(getErrorMessage(error));
    }
  }

  async function handleAsk(question: string) {
    if (!repository) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: question,
      citations: [],
    };
    const assistantId = createId();
    const assistantPlaceholder: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      citations: [],
      isStreaming: true,
      streamPhase: "searching",
    };
    setChatError(null);
    setMessages((current) => [...current, userMessage, assistantPlaceholder]);

    const controller = refreshController();
    setIsChatStreaming(true);

    const patchAssistant = (fn: (m: ChatMessage) => ChatMessage) => {
      setMessages((current) =>
        current.map((m) => (m.id === assistantId ? fn(m) : m)),
      );
    };

    try {
      await streamInvestigation(
        {
          repository_id: repository.id,
          question,
          session_id: sessionId,
        },
        {
          onSession: (data) => {
            setSessionId(data.session_id);
          },
          onStatus: (data) => {
            if (data.phase === "answering") {
              patchAssistant((m) => ({
                ...m,
                streamPhase: "answering",
              }));
            }
          },
          onMessage: (data) => {
            patchAssistant((m) => ({
              ...m,
              content: m.content + data.content,
              streamPhase: undefined,
            }));
          },
          onDone: (data) => {
            setSessionId(data.session_id);
            patchAssistant((m) => ({
              ...m,
              citations: data.citations,
              audit: data.audit,
              reasoning_summary: data.reasoning_summary,
              isStreaming: false,
              streamPhase: undefined,
            }));
          },
          onError: (data) => {
            setChatError(data.message);
            patchAssistant((m) => ({
              ...m,
              isStreaming: false,
              streamPhase: undefined,
            }));
          },
        },
        { signal: controller.signal },
      );
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        patchAssistant((m) => ({
          ...m,
          isStreaming: false,
          streamPhase: undefined,
        }));
      } else {
        setChatError(getErrorMessage(error));
        patchAssistant((m) => ({
          ...m,
          isStreaming: false,
          streamPhase: undefined,
        }));
      }
    } finally {
      setIsChatStreaming(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-1 min-h-0 flex-col gap-4 p-4 lg:p-6">
        <header className="flex items-center justify-between gap-4 rounded-lg border bg-card px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <BrainCircuit className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-base font-semibold">
                AI Codebase Investigator
              </h1>
              <p className="truncate text-sm text-muted-foreground">
                {sessionId ? `Session ${sessionId.slice(0, 8)}` : "No active session"}
              </p>
            </div>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[360px_minmax(0,1fr)] lg:items-stretch">
          <aside className="space-y-4 lg:min-h-0">
            <RepositoryForm
              isPending={submitRepository.isPending}
              errorMessage={repositoryError}
              onSubmit={handleRepositorySubmit}
            />
            <RepositoryStatus repository={repository} />
          </aside>
          <div className="flex min-h-0 min-w-0 flex-col">
            <ChatPanel
              className="flex-1"
              repository={repository}
              messages={messages}
              isPending={isChatStreaming}
              errorMessage={chatError}
              onAsk={handleAsk}
            />
          </div>
        </div>
      </div>
    </main>
  );
}

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

