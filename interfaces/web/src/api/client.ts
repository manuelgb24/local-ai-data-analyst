import type {
  ApiError,
  ApplicationHealth,
  ArtifactListItem,
  CreateRunRequest,
  ProveedorHealth,
  ReadinessState,
  RunDetail,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class ApiClientError extends Error {
  payload: ApiError;

  constructor(payload: ApiError) {
    super(payload.message);
    this.name = "ApiClientError";
    this.payload = payload;
  }
}

export function isApiError(value: unknown): value is ApiError {
  return Boolean(
    value &&
      typeof value === "object" &&
      "code" in value &&
      "message" in value &&
      "status" in value,
  );
}

export function normalizeUnknownError(error: unknown): ApiError {
  if (error instanceof ApiClientError) {
    return error.payload;
  }

  if (isApiError(error)) {
    return error;
  }

  if (error instanceof Error) {
    return {
      code: "network_error",
      message: error.message,
      status: 0,
      details: null,
      trace_id: null,
    };
  }

  return {
    code: "unexpected_frontend_error",
    message: "Unexpected frontend error",
    status: 0,
    details: null,
    trace_id: null,
  };
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
      ...init,
    });
  } catch (error) {
    throw new ApiClientError(normalizeUnknownError(error));
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload =
    contentType.includes("application/json") && response.status !== 204
      ? ((await response.json()) as unknown)
      : null;

  if (!response.ok) {
    const apiError = isApiError(payload)
      ? payload
      : {
          code: "unexpected_api_error",
          message: `Unexpected API error (${response.status})`,
          status: response.status,
          details: payload && typeof payload === "object" ? (payload as Record<string, unknown>) : null,
          trace_id: null,
        };
    throw new ApiClientError(apiError);
  }

  return payload as T;
}

export async function fetchApplicationHealth(): Promise<ApplicationHealth> {
  return requestJson<ApplicationHealth>("/health");
}

export async function fetchProviderHealth(): Promise<ProveedorHealth> {
  return requestJson<ProveedorHealth>("/health/proveedor");
}

export async function fetchReadiness(): Promise<ReadinessState> {
  const [application, provider] = await Promise.all([
    fetchApplicationHealth(),
    fetchProviderHealth(),
  ]);
  return { application, provider };
}

export async function createRun(payload: CreateRunRequest): Promise<RunDetail> {
  return requestJson<RunDetail>("/runs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchRunArtifacts(runId: string): Promise<ArtifactListItem[]> {
  return requestJson<ArtifactListItem[]>(`/runs/${encodeURIComponent(runId)}/artifacts`);
}

