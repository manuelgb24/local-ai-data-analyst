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
    return <p className="muted compact-copy">Sin checks adicionales.</p>;
  }

  return (
    <ul className="bullet-list bullet-list-compact">
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

function renderDetails(details: string[] | undefined, options: { skipFirst?: boolean } = {}) {
  const visibleDetails = options.skipFirst ? (details ?? []).slice(1) : (details ?? []);
  if (visibleDetails.length === 0) {
    return <p className="muted compact-copy">Sin detalles adicionales.</p>;
  }

  return (
    <ul className="bullet-list bullet-list-compact">
      {visibleDetails.map((detail) => (
        <li key={detail}>{detail}</li>
      ))}
    </ul>
  );
}

function primaryDetail(details: string[] | undefined, fallback: string): string {
  return details?.[0] ?? fallback;
}

export function ReadinessPanel({
  readiness,
  error,
  isLoading,
  onRefresh,
}: ReadinessPanelProps) {
  return (
    <section className="panel readiness-panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Readiness</p>
          <h2>Operación local</h2>
        </div>
        <button type="button" className="secondary-button" onClick={() => void onRefresh()}>
          Refrescar
        </button>
      </div>

      {isLoading ? (
        <div className="skeleton-stack" aria-label="Cargando readiness">
          <span className="skeleton-line skeleton-line-short" />
          <span className="skeleton-line" />
          <span className="skeleton-card" />
        </div>
      ) : null}
      {error ? <ErrorBanner title="No se pudo obtener readiness" error={error} /> : null}

      {readiness ? (
        <div className="readiness-grid">
          <article className={`status-card ${readiness.application.ready ? "status-card-ok" : "status-card-error"}`}>
            <div className="status-card-header">
              <div>
                <h3>{readiness.application.ready ? "Sistema listo" : "Sistema requiere revisión"}</h3>
                <p className="provider-summary">
                  {readiness.application.ready
                    ? "La aplicación local está preparada para operar."
                    : primaryDetail(readiness.application.details, "Revisa la configuración local de la aplicación.")}
                </p>
              </div>
              <span className={`status-chip ${readiness.application.ready ? "status-ok" : "status-error"}`}>
                {readiness.application.ready ? "lista" : "no lista"}
              </span>
            </div>
            <details className="technical-details">
              <summary>Checks y detalles</summary>
              <h4>Checks</h4>
              {renderChecks(readiness.application.checks)}
              <h4>Detalles</h4>
              {renderDetails(readiness.application.details, { skipFirst: !readiness.application.ready })}
              <dl className="metadata-list metadata-list-compact">
                <div>
                  <dt>Agente por defecto</dt>
                  <dd>{readiness.application.default_agent_id}</dd>
                </div>
                <div>
                  <dt>Artifacts root</dt>
                  <dd>{readiness.application.artifacts_root}</dd>
                </div>
              </dl>
            </details>
          </article>

          <article className={`status-card ${readiness.provider.ready ? "status-card-ok" : "status-card-error"}`}>
            <div className="status-card-header">
              <div>
                <h3>{readiness.provider.ready ? "Proveedor local listo" : "Proveedor requiere revisión"}</h3>
                <p className="provider-summary">
                  {readiness.provider.ready
                    ? "Ollama responde y el modelo configurado está disponible."
                    : primaryDetail(readiness.provider.details, "Revisa Ollama antes de enviar nuevos análisis.")}
                </p>
              </div>
              <span className={`status-chip ${readiness.provider.ready ? "status-ok" : "status-error"}`}>
                {readiness.provider.ready ? "listo" : "no listo"}
              </span>
            </div>
            <details className="technical-details">
              <summary>Proveedor y modelo</summary>
              <dl className="metadata-list metadata-list-compact">
                <div>
                  <dt>Proveedor</dt>
                  <dd>{readiness.provider.proveedor}</dd>
                </div>
                <div>
                  <dt>Modelo</dt>
                  <dd>{readiness.provider.model}</dd>
                </div>
                <div>
                  <dt>Endpoint</dt>
                  <dd>{readiness.provider.endpoint}</dd>
                </div>
              </dl>
              <h4>Detalles</h4>
              {renderDetails(readiness.provider.details, { skipFirst: !readiness.provider.ready })}
            </details>
          </article>
        </div>
      ) : null}
    </section>
  );
}
