import { type FormEvent, useState } from "react";

import { Field } from "../../components/Field";
import { ApiError, errorMessage } from "../../services/apiClient";
import type { Inmueble, InmuebleCreate } from "../../types/inmueble";
import { useCatalogos } from "../catalogos/useCatalogos";
import { PersonaListPicker } from "../personas/PersonaListPicker";
import { errorsFromApi } from "../shared/validation";
import { ServiciosEditor } from "./ServiciosEditor";
import {
  aInmuebleCreate,
  CAMPOS_INMUEBLE,
  type InmuebleErrors,
  type InmuebleFormValues,
  validateInmueble,
  valoresIniciales,
} from "./validation";

interface InmuebleFormProps {
  modo: "crear" | "editar";
  inicial?: Inmueble;
  onSubmit: (input: InmuebleCreate) => Promise<unknown>;
  onCancel: () => void;
}

export function InmuebleForm({ modo, inicial, onSubmit, onCancel }: InmuebleFormProps) {
  const { catalogos } = useCatalogos();
  const [values, setValues] = useState<InmuebleFormValues>(() => valoresIniciales(inicial));
  const [errors, setErrors] = useState<InmuebleErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof InmuebleFormValues>(field: K, value: InmuebleFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    const campo = field === "propietarios" ? "propietarios_ids" : field;
    setErrors((current) => ({ ...current, [campo]: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    const validation = validateInmueble(values);
    setErrors(validation);
    if (Object.keys(validation).length > 0) return;
    setSubmitting(true);
    try {
      await onSubmit(aInmuebleCreate(values));
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(errorsFromApi(error.details, CAMPOS_INMUEBLE));
        setFormError(errorMessage(error));
      } else {
        setFormError("No fue posible guardar el inmueble.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const estados = catalogos?.estados_ocupacion ?? [];

  return (
    <form
      className="form"
      onSubmit={handleSubmit}
      noValidate
      aria-label={modo === "crear" ? "Registrar inmueble" : "Editar inmueble"}
    >
      <p className="alert alert-info">
        Los datos ingresados se vinculan al módulo de contratos y al detalle de cada propietario.
      </p>
      <div className="form-section">
        <h3>1. Identificación y localización</h3>
        <div className="form-grid">
          <Field
            id="inmueble-direccion"
            label="Dirección completa"
            value={values.direccion}
            error={errors.direccion}
            placeholder="Ej: Calle 93B # 11A-44 Apto 502"
            maxLength={255}
            required
            className="span-2"
            onChange={(value) => update("direccion", value)}
          />
          <Field
            id="inmueble-ciudad"
            label="Ciudad / municipio"
            value={values.ciudad}
            error={errors.ciudad}
            list="ciudades-sugeridas"
            maxLength={255}
            onChange={(value) => update("ciudad", value)}
          />
          <datalist id="ciudades-sugeridas">
            {(catalogos?.ciudades ?? []).map((ciudad) => (
              <option key={ciudad.id} value={ciudad.nombre} />
            ))}
          </datalist>
          <Field
            id="inmueble-matricula"
            label="Matrícula inmobiliaria"
            value={values.matricula}
            error={errors.matricula}
            placeholder="Ej: 50C-184920"
            maxLength={255}
            onChange={(value) => update("matricula", value)}
          />
        </div>
      </div>

      <div className="form-section">
        <h3>2. Canon y titularidad</h3>
        <PersonaListPicker
          idPrefix="inmueble-propietario"
          label="Propietario legal asociado"
          papel="propietario"
          value={values.propietarios}
          error={errors.propietarios_ids}
          onChange={(propietarios) => update("propietarios", propietarios)}
        />
        <div className="form-grid">
          <Field
            id="inmueble-canon"
            label="Canon mensual (COP)"
            inputMode="decimal"
            value={values.canon}
            error={errors.canon}
            placeholder="Ej: 1.500.000"
            maxLength={20}
            onChange={(value) => update("canon", value)}
          />
          <fieldset className="field">
            <legend className="field-label-text">Estado de ocupación</legend>
            <div className="choices" role="radiogroup" aria-label="Estado de ocupación">
              {estados.map((estado) => (
                <label key={estado.codigo}>
                  <input
                    type="radio"
                    name="inmueble-estado"
                    value={estado.codigo}
                    checked={values.estado === estado.codigo}
                    onChange={() => update("estado", estado.codigo)}
                  />
                  {estado.nombre}
                </label>
              ))}
            </div>
            {errors.estado && <p className="field-error">{errors.estado}</p>}
          </fieldset>
        </div>
      </div>

      <div className="form-section">
        <h3>3. Cuentas de servicios públicos</h3>
        <ServiciosEditor
          value={values.servicios}
          onChange={(servicios) => update("servicios", servicios)}
          tipos={catalogos?.tipos_servicio ?? []}
          proveedores={catalogos?.proveedores_servicios ?? []}
          error={errors.servicios}
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
          {submitting ? "Guardando…" : "Guardar inmueble"}
        </button>
      </div>
    </form>
  );
}
