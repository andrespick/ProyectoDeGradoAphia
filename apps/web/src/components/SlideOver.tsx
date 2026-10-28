import { X } from "lucide-react";
import { type ReactNode, useEffect, useRef } from "react";

interface SlideOverProps {
  titulo: string;
  subtitulo?: string;
  icono?: ReactNode;
  onClose: () => void;
  children: ReactNode;
  pie?: ReactNode;
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Panel lateral derecho para formularios (identidad visual: «Registrar nuevo inmueble»). */
export function SlideOver({ titulo, subtitulo, icono, onClose, children, pie }: SlideOverProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const panel = panelRef.current;
    const previous = document.activeElement as HTMLElement | null;
    focusables(panel)[0]?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onCloseRef.current();
        return;
      }
      if (event.key !== "Tab" || !panel) return;
      const items = focusables(panel);
      const first = items[0];
      const last = items[items.length - 1];
      if (!first || !last) return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    document.body.classList.add("no-scroll");
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.classList.remove("no-scroll");
      previous?.focus();
    };
  }, []);

  return (
    <div className="slide-over-backdrop" onClick={() => onCloseRef.current()}>
      <div
        ref={panelRef}
        className="slide-over"
        role="dialog"
        aria-modal="true"
        aria-labelledby="slide-over-titulo"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="slide-over-header">
          {icono && (
            <span className="icon-box" aria-hidden="true">
              {icono}
            </span>
          )}
          <div className="slide-over-titles">
            <h2 id="slide-over-titulo">{titulo}</h2>
            {subtitulo && <p className="muted">{subtitulo}</p>}
          </div>
          <button
            type="button"
            className="ghost icon-button"
            onClick={() => onCloseRef.current()}
            aria-label="Cerrar"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </header>
        <div className="slide-over-body">{children}</div>
        {pie && <footer className="slide-over-footer">{pie}</footer>}
      </div>
    </div>
  );
}

function focusables(root: HTMLElement | null): HTMLElement[] {
  return root ? Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)) : [];
}
