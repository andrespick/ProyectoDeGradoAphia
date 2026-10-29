import { Activity, Database, HardDriveDownload, RefreshCw, Server, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { AyudaLink } from "../components/AyudaLink";
import { KpiCard } from "../components/KpiCard";
import { ESTADO_RESPALDO } from "../features/administracion/etiquetas";
import { getEstadoSistema, listRespaldos, solicitarRespaldo } from "../services/administracionService";
import { errorMessage } from "../services/apiClient";
import type { EstadoSistema, Respaldo } from "../types/administracion";
import { formatearBytes, formatearFechaHora } from "../utils/formato";

const RUNTIME = { workers: "Cloudflare Workers", asgi: "ASGI (Uvicorn)" } as const;

export function SistemaPage() {
  const [estado, setEstado] = useState<EstadoSistema | null>(null);
  const [respaldos, setRespaldos] = useState<Respaldo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const recargar = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    Promise.all([getEstadoSistema(controller.signal), listRespaldos(controller.signal)])
      .then(([nuevoEstado, pagina]) => {
        setEstado(nuevoEstado);
        setRespaldos(pagina.items);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [version]);

  async function solicitar() {
    setMensaje(null);
    setError(null);
    try {
      await solicitarRespaldo();
      setMensaje("Respaldo solicitado. El servidor lo ejecutará en los próximos minutos.");
      recargar();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  const bd = estado?.base_de_datos;
  const ultimo = estado?.respaldos?.ultimo_exitoso ?? null;
  const pendiente = estado?.respaldos?.pendiente ?? null;

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Sistema</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <Activity size={20} />
          </span>
          <div>
            <h1>Estado del sistema</h1>
            <p>Disponibilidad de la API y la base de datos, migraciones aplicadas y respaldos.</p>
          </div>
        </div>
        <div className="actions">
          <button type="button" className="secondary" onClick={recargar}>
            <RefreshCw size={16} aria-hidden="true" /> Actualizar
          </button>
          <AyudaLink seccion="sistema" etiqueta="el estado del sistema" />
        </div>
      </header>

      {error && (
        <p className="alert alert-error" role="alert">
          {error}
        </p>
      )}
      {mensaje && (
        <p className="alert alert-success" role="status">
          {mensaje}
        </p>
      )}
      {!estado && !error && (
        <p className="muted" role="status">
          Consultando el estado…
        </p>
      )}

      {estado && (
        <section className="kpi-grid" aria-label="Indicadores del sistema">
          <KpiCard
            etiqueta="API"
            valor={`v${estado.api.version}`}
            detalle={`${RUNTIME[estado.api.runtime]} · ${estado.api.entorno}`}
            icono={<Server size={20} />}
            tono="ok"
          />
          <KpiCard
            etiqueta="Base de datos"
            valor={bd?.disponible ? "En línea" : "Sin conexión"}
            detalle={bd?.disponible ? `MySQL ${bd.version ?? ""} · ${bd.latencia_ms ?? "—"} ms` : "La API no logra conectarse a MySQL"}
            icono={<Database size={20} />}
            tono={bd?.disponible ? "ok" : "error"}
          />
          <KpiCard
            etiqueta="Migraciones"
            valor={estado.migraciones ? estado.migraciones.aplicadas : "—"}
            detalle={
              estado.migraciones?.ultima
                ? `Última: ${estado.migraciones.ultima} · ${formatearFechaHora(estado.migraciones.aplicada_en)}`
                : "Sin información"
            }
            icono={<Activity size={20} />}
            tono="info"
          />
          <KpiCard
            etiqueta="Último respaldo"
            valor={ultimo ? formatearFechaHora(ultimo.terminado_en) : "Ninguno"}
            detalle={ultimo ? `${ultimo.archivo ?? ""} · ${formatearBytes(ultimo.tamano_bytes)}` : "No hay respaldos exitosos registrados"}
            icono={<HardDriveDownload size={20} />}
            tono={estado.respaldos?.atrasado ? "warn" : "ok"}
          />
        </section>
      )}

      {estado?.registros && (
        <section className="card" aria-labelledby="registros-titulo">
          <h2 id="registros-titulo">Registros</h2>
          <dl className="meta">
            <div>
              <dt>Personas</dt>
              <dd>{estado.registros.personas}</dd>
            </div>
            <div>
              <dt>Inmuebles</dt>
              <dd>{estado.registros.inmuebles}</dd>
            </div>
            <div>
              <dt>Contratos</dt>
              <dd>{estado.registros.contratos}</dd>
            </div>
            <div>
              <dt>Usuarios</dt>
              <dd>{estado.registros.usuarios}</dd>
            </div>
            <div>
              <dt>Eventos de auditoría</dt>
              <dd>{estado.registros.eventos_auditoria}</dd>
            </div>
            <div>
              <dt>En la papelera</dt>
              <dd>{estado.registros.en_papelera}</dd>
            </div>
            <div>
              <dt>Tamaño de la base de datos</dt>
              <dd>{formatearBytes(bd?.tamano_bytes)}</dd>
            </div>
          </dl>
        </section>
      )}

      {estado?.respaldos && (
        <section className="card" aria-labelledby="respaldos-titulo">
          <div className="card-header">
            <h2 id="respaldos-titulo">Respaldos</h2>
            <button type="button" onClick={() => void solicitar()} disabled={pendiente !== null}>
              <HardDriveDownload size={16} aria-hidden="true" /> Solicitar respaldo ahora
            </button>
          </div>
          {estado.respaldos.atrasado && (
            <p className="alert alert-warn">
              <TriangleAlert size={16} aria-hidden="true" /> No hay un respaldo exitoso en las últimas 26 horas.
              Revise la tarea programada del servidor (docs/despliegue/restauracion.md).
            </p>
          )}
          {pendiente && (
            <p className="alert alert-info">
              Respaldo {ESTADO_RESPALDO[pendiente.estado].label.toLowerCase()} desde{" "}
              {formatearFechaHora(pendiente.iniciado_en ?? pendiente.solicitado_en)}.
            </p>
          )}
          {respaldos.length === 0 ? (
            <p className="empty-state">Aún no hay respaldos registrados.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Solicitado</th>
                    <th scope="col">Origen</th>
                    <th scope="col">Estado</th>
                    <th scope="col">Archivo</th>
                    <th scope="col">Tamaño</th>
                    <th scope="col">Copia externa</th>
                  </tr>
                </thead>
                <tbody>
                  {respaldos.map((r) => (
                    <tr key={r.id}>
                      <td className="nowrap">{formatearFechaHora(r.solicitado_en)}</td>
                      <td>{r.origen === "manual" ? "Manual" : "Programado"}</td>
                      <td>
                        <span className={`badge ${ESTADO_RESPALDO[r.estado].badge}`}>{ESTADO_RESPALDO[r.estado].label}</span>
                        {r.error && <span className="cell-sub">{r.error}</span>}
                      </td>
                      <td className="wrap-anywhere">{r.archivo ?? "—"}</td>
                      <td className="num">{formatearBytes(r.tamano_bytes)}</td>
                      <td>{r.copia_externa === null ? "—" : r.copia_externa ? "Sí" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  );
}
