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

**No abra los puertos 3306, 4000, 80 ni 443**: el túnel de Cloudflare es una conexión
saliente. Nota: Docker puede saltarse ufw para puertos publicados; por eso el Compose de
producción no publica ninguno.

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
# Edite .env.production: TUNNEL_TOKEN (paso del túnel) y ajuste de memoria
chmod 644 mysql/conf.d/aphia.cnf   # MySQL ignora archivos de configuración con escritura global
```

## 5. Arranque

```bash
docker compose --env-file .env.production up -d --build mysql files
docker compose --env-file .env.production ps        # ambos "healthy"
docker compose --env-file .env.production logs mysql | grep 01-usuarios
```

Luego continúe con [MySQL](mysql.md) (migraciones) y [el túnel](tunnel-y-acceso-privado.md).
Cuando el túnel esté creado: `docker compose --env-file .env.production up -d`.

## 6. Actualizaciones

```bash
cd /opt/aphia && git pull
cd infra/production
docker compose --env-file .env.production up -d --build
```

Actualice `MYSQL_VERSION` y `CLOUDFLARED_VERSION` de forma deliberada, con respaldo previo.

## Recursos estimados

| Servicio | Límite de memoria |
| --- | --- |
| MySQL (buffer pool 512 MB) | 1200 MB (`MYSQL_MEMORY_LIMIT`) |
| Documentos | 256 MB |
| cloudflared | 128 MB |
