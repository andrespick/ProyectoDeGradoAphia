import { Info, UserPlus, X } from "lucide-react";
import { type FormEvent, useCallback, useState } from "react";
import { Link, Outlet, useLocation } from "react-router";

import { Field } from "../components/Field";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { Segmented } from "../components/Segmented";
import { useAuth } from "../features/auth/AuthProvider";
import { ELIMINACION, ESCRITURA } from "../features/auth/roles";
import { type Modulo, MODULOS } from "../features/personas/modulos";
import { PersonasTable } from "../features/personas/PersonasTable";
import { useResumen } from "../features/resumen/useResumen";
import { type ListParams, usePagedList } from "../hooks/usePagedList";
import { errorMessage } from "../services/apiClient";
import { deletePersona, listPersonas } from "../services/personasService";
import type { Papel, Persona } from "../types/persona";

const PAPELES_SEGMENTOS = [
  { value: "", label: "Todos" },
  { value: "arrendatario", label: "Arrendatarios" },
  { value: "propietario", label: "Propietarios" },
  { value: "codeudor", label: "Codeudores" },
] as const;

const FETCHERS: Record<Modulo, (params: ListParams, signal: AbortSignal) => ReturnType<typeof listPersonas>> = {
  clientes: (params, signal) => listPersonas(MODULOS.clientes.api, params, signal),
  propietarios: (params, signal) => listPersonas(MODULOS.propietarios.api, params, signal),
  codeudores: (params, signal) => listPersonas(MODULOS.codeudores.api, params, signal),
};

export interface PersonasOutletContext {
  onSaved: (mensaje: string) => void;
}

export function PersonasListPage({ modulo }: { modulo: Modulo }) {
  const config = MODULOS[modulo];
  const { tiene } = useAuth();
  const location = useLocation();
  const lista = usePagedList(FETCHERS[modulo], { filtros: config.filtros });
  const resumen = useResumen();
  const [q, setQ] = useState(lista.filtros.q ?? "");
  const [correo, setCorreo] = useState(lista.filtros.correo ?? "");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const recargar = useCallback(() => {
    lista.reload();
    resumen.reload();
  }, [lista, resumen]);

  function buscar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    lista.setFiltros({ q: q.trim() || null, correo: correo.trim() || null });
  }

  async function eliminar(persona: Persona) {
    if (!window.confirm(`¿Eliminar a ${persona.nombre}? Esta acción no se puede deshacer.`)) return;
    setMensaje(null);
    setErrorAccion(null);
    try {
      await deletePersona(config.api, persona.id);
      setMensaje(`${persona.nombre} se eliminó correctamente.`);
      recargar();
    } catch (error) {
      setErrorAccion(errorMessage(error));
    }
  }

  const context: PersonasOutletContext = {
    onSaved: (texto) => {
      setMensaje(texto);
      recargar();
    },
  };
  const personas = resumen.resumen?.personas;
  const Icon = config.icon;

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Módulos operativos</span>
        <span>{config.titulo}</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <Icon size={20} />
          </span>
          <div>
            <h1>
              {config.titulo}
              {personas && (
                <span className="badge badge-muted">
                  {modulo === "clientes" ? personas.total : modulo === "propietarios" ? personas.propietarios : personas.codeudores}{" "}
                  en total
                </span>
              )}
            </h1>
            <p>{config.descripcion}</p>
          </div>
        </div>
        {tiene(ESCRITURA) && (
          <div className="actions">
            <Link to={{ pathname: `${config.ruta}/nuevo`, search: location.search }} className="button-link">
              <UserPlus size={18} aria-hidden="true" /> Registrar {config.singular}
            </Link>
          </div>
        )}
      </header>

      {modulo === "propietarios" && (
        <p className="alert alert-info">
          <Info size={16} aria-hidden="true" /> Un propietario con inmuebles vinculados no se puede
          eliminar: primero reasigne o elimine sus inmuebles.
        </p>
      )}

      {personas && (
        <section className="kpi-grid" aria-label="Indicadores">
          {modulo === "clientes" && (
            <>
              <KpiCard etiqueta="Arrendatarios" valor={personas.arrendatarios} tono="ok" />
              <KpiCard etiqueta="Propietarios" valor={personas.propietarios} tono="error" />
              <KpiCard etiqueta="Codeudores" valor={personas.codeudores} tono="info" />
              <KpiCard etiqueta="Clientes registrados" valor={personas.total} detalle="personas con al menos un papel" />
            </>
          )}
          {modulo === "propietarios" && resumen.resumen && (
            <>
              <KpiCard etiqueta="Propietarios" valor={personas.propietarios} tono="error" />
              <KpiCard etiqueta="Inmuebles registrados" valor={resumen.resumen.inmuebles.total} detalle="en el portafolio" />
            </>
          )}
          {modulo === "codeudores" && resumen.resumen && (
            <>
              <KpiCard etiqueta="Codeudores" valor={personas.codeudores} tono="info" />
              <KpiCard
                etiqueta="Vínculos en contratos"
                valor={resumen.resumen.contratos.codeudores_vinculados}
                detalle="codeudores asociados a contratos"
              />
            </>
          )}
        </section>
      )}

      {mensaje && (
        <p className="alert alert-success" role="status">
          {mensaje}
        </p>
      )}
      {errorAccion && (
        <p className="alert alert-error" role="alert">
          {errorAccion}
        </p>
      )}

      <form className="filters" onSubmit={buscar} role="search" aria-label={`Filtrar ${config.plural}`}>
        <Field
          id={`${modulo}-q`}
          label="Buscar"
          type="search"
          placeholder="Nombre o identificación"
          value={q}
          className="filters-search"
          onChange={setQ}
        />
        {modulo === "clientes" && (
          <Segmented
            label="Tipo de cliente"
            value={(lista.filtros.papel as Papel | undefined) ?? ""}
            options={PAPELES_SEGMENTOS}
            onChange={(value) => lista.setFiltros({ papel: value || null })}
          />
        )}
        {modulo === "propietarios" && (
          <Field id="propietarios-correo" label="Correo" type="search" value={correo} onChange={setCorreo} />
        )}
        {modulo === "codeudores" && lista.filtros.contrato_id && (
          <span className="chip">
            Contrato #{lista.filtros.contrato_id}
            <button type="button" aria-label="Quitar filtro de contrato" onClick={() => lista.setFiltros({ contrato_id: null })}>
              <X size={14} aria-hidden="true" />
            </button>
          </span>
        )}
        <button type="submit" className="secondary">
          Buscar
        </button>
      </form>

      <section className="card" aria-label={`Listado de ${config.plural}`}>
        <PersonasTable
          modulo={modulo}
          items={lista.items}
          loading={lista.loading}
          error={lista.error}
          puedeEditar={tiene(ESCRITURA)}
          puedeEliminar={tiene(ELIMINACION)}
          onRetry={lista.reload}
          onEliminar={(persona) => void eliminar(persona)}
        />
        <Pagination
          total={lista.total}
          limit={lista.limit}
          offset={lista.offset}
          onOffsetChange={lista.setOffset}
          onLimitChange={lista.setLimit}
          etiqueta={config.plural}
        />
      </section>

      <Outlet context={context} />
    </>
  );
}
