# Despliegue

> Nada de esto se ha ejecutado contra recursos reales: no hay VPS contratado ni recursos de
> Cloudflare creados. Los archivos están listos y la configuración de producción se verificó
> en una réplica local (salvo el túnel y Cloudflare). Cada paso que crea o cambia recursos
> externos requiere una decisión y credenciales de la persona responsable.

## Orden recomendado

La API se despliega con Docker en el VPS (Uvicorn detrás de Caddy); el frontend, en
Cloudflare Pages. Los pasos 6 a 8 solo aplican a la ruta alternativa de la API en Workers.

1. [Preparar el VPS](vps.md) (Docker Compose con `api`, `mysql` y `files`; Caddy)
2. [MySQL en el VPS](mysql.md) (usuarios, TLS, migraciones)
3. [Servicio de documentos](documentos.md)
4. [Cloudflare Pages (frontend)](cloudflare-pages.md)
5. [GitHub Actions](github-actions.md)
6. Opcional: [Cloudflare Tunnel y acceso privado (Workers VPC)](tunnel-y-acceso-privado.md)
7. Opcional: [Hyperdrive](hyperdrive.md)
8. Opcional: [Cloudflare Workers (API)](cloudflare-workers.md)
9. [Respaldos, restauración y recuperación ante fallos](restauracion.md)
10. [Guía de instalación y mantenimiento](instalacion-y-mantenimiento.md) (primer administrador, rotación de secretos, tareas recurrentes, logs)

## Elementos que requieren credenciales o acción manual

| Elemento | Dónde se usa | Quién lo provee |
| --- | --- | --- |
| VPS Linux (2 vCPU, 2–4 GB, 20–40 GB) | Todo el backend de datos | Responsable del proyecto (proveedor por definir) |
| Dominio y registro DNS `A` para la API | Caddy en el VPS | Responsable del proyecto |
| Clave SSH de despliegue (`VPS_SSH_*`) | GitHub Actions → VPS | Generada en el VPS (usuario `aphia`) |
| Cuenta de Cloudflare y `CLOUDFLARE_ACCOUNT_ID` | Pages (y Workers si se usa) | Responsable del proyecto |
| Token de API de Cloudflare (permisos mínimos) | GitHub Actions | Responsable del proyecto |
| Nombre del proyecto de Pages y URL de la API | `.env.production` (CORS) y variables de GitHub | Al crear el proyecto |
| Solo Workers: token del túnel e IDs de VPC/Hyperdrive | `.env.production`, `apps/api/wrangler.jsonc` (`REEMPLAZAR_*`) | Panel de Cloudflare / `wrangler` |
| Destino de respaldos (rclone) y clave `age` | `backup.env` | Responsable del proyecto |
| Revisores de producción | GitHub → Settings → Environments | Responsable del proyecto |
