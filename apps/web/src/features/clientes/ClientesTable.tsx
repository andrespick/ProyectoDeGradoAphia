import type { Cliente } from "../../types/cliente";

interface ClientesTableProps {
  items: Cliente[];
  total: number;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

const dateFormat = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Bogota",
});

export function ClientesTable({ items, total, loading, error, onRetry }: ClientesTableProps) {
  if (error) {
    return (
      <div className="alert alert-error" role="alert">
        <p>{error}</p>
        <button type="button" className="secondary" onClick={onRetry}>
          Reintentar
        </button>
      </div>
    );
  }
  if (loading && items.length === 0) {
    return (
      <p className="muted" role="status">
        Cargando clientes…
      </p>
    );
  }
  if (items.length === 0) {
    return <p className="muted">No hay clientes registrados todavía.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <caption>
          {total} cliente{total === 1 ? "" : "s"} registrado{total === 1 ? "" : "s"}
        </caption>
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Nombre</th>
            <th scope="col">Correo</th>
            <th scope="col">Creado</th>
          </tr>
        </thead>
        <tbody>
          {items.map((cliente) => (
            <tr key={cliente.id}>
              <td>{cliente.id}</td>
              <td>{cliente.nombre}</td>
              <td className="wrap-anywhere">{cliente.correo}</td>
              <td className="nowrap">
                <time dateTime={cliente.creado_en}>
                  {dateFormat.format(new Date(cliente.creado_en))}
                </time>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
