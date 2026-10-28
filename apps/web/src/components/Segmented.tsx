export interface SegmentedOption<V extends string> {
  value: V;
  label: string;
  count?: number;
}

interface SegmentedProps<V extends string> {
  label: string;
  value: V;
  options: readonly SegmentedOption<V>[];
  onChange: (value: V) => void;
}

/** Grupo de segmentos («Todos · Arrendatarios · Propietarios …») para filtrar listados. */
export function Segmented<V extends string>({ label, value, options, onChange }: SegmentedProps<V>) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
          {option.count !== undefined && <span className="segmented-count">{option.count}</span>}
        </button>
      ))}
    </div>
  );
}
