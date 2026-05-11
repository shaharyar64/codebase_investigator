"use client";

import { MessageSquareText } from "lucide-react";

import { ChatInput } from "@/components/chat/chat-input";
import { MessageList } from "@/components/chat/message-list";
import { Card } from "@/components/ui/card";
import type { ChatMessage, Repository } from "@/types/api";

interface ChatPanelProps {
  repository: Repository | null;
  messages: ChatMessage[];
  isPending: boolean;
  errorMessage?: string | null;
  onAsk: (question: string) => Promise<void>;
}

export function ChatPanel({
  repository,
  messages,
  isPending,
  errorMessage,
  onAsk,
}: ChatPanelProps) {
  const disabled = !repository || repository.status !== "ready";

  return (
    <Card className="flex min-h-[720px] flex-1 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex min-w-0 items-center gap-2">
          <MessageSquareText className="h-5 w-5 shrink-0 text-muted-foreground" />
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold">Investigation</h2>
            <p className="truncate text-xs text-muted-foreground">
              {repository ? `${repository.owner}/${repository.name}` : "Idle"}
            </p>
          </div>
        </div>
        {errorMessage ? (
          <p className="max-w-[50%] truncate text-sm text-destructive">
            {errorMessage}
          </p>
        ) : null}
      </div>
      <div className="min-h-0 flex-1">
        <MessageList messages={messages} isThinking={isPending} />
      </div>
      <ChatInput disabled={disabled} isPending={isPending} onSubmit={onAsk} />
    </Card>
  );
}

