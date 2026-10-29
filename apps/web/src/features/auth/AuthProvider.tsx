import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getCurrentPrincipal, login as loginRequest } from "../../services/authService";
import { clearToken, replaceToken, SESSION_EXPIRED_EVENT, setToken } from "../../services/session";
import type { LoginResponse, Principal, Role } from "../../types/auth";
import { tieneRol } from "./roles";

export interface AuthState {
  status: "cargando" | "autenticado" | "anonimo";
  principal: Principal | null;
}

export interface AuthContextValue extends AuthState {
  login: (usuario: string, clave: string, recordar: boolean) => Promise<void>;
  logout: () => void;
  /** Sesión renovada por la API (p. ej. tras cambiar la contraseña). */
  actualizarSesion: (response: LoginResponse) => void;
  /** ¿El usuario actual tiene alguno de los roles indicados? */
  tiene: (roles: readonly Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const ANONIMO: AuthState = { status: "anonimo", principal: null };

/**
 * Sesión de la aplicación. Al cargar consulta `/auth/me` con el token guardado (si existe);
 * en AUTH_MODE=development la API responde con el usuario ficticio aunque no haya token.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "cargando", principal: null });

  useEffect(() => {
    const controller = new AbortController();
    getCurrentPrincipal(controller.signal)
      .then((principal) => setState({ status: "autenticado", principal }))
      .catch(() => {
        if (controller.signal.aborted) return;
        clearToken();
        setState(ANONIMO);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const onExpired = () => setState(ANONIMO);
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, []);

  const login = useCallback(async (usuario: string, clave: string, recordar: boolean) => {
    const response = await loginRequest(usuario, clave);
    setToken(response.token, recordar);
    setState({ status: "autenticado", principal: response.principal });
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setState(ANONIMO);
  }, []);

  const actualizarSesion = useCallback((response: LoginResponse) => {
    replaceToken(response.token);
    setState({ status: "autenticado", principal: response.principal });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      logout,
      actualizarSesion,
      tiene: (roles) => (state.principal ? tieneRol(state.principal.roles, roles) : false),
    }),
    [state, login, logout, actualizarSesion],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  return context;
}
