from __future__ import annotations

from modules.personas.router import build_personas_router

# Clientes = toda persona con al menos un papel; ``?papel=`` filtra por tipo de cliente.
router = build_personas_router("/api/v1/clientes", "clientes", papel_fijo=None)
