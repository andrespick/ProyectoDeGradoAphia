import { type FormEvent, useState } from "react";

import { Field } from "../../components/Field";
import { SelectField } from "../../components/SelectField";
import { ApiError, errorMessage } from "../../services/apiClient";
import { NOMBRE_PAPEL, PAPELES, type Papel, type Persona, type PersonaCreate } from "../../types/persona";
import { useCatalogos } from "../catalogos/useCatalogos";
import { errorsFromApi } from "../shared/validation";
import {
  aPersonaCreate,
  CAMPOS_PERSONA,
  type PersonaErrors,
  type PersonaFormValues,
  validatePersona,
  valoresIniciales,
} from "./validation";

interface PersonaFormProps {
  modo: "crear" | "editar";
  papelFijo: Papel | null;
  inicial?: Persona;
  onSubmit: (input: PersonaCreate) => Promise<unknown>;
  onCancel: () => void;
  /** Texto del botón de guardar (p. ej. «Guardar cliente»). */
  etiquetaGuardar?: string;
}

export function PersonaForm({
  modo,
  papelFijo,
  inicial,
  onSubmit,
  onCancel,
  etiquetaGuardar = "Guardar",
}: PersonaFormProps) {
  const { catalogos } = useCatalogos();
  const [values, setValues] = useState<PersonaFormValues>(() => valoresIniciales(inicial, papelFijo));
  const [errors, setErrors] = useState<PersonaErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof PersonaFormValues>(field: K, value: PersonaFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function togglePapel(papel: Papel, checked: boolean) {
    const papeles = checked
      ? PAPELES.filter((p) => p === papel || values.papeles.includes(p))
      : values.papeles.filter((p) => p !== papel);
    update("papeles", papeles);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    const limpio: PersonaFormValues = {
      ...values,
      nombre: values.nombre.trim(),
      identificacion: values.identificacion.trim(),
      telefono: values.telefono.trim(),
      correo: values.correo.trim(),
      direccion: values.direccion.trim(),
      banco: values.banco.trim(),
      cuentaNumero: values.cuentaNumero.trim(),
    };
    const validation = validatePersona(limpio, papelFijo);
    setErrors(validation);
    if (Object.keys(validation).length > 0) return;
    setSubmitting(true);
    try {
      await onSubmit(aPersonaCreate(limpio));
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(errorsFromApi(error.details, CAMPOS_PERSONA));
        setFormError(errorMessage(error));
      } else {
        setFormError("No fue posible guardar la información.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const tipos = (catalogos?.tipos_identificacion ?? []).map((o) => ({ value: o.codigo, label: o.nombre }));
  const papelesOpciones = (catalogos?.papeles ?? []).map((o) => ({ value: o.codigo, label: o.nombre }));
  const tiposCuenta = (catalogos?.tipos_cuenta_bancaria ?? []).map((o) => ({ value: o.codigo, label: o.nombre }));
  const seleccionUnica = modo === "crear" && papelFijo === null;

  return (
    <form
      className="form"
      onSubmit={handleSubmit}
      noValidate
      aria-label={modo === "crear" ? `Registrar ${papelFijo ?? "cliente"}` : "Editar persona"}
    >
      <div className="form-section">
        <h3>1. Identificación</h3>
        <div className="form-grid">
          <Field
            id="persona-nombre"
            label="Nombre completo"
            value={values.nombre}
            error={errors.nombre}
            maxLength={255}
            required
            className="span-2"
            onChange={(value) => update("nombre", value)}
          />
          <SelectField
            id="persona-tipo"
            label="Tipo de identificación"
            value={values.tipo_identificacion}
            options={tipos}
            error={errors.tipo_identificacion}
            required
            onChange={(value) => update("tipo_identificacion", value)}
          />
          <Field
            id="persona-identificacion"
            label="Identificación"
            value={values.identificacion}
            error={errors.identificacion}
            maxLength={50}
            required
            onChange={(value) => update("identificacion", value)}
          />
        </div>
      </div>

      <div className="form-section">
        <h3>2. Contacto</h3>
        <div className="form-grid">
          <Field
            id="persona-telefono"
            label="Teléfono"
            type="tel"
            inputMode="tel"
            value={values.telefono}
            error={errors.telefono}
            maxLength={50}
            required={papelFijo === "propietario"}
            onChange={(value) => update("telefono", value)}
          />
          <Field
            id="persona-correo"
            label="Correo electrónico"
            type="email"
            value={values.correo}
            error={errors.correo}
            maxLength={254}
            required={papelFijo === "propietario"}
            onChange={(value) => update("correo", value)}
          />
          <Field
            id="persona-direccion"
            label="Dirección"
            value={values.direccion}
            error={errors.direccion}
            maxLength={255}
            required={papelFijo === "propietario"}
            className="span-2"
            onChange={(value) => update("direccion", value)}
          />
        </div>
      </div>

      <div className="form-section">
        <h3>3. Tipo de cliente</h3>
        {seleccionUnica ? (
          <SelectField
            id="persona-papel"
            label="Tipo de cliente"
            value={values.papeles[0] ?? ""}
            options={papelesOpciones}
            error={errors.papeles}
            hint="Podrá agregar otros papeles más adelante al editar la persona."
            required
            onChange={(value) => update("papeles", value ? [value as Papel] : [])}
          />
        ) : (
          <fieldset className="field">
            <legend className="field-label-text">Papeles</legend>
            <div className="choices" role="group">
              {PAPELES.map((papel) => (
                <label key={papel}>
                  <input
                    type="checkbox"
                    checked={values.papeles.includes(papel)}
                    disabled={papel === papelFijo}
                    onChange={(event) => togglePapel(papel, event.target.checked)}
                  />
                  {NOMBRE_PAPEL[papel]}
                </label>
              ))}
            </div>
            {errors.papeles && <p className="field-error">{errors.papeles}</p>}
          </fieldset>
        )}
      </div>

      <div className="form-section">
        <h3>4. Cuenta bancaria {papelFijo === "propietario" ? "" : "(opcional)"}</h3>
        {papelFijo !== "propietario" && (
          <label className="checkbox">
            <input
              type="checkbox"
              checked={values.conCuenta}
              onChange={(event) => update("conCuenta", event.target.checked)}
            />
            Registrar cuenta bancaria
          </label>
        )}
        {values.conCuenta && (
          <div className="form-grid">
            <Field
              id="persona-banco"
              label="Banco"
              value={values.banco}
              error={errors["cuenta_bancaria.banco"]}
              list="bancos-sugeridos"
              maxLength={255}
              required
              onChange={(value) => update("banco", value)}
            />
            <datalist id="bancos-sugeridos">
              {(catalogos?.bancos ?? []).map((banco) => (
                <option key={banco} value={banco} />
              ))}
            </datalist>
            <SelectField
              id="persona-cuenta-tipo"
              label="Tipo de cuenta"
              value={values.cuentaTipo}
              options={tiposCuenta}
              error={errors["cuenta_bancaria.tipo"]}
              required
              onChange={(value) => update("cuentaTipo", value)}
            />
            <Field
              id="persona-cuenta-numero"
              label="Número de cuenta"
              inputMode="numeric"
              value={values.cuentaNumero}
              error={errors["cuenta_bancaria.numero"]}
              maxLength={50}
              required
              className="span-2"
              onChange={(value) => update("cuentaNumero", value)}
            />
          </div>
        )}
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
          {submitting ? "Guardando…" : etiquetaGuardar}
        </button>
      </div>
    </form>
  );
}
