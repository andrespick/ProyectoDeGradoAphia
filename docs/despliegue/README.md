# Despliegue

> Producción funciona desde el 2026-10-30: API en `https://api.aphia.com.co` (VPS) y web en
> `https://app.aphia.com.co` (Cloudflare Pages). Cada paso que crea o cambia recursos externos
> requiere una decisión y credenciales de la persona responsable.

## Orden recomendado

La API se despliega con Docker en el VPS (Uvicorn detrás de Caddy); el frontend, en
Cloudflare Pages.

1. [Preparar el VPS](vps.md) (Docker Compose con `api`, `mysql` y `files`; Caddy)
2. [MySQL en el VPS](mysql.md) (usuarios, TLS, migraciones)
3. [Servicio de documentos](documentos.md)
4. [Cloudflare Pages (frontend)](cloudflare-pages.md)
5. [GitHub Actions](github-actions.md)
6. [Respaldos, restauración y recuperación ante fallos](restauracion.md)
7. [Guía de instalación y mantenimiento](instalacion-y-mantenimiento.md) (primer administrador, rotación de secretos, tareas recurrentes, logs)

## Elementos que requieren credenciales o acción manual

| Elemento | Dónde se usa | Quién lo provee |
| --- | --- | --- |
| VPS Linux (2 vCPU, 2–4 GB, 20–40 GB) | Todo el backend de datos | Responsable del proyecto (proveedor por definir) |
| Dominio y registro DNS `A` para la API | Caddy en el VPS | Responsable del proyecto |
| Clave SSH de despliegue (`VPS_SSH_*`) | GitHub Actions → VPS | Generada en el VPS (usuario `aphia`) |
| Cuenta de Cloudflare | Pages (frontend) | Responsable del proyecto |
| Nombre del proyecto de Pages y URL de la API | `.env.production` (CORS) y variables de GitHub | Al crear el proyecto |
| Destino de respaldos (rclone) y clave `age` | `backup.env` | Responsable del proyecto |
| Revisores de producción | GitHub → Settings → Environments | Responsable del proyecto |
