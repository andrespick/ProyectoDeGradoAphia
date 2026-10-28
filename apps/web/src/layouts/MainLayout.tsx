import {
  Building2,
  LayoutDashboard,
  LogOut,
  type LucideIcon,
  Menu,
  ShieldUser,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";

import { Avatar } from "../components/Avatar";
import { useAuth } from "../features/auth/AuthProvider";
import { GESTION_USUARIOS, LECTURA, NOMBRE_ROL } from "../features/auth/roles";
import { MODULOS } from "../features/personas/modulos";
import { useApiStatus } from "../hooks/useApiStatus";
import type { Role } from "../types/auth";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  roles: readonly Role[];
  end?: boolean;
}

// Inmuebles y contratos se agregan en las fases 3 y 4 del plan.
const NAV: readonly NavItem[] = [
  { to: "/", label: "Inicio", icon: LayoutDashboard, roles: LECTURA, end: true },
  { to: MODULOS.clientes.ruta, label: "Clientes", icon: MODULOS.clientes.icon, roles: LECTURA },
  { to: MODULOS.propietarios.ruta, label: "Propietarios", icon: MODULOS.propietarios.icon, roles: LECTURA },
  { to: MODULOS.codeudores.ruta, label: "Codeudores", icon: MODULOS.codeudores.icon, roles: LECTURA },
  { to: "/usuarios", label: "Usuarios", icon: ShieldUser, roles: GESTION_USUARIOS },
];

const RUNTIME_LABELS = { workers: "Cloudflare Workers", asgi: "ASGI (Uvicorn)" } as const;
const STATUS_LABEL = {
  verificando: "Verificando…",
  conectada: "En línea",
  degradada: "Sin base de datos",
  sin_conexion: "Sin conexión",
} as const;
const STATUS_BADGE = {
  verificando: "badge-warn",
  conectada: "badge-ok",
  degradada: "badge-warn",
  sin_conexion: "badge-error",
} as const;

export function MainLayout() {
  const auth = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!drawerOpen) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setDrawerOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  if (auth.status !== "autenticado") {
    return (
      <div className="app-public">
        <header className="public-bar">
          <Brand />
          <SystemStatus compact />
        </header>
        <main id="contenido" className="app-main">
          {auth.status === "cargando" ? (
            <p className="muted" role="status">
              Verificando sesión…
            </p>
          ) : (
            <Outlet />
          )}
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="app">
      <a className="skip-link" href="#contenido">
        Ir al contenido
      </a>
      <aside className="sidebar" aria-label="Barra lateral">
        <SidebarContent />
      </aside>
      <div className="app-body">
        <header className="topbar" aria-label="Barra superior">
          <button
            type="button"
            className="secondary icon-button menu-button"
            aria-label="Abrir menú"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen(true)}
          >
            <Menu size={20} aria-hidden="true" />
          </button>
          <Brand />
          <span className="topbar-spacer" />
          <UserMenu />
        </header>
        <main id="contenido" className="app-main">
          <Outlet />
        </main>
        <Footer />
      </div>
      {drawerOpen && (
        <>
          <div className="drawer-backdrop" onClick={() => setDrawerOpen(false)} />
          <aside className="sidebar drawer" aria-label="Menú de navegación">
            <SidebarContent onClose={() => setDrawerOpen(false)} />
          </aside>
        </>
      )}
    </div>
  );
}

function Brand() {
  return (
    <Link to="/" className="brand">
      <span className="brand-logo" aria-hidden="true">
        <Building2 size={20} />
      </span>
      <span className="brand-text">
        <span className="brand-name">APHIA</span>
        <span className="brand-tagline">Gestión inmobiliaria</span>
      </span>
    </Link>
  );
}

function Footer() {
  return <footer className="app-footer">APHIA S.A.S. · Gestión inmobiliaria · v0.1.0</footer>;
}

function SystemStatus({ compact = false }: { compact?: boolean }) {
  const api = useApiStatus();
  const badge = (
    <span className={`badge ${STATUS_BADGE[api.status]}`}>{STATUS_LABEL[api.status]}</span>
  );
  if (compact) return badge;
  return (
    <div className="system-status">
      <div className="system-status-row">
        <span>Estado del sistema</span>
        {badge}
      </div>
      <span className="muted">
        {api.health ? `${RUNTIME_LABELS[api.health.runtime]} · ${api.health.environment}` : "—"}
      </span>
    </div>
  );
}

function UserMenu() {
  const { principal, logout } = useAuth();
  const navigate = useNavigate();
  if (!principal) return null;
  const rol = principal.roles[0];
  return (
    <div className="topbar-user">
      <Avatar nombre={principal.nombre} tono="primary" />
      <span className="topbar-user-text">
        <strong>{principal.nombre}</strong>
        <span>{rol ? NOMBRE_ROL[rol] : ""}</span>
      </span>
      <button
        type="button"
        className="ghost"
        onClick={() => {
          logout();
          navigate("/login");
        }}
      >
        <LogOut size={18} aria-hidden="true" />
        <span className="nav-label">Cerrar sesión</span>
      </button>
    </div>
  );
}

function SidebarContent({ onClose }: { onClose?: () => void }) {
  const { tiene, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <>
      <div className="brand-row">
        <Brand />
        {onClose && (
          <button
            type="button"
            className="ghost icon-button"
            aria-label="Cerrar menú"
            onClick={onClose}
          >
            <X size={20} aria-hidden="true" />
          </button>
        )}
      </div>
      <nav aria-label="Principal">
        {NAV.filter((item) => tiene(item.roles)).map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} title={label}>
            <Icon size={20} aria-hidden="true" />
            <span className="nav-label">{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <SystemStatus />
        <button
          type="button"
          className="link"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          <LogOut size={18} aria-hidden="true" />
          <span className="label">Salir</span>
        </button>
      </div>
    </>
  );
}
