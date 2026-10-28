import { Navigate, Outlet, useLocation } from "react-router";

import { useAuth } from "../features/auth/AuthProvider";
import { tieneRol } from "../features/auth/roles";
import type { Role } from "../types/auth";

export function ProtectedRoute({ roles }: { roles?: readonly Role[] }) {
  const { status, principal } = useAuth();
  const location = useLocation();

  if (status === "cargando") {
    return (
      <p className="muted" role="status">
        Verificando sesión…
      </p>
    );
  }
  if (!principal) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (roles && !tieneRol(principal.roles, roles)) {
    return (
      <p className="alert alert-error" role="alert">
        No tiene permisos para ver esta sección.
      </p>
    );
  }
  return <Outlet />;
}
