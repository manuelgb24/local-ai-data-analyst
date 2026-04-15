import { useCallback, useMemo, useState } from "react";

import { createRun, fetchRunArtifacts, normalizeUnknownError } from "../api/client";
import type { ApiError, ArtifactListItem, CreateRunRequest, RunDetail } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { ReadinessPanel } from "../components/ReadinessPanel";
import { RunForm } from "../components/RunForm";
import { RunResult } from "../components/RunResult";
import { useReadiness } from "./useReadiness";

export function App() {
  const {
    readiness,
    error: readinessError,
    isLoading: readinessLoading,
    canSubmit,
    blockedReason,
    refresh,
  } = useReadiness();
  const [runRequest, setRunRequest] = useState<CreateRunRequest | null>(null);
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactListItem[]>([]);
  const [submitError, setSubmitError] = useState<ApiError | null>(null);
  const [artifactError, setArtifactError] = useState<ApiError | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const defaultAgentId = readiness?.application.default_agent_id ?? "data_analyst";

  const handleSubmit = useCallback(async (payload: CreateRunRequest) => {
    setSubmitting(true);
    setSubmitError(null);
    setArtifactError(null);
    setRunRequest(payload);
    setRunDetail(null);
    setArtifacts([]);

    try {
      const nextRunDetail = await createRun(payload);
      setRunDetail(nextRunDetail);

      try {
        const nextArtifacts = await fetchRunArtifacts(nextRunDetail.run_id);
        setArtifacts(nextArtifacts);
      } catch (error) {
        setArtifactError(normalizeUnknownError(error));
      }
    } catch (error) {
      setSubmitError(normalizeUnknownError(error));
    } finally {
      setSubmitting(false);
    }
  }, []);

  const titleStatus = useMemo(() => {
    if (readinessLoading) {
      return "Verificando readiness...";
    }
    if (canSubmit) {
      return "Producto listo para lanzar un run";
    }
    return blockedReason ?? "El producto no esta listo.";
  }, [blockedReason, canSubmit, readinessLoading]);

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">3_agents - Fase 3</p>
          <h1>UI local-first para lanzar y revisar runs</h1>
          <p className="hero-text">
            Esta interfaz reutiliza la API local existente y mantiene la entrada del dataset por
            ruta manual local.
          </p>
        </div>
        <div className="hero-status">
          <span className={`status-chip ${canSubmit ? "status-ok" : "status-error"}`}>
            {canSubmit ? "ready" : "blocked"}
          </span>
          <p>{titleStatus}</p>
        </div>
      </header>

      <ReadinessPanel
        readiness={readiness}
        error={readinessError}
        isLoading={readinessLoading}
        onRefresh={refresh}
      />

      <div className="content-grid">
        <div className="content-column">
          <RunForm
            defaultAgentId={defaultAgentId}
            disabled={!canSubmit}
            disabledReason={blockedReason}
            submitting={submitting}
            onSubmit={handleSubmit}
          />
          {submitError ? <ErrorBanner title="El run no se pudo completar" error={submitError} /> : null}
        </div>
        <div className="content-column">
          <RunResult
            request={runRequest}
            runDetail={runDetail}
            artifacts={artifacts}
            artifactError={artifactError}
          />
        </div>
      </div>
    </main>
  );
}