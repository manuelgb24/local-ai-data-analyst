import type { ApiError, ReadinessState } from "../api/types";

import { ErrorBanner } from "./ErrorBanner";

interface ReadinessPanelProps {
  readiness: ReadinessState | null;
  error: ApiError | null;
  isLoading: boolean;
  onRefresh: () => Promise<void>;
}

function renderChecks(checks: Record<string, boolean> | undefined) {
  if (!checks || Object.keys(checks).length === 0) {
    return <p className="muted">Sin checks adicionales.</p>;
  }

  return (
    <ul className="bullet-list">
      {Object.entries(checks).map(([name, value]) => (
        <li key={name}>
          <span className={`status-chip ${value ? "status-ok" : "status-error"}`}>
            {value ? "ok" : "error"}
          </span>{" "}
          <span>{name}</span>
        </li>
      ))}
    </ul>
  );
}

function renderDetails(details: string[] | undefined) {
  if (!details || details.length === 0) {
    return <p className="muted">Sin detalles adicionales.</p>;
  }

  return (
    <ul className="bullet-list">
      {details.map((detail) => (
        <li key={detail}>{detail}</li>
      ))}
    </ul>
  );
}

export function ReadinessPanel({
  readiness,
  error,
  isLoading,
  onRefresh,
}: ReadinessPanelProps) {
  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Readiness</p>
          <h2>Estado operativo</h2>
        </div>
        <button type="button" className="secondary-button" onClick={() => void onRefresh()}>
          Refrescar
        </button>
      </div>

      {isLoading ? <p className="muted">Cargando readiness…</p> : null}
      {error ? <ErrorBanner title="No se pudo obtener readiness" error={error} /> : null}

      {readiness ? (
        <div className="readiness-grid">
          <article className="status-card">
            <div className="status-card-header">
              <h3>Sistema</h3>
              <span
                className={`status-chip ${
                  readiness.application.ready ? "status-ok" : "status-error"
                }`}
              >
                {readiness.application.ready ? "lista" : "no lista"}
              </span>
            </div>
            <h4>Checks</h4>
            {renderChecks(readiness.application.checks)}
            {!readiness.application.ready ? (
              <>
                <h4>Qué revisar</h4>
                {renderDetails(readiness.application.details)}
              </>
            ) : null}
          </article>

          <article className="status-card">
            <div className="status-card-header">
              <h3>Proveedor</h3>
              <span
                className={`status-chip ${readiness.provider.ready ? "status-ok" : "status-error"}`}
              >
                {readiness.provider.ready ? "listo" : "no listo"}
              </span>
            </div>
            <p className="provider-summary">
              {readiness.provider.proveedor} · {readiness.provider.model}
            </p>
            {!readiness.provider.ready ? (
              <>
                <h4>Qué revisar</h4>
                {renderDetails(readiness.provider.details)}
              </>
            ) : null}
          </article>
        </div>
      ) : null}
    </section>
  );
}
