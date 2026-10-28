import { Plus, Trash2 } from "lucide-react";

import { Field } from "../../components/Field";
import { SelectField } from "../../components/SelectField";
import type { Opcion } from "../../types/catalogos";
import type { ServicioFormValues } from "./validation";

interface ServiciosEditorProps {
  value: ServicioFormValues[];
  onChange: (servicios: ServicioFormValues[]) => void;
  tipos: Opcion[];
  proveedores: string[];
  error?: string;
}

const VACIO: ServicioFormValues = { tipo: "", proveedor: "", numero_contrato: "" };

/** Lista editable de contratos de servicios públicos (tipo, proveedor y número). */
export function ServiciosEditor({ value, onChange, tipos, proveedores, error }: ServiciosEditorProps) {
  function update(index: number, cambios: Partial<ServicioFormValues>) {
    onChange(value.map((s, i) => (i === index ? { ...s, ...cambios } : s)));
  }
  return (
    <div className="servicios-editor">
      {value.length === 0 && <p className="muted">Sin servicios registrados.</p>}
      {value.map((servicio, index) => (
        <div key={index} className="servicio-fila" role="group" aria-label={`Servicio ${index + 1}`}>
          <SelectField
            id={`servicio-${index}-tipo`}
            label="Tipo de servicio"
            value={servicio.tipo}
            options={tipos.map((t) => ({ value: t.codigo, label: t.nombre }))}
            placeholder="Sin especificar"
            onChange={(tipo) => update(index, { tipo })}
          />
          <Field
            id={`servicio-${index}-proveedor`}
            label="Proveedor"
            value={servicio.proveedor}
            list="proveedores-sugeridos"
            maxLength={255}
            onChange={(proveedor) => update(index, { proveedor })}
          />
          <Field
            id={`servicio-${index}-numero`}
            label="Número de contrato"
            value={servicio.numero_contrato}
            maxLength={255}
            required
            onChange={(numero_contrato) => update(index, { numero_contrato })}
          />
          <button
            type="button"
            className="ghost icon-button servicio-quitar"
            aria-label={`Quitar servicio ${index + 1}`}
            onClick={() => onChange(value.filter((_, i) => i !== index))}
          >
            <Trash2 size={18} aria-hidden="true" />
          </button>
        </div>
      ))}
      <datalist id="proveedores-sugeridos">
        {proveedores.map((proveedor) => (
          <option key={proveedor} value={proveedor} />
        ))}
      </datalist>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <button type="button" className="secondary" disabled={value.length >= 20} onClick={() => onChange([...value, VACIO])}>
        <Plus size={16} aria-hidden="true" /> Agregar servicio
      </button>
    </div>
  );
}
