import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <section className="card narrow" aria-labelledby="no-encontrada-titulo">
      <h1 id="no-encontrada-titulo">Página no encontrada</h1>
      <p>
        <Link to="/">Volver al inicio</Link>
      </p>
    </section>
  );
}
