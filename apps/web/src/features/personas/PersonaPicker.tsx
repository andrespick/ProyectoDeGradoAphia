import { Search, UserPlus, X } from "lucide-react";
import { type FormEvent, useState } from "react";

import { Field } from "../../components/Field";
import { SelectField } from "../../components/SelectField";
import { ApiError, errorMessage } from "../../services/apiClient";
import { buscarPersona, createPersona } from "../../services/personasService";
import { identificacionDe, NOMBRE_PAPEL, type Papel, type Persona, type PersonaResumen } from "../../types/persona";
import { useCatalogos } from "../catalogos/useCatalogos";
import { EMAIL_RE } from "../shared/validation";

interface PersonaPickerProps {
  /** Prefijo de ids para que varios selectores convivan en la misma página. */
  idPrefix: string;
  label: string;
  /** Papel que recibe la persona si se registra desde aquí. */
  papel: Papel;
  value: PersonaResumen | null;
  onChange: (persona: PersonaResumen | null) => void;
  /** Sin registro en línea (filtros de listados). */
  soloBuscar?: boolean;
  /** Ids ya elegidos (para listas): no se vuelven a ofrecer. */
  excluir?: readonly number[];
}

/** Busca una persona por identificación; si no existe, permite registrarla en el momento. */
export function PersonaPicker({
  idPrefix,
  label,
  papel,
  value,
  onChange,
  soloBuscar = false,
  excluir = [],
}: PersonaPickerProps) {
  const { catalogos } = useCatalogos();
  const [tipo, setTipo] = useState("CC");
  const [numero, setNumero] = useState("");
  const [resultado, setResultado] = useState<Persona | null>(null);
  const [noEncontrada, setNoEncontrada] = useState(false);
  const [registrando, setRegistrando] = useState(false);
  const [nuevo, setNuevo] = useState({ nombre: "", telefono: "", correo: "" });
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const tipos = (catalogos?.tipos_identificacion ?? []).map((o) => ({ value: o.codigo, label: o.nombre }));

  async function buscar(event?: FormEvent) {
    event?.preventDefault();
    setError(null);
    setResultado(null);
    setNoEncontrada(false);
    setRegistrando(false);
    if (!numero.trim()) {
      setError("Ingrese la identificación que desea buscar.");
      return;
    }
    setOcupado(true);
    try {
      const persona = await buscarPersona(tipo, numero.trim());
      if (excluir.includes(persona.id)) {
        setError("Esa persona ya está en la lista.");
      } else {
        setResultado(persona);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setNoEncontrada(true);
      else setError(errorMessage(err));
    } finally {
      setOcupado(false);
    }
  }

  async function registrar(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (nuevo.nombre.trim().length < 2) {
      setError("Ingrese el nombre completo de la persona.");
      return;
    }
    if (nuevo.correo && !EMAIL_RE.test(nuevo.correo)) {
      setError("Ingrese un correo electrónico válido.");
      return;
    }
    setOcupado(true);
    try {
      const persona = await createPersona("/api/v1/clientes", {
        nombre: nuevo.nombre.trim(),
        tipo_identificacion: tipo,
        identificacion: numero.trim(),
        telefono: nuevo.telefono.trim() || null,
        correo: nuevo.correo.trim() || null,
        direccion: null,
        papeles: [papel],
        cuenta_bancaria: null,
      });
      seleccionar(persona);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setOcupado(false);
    }
  }

  function seleccionar(persona: PersonaResumen) {
    onChange(persona);
    setResultado(null);
    setNoEncontrada(false);
    setRegistrando(false);
    setNumero("");
    setNuevo({ nombre: "", telefono: "", correo: "" });
  }

  if (value) {
    return (
      <div className="field">
        <span className="field-label-text">{label}</span>
        <span className="chip-list">
          <span className="chip chip-persona">
            <strong>{value.nombre}</strong> · {identificacionDe(value)}
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
      <div className="picker-search">
        <SelectField id={`${idPrefix}-tipo`} label="Tipo" value={tipo} options={tipos} placeholder="Tipo" onChange={setTipo} />
        <Field
          id={`${idPrefix}-numero`}
          label="Identificación"
          value={numero}
          maxLength={50}
          onChange={setNumero}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void buscar();
            }
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
      {resultado && (
        <div className="picker-result">
          <span>
            <strong>{resultado.nombre}</strong> · {identificacionDe(resultado)}
            {resultado.papeles.length > 0 && (
              <span className="muted"> · {resultado.papeles.map((p) => NOMBRE_PAPEL[p]).join(", ")}</span>
            )}
          </span>
          <button type="button" onClick={() => seleccionar(resultado)}>
            Seleccionar
          </button>
        </div>
      )}
      {noEncontrada && !registrando && (
        <div className="picker-result">
          <span>No existe una persona con esa identificación.</span>
          {!soloBuscar && (
            <button type="button" className="secondary" onClick={() => setRegistrando(true)}>
              <UserPlus size={16} aria-hidden="true" /> Registrar nueva persona
            </button>
          )}
        </div>
      )}
      {registrando && (
        <div className="picker-nuevo form-grid" role="group" aria-label={`Registrar ${NOMBRE_PAPEL[papel].toLowerCase()}`}>
          <Field
            id={`${idPrefix}-nuevo-nombre`}
            label="Nombre completo"
            value={nuevo.nombre}
            maxLength={255}
            required
            className="span-2"
            onChange={(v) => setNuevo((c) => ({ ...c, nombre: v }))}
          />
          <Field
            id={`${idPrefix}-nuevo-telefono`}
            label="Teléfono"
            type="tel"
            value={nuevo.telefono}
            maxLength={50}
            onChange={(v) => setNuevo((c) => ({ ...c, telefono: v }))}
          />
          <Field
            id={`${idPrefix}-nuevo-correo`}
            label="Correo electrónico"
            type="email"
            value={nuevo.correo}
            maxLength={254}
            onChange={(v) => setNuevo((c) => ({ ...c, correo: v }))}
          />
          <div className="actions span-2">
            <button type="button" className="secondary" onClick={() => setRegistrando(false)}>
              Cancelar
            </button>
            <button type="button" disabled={ocupado} onClick={(e) => void registrar(e)}>
              Registrar como {NOMBRE_PAPEL[papel].toLowerCase()}
            </button>
          </div>
        </div>
      )}
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
