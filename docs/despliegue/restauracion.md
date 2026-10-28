# Respaldos, restauración y recuperación ante fallos

## Qué se respalda

| Elemento | Cómo | Dónde |
| --- | --- | --- |
| Base de datos `aphia` | `mysqldump --single-transaction` (sin bloquear InnoDB) | Archivo cifrado fuera del VPS |
| Documentos | `tar` del volumen `/data` (contenido + metadatos) | Mismo archivo |
| Sumas SHA-256 | `SHA256SUMS` dentro del archivo | Mismo archivo |
| Secretos del VPS | **Manual**, una vez y en cada rotación | Gestor de contraseñas (no en el respaldo) |
| Código y configuración | Git | GitHub |

Los usuarios de MySQL no van en el volcado; los recrea `01-usuarios.sh` en un volumen nuevo.

Verificado localmente: el volcado y su restauración en una base nueva (tabla y historial de
migraciones presentes), y el `tar` del volumen de documentos. El ciclo completo con `age` y
`rclone` no se ha ejecutado (requiere el VPS y el destino externo).

## Configuración en el VPS

```bash
age-keygen -o aphia-backup-identity.txt   # en un equipo seguro, NO en el VPS
# Copie la línea "public key: age1..." en backup.env; guarde el archivo de identidad fuera del VPS
cd /opt/aphia/infra/production/backup
cp backup.env.example backup.env && chmod 600 backup.env
rclone config                            # destino externo (S3, B2, Drive...)
./backup.sh                              # primera ejecución manual
```

Cron diario (UTC):

```cron
15 3 * * * /opt/aphia/infra/production/backup/backup.sh >> /var/log/aphia-backup.log 2>&1
```

Con respaldos diarios, la pérdida máxima de datos (RPO) es de 24 h. Si la empresa necesita
menos, aumente la frecuencia o active binlogs con copia externa.

## Restaurar

```bash
cd /opt/aphia/infra/production/backup
./backup.sh                                            # 1. respaldo del estado actual
./restore.sh aphia-20261027T031500Z.tar.age /ruta/identidad.txt --confirm
curl https://<api>/api/ready                           # 2. verificar
```

`restore.sh` descifra, verifica las sumas SHA-256, restaura la base y reemplaza el volumen de
documentos. Durante la restauración, considere poner la API en mantenimiento (desplegar una
versión que responda 503) para evitar escrituras.

## Escenarios

| Escenario | Acción |
| --- | --- |
| Borrado accidental de datos | Restaurar en una base temporal (cambiando el nombre en el volcado, como se probó localmente), extraer lo necesario y reinsertarlo; evita perder cambios posteriores. |
| Contenedor dañado | `docker compose up -d --force-recreate <servicio>`: los volúmenes persisten. |
| Pérdida total del VPS | Nuevo VPS ([vps.md](vps.md)) → restaurar secretos desde el gestor → `up -d mysql files` → `restore.sh` → nuevo token de túnel (o reutilizar) → verificar Hyperdrive y `/api/ready`. |
| Migración fallida | Revertir el Worker (`pywrangler rollback`) y, si es necesario, restaurar el respaldo tomado antes de migrar. |
| Fuga de un secreto | Rotarlo (ver docs/seguridad) y revisar logs de acceso. |

## Simulacro

Al menos cada trimestre restaure el último respaldo en un entorno aislado (por ejemplo, la
infraestructura local) y verifique que la aplicación funciona con esos datos. Un respaldo
que nunca se restauró no está verificado.
