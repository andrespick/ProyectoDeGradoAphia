import { KeyRound } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { Field } from "../components/Field";
import { useAuth } from "../features/auth/AuthProvider";
import { errorsFromApi, type Errores } from "../features/shared/validation";
import { getPoliticaPublica } from "../services/administracionService";
import { ApiError, errorMessage } from "../services/apiClient";
import { cambiarClave } from "../services/authService";

const CAMPOS = ["clave_actual", "clave_nueva", "confirmacion"] as const;
type Campo = (typeof CAMPOS)[number];

export function CambiarClavePage() {
  const { principal, actualizarSesion } = useAuth();
  const navigate = useNavigate();
  const [valores, setValores] = useState<Record<Campo, string>>({ clave_actual: "", clave_nueva: "", confirmacion: "" });
  const [errores, setErrores] = useState<Errores<Campo>>({});
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [largoMinimo, setLargoMinimo] = useState(8);
  const obligatorio = principal?.debe_cambiar_clave ?? false;

  useEffect(() => {
    const controller = new AbortController();
    getPoliticaPublica(controller.signal)
      .then((politica) => setLargoMinimo(politica.largo_minimo_clave))
      .catch(() => undefined); // la API valida igual; la pista conserva el mínimo general
    return () => controller.abort();
  }, []);

  function update(campo: Campo, value: string) {
    setValores((actual) => ({ ...actual, [campo]: value }));
    setErrores((actual) => ({ ...actual, [campo]: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const validacion: Errores<Campo> = {};
    if (!valores.clave_actual) validacion.clave_actual = "Ingrese su contraseña actual.";
    if (valores.clave_nueva.length < largoMinimo || !/[a-zA-Z]/.test(valores.clave_nueva) || !/\d/.test(valores.clave_nueva)) {
      validacion.clave_nueva = `Mínimo ${largoMinimo} caracteres, con letras y números.`;
    }
    if (valores.confirmacion !== valores.clave_nueva) validacion.confirmacion = "Las contraseñas no coinciden.";
    setErrores(validacion);
    if (Object.keys(validacion).length > 0) return;

    setEnviando(true);
    try {
      actualizarSesion(await cambiarClave(valores.clave_actual, valores.clave_nueva));
      navigate("/", { replace: true });
    } catch (err) {
      if (err instanceof ApiError) setErrores(errorsFromApi(err.details, CAMPOS));
      setError(errorMessage(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="card narrow" aria-labelledby="cambiar-clave-titulo">
      <h1 id="cambiar-clave-titulo">
        <KeyRound size={22} aria-hidden="true" /> Cambiar contraseña
      </h1>
      {obligatorio ? (
        <p className="alert alert-warn">
          El Administrador de Sistemas restableció su contraseña. Cámbiela para continuar.
        </p>
      ) : (
        <p className="muted">Al cambiarla se cierran sus sesiones abiertas en otros equipos.</p>
      )}
      <form className="form" onSubmit={(event) => void handleSubmit(event)} noValidate aria-label="Cambiar contraseña">
        <Field
          id="clave-actual"
          label={obligatorio ? "Contraseña temporal" : "Contraseña actual"}
          type="password"
          value={valores.clave_actual}
          error={errores.clave_actual}
          autoComplete="current-password"
          maxLength={128}
          required
          onChange={(value) => update("clave_actual", value)}
        />
        <Field
          id="clave-nueva"
          label="Contraseña nueva"
          type="password"
          value={valores.clave_nueva}
          error={errores.clave_nueva}
          hint={`Mínimo ${largoMinimo} caracteres, con letras y números`}
          autoComplete="new-password"
          maxLength={128}
          required
          onChange={(value) => update("clave_nueva", value)}
        />
        <Field
          id="clave-confirmacion"
          label="Repita la contraseña nueva"
          type="password"
          value={valores.confirmacion}
          error={errores.confirmacion}
          autoComplete="new-password"
          maxLength={128}
          required
          onChange={(value) => update("confirmacion", value)}
        />
        {error && (
          <p className="alert alert-error" role="alert">
            {error}
          </p>
        )}
        <div className="actions form-actions">
          <button type="submit" disabled={enviando}>
            {enviando ? "Guardando…" : "Cambiar contraseña"}
          </button>
        </div>
      </form>
    </section>
  );
}
