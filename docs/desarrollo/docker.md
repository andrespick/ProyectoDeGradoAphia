# Docker en desarrollo

Archivo: `infra/local/compose.yaml` (proyecto `aphia-local`). Lo invocan los scripts de
`pnpm`, que agregan `--env-file .env`.

| Servicio | Imagen | Puerto local | Datos |
| --- | --- | --- | --- |
| `mysql` | `mysql:8.4` | `127.0.0.1:3307` | volumen `aphia-local_mysql-data` |
| `files` | construida desde `apps/files` | `127.0.0.1:4000` | volumen `aphia-local_files-data` |
| `mysql-test` (perfil `test`) | `mysql:8.4` | `127.0.0.1:3308` | en memoria (tmpfs) |

## Comandos

```bash
pnpm infra:up              # construye y levanta mysql + files, espera a que estén sanos
pnpm infra:ps              # estado
pnpm infra:logs            # registros en vivo
pnpm infra:down            # detiene (conserva volúmenes)
pnpm infra:reset -- --yes  # elimina contenedores Y volúmenes locales
```

Consola de MySQL local:

```bash
docker exec -it aphia-local-mysql-1 mysql -uaphia_app -p aphia
```

## Notas

- Los puertos solo escuchan en `127.0.0.1`: no son accesibles desde la red local.
- El contenedor de documentos corre como usuario sin privilegios, con sistema de archivos de
  solo lectura salvo `/data` y `/tmp`, sin capacidades Linux.
- MySQL usa las variables de contraseña **solo al crear el volumen**. Si cambia `.env`,
  ejecute `pnpm infra:reset -- --yes` (pierde los datos locales).
- Si edita `apps/files`, `pnpm infra:up` reconstruye la imagen automáticamente.
- En Windows, Docker Desktop requiere WSL 2 y virtualización habilitada.
