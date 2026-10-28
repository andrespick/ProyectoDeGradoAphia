import { type FormEvent, useState } from "react";

import { Field } from "../../components/Field";
import { SelectField } from "../../components/SelectField";
import { TextAreaField } from "../../components/TextAreaField";
import { ApiError } from "../../services/apiClient";
import type { Contrato, ContratoCreate } from "../../types/contrato";
import { useCatalogos } from "../catalogos/useCatalogos";
import { PersonaListPicker } from "../personas/PersonaListPicker";
import { PersonaPicker } from "../personas/PersonaPicker";
import { errorsFromApi } from "../shared/validation";
import { InmueblePicker } from "./InmueblePicker";
import {
  aContratoCreate,
  CAMPOS_CONTRATO,
  type ContratoErrors,
  type ContratoFormValues,
  validateContrato,
  valoresIniciales,
} from "./validation";

interface ContratoFormProps {
  modo: "crear" | "editar";
  inicial?: Contrato;
  onSubmit: (input: ContratoCreate) => Promise<unknown>;
  onCancel: () => void;
}

const CAMPO_DE: Partial<Record<keyof ContratoFormValues, keyof ContratoErrors>> = {
  inmueble: "inmueble_id",
  canon: "canon_pactado",
  propietarios: "propietarios_ids",
  arrendatario: "arrendatario_id",
  codeudores: "codeudores_ids",
};

export function ContratoForm({ modo, inicial, onSubmit, onCancel }: ContratoFormProps) {
  const { catalogos } = useCatalogos();
  const [values, setValues] = useState<ContratoFormValues>(() => valoresIniciales(inicial));
  const [errors, setErrors] = useState<ContratoErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof ContratoFormValues>(field: K, value: ContratoFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [CAMPO_DE[field] ?? field]: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    const validation = validateContrato(values);
    setErrors(validation);
    if (Object.keys(validation).length > 0) return;
    setSubmitting(true);
    try {
      await onSubmit(aContratoCreate(values));
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(errorsFromApi(error.details, CAMPOS_CONTRATO));
        setFormError(error.message);
      } else {
        setFormError("No fue posible guardar el contrato.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const tipos = (catalogos?.tipos_contrato ?? []).map((t) => ({ value: t.codigo, label: t.nombre }));

  return (
    <form
      className="form"
      onSubmit={handleSubmit}
      noValidate
      aria-label={modo === "crear" ? "Registrar contrato" : "Editar contrato"}
    >
      <div className="form-section">
        <h3>1. Datos del contrato</h3>
        <div className="form-grid">
          <SelectField
            id="contrato-tipo"
            label="Tipo de contrato"
            value={values.tipo}
            options={tipos}
            error={errors.tipo}
            onChange={(tipo) => update("tipo", tipo)}
          />
          <Field
            id="contrato-canon"
            label="Canon pactado (COP)"
            inputMode="decimal"
            value={values.canon}
            error={errors.canon_pactado}
            placeholder="Ej: 1.500.000"
            maxLength={20}
            onChange={(canon) => update("canon", canon)}
          />
          <Field
            id="contrato-inicio"
            label="Fecha de inicio"
            type="date"
            value={values.fecha_inicio}
            error={errors.fecha_inicio}
            required
            onChange={(fecha) => update("fecha_inicio", fecha)}
          />
          <Field
            id="contrato-fin"
            label="Fecha de fin"
            type="date"
            value={values.fecha_fin}
            error={errors.fecha_fin}
            hint="Déjela vacía si el contrato es indefinido."
            onChange={(fecha) => update("fecha_fin", fecha)}
          />
        </div>
        <InmueblePicker
          idPrefix="contrato-inmueble"
          label="Inmueble"
          value={values.inmueble}
          error={errors.inmueble_id}
          onChange={(inmueble) => {
            update("inmueble", inmueble);
            // Al elegir el inmueble, los propietarios del contrato parten de sus dueños actuales.
            if (inmueble) update("propietarios", inmueble.propietarios);
          }}
        />
      </div>

      <div className="form-section">
        <h3>2. Partes</h3>
        <PersonaListPicker
          idPrefix="contrato-propietario"
          label="Propietarios"
          papel="propietario"
          value={values.propietarios}
          error={errors.propietarios_ids}
          onChange={(propietarios) => update("propietarios", propietarios)}
        />
        <PersonaPicker
          idPrefix="contrato-arrendatario"
          label="Arrendatario"
          papel="arrendatario"
          value={values.arrendatario}
          excluir={values.codeudores.map((c) => c.id)}
          onChange={(arrendatario) => update("arrendatario", arrendatario)}
        />
        {errors.arrendatario_id && <p className="field-error">{errors.arrendatario_id}</p>}
        <PersonaListPicker
          idPrefix="contrato-codeudor"
          label="Codeudores"
          papel="codeudor"
          value={values.codeudores}
          error={errors.codeudores_ids}
          excluir={values.arrendatario ? [values.arrendatario.id] : []}
          onChange={(codeudores) => update("codeudores", codeudores)}
        />
      </div>

      <div className="form-section">
        <h3>3. Condiciones y texto</h3>
        <TextAreaField
          id="contrato-condiciones"
          label="Condiciones"
          value={values.condiciones}
          error={errors.condiciones}
          rows={4}
          maxLength={20000}
          onChange={(condiciones) => update("condiciones", condiciones)}
        />
        <TextAreaField
          id="contrato-texto"
          label="Texto completo del contrato (para impresión)"
          value={values.texto}
          error={errors.texto}
          rows={12}
          maxLength={1000000}
          onChange={(texto) => update("texto", texto)}
        />
      </div>

      {formError && (
        <p className="alert alert-error" role="alert">
          {formError}
        </p>
      )}
      <div className="actions form-actions">
        <button type="button" className="secondary" onClick={onCancel}>
          Cancelar
        </button>
        <button type="submit" disabled={submitting}>
          {submitting ? "Guardando…" : "Guardar contrato"}
        </button>
      </div>
    </form>
  );
}
