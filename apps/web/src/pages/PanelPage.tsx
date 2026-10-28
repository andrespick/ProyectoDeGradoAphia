import { useAuth } from "../features/auth/AuthProvider";

export function PanelPage() {
  const { principal } = useAuth();
  return (
    <section className="card" aria-labelledby="panel-titulo">
      <h1 id="panel-titulo">Panel</h1>
      <p>Ruta protegida de ejemplo. Requiere rol admin o asesor.</p>
      {principal && (
        <dl className="meta">
          <div>
            <dt>Usuario</dt>
            <dd>{principal.nombre}</dd>
          </div>
          <div>
            <dt>Roles</dt>
            <dd>{principal.roles.join(", ")}</dd>
          </div>
          <div>
            <dt>Modo</dt>
            <dd>{principal.modo === "development" ? "desarrollo (ficticio)" : principal.modo}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}
