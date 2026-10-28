import { Eye, Pencil, Trash2 } from "lucide-react";
import { Link } from "react-router";

import { Avatar } from "../../components/Avatar";
import { BADGE_PAPEL, identificacionDe, NOMBRE_PAPEL, type Persona } from "../../types/persona";
import type { Modulo } from "./modulos";
import { MODULOS } from "./modulos";

interface PersonasTableProps {
  modulo: Modulo;
  items: Persona[];
  loading: boolean;
  error: string | null;
  puedeEditar: boolean;
  puedeEliminar: boolean;
  onRetry: () => void;
  onEliminar: (persona: Persona) => void;
}

export function enmascarar(numero: string): string {
  return `•••• ${numero.slice(-4)}`;
}

export function PersonasTable({
  modulo,
  items,
  loading,
  error,
  puedeEditar,
  puedeEliminar,
  onRetry,
  onEliminar,
}: PersonasTableProps) {
  const config = MODULOS[modulo];
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
        Cargando {config.plural}…
      </p>
    );
  }
  if (items.length === 0) {
    return <p className="empty-state">No hay {config.plural} que coincidan con la búsqueda.</p>;
  }
  const esPropietarios = modulo === "propietarios";
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Nombre</th>
            <th scope="col">Identificación</th>
            <th scope="col">Teléfono</th>
            <th scope="col">Tipo de cliente</th>
            {esPropietarios && <th scope="col">Cuenta bancaria</th>}
            {esPropietarios && <th scope="col">Inmuebles</th>}
            <th scope="col">
              <span className="visually-hidden">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((persona) => (
            <tr key={persona.id}>
              <td>
                <span className="cell-person">
                  <Avatar nombre={persona.nombre} tono={persona.papeles.includes("codeudor") ? "info" : "neutro"} />
                  <span>
                    <span className="cell-title">{persona.nombre}</span>
                    {persona.correo && <span className="cell-sub wrap-anywhere">{persona.correo}</span>}
                  </span>
                </span>
              </td>
              <td className="nowrap">{identificacionDe(persona)}</td>
              <td className="nowrap">{persona.telefono ?? "—"}</td>
              <td>
                <span className="chip-list">
                  {persona.papeles.map((papel) => (
                    <span key={papel} className={`badge ${BADGE_PAPEL[papel]}`}>
                      {NOMBRE_PAPEL[papel]}
                    </span>
                  ))}
                </span>
              </td>
              {esPropietarios && (
                <td>
                  {persona.cuenta_bancaria ? (
                    <>
                      <span className="cell-title">{persona.cuenta_bancaria.banco}</span>
                      <span className="cell-sub">
                        {persona.cuenta_bancaria.tipo} {enmascarar(persona.cuenta_bancaria.numero)}
                      </span>
                    </>
                  ) : (
                    <span className="muted">Sin cuenta</span>
                  )}
                </td>
              )}
              {esPropietarios && (
                <td>
                  <span className={`badge ${persona.total_inmuebles > 0 ? "badge-info" : "badge-muted"}`}>
                    {persona.total_inmuebles > 0
                      ? `${persona.total_inmuebles} inmueble${persona.total_inmuebles === 1 ? "" : "s"}`
                      : "Sin inmuebles"}
                  </span>
                </td>
              )}
              <td>
                <span className="row-actions">
                  <Link to={`${config.ruta}/${persona.id}`} aria-label={`Ver ${persona.nombre}`}>
                    <Eye size={16} aria-hidden="true" /> Ver
                  </Link>
                  {puedeEditar && (
                    <Link to={`${config.ruta}/${persona.id}/editar`} aria-label={`Editar ${persona.nombre}`}>
                      <Pencil size={16} aria-hidden="true" /> Editar
                    </Link>
                  )}
                  {puedeEliminar && (
                    <button
                      type="button"
                      className="danger"
                      aria-label={`Eliminar ${persona.nombre}`}
                      onClick={() => onEliminar(persona)}
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
