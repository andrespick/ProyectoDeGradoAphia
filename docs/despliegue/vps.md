# Preparación del VPS

Independiente del proveedor. Probado conceptualmente para Ubuntu Server 24.04 LTS o Debian 12/13;
los comandos son estándar de Debian/Ubuntu.

## 1. Acceso y usuario

```bash
# Como root, la primera vez
adduser aphia
usermod -aG sudo aphia
mkdir -p /home/aphia/.ssh && cp ~/.ssh/authorized_keys /home/aphia/.ssh/
chown -R aphia:aphia /home/aphia/.ssh && chmod 700 /home/aphia/.ssh
```

En `/etc/ssh/sshd_config`: `PermitRootLogin no`, `PasswordAuthentication no`. Reinicie `ssh`.

## 2. Sistema y cortafuegos

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades ufw fail2ban git age rclone
sudo dpkg-reconfigure -plow unattended-upgrades
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw enable
```

```bash
sudo ufw allow 80/tcp && sudo ufw allow 443/tcp   # solo Caddy
```

**No abra los puertos 3306, 4000 ni 8000**: MySQL y documentos viven en la red interna de
Docker, y la API solo escucha en `127.0.0.1:8000` para Caddy. Nota: Docker puede saltarse ufw
para puertos publicados; por eso el Compose solo publica la API y solo en `127.0.0.1`.

Con 2 GB de RAM agregue swap:

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 3. Docker Engine

Instale Docker Engine y el plugin Compose desde el repositorio oficial de Docker
(https://docs.docker.com/engine/install/). Luego:

```bash
sudo usermod -aG docker aphia   # cierre sesión y vuelva a entrar
docker version && docker compose version
```

## 4. Código y configuración

```bash
sudo mkdir -p /opt/aphia && sudo chown aphia:aphia /opt/aphia
git clone https://github.com/andrespick/ProyectoDeGradoAphia.git /opt/aphia
cd /opt/aphia/infra/production
bash scripts/generate-secrets.sh
cp .env.production.example .env.production && chmod 600 .env.production
# Edite .env.production: CORS_ORIGINS (URL del frontend en Pages) y ajuste de memoria
chmod 644 mysql/conf.d/aphia.cnf   # MySQL ignora archivos de configuración con escritura global
```

## 5. Arranque

```bash
docker compose --env-file .env.production up -d --build
docker compose --env-file .env.production ps        # api, mysql y files "healthy"
docker compose --env-file .env.production logs mysql | grep 01-usuarios
curl -s http://127.0.0.1:8000/api/health            # {"status":"ok",...,"runtime":"asgi"}
```

Luego aplique las [migraciones](mysql.md); hasta entonces `/api/ready` responde 503.

## 6. Caddy (HTTPS público hacia la API)

Caddy se instala en el sistema (no en Docker), obtiene el certificado de Let's Encrypt y
reenvía a la API. Apunte un registro DNS `A` de `api.<su dominio>` a la IP del VPS e
instale Caddy desde su repositorio oficial (https://caddyserver.com/docs/install). En
`/etc/caddy/Caddyfile`:

```
api.aphia.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

`sudo systemctl reload caddy` y compruebe `curl https://api.aphia.example.com/api/health`.
Esa URL es `API_BASE_URL` en GitHub; la del frontend debe estar en `CORS_ORIGINS`.

## 7. Actualizaciones

El workflow *Deploy* de GitHub Actions hace esto por SSH con el commit que pasó la CI
([github-actions.md](github-actions.md)). A mano:

```bash
cd /opt/aphia && git fetch origin && git checkout --detach origin/main
cd infra/production
docker compose --env-file .env.production up -d --build api files
```

MySQL no se reconstruye en cada despliegue. Actualice `MYSQL_VERSION` de forma deliberada,
con respaldo previo. El túnel de Cloudflare (`--profile tunnel`) solo se necesita si la API se
despliega en Workers ([tunnel-y-acceso-privado.md](tunnel-y-acceso-privado.md)).

## Recursos estimados

| Servicio | Límite de memoria |
| --- | --- |
| MySQL (buffer pool 512 MB) | 1200 MB (`MYSQL_MEMORY_LIMIT`) |
| API (Uvicorn) | 384 MB |
| Documentos | 256 MB |
| cloudflared (opcional) | 128 MB |
