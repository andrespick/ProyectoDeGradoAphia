import type { ComponentPropsWithoutRef } from "react";

type InputType = "text" | "email" | "password" | "date" | "search" | "tel" | "number";

interface FieldProps
  extends Omit<ComponentPropsWithoutRef<"input">, "id" | "value" | "onChange" | "type"> {
  id: string;
  label: string;
  value: string;
  error?: string;
  hint?: string;
  type?: InputType;
  onChange: (value: string) => void;
}

/** Campo de texto con etiqueta, pista y error accesibles. */
export function Field({
  id,
  label,
  value,
  error,
  hint,
  type = "text",
  onChange,
  className,
  required,
  ...rest
}: FieldProps) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(" ");
  return (
    <div className={className ? `field ${className}` : "field"}>
      <label htmlFor={id}>
        {label}
        {required && (
          <span className="required" aria-hidden="true">
            {" "}
            *
          </span>
        )}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        required={required}
        autoComplete="off"
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy || undefined}
        onChange={(event) => onChange(event.target.value)}
        {...rest}
      />
      {hint && (
        <p id={hintId} className="field-hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="field-error">
          {error}
        </p>
      )}
    </div>
  );
}
