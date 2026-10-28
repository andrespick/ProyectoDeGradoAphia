import { FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { ContratoForm } from "../features/contratos/ContratoForm";
import { errorMessage } from "../services/apiClient";
import { createContrato, getContrato, updateContrato } from "../services/contratosService";
import type { Contrato, ContratoCreate } from "../types/contrato";

export const MENSAJE_GUARDADO =
  "Contrato guardado. Recuerde actualizar el estado de ocupación del inmueble si corresponde.";

export function ContratoFormPage({ modo }: { modo: "crear" | "editar" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [inicial, setInicial] = useState<Contrato | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (modo !== "editar" || !id) return;
    const controller = new AbortController();
    getContrato(Number(id), controller.signal)
      .then(setInicial)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [modo, id]);

  async function guardar(input: ContratoCreate) {
    const contrato = modo === "crear" ? await createContrato(input) : await updateContrato(Number(id), input);
    navigate(`/contratos/${contrato.id}`, { state: { mensaje: MENSAJE_GUARDADO } });
  }

  const titulo = modo === "crear" ? "Nuevo contrato" : `Editar contrato #${id}`;

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>
          <Link to="/contratos">Contratos</Link>
        </span>
        <span>{titulo}</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <FileText size={20} />
          </span>
          <div>
            <h1>{titulo}</h1>
            <p>Los propietarios se toman del inmueble elegido; puede ajustarlos antes de guardar.</p>
          </div>
        </div>
      </header>
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
        <section className="card">
          <ContratoForm
            modo={modo}
            inicial={inicial ?? undefined}
            onSubmit={guardar}
            onCancel={() => navigate(inicial ? `/contratos/${inicial.id}` : "/contratos")}
          />
        </section>
      )}
    </>
  );
}
