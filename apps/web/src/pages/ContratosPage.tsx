import { FileText, Plus, X } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useLocation } from "react-router";

import { Field } from "../components/Field";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { Segmented } from "../components/Segmented";
import { SelectField } from "../components/SelectField";
import { useAuth } from "../features/auth/AuthProvider";
import { ELIMINACION, ESCRITURA } from "../features/auth/roles";
import { useCatalogos } from "../features/catalogos/useCatalogos";
import { ContratosTable } from "../features/contratos/ContratosTable";
import { InmueblePicker } from "../features/contratos/InmueblePicker";
import { PersonaPicker } from "../features/personas/PersonaPicker";
import { useResumen } from "../features/resumen/useResumen";
import { usePagedList } from "../hooks/usePagedList";
import { errorMessage } from "../services/apiClient";
import { deleteContrato, listContratos } from "../services/contratosService";
import { type ContratoListado, DIAS_POR_VENCER } from "../types/contrato";
import type { InmuebleResumen, PersonaResumen } from "../types/persona";

const FILTROS = ["q", "estado", "fecha_desde", "fecha_hasta", "tipo", "inmueble_id", "propietario_id", "inquilino_id"] as const;
type Estado = "" | "vigente" | "por_vencer" | "finalizado";
const PESTANAS: readonly { value: Estado; label: string }[] = [
  { value: "", label: "Todos" },
  { value: "vigente", label: "Vigentes" },
  { value: "por_vencer", label: "Por vencer" },
  { value: "finalizado", label: "Finalizados" },
];
const ETIQUETAS: Record<string, string> = {
  q: "Búsqueda",
  estado: "Estado",
  fecha_desde: "Desde",
  fecha_hasta: "Hasta",
  tipo: "Tipo",
  inmueble_id: "Inmueble",
  propietario_id: "Propietario",
  inquilino_id: "Arrendatario",
};

export function ContratosPage() {
  const { tiene } = useAuth();
  const location = useLocation();
  const { catalogos } = useCatalogos();
  const lista = usePagedList(listContratos, { filtros: FILTROS });
  const resumen = useResumen();
  const [q, setQ] = useState(lista.filtros.q ?? "");
  const [desde, setDesde] = useState(lista.filtros.fecha_desde ?? "");
  const [hasta, setHasta] = useState(lista.filtros.fecha_hasta ?? "");
  const [inmueble, setInmueble] = useState<InmuebleResumen | null>(null);
  const [propietario, setPropietario] = useState<PersonaResumen | null>(null);
  const [inquilino, setInquilino] = useState<PersonaResumen | null>(null);
  const [mensaje, setMensaje] = useState<string | null>((location.state as { mensaje?: string } | null)?.mensaje ?? null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  function buscar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    lista.setFiltros({ q: q.trim() || null, fecha_desde: desde || null, fecha_hasta: hasta || null });
  }

  function restablecer() {
    setQ("");
    setDesde("");
    setHasta("");
    setInmueble(null);
    setPropietario(null);
    setInquilino(null);
    lista.setFiltros(Object.fromEntries(FILTROS.map((f) => [f, null])));
  }

  function quitar(clave: string) {
    if (clave === "q") setQ("");
    if (clave === "fecha_desde") setDesde("");
    if (clave === "fecha_hasta") setHasta("");
    if (clave === "inmueble_id") setInmueble(null);
    if (clave === "propietario_id") setPropietario(null);
    if (clave === "inquilino_id") setInquilino(null);
    lista.setFiltros({ [clave]: null });
  }

  async function eliminar(contrato: ContratoListado) {
    if (!window.confirm(`¿Eliminar el contrato #${contrato.id}? Esta acción no se puede deshacer.`)) return;
    setMensaje(null);
    setErrorAccion(null);
    try {
      await deleteContrato(contrato.id);
      setMensaje("Contrato eliminado correctamente.");
      lista.reload();
      resumen.reload();
    } catch (error) {
      setErrorAccion(errorMessage(error));
    }
  }

  const tipos = (catalogos?.tipos_contrato ?? []).map((t) => ({ value: t.codigo, label: t.nombre }));
  const contratos = resumen.resumen?.contratos;
  const aplicados = Object.entries(lista.filtros).filter(([clave]) => clave !== "estado");
  const estado = (lista.filtros.estado ?? "") as Estado;

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Módulos operativos</span>
        <span>Gestión de contratos</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <FileText size={20} />
          </span>
          <div>
            <h1>
              Contratos y codeudores
              {contratos && <span className="badge badge-muted">{contratos.total} registrados</span>}
            </h1>
            <p>Arrendamientos y administraciones con sus propietarios, arrendatarios y codeudores.</p>
          </div>
        </div>
        {tiene(ESCRITURA) && (
          <div className="actions">
            <Link to="/contratos/nuevo" className="button-link">
              <Plus size={18} aria-hidden="true" /> Nuevo contrato
            </Link>
          </div>
        )}
      </header>

      <p className="alert alert-warn">
        Un contrato con registros financieros o archivos asociados no se puede modificar ni eliminar. El estado de
        ocupación del inmueble no cambia solo: actualícelo en Inmuebles al firmar o terminar un contrato.
      </p>

      {contratos && (
        <section className="kpi-grid" aria-label="Indicadores">
          <KpiCard etiqueta="Contratos" valor={contratos.total} detalle="registrados" />
          <KpiCard etiqueta="Vigentes" valor={contratos.vigentes} detalle="en curso hoy" tono="ok" />
          <KpiCard etiqueta="Codeudores vinculados" valor={contratos.codeudores_vinculados} detalle="en todos los contratos" tono="info" />
          <KpiCard
            etiqueta="Por vencer"
            valor={contratos.por_vencer_60}
            detalle={`terminan en menos de ${DIAS_POR_VENCER} días`}
            tono={contratos.por_vencer_60 > 0 ? "warn" : "neutro"}
          />
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

      <Segmented label="Estado" value={estado} options={PESTANAS} onChange={(valor) => lista.setFiltros({ estado: valor || null })} />

      <form className="filters" onSubmit={buscar} role="search" aria-label="Filtrar contratos">
        <Field
          id="contratos-q"
          label="Buscar"
          type="search"
          placeholder="Dirección del inmueble o nombre de una parte"
          value={q}
          className="filters-search"
          onChange={setQ}
        />
        <Field id="contratos-desde" label="Vigente desde" type="date" value={desde} onChange={setDesde} />
        <Field id="contratos-hasta" label="Vigente hasta" type="date" value={hasta} onChange={setHasta} />
        <SelectField
          id="contratos-tipo"
          label="Tipo"
          value={lista.filtros.tipo ?? ""}
          options={tipos}
          placeholder="Todos"
          onChange={(value) => lista.setFiltros({ tipo: value || null })}
        />
        <button type="submit" className="secondary">
          Buscar
        </button>
        <div className="filters-row form-grid">
          <InmueblePicker
            idPrefix="contratos-inmueble"
            label="Inmueble"
            value={inmueble ?? desdeUrl(lista.filtros.inmueble_id, "Inmueble")}
            onChange={(elegido) => {
              setInmueble(elegido);
              lista.setFiltros({ inmueble_id: elegido ? String(elegido.id) : null });
            }}
          />
          <PersonaPicker
            idPrefix="contratos-propietario"
            label="Propietario"
            papel="propietario"
            value={propietario ?? personaDesdeUrl(lista.filtros.propietario_id, "Propietario")}
            soloBuscar
            onChange={(persona) => {
              setPropietario(persona);
              lista.setFiltros({ propietario_id: persona ? String(persona.id) : null });
            }}
          />
          <PersonaPicker
            idPrefix="contratos-inquilino"
            label="Arrendatario"
            papel="arrendatario"
            value={inquilino ?? personaDesdeUrl(lista.filtros.inquilino_id, "Arrendatario")}
            soloBuscar
            onChange={(persona) => {
              setInquilino(persona);
              lista.setFiltros({ inquilino_id: persona ? String(persona.id) : null });
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

      <section className="card" aria-label="Listado de contratos">
        <ContratosTable
          items={lista.items}
          loading={lista.loading}
          error={lista.error}
          puedeEditar={tiene(ESCRITURA)}
          puedeEliminar={tiene(ELIMINACION)}
          onRetry={lista.reload}
          onEliminar={(contrato) => void eliminar(contrato)}
        />
        <Pagination
          total={lista.total}
          limit={lista.limit}
          offset={lista.offset}
          onOffsetChange={lista.setOffset}
          onLimitChange={lista.setLimit}
          etiqueta="contratos"
        />
      </section>
    </>
  );
}

function desdeUrl(id: string | undefined, etiqueta: string): InmuebleResumen | null {
  return id ? { id: Number(id), direccion: `${etiqueta} #${id}`, ciudad: null, estado: null } : null;
}

function personaDesdeUrl(id: string | undefined, etiqueta: string): PersonaResumen | null {
  return id
    ? { id: Number(id), nombre: `${etiqueta} #${id}`, tipo_identificacion: null, identificacion: null, telefono: null, correo: null }
    : null;
}
