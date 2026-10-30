# Cloudflare Pages (frontend)

## Configuración incluida

- `apps/web/public/_redirects`: `/* /index.html 200` (rutas de la SPA como `/panel`).
- `apps/web/public/_headers`: CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy` y caché inmutable para `/assets/*`.
- Variable de build: `VITE_API_BASE_URL` (URL pública de la API; no es secreta). **Obligatoria**:
  `vite build` falla en modo producción si falta. Sin ella la web llamaría a su propio origen,
  Pages respondería `index.html` a `/api/...` y la aplicación mostraría el cascarón sin sesión.

## Configuración en uso: integración Git nativa de Pages

Proyecto `proyectodegradoaphia` conectado al repositorio; cada push a `main` compila y publica
producción, y cada otra rama genera una vista previa. En el panel: Workers & Pages → proyecto →
Settings → Builds & deployments y Variables and Secrets:

| Campo | Valor |
| --- | --- |
| Framework preset | None |
| Build command | `pnpm --filter @aphia/web build` (Pages ejecuta `pnpm install` solo) |
| Build output directory | `apps/web/dist` |
| Root directory | `/` |
| Variables (Production **y** Preview) | `VITE_API_BASE_URL=https://api.aphia.com.co` |

Sin la variable, el build falla con «Defina VITE_API_BASE_URL». Tras agregarla hay que
relanzar el despliegue (Deployments → Retry deployment) o hacer un push.

Alternativa no usada: subir el build desde GitHub Actions con `wrangler pages deploy`
(Direct Upload). Un proyecto conectado a Git no admite ese modo, y viceversa.

## Después del primer despliegue

1. Copie la URL de Pages (y el dominio propio, p. ej. `https://app.aphia.com.co`) en
   `CORS_ORIGINS` de `infra/production/.env.production` en el VPS (varios orígenes separados
   por coma). Con la API en Workers, el valor va en `apps/api/wrangler.jsonc`.
2. Aplique el cambio: `docker compose --env-file .env.production up -d api`.
3. Abra la URL: debe aparecer la pantalla de inicio de sesión y, en la barra lateral, «En línea».

## Dominio propio

En el proyecto de Pages → Custom domains agregue `app.aphia.com.co` (DNS en la misma cuenta).
La API queda en el subdominio que atiende Caddy en el VPS (`api.aphia.com.co`); ese valor es
`VITE_API_BASE_URL` (variable `API_BASE_URL` del entorno en GitHub).

## Síntomas de configuración incorrecta

| Síntoma | Causa | Solución |
| --- | --- | --- |
| Al abrir la web aparece el gestor sin pedir usuario y sin datos | La web se construyó sin `VITE_API_BASE_URL` (llama a Pages, que responde `index.html`) | Defina la variable en Pages (Production y Preview), vuelva a desplegar |
| «No fue posible conectar con la API» o error de CORS en la consola | El origen de Pages no está en `CORS_ORIGINS` de la API | Agregue el origen exacto (con `https://`) en `.env.production` y `up -d api` |
| «API sin conexión» pero `/api/health` responde | `/api/ready` falla: MySQL caído o sin migrar | `docker compose ps`, logs de `mysql`, [mysql.md](mysql.md) |
