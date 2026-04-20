export interface ApiError {
  code: string;
  message: string;
  status: number;
  details?: Record<string, unknown> | null;
  trace_id?: string | null;
}

export interface ApplicationHealth {
  status: "ok" | "error";
  ready: boolean;
  default_agent_id: string;
  artifacts_root: string;
  checks: Record<string, boolean>;
  details?: string[];
}

export interface ProveedorHealth {
  status: "ok" | "error";
  ready: boolean;
  proveedor: string;
  endpoint: string;
  binary_available: boolean;
  binary_path?: string | null;
  reachable: boolean;
  version?: string | null;
  model: string;
  model_available: boolean;
  details?: string[];
}

export interface CreateRunRequest {
  agent_id: string;
  dataset_path: string;
  user_prompt: string;
  session_id?: string | null;
  conversation_context?: Array<{ role: "user" | "assistant"; content: string }> | null;
}

export interface CreateChatRequest {
  agent_id: string;
  dataset_path: string;
  user_prompt: string;
}

export interface SendChatMessageRequest {
  user_prompt: string;
}

export interface RunSummary {
  run_id: string;
  session_id: string;
  agent_id: string;
  dataset_path: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DatasetColumn {
  name: string;
  type: string;
}

export interface DatasetProfile {
  source_path: string;
  format: string;
  table_name: string;
  schema: DatasetColumn[];
  row_count: number;
  nulls?: Record<string, number> | null;
  sample?: Array<Record<string, unknown>> | null;
}

export interface SqlTraceEntry {
  statement: string;
  status: "ok" | "error";
  purpose?: string | null;
  rows_returned?: number | null;
}

export interface TableResult {
  name: string;
  rows: Array<Record<string, unknown>>;
}

export interface ChartReference {
  name: string;
  path?: string | null;
  chart_type?: "bar" | string;
  title?: string | null;
  x_key?: string | null;
  y_key?: string | null;
  data?: Array<Record<string, unknown>>;
}

export interface ArtifactManifest {
  run_id: string;
  response_path?: string | null;
  table_paths: string[];
  chart_paths: string[];
}

export interface AgentResult {
  narrative: string;
  findings: string[];
  sql_trace: SqlTraceEntry[];
  tables: TableResult[];
  charts: ChartReference[];
  artifact_manifest: ArtifactManifest;
  recommendations?: string[] | null;
}

export interface RunDetail {
  run_id: string;
  session_id: string;
  agent_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  dataset_profile?: DatasetProfile | null;
  result?: AgentResult | null;
  error?: {
    code: string;
    message: string;
    stage: string;
    details?: Record<string, unknown> | null;
  } | null;
  artifact_manifest?: ArtifactManifest | null;
}

export interface ArtifactListItem {
  name: string;
  type: string;
  path: string;
  run_id: string;
  size_bytes?: number | null;
}

export interface ChatMessage {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  run_id?: string | null;
  status?: string | null;
  result?: AgentResult | null;
  error?: {
    code: string;
    message: string;
    stage: string;
    details?: Record<string, unknown> | null;
  } | null;
}

export interface ChatSummary {
  chat_id: string;
  agent_id: string;
  dataset_path: string;
  title: string;
  created_at: string;
  updated_at: string;
  latest_run_id?: string | null;
  message_count: number;
}

export interface ChatDetail {
  chat_id: string;
  agent_id: string;
  dataset_path: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
  run_ids: string[];
  latest_run_id?: string | null;
}

export interface ReadinessState {
  application: ApplicationHealth;
  provider: ProveedorHealth;
}

