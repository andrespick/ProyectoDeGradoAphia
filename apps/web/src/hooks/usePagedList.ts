import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router";

import { errorMessage } from "../services/apiClient";
import type { Page } from "../types/api";

export interface ListParams {
  limit: number;
  offset: number;
  filtros: Record<string, string>;
}

interface Options {
  /** Nombres de los filtros que viven en la URL (p. ej. ["q", "correo"]). */
  filtros: readonly string[];
  limitPorDefecto?: number;
}

interface ListState<T> {
  items: T[];
  total: number;
  loading: boolean;
  error: string | null;
}

/**
 * Listado paginado cuyo estado (filtros, límite y desplazamiento) vive en la query string,
 * de modo que recargar o compartir la URL conserva la vista. `fetcher` debe ser estable
 * (función de módulo o `useCallback`).
 */
export function usePagedList<T>(
  fetcher: (params: ListParams, signal: AbortSignal) => Promise<Page<T>>,
  { filtros: claves, limitPorDefecto = 20 }: Options,
) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, setState] = useState<ListState<T>>({
    items: [],
    total: 0,
    loading: true,
    error: null,
  });
  const [version, setVersion] = useState(0);

  const limit = clampInt(searchParams.get("limit"), limitPorDefecto, 1, 100);
  const offset = clampInt(searchParams.get("offset"), 0, 0, 100_000);
  const clavesKey = claves.join(",");
  const filtros = useMemo(() => {
    const result: Record<string, string> = {};
    for (const clave of clavesKey.split(",").filter(Boolean)) {
      const value = searchParams.get(clave);
      if (value) result[clave] = value;
    }
    return result;
  }, [searchParams, clavesKey]);

  useEffect(() => {
    const controller = new AbortController();
    setState((current) => ({ ...current, loading: true, error: null }));
    fetcher({ limit, offset, filtros }, controller.signal)
      .then((page) => setState({ items: page.items, total: page.total, loading: false, error: null }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState((current) => ({ ...current, loading: false, error: errorMessage(error) }));
      });
    return () => controller.abort();
  }, [fetcher, limit, offset, filtros, version]);

  const setFiltros = useCallback(
    (cambios: Record<string, string | null | undefined>) => {
      setSearchParams((previous) => {
        const next = new URLSearchParams(previous);
        for (const [clave, value] of Object.entries(cambios)) {
          if (value) next.set(clave, value);
          else next.delete(clave);
        }
        next.delete("offset");
        return next;
      });
    },
    [setSearchParams],
  );

  const setOffset = useCallback(
    (value: number) => {
      setSearchParams((previous) => {
        const next = new URLSearchParams(previous);
        if (value > 0) next.set("offset", String(value));
        else next.delete("offset");
        return next;
      });
    },
    [setSearchParams],
  );

  const setLimit = useCallback(
    (value: number) => {
      setSearchParams((previous) => {
        const next = new URLSearchParams(previous);
        next.set("limit", String(value));
        next.delete("offset");
        return next;
      });
    },
    [setSearchParams],
  );

  const reload = useCallback(() => setVersion((current) => current + 1), []);

  return { ...state, limit, offset, filtros, setFiltros, setOffset, setLimit, reload };
}

function clampInt(raw: string | null, fallback: number, min: number, max: number): number {
  const value = Number.parseInt(raw ?? "", 10);
  if (Number.isNaN(value)) return fallback;
  return Math.min(max, Math.max(min, value));
}
