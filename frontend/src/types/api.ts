export type RepositoryStatus = "cloning" | "indexing" | "ready" | "failed";

export interface RepositoryMetadata {
  languages?: Record<string, number>;
  important_files?: string[];
  tree?: string[];
  manifests?: Array<{ file: string; excerpt: string }>;
  clone?: {
    default_branch?: string | null;
    commit_sha?: string | null;
  };
}

export interface Repository {
  id: string;
  url: string;
  owner: string;
  name: string;
  status: RepositoryStatus;
  local_path: string;
  default_branch: string | null;
  commit_sha: string | null;
  file_count: number;
  line_count: number;
  metadata: RepositoryMetadata;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  file: string;
  start_line: number;
  end_line: number;
  excerpt?: string | null;
}

export interface AuditResult {
  verified: boolean;
  warnings: string[];
  unsupported_claims: string[];
  checked_citations: Citation[];
  details: string;
}

export interface ChatRequest {
  repository_id: string;
  question: string;
  session_id?: string | null;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  citations: Citation[];
  audit: AuditResult;
  reasoning_summary: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  audit?: AuditResult | null;
  reasoning_summary?: string | null;
  created_at?: string;
}

export interface SessionResponse {
  id: string;
  repository_id: string;
  title: string;
  memory_summary: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

