import { X } from "lucide-react";

import { identificacionDe, type Papel, type PersonaResumen } from "../../types/persona";
import { PersonaPicker } from "./PersonaPicker";

interface PersonaListPickerProps {
  idPrefix: string;
  label: string;
  papel: Papel;
  value: PersonaResumen[];
  onChange: (personas: PersonaResumen[]) => void;
  error?: string;
}

/** Varias personas (propietarios de un inmueble, codeudores de un contrato). */
export function PersonaListPicker({ idPrefix, label, papel, value, onChange, error }: PersonaListPickerProps) {
  return (
    <div className="field">
      {value.length > 0 && (
        <ul className="chip-list chip-list-block" aria-label={label}>
          {value.map((persona) => (
            <li key={persona.id} className="chip chip-persona">
              <strong>{persona.nombre}</strong> · {identificacionDe(persona)}
              <button
                type="button"
                aria-label={`Quitar ${persona.nombre}`}
                onClick={() => onChange(value.filter((p) => p.id !== persona.id))}
              >
                <X size={14} aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <PersonaPicker
        idPrefix={idPrefix}
        label={value.length > 0 ? `Agregar otro ${label.toLowerCase()}` : label}
        papel={papel}
        value={null}
        excluir={value.map((p) => p.id)}
        onChange={(persona) => persona && onChange([...value, persona])}
      />
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
