import { type FormEvent, useState } from "react";

import { Field } from "../../components/Field";
import { SelectField } from "../../components/SelectField";
import { ApiError, errorMessage } from "../../services/apiClient";
import type { Role } from "../../types/auth";
import type { Usuario, UsuarioCreate, UsuarioUpdate } from "../../types/usuario";
import { useCatalogos } from "../catalogos/useCatalogos";
import { errorsFromApi } from "../shared/validation";
import {
  CAMPOS_USUARIO,
  type UsuarioErrors,
  type UsuarioFormValues,
  validateUsuario,
} from "./validation";

interface UsuarioFormProps {
  modo: "crear" | "editar";
  inicial?: Usuario;
  onSubmit: (input: UsuarioCreate | UsuarioUpdate) => Promise<unknown>;
  onCancel: () => void;
}

function valoresIniciales(inicial?: Usuario): UsuarioFormValues {
  return {
    usuario: inicial?.usuario ?? "",
    nombre: inicial?.nombre ?? "",
    tipo_identificacion: inicial?.tipo_identificacion ?? "",
    identificacion: inicial?.identificacion ?? "",
    correo: inicial?.correo ?? "",
    clave: "",
    rol: inicial?.rol ?? "",
    activo: inicial?.activo ?? true,
  };
}

export function UsuarioForm({ modo, inicial, onSubmit, onCancel }: UsuarioFormProps) {
  const { catalogos } = useCatalogos();
  const [values, setValues] = useState<UsuarioFormValues>(() => valoresIniciales(inicial));
  const [errors, setErrors] = useState<UsuarioErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof UsuarioFormValues>(field: K, value: UsuarioFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    const limpio: UsuarioFormValues = {
      ...values,
      usuario: values.usuario.trim(),
      nombre: values.nombre.trim(),
      identificacion: values.identificacion.trim(),
      correo: values.correo.trim(),
    };
    const validation = validateUsuario(limpio, modo);
    setErrors(validation);
    if (Object.keys(validation).length > 0 || !limpio.rol) return;

    const base = {
      nombre: limpio.nombre,
      tipo_identificacion: limpio.tipo_identificacion,
      identificacion: limpio.identificacion,
      correo: limpio.correo,
      rol: limpio.rol as Role,
    };
    const input: UsuarioCreate | UsuarioUpdate =
      modo === "crear"
        ? { ...base, usuario: limpio.usuario, clave: limpio.clave }
        : { ...base, activo: limpio.activo, ...(limpio.clave ? { clave: limpio.clave } : {}) };

    setSubmitting(true);
    try {
      await onSubmit(input);
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(errorsFromApi(error.details, CAMPOS_USUARIO));
        setFormError(errorMessage(error));
      } else {
        setFormError("No fue posible guardar el usuario.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const tipos = (catalogos?.tipos_identificacion ?? []).map((o) => ({ value: o.codigo, label: o.nombre }));
  const roles = (catalogos?.roles ?? []).map((o) => ({ value: o.codigo, label: o.nombre }));

  return (
    <form
      className="form"
      onSubmit={handleSubmit}
      noValidate
      aria-label={modo === "crear" ? "Registrar usuario" : "Editar usuario"}
    >
      <div className="form-section">
        <h3>1. Cuenta de acceso</h3>
        <div className="form-grid">
          {modo === "crear" ? (
            <Field
              id="usuario-usuario"
              label="Nombre de usuario"
              value={values.usuario}
              error={errors.usuario}
              hint="Minúsculas, números, punto, guion o guion bajo"
              maxLength={50}
              required
              onChange={(value) => update("usuario", value.toLowerCase())}
            />
          ) : (
            <Field
              id="usuario-usuario"
              label="Nombre de usuario"
              value={values.usuario}
              disabled
              onChange={() => undefined}
            />
          )}
          <SelectField
            id="usuario-rol"
            label="Rol"
            value={values.rol}
            options={roles}
            error={errors.rol}
            required
            onChange={(value) => update("rol", value as Role | "")}
          />
          <Field
            id="usuario-clave"
            label={modo === "crear" ? "Clave" : "Nueva clave"}
            type="password"
            value={values.clave}
            error={errors.clave}
            hint={
              modo === "crear"
                ? "Mínimo 8 caracteres, con letras y números"
                : "Déjela en blanco para no cambiarla"
            }
            autoComplete="new-password"
            maxLength={128}
            required={modo === "crear"}
            onChange={(value) => update("clave", value)}
          />
          {modo === "editar" && (
            <div className="field">
              <span className="field-label-text">Estado</span>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={values.activo}
                  onChange={(event) => update("activo", event.target.checked)}
                />
                Cuenta activa
              </label>
            </div>
          )}
        </div>
      </div>

      <div className="form-section">
        <h3>2. Datos de la persona</h3>
        <div className="form-grid">
          <Field
            id="usuario-nombre"
            label="Nombre completo"
            value={values.nombre}
            error={errors.nombre}
            maxLength={255}
            required
            className="span-2"
            onChange={(value) => update("nombre", value)}
          />
          <SelectField
            id="usuario-tipo"
            label="Tipo de identificación"
            value={values.tipo_identificacion}
            options={tipos}
            error={errors.tipo_identificacion}
            required
            onChange={(value) => update("tipo_identificacion", value)}
          />
          <Field
            id="usuario-identificacion"
            label="Identificación"
            value={values.identificacion}
            error={errors.identificacion}
            maxLength={50}
            required
            onChange={(value) => update("identificacion", value)}
          />
          <Field
            id="usuario-correo"
            label="Correo electrónico"
            type="email"
            value={values.correo}
            error={errors.correo}
            maxLength={254}
            required
            className="span-2"
            onChange={(value) => update("correo", value)}
          />
        </div>
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
          {submitting ? "Guardando…" : "Guardar usuario"}
        </button>
      </div>
    </form>
  );
}
