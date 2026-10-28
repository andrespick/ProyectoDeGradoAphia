import { Pencil, Trash2 } from "lucide-react";
import { Link } from "react-router";

import { BADGE_ESTADO, type Inmueble, NOMBRE_ESTADO } from "../../types/inmueble";
import { formatearMoneda } from "../../utils/formato";

interface InmueblesTableProps {
  items: Inmueble[];
  loading: boolean;
  error: string | null;
  puedeEditar: boolean;
  puedeEliminar: boolean;
  onRetry: () => void;
  onEliminar: (inmueble: Inmueble) => void;
}

export function InmueblesTable({
  items,
  loading,
  error,
  puedeEditar,
  puedeEliminar,
  onRetry,
  onEliminar,
}: InmueblesTableProps) {
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
        Cargando inmuebles…
      </p>
    );
  }
  if (items.length === 0) {
    return <p className="empty-state">No hay inmuebles que coincidan con la búsqueda.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Matrícula</th>
            <th scope="col">Inmueble</th>
            <th scope="col">Propietarios</th>
            <th scope="col" className="num">
              Canon mensual
            </th>
            <th scope="col">Estado</th>
            <th scope="col">Servicios públicos</th>
            <th scope="col">
              <span className="visually-hidden">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((inmueble) => (
            <tr key={inmueble.id}>
              <td className="nowrap">{inmueble.matricula ?? "—"}</td>
              <td>
                <span className="cell-title">{inmueble.direccion}</span>
                <span className="cell-sub">{inmueble.ciudad ?? "Sin ciudad"}</span>
              </td>
              <td>
                {inmueble.propietarios.map((p) => (
                  <Link key={p.id} to={`/propietarios/${p.id}`} className="cell-link">
                    {p.nombre}
                  </Link>
                ))}
              </td>
              <td className="num">{formatearMoneda(inmueble.canon)}</td>
              <td>
                {inmueble.estado ? (
                  <span className={`badge ${BADGE_ESTADO[inmueble.estado] ?? "badge-muted"}`}>
                    {NOMBRE_ESTADO[inmueble.estado] ?? inmueble.estado}
                  </span>
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td>
                <span className="chip-list">
                  {inmueble.servicios.length === 0 && <span className="muted">—</span>}
                  {inmueble.servicios.map((s) => (
                    <span key={s.id} className="chip" title={s.proveedor ?? undefined}>
                      {s.tipo ? `${s.tipo} · ` : ""}
                      {s.numero_contrato}
                    </span>
                  ))}
                </span>
              </td>
              <td>
                <span className="row-actions">
                  {puedeEditar && (
                    <Link to={`/inmuebles/${inmueble.id}/editar`} aria-label={`Editar ${inmueble.direccion}`}>
                      <Pencil size={16} aria-hidden="true" /> Editar
                    </Link>
                  )}
                  {puedeEliminar && (
                    <button
                      type="button"
                      className="danger"
                      aria-label={`Eliminar ${inmueble.direccion}`}
                      onClick={() => onEliminar(inmueble)}
                    >
                      <Trash2 size={16} aria-hidden="true" /> Eliminar
                    </button>
                  )}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
