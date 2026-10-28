# Desarrollo

- [Cómo crear un módulo](crear-modulo.md)
- [Convenciones de código](convenciones.md)
- [Migraciones](migraciones.md)
- [Docker en desarrollo](docker.md)
- [Cómo ejecutar pruebas](../pruebas/README.md)

## Flujo diario

```bash
pnpm dev            # Docker + web (5173) + API en Python Workers local (8787)
# … editar código: Vite y pywrangler recargan automáticamente
pnpm lint && pnpm typecheck && pnpm test
pnpm infra:down     # al terminar (los datos se conservan)
```

`pnpm dev:asgi` ejecuta la API con Uvicorn en lugar de Workers. Úselo para depurar con
herramientas de Python estándar, pero valide siempre los cambios también con `pnpm dev`,
que reproduce el runtime de producción.

## Diferencias entre desarrollo local y producción

| Aspecto | Local | Producción |
| --- | --- | --- |
| Runtime de la API | workerd local (`pywrangler dev`) | Cloudflare Workers |
| Conexión a MySQL | Hyperdrive con cadena local: conexión directa, **sin pool ni caché** | Hyperdrive con pool, vía Workers VPC y túnel |
| TLS a MySQL | No | Sí (obligatorio) |
| Variables | `wrangler.jsonc` (`vars` raíz) + `.env` | `env.staging` / `env.production` + secretos |
| Autenticación | Usuario ficticio | Cerrada hasta implementar la real |
| Servicio de documentos | `127.0.0.1:4000` (Docker) | Red interna del VPS, solo vía túnel |
