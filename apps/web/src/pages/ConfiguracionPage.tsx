import { Building, Settings, ShieldCheck } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";

import { AyudaLink } from "../components/AyudaLink";
import { Field } from "../components/Field";
import { useCatalogos } from "../features/catalogos/useCatalogos";
import { errorsFromApi, type Errores } from "../features/shared/validation";
import { getEmpresa, getPolitica, updateEmpresa, updatePolitica } from "../services/administracionService";
import { ApiError, errorMessage } from "../services/apiClient";
import type { Empresa, PoliticaSeguridad } from "../types/administracion";

const CAMPOS_POLITICA = ["max_intentos", "minutos_bloqueo", "horas_sesion", "largo_minimo_clave"] as const;
const CAMPOS_EMPRESA = ["nombre", "nit", "direccion", "ciudad", "telefono", "correo"] as const;
type CampoPolitica = (typeof CAMPOS_POLITICA)[number];
type CampoEmpresa = (typeof CAMPOS_EMPRESA)[number];

// Mismos límites que la API (modules/configuracion/schemas.py y los CHECK de la migración 0014).
const LIMITES: Record<CampoPolitica, { etiqueta: string; min: number; max: number; unidad: string }> = {
  max_intentos: { etiqueta: "Intentos antes del bloqueo", min: 3, max: 10, unidad: "intentos" },
  minutos_bloqueo: { etiqueta: "Duración del bloqueo", min: 5, max: 1440, unidad: "minutos" },
  horas_sesion: { etiqueta: "Vigencia de la sesión", min: 1, max: 24, unidad: "horas" },
  largo_minimo_clave: { etiqueta: "Largo mínimo de la contraseña", min: 8, max: 64, unidad: "caracteres" },
};

interface Estado<C extends string> {
  errores: Errores<C>;
  mensaje: string | null;
  error: string | null;
}

const LIMPIO = { errores: {}, mensaje: null, error: null };

export function ConfiguracionPage() {
  const { catalogos } = useCatalogos();
  const [politica, setPolitica] = useState<Record<CampoPolitica, string> | null>(null);
  const [empresa, setEmpresa] = useState<Record<CampoEmpresa, string> | null>(null);
  const [estadoPolitica, setEstadoPolitica] = useState<Estado<CampoPolitica>>(LIMPIO);
  const [estadoEmpresa, setEstadoEmpresa] = useState<Estado<CampoEmpresa>>(LIMPIO);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([getPolitica(controller.signal), getEmpresa()])
      .then(([p, e]) => {
        setPolitica(aTexto(p));
        setEmpresa(aTexto(e));
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setErrorCarga(errorMessage(err));
      });
    return () => controller.abort();
  }, []);

  async function guardarPolitica(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!politica) return;
    setEstadoPolitica(LIMPIO);
    const datos = Object.fromEntries(CAMPOS_POLITICA.map((c) => [c, Number(politica[c])])) as unknown as PoliticaSeguridad;
    try {
      setPolitica(aTexto(await updatePolitica(datos)));
      setEstadoPolitica({ ...LIMPIO, mensaje: "Política de seguridad guardada. Rige desde el próximo inicio de sesión." });
    } catch (err) {
      setEstadoPolitica(fallo(err, CAMPOS_POLITICA));
    }
  }

  async function guardarEmpresa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!empresa) return;
    setEstadoEmpresa(LIMPIO);
    const datos = Object.fromEntries(CAMPOS_EMPRESA.map((c) => [c, empresa[c].trim() || null])) as unknown as Empresa;
    try {
      setEmpresa(aTexto(await updateEmpresa(datos)));
      setEstadoEmpresa({ ...LIMPIO, mensaje: "Datos de la empresa guardados." });
    } catch (err) {
      setEstadoEmpresa(fallo(err, CAMPOS_EMPRESA));
    }
  }

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Sistema</span>
        <span>Configuración</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <Settings size={20} />
          </span>
          <div>
            <h1>Configuración</h1>
            <p>Política de seguridad del inicio de sesión y datos de la empresa.</p>
          </div>
        </div>
        <div className="actions">
          <AyudaLink seccion="configuracion" etiqueta="la configuración" />
        </div>
      </header>

      {errorCarga && (
        <p className="alert alert-error" role="alert">
          {errorCarga}
        </p>
      )}

      {politica && (
        <section className="card" aria-labelledby="politica-titulo">
          <h2 id="politica-titulo">
            <ShieldCheck size={18} aria-hidden="true" /> Política de seguridad
          </h2>
          <form className="form" onSubmit={(event) => void guardarPolitica(event)} noValidate aria-label="Política de seguridad">
            <div className="form-grid">
              {CAMPOS_POLITICA.map((campo) => (
                <Field
                  key={campo}
                  id={`politica-${campo}`}
                  label={LIMITES[campo].etiqueta}
                  type="number"
                  inputMode="numeric"
                  min={LIMITES[campo].min}
                  max={LIMITES[campo].max}
                  value={politica[campo]}
                  error={estadoPolitica.errores[campo]}
                  hint={`Entre ${LIMITES[campo].min} y ${LIMITES[campo].max} ${LIMITES[campo].unidad}`}
                  required
                  onChange={(value) => setPolitica({ ...politica, [campo]: value })}
                />
              ))}
            </div>
            <Mensajes estado={estadoPolitica} />
            <div className="actions form-actions">
              <button type="submit">Guardar política</button>
            </div>
          </form>
        </section>
      )}

      {empresa && (
        <section className="card" aria-labelledby="empresa-titulo">
          <h2 id="empresa-titulo">
            <Building size={18} aria-hidden="true" /> Datos de la empresa
          </h2>
          <p className="muted">
            Aparecen al imprimir los contratos y en el pie de página. El logotipo no se puede cambiar desde aquí.
          </p>
          <form className="form" onSubmit={(event) => void guardarEmpresa(event)} noValidate aria-label="Datos de la empresa">
            <div className="form-grid">
              <Field
                id="empresa-nombre"
                label="Razón social"
                value={empresa.nombre}
                error={estadoEmpresa.errores.nombre}
                maxLength={255}
                required
                className="span-2"
                onChange={(value) => setEmpresa({ ...empresa, nombre: value })}
              />
              <Field
                id="empresa-nit"
                label="NIT"
                value={empresa.nit}
                error={estadoEmpresa.errores.nit}
                hint="Ej.: 900.123.456-7"
                maxLength={50}
                onChange={(value) => setEmpresa({ ...empresa, nit: value })}
              />
              <Field
                id="empresa-telefono"
                label="Teléfono"
                type="tel"
                value={empresa.telefono}
                error={estadoEmpresa.errores.telefono}
                maxLength={50}
                onChange={(value) => setEmpresa({ ...empresa, telefono: value })}
              />
              <Field
                id="empresa-direccion"
                label="Dirección"
                value={empresa.direccion}
                error={estadoEmpresa.errores.direccion}
                maxLength={255}
                onChange={(value) => setEmpresa({ ...empresa, direccion: value })}
              />
              <Field
                id="empresa-ciudad"
                label="Ciudad"
                value={empresa.ciudad}
                error={estadoEmpresa.errores.ciudad}
                maxLength={255}
                list="empresa-ciudades"
                onChange={(value) => setEmpresa({ ...empresa, ciudad: value })}
              />
              <datalist id="empresa-ciudades">
                {catalogos?.ciudades.map((c) => <option key={c.id} value={c.nombre} />)}
              </datalist>
              <Field
                id="empresa-correo"
                label="Correo electrónico"
                type="email"
                value={empresa.correo}
                error={estadoEmpresa.errores.correo}
                maxLength={254}
                className="span-2"
                onChange={(value) => setEmpresa({ ...empresa, correo: value })}
              />
            </div>
            <Mensajes estado={estadoEmpresa} />
            <div className="actions form-actions">
              <button type="submit">Guardar datos</button>
            </div>
          </form>
        </section>
      )}
    </>
  );
}

function Mensajes<C extends string>({ estado }: { estado: Estado<C> }) {
  return (
    <>
      {estado.mensaje && (
        <p className="alert alert-success" role="status">
          {estado.mensaje}
        </p>
      )}
      {estado.error && (
        <p className="alert alert-error" role="alert">
          {estado.error}
        </p>
      )}
    </>
  );
}

function aTexto<T extends object>(datos: T): Record<keyof T, string> {
  return Object.fromEntries(Object.entries(datos).map(([k, v]) => [k, v === null ? "" : String(v)])) as Record<
    keyof T,
    string
  >;
}

function fallo<C extends string>(err: unknown, campos: readonly C[]): Estado<C> {
  return {
    errores: err instanceof ApiError ? errorsFromApi(err.details, campos) : {},
    mensaje: null,
    error: errorMessage(err),
  };
}
