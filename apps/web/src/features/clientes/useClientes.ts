import { useCallback, useEffect, useState } from "react";

import { errorMessage } from "../../services/apiClient";
import { createCliente, listClientes } from "../../services/clientesService";
import type { Cliente, ClienteCreate } from "../../types/cliente";

interface ClientesState {
  items: Cliente[];
  total: number;
  loading: boolean;
  error: string | null;
}

export function useClientes(pageSize = 20) {
  const [state, setState] = useState<ClientesState>({
    items: [],
    total: 0,
    loading: true,
    error: null,
  });

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setState((current) => ({ ...current, loading: true, error: null }));
      try {
        const page = await listClientes({ limit: pageSize }, signal);
        setState({ items: page.items, total: page.total, loading: false, error: null });
      } catch (error) {
        if (signal?.aborted) return;
        setState((current) => ({ ...current, loading: false, error: errorMessage(error) }));
      }
    },
    [pageSize],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const create = useCallback(
    async (input: ClienteCreate) => {
      const created = await createCliente(input);
      await load();
      return created;
    },
    [load],
  );

  return { ...state, reload: () => void load(), create };
}
