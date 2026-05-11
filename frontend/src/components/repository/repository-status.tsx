"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Files,
  GitBranch,
  GitCommit,
  Loader2,
} from "lucide-react";
import type * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Repository, RepositoryStatus as Status } from "@/types/api";

interface RepositoryStatusProps {
  repository: Repository | null;
}

const statusVariant: Record<Status, "success" | "warning" | "destructive"> = {
  ready: "success",
  cloning: "warning",
  indexing: "warning",
  failed: "destructive",
};

export function RepositoryStatus({ repository }: RepositoryStatusProps) {
  if (!repository) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No repository selected.</p>
        </CardContent>
      </Card>
    );
  }

  const languages = Object.entries(repository.metadata.languages ?? {}).slice(0, 5);
  const commit = repository.commit_sha?.slice(0, 12) ?? "unknown";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="truncate">
            {repository.owner}/{repository.name}
          </CardTitle>
          <Badge variant={statusVariant[repository.status]}>
            {repository.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <Metric
            icon={<Files className="h-4 w-4" />}
            label="Files"
            value={repository.file_count.toLocaleString()}
          />
          <Metric
            icon={<Clock3 className="h-4 w-4" />}
            label="Lines"
            value={repository.line_count.toLocaleString()}
          />
          <Metric
            icon={<GitBranch className="h-4 w-4" />}
            label="Branch"
            value={repository.default_branch ?? "unknown"}
          />
          <Metric
            icon={<GitCommit className="h-4 w-4" />}
            label="Commit"
            value={commit}
          />
        </div>

        {languages.length ? (
          <>
            <Separator />
            <div className="space-y-2">
              {languages.map(([language, count]) => (
                <div
                  key={language}
                  className="flex items-center justify-between gap-3 text-sm"
                >
                  <span className="truncate text-muted-foreground">{language}</span>
                  <span className="font-medium">{count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </>
        ) : null}

        {repository.status === "failed" && repository.error_message ? (
          <div className="flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{repository.error_message}</span>
          </div>
        ) : null}

        {repository.status === "ready" ? (
          <div className="flex items-center gap-2 text-sm text-emerald-700">
            <CheckCircle2 className="h-4 w-4" />
            <span>Ready</span>
          </div>
        ) : null}
        {repository.status === "cloning" || repository.status === "indexing" ? (
          <div className="flex items-center gap-2 text-sm text-amber-700">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>{repository.status}</span>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0 rounded-md border bg-muted/40 p-3">
      <div className="mb-1 flex items-center gap-2 text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <div className="truncate font-medium">{value}</div>
    </div>
  );
}
