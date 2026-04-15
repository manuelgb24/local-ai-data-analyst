import { useMemo, useState } from "react";

import type { ApiError, ArtifactListItem, CreateRunRequest, RunDetail, TableResult } from "../api/types";

import { ErrorBanner } from "./ErrorBanner";

interface RunResultProps {
  request: CreateRunRequest | null;
  runDetail: RunDetail | null;
  artifacts: ArtifactListItem[];
  artifactError: ApiError | null;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function TablePreview({ table }: { table: TableResult }) {
  const columns = useMemo(() => {
    const names = new Set<string>();
    for (const row of table.rows) {
      Object.keys(row).forEach((column) => names.add(column));
    }
    return [...names];
  }, [table.rows]);

  if (table.rows.length === 0 || columns.length === 0) {
    return (
      <article className="result-card">
        <h4>{table.name}</h4>
        <p className="muted">La tabla no tiene filas para mostrar.</p>
      </article>
    );
  }

  return (
    <article className="result-card">
      <h4>{table.name}</h4>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, index) => (
              <tr key={`${table.name}-${index}`}>
                {columns.map((column) => (
                  <td key={`${table.name}-${index}-${column}`}>{formatValue(row[column])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function ArtifactList({ artifacts }: { artifacts: ArtifactListItem[] }) {
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  async function copyPath(path: string) {
    try {
      await navigator.clipboard.writeText(path);
      setCopiedPath(path);
    } catch {
      setCopiedPath(null);
    }
  }

  if (artifacts.length === 0) {
    return <p className="muted">Este run no devolvio artifacts adicionales.</p>;
  }

  return (
    <ul className="artifact-list">
      {artifacts.map((artifact) => (
        <li key={`${artifact.run_id}-${artifact.path}`} className="artifact-item">
          <div>
            <p className="artifact-name">{artifact.name}</p>
            <p className="muted">
              {artifact.type} Â· {artifact.size_bytes ?? "?"} bytes
            </p>
            <code>{artifact.path}</code>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => void copyPath(artifact.path)}
          >
            {copiedPath === artifact.path ? "Ruta copiada" : "Copiar ruta"}
          </button>
        </li>
      ))}
    </ul>
  );
}

export function RunResult({ request, runDetail, artifacts, artifactError }: RunResultProps) {
  if (!runDetail) {
    return (
      <section className="panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Resultado</p>
            <h2>Ultimo run</h2>
          </div>
        </div>
        <p className="muted">Lanza un run para ver narrativa, hallazgos, tablas y artifacts.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Resultado</p>
          <h2>Ultimo run</h2>
        </div>
        <span className={`status-chip ${runDetail.status === "succeeded" ? "status-ok" : "status-error"}`}>
          {runDetail.status}
        </span>
      </div>

      <dl className="metadata-list">
        <div>
          <dt>Run ID</dt>
          <dd>{runDetail.run_id}</dd>
        </div>
        <div>
          <dt>Session ID</dt>
          <dd>{runDetail.session_id}</dd>
        </div>
        <div>
          <dt>Agente</dt>
          <dd>{runDetail.agent_id}</dd>
        </div>
        <div>
          <dt>Dataset path</dt>
          <dd>{request?.dataset_path ?? "-"}</dd>
        </div>
      </dl>

      {runDetail.dataset_profile ? (
        <article className="result-card">
          <h3>Perfil del dataset</h3>
          <dl className="metadata-list">
            <div>
              <dt>Formato</dt>
              <dd>{runDetail.dataset_profile.format}</dd>
            </div>
            <div>
              <dt>Tabla</dt>
              <dd>{runDetail.dataset_profile.table_name}</dd>
            </div>
            <div>
              <dt>Filas</dt>
              <dd>{runDetail.dataset_profile.row_count}</dd>
            </div>
          </dl>
        </article>
      ) : null}

      {runDetail.result ? (
        <>
          <article className="result-card">
            <h3>Narrativa</h3>
            <p className="narrative-text">{runDetail.result.narrative}</p>
          </article>

          <article className="result-card">
            <h3>Hallazgos</h3>
            {runDetail.result.findings.length > 0 ? (
              <ul className="bullet-list">
                {runDetail.result.findings.map((finding) => (
                  <li key={finding}>{finding}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">Sin hallazgos adicionales.</p>
            )}
          </article>

          {runDetail.result.recommendations?.length ? (
            <article className="result-card">
              <h3>Recomendaciones</h3>
              <ul className="bullet-list">
                {runDetail.result.recommendations.map((recommendation) => (
                  <li key={recommendation}>{recommendation}</li>
                ))}
              </ul>
            </article>
          ) : null}

          <div className="result-grid">
            {runDetail.result.tables.map((table) => (
              <TablePreview key={table.name} table={table} />
            ))}
          </div>
        </>
      ) : null}

      <article className="result-card">
        <h3>Artifacts</h3>
        {artifactError ? <ErrorBanner title="No se pudieron cargar los artifacts" error={artifactError} /> : null}
        <ArtifactList artifacts={artifacts} />
      </article>
    </section>
  );
}