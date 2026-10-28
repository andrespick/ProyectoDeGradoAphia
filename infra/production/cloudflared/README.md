# Cloudflare Tunnel (cloudflared)

El túnel se administra de forma **remota** desde el panel de Cloudflare: el contenedor
`cloudflared` de `compose.yaml` solo necesita el `TUNNEL_TOKEN` y no requiere archivo de
configuración local ni rutas públicas (*public hostnames*).

Destinos privados que se registran como servicios de **Workers VPC** (beta) apuntando a
este túnel. Los nombres son los de la red Docker `backend`:

| Servicio VPC          | Tipo | Destino           | Consumidor                      |
| --------------------- | ---- | ----------------- | ------------------------------- |
| `aphia-mysql`         | TCP  | `mysql:3306`      | Hyperdrive (`--scheme mysql`)   |
| `aphia-files`         | HTTP | `files:4000`      | Worker (`env.FILES_SERVICE`)    |

Los comandos exactos están en [docs/despliegue/tunnel-y-acceso-privado.md](../../../docs/despliegue/tunnel-y-acceso-privado.md).

No cree rutas públicas para MySQL ni para el servicio de documentos.
