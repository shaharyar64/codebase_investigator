"use client";

import { MessageSquareText } from "lucide-react";

import { ChatInput } from "@/components/chat/chat-input";
import { MessageList } from "@/components/chat/message-list";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ChatMessage, Repository } from "@/types/api";

interface ChatPanelProps {
  repository: Repository | null;
  messages: ChatMessage[];
  isPending: boolean;
  errorMessage?: string | null;
  onAsk: (question: string) => Promise<void>;
  className?: string;
}

export function ChatPanel({
  repository,
  messages,
  isPending,
  errorMessage,
  onAsk,
  className,
}: ChatPanelProps) {
  const disabled = !repository || repository.status !== "ready";

  return (
    <Card
      className={cn(
        "flex h-full min-h-0 flex-1 flex-col overflow-hidden min-h-[28rem] lg:min-h-[calc(100vh-7.5rem)]",
        className,
      )}
    >
      <div className="flex shrink-0 items-center justify-between border-b p-4">
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
      <div className="flex min-h-0 flex-1 flex-col">
        <MessageList messages={messages} isThinking={isPending} />
      </div>
      <div className="shrink-0">
        <ChatInput disabled={disabled} isPending={isPending} onSubmit={onAsk} />
      </div>
    </Card>
  );
}

