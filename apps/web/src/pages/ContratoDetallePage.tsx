import { ArrowLeft, Pencil, Printer, Trash2, UserPlus, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router";

import { useAuth } from "../features/auth/AuthProvider";
import { ELIMINACION, ESCRITURA } from "../features/auth/roles";
import { diasRestantesTexto } from "../features/contratos/ContratosTable";
import { aContratoCreate, valoresIniciales } from "../features/contratos/validation";
import { PersonaPicker } from "../features/personas/PersonaPicker";
import { errorMessage } from "../services/apiClient";
import { deleteContrato, getContrato, updateContrato } from "../services/contratosService";
import { type Contrato, etiquetaEstado, NOMBRE_TIPO } from "../types/contrato";
import { identificacionDe, type PersonaResumen } from "../types/persona";
import { formatearFecha, formatearMoneda } from "../utils/formato";

export function ContratoDetallePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { tiene } = useAuth();
  const [contrato, setContrato] = useState<Contrato | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>((location.state as { mensaje?: string } | null)?.mensaje ?? null);
  const [asociando, setAsociando] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getContrato(Number(id), controller.signal)
      .then(setContrato)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [id]);

  async function guardarCodeudores(codeudores: PersonaResumen[]) {
    if (!contrato) return;
    setError(null);
    try {
      const actualizado = await updateContrato(contrato.id, aContratoCreate({ ...valoresIniciales(contrato), codeudores }));
      setContrato(actualizado);
      setAsociando(false);
      setMensaje("Codeudores del contrato actualizados.");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function eliminar() {
    if (!contrato || !window.confirm(`¿Eliminar el contrato #${contrato.id}? Esta acción no se puede deshacer.`)) return;
    try {
      await deleteContrato(contrato.id);
      navigate("/contratos", { state: { mensaje: "Contrato eliminado correctamente." } });
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  const estado = contrato ? etiquetaEstado(contrato) : null;
  const titulo = contrato ? `Contrato #${contrato.id} · ${NOMBRE_TIPO[contrato.tipo] ?? contrato.tipo}` : "…";

  return (
    <>
      <p className="breadcrumbs no-print">
        <span>APHIA</span>
        <span>
          <Link to="/contratos">Contratos</Link>
        </span>
        <span>{titulo}</span>
      </p>
      {error && (
        <p className="alert alert-error no-print" role="alert">
          {error}
        </p>
      )}
      {mensaje && (
        <p className="alert alert-success no-print" role="status">
          {mensaje}
        </p>
      )}
      {!contrato && !error && (
        <p className="muted" role="status">
          Cargando…
        </p>
      )}
      {contrato && estado && (
        <>
          <header className="page-header no-print">
            <div className="page-header-title">
              <div>
                <h1>
                  {titulo} <span className={`badge ${estado.badge}`}>{estado.texto}</span>
                </h1>
                <p>
                  {contrato.inmueble.direccion}
                  {contrato.inmueble.ciudad ? ` · ${contrato.inmueble.ciudad}` : ""}
                </p>
              </div>
            </div>
            <div className="actions">
              <Link to="/contratos" className="button-link secondary">
                <ArrowLeft size={16} aria-hidden="true" /> Volver
              </Link>
              <button type="button" className="secondary" disabled={!contrato.texto} onClick={() => window.print()}>
                <Printer size={16} aria-hidden="true" /> Imprimir / guardar PDF
              </button>
              {tiene(ESCRITURA) && (
                <Link to={`/contratos/${contrato.id}/editar`} className="button-link secondary">
                  <Pencil size={16} aria-hidden="true" /> Editar
                </Link>
              )}
              {tiene(ELIMINACION) && (
                <button type="button" className="danger" onClick={() => void eliminar()}>
                  <Trash2 size={16} aria-hidden="true" /> Eliminar
                </button>
              )}
            </div>
          </header>

          <div className="grid no-print">
            <section className="card" aria-labelledby="datos-titulo">
              <h2 id="datos-titulo">Datos</h2>
              <dl className="meta meta-stack">
                <div>
                  <dt>Inmueble</dt>
                  <dd>
                    <Link to={`/inmuebles/${contrato.inmueble.id}/editar`}>{contrato.inmueble.direccion}</Link>
                  </dd>
                </div>
                <div>
                  <dt>Vigencia</dt>
                  <dd>
                    {formatearFecha(contrato.fecha_inicio)} – {contrato.fecha_fin ? formatearFecha(contrato.fecha_fin) : "indefinido"}
                    {contrato.estado !== "finalizado" && contrato.fecha_fin && ` (${diasRestantesTexto(contrato.dias_restantes)})`}
                  </dd>
                </div>
                <div>
                  <dt>Canon pactado</dt>
                  <dd>{formatearMoneda(contrato.canon_pactado)}</dd>
                </div>
                <div>
                  <dt>Condiciones</dt>
                  <dd className="wrap-anywhere">{contrato.condiciones ?? "—"}</dd>
                </div>
              </dl>
            </section>

            <div className="stack">
              <section className="card" aria-labelledby="partes-titulo">
                <h2 id="partes-titulo">Partes</h2>
                <dl className="meta meta-stack">
                  <div>
                    <dt>Propietario(s)</dt>
                    <dd>
                      {contrato.propietarios.map((p) => (
                        <Link key={p.id} to={`/propietarios/${p.id}`} className="cell-link">
                          {p.nombre} · {identificacionDe(p)}
                        </Link>
                      ))}
                    </dd>
                  </div>
                  <div>
                    <dt>Arrendatario</dt>
                    <dd>
                      {contrato.arrendatario ? (
                        <Link to={`/clientes/${contrato.arrendatario.id}`} className="cell-link">
                          {contrato.arrendatario.nombre} · {identificacionDe(contrato.arrendatario)}
                        </Link>
                      ) : (
                        "Sin arrendatario"
                      )}
                    </dd>
                  </div>
                </dl>
              </section>

              <section className="card" aria-labelledby="codeudores-titulo">
                <h2 id="codeudores-titulo">Codeudores</h2>
                {contrato.codeudores.length === 0 ? (
                  <p className="muted">Ninguno.</p>
                ) : (
                  <ul className="chip-list chip-list-block" aria-label="Codeudores del contrato">
                    {contrato.codeudores.map((c) => (
                      <li key={c.id} className="chip chip-persona">
                        <Link to={`/codeudores/${c.id}`}>
                          <strong>{c.nombre}</strong>
                        </Link>{" "}
                        · {identificacionDe(c)}
                        {tiene(ESCRITURA) && (
                          <button
                            type="button"
                            aria-label={`Quitar ${c.nombre}`}
                            onClick={() => void guardarCodeudores(contrato.codeudores.filter((x) => x.id !== c.id))}
                          >
                            <X size={14} aria-hidden="true" />
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
                {tiene(ESCRITURA) && !asociando && contrato.codeudores.length < 10 && (
                  <button type="button" className="secondary" onClick={() => setAsociando(true)}>
                    <UserPlus size={16} aria-hidden="true" /> Asociar codeudor
                  </button>
                )}
                {asociando && (
                  <PersonaPicker
                    idPrefix="detalle-codeudor"
                    label="Nuevo codeudor"
                    papel="codeudor"
                    value={null}
                    excluir={[...contrato.codeudores.map((c) => c.id), ...(contrato.arrendatario ? [contrato.arrendatario.id] : [])]}
                    onChange={(persona) => persona && void guardarCodeudores([...contrato.codeudores, persona])}
                  />
                )}
              </section>
            </div>
          </div>

          <section className="card contrato-impresion" aria-labelledby="texto-titulo">
            <header className="contrato-encabezado">
              <p className="contrato-marca">APHIA S.A.S. · Gestión inmobiliaria</p>
              <h2 id="texto-titulo">{titulo}</h2>
              <p>
                {contrato.inmueble.direccion}
                {contrato.inmueble.ciudad ? `, ${contrato.inmueble.ciudad}` : ""} · {formatearFecha(contrato.fecha_inicio)} –{" "}
                {contrato.fecha_fin ? formatearFecha(contrato.fecha_fin) : "indefinido"}
              </p>
              <p>
                Propietario(s): {contrato.propietarios.map((p) => p.nombre).join(", ") || "—"}. Arrendatario:{" "}
                {contrato.arrendatario?.nombre ?? "—"}. Codeudores: {contrato.codeudores.map((c) => c.nombre).join(", ") || "—"}.
              </p>
            </header>
            {contrato.texto ? (
              <pre className="contrato-texto">{contrato.texto}</pre>
            ) : (
              <p className="muted">Este contrato no tiene texto completo registrado; edítelo para poder imprimirlo.</p>
            )}
          </section>
        </>
      )}
    </>
  );
}
