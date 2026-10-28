import { useEffect, useState } from "react";

import { errorMessage } from "../../services/apiClient";
import { getCatalogos } from "../../services/catalogosService";
import type { Catalogos } from "../../types/catalogos";

interface CatalogosState {
  catalogos: Catalogos | null;
  error: string | null;
}

export function useCatalogos() {
  const [state, setState] = useState<CatalogosState>({ catalogos: null, error: null });

  useEffect(() => {
    let active = true;
    getCatalogos()
      .then((catalogos) => {
        if (active) setState({ catalogos, error: null });
      })
      .catch((error: unknown) => {
        if (active) setState({ catalogos: null, error: errorMessage(error) });
      });
    return () => {
      active = false;
    };
  }, []);

  return { ...state, loading: state.catalogos === null && state.error === null };
}
