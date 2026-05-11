"use client";

import { FileCode2 } from "lucide-react";

import type { Citation } from "@/types/api";

interface CitationListProps {
  citations: Citation[];
}

export function CitationList({ citations }: CitationListProps) {
  if (!citations.length) {
    return null;
  }

  return (
    <div className="space-y-2">
      {citations.map((citation) => (
        <div
          key={`${citation.file}:${citation.start_line}-${citation.end_line}`}
          className="rounded-md border bg-background p-3"
        >
          <div className="mb-2 flex min-w-0 items-center gap-2 text-sm">
            <FileCode2 className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="truncate font-medium">{citation.file}</span>
            <span className="shrink-0 text-muted-foreground">
              {citation.start_line}-{citation.end_line}
            </span>
          </div>
          {citation.excerpt ? (
            <pre className="max-h-48 overflow-auto rounded-sm bg-muted p-3 text-xs leading-5 text-foreground">
              <code>{citation.excerpt}</code>
            </pre>
          ) : null}
        </div>
      ))}
    </div>
  );
}

