from __future__ import annotations

from modules.personas.router import build_personas_router

# ``?contrato_id=`` lista los codeudores de un contrato; ``?q=`` busca por identificación o nombre.
router = build_personas_router("/api/v1/codeudores", "codeudores", papel_fijo="codeudor")
