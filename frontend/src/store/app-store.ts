import type { ChatMessage, Repository } from "@/types/api";

export interface InvestigatorState {
  repository: Repository | null;
  sessionId: string | null;
  messages: ChatMessage[];
}

