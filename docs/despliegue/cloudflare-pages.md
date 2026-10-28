# Cloudflare Pages (frontend)

## Configuración incluida

- `apps/web/public/_redirects`: `/* /index.html 200` (rutas de la SPA como `/panel`).
- `apps/web/public/_headers`: CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy` y caché inmutable para `/assets/*`.
- Variable de build: `VITE_API_BASE_URL` (URL pública de la API; no es secreta).

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

1. Copie la URL de Pages en `CORS_ORIGINS` del entorno correspondiente en `apps/api/wrangler.jsonc`.
2. Redespliegue la API.
3. Abra la URL: el indicador debe mostrar «API conectada».
