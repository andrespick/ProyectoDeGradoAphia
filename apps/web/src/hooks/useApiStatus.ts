import { useCallback, useEffect, useState } from "react";

import { errorMessage } from "../services/apiClient";
import { getHealth, getReady } from "../services/healthService";
import type { HealthResponse } from "../types/api";

export type ApiStatus = "verificando" | "conectada" | "degradada" | "sin_conexion";

interface ApiStatusState {
  status: ApiStatus;
  health: HealthResponse | null;
  error: string | null;
}

export function useApiStatus() {
  const [state, setState] = useState<ApiStatusState>({
    status: "verificando",
    health: null,
    error: null,
  });

  const check = useCallback(async (signal?: AbortSignal) => {
    setState((current) => ({ ...current, status: "verificando" }));
    try {
      const health = await getHealth(signal);
      const ready = await getReady(signal);
      const isReady = ready.status === "ready";
      setState({
        status: isReady ? "conectada" : "degradada",
        health,
        error: isReady ? null : "La API responde, pero la base de datos no está disponible.",
      });
    } catch (error) {
      if (signal?.aborted) return;
      setState({ status: "sin_conexion", health: null, error: errorMessage(error) });
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void check(controller.signal);
    return () => controller.abort();
  }, [check]);

  return { ...state, refresh: () => void check() };
}
