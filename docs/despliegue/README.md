# Despliegue

> Nada de esto se ha ejecutado contra recursos reales: no hay VPS contratado ni recursos de
> Cloudflare creados. Los archivos están listos y la configuración de producción se verificó
> en una réplica local (salvo el túnel y Cloudflare). Cada paso que crea o cambia recursos
> externos requiere una decisión y credenciales de la persona responsable.

## Orden recomendado

1. [Preparar el VPS](vps.md)
2. [MySQL en el VPS](mysql.md) (usuarios, TLS, migraciones)
3. [Servicio de documentos](documentos.md)
4. [Cloudflare Tunnel y acceso privado (Workers VPC)](tunnel-y-acceso-privado.md)
5. [Hyperdrive](hyperdrive.md)
6. [Cloudflare Workers (API)](cloudflare-workers.md)
7. [Cloudflare Pages (frontend)](cloudflare-pages.md)
8. [GitHub Actions](github-actions.md)
9. [Respaldos, restauración y recuperación ante fallos](restauracion.md)

## Elementos que requieren credenciales o acción manual

| Elemento | Dónde se usa | Quién lo provee |
| --- | --- | --- |
| VPS Linux (2 vCPU, 2–4 GB, 20–40 GB) | Todo el backend de datos | Responsable del proyecto (proveedor por definir) |
| Cuenta de Cloudflare y `CLOUDFLARE_ACCOUNT_ID` | Workers, Pages, Hyperdrive, túnel | Responsable del proyecto |
| Token de API de Cloudflare (permisos mínimos) | GitHub Actions | Responsable del proyecto |
| Token del túnel | `infra/production/.env.production` | Panel de Cloudflare |
| IDs de servicios VPC y de Hyperdrive | `apps/api/wrangler.jsonc` (`REEMPLAZAR_*`) | Salida de `wrangler vpc service create` / `wrangler hyperdrive create` |
| Nombre del proyecto de Pages y URL de la API | `wrangler.jsonc` (CORS) y variables de GitHub | Al crear el proyecto |
| Destino de respaldos (rclone) y clave `age` | `backup.env` | Responsable del proyecto |
| Revisores de producción | GitHub → Settings → Environments | Responsable del proyecto |
