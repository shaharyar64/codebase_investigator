"use client";

import * as React from "react";
import { SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  disabled: boolean;
  isPending: boolean;
  onSubmit: (question: string) => Promise<void>;
}

export function ChatInput({ disabled, isPending, onSubmit }: ChatInputProps) {
  const [question, setQuestion] = React.useState("");
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const canSend = !disabled && !isPending && question.trim().length > 0;

  async function sendQuestion() {
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    await onSubmit(trimmed);
    setQuestion("");
    textareaRef.current?.focus();
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSend) {
      return;
    }
    await sendQuestion();
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter") {
      return;
    }
    if (event.shiftKey) {
      return;
    }
    if (event.nativeEvent.isComposing) {
      return;
    }
    event.preventDefault();
    if (!canSend) {
      return;
    }
    void sendQuestion();
  }

  return (
    <form className="border-t bg-card px-4 py-3" onSubmit={handleSubmit}>
      <label htmlFor="investigation-question" className="sr-only">
        Question
      </label>
      <div
        className={cn(
          "flex gap-1.5 rounded-2xl border bg-background p-1.5 shadow-sm transition-shadow",
          "focus-within:border-ring/60 focus-within:ring-2 focus-within:ring-ring/25",
          (disabled || isPending) && "opacity-60",
        )}
      >
        <Textarea
          id="investigation-question"
          ref={textareaRef}
          aria-label="Question"
          placeholder="Ask about auth, routes, dead code, async flows…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isPending}
          rows={1}
          className={cn(
            "min-h-[44px] max-h-[min(40vh,12rem)] flex-1 resize-none border-0 bg-transparent px-2.5 py-2.5 text-sm leading-snug shadow-none",
            "placeholder:text-muted-foreground/80",
            "focus-visible:outline-none focus-visible:ring-0",
          )}
        />
        <div className="flex shrink-0 flex-col justify-end pb-0.5 pr-0.5">
          <Button
            type="submit"
            size="icon"
            disabled={!canSend}
            className="h-10 w-10 shrink-0 rounded-xl"
            aria-label="Send question"
          >
            <SendHorizontal className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground sm:text-left">
        <kbd className="rounded border border-border bg-muted/80 px-1 py-px font-mono text-[10px]">
          Enter
        </kbd>{" "}
        to send ·{" "}
        <kbd className="rounded border border-border bg-muted/80 px-1 py-px font-mono text-[10px]">
          Shift
        </kbd>
        +
        <kbd className="rounded border border-border bg-muted/80 px-1 py-px font-mono text-[10px]">
          Enter
        </kbd>{" "}
        new line
      </p>
    </form>
  );
}
