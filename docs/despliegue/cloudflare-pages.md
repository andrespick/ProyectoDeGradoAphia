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
   `CORS_ORIGINS` del entorno correspondiente en `apps/api/wrangler.jsonc`.
2. Redespliegue la API (`uv run pywrangler deploy --env production`).
3. Abra la URL: debe aparecer la pantalla de inicio de sesión y, en la barra lateral, «En línea».

## Dominio propio

En el proyecto de Pages → Custom domains agregue `app.aphia.com.co` (DNS en la misma cuenta).
La API puede quedar en `https://aphia-api.<cuenta>.workers.dev` o en un subdominio propio
(`api.aphia.com.co`, ruta del Worker); en ambos casos ese valor es `VITE_API_BASE_URL`.

## Síntomas de configuración incorrecta

| Síntoma | Causa | Solución |
| --- | --- | --- |
| Al abrir la web aparece el gestor sin pedir usuario y sin datos | La web se construyó sin `VITE_API_BASE_URL` (llama a Pages, que responde `index.html`) | Defina la variable en Pages (Production y Preview), vuelva a desplegar |
| «No fue posible conectar con la API» o error de CORS en la consola | El origen de Pages no está en `CORS_ORIGINS` del Worker | Agregue el origen exacto (con `https://`) y redespliegue la API |
| «API sin conexión» pero `/api/health` responde | `/api/ready` falla: Hyperdrive o túnel caídos | Ver [hyperdrive.md](hyperdrive.md) y [tunnel-y-acceso-privado.md](tunnel-y-acceso-privado.md) |
