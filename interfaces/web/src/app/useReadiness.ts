import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchReadiness, normalizeUnknownError } from "../api/client";
import type { ApiError, ReadinessState } from "../api/types";

interface UseReadinessState {
  readiness: ReadinessState | null;
  error: ApiError | null;
  isLoading: boolean;
  canSubmit: boolean;
  blockedReason: string | null;
  refresh: () => Promise<void>;
}

export function useReadiness(): UseReadinessState {
  const [readiness, setReadiness] = useState<ReadinessState | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const nextReadiness = await fetchReadiness();
      setReadiness(nextReadiness);
    } catch (nextError) {
      setReadiness(null);
      setError(normalizeUnknownError(nextError));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const blockedReason = useMemo(() => {
    if (isLoading) {
      return "Cargando estado operativo…";
    }
    if (error) {
      return "No se pudo cargar el estado operativo de la API local.";
    }
    if (!readiness?.application.ready) {
      return "La aplicacion local no esta lista todavia.";
    }
    if (!readiness.provider.ready) {
      return "El proveedor local no esta listo. Revisa la seccion de readiness antes de lanzar el run.";
    }
    return null;
  }, [error, isLoading, readiness]);

  return {
    readiness,
    error,
    isLoading,
    canSubmit: blockedReason === null,
    blockedReason,
    refresh,
  };
}