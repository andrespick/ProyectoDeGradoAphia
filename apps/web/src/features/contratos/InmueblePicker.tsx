import { Search, X } from "lucide-react";
import { type FormEvent, useState } from "react";

import { Field } from "../../components/Field";
import { errorMessage } from "../../services/apiClient";
import { listInmuebles } from "../../services/inmueblesService";
import type { Inmueble } from "../../types/inmueble";
import type { InmuebleResumen } from "../../types/persona";

interface InmueblePickerProps {
  idPrefix: string;
  label: string;
  value: InmuebleResumen | null;
  /** Entrega el inmueble completo (con propietarios) al elegirlo de la lista. */
  onChange: (inmueble: Inmueble | null) => void;
  error?: string;
}

/** Busca un inmueble por dirección o matrícula y lo fija como chip con «Cambiar». */
export function InmueblePicker({ idPrefix, label, value, onChange, error }: InmueblePickerProps) {
  const [q, setQ] = useState("");
  const [resultados, setResultados] = useState<Inmueble[] | null>(null);
  const [fallo, setFallo] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  async function buscar(event?: FormEvent) {
    event?.preventDefault();
    setFallo(null);
    if (q.trim().length < 2) {
      setFallo("Escriba al menos dos caracteres de la dirección o la matrícula.");
      return;
    }
    setOcupado(true);
    try {
      const pagina = await listInmuebles({ filtros: { q: q.trim() }, limit: 20, offset: 0 });
      setResultados(pagina.items);
    } catch (err) {
      setFallo(errorMessage(err));
    } finally {
      setOcupado(false);
    }
  }

  if (value) {
    return (
      <div className="field">
        <span className="field-label-text">{label}</span>
        <span className="chip-list">
          <span className="chip chip-persona">
            <strong>{value.direccion}</strong>
            {value.ciudad ? ` · ${value.ciudad}` : ""}
            <button type="button" aria-label={`Cambiar ${label.toLowerCase()}`} onClick={() => onChange(null)}>
              <X size={14} aria-hidden="true" />
            </button>
          </span>
        </span>
      </div>
    );
  }

  return (
    <div className="picker" role="group" aria-label={label}>
      <span className="field-label-text">{label}</span>
      <div className="picker-row">
        <Field
          id={`${idPrefix}-q`}
          label="Dirección o matrícula"
          value={q}
          error={error}
          maxLength={100}
          onChange={setQ}
          onKeyDown={(event) => {
            if (event.key === "Enter") void buscar(event);
          }}
        />
        <button
          type="button"
          className="secondary"
          disabled={ocupado}
          aria-label={`Buscar ${label.toLowerCase()}`}
          onClick={() => void buscar()}
        >
          <Search size={16} aria-hidden="true" /> Buscar
        </button>
      </div>
      {fallo && (
        <p className="field-error" role="alert">
          {fallo}
        </p>
      )}
      {resultados && resultados.length === 0 && <p className="muted">No hay inmuebles que coincidan.</p>}
      {resultados && resultados.length > 0 && (
        <ul className="picker-lista" aria-label={`Resultados de ${label.toLowerCase()}`}>
          {resultados.map((inmueble) => (
            <li key={inmueble.id} className="picker-result">
              <span>
                <strong>{inmueble.direccion}</strong>
                {inmueble.ciudad ? ` · ${inmueble.ciudad}` : ""}
                {inmueble.matricula ? ` · ${inmueble.matricula}` : ""}
                <span className="muted"> · {inmueble.propietarios.map((p) => p.nombre).join(", ") || "sin propietarios"}</span>
              </span>
              <button type="button" onClick={() => onChange(inmueble)}>
                Seleccionar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
