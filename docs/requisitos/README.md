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
| Clientes | `person` y contactos | Flujo mínimo de prueba sobre la tabla demo `clientes`; pendiente migrarlo a `person` |
| Propietarios | `person`, `property_owner` | Pendiente |
| Inmuebles | `property` y relacionadas | Pendiente |
| Contratos | `property_agreement`, `agreement_party` | Pendiente |
| Finanzas | `financial_record`, `bank_account` | Pendiente (submodelo de pagos por definir) |
| Documentos | `file_record` y vínculos | Servicio de almacenamiento listo; integración con la API pendiente |
| Usuarios, permisos y trazabilidad | `user_account`, `app_role`, `user_role` | Estructura de roles preparada; autenticación y auditoría pendientes |

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
- Roles reales y matriz de permisos (borrador actual: `admin`, `asesor`, `consulta`).
- Tipos y tamaños de documentos esperados; tiempo de retención.
- Requisitos legales aplicables al tratamiento de datos personales en Colombia
  (Ley 1581 de 2012 y normas reglamentarias) — validar con el asesor del proyecto.
- Objetivos de recuperación (RPO/RTO) aceptables para la empresa.
