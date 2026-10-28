import { Building2, Eye, EyeOff, LockKeyhole, LogIn, ShieldCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, Navigate, useLocation } from "react-router";

import { Field } from "../components/Field";
import { useAuth } from "../features/auth/AuthProvider";
import { ApiError } from "../services/apiClient";

export function LoginPage() {
  const auth = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;
  const destino = from && from !== "/login" ? from : "/";
  const [usuario, setUsuario] = useState("");
  const [clave, setClave] = useState("");
  const [recordar, setRecordar] = useState(false);
  const [verClave, setVerClave] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (auth.status === "autenticado") return <Navigate to={destino} replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!usuario.trim() || !clave) {
      setError("Ingrese su usuario y su contraseña.");
      return;
    }
    setEnviando(true);
    try {
      await auth.login(usuario.trim(), clave, recordar); // al autenticarse, <Navigate> redirige
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "No fue posible iniciar sesión. Intente de nuevo.",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login-layout">
      <section className="login-intro" aria-labelledby="login-intro-titulo">
        <span className="badge badge-primary">
          <ShieldCheck size={14} aria-hidden="true" /> Portal administrativo
        </span>
        <h1 id="login-intro-titulo">Gestión integral de propiedad horizontal e inmobiliaria.</h1>
        <p className="muted">
          Control unificado de clientes, propietarios, inmuebles y contratos de APHIA S.A.S.
        </p>
        <p className="login-note">
          <LockKeyhole size={16} aria-hidden="true" /> Acceso corporativo protegido: la cuenta se
          bloquea 15 minutos tras 3 intentos fallidos.
        </p>
      </section>

      <section className="card login-card" aria-labelledby="login-titulo">
        <span className="brand-logo login-logo" aria-hidden="true">
          <Building2 size={22} />
        </span>
        <h1 id="login-titulo">Iniciar sesión</h1>
        <p className="muted">Ingrese con sus credenciales institucionales</p>
        <form className="form" onSubmit={handleSubmit} noValidate aria-label="Iniciar sesión">
          <Field
            id="login-usuario"
            label="Usuario"
            value={usuario}
            autoComplete="username"
            maxLength={255}
            onChange={setUsuario}
          />
          <div className="field-with-action">
            <Field
              id="login-clave"
              label="Contraseña"
              type={verClave ? "text" : "password"}
              value={clave}
              autoComplete="current-password"
              maxLength={128}
              onChange={setClave}
            />
            <button
              type="button"
              className="ghost icon-button field-action"
              aria-label={verClave ? "Ocultar contraseña" : "Mostrar contraseña"}
              aria-pressed={verClave}
              onClick={() => setVerClave((current) => !current)}
            >
              {verClave ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
            </button>
          </div>
          <div className="login-options">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={recordar}
                onChange={(event) => setRecordar(event.target.checked)}
              />
              Recordarme en este equipo
            </label>
            <Link to="/ayuda#inicio-de-sesion" className="muted">
              ¿Olvidó su contraseña?
            </Link>
          </div>
          {error && (
            <p className="alert alert-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="login-submit" disabled={enviando}>
            <LogIn size={18} aria-hidden="true" />
            {enviando ? "Verificando…" : "Iniciar sesión"}
          </button>
        </form>
      </section>
    </div>
  );
}
