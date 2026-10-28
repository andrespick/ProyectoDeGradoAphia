import { ArrowRight, Building2, FileText, type LucideIcon, ShieldUser, Users } from "lucide-react";
import { Link } from "react-router";

import { KpiCard } from "../components/KpiCard";
import { useAuth } from "../features/auth/AuthProvider";
import { GESTION_USUARIOS } from "../features/auth/roles";
import { ClienteForm } from "../features/clientes/ClienteForm";
import { ClientesTable } from "../features/clientes/ClientesTable";
import { useClientes } from "../features/clientes/useClientes";
import { useResumen } from "../features/resumen/useResumen";
import type { Role } from "../types/auth";

interface Modulo {
  to: string;
  titulo: string;
  descripcion: string;
  icon: LucideIcon;
  roles?: readonly Role[];
  conteo: (r: NonNullable<ReturnType<typeof useResumen>["resumen"]>) => string;
}

// Las tarjetas de clientes, propietarios, codeudores, inmuebles y contratos llegan en las fases 2–4.
const MODULOS: readonly Modulo[] = [
  {
    to: "/usuarios",
    titulo: "Gestión de usuarios",
    descripcion: "Roles de administradores, administrativos y asesores; bloqueos y desbloqueos.",
    icon: ShieldUser,
    roles: GESTION_USUARIOS,
    conteo: (r) => `${r.usuarios.total} cuenta${r.usuarios.total === 1 ? "" : "s"}`,
  },
];

const fechaLarga = new Intl.DateTimeFormat("es-CO", { dateStyle: "full", timeZone: "America/Bogota" });

export function HomePage() {
  const { principal, tiene } = useAuth();
  const { resumen, error } = useResumen();
  const clientes = useClientes();
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
          />
          <KpiCard
            etiqueta="Clientes activos"
            valor={resumen.personas.total}
            detalle={`${resumen.personas.propietarios} propietarios · ${resumen.personas.arrendatarios} arrendatarios · ${resumen.personas.codeudores} codeudores`}
            icono={<Users size={20} />}
            tono="info"
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
          {MODULOS.filter((m) => !m.roles || tiene(m.roles)).map(({ icon: Icon, ...modulo }) => (
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

      {/* Flujo de demostración de la fase anterior; se reemplaza por el módulo real en la fase 2. */}
      <div className="grid">
        <section className="card" aria-labelledby="form-titulo">
          <h2 id="form-titulo">Nuevo cliente de prueba</h2>
          <p className="muted">Use únicamente datos ficticios.</p>
          <ClienteForm onSubmit={clientes.create} />
        </section>
        <section className="card" aria-labelledby="lista-titulo">
          <h2 id="lista-titulo">Clientes</h2>
          <ClientesTable
            items={clientes.items}
            total={clientes.total}
            loading={clientes.loading}
            error={clientes.error}
            onRetry={clientes.reload}
          />
        </section>
      </div>
    </>
  );
}
