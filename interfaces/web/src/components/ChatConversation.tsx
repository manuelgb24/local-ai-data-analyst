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

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("es", {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : DATE_TIME_FORMATTER.format(date);
}

function datasetLabel(path: string): string {
  const normalized = path.split(/[\\/]/).pop() ?? path;
  return normalized.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ");
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

function ConversationSkeleton() {
  return (
    <section className="conversation-panel panel conversation-panel-loading" aria-label="Cargando chat">
      <div className="conversation-header">
        <div className="skeleton-stack">
          <span className="skeleton-line skeleton-line-short" />
          <span className="skeleton-line skeleton-line-title" />
        </div>
        <span className="skeleton-pill" />
      </div>
      <div className="message-list">
        <span className="skeleton-message skeleton-message-user" />
        <span className="skeleton-message skeleton-message-assistant" />
        <span className="skeleton-card skeleton-card-tall" />
      </div>
    </section>
  );
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
    return (
      <div className="compact-table">
        <p className="eyebrow">Evidencia</p>
        <h4>{table.name.replace(/[_-]+/g, " ")}</h4>
        <p className="muted compact-copy">Sin filas para mostrar.</p>
      </div>
    );
  }

  return (
    <div className="compact-table">
      <p className="eyebrow">Evidencia</p>
      <h4>{table.name.replace(/[_-]+/g, " ")}</h4>
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

function isTechnicalFinding(finding: string): boolean {
  return (
    /^Dataset has /i.test(finding) ||
    /^Preview query returned /i.test(finding) ||
    /^Dataset has no numeric columns/i.test(finding) ||
    /^Column .+: count=/i.test(finding)
  );
}

function isTechnicalTable(table: TableResult): boolean {
  return table.name === "preview" || table.name === "numeric_summary";
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
  const visibleFindings = result.findings.filter((finding) => !isTechnicalFinding(finding));
  const visibleTables = result.tables.filter((table) => !chartNames.has(table.name) && !isTechnicalTable(table));

  return (
    <>
      <p className="assistant-narrative">{result.narrative}</p>
      {visibleFindings.length > 0 ? (
        <div className="finding-grid">
          {visibleFindings.slice(0, 4).map((finding) => (
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
    </>
  );
}

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <article className={`chat-message ${isUser ? "chat-message-user" : "chat-message-assistant"}`}>
      <div className="message-avatar" aria-hidden="true">
        {isUser ? "Tú" : "IA"}
      </div>
      <div className="message-card">
        <div className="message-meta">
          <span>{isUser ? "Tú" : "Analista local"}</span>
          <time dateTime={message.created_at} title={message.created_at}>
            {formatTimestamp(message.created_at)}
          </time>
        </div>
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
    return <ConversationSkeleton />;
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
      <section className="conversation-panel panel empty-state empty-state-card">
        <div className="empty-illustration" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <p className="eyebrow">Empieza aquí</p>
        <h2>Crea o selecciona un chat</h2>
        <p className="muted">
          Elige un dataset local, formula una pregunta y mantén el análisis en una conversación persistente.
        </p>
      </section>
    );
  }

  const label = datasetLabel(chat.dataset_path);

  return (
    <section className="conversation-panel panel">
      <div className="conversation-header">
        <div>
          <p className="eyebrow">Chat activo</p>
          <h2>{chat.title}</h2>
          <p className="muted" data-testid="chat-memory-note">
            Mismo dataset · {label}
          </p>
          <details className="technical-details technical-details-inline">
            <summary>Ver ruta y trazabilidad</summary>
            <dl className="metadata-list metadata-list-compact">
              <div>
                <dt>Dataset path</dt>
                <dd>{chat.dataset_path}</dd>
              </div>
              <div>
                <dt>Último run</dt>
                <dd>{chat.latest_run_id ?? "Sin run asociado"}</dd>
              </div>
              <div>
                <dt>Runs del chat</dt>
                <dd>{chat.run_ids.length}</dd>
              </div>
            </dl>
          </details>
        </div>
        <span className="status-chip status-ok">{chat.messages.length} mensajes</span>
      </div>

      <div className="message-list" aria-live="polite">
        {chat.messages.map((message) => (
          <ChatMessageBubble key={message.message_id} message={message} />
        ))}
        {sending ? (
          <article className="chat-message chat-message-assistant" role="status" aria-label="Analizando">
            <div className="message-avatar" aria-hidden="true">
              IA
            </div>
            <div className="message-card message-card-loading">
              <span className="skeleton-line skeleton-line-short" />
              <span className="skeleton-line" />
              <span className="skeleton-line skeleton-line-medium" />
            </div>
          </article>
        ) : null}
      </div>

      <form className="follow-up-form composer-card" onSubmit={(event) => void handleSubmit(event)}>
        <label className="form-field">
          <span>Nueva pregunta</span>
          <textarea
            aria-label="Nueva pregunta"
            name="follow_up_prompt"
            rows={3}
            placeholder="Ej. compara la primera carrera con la segunda…"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            disabled={!canSubmit || sending}
            autoComplete="off"
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
