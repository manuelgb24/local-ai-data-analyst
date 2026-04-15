import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import type { CreateRunRequest } from "../api/types";

const LOCAL_URL_PATTERN = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//;
const SUPPORTED_EXTENSIONS = new Set(["csv", "xlsx", "parquet"]);

type FieldErrors = Partial<Record<keyof CreateRunRequest, string>>;

interface RunFormProps {
  defaultAgentId: string;
  disabled: boolean;
  disabledReason: string | null;
  submitting: boolean;
  onSubmit: (payload: CreateRunRequest) => Promise<void>;
}

function validatePayload(payload: CreateRunRequest): FieldErrors {
  const errors: FieldErrors = {};

  if (!payload.agent_id.trim()) {
    errors.agent_id = "El agente es obligatorio.";
  }

  const datasetPath = payload.dataset_path.trim();
  if (!datasetPath) {
    errors.dataset_path = "La ruta del dataset es obligatoria.";
  } else if (LOCAL_URL_PATTERN.test(datasetPath)) {
    errors.dataset_path = "La ruta debe apuntar a un archivo local, no a una URL.";
  } else {
    const extension = datasetPath.includes(".") ? datasetPath.split(".").pop()?.toLowerCase() : "";
    if (!extension || !SUPPORTED_EXTENSIONS.has(extension)) {
      errors.dataset_path = "La ruta debe terminar en csv, xlsx o parquet.";
    }
  }

  if (!payload.user_prompt.trim()) {
    errors.user_prompt = "El prompt es obligatorio.";
  }

  return errors;
}

export function RunForm({
  defaultAgentId,
  disabled,
  disabledReason,
  submitting,
  onSubmit,
}: RunFormProps) {
  const [payload, setPayload] = useState<CreateRunRequest>({
    agent_id: defaultAgentId,
    dataset_path: "",
    user_prompt: "",
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  useEffect(() => {
    setPayload((current) => ({
      ...current,
      agent_id: defaultAgentId,
    }));
  }, [defaultAgentId]);

  const submitLabel = useMemo(() => {
    if (submitting) {
      return "Ejecutando runâ€¦";
    }
    return "Lanzar run";
  }, [submitting]);

  function updateField<Key extends keyof CreateRunRequest>(field: Key, value: CreateRunRequest[Key]) {
    setPayload((current) => ({
      ...current,
      [field]: value,
    }));
    setFieldErrors((current) => ({
      ...current,
      [field]: undefined,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validatePayload(payload);
    setFieldErrors(nextErrors);
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
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Run</p>
          <h2>Formulario principal</h2>
        </div>
      </div>

      <form className="run-form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="form-field">
          <span>Agente</span>
          <select
            aria-label="Agente"
            name="agent_id"
            value={payload.agent_id}
            onChange={(event) => updateField("agent_id", event.target.value)}
            disabled
          >
            <option value="data_analyst">data_analyst</option>
          </select>
        </label>

        <label className="form-field">
          <span>Ruta local del dataset</span>
          <input
            aria-label="Ruta local del dataset"
            name="dataset_path"
            placeholder="DatasetV1/Walmart_Sales.csv"
            value={payload.dataset_path}
            onChange={(event) => updateField("dataset_path", event.target.value)}
            disabled={submitting}
          />
          {fieldErrors.dataset_path ? <small className="field-error">{fieldErrors.dataset_path}</small> : null}
        </label>

        <label className="form-field">
          <span>Prompt</span>
          <textarea
            aria-label="Prompt"
            name="user_prompt"
            rows={5}
            placeholder="Resume los hallazgos principales"
            value={payload.user_prompt}
            onChange={(event) => updateField("user_prompt", event.target.value)}
            disabled={submitting}
          />
          {fieldErrors.user_prompt ? <small className="field-error">{fieldErrors.user_prompt}</small> : null}
        </label>

        {disabledReason ? <p className="submit-help">{disabledReason}</p> : null}

        <button type="submit" className="primary-button" disabled={disabled || submitting}>
          {submitLabel}
        </button>
      </form>
    </section>
  );
}
