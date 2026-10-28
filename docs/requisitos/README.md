# Requisitos y alcance

## Contexto

APHIA S.A.S. es una inmobiliaria pequeña en Colombia. El sistema es de uso interno, con pocos
usuarios simultáneos y carga moderada.

## Dominios del sistema

El esquema de base de datos de todos los dominios ya está creado (modelo 3FN, migraciones
`0002`–`0007`, ver [modelo de datos](../arquitectura/modelo-de-datos.md)). Lo pendiente son
los módulos de la API y las pantallas, y las decisiones de negocio que el modelo deja abiertas.

| Dominio | Tablas | Estado de la aplicación |
| --- | --- | --- |
| Clientes | `person`, `person_document`, `person_phone`, `person_email`, `person_party_role` | Implementado (fase 2): CRUD, filtros por nombre/identificación y tipo de cliente, detalle con relaciones |
| Propietarios | `person`, `bank_account`, `property_owner` | Implementado (fase 2): CRUD con cuenta bancaria, filtros por nombre/identificación/correo, bloqueo de eliminación con inmuebles |
| Codeudores | `person`, `agreement_party` (`CO_DEBTOR`) | Implementado (fase 2): CRUD y consulta por identificación o contrato |
| Inmuebles | `property`, `property_owner`, `property_utility`, `city`, `service_provider` | Implementado (fase 3): CRUD con propietarios (papel automático), canon COP, estado y servicios públicos; filtros por estado, ciudad, propietario y texto; bloqueo de eliminación con contratos |
| Contratos | `property_agreement`, `agreement_party` | Pendiente |
| Finanzas | `financial_record`, `bank_account` | Pendiente (submodelo de pagos por definir) |
| Documentos | `file_record` y vínculos | Servicio de almacenamiento listo; integración con la API pendiente |
| Usuarios, permisos y trazabilidad | `user_account`, `app_role`, `user_role` | Implementado (fase 1): login con contraseña, bloqueo tras 3 intentos, CRUD de usuarios y roles. Auditoría pendiente |

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

- Las 10 decisiones de negocio del modelo de datos (identidad, roles, histórico, contratos
  simultáneos, finanzas, monedas, banca, archivos, permisos): ver
  [modelo de datos](../arquitectura/modelo-de-datos.md#decisiones-de-negocio-pendientes-antes-de-producción).
- ~~Roles reales y matriz de permisos~~ → definidos el 2026-10-28: `admin_sistemas` (todo),
  `administrativo` (crear, editar, eliminar), `asesor` (crear y editar, sin eliminar).
- Tipos y tamaños de documentos esperados; tiempo de retención.
- Requisitos legales aplicables al tratamiento de datos personales en Colombia
  (Ley 1581 de 2012 y normas reglamentarias) — validar con el asesor del proyecto.
- Objetivos de recuperación (RPO/RTO) aceptables para la empresa.
