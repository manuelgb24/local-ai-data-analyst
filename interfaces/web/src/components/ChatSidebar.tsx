import type { ApiError, ChatSummary } from "../api/types";

import { ErrorBanner } from "./ErrorBanner";

interface ChatSidebarProps {
  chats: ChatSummary[];
  selectedChatId: string | null;
  isLoading: boolean;
  error: ApiError | null;
  onSelect: (chatId: string) => void;
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

export function ChatSidebar({
  chats,
  selectedChatId,
  isLoading,
  error,
  onSelect,
}: ChatSidebarProps) {
  return (
    <aside className="chat-sidebar panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Memoria local</p>
          <h2>Chats recientes</h2>
        </div>
        <span className="status-chip status-soft">{chats.length}</span>
      </div>

      {error ? <ErrorBanner title="No se pudieron cargar los chats" error={error} /> : null}
      {!error && isLoading ? <p className="muted">Cargando conversaciones…</p> : null}
      {!error && !isLoading && chats.length === 0 ? (
        <p className="muted">Crea el primer chat para analizar un dataset local.</p>
      ) : null}

      <ul className="chat-list">
        {chats.map((chat) => (
          <li key={chat.chat_id}>
            <button
              type="button"
              className={`chat-list-item ${chat.chat_id === selectedChatId ? "chat-list-item-active" : ""}`}
              onClick={() => onSelect(chat.chat_id)}
            >
              <strong>{datasetLabel(chat.dataset_path)}</strong>
              <span>{chat.title}</span>
              <small>
                {chat.message_count} mensajes ·{" "}
                <time dateTime={chat.updated_at} title={chat.updated_at}>
                  {formatTimestamp(chat.updated_at)}
                </time>
              </small>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

