import { KeyRound, LockOpen, LogOut, Pencil, Trash2 } from "lucide-react";
import { Link } from "react-router";

import { Avatar } from "../../components/Avatar";
import type { Usuario } from "../../types/usuario";
import { NOMBRE_ROL } from "../auth/roles";

interface UsuariosTableProps {
  items: Usuario[];
  loading: boolean;
  error: string | null;
  /** Sujeto del usuario autenticado: no puede eliminarse ni desactivarse a sí mismo. */
  actorId: string;
  onRetry: () => void;
  onToggleActivo: (usuario: Usuario) => void;
  onDesbloquear: (usuario: Usuario) => void;
  onEliminar: (usuario: Usuario) => void;
  onRestablecerClave: (usuario: Usuario) => void;
  onCerrarSesiones: (usuario: Usuario) => void;
}

const ROL_BADGE = {
  admin_sistemas: "badge-primary",
  administrativo: "badge-muted",
  asesor: "badge-ok",
} as const;

export function UsuariosTable({
  items,
  loading,
  error,
  actorId,
  onRetry,
  onToggleActivo,
  onDesbloquear,
  onEliminar,
  onRestablecerClave,
  onCerrarSesiones,
}: UsuariosTableProps) {
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
        Cargando usuarios…
      </p>
    );
  }
  if (items.length === 0) {
    return <p className="empty-state">No hay usuarios que coincidan con la búsqueda.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Usuario</th>
            <th scope="col">Documento</th>
            <th scope="col">Correo</th>
            <th scope="col">Rol</th>
            <th scope="col">Estado</th>
            <th scope="col">Seguridad</th>
            <th scope="col">
              <span className="visually-hidden">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((usuario) => {
            const esActor = String(usuario.id) === actorId;
            return (
              <tr key={usuario.id}>
                <td>
                  <span className="cell-person">
                    <Avatar nombre={usuario.nombre} tono={usuario.bloqueada ? "primary" : "neutro"} />
                    <span>
                      <span className="cell-title">{usuario.nombre}</span>
                      <span className="cell-sub">@{usuario.usuario}</span>
                    </span>
                  </span>
                </td>
                <td className="nowrap">
                  {usuario.tipo_identificacion} {usuario.identificacion}
                </td>
                <td className="wrap-anywhere">{usuario.correo}</td>
                <td>
                  <span className={`badge ${ROL_BADGE[usuario.rol]}`}>{NOMBRE_ROL[usuario.rol]}</span>
                </td>
                <td>
                  {usuario.bloqueada ? (
                    <span className="badge badge-error">Bloqueada</span>
                  ) : (
                    <label className="switch">
                      <input
                        type="checkbox"
                        role="switch"
                        checked={usuario.activo}
                        disabled={esActor}
                        aria-label={`Cuenta de ${usuario.usuario} activa`}
                        onChange={() => onToggleActivo(usuario)}
                      />
                      {usuario.activo ? "Activo" : "Inactivo"}
                    </label>
                  )}
                </td>
                <td>
                  {usuario.bloqueada ? (
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => onDesbloquear(usuario)}
                    >
                      <LockOpen size={16} aria-hidden="true" /> Desbloquear
                    </button>
                  ) : (
                    <span className={usuario.intentos_fallidos > 0 ? "badge badge-warn" : "muted"}>
                      {usuario.intentos_fallidos} fallo{usuario.intentos_fallidos === 1 ? "" : "s"}
                    </span>
                  )}
                  {usuario.debe_cambiar_clave && <span className="badge badge-info">Clave temporal</span>}
                </td>
                <td>
                  <span className="row-actions">
                    <Link to={`/usuarios/${usuario.id}/editar`} aria-label={`Editar ${usuario.usuario}`}>
                      <Pencil size={16} aria-hidden="true" /> Editar
                    </Link>
                    <button
                      type="button"
                      className="secondary"
                      disabled={esActor}
                      aria-label={`Restablecer la clave de ${usuario.usuario}`}
                      title="Genera una clave temporal"
                      onClick={() => onRestablecerClave(usuario)}
                    >
                      <KeyRound size={16} aria-hidden="true" /> Clave
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      disabled={esActor}
                      aria-label={`Cerrar las sesiones de ${usuario.usuario}`}
                      title="Cierra sus sesiones abiertas"
                      onClick={() => onCerrarSesiones(usuario)}
                    >
                      <LogOut size={16} aria-hidden="true" /> Sesiones
                    </button>
                    <button
                      type="button"
                      className="danger"
                      disabled={esActor}
                      aria-label={`Eliminar ${usuario.usuario}`}
                      onClick={() => onEliminar(usuario)}
                    >
                      <Trash2 size={16} aria-hidden="true" /> Eliminar
                    </button>
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
