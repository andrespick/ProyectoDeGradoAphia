import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { useAuth } from "../features/auth/AuthProvider";
import { ELIMINACION, ESCRITURA } from "../features/auth/roles";
import { type Modulo, MODULOS } from "../features/personas/modulos";
import { enmascarar } from "../features/personas/PersonasTable";
import { errorMessage } from "../services/apiClient";
import { deletePersona, getPersona } from "../services/personasService";
import {
  BADGE_PAPEL,
  type ContratoResumen,
  identificacionDe,
  NOMBRE_PAPEL,
  type PersonaDetalle,
} from "../types/persona";

const fecha = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeZone: "UTC" });

export function PersonaDetallePage({ modulo }: { modulo: Modulo }) {
  const config = MODULOS[modulo];
  const { id } = useParams();
  const navigate = useNavigate();
  const { tiene } = useAuth();
  const [persona, setPersona] = useState<PersonaDetalle | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getPersona(config.api, Number(id), controller.signal)
      .then(setPersona)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [config.api, id]);

  async function eliminar() {
    if (!persona || !window.confirm(`¿Eliminar a ${persona.nombre}? Esta acción no se puede deshacer.`)) return;
    try {
      await deletePersona(config.api, persona.id);
      navigate(config.ruta);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>
          <Link to={config.ruta}>{config.titulo}</Link>
        </span>
        <span>{persona?.nombre ?? "…"}</span>
      </p>
      {error && (
        <p className="alert alert-error" role="alert">
          {error}
        </p>
      )}
      {!persona && !error && (
        <p className="muted" role="status">
          Cargando…
        </p>
      )}
      {persona && (
        <>
          <header className="page-header">
            <div className="page-header-title">
              <div>
                <h1>{persona.nombre}</h1>
                <p>{identificacionDe(persona)}</p>
              </div>
            </div>
            <div className="actions">
              <Link to={config.ruta} className="button-link secondary">
                <ArrowLeft size={16} aria-hidden="true" /> Volver
              </Link>
              {tiene(ESCRITURA) && (
                <Link to={`${config.ruta}/${persona.id}/editar`} className="button-link secondary">
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

          <div className="grid">
            <section className="card" aria-labelledby="datos-titulo">
              <h2 id="datos-titulo">Datos</h2>
              <dl className="meta meta-stack">
                <div>
                  <dt>Teléfono</dt>
                  <dd>{persona.telefono ?? "—"}</dd>
                </div>
                <div>
                  <dt>Correo electrónico</dt>
                  <dd className="wrap-anywhere">{persona.correo ?? "—"}</dd>
                </div>
                <div>
                  <dt>Dirección</dt>
                  <dd>{persona.direccion ?? "—"}</dd>
                </div>
                <div>
                  <dt>Tipo de cliente</dt>
                  <dd>
                    <span className="chip-list">
                      {persona.papeles.map((papel) => (
                        <span key={papel} className={`badge ${BADGE_PAPEL[papel]}`}>
                          {NOMBRE_PAPEL[papel]}
                        </span>
                      ))}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>Cuenta bancaria</dt>
                  <dd>
                    {persona.cuenta_bancaria
                      ? `${persona.cuenta_bancaria.banco} · ${persona.cuenta_bancaria.tipo} ${enmascarar(persona.cuenta_bancaria.numero)}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt>Usuario del sistema</dt>
                  <dd>{persona.usuario ? `@${persona.usuario}` : "No tiene"}</dd>
                </div>
              </dl>
            </section>

            <div className="stack">
              <section className="card" aria-labelledby="inmuebles-titulo">
                <h2 id="inmuebles-titulo">Inmuebles de los que es propietario</h2>
                {persona.inmuebles.length === 0 ? (
                  <p className="muted">Ninguno.</p>
                ) : (
                  <ul className="plain-list">
                    {persona.inmuebles.map((inmueble) => (
                      <li key={inmueble.id}>
                        <strong>{inmueble.direccion}</strong>
                        {inmueble.ciudad && <span className="muted"> · {inmueble.ciudad}</span>}
                        {inmueble.estado && <span className="badge badge-muted">{inmueble.estado}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <ListaContratos titulo="Contratos como arrendatario" contratos={persona.contratos_como_arrendatario} />
              <ListaContratos titulo="Contratos como codeudor" contratos={persona.contratos_como_codeudor} />
              <ListaContratos titulo="Contratos como propietario" contratos={persona.contratos_como_propietario} />
            </div>
          </div>
        </>
      )}
    </>
  );
}

function ListaContratos({ titulo, contratos }: { titulo: string; contratos: ContratoResumen[] }) {
  const id = titulo.toLowerCase().replace(/\s+/g, "-");
  return (
    <section className="card" aria-labelledby={id}>
      <h2 id={id}>{titulo}</h2>
      {contratos.length === 0 ? (
        <p className="muted">Ninguno.</p>
      ) : (
        <ul className="plain-list">
          {contratos.map((contrato) => (
            <li key={contrato.id}>
              <strong>
                Contrato #{contrato.id} · {contrato.tipo}
              </strong>
              <span className="muted">
                {" "}
                · {contrato.inmueble.direccion} · {fecha.format(new Date(contrato.fecha_inicio))}
                {contrato.fecha_fin ? ` – ${fecha.format(new Date(contrato.fecha_fin))}` : " – indefinido"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
