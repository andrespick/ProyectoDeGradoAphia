import { ScrollText } from "lucide-react";
import { type FormEvent, useState } from "react";

import { AyudaLink } from "../components/AyudaLink";
import { Field } from "../components/Field";
import { Pagination } from "../components/Pagination";
import { SelectField } from "../components/SelectField";
import { ACCIONES, ENTIDADES } from "../features/administracion/etiquetas";
import { usePagedList } from "../hooks/usePagedList";
import { listAuditoria } from "../services/administracionService";
import { formatearFechaHora } from "../utils/formato";

const FILTROS = ["q", "accion", "entidad", "desde", "hasta"] as const;
const opciones = (mapa: Record<string, string>) =>
  Object.entries(mapa).map(([value, label]) => ({ value, label }));

export function AuditoriaPage() {
  const lista = usePagedList(listAuditoria, { filtros: FILTROS });
  const [q, setQ] = useState(lista.filtros.q ?? "");
  const [desde, setDesde] = useState(lista.filtros.desde ?? "");
  const [hasta, setHasta] = useState(lista.filtros.hasta ?? "");

  function buscar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    lista.setFiltros({ q: q.trim() || null, desde: desde || null, hasta: hasta || null });
  }

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Seguridad</span>
        <span>Auditoría</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <ScrollText size={20} />
          </span>
          <div>
            <h1>
              Auditoría
              <span className="badge badge-muted">{lista.total} eventos</span>
            </h1>
            <p>Quién inició sesión y quién creó, modificó o eliminó cada registro, y cuándo.</p>
          </div>
        </div>
        <div className="actions">
          <AyudaLink seccion="auditoria" etiqueta="la auditoría" />
        </div>
      </header>

      <form className="filters" onSubmit={buscar} role="search" aria-label="Filtrar eventos">
        <Field
          id="auditoria-q"
          label="Usuario"
          type="search"
          placeholder="Nombre o usuario"
          value={q}
          className="filters-search"
          onChange={setQ}
        />
        <SelectField
          id="auditoria-accion"
          label="Acción"
          value={lista.filtros.accion ?? ""}
          options={opciones(ACCIONES)}
          placeholder="Todas las acciones"
          onChange={(value) => lista.setFiltros({ accion: value || null })}
        />
        <SelectField
          id="auditoria-entidad"
          label="Registro"
          value={lista.filtros.entidad ?? ""}
          options={opciones(ENTIDADES)}
          placeholder="Todos los registros"
          onChange={(value) => lista.setFiltros({ entidad: value || null })}
        />
        <Field id="auditoria-desde" label="Desde" type="date" value={desde} onChange={setDesde} />
        <Field id="auditoria-hasta" label="Hasta" type="date" value={hasta} onChange={setHasta} />
        <button type="submit" className="secondary">
          Filtrar
        </button>
      </form>

      <section className="card" aria-label="Eventos de auditoría">
        {lista.error ? (
          <div className="alert alert-error" role="alert">
            <p>{lista.error}</p>
            <button type="button" className="secondary" onClick={lista.reload}>
              Reintentar
            </button>
          </div>
        ) : lista.loading && lista.items.length === 0 ? (
          <p className="muted" role="status">
            Cargando eventos…
          </p>
        ) : lista.items.length === 0 ? (
          <p className="empty-state">No hay eventos que coincidan con los filtros.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Fecha y hora</th>
                  <th scope="col">Usuario</th>
                  <th scope="col">Acción</th>
                  <th scope="col">Registro</th>
                  <th scope="col">Detalle</th>
                </tr>
              </thead>
              <tbody>
                {lista.items.map((evento) => (
                  <tr key={evento.id}>
                    <td className="nowrap">{formatearFechaHora(evento.fecha)}</td>
                    <td>
                      <span className="cell-title">{evento.actor_nombre ?? "Desconocido"}</span>
                      {evento.actor_usuario && <span className="cell-sub">@{evento.actor_usuario}</span>}
                    </td>
                    <td>
                      <span
                        className={`badge ${evento.accion.includes("fallido") || evento.accion === "cuenta_bloqueada" ? "badge-error" : "badge-muted"}`}
                      >
                        {ACCIONES[evento.accion] ?? evento.accion}
                      </span>
                    </td>
                    <td className="nowrap">
                      {evento.entidad ? (ENTIDADES[evento.entidad] ?? evento.entidad) : "—"}
                      {evento.entidad_id !== null && ` #${evento.entidad_id}`}
                    </td>
                    <td className="wrap-anywhere">{evento.detalle ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          total={lista.total}
          limit={lista.limit}
          offset={lista.offset}
          onOffsetChange={lista.setOffset}
          onLimitChange={lista.setLimit}
          etiqueta="eventos"
        />
      </section>
    </>
  );
}
