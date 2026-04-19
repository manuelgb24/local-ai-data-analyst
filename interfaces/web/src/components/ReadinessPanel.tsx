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
              <h3>Aplicacion</h3>
              <span
                className={`status-chip ${
                  readiness.application.ready ? "status-ok" : "status-error"
                }`}
              >
                {readiness.application.ready ? "lista" : "no lista"}
              </span>
            </div>
            <dl className="metadata-list">
              <div>
                <dt>Agente por defecto</dt>
                <dd>{readiness.application.default_agent_id}</dd>
              </div>
              <div>
                <dt>Artifacts root</dt>
                <dd>{readiness.application.artifacts_root}</dd>
              </div>
            </dl>
            <h4>Checks</h4>
            {renderChecks(readiness.application.checks)}
            <h4>Detalles</h4>
            {renderDetails(readiness.application.details)}
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
            <dl className="metadata-list">
              <div>
                <dt>Nombre</dt>
                <dd>{readiness.provider.proveedor}</dd>
              </div>
              <div>
                <dt>Endpoint</dt>
                <dd>{readiness.provider.endpoint}</dd>
              </div>
              <div>
                <dt>Modelo</dt>
                <dd>{readiness.provider.model}</dd>
              </div>
              <div>
                <dt>Modelo disponible</dt>
                <dd>{readiness.provider.model_available ? "si" : "no"}</dd>
              </div>
            </dl>
            <h4>Detalles</h4>
            {renderDetails(readiness.provider.details)}
          </article>
        </div>
      ) : null}
    </section>
  );
}