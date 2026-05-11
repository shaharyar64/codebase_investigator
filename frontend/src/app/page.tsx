"use client";

import * as React from "react";
import { BrainCircuit } from "lucide-react";

import { ChatPanel } from "@/components/chat/chat-panel";
import { RepositoryForm } from "@/components/repository/repository-form";
import { RepositoryStatus } from "@/components/repository/repository-status";
import { useAskQuestion, useSubmitRepository } from "@/hooks/use-investigator-api";
import { getErrorMessage } from "@/lib/errors";
import type { ChatMessage, Repository } from "@/types/api";

export default function Home() {
  const [repository, setRepository] = React.useState<Repository | null>(null);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [repositoryError, setRepositoryError] = React.useState<string | null>(null);
  const [chatError, setChatError] = React.useState<string | null>(null);

  const submitRepository = useSubmitRepository();
  const askQuestion = useAskQuestion();

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
    setChatError(null);
    setMessages((current) => [...current, userMessage]);

    try {
      const response = await askQuestion.mutateAsync({
        repository_id: repository.id,
        question,
        session_id: sessionId,
      });
      setSessionId(response.session_id);
      setMessages((current) => [
        ...current,
        {
          id: createId(),
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          audit: response.audit,
          reasoning_summary: response.reasoning_summary,
        },
      ]);
    } catch (error) {
      setChatError(getErrorMessage(error));
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
              isPending={askQuestion.isPending}
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

