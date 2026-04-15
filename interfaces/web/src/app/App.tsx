import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createRun,
  fetchRunArtifacts,
  fetchRunDetail,
  fetchRuns,
  normalizeUnknownError,
} from "../api/client";
import type {
  ApiError,
  ArtifactListItem,
  CreateRunRequest,
  RunDetail,
  RunSummary,
} from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { ReadinessPanel } from "../components/ReadinessPanel";
import { RunForm } from "../components/RunForm";
import { RunHistoryPanel } from "../components/RunHistoryPanel";
import { RunResult } from "../components/RunResult";
import { useReadiness } from "./useReadiness";

function extractErrorStage(error: ApiError): string | null {
  const stage = error.details?.stage;
  return typeof stage === "string" ? stage : null;
}

function shouldRefreshHistoryAfterSubmitError(error: ApiError): boolean {
  const stage = extractErrorStage(error);
  if (stage === "request_validation") {
    return false;
  }
  if (stage === null && error.code === "invalid_request") {
    return false;
  }
  return true;
}

export function App() {
  const {
    readiness,
    error: readinessError,
    isLoading: readinessLoading,
    canSubmit,
    blockedReason,
    refresh,
  } = useReadiness();
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactListItem[]>([]);
  const [historyError, setHistoryError] = useState<ApiError | null>(null);
  const [detailError, setDetailError] = useState<ApiError | null>(null);
  const [submitError, setSubmitError] = useState<ApiError | null>(null);
  const [artifactError, setArtifactError] = useState<ApiError | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const defaultAgentId = readiness?.application.default_agent_id ?? "data_analyst";

  const selectedRunSummary = useMemo(
    () => runs.find((run) => run.run_id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );

  const loadHistory = useCallback(
    async ({
      preferredRunId,
      preferLatest = false,
    }: {
      preferredRunId?: string;
      preferLatest?: boolean;
    } = {}) => {
      setHistoryLoading(true);
      setHistoryError(null);

      try {
        const nextRuns = await fetchRuns();
        setRuns(nextRuns);
        setSelectedRunId((current) => {
          if (preferredRunId && nextRuns.some((run) => run.run_id === preferredRunId)) {
            return preferredRunId;
          }
          if (!preferLatest && current && nextRuns.some((run) => run.run_id === current)) {
            return current;
          }
          return nextRuns[0]?.run_id ?? null;
        });
      } catch (error) {
        setHistoryError(normalizeUnknownError(error));
        setRuns([]);
        setSelectedRunId(null);
      } finally {
        setHistoryLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadHistory({ preferLatest: true });
  }, [loadHistory]);

  useEffect(() => {
    let ignore = false;

    if (!selectedRunId) {
      setRunDetail(null);
      setArtifacts([]);
      setDetailError(null);
      setArtifactError(null);
      setDetailLoading(false);
      return () => {
        ignore = true;
      };
    }

    async function loadSelectedRun(runId: string) {
      setDetailLoading(true);
      setDetailError(null);
      setArtifactError(null);

      try {
        const artifactsPromise = fetchRunArtifacts(runId).catch((error) => {
          const nextArtifactError = normalizeUnknownError(error);
          if (!ignore) {
            setArtifactError(nextArtifactError);
          }
          return [] as ArtifactListItem[];
        });

        const [nextRunDetail, nextArtifacts] = await Promise.all([
          fetchRunDetail(runId),
          artifactsPromise,
        ]);

        if (ignore) {
          return;
        }

        setRunDetail(nextRunDetail);
        setArtifacts(nextArtifacts);
      } catch (error) {
        if (ignore) {
          return;
        }

        setRunDetail(null);
        setArtifacts([]);
        setDetailError(normalizeUnknownError(error));
      } finally {
        if (!ignore) {
          setDetailLoading(false);
        }
      }
    }

    void loadSelectedRun(selectedRunId);

    return () => {
      ignore = true;
    };
  }, [selectedRunId]);

  const handleSubmit = useCallback(
    async (payload: CreateRunRequest) => {
      setSubmitting(true);
      setSubmitError(null);

      try {
        const nextRunDetail = await createRun(payload);
        await loadHistory({ preferredRunId: nextRunDetail.run_id });
      } catch (error) {
        const nextSubmitError = normalizeUnknownError(error);
        setSubmitError(nextSubmitError);

        if (shouldRefreshHistoryAfterSubmitError(nextSubmitError)) {
          await loadHistory({ preferLatest: true });
        }
      } finally {
        setSubmitting(false);
      }
    },
    [loadHistory],
  );

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
          <p className="eyebrow">3_agents - Fase 4</p>
          <h1>UI local-first para lanzar y explorar runs persistidos</h1>
          <p className="hero-text">
            Esta interfaz reutiliza la API local existente para lanzar runs, revisar historial
            persistido y explorar artifacts locales sin salir del producto.
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
          <RunHistoryPanel
            runs={runs}
            selectedRunId={selectedRunId}
            isLoading={historyLoading}
            error={historyError}
            onSelect={setSelectedRunId}
          />
        </div>
        <div className="content-column">
          <RunResult
            selectedRunSummary={selectedRunSummary}
            runDetail={runDetail}
            artifacts={artifacts}
            detailError={detailError}
            artifactError={artifactError}
            isLoading={detailLoading}
          />
        </div>
      </div>
    </main>
  );
}
