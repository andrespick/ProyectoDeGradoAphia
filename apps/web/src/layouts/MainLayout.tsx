import { NavLink, Outlet } from "react-router";

export function MainLayout() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-name">APHIA</span>
          <span className="brand-tagline">Gestión inmobiliaria</span>
        </div>
        <nav aria-label="Principal">
          <NavLink to="/" end>
            Inicio
          </NavLink>
          <NavLink to="/panel">Panel</NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">APHIA S.A.S. · entorno de desarrollo · v0.1.0</footer>
    </div>
  );
}
