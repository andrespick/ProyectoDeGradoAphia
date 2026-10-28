import { StatusIndicator } from "../components/StatusIndicator";
import { ClienteForm } from "../features/clientes/ClienteForm";
import { ClientesTable } from "../features/clientes/ClientesTable";
import { useClientes } from "../features/clientes/useClientes";
import { useApiStatus } from "../hooks/useApiStatus";

const RUNTIME_LABELS = { workers: "Cloudflare Workers", asgi: "ASGI (Uvicorn)" } as const;

export function HomePage() {
  const api = useApiStatus();
  const clientes = useClientes();

  return (
    <>
      <section className="card" aria-labelledby="estado-titulo">
        <div className="card-header">
          <h1 id="estado-titulo">Estado del sistema</h1>
          <button type="button" className="secondary" onClick={api.refresh}>
            Verificar de nuevo
          </button>
        </div>
        <StatusIndicator status={api.status} />
        {api.health && (
          <dl className="meta">
            <div>
              <dt>Entorno</dt>
              <dd>{api.health.environment}</dd>
            </div>
            <div>
              <dt>Runtime</dt>
              <dd>{RUNTIME_LABELS[api.health.runtime]}</dd>
            </div>
            <div>
              <dt>Versión de la API</dt>
              <dd>{api.health.version}</dd>
            </div>
          </dl>
        )}
        {api.error && <p className="muted">{api.error}</p>}
      </section>

      <div className="grid">
        <section className="card" aria-labelledby="form-titulo">
          <h2 id="form-titulo">Nuevo cliente de prueba</h2>
          <p className="muted">Use únicamente datos ficticios.</p>
          <ClienteForm onSubmit={clientes.create} />
        </section>
        <section className="card" aria-labelledby="lista-titulo">
          <h2 id="lista-titulo">Clientes</h2>
          <ClientesTable
            items={clientes.items}
            total={clientes.total}
            loading={clientes.loading}
            error={clientes.error}
            onRetry={clientes.reload}
          />
        </section>
      </div>
    </>
  );
}
