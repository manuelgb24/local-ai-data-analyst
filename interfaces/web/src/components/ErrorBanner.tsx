import type { ApiError } from "../api/types";

interface ErrorBannerProps {
  title: string;
  error: ApiError;
}

export function ErrorBanner({ title, error }: ErrorBannerProps) {
  const details = error.details ? JSON.stringify(error.details, null, 2) : null;

  return (
    <section className="panel panel-error" aria-live="polite">
      <h2>{title}</h2>
      <p className="error-message">
        <strong>{error.code}</strong>: {error.message}
      </p>
      <dl className="metadata-list">
        <div>
          <dt>Status</dt>
          <dd>{error.status === 0 ? "network" : error.status}</dd>
        </div>
        {error.trace_id ? (
          <div>
            <dt>Trace</dt>
            <dd>{error.trace_id}</dd>
          </div>
        ) : null}
      </dl>
      {details ? <pre className="details-block">{details}</pre> : null}
    </section>
  );
}

