"use client";

import * as React from "react";
import { SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  disabled: boolean;
  isPending: boolean;
  onSubmit: (question: string) => Promise<void>;
}

export function ChatInput({ disabled, isPending, onSubmit }: ChatInputProps) {
  const [question, setQuestion] = React.useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    await onSubmit(trimmed);
    setQuestion("");
  }

  return (
    <form className="border-t bg-card p-4" onSubmit={handleSubmit}>
      <div className="flex items-end gap-2">
        <Textarea
          aria-label="Question"
          placeholder="Ask about auth, routes, dead code, async flows..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={disabled || isPending}
          className="min-h-20"
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || isPending || !question.trim()}
        >
          <SendHorizontal className="h-4 w-4" aria-hidden="true" />
          <span className="sr-only">Send</span>
        </Button>
      </div>
    </form>
  );
}

