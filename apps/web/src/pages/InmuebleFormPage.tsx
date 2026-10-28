import { Building2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate, useOutletContext, useParams } from "react-router";

import { SlideOver } from "../components/SlideOver";
import { InmuebleForm } from "../features/inmuebles/InmuebleForm";
import { errorMessage } from "../services/apiClient";
import { invalidateCatalogos } from "../services/catalogosService";
import { createInmueble, getInmueble, updateInmueble } from "../services/inmueblesService";
import type { Inmueble, InmuebleCreate } from "../types/inmueble";
import type { InmueblesOutletContext } from "./InmueblesPage";

export function InmuebleFormPage({ modo }: { modo: "crear" | "editar" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { onSaved } = useOutletContext<InmueblesOutletContext>();
  const [inicial, setInicial] = useState<Inmueble | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cerrar = useCallback(
    () => navigate({ pathname: "/inmuebles", search: location.search }),
    [navigate, location.search],
  );

  useEffect(() => {
    if (modo !== "editar" || !id) return;
    const controller = new AbortController();
    getInmueble(Number(id), controller.signal)
      .then(setInicial)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [modo, id]);

  async function guardar(input: InmuebleCreate) {
    if (modo === "crear") {
      await createInmueble(input);
      onSaved("Inmueble registrado correctamente.");
    } else {
      await updateInmueble(Number(id), input);
      onSaved("Inmueble actualizado correctamente.");
    }
    invalidateCatalogos(); // ciudades y proveedores nuevos aparecen en las sugerencias
    cerrar();
  }

  return (
    <SlideOver
      titulo={modo === "crear" ? "Registrar nuevo inmueble" : "Editar inmueble"}
      subtitulo="Expediente catastral, servicios y titularidad"
      icono={<Building2 size={20} />}
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
        <InmuebleForm modo={modo} inicial={inicial ?? undefined} onSubmit={guardar} onCancel={cerrar} />
      )}
    </SlideOver>
  );
}
