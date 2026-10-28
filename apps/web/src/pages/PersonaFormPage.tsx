import { UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate, useOutletContext, useParams } from "react-router";

import { SlideOver } from "../components/SlideOver";
import { type Modulo, MODULOS } from "../features/personas/modulos";
import { PersonaForm } from "../features/personas/PersonaForm";
import { errorMessage } from "../services/apiClient";
import { invalidateCatalogos } from "../services/catalogosService";
import { createPersona, getPersona, updatePersona } from "../services/personasService";
import type { PersonaCreate, PersonaDetalle } from "../types/persona";
import type { PersonasOutletContext } from "./PersonasListPage";

export function PersonaFormPage({ modulo, modo }: { modulo: Modulo; modo: "crear" | "editar" }) {
  const config = MODULOS[modulo];
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { onSaved } = useOutletContext<PersonasOutletContext>();
  const [inicial, setInicial] = useState<PersonaDetalle | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cerrar = useCallback(
    () => navigate({ pathname: config.ruta, search: location.search }),
    [navigate, config.ruta, location.search],
  );

  useEffect(() => {
    if (modo !== "editar" || !id) return;
    const controller = new AbortController();
    getPersona(config.api, Number(id), controller.signal)
      .then(setInicial)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [modo, id, config.api]);

  async function guardar(input: PersonaCreate) {
    if (modo === "crear") {
      await createPersona(config.api, input);
      onSaved(`${capitalizar(config.singular)} registrado correctamente.`);
    } else {
      await updatePersona(config.api, Number(id), input);
      onSaved(`${capitalizar(config.singular)} actualizado correctamente.`);
    }
    if (input.cuenta_bancaria) invalidateCatalogos(); // puede haber un banco nuevo
    cerrar();
  }

  return (
    <SlideOver
      titulo={modo === "crear" ? `Registrar ${config.singular}` : `Editar ${config.singular}`}
      subtitulo="Identificación, contacto, tipo de cliente y cuenta bancaria"
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
          Cargando…
        </p>
      )}
      {(modo === "crear" || inicial) && (
        <PersonaForm
          modo={modo}
          papelFijo={config.papelFijo}
          inicial={inicial ?? undefined}
          onSubmit={guardar}
          onCancel={cerrar}
          etiquetaGuardar={`Guardar ${config.singular}`}
        />
      )}
    </SlideOver>
  );
}

function capitalizar(texto: string): string {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}
