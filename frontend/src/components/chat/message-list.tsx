"use client";

import { Bot, User } from "lucide-react";
import type * as React from "react";

import { AuditPanel } from "@/components/audit/audit-panel";
import { CitationList } from "@/components/chat/citation-list";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage } from "@/types/api";
import { cn } from "@/lib/utils";

interface MessageListProps {
  messages: ChatMessage[];
  isThinking: boolean;
}

export function MessageList({ messages, isThinking }: MessageListProps) {
  return (
    <ScrollArea className="h-full">
      <div className="space-y-4 p-4">
        {!messages.length ? (
          <div className="flex h-[420px] items-center justify-center text-sm text-muted-foreground">
            Select a repository to start.
          </div>
        ) : null}
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3",
              message.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            {message.role === "assistant" ? (
              <Avatar icon={<Bot className="h-4 w-4" />} />
            ) : null}
            <div
              className={cn(
                "max-w-[78%] space-y-3 rounded-lg border p-4 text-sm leading-6",
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card",
              )}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.reasoning_summary ? (
                <p className="border-l-2 pl-3 text-xs text-muted-foreground">
                  {message.reasoning_summary}
                </p>
              ) : null}
              <CitationList citations={message.citations} />
              {message.audit ? <AuditPanel audit={message.audit} /> : null}
            </div>
            {message.role === "user" ? (
              <Avatar icon={<User className="h-4 w-4" />} />
            ) : null}
          </div>
        ))}
        {isThinking ? (
          <div className="flex gap-3">
            <Avatar icon={<Bot className="h-4 w-4" />} />
            <div className="rounded-lg border bg-card p-4 text-sm text-muted-foreground">
              Investigating...
            </div>
          </div>
        ) : null}
      </div>
    </ScrollArea>
  );
}

function Avatar({ icon }: { icon: React.ReactNode }) {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border bg-background text-muted-foreground">
      {icon}
    </div>
  );
}
