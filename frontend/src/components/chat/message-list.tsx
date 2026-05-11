"use client";

import { Bot, User } from "lucide-react";
import * as React from "react";

import { AuditPanel } from "@/components/audit/audit-panel";
import { CitationList } from "@/components/chat/citation-list";
import { MarkdownContent } from "@/components/chat/markdown-content";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage } from "@/types/api";
import { cn } from "@/lib/utils";

interface MessageListProps {
  messages: ChatMessage[];
  isThinking: boolean;
}

export function MessageList({ messages, isThinking }: MessageListProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    el.scrollTop = el.scrollHeight;
  }, [messages]);

  const showDetachedTyping =
    isThinking &&
    !messages.some((m) => m.role === "assistant" && m.isStreaming);

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
      <ScrollArea
        ref={scrollRef}
        className="min-h-0 flex-1 basis-0 overflow-y-auto"
      >
        <div className="space-y-4 p-4 pb-2">
        {!messages.length ? (
          <div className="flex min-h-[min(40vh,20rem)] items-center justify-center py-12 text-center text-sm text-muted-foreground">
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
              {message.role === "assistant" &&
              message.isStreaming &&
              !message.content ? (
                <p className="text-sm text-muted-foreground">
                  {message.streamPhase === "answering"
                    ? "Drafting the answer…"
                    : "Searching the repository…"}
                </p>
              ) : (
                <div className="inline-block max-w-full">
                  <MarkdownContent
                    content={message.content}
                    variant={message.role === "user" ? "user" : "assistant"}
                  />
                  {message.role === "assistant" &&
                  message.isStreaming &&
                  message.content ? (
                    <span
                      className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-primary align-middle"
                      aria-hidden
                    />
                  ) : null}
                </div>
              )}
              {message.reasoning_summary ? (
                <div className="border-l-2 border-muted-foreground/40 pl-3">
                  <MarkdownContent
                    content={message.reasoning_summary}
                    variant="assistant"
                    className="text-xs text-muted-foreground prose-p:my-1 prose-headings:my-2"
                  />
                </div>
              ) : null}
              {!message.isStreaming ? (
                <>
                  <CitationList citations={message.citations} />
                  {message.audit ? <AuditPanel audit={message.audit} /> : null}
                </>
              ) : null}
            </div>
            {message.role === "user" ? (
              <Avatar icon={<User className="h-4 w-4" />} />
            ) : null}
          </div>
        ))}
        {showDetachedTyping ? (
          <div className="flex gap-3">
            <Avatar icon={<Bot className="h-4 w-4" />} />
            <div className="rounded-lg border bg-card p-4 text-sm text-muted-foreground">
              Investigating...
            </div>
          </div>
        ) : null}
        </div>
      </ScrollArea>
    </div>
  );
}

function Avatar({ icon }: { icon: React.ReactNode }) {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border bg-background text-muted-foreground">
      {icon}
    </div>
  );
}
