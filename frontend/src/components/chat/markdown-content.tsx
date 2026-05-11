"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";

interface MarkdownContentProps {
  content: string;
  variant?: "assistant" | "user";
  className?: string;
}

export function MarkdownContent({
  content,
  variant = "assistant",
  className,
}: MarkdownContentProps) {
  return (
    <div
      className={cn(
        "max-w-none text-sm leading-relaxed [&_a]:break-words",
        variant === "assistant" &&
          [
            "prose prose-neutral prose-sm",
            "prose-headings:mb-2 prose-headings:mt-3 prose-headings:font-semibold prose-headings:text-foreground [&_h1:first-child]:mt-0 [&_h2:first-child]:mt-0 [&_h3:first-child]:mt-0",
            "prose-p:my-2 prose-p:text-foreground",
            "prose-li:my-0.5 prose-li:text-foreground",
            "prose-blockquote:border-l-muted-foreground prose-blockquote:text-muted-foreground",
            "prose-pre:bg-muted prose-pre:text-foreground prose-pre:rounded-md prose-pre:border prose-pre:border-border",
            "prose-code:rounded prose-code:bg-muted/90 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-foreground prose-code:before:content-none prose-code:after:content-none",
            "prose-table:text-foreground prose-th:border prose-td:border prose-th:border-border prose-td:border-border",
          ].join(" "),
        variant === "user" &&
          [
            "prose prose-sm prose-invert",
            "prose-headings:text-primary-foreground prose-p:text-primary-foreground",
            "prose-strong:text-primary-foreground prose-li:text-primary-foreground",
            "prose-blockquote:border-primary-foreground/40 prose-blockquote:text-primary-foreground/90",
            "prose-pre:bg-primary-foreground/10 prose-pre:text-primary-foreground prose-pre:rounded-md prose-pre:border prose-pre:border-primary-foreground/20",
            "prose-code:bg-primary-foreground/15 prose-code:text-primary-foreground prose-code:before:content-none prose-code:after:content-none",
          ].join(" "),
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
