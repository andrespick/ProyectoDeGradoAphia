import { LockOpen, ShieldCheck, ShieldUser, UserPlus } from "lucide-react";
import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router";

import { Field } from "../components/Field";
import { AyudaLink } from "../components/AyudaLink";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { Segmented } from "../components/Segmented";
import { SelectField } from "../components/SelectField";
import { useAuth } from "../features/auth/AuthProvider";
import { useResumen } from "../features/resumen/useResumen";
import { UsuariosTable } from "../features/usuarios/UsuariosTable";
import { usePagedList } from "../hooks/usePagedList";
import { getPoliticaPublica } from "../services/administracionService";
import { errorMessage } from "../services/apiClient";
import {
  cerrarSesiones,
  deleteUsuario,
  desbloquearUsuario,
  listUsuarios,
  restablecerClave,
  updateUsuario,
} from "../services/usuariosService";
import type { PoliticaPublica } from "../types/administracion";
import type { Role } from "../types/auth";
import type { Usuario } from "../types/usuario";

const FILTROS = ["q", "rol", "estado"] as const;
const ROLES = [
  { value: "", label: "Todos" },
  { value: "admin_sistemas", label: "Admin. de Sistemas" },
  { value: "administrativo", label: "Administrativo" },
  { value: "asesor", label: "Asesor" },
] as const;
const ESTADOS = [
  { value: "activo", label: "Activos" },
  { value: "inactivo", label: "Inactivos" },
  { value: "bloqueado", label: "Bloqueados" },
];

export interface UsuariosOutletContext {
  onSaved: (mensaje: string) => void;
}

export function UsuariosPage() {
  const { principal } = useAuth();
  const location = useLocation();
  const lista = usePagedList(listUsuarios, { filtros: FILTROS });
  const resumen = useResumen();
  const [bloqueados, setBloqueados] = useState<Usuario[]>([]);
  const [q, setQ] = useState(lista.filtros.q ?? "");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const [claveTemporal, setClaveTemporal] = useState<{ usuario: string; clave: string } | null>(null);
  const [politica, setPolitica] = useState<PoliticaPublica | null>(null);

  useEffect(() => {
    getPoliticaPublica()
      .then(setPolitica)
      .catch(() => setPolitica(null));
  }, []);

  const cargarBloqueados = useCallback(() => {
    listUsuarios({ limit: 10, offset: 0, filtros: { estado: "bloqueado" } })
      .then((page) => setBloqueados(page.items))
      .catch(() => setBloqueados([]));
  }, []);

  useEffect(() => {
    cargarBloqueados();
  }, [cargarBloqueados]);

  const recargarTodo = useCallback(() => {
    lista.reload();
    resumen.reload();
    cargarBloqueados();
  }, [lista, resumen, cargarBloqueados]);

  async function ejecutar(accion: () => Promise<unknown>, exito: string) {
    setErrorAccion(null);
    setMensaje(null);
    setClaveTemporal(null);
    try {
      await accion();
      setMensaje(exito);
      recargarTodo();
    } catch (error) {
      setErrorAccion(errorMessage(error));
    }
  }

  function desbloquear(usuario: Usuario) {
    void ejecutar(
      () => desbloquearUsuario(usuario.id),
      `La cuenta de ${usuario.usuario} quedó desbloqueada.`,
    );
  }

  function restablecer(usuario: Usuario) {
    if (!window.confirm(`¿Generar una clave temporal para ${usuario.usuario}? Sus sesiones abiertas se cerrarán.`)) {
      return;
    }
    void ejecutar(async () => {
      const { clave_temporal } = await restablecerClave(usuario.id);
      setClaveTemporal({ usuario: usuario.usuario, clave: clave_temporal });
    }, `Se restableció la clave de ${usuario.usuario}.`);
  }

  function cerrar(usuario: Usuario) {
    void ejecutar(() => cerrarSesiones(usuario.id), `Se cerraron las sesiones abiertas de ${usuario.usuario}.`);
  }

  function eliminar(usuario: Usuario) {
    if (!window.confirm(`¿Eliminar al usuario ${usuario.usuario}? Esta acción no se puede deshacer.`)) {
      return;
    }
    void ejecutar(() => deleteUsuario(usuario.id), `Usuario ${usuario.usuario} eliminado.`);
  }

  function toggleActivo(usuario: Usuario) {
    void ejecutar(
      () =>
        updateUsuario(usuario.id, {
          nombre: usuario.nombre,
          tipo_identificacion: usuario.tipo_identificacion ?? "",
          identificacion: usuario.identificacion ?? "",
          correo: usuario.correo ?? "",
          rol: usuario.rol,
          activo: !usuario.activo,
        }),
      `Cuenta de ${usuario.usuario} ${usuario.activo ? "desactivada" : "activada"}.`,
    );
  }

  function buscar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    lista.setFiltros({ q: q.trim() || null });
  }

  const context: UsuariosOutletContext = {
    onSaved: (texto) => {
      setMensaje(texto);
      recargarTodo();
    },
  };

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Seguridad</span>
        <span>Usuarios</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <ShieldUser size={20} />
          </span>
          <div>
            <h1>
              Usuarios y roles
              {resumen.resumen && <span className="badge badge-muted">{resumen.resumen.usuarios.total} en total</span>}
            </h1>
            <p>Control de credenciales, accesos del equipo y permisos del sistema.</p>
          </div>
        </div>
        <div className="actions">
          <Link to={{ pathname: "/usuarios/nuevo", search: location.search }} className="button-link">
            <UserPlus size={18} aria-hidden="true" /> Registrar usuario
          </Link>
          <AyudaLink seccion="usuarios" etiqueta="usuarios" />
        </div>
      </header>

      {politica && (
        <p className="alert alert-info">
          <ShieldCheck size={16} aria-hidden="true" /> Protocolo activo: la cuenta se suspende{" "}
          {politica.minutos_bloqueo} minutos tras {politica.max_intentos} intentos fallidos de inicio de
          sesión. Puede desbloquearla aquí o cambiar la política en Configuración.
        </p>
      )}

      {resumen.resumen && (
        <section className="kpi-grid" aria-label="Indicadores de usuarios">
          <KpiCard etiqueta="Total usuarios" valor={resumen.resumen.usuarios.total} detalle="cuentas" />
          <KpiCard etiqueta="Activos" valor={resumen.resumen.usuarios.activos} detalle="pueden iniciar sesión" tono="ok" />
          <KpiCard
            etiqueta="Bloqueados"
            valor={resumen.resumen.usuarios.bloqueados}
            detalle="por reintentos fallidos"
            tono={resumen.resumen.usuarios.bloqueados > 0 ? "error" : "neutro"}
          />
        </section>
      )}

      {bloqueados.map((usuario) => (
        <div key={usuario.id} className="alert alert-error" role="alert">
          <p>
            <strong>{usuario.nombre}</strong> (@{usuario.usuario}) tiene el acceso suspendido por{" "}
            {usuario.intentos_fallidos} intentos fallidos.
          </p>
          <div className="actions">
            <button type="button" onClick={() => desbloquear(usuario)}>
              <LockOpen size={16} aria-hidden="true" /> Desbloquear
            </button>
          </div>
        </div>
      ))}

      {mensaje && (
        <div className="alert alert-success" role="status">
          <p>{mensaje}</p>
          {claveTemporal && (
            <p>
              Clave temporal de @{claveTemporal.usuario}: <code className="clave-temporal">{claveTemporal.clave}</code>.
              Entréguela por un canal seguro; no se volverá a mostrar y se pedirá cambiarla al entrar.
            </p>
          )}
        </div>
      )}
      {errorAccion && (
        <p className="alert alert-error" role="alert">
          {errorAccion}
        </p>
      )}

      <form className="filters" onSubmit={buscar} role="search" aria-label="Filtrar usuarios">
        <Field
          id="usuarios-q"
          label="Buscar"
          type="search"
          placeholder="Usuario o nombre"
          value={q}
          className="filters-search"
          onChange={setQ}
        />
        <Segmented
          label="Rol"
          value={(lista.filtros.rol as Role | undefined) ?? ""}
          options={ROLES}
          onChange={(value) => lista.setFiltros({ rol: value || null })}
        />
        <SelectField
          id="usuarios-estado"
          label="Estado"
          value={lista.filtros.estado ?? ""}
          options={ESTADOS}
          placeholder="Todos los estados"
          onChange={(value) => lista.setFiltros({ estado: value || null })}
        />
        <button type="submit" className="secondary">
          Buscar
        </button>
      </form>

      <section className="card" aria-label="Listado de usuarios">
        <UsuariosTable
          items={lista.items}
          loading={lista.loading}
          error={lista.error}
          actorId={principal?.sujeto ?? ""}
          onRetry={lista.reload}
          onToggleActivo={toggleActivo}
          onDesbloquear={desbloquear}
          onEliminar={eliminar}
          onRestablecerClave={restablecer}
          onCerrarSesiones={cerrar}
        />
        <Pagination
          total={lista.total}
          limit={lista.limit}
          offset={lista.offset}
          onOffsetChange={lista.setOffset}
          onLimitChange={lista.setLimit}
          etiqueta="usuarios"
        />
      </section>

      <Outlet context={context} />
    </>
  );
}
