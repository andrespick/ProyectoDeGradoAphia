import { useCallback, useEffect, useState } from "react";

import { errorMessage } from "../../services/apiClient";
import { getResumen } from "../../services/resumenService";
import type { Resumen } from "../../types/resumen";

interface ResumenState {
  resumen: Resumen | null;
  error: string | null;
}

/** Conteos para el tablero y las tarjetas de indicadores de cada módulo. */
export function useResumen() {
  const [state, setState] = useState<ResumenState>({ resumen: null, error: null });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getResumen(controller.signal)
      .then((resumen) => setState({ resumen, error: null }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setState({ resumen: null, error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [version]);

  const reload = useCallback(() => setVersion((current) => current + 1), []);
  return { ...state, reload };
}
