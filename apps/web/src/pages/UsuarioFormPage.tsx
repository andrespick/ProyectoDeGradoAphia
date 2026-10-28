import { UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate, useOutletContext, useParams } from "react-router";

import { SlideOver } from "../components/SlideOver";
import { UsuarioForm } from "../features/usuarios/UsuarioForm";
import { errorMessage } from "../services/apiClient";
import { createUsuario, getUsuario, updateUsuario } from "../services/usuariosService";
import type { Usuario, UsuarioCreate, UsuarioUpdate } from "../types/usuario";
import type { UsuariosOutletContext } from "./UsuariosPage";

export function UsuarioFormPage({ modo }: { modo: "crear" | "editar" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { onSaved } = useOutletContext<UsuariosOutletContext>();
  const [inicial, setInicial] = useState<Usuario | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cerrar = useCallback(
    () => navigate({ pathname: "/usuarios", search: location.search }),
    [navigate, location.search],
  );

  useEffect(() => {
    if (modo !== "editar" || !id) return;
    const controller = new AbortController();
    getUsuario(Number(id), controller.signal)
      .then(setInicial)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [modo, id]);

  async function guardar(input: UsuarioCreate | UsuarioUpdate) {
    if (modo === "crear") {
      await createUsuario(input as UsuarioCreate);
      onSaved("Usuario registrado correctamente.");
    } else {
      await updateUsuario(Number(id), input as UsuarioUpdate);
      onSaved("Usuario actualizado correctamente.");
    }
    cerrar();
  }

  return (
    <SlideOver
      titulo={modo === "crear" ? "Registrar usuario" : "Editar usuario"}
      subtitulo="Cuenta de acceso, rol y datos de la persona"
      icono={<UserPlus size={20} />}
      onClose={cerrar}
    >
      {error && (
        <p className="alert alert-error" role="alert">
          {error}
        </p>
      )}
      {modo === "editar" && !inicial && !error && (
        <p className="muted" role="status">
          Cargando usuario…
        </p>
      )}
      {(modo === "crear" || inicial) && (
        <UsuarioForm modo={modo} inicial={inicial ?? undefined} onSubmit={guardar} onCancel={cerrar} />
      )}
    </SlideOver>
  );
}
