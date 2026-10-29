import { RotateCcw, Trash2 } from "lucide-react";
import { useRef, useState } from "react";

import { AyudaLink } from "../components/AyudaLink";
import { Pagination } from "../components/Pagination";
import { Segmented } from "../components/Segmented";
import { TIPOS_REGISTRO } from "../features/administracion/etiquetas";
import { usePagedList } from "../hooks/usePagedList";
import { eliminarDefinitivamente, listPapelera, restaurarRegistro } from "../services/administracionService";
import { errorMessage } from "../services/apiClient";
import type { RegistroEliminado, TipoRegistro } from "../types/administracion";
import { formatearFechaHora } from "../utils/formato";

const FILTROS = ["tipo"] as const;
const TIPOS = [
  { value: "", label: "Todos" },
  { value: "persona", label: "Personas" },
  { value: "inmueble", label: "Inmuebles" },
  { value: "contrato", label: "Contratos" },
] as const;

export function PapeleraPage() {
  const lista = usePagedList(listPapelera, { filtros: FILTROS });
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const enCurso = useRef(false); // el segundo clic de un doble clic llega antes de re-renderizar

  async function ejecutar(accion: () => Promise<string>) {
    if (enCurso.current) return;
    enCurso.current = true;
    setMensaje(null);
    setError(null);
    setOcupado(true);
    try {
      setMensaje(await accion());
      lista.reload();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      enCurso.current = false;
      setOcupado(false);
    }
  }

  function restaurar(registro: RegistroEliminado) {
    void ejecutar(async () => {
      const nuevo = await restaurarRegistro(registro.id);
      return `«${registro.descripcion}» se restauró como ${TIPOS_REGISTRO[nuevo.tipo].toLowerCase()} #${nuevo.id}.`;
    });
  }

  function eliminar(registro: RegistroEliminado) {
    if (!window.confirm(`¿Eliminar definitivamente «${registro.descripcion}»? Ya no se podrá restaurar.`)) return;
    void ejecutar(async () => {
      await eliminarDefinitivamente(registro.id);
      return `«${registro.descripcion}» se eliminó definitivamente.`;
    });
  }

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Sistema</span>
        <span>Papelera</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <Trash2 size={20} />
          </span>
          <div>
            <h1>
              Papelera
              <span className="badge badge-muted">{lista.total} registros</span>
            </h1>
            <p>Personas, inmuebles y contratos eliminados. Restaurarlos los registra de nuevo con otro número.</p>
          </div>
        </div>
        <div className="actions">
          <AyudaLink seccion="papelera" etiqueta="la papelera" />
        </div>
      </header>

      <div className="filters">
        <Segmented
          label="Tipo de registro"
          value={(lista.filtros.tipo as TipoRegistro | undefined) ?? ""}
          options={TIPOS}
          onChange={(value) => lista.setFiltros({ tipo: value || null })}
        />
      </div>

      {mensaje && (
        <p className="alert alert-success" role="status">
          {mensaje}
        </p>
      )}
      {error && (
        <p className="alert alert-error" role="alert">
          {error}
        </p>
      )}

      <section className="card" aria-label="Registros eliminados">
        {lista.error ? (
          <div className="alert alert-error" role="alert">
            <p>{lista.error}</p>
            <button type="button" className="secondary" onClick={lista.reload}>
              Reintentar
            </button>
          </div>
        ) : lista.loading && lista.items.length === 0 ? (
          <p className="muted" role="status">
            Cargando…
          </p>
        ) : lista.items.length === 0 ? (
          <p className="empty-state">La papelera está vacía.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Tipo</th>
                  <th scope="col">Registro</th>
                  <th scope="col">Eliminado por</th>
                  <th scope="col">Fecha</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {lista.items.map((registro) => (
                  <tr key={registro.id}>
                    <td>
                      <span className="badge badge-muted">{TIPOS_REGISTRO[registro.tipo]}</span>
                    </td>
                    <td>
                      <span className="cell-title">{registro.descripcion}</span>
                      <span className="cell-sub">Antes #{registro.entidad_id}</span>
                    </td>
                    <td>{registro.eliminado_por ?? "—"}</td>
                    <td className="nowrap">{formatearFechaHora(registro.eliminado_en)}</td>
                    <td>
                      <span className="row-actions">
                        <button
                          type="button"
                          className="secondary"
                          disabled={ocupado}
                          aria-label={`Restaurar ${registro.descripcion}`}
                          onClick={() => restaurar(registro)}
                        >
                          <RotateCcw size={16} aria-hidden="true" /> Restaurar
                        </button>
                        <button
                          type="button"
                          className="danger"
                          disabled={ocupado}
                          aria-label={`Eliminar definitivamente ${registro.descripcion}`}
                          onClick={() => eliminar(registro)}
                        >
                          <Trash2 size={16} aria-hidden="true" /> Eliminar
                        </button>
                      </span>
                    </td>
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
          etiqueta="registros"
        />
      </section>
    </>
  );
}
