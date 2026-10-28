export function LoginPage() {
  return (
    <section className="card narrow" aria-labelledby="login-titulo">
      <h1 id="login-titulo">Iniciar sesión</h1>
      <p>
        El inicio de sesión todavía no está implementado. Esta ruta existe para validar el flujo
        de rutas protegidas.
      </p>
      <p className="muted">
        En desarrollo local la API entrega un usuario ficticio (AUTH_MODE=development). En staging
        y producción las rutas protegidas permanecen cerradas hasta implementar la autenticación.
      </p>
    </section>
  );
}
