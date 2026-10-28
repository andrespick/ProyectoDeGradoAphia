import { ArrowRight, Building2, FileText, type LucideIcon, ShieldUser, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";

import { KpiCard } from "../components/KpiCard";
import { useAuth } from "../features/auth/AuthProvider";
import { GESTION_USUARIOS } from "../features/auth/roles";
import { MODULOS } from "../features/personas/modulos";
import { diasRestantesTexto } from "../features/contratos/ContratosTable";
import { useResumen } from "../features/resumen/useResumen";
import { listContratos } from "../services/contratosService";
import type { ContratoListado } from "../types/contrato";
import type { Role } from "../types/auth";
import type { Resumen } from "../types/resumen";

interface Modulo {
  to: string;
  titulo: string;
  descripcion: string;
  icon: LucideIcon;
  roles?: readonly Role[];
  conteo: (r: Resumen) => string;
}

function plural(n: number, singular: string, plural: string): string {
  return `${n} ${n === 1 ? singular : plural}`;
}

const MODULOS_TABLERO: readonly Modulo[] = [
  {
    to: MODULOS.clientes.ruta,
    titulo: "Clientes",
    descripcion: MODULOS.clientes.descripcion,
    icon: MODULOS.clientes.icon,
    conteo: (r) => plural(r.personas.total, "registro", "registros"),
  },
  {
    to: MODULOS.propietarios.ruta,
    titulo: "Propietarios",
    descripcion: MODULOS.propietarios.descripcion,
    icon: MODULOS.propietarios.icon,
    conteo: (r) => plural(r.personas.propietarios, "propietario", "propietarios"),
  },
  {
    to: MODULOS.codeudores.ruta,
    titulo: "Codeudores",
    descripcion: MODULOS.codeudores.descripcion,
    icon: MODULOS.codeudores.icon,
    conteo: (r) => plural(r.personas.codeudores, "codeudor", "codeudores"),
  },
  {
    to: "/inmuebles",
    titulo: "Inmuebles",
    descripcion: "Apartamentos, locales, oficinas y bodegas con sus propietarios y servicios públicos.",
    icon: Building2,
    conteo: (r) => plural(r.inmuebles.total, "inmueble", "inmuebles"),
  },
  {
    to: "/contratos",
    titulo: "Contratos",
    descripcion: "Arrendamientos y administraciones con propietarios, arrendatarios y codeudores.",
    icon: FileText,
    conteo: (r) => plural(r.contratos.vigentes, "contrato vigente", "contratos vigentes"),
  },
  {
    to: "/usuarios",
    titulo: "Gestión de usuarios",
    descripcion: "Roles de administradores, administrativos y asesores; bloqueos y desbloqueos.",
    icon: ShieldUser,
    roles: GESTION_USUARIOS,
    conteo: (r) => plural(r.usuarios.total, "cuenta", "cuentas"),
  },
];

const fechaLarga = new Intl.DateTimeFormat("es-CO", { dateStyle: "full", timeZone: "America/Bogota" });

export function HomePage() {
  const { principal, tiene } = useAuth();
  const { resumen, error } = useResumen();
  const nombre = principal?.nombre.split(" ")[0] ?? "";
  const [porVencer, setPorVencer] = useState<ContratoListado[] | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listContratos({ filtros: { estado: "por_vencer" }, limit: 5, offset: 0 }, controller.signal)
      .then((pagina) => setPorVencer(pagina.items))
      .catch(() => {
        if (!controller.signal.aborted) setPorVencer([]);
      });
    return () => controller.abort();
  }, []);

  return (
    <>
      <header className="page-header">
        <div className="page-header-title">
          <div>
            <p className="muted">{fechaLarga.format(new Date())}</p>
            <h1>
              Bienvenido de nuevo, <span className="accent">{nombre}</span>
            </h1>
            <p>Centro de control de clientes, propietarios, inmuebles y contratos de APHIA.</p>
          </div>
        </div>
      </header>

      {error && (
        <p className="alert alert-error" role="alert">
          {error}
        </p>
      )}
      {resumen && (
        <section className="kpi-grid" aria-label="Indicadores">
          <KpiCard
            etiqueta="Total inmuebles"
            valor={resumen.inmuebles.total}
            detalle={`${resumen.inmuebles.ocupados} ocupados · ${resumen.inmuebles.disponibles} disponibles`}
            icono={<Building2 size={20} />}
            to="/inmuebles"
          />
          <KpiCard
            etiqueta="Clientes activos"
            valor={resumen.personas.total}
            detalle={`${resumen.personas.propietarios} propietarios · ${resumen.personas.arrendatarios} arrendatarios · ${resumen.personas.codeudores} codeudores`}
            icono={<Users size={20} />}
            tono="info"
            to={MODULOS.clientes.ruta}
          />
          <KpiCard
            etiqueta="Contratos vigentes"
            valor={resumen.contratos.vigentes}
            detalle={`${resumen.contratos.total} en total · ${resumen.contratos.codeudores_vinculados} codeudores vinculados`}
            icono={<FileText size={20} />}
            tono="ok"
            to="/contratos?estado=vigente"
          />
          <KpiCard
            etiqueta="Vencimientos próximos"
            valor={resumen.contratos.por_vencer_30}
            detalle="contratos que terminan en menos de 30 días"
            icono={<FileText size={20} />}
            tono={resumen.contratos.por_vencer_30 > 0 ? "error" : "neutro"}
            to="/contratos?estado=por_vencer"
          />
        </section>
      )}

      <section className="card" aria-labelledby="vencimientos-titulo">
        <h2 id="vencimientos-titulo">Contratos que vencen pronto</h2>
        {porVencer === null && (
          <p className="muted" role="status">
            Cargando…
          </p>
        )}
        {porVencer && porVencer.length === 0 && <p className="muted">Ningún contrato termina en los próximos 60 días.</p>}
        {porVencer && porVencer.length > 0 && (
          <ul className="plain-list">
            {porVencer.map((c) => (
              <li key={c.id}>
                <Link to={`/contratos/${c.id}`}>
                  <strong>Contrato #{c.id}</strong>
                </Link>
                <span className="muted">
                  {" "}
                  · {c.inmueble.direccion} · {c.arrendatario?.nombre ?? "sin arrendatario"} · {diasRestantesTexto(c.dias_restantes)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="modulos-titulo">
        <h2 id="modulos-titulo">Módulos de gestión</h2>
        <div className="module-grid">
          {MODULOS_TABLERO.filter((m) => !m.roles || tiene(m.roles)).map(({ icon: Icon, ...modulo }) => (
            <Link key={modulo.to} to={modulo.to} className="card module-card">
              <span className="icon-box" aria-hidden="true">
                <Icon size={20} />
              </span>
              <h2>{modulo.titulo}</h2>
              <p className="muted">{modulo.descripcion}</p>
              <span className="module-footer">
                {resumen ? modulo.conteo(resumen) : "…"}
                <ArrowRight size={18} aria-hidden="true" />
              </span>
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}
