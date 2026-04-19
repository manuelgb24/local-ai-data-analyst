import type { ApiError, RunSummary } from "../api/types";

import { ErrorBanner } from "./ErrorBanner";

interface RunHistoryPanelProps {
  runs: RunSummary[];
  selectedRunId: string | null;
  isLoading: boolean;
  error: ApiError | null;
  onSelect: (runId: string) => void;
}

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("es", {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : DATE_TIME_FORMATTER.format(date);
}

function RunHistoryItem({
  run,
  selected,
  onSelect,
}: {
  run: RunSummary;
  selected: boolean;
  onSelect: (runId: string) => void;
}) {
  return (
    <li>
      <button
        type="button"
        className={`run-history-button ${selected ? "run-history-button-active" : ""}`}
        onClick={() => onSelect(run.run_id)}
        aria-pressed={selected}
      >
        <div className="run-history-header">
          <strong>{run.run_id}</strong>
          <span className={`status-chip ${run.status === "succeeded" ? "status-ok" : "status-error"}`}>
            {run.status}
          </span>
        </div>
        <p className="muted run-history-path">{run.dataset_path}</p>
        <dl className="run-history-meta">
          <div>
            <dt>Agente</dt>
            <dd>{run.agent_id}</dd>
          </div>
          <div>
            <dt>Session</dt>
            <dd>{run.session_id}</dd>
          </div>
          <div>
            <dt>Creado</dt>
            <dd>
              <time dateTime={run.created_at} title={run.created_at}>
                {formatTimestamp(run.created_at)}
              </time>
            </dd>
          </div>
          <div>
            <dt>Actualizado</dt>
            <dd>
              <time dateTime={run.updated_at} title={run.updated_at}>
                {formatTimestamp(run.updated_at)}
              </time>
            </dd>
          </div>
        </dl>
      </button>
    </li>
  );
}

export function RunHistoryPanel({
  runs,
  selectedRunId,
  isLoading,
  error,
  onSelect,
}: RunHistoryPanelProps) {
  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Historial</p>
          <h2>Runs persistidos</h2>
        </div>
      </div>

      {error ? <ErrorBanner title="No se pudo cargar el historial" error={error} /> : null}

      {!error && isLoading ? <p className="muted">Cargando historial persistido…</p> : null}

      {!error && !isLoading && runs.length === 0 ? (
        <p className="muted">Todavia no hay runs persistidos en este entorno local.</p>
      ) : null}

      {!error && runs.length > 0 ? (
        <ul className="run-history-list">
          {runs.map((run) => (
            <RunHistoryItem
              key={run.run_id}
              run={run}
              selected={run.run_id === selectedRunId}
              onSelect={onSelect}
            />
          ))}
        </ul>
      ) : null}
    </section>
  );
}
