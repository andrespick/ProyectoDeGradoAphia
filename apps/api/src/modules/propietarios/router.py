from __future__ import annotations

from modules.personas.router import build_personas_router

router = build_personas_router("/api/v1/propietarios", "propietarios", papel_fijo="propietario")
