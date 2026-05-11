"use client";

import * as React from "react";
import { Github, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface RepositoryFormProps {
  isPending: boolean;
  errorMessage?: string | null;
  onSubmit: (url: string) => Promise<void>;
}

export function RepositoryForm({
  isPending,
  errorMessage,
  onSubmit,
}: RepositoryFormProps) {
  const [url, setUrl] = React.useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!url.trim()) {
      return;
    }
    await onSubmit(url.trim());
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Repository</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div className="flex gap-2">
            <Input
              aria-label="GitHub repository URL"
              placeholder="https://github.com/org/repo"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              disabled={isPending}
            />
            <Button type="submit" size="icon" disabled={isPending || !url.trim()}>
              {isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Github className="h-4 w-4" aria-hidden="true" />
              )}
              <span className="sr-only">Submit repository</span>
            </Button>
          </div>
          {errorMessage ? (
            <p className="text-sm text-destructive">{errorMessage}</p>
          ) : null}
        </form>
      </CardContent>
    </Card>
  );
}

