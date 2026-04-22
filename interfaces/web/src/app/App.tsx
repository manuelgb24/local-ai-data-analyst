import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import {
  createChat,
  fetchChatDetail,
  fetchChats,
  fetchLocalDatasets,
  normalizeUnknownError,
  sendChatMessage,
} from "../api/client";
import type { ApiError, ChatDetail, ChatSummary, CreateChatRequest, LocalDatasetListItem } from "../api/types";
import { ChatConversation } from "../components/ChatConversation";
import { ChatSidebar } from "../components/ChatSidebar";
import { ErrorBanner } from "../components/ErrorBanner";
import { ReadinessPanel } from "../components/ReadinessPanel";
import { useReadiness } from "./useReadiness";

const LOCAL_URL_PATTERN = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//;
const SUPPORTED_EXTENSIONS = new Set(["csv", "xlsx", "parquet"]);

type NewChatErrors = Partial<Record<keyof CreateChatRequest, string>>;

function validateNewChat(payload: CreateChatRequest): NewChatErrors {
  const errors: NewChatErrors = {};
  if (!payload.agent_id.trim()) {
    errors.agent_id = "El agente es obligatorio.";
  }
  const datasetPath = payload.dataset_path.trim();
  if (!datasetPath) {
    errors.dataset_path = "La ruta del dataset es obligatoria.";
  } else if (LOCAL_URL_PATTERN.test(datasetPath)) {
    errors.dataset_path = "La ruta debe ser local, no una URL.";
  } else {
    const extension = datasetPath.includes(".") ? datasetPath.split(".").pop()?.toLowerCase() : "";
    if (!extension || !SUPPORTED_EXTENSIONS.has(extension)) {
      errors.dataset_path = "La ruta debe terminar en csv, xlsx o parquet.";
    }
  }
  if (!payload.user_prompt.trim()) {
    errors.user_prompt = "La pregunta inicial es obligatoria.";
  }
  return errors;
}

interface NewChatCardProps {
  defaultAgentId: string;
  disabled: boolean;
  disabledReason: string | null;
  datasets: LocalDatasetListItem[];
  datasetsLoading: boolean;
  datasetError: ApiError | null;
  submitting: boolean;
  onSubmit: (payload: CreateChatRequest) => Promise<void>;
}

function NewChatCard({
  defaultAgentId,
  disabled,
  disabledReason,
  datasets,
  datasetsLoading,
  datasetError,
  submitting,
  onSubmit,
}: NewChatCardProps) {
  const [payload, setPayload] = useState<CreateChatRequest>({
    agent_id: defaultAgentId,
    dataset_path: "",
    user_prompt: "",
  });
  const [errors, setErrors] = useState<NewChatErrors>({});
  const [manualDatasetMode, setManualDatasetMode] = useState(false);

  useEffect(() => {
    setPayload((current) => ({ ...current, agent_id: defaultAgentId }));
  }, [defaultAgentId]);

  useEffect(() => {
    if (manualDatasetMode || datasets.length === 0) {
      return;
    }
    setPayload((current) => {
      if (current.dataset_path && datasets.some((dataset) => dataset.path === current.dataset_path)) {
        return current;
      }
      return { ...current, dataset_path: datasets[0].path };
    });
  }, [datasets, manualDatasetMode]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validateNewChat(payload);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }
    await onSubmit({
      agent_id: payload.agent_id.trim(),
      dataset_path: payload.dataset_path.trim(),
      user_prompt: payload.user_prompt.trim(),
    });
  }

  return (
    <section className="new-chat-card panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Nuevo análisis</p>
          <h2>Crear chat</h2>
        </div>
        <span className="status-chip status-soft">data_analyst</span>
      </div>
      <form className="run-form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="form-field">
          <span>Agente</span>
          <select aria-label="Agente" value={payload.agent_id} disabled>
            <option value="data_analyst">data_analyst</option>
          </select>
        </label>
        {!manualDatasetMode && datasets.length > 0 ? (
          <label className="form-field">
            <span>Dataset local</span>
            <select
              aria-label="Dataset local"
              value={payload.dataset_path}
              onChange={(event) => {
                setPayload((current) => ({ ...current, dataset_path: event.target.value }));
                setErrors((current) => ({ ...current, dataset_path: undefined }));
              }}
              disabled={submitting}
            >
              {datasets.map((dataset) => (
                <option key={dataset.path} value={dataset.path}>
                  {dataset.label} · {dataset.format.toUpperCase()}
                </option>
              ))}
            </select>
            <small className="field-help">Detectados en DatasetV1. Puedes cambiar a ruta manual si lo necesitas.</small>
            <button
              type="button"
              className="text-button"
              onClick={() => setManualDatasetMode(true)}
              disabled={submitting}
            >
              Usar ruta manual
            </button>
            {errors.dataset_path ? <small className="field-error">{errors.dataset_path}</small> : null}
          </label>
        ) : (
          <label className="form-field">
            <span>Ruta local del dataset</span>
            <input
              aria-label="Ruta local del dataset"
              name="dataset_path"
              placeholder="DatasetV1/student_lifestyle_performance_dataset.csv…"
              value={payload.dataset_path}
              onChange={(event) => {
                setPayload((current) => ({ ...current, dataset_path: event.target.value }));
                setErrors((current) => ({ ...current, dataset_path: undefined }));
              }}
              disabled={submitting}
            />
            {datasetsLoading ? <small className="field-help">Buscando datasets en DatasetV1…</small> : null}
            {datasetError ? <small className="field-error">No se pudieron cargar los datasets guardados.</small> : null}
            {datasets.length > 0 ? (
              <button
                type="button"
                className="text-button"
                onClick={() => {
                  setManualDatasetMode(false);
                  setPayload((current) => ({ ...current, dataset_path: datasets[0].path }));
                  setErrors((current) => ({ ...current, dataset_path: undefined }));
                }}
                disabled={submitting}
              >
                Elegir desde DatasetV1
              </button>
            ) : null}
            {errors.dataset_path ? <small className="field-error">{errors.dataset_path}</small> : null}
          </label>
        )}
        <label className="form-field">
          <span>Pregunta inicial</span>
          <textarea
            aria-label="Pregunta inicial"
            name="initial_prompt"
            rows={4}
            placeholder="Ej. dime cuál es la carrera en la que más se estudia…"
            value={payload.user_prompt}
            onChange={(event) => {
              setPayload((current) => ({ ...current, user_prompt: event.target.value }));
              setErrors((current) => ({ ...current, user_prompt: undefined }));
            }}
            disabled={submitting}
          />
          {errors.user_prompt ? <small className="field-error">{errors.user_prompt}</small> : null}
        </label>
        {disabledReason ? <p className="submit-help">{disabledReason}</p> : null}
        <button type="submit" className="primary-button" disabled={disabled || submitting}>
          {submitting ? "Creando chat…" : "Crear chat"}
        </button>
      </form>
    </section>
  );
}

export function App() {
  const {
    readiness,
    error: readinessError,
    isLoading: readinessLoading,
    canSubmit,
    blockedReason,
    refresh,
  } = useReadiness();
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [chatDetail, setChatDetail] = useState<ChatDetail | null>(null);
  const [chatListError, setChatListError] = useState<ApiError | null>(null);
  const [chatDetailError, setChatDetailError] = useState<ApiError | null>(null);
  const [submitError, setSubmitError] = useState<ApiError | null>(null);
  const [datasetListError, setDatasetListError] = useState<ApiError | null>(null);
  const [chatListLoading, setChatListLoading] = useState(true);
  const [chatDetailLoading, setChatDetailLoading] = useState(false);
  const [datasetListLoading, setDatasetListLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [sending, setSending] = useState(false);
  const [localDatasets, setLocalDatasets] = useState<LocalDatasetListItem[]>([]);

  const defaultAgentId = readiness?.application.default_agent_id ?? "data_analyst";

  const loadChats = useCallback(
    async ({ preferredChatId, preferLatest = false }: { preferredChatId?: string; preferLatest?: boolean } = {}) => {
      setChatListLoading(true);
      setChatListError(null);
      try {
        const nextChats = await fetchChats();
        setChats(nextChats);
        setSelectedChatId((current) => {
          if (preferredChatId && nextChats.some((chat) => chat.chat_id === preferredChatId)) {
            return preferredChatId;
          }
          if (!preferLatest && current && nextChats.some((chat) => chat.chat_id === current)) {
            return current;
          }
          return nextChats[0]?.chat_id ?? null;
        });
      } catch (error) {
        setChatListError(normalizeUnknownError(error));
        setChats([]);
        setSelectedChatId(null);
      } finally {
        setChatListLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadChats({ preferLatest: true });
  }, [loadChats]);

  useEffect(() => {
    let ignore = false;

    async function loadLocalDatasets() {
      setDatasetListLoading(true);
      setDatasetListError(null);
      try {
        const datasets = await fetchLocalDatasets();
        if (!ignore) {
          setLocalDatasets(datasets);
        }
      } catch (error) {
        if (!ignore) {
          setDatasetListError(normalizeUnknownError(error));
          setLocalDatasets([]);
        }
      } finally {
        if (!ignore) {
          setDatasetListLoading(false);
        }
      }
    }

    void loadLocalDatasets();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;
    if (!selectedChatId) {
      setChatDetail(null);
      setChatDetailError(null);
      setChatDetailLoading(false);
      return () => {
        ignore = true;
      };
    }

    async function loadSelectedChat(chatId: string) {
      setChatDetailLoading(true);
      setChatDetailError(null);
      try {
        const nextDetail = await fetchChatDetail(chatId);
        if (!ignore) {
          setChatDetail(nextDetail);
        }
      } catch (error) {
        if (!ignore) {
          setChatDetail(null);
          setChatDetailError(normalizeUnknownError(error));
        }
      } finally {
        if (!ignore) {
          setChatDetailLoading(false);
        }
      }
    }

    void loadSelectedChat(selectedChatId);
    return () => {
      ignore = true;
    };
  }, [selectedChatId]);

  const handleCreateChat = useCallback(
    async (payload: CreateChatRequest) => {
      setSubmitting(true);
      setSubmitError(null);
      try {
        const detail = await createChat(payload);
        setChatDetail(detail);
        await loadChats({ preferredChatId: detail.chat_id });
      } catch (error) {
        setSubmitError(normalizeUnknownError(error));
        await loadChats({ preferLatest: true });
      } finally {
        setSubmitting(false);
      }
    },
    [loadChats],
  );

  const handleSendMessage = useCallback(
    async (prompt: string) => {
      if (!chatDetail) {
        return;
      }
      setSending(true);
      setSubmitError(null);
      try {
        const detail = await sendChatMessage(chatDetail.chat_id, { user_prompt: prompt });
        setChatDetail(detail);
        await loadChats({ preferredChatId: detail.chat_id });
      } catch (error) {
        setSubmitError(normalizeUnknownError(error));
        await loadChats({ preferredChatId: chatDetail.chat_id });
        setSelectedChatId(chatDetail.chat_id);
      } finally {
        setSending(false);
      }
    },
    [chatDetail, loadChats],
  );

  const titleStatus = useMemo(() => {
    if (readinessLoading) {
      return "Verificando operación local…";
    }
    if (canSubmit) {
      return "Listo para conversar con data_analyst";
    }
    return blockedReason ?? "El producto no está listo.";
  }, [blockedReason, canSubmit, readinessLoading]);

  return (
    <main className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">3_agents · Local-first</p>
          <h1>Chats analíticos locales</h1>
          <p className="hero-text">
            Analiza un dataset local, conversa con memoria corta y revisa gráficos embebidos sin salir de la interfaz.
          </p>
        </div>
        <div className="hero-status">
          <span className={`status-chip ${canSubmit ? "status-ok" : "status-error"}`}>
            {canSubmit ? "ready" : "blocked"}
          </span>
          <p>{titleStatus}</p>
        </div>
      </header>

      <div className={`product-layout ${selectedChatId ? "product-layout-has-chat" : "product-layout-empty"}`}>
        <div className="left-rail">
          <NewChatCard
            defaultAgentId={defaultAgentId}
            disabled={!canSubmit}
            disabledReason={blockedReason}
            datasets={localDatasets}
            datasetsLoading={datasetListLoading}
            datasetError={datasetListError}
            submitting={submitting}
            onSubmit={handleCreateChat}
          />
          {submitError ? <ErrorBanner title="No se pudo completar la conversación" error={submitError} /> : null}
          <ChatSidebar
            chats={chats}
            selectedChatId={selectedChatId}
            isLoading={chatListLoading}
            error={chatListError}
            onSelect={setSelectedChatId}
          />
        </div>

        <ChatConversation
          chat={chatDetail}
          isLoading={chatDetailLoading}
          error={chatDetailError}
          canSubmit={canSubmit}
          disabledReason={blockedReason}
          sending={sending}
          onSendMessage={handleSendMessage}
        />

        <aside className="right-rail">
          <ReadinessPanel
            readiness={readiness}
            error={readinessError}
            isLoading={readinessLoading}
            onRefresh={refresh}
          />
        </aside>
      </div>
    </main>
  );
}
