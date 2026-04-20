import { useMemo, useState } from "react";
import type { FormEvent } from "react";

import type { ApiError, ChatDetail, ChatMessage, TableResult } from "../api/types";

import { ErrorBanner } from "./ErrorBanner";
import { InsightChart } from "./InsightChart";

interface ChatConversationProps {
  chat: ChatDetail | null;
  isLoading: boolean;
  error: ApiError | null;
  canSubmit: boolean;
  disabledReason: string | null;
  sending: boolean;
  onSendMessage: (prompt: string) => Promise<void>;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "number") {
    return new Intl.NumberFormat("es", { maximumFractionDigits: 4 }).format(value);
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function ResultTable({ table }: { table: TableResult }) {
  const columns = useMemo(() => {
    const names = new Set<string>();
    for (const row of table.rows) {
      Object.keys(row).forEach((column) => names.add(column));
    }
    return [...names];
  }, [table.rows]);

  if (table.rows.length === 0 || columns.length === 0) {
    return null;
  }

  return (
    <div className="compact-table">
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
            {table.rows.slice(0, 8).map((row, index) => (
              <tr key={`${table.name}-${index}`}>
                {columns.map((column) => (
                  <td key={`${table.name}-${index}-${column}`}>{formatValue(row[column])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TechnicalExports({ message }: { message: ChatMessage }) {
  const manifest = message.result?.artifact_manifest;
  const paths = [
    manifest?.response_path,
    ...(manifest?.table_paths ?? []),
    ...(manifest?.chart_paths ?? []),
  ].filter((path): path is string => Boolean(path));

  if (paths.length === 0 && !message.run_id) {
    return null;
  }

  return (
    <details className="technical-details">
      <summary>Exportaciones técnicas</summary>
      <dl className="metadata-list metadata-list-compact">
        {message.run_id ? (
          <div>
            <dt>Run técnico</dt>
            <dd>{message.run_id}</dd>
          </div>
        ) : null}
      </dl>
      {paths.length > 0 ? (
        <ul className="artifact-list">
          {paths.map((path) => (
            <li key={path} className="artifact-item artifact-item-compact">
              <code>{path}</code>
            </li>
          ))}
        </ul>
      ) : null}
    </details>
  );
}

function AssistantPayload({ message }: { message: ChatMessage }) {
  if (message.status === "failed" || message.error) {
    return (
      <div className="message-error">
        <strong>{message.error?.code ?? "error"}</strong>
        <span>{message.error?.message ?? message.content}</span>
      </div>
    );
  }

  const result = message.result;
  if (!result) {
    return <p>{message.content}</p>;
  }

  const chartNames = new Set((result.charts ?? []).map((chart) => chart.name));
  const visibleTables = result.tables.filter((table) => !chartNames.has(table.name));

  return (
    <>
      <p className="assistant-narrative">{result.narrative}</p>
      {result.findings.length > 0 ? (
        <div className="finding-grid">
          {result.findings.slice(0, 4).map((finding) => (
            <article className="finding-card" key={finding}>
              {finding}
            </article>
          ))}
        </div>
      ) : null}
      {result.charts.map((chart) => (
        <InsightChart key={chart.name} chart={chart} />
      ))}
      {visibleTables.slice(0, 3).map((table) => (
        <ResultTable key={table.name} table={table} />
      ))}
      <TechnicalExports message={message} />
    </>
  );
}

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <article className={`chat-message ${isUser ? "chat-message-user" : "chat-message-assistant"}`}>
      <div className="message-avatar">{isUser ? "Tú" : "AI"}</div>
      <div className="message-card">
        {isUser ? <p>{message.content}</p> : <AssistantPayload message={message} />}
      </div>
    </article>
  );
}

export function ChatConversation({
  chat,
  isLoading,
  error,
  canSubmit,
  disabledReason,
  sending,
  onSendMessage,
}: ChatConversationProps) {
  const [prompt, setPrompt] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedPrompt = prompt.trim();
    if (!normalizedPrompt) {
      return;
    }
    await onSendMessage(normalizedPrompt);
    setPrompt("");
  }

  if (isLoading && !chat) {
    return <section className="conversation-panel panel">Cargando chat…</section>;
  }

  if (error) {
    return (
      <section className="conversation-panel panel">
        <ErrorBanner title="No se pudo cargar el chat" error={error} />
      </section>
    );
  }

  if (!chat) {
    return (
      <section className="conversation-panel panel empty-state">
        <p className="eyebrow">Empieza aquí</p>
        <h2>Crea o selecciona un chat</h2>
        <p className="muted">
          Cada conversación conserva el dataset local y permite preguntas de seguimiento sobre el
          mismo análisis.
        </p>
      </section>
    );
  }

  return (
    <section className="conversation-panel panel">
      <div className="conversation-header">
        <div>
          <p className="eyebrow">Chat activo</p>
          <h2>{chat.title}</h2>
          <p className="muted" data-testid="chat-memory-note">
            Mismo dataset · {chat.dataset_path}
          </p>
        </div>
        <span className="status-chip status-ok">{chat.messages.length} mensajes</span>
      </div>

      <div className="message-list">
        {chat.messages.map((message) => (
          <ChatMessageBubble key={message.message_id} message={message} />
        ))}
      </div>

      <form className="follow-up-form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="form-field">
          <span>Nueva pregunta</span>
          <textarea
            aria-label="Nueva pregunta"
            rows={3}
            placeholder="Ej. compara la primera carrera con la segunda"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            disabled={!canSubmit || sending}
          />
        </label>
        {disabledReason ? <p className="submit-help">{disabledReason}</p> : null}
        <button type="submit" className="primary-button" disabled={!canSubmit || sending || !prompt.trim()}>
          {sending ? "Analizando…" : "Enviar"}
        </button>
      </form>
    </section>
  );
}

