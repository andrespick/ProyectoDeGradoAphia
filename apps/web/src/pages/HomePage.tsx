import { ArrowRight, Building2, FileText, type LucideIcon, ShieldUser, Users } from "lucide-react";
import { Link } from "react-router";

import { KpiCard } from "../components/KpiCard";
import { useAuth } from "../features/auth/AuthProvider";
import { GESTION_USUARIOS } from "../features/auth/roles";
import { MODULOS } from "../features/personas/modulos";
import { useResumen } from "../features/resumen/useResumen";
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

// Contratos llega en la fase 4.
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
          />
          <KpiCard
            etiqueta="Vencimientos próximos"
            valor={resumen.contratos.por_vencer_30}
            detalle="contratos que terminan en menos de 30 días"
            icono={<FileText size={20} />}
            tono={resumen.contratos.por_vencer_30 > 0 ? "error" : "neutro"}
          />
        </section>
      )}

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
