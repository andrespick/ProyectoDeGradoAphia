import { createContext, type ReactNode, useContext, useEffect, useState } from "react";

import { getCurrentPrincipal } from "../../services/authService";
import type { Principal } from "../../types/auth";

/**
 * Estado de autenticación de la aplicación.
 *
 * FASE ACTUAL: no hay inicio de sesión real. La API solo reconoce el usuario ficticio de
 * desarrollo (AUTH_MODE=development); en cualquier otro entorno responde 401 y la
 * aplicación queda como "anonimo". Aquí se conectará el proveedor de identidad.
 */
export interface AuthState {
  status: "cargando" | "autenticado" | "anonimo";
  principal: Principal | null;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "cargando", principal: null });

  useEffect(() => {
    const controller = new AbortController();
    getCurrentPrincipal(controller.signal)
      .then((principal) => setState({ status: "autenticado", principal }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ status: "anonimo", principal: null });
      });
    return () => controller.abort();
  }, []);

  return <AuthContext.Provider value={state}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  return context;
}
