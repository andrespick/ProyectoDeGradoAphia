import type { ApiStatus } from "../hooks/useApiStatus";

const LABELS: Record<ApiStatus, string> = {
  verificando: "Verificando conexión…",
  conectada: "API conectada",
  degradada: "API sin base de datos",
  sin_conexion: "API sin conexión",
};

export function StatusIndicator({ status }: { status: ApiStatus }) {
  return (
    <p className={`status status-${status}`} role="status" aria-live="polite">
      <span className="status-dot" aria-hidden="true" />
      {LABELS[status]}
    </p>
  );
}
