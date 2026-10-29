import { Building2, Plus, X } from "lucide-react";
import { type FormEvent, useCallback, useState } from "react";
import { Link, Outlet, useLocation } from "react-router";

import { AyudaLink } from "../components/AyudaLink";
import { Field } from "../components/Field";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { SelectField } from "../components/SelectField";
import { useAuth } from "../features/auth/AuthProvider";
import { ELIMINACION, ESCRITURA } from "../features/auth/roles";
import { useCatalogos } from "../features/catalogos/useCatalogos";
import { InmueblesTable } from "../features/inmuebles/InmueblesTable";
import { PersonaPicker } from "../features/personas/PersonaPicker";
import { useResumen } from "../features/resumen/useResumen";
import { usePagedList } from "../hooks/usePagedList";
import { errorMessage } from "../services/apiClient";
import { deleteInmueble, listInmuebles } from "../services/inmueblesService";
import type { Inmueble } from "../types/inmueble";
import type { PersonaResumen } from "../types/persona";

const FILTROS = ["q", "estado", "ciudad", "propietario_id"] as const;

export interface InmueblesOutletContext {
  onSaved: (mensaje: string) => void;
}

export function InmueblesPage() {
  const { tiene } = useAuth();
  const location = useLocation();
  const { catalogos } = useCatalogos();
  const lista = usePagedList(listInmuebles, { filtros: FILTROS });
  const resumen = useResumen();
  const [q, setQ] = useState(lista.filtros.q ?? "");
  const [ciudad, setCiudad] = useState(lista.filtros.ciudad ?? "");
  const [propietario, setPropietario] = useState<PersonaResumen | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const recargar = useCallback(() => {
    lista.reload();
    resumen.reload();
  }, [lista, resumen]);

  function buscar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    lista.setFiltros({ q: q.trim() || null, ciudad: ciudad.trim() || null });
  }

  function restablecer() {
    setQ("");
    setCiudad("");
    setPropietario(null);
    lista.setFiltros({ q: null, ciudad: null, estado: null, propietario_id: null });
  }

  async function eliminar(inmueble: Inmueble) {
    if (!window.confirm(`¿Eliminar el inmueble ${inmueble.direccion}? Irá a la papelera; solo el Administrador de Sistemas puede restaurarlo.`)) return;
    setMensaje(null);
    setErrorAccion(null);
    try {
      await deleteInmueble(inmueble.id);
      setMensaje("Inmueble eliminado correctamente.");
      recargar();
    } catch (error) {
      setErrorAccion(errorMessage(error));
    }
  }

  const context: InmueblesOutletContext = {
    onSaved: (texto) => {
      setMensaje(texto);
      recargar();
    },
  };
  const estados = (catalogos?.estados_ocupacion ?? []).map((e) => ({ value: e.codigo, label: e.nombre }));
  const aplicados = Object.entries(lista.filtros);
  const inmuebles = resumen.resumen?.inmuebles;

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Módulos operativos</span>
        <span>Gestión de inmuebles</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <Building2 size={20} />
          </span>
          <div>
            <h1>
              Portafolio de inmuebles
              {inmuebles && <span className="badge badge-muted">{inmuebles.total} activos</span>}
            </h1>
            <p>Registro catastral, titularidad y contratos de servicios públicos de cada inmueble.</p>
          </div>
        </div>
        <div className="actions">
          {tiene(ESCRITURA) && (
            <Link to={{ pathname: "/inmuebles/nuevo", search: location.search }} className="button-link">
              <Plus size={18} aria-hidden="true" /> Registrar inmueble
            </Link>
          )}
          <AyudaLink seccion="inmuebles" etiqueta="inmuebles" />
        </div>
      </header>

      {inmuebles && (
        <section className="kpi-grid" aria-label="Indicadores">
          <KpiCard etiqueta="Total inmuebles" valor={inmuebles.total} detalle="en el portafolio" />
          <KpiCard etiqueta="Ocupados" valor={inmuebles.ocupados} detalle="con arrendatario" tono="ok" />
          <KpiCard etiqueta="Disponibles" valor={inmuebles.disponibles} detalle="listos para arrendar" tono="warn" />
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

      <form className="filters" onSubmit={buscar} role="search" aria-label="Filtrar inmuebles">
        <Field
          id="inmuebles-q"
          label="Buscar"
          type="search"
          placeholder="Dirección o matrícula"
          value={q}
          className="filters-search"
          onChange={setQ}
        />
        <SelectField
          id="inmuebles-estado"
          label="Estado"
          value={lista.filtros.estado ?? ""}
          options={estados}
          placeholder="Todos"
          onChange={(value) => lista.setFiltros({ estado: value || null })}
        />
        <Field id="inmuebles-ciudad" label="Ciudad" type="search" value={ciudad} list="ciudades-filtro" onChange={setCiudad} />
        <datalist id="ciudades-filtro">
          {(catalogos?.ciudades ?? []).map((c) => (
            <option key={c.id} value={c.nombre} />
          ))}
        </datalist>
        <button type="submit" className="secondary">
          Buscar
        </button>
        <div className="filters-row">
          <PersonaPicker
            idPrefix="inmuebles-propietario"
            label="Propietario"
            papel="propietario"
            value={propietario ?? (lista.filtros.propietario_id ? propietarioDesdeUrl(lista.filtros.propietario_id) : null)}
            soloBuscar
            onChange={(persona) => {
              setPropietario(persona);
              lista.setFiltros({ propietario_id: persona ? String(persona.id) : null });
            }}
          />
        </div>
        {aplicados.length > 0 && (
          <div className="chip-list filters-row">
            <span className="muted">Filtros aplicados:</span>
            {aplicados.map(([clave, valor]) => (
              <span key={clave} className="chip">
                {ETIQUETAS[clave] ?? clave}: {valor}
                <button type="button" aria-label={`Quitar filtro ${ETIQUETAS[clave] ?? clave}`} onClick={() => quitar(clave)}>
                  <X size={14} aria-hidden="true" />
                </button>
              </span>
            ))}
            <button type="button" className="link" onClick={restablecer}>
              Restablecer filtros
            </button>
          </div>
        )}
      </form>

      <section className="card" aria-label="Listado de inmuebles">
        <InmueblesTable
          items={lista.items}
          loading={lista.loading}
          error={lista.error}
          puedeEditar={tiene(ESCRITURA)}
          puedeEliminar={tiene(ELIMINACION)}
          onRetry={lista.reload}
          onEliminar={(inmueble) => void eliminar(inmueble)}
        />
        <Pagination
          total={lista.total}
          limit={lista.limit}
          offset={lista.offset}
          onOffsetChange={lista.setOffset}
          onLimitChange={lista.setLimit}
          etiqueta="inmuebles"
        />
      </section>

      <Outlet context={context} />
    </>
  );

  function quitar(clave: string) {
    if (clave === "q") setQ("");
    if (clave === "ciudad") setCiudad("");
    if (clave === "propietario_id") setPropietario(null);
    lista.setFiltros({ [clave]: null });
  }
}

const ETIQUETAS: Record<string, string> = {
  q: "Búsqueda",
  estado: "Estado",
  ciudad: "Ciudad",
  propietario_id: "Propietario",
};

function propietarioDesdeUrl(id: string): PersonaResumen {
  return { id: Number(id), nombre: `Propietario #${id}`, tipo_identificacion: null, identificacion: null, telefono: null, correo: null };
}
