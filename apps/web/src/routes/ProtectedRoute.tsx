import { Navigate, Outlet, useLocation } from "react-router";

import { useAuth } from "../features/auth/AuthProvider";
import type { Role } from "../types/auth";

export function ProtectedRoute({ roles }: { roles?: Role[] }) {
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
  if (roles && !principal.roles.some((role) => roles.includes(role))) {
    return (
      <p className="alert alert-error" role="alert">
        No tiene permisos para ver esta sección.
      </p>
    );
  }
  return <Outlet />;
}
