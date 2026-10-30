# Cloudflare Pages (frontend)

## Configuración incluida

- `apps/web/public/_redirects`: `/* /index.html 200` (rutas de la SPA como `/panel`).
- `apps/web/public/_headers`: CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy` y caché inmutable para `/assets/*`.
- Variable de build: `VITE_API_BASE_URL` (URL pública de la API; no es secreta). **Obligatoria**:
  `vite build` falla en modo producción si falta. Sin ella la web llamaría a su propio origen,
  Pages respondería `index.html` a `/api/...` y la aplicación mostraría el cascarón sin sesión.

## Opción A (configurada): despliegue desde GitHub Actions

El workflow `Deploy` compila con la `API_BASE_URL` del entorno y ejecuta
`wrangler pages deploy apps/web/dist --project-name <proyecto> --branch <main|staging>`:

- `--branch main` → producción del proyecto de Pages.
- `--branch staging` → despliegue de vista previa con URL estable `staging.<proyecto>.pages.dev`.

Crear el proyecto una vez (Direct Upload):

```bash
pnpm --filter @aphia/api exec wrangler pages project create <proyecto> --production-branch main
```

Ventaja: producción solo se publica con la aprobación del entorno `production` en GitHub.

## Opción B: integración Git nativa de Pages

En el panel: Workers & Pages → Create → Pages → Connect to Git, con:

| Campo | Valor |
| --- | --- |
| Framework preset | None |
| Build command | `pnpm install --frozen-lockfile && pnpm --filter @aphia/web build` |
| Build output directory | `apps/web/dist` |
| Root directory | `/` |
| Variables (Production / Preview) | `VITE_API_BASE_URL`, `NODE_VERSION=24` |

Atención: con esta opción Pages publica producción en cada push a `main` **sin** la aprobación
manual, y un proyecto Direct Upload no puede cambiarse luego a integración Git. Elija una sola.

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
