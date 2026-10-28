# Cloudflare Tunnel y acceso privado (Workers VPC)

Objetivo: que Hyperdrive y el Worker lleguen a MySQL y al servicio de documentos **sin abrir
puertos** en el VPS.

Fuentes (consultadas el 2026-10-27):
- https://developers.cloudflare.com/hyperdrive/configuration/connect-to-private-database-vpc/ (ruta recomendada)
- https://developers.cloudflare.com/workers-vpc/ (Workers VPC está en **beta**)
- https://developers.cloudflare.com/hyperdrive/configuration/connect-to-private-database/ (alternativa Tunnel + Access)

Verifique la documentación vigente antes de ejecutar: los comandos de una función beta pueden cambiar.

## 1. Crear el túnel

En el panel de Cloudflare: **Workers VPC → Tunnels → crear túnel**. Copie el token y póngalo
en `infra/production/.env.production` (`TUNNEL_TOKEN`). No configure *public hostnames*.

```bash
cd /opt/aphia/infra/production
docker compose --env-file .env.production up -d cloudflared
docker compose --env-file .env.production logs cloudflared   # "Registered tunnel connection"
```

## 2. Servicio VPC para MySQL (TCP)

Desde un equipo con el repositorio y `pnpm install` (wrangler está en `apps/api`):

```bash
pnpm --filter @aphia/api exec wrangler login
pnpm --filter @aphia/api exec wrangler vpc service create aphia-mysql \
  --type tcp --tcp-port 3306 --app-protocol mysql \
  --tunnel-id <TUNNEL_ID> --hostname mysql
```

`mysql` es el nombre del servicio en la red Docker, resoluble por `cloudflared`. Guarde el
`service_id` devuelto.

### TLS entre Hyperdrive y MySQL

Hyperdrive exige TLS. MySQL 8.4 genera un certificado **autofirmado**; Workers VPC verifica
por defecto con `verify_full` y la documentación indica que aún no admite subir una CA
propia. Opciones:

1. `--cert-verification-mode disabled` en el servicio VPC: el tráfico va cifrado (TLS) y
   además dentro del túnel autenticado, pero sin validar el certificado. Es la opción práctica hoy.
2. Instalar en MySQL un certificado emitido por una CA pública para un nombre que controle
   y usar `verify_full`. Más complejo de mantener.

Documente la opción elegida.

## 3. Servicio VPC para documentos (HTTP)

```bash
pnpm --filter @aphia/api exec wrangler vpc service create aphia-files \
  --type http --tunnel-id <TUNNEL_ID> --hostname files --http-port 4000
```

Copie el `service_id` en `apps/api/wrangler.jsonc` → `env.<entorno>.vpc_services[0].service_id`.

## 4. Permisos

La cuenta que crea bindings necesita el rol `Connectivity Directory Bind` (o `Admin`).

## Limitación conocida

La documentación de Workers VPC muestra el uso del binding desde JavaScript
(`env.FILES_SERVICE.fetch(...)`). Su uso desde **Python Workers no está confirmado**. Antes de
implementar el adaptador de documentos, pruébelo con `pywrangler dev --remote` (los servicios
VPC solo funcionan con bindings remotos). Si no funcionara, alternativa compatible:

- Publicar `files` en un hostname del túnel protegido con **Cloudflare Access** (política
  *Service Auth* con token de servicio) y llamarlo con `fetch` HTTP normal enviando las
  cabeceras de Access **y** el token propio del servicio de documentos.

## Alternativa para MySQL: Tunnel + Access

Documentada por Cloudflare como opción anterior: ruta TCP pública del túnel + aplicación de
Access con token de servicio + `wrangler hyperdrive create ... --access-client-id ...
--access-client-secret ...`. Úsela solo si Workers VPC no estuviera disponible en la cuenta.
