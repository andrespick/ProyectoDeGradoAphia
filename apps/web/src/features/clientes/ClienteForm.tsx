import { type FormEvent, useState } from "react";

import { Field } from "../../components/Field";
import { ApiError } from "../../services/apiClient";
import type { ClienteCreate } from "../../types/cliente";
import { errorsFromApi } from "../shared/validation";
import { CAMPOS_CLIENTE, type ClienteErrors, validateCliente } from "./validation";

interface ClienteFormProps {
  onSubmit: (input: ClienteCreate) => Promise<unknown>;
}

const EMPTY: ClienteCreate = { nombre: "", correo: "" };

export function ClienteForm({ onSubmit }: ClienteFormProps) {
  const [values, setValues] = useState<ClienteCreate>(EMPTY);
  const [errors, setErrors] = useState<ClienteErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update(field: keyof ClienteCreate, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSuccess(null);

    const input = { nombre: values.nombre.trim(), correo: values.correo.trim() };
    const validation = validateCliente(input);
    setErrors(validation);
    if (Object.keys(validation).length > 0) return;

    setSubmitting(true);
    try {
      await onSubmit(input);
      setValues(EMPTY);
      setSuccess("Cliente registrado correctamente.");
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(errorsFromApi(error.details, CAMPOS_CLIENTE));
        setFormError(error.message);
      } else {
        setFormError("No fue posible registrar el cliente.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate aria-label="Registrar cliente">
      <Field
        id="cliente-nombre"
        label="Nombre"
        value={values.nombre}
        error={errors.nombre}
        maxLength={150}
        onChange={(value) => update("nombre", value)}
      />
      <Field
        id="cliente-correo"
        label="Correo electrónico"
        type="email"
        value={values.correo}
        error={errors.correo}
        maxLength={254}
        onChange={(value) => update("correo", value)}
      />
      {formError && (
        <p className="alert alert-error" role="alert">
          {formError}
        </p>
      )}
      {success && (
        <p className="alert alert-success" role="status">
          {success}
        </p>
      )}
      <button type="submit" disabled={submitting}>
        {submitting ? "Guardando…" : "Registrar cliente"}
      </button>
    </form>
  );
}
