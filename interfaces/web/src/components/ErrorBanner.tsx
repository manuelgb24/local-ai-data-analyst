import type { ApiError } from "../api/types";

interface ErrorBannerProps {
  title: string;
  error: ApiError;
}

function recoveryHint(error: ApiError): string {
  const category = extractCategory(error);
  if (error.status === 0) {
    return "Comprueba que la API local esté arrancada y vuelve a intentarlo.";
  }
  if (category === "provider" || /ollama|proveedor|model/i.test(error.message)) {
    return "Revisa Ollama y el modelo local antes de lanzar otro análisis.";
  }
  if (category === "dataset" || /dataset|archivo|ruta/i.test(error.message)) {
    return "Comprueba que la ruta local exista y use csv, xlsx o parquet.";
  }
  return "Revisa el mensaje, ajusta la entrada si hace falta y vuelve a intentarlo.";
}

function extractCategory(error: ApiError): string | null {
  const details = error.details;
  if (!details || typeof details !== "object") {
    return null;
  }
  const category = details.category;
  return typeof category === "string" ? category : null;
}

export function ErrorBanner({ title, error }: ErrorBannerProps) {
  const details = error.details ? JSON.stringify(error.details, null, 2) : null;
  const category = extractCategory(error);

  return (
    <section className="panel panel-error" aria-live="polite" role="alert">
      <div className="error-summary">
        <span className="status-dot status-dot-error" aria-hidden="true" />
        <div>
          <p className="eyebrow">Requiere atención</p>
          <h2>{title}</h2>
        </div>
      </div>
      <p className="error-message">{error.message}</p>
      <p className="error-recovery">{recoveryHint(error)}</p>

      <details className="technical-details">
        <summary>Detalles técnicos</summary>
        <dl className="metadata-list metadata-list-compact">
          <div>
            <dt>Código</dt>
            <dd>{error.code}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{error.status === 0 ? "network" : error.status}</dd>
          </div>
          {category ? (
            <div>
              <dt>Categoría</dt>
              <dd>{category}</dd>
            </div>
          ) : null}
          {error.trace_id ? (
            <div>
              <dt>Trace</dt>
              <dd>{error.trace_id}</dd>
            </div>
          ) : null}
        </dl>
        {details ? <pre className="details-block">{details}</pre> : null}
      </details>
    </section>
  );
}

