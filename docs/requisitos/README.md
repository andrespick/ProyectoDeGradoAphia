# Requisitos y alcance

## Contexto

APHIA S.A.S. es una inmobiliaria pequeña en Colombia. El sistema es de uso interno, con pocos
usuarios simultáneos y carga moderada.

## Dominios del sistema

| Dominio | Estado |
| --- | --- |
| Clientes | Versión mínima de prueba (nombre, correo, fechas) para validar la arquitectura |
| Propietarios | Pendiente |
| Inmuebles | Pendiente |
| Contratos | Pendiente |
| Documentos | Servicio de almacenamiento listo; integración con la API pendiente |
| Usuarios, permisos y trazabilidad | Estructura de roles preparada; autenticación pendiente |

## Prioridades no funcionales (en orden)

1. Bajo costo de infraestructura.
2. Seguridad de la información.
3. Facilidad de desarrollo y mantenimiento.
4. Portabilidad.
5. Pruebas automatizadas.
6. Despliegue reproducible.
7. Simplicidad arquitectónica.
8. Posibilidad de crecimiento futuro.

## Restricciones

- Backend en Cloudflare Python Workers con ruta alternativa en Linux (Uvicorn).
- MySQL 8.4 LTS en un VPS Linux (2 vCPU, 2–4 GB RAM, 20–40 GB SSD), proveedor no definido.
- Documentos en el VPS, no en MySQL.
- Sin datos personales reales en desarrollo ni en pruebas.

## Pendiente de levantar con la empresa

- Campos y reglas de negocio de propietarios, inmuebles, contratos y clientes.
- Roles reales y matriz de permisos (borrador actual: `admin`, `asesor`, `consulta`).
- Tipos y tamaños de documentos esperados; tiempo de retención.
- Requisitos legales aplicables al tratamiento de datos personales en Colombia
  (Ley 1581 de 2012 y normas reglamentarias) — validar con el asesor del proyecto.
- Objetivos de recuperación (RPO/RTO) aceptables para la empresa.
