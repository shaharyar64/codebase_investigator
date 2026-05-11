import axios from "axios";

import type {
  ChatRequest,
  ChatResponse,
  Repository,
  SessionResponse,
} from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180_000,
});

export async function submitRepository(url: string): Promise<Repository> {
  const response = await apiClient.post<Repository>("/repositories", { url });
  return response.data;
}

export async function getRepository(repositoryId: string): Promise<Repository> {
  const response = await apiClient.get<Repository>(`/repositories/${repositoryId}`);
  return response.data;
}

export async function askQuestion(payload: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>("/chat", payload);
  return response.data;
}

export async function getSession(sessionId: string): Promise<SessionResponse> {
  const response = await apiClient.get<SessionResponse>(`/sessions/${sessionId}`);
  return response.data;
}

