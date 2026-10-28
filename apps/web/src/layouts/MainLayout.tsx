import { Building2, Gauge, LayoutDashboard, type LucideIcon, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";

import { useApiStatus } from "../hooks/useApiStatus";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

// Los módulos de negocio y «Usuarios» se agregan en las fases 1–5 según el rol.
const NAV: readonly NavItem[] = [
  { to: "/", label: "Inicio", icon: LayoutDashboard, end: true },
  { to: "/panel", label: "Panel", icon: Gauge },
];

const STATUS_LABEL = {
  verificando: "Verificando…",
  conectada: "En línea",
  degradada: "Sin base de datos",
  sin_conexion: "Sin conexión",
} as const;

const STATUS_DOT = {
  verificando: "status-dot-warn",
  conectada: "status-dot-ok",
  degradada: "status-dot-warn",
  sin_conexion: "status-dot-error",
} as const;

export function MainLayout() {
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

  return (
    <div className="app">
      <a className="skip-link" href="#contenido">
        Ir al contenido
      </a>
      <aside className="sidebar" aria-label="Barra lateral">
        <SidebarContent />
      </aside>
      <div className="app-body">
        <header className="topbar">
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
        </header>
        <main id="contenido" className="app-main">
          <Outlet />
        </main>
        <footer className="app-footer">APHIA S.A.S. · Gestión inmobiliaria · v0.1.0</footer>
      </div>
      {drawerOpen && (
        <>
          <div className="drawer-backdrop" onClick={() => setDrawerOpen(false)} />
          <aside className="sidebar drawer" aria-label="Menú de navegación">
            <SidebarContent
              onClose={() => setDrawerOpen(false)}
            />
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

function SidebarContent({ onClose }: { onClose?: () => void }) {
  const api = useApiStatus();
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
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} title={label}>
            <Icon size={20} aria-hidden="true" />
            <span className="nav-label">{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="system-status">
          <div className="system-status-row">
            <span>Estado del sistema</span>
            <span className={`badge ${api.status === "conectada" ? "badge-ok" : api.status === "sin_conexion" ? "badge-error" : "badge-warn"}`}>
              <span className={STATUS_DOT[api.status]} aria-hidden="true" />
              {STATUS_LABEL[api.status]}
            </span>
          </div>
          <span className="muted">Servidor {api.health ? api.health.environment : "—"}</span>
        </div>
      </div>
    </>
  );
}
