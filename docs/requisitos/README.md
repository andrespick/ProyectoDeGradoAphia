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
| Codeudores | `person`, `agreement_party` (`CO_DEBTOR`) | Implementado (fases 2 y 4): CRUD, consulta por identificación o contrato, varios codeudores por contrato y asociación desde el detalle del contrato |
| Inmuebles | `property`, `property_owner`, `property_utility`, `city`, `service_provider` | Implementado (fase 3): CRUD con propietarios (papel automático), canon COP, estado y servicios públicos; filtros por estado, ciudad, propietario y texto; bloqueo de eliminación con contratos |
| Contratos | `property_agreement`, `agreement_party`, `agreement_category` | Implementado (fase 4): CRUD con propietarios, arrendatario y codeudores; filtros por fechas (solapamiento), inmueble, propietario, inquilino, tipo y estado; detalle con vista de impresión (PDF del navegador); bloqueo con dependencias |
| Finanzas | `financial_record`, `bank_account` | Pendiente (submodelo de pagos por definir) |
| Documentos | `file_record` y vínculos | Servicio de almacenamiento listo; integración con la API pendiente |
| Usuarios, permisos y trazabilidad | `user_account`, `app_role`, `user_role`, `audit_event` | Implementado (fases 1 y 6): login con contraseña, bloqueo configurable, CRUD de usuarios y roles, clave temporal, cierre de sesiones y auditoría |
| Administración del sistema | `security_policy`, `organization_profile`, `deleted_record`, `backup_run` | Implementado (fase 6): estado del sistema y respaldos, catálogos, política de seguridad, datos de la empresa y papelera |

## Requisitos funcionales del cliente

| Id | Requisito | Estado |
| --- | --- | --- |
| RF-01 | Registrar clientes (nombre, identificación, teléfono, correo, tipo de cliente) | Hecho (fase 2) |
| RF-02 | Consultar, modificar y eliminar clientes | Hecho (fase 2) |
| RF-03 | Registrar propietarios con datos de contacto y cuenta bancaria | Hecho (fase 2) |
| RF-04 | Consultar propietarios por nombre, identificación o correo | Hecho (fase 2) |
| RF-05 | Modificar y eliminar propietarios, excepto si tienen inmuebles | Hecho (fase 2) |
| RF-06 | Registrar inmuebles con dirección, propietario, canon, estado y servicios públicos | Hecho (fase 3) |
| RF-07 | Consultar inmuebles por estado, ciudad, propietario o texto | Hecho (fase 3) |
| RF-08 | Modificar y eliminar inmuebles (no con contratos) | Hecho (fase 3) |
| RF-09 | Registrar codeudores y asociar varios a un contrato | Hecho (fases 2 y 4) |
| RF-10 | Consultar codeudores por identificación o por contrato | Hecho (fases 2 y 4) |
| RF-11 | Modificar y eliminar codeudores | Hecho (fase 2) |
| RF-12 | Registrar contratos con inmueble, partes, fechas, canon, condiciones y texto | Hecho (fase 4) |
| RF-13 | Consultar contratos por fechas, inmueble, propietario, inquilino, tipo y estado | Hecho (fase 4) |
| RF-14 | Modificar y eliminar contratos (no con dependencias) | Hecho (fase 4) |
| RF-15 | Imprimir / guardar el contrato en PDF | Hecho (fase 4) |
| RF-16 | Gestionar usuarios y roles (solo Administrador de Sistemas) | Hecho (fase 1) |
| RF-17 | Inicio de sesión con usuario y contraseña | Hecho (fase 1) |
| RF-18 | Bloqueo de la cuenta tras 3 intentos fallidos (15 min) e información al administrador | Hecho (fase 1); valores configurables (fase 6) |
| RF-19 | Auditoría de inicios de sesión y cambios (quién, qué, cuándo) | Hecho (fase 6, ampliación pedida por el responsable) |
| RF-20 | Estado del sistema y respaldos visibles para el administrador; solicitud de respaldo manual | Hecho (fase 6) |
| RF-21 | Administración de catálogos (tipos, ciudades, bancos, proveedores) | Hecho (fase 6) |
| RF-22 | Política de seguridad configurable y datos de la empresa (sin cambio de logotipo) | Hecho (fase 6) |
| RF-23 | Clave temporal con cambio obligatorio y cierre de sesiones | Hecho (fase 6) |
| RF-24 | Papelera: restaurar personas, inmuebles y contratos eliminados | Hecho (fase 6) |

## Requisitos no funcionales del cliente

| Id | Requisito | Cómo se cumple |
| --- | --- | --- |
| RNF-01 | Respuesta a consultas en menos de 3 s | Índices del modelo 3FN, paginación; medición en `test_rendimiento_mysql.py` con 500 personas |
| RNF-02 | Actualización de pantalla en menos de 2 s tras guardar | Recarga de la lista tras cada escritura; E2E con `toBeVisible({ timeout: 2000 })` |
| RNF-03 | Contraseñas con hash (SHA-256) | PBKDF2-HMAC-SHA256 con sal y 100 000 iteraciones (más fuerte que SHA-256 simple) |
| RNF-04 | Control de acceso por roles | Grupos `LECTURA`/`ESCRITURA`/`ELIMINACION`/`GESTION_SISTEMA` en la API y en la web |
| RNF-05 | Respaldo diario local en un directorio restringido | `backup.sh`: copia cifrada en `BACKUP_LOCAL_DIR` (700/600) con retención, cron diario |
| RNF-06 | Manual de usuario y ayuda en línea | `docs/manual-usuario.md` y `/ayuda` con enlace desde cada pantalla |
| RNF-07 | Interfaz adaptable a computador, tableta y celular | Barra lateral / riel / cajón; tablas desplazables; E2E a 375 px |
| RNF-08 | Compatibilidad con Chrome, Safari y Firefox | Playwright: Chromium completo; Firefox y WebKit con pruebas *smoke* |
| RNF-09 | Tamaño de la aplicación ≤ 5 GB | Imágenes y volúmenes acotados; documentos en volumen aparte con límite por archivo |
| RNF-10 | Código modular y documentado | Módulos `router → service → repository`, features por dominio, `docs/` y `AGENTS.md` |
| RNF-11 | Disponibilidad y recuperación | `/api/ready`, respaldos cifrados y guía de restauración |
| RNF-12 | Datos ficticios en desarrollo y pruebas | Seeds y pruebas con dominios `example.test` |

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
- ~~Roles reales y matriz de permisos~~ → definidos el 2026-10-28: `admin_sistemas` (solo gestión
  del sistema: usuarios, auditoría, catálogos, configuración, papelera, estado y respaldos),
  `administrativo` (crear, editar, eliminar), `asesor` (crear y editar, sin eliminar).
- Retención de la auditoría y de la papelera (hoy se vacían a mano).
- Tipos y tamaños de documentos esperados; tiempo de retención.
- Requisitos legales aplicables al tratamiento de datos personales en Colombia
  (Ley 1581 de 2012 y normas reglamentarias) — validar con el asesor del proyecto.
- Objetivos de recuperación (RPO/RTO) aceptables para la empresa.

## Matriz de trazabilidad

| Requisito | API | Pantallas | Pruebas |
| --- | --- | --- | --- |
| RF-01, RF-02 | `GET/POST /api/v1/clientes`, `GET/PUT/DELETE /clientes/{id}`, `GET /personas/buscar` | `/clientes`, `/clientes/nuevo`, `/clientes/:id`, `/clientes/:id/editar` | `test_personas.py`, `test_personas_mysql.py`, `PersonaForm.test.tsx`, `PersonasListPage.test.tsx`, `clientes.spec.ts` |
| RF-03, RF-04, RF-05 | `/api/v1/propietarios` (misma fábrica; papel OWNER fijo) | `/propietarios…` | `test_personas.py` (dependencias al eliminar), `test_personas_mysql.py` (propietario con inmueble → 409), `propietarios.spec.ts` |
| RF-06, RF-07, RF-08 | `/api/v1/inmuebles` | `/inmuebles`, panel `/inmuebles/nuevo`, `/inmuebles/:id/editar` | `test_inmuebles.py`, `test_inmuebles_mysql.py`, `InmuebleForm.test.tsx`, `InmueblesPage.test.tsx`, `inmuebles.spec.ts` |
| RF-09, RF-10, RF-11 | `/api/v1/codeudores` (`?contrato_id`, `?q`), `codeudores_ids` de contratos | `/codeudores…`, detalle del contrato «Asociar codeudor» | `test_personas.py`, `test_contratos.py`, `test_contratos_mysql.py`, `ContratoDetallePage.test.tsx`, `codeudores.spec.ts`, `contratos.spec.ts` |
| RF-12, RF-13, RF-14 | `/api/v1/contratos` | `/contratos`, `/contratos/nuevo`, `/contratos/:id`, `/contratos/:id/editar` | `test_contratos.py` (matriz de fechas), `test_contratos_mysql.py`, `ContratoForm.test.tsx`, `ContratosPage.test.tsx`, `contratos.spec.ts` |
| RF-15 | `GET /api/v1/contratos/{id}` (texto completo) | `/contratos/:id` «Imprimir / guardar PDF» (`@media print`) | `ContratoDetallePage.test.tsx` (`window.print`), `contratos.spec.ts` |
| RF-16 | `/api/v1/usuarios`, `POST /usuarios/{id}/desbloquear` | `/usuarios`, panel de usuario | `test_usuarios.py`, `test_usuarios_mysql.py`, `UsuariosPage.test.tsx`, `usuarios.spec.ts` |
| RF-17, RF-18 | `POST /api/v1/auth/login`, `GET /auth/me`, `GET /auth/politica` | `/login`, alertas de bloqueo en `/usuarios` | `test_auth.py`, `test_sesiones.py`, `test_passwords.py`, `test_tokens.py`, `test_auth_mysql.py`, `LoginPage.test.tsx`, `auth.spec.ts` |
| RF-19 | `GET /api/v1/auditoria` (y `Auditar` en cada escritura) | `/auditoria` | `test_administracion.py::TestAuditoria`, `test_sesiones.py`, `test_administracion_mysql.py`, `Administracion.test.tsx`, `administracion.spec.ts` |
| RF-20 | `GET /api/v1/sistema/estado`, `GET/POST /sistema/respaldos`; `backup.sh` registra en `backup_run` | `/sistema` | `test_administracion.py::TestSistema`, `test_administracion_mysql.py`, `Administracion.test.tsx`, `administracion.spec.ts` |
| RF-21 | `GET/POST /api/v1/catalogos/{catalogo}`, `PUT/DELETE /catalogos/{catalogo}/{id}` | `/catalogos` | `test_administracion.py::TestCatalogos`, `test_administracion_mysql.py`, `Administracion.test.tsx`, `administracion.spec.ts` |
| RF-22 | `GET/PUT /api/v1/configuracion/seguridad`, `GET/PUT /configuracion/empresa` | `/configuracion`, encabezado de impresión del contrato, pie de página | `test_administracion.py::TestConfiguracion`, `test_sesiones.py::TestPoliticaEnElLogin`, `test_administracion_mysql.py`, `Administracion.test.tsx`, `administracion.spec.ts` |
| RF-23 | `POST /api/v1/usuarios/{id}/restablecer-clave`, `POST /usuarios/{id}/cerrar-sesiones`, `POST /auth/cambiar-clave` | `/usuarios` (Clave, Sesiones), `/cambiar-clave` | `test_sesiones.py`, `test_administracion.py::TestUsuarios`, `test_administracion_mysql.py`, `Administracion.test.tsx`, `administracion.spec.ts` |
| RF-24 | `GET /api/v1/papelera`, `POST /papelera/{id}/restaurar`, `DELETE /papelera/{id}` | `/papelera` | `test_papelera.py`, `test_administracion_mysql.py`, `Administracion.test.tsx`, `administracion.spec.ts` |
| RNF-01 | Listados paginados con `COUNT` separado | — | `test_rendimiento_mysql.py` (< 3 s con 500 personas) |
| RNF-02 | — | `reload()` tras cada escritura | E2E `toBeVisible({ timeout: 2_000 })` en clientes, inmuebles y contratos |
| RNF-03, RNF-04 | `passwords.py`, `require_roles` | enlaces y botones según `tiene(roles)` | `test_passwords.py`, `test_*` «asesor 403», `ProtectedRoute.test.tsx` |
| RNF-05 | — | — | `infra/production/backup/backup.sh` (manual, ver restauración) |
| RNF-06 | — | `/ayuda`, enlace «Ayuda» en cada cabecera y en el login | `ayuda.spec.ts` |
| RNF-07 | — | `MainLayout` (barra / riel / cajón), `.table-wrap`, `SlideOver` a pantalla completa | `responsive.spec.ts` (375 px), `MainLayout.test.tsx` |
| RNF-08 | — | — | Proyectos Playwright `firefox` y `webkit` (`@smoke`) |
| RNF-10 | `modules/<dominio>` | `features/<dominio>` | `pnpm lint`, `pnpm typecheck`, `docs/desarrollo/crear-modulo.md` |
