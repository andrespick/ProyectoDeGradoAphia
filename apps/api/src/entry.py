"""Punto de entrada para Cloudflare Python Workers (``main`` en wrangler.jsonc).

Patrón documentado en developers.cloudflare.com/workers/languages/python/packages/fastapi/.
Toda la lógica vive en ``main.py`` para que la misma app funcione con Uvicorn.
"""

from workers import asgi

from main import app

Default = asgi.entrypoint(app)
