"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import {
  askQuestion,
  getRepository,
  getSession,
  submitRepository,
} from "@/services/api";
import type { ChatRequest } from "@/types/api";

export function useSubmitRepository() {
  return useMutation({
    mutationFn: (url: string) => submitRepository(url),
  });
}

export function useAskQuestion() {
  return useMutation({
    mutationFn: (payload: ChatRequest) => askQuestion(payload),
  });
}

export function useRepository(repositoryId: string | null) {
  return useQuery({
    queryKey: ["repository", repositoryId],
    queryFn: () => getRepository(repositoryId as string),
    enabled: Boolean(repositoryId),
  });
}

export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId as string),
    enabled: Boolean(sessionId),
  });
}

