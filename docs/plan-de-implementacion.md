# Plan de implementación de los requisitos de APHIA

> Copia versionada del plan aprobado el 28 de octubre de 2026. Es la referencia para retomar el
> trabajo en cualquier sesión: ubique la fase en curso, siga sus criterios de aceptación y
> actualice la tabla de estado y la bitácora al cerrar cada fase.

## Estado por fase

| Fase | Contenido | Commit | Estado | Fecha |
| --- | --- | --- | --- | --- |
| 0 | Base: catálogos, papeles de persona, bloqueo, identidad visual, componentes compartidos | «Agrega catálogos base, papeles de persona y columnas de bloqueo (fase 0)» | hecha | 2026-10-28 |
| 1 | Usuarios y login real | — | pendiente | — |
| 2 | Clientes, propietarios y codeudores sobre `person` | — | pendiente | — |
| 3 | Inmuebles | — | pendiente | — |
| 4 | Contratos | — | pendiente | — |
| 5 | Ayuda, responsive, respaldo local y documentación | — | pendiente | — |

## Contexto

El repositorio tiene la base técnica (API FastAPI para Workers/Uvicorn, web React, MySQL con el
modelo 3FN en migraciones `0002`–`0007`, servicio de documentos, infra) pero solo un flujo de
demostración: el módulo `clientes` sobre la tabla demo `clientes` (migración `0001`), sin
autenticación real (`AUTH_MODE=development` entrega un usuario ficticio) y sin pantallas de
negocio. El cliente entregó los requisitos funcionales (clientes, propietarios, inmuebles,
codeudores, contratos, usuarios/acceso) y no funcionales (rendimiento, seguridad, usabilidad,
disponibilidad, compatibilidad, mantenibilidad). Este plan los implementa sobre el modelo 3FN
existente, en seis fases, cada una con API + pantallas + pruebas + documentación y un commit
propio, en la rama `feat/entorno-desarrollo`.

## Decisiones cerradas con el responsable (no reabrir)

1. **Personas con varios papeles.** Una fila en `person` por identificación. Una persona puede
   ser a la vez propietaria, arrendataria y codeudora. El «tipo de cliente» del requisito son
   esos papeles: al registrar se elige uno; los demás se agregan a mano o automáticamente al
   asociarla como propietaria de un inmueble o como inquilina/codeudora de un contrato (la UI
   busca la persona por identificación o la registra en el momento). La consulta de un cliente
   muestra todo lo relacionado (papeles, inmuebles, contratos por papel, cuentas bancarias); en
   un contrato cada persona aparece solo con el papel que tiene ahí. Requiere una tabla nueva
   `person_party_role` (migración) que reutiliza el catálogo `party_role` con códigos
   `OWNER`, `TENANT`, `CO_DEBTOR`. `person_category` queda sin uso (NULL).
2. **Permisos.** `admin_sistemas`: todo, incluido usuarios. `administrativo`: crear, editar y
   eliminar en los módulos de negocio. `asesor`: crear y editar, **no** eliminar. Solo
   `admin_sistemas` gestiona usuarios.
3. **Bloqueo de cuenta.** Tras 3 intentos fallidos, bloqueo de 15 minutos. La pantalla de
   Usuarios muestra «Bloqueada» con botón «Desbloquear»; el evento queda en los logs JSON. Sin
   correo.
4. **Entrega.** Todas las fases, un commit por fase: 0 base → 1 usuarios y login → 2
   clientes/propietarios/codeudores → 3 inmuebles → 4 contratos → 5 ayuda, responsive,
   respaldo local y documentación.

## Decisiones técnicas (sin dependencias nuevas; compatibles con Pyodide)

- **Hash de contraseñas:** `hashlib.pbkdf2_hmac("sha256", clave, sal_aleatoria, iteraciones)`
  guardado como `pbkdf2_sha256$<iter>$<sal_b64>$<hash_b64>` en `user_account.hashed_password`.
- **Sesión:** token firmado con HMAC-SHA256 (stdlib) = `base64url(json{sub, nombre, roles, exp})
  . firma`, secreto `AUTH_SECRET` en `Settings`. Se envía como `Authorization: Bearer` (CORS ya
  lo permite; `credentials: "omit"` se mantiene). La web lo guarda en `sessionStorage`.
  Caducidad 8 h. Nuevo `AUTH_MODE=database`; `development` queda solo para pruebas unitarias.
- **PDF del contrato:** vista de impresión del navegador (hoja de estilos `@media print` y botón
  «Imprimir / guardar PDF»). Sin librería de PDF.
- **Catálogos de nombre libre** (`city`, `financial_institution`, `service_provider`): la API
  hace *buscar o crear* por nombre exacto; la UI usa `<input list>` con `<datalist>`. Sin
  pantallas de catálogos. Los códigos de los que depende la aplicación van en una migración
  (producción los necesita); los datos ficticios, en `database/seeds/`.
- **Búsquedas sin distinguir mayúsculas/acentos** sobre colación binaria: `COLLATE
  utf8mb4_0900_ai_ci` en los filtros `LIKE` (volumen pequeño; sin índice). `user_name` e
  identificación se comparan exactas.
- **Códigos de catálogo** (tipo de identificación, tipo de contrato, estado, papel, rol) se
  validan contra la tabla en el repositorio (`INSERT … SELECT … FROM catalogo WHERE code=%s`
  y comprobación de `rowcount`), no con `Literal` en Pydantic: agregar un valor es una
  migración, no un cambio de código.

## Identidad visual y mockups (Google Stitch)

Fuente de verdad: el proyecto de Stitch
<https://stitch.google.com/projects/8942478746065544413>, exportado en la raíz del repo como
`DESIGN.md` (sistema «APHIA Real Estate & Property Core») y la carpeta
`stitch_sistema_aphia_ui_ux/` (13 pantallas, cada una con `screen.png` y `code.html` hecho con
Tailwind por CDN, Plus Jakarta Sans y Material Symbols desde Google Fonts, más una copia
idéntica de `DESIGN.md`). Identidad: rojo institucional (`#B70011` marca y botones primarios,
`#DC2626` acento, `#991B1B` hover, `#FEE2E2` fondos suaves), neutros pizarra `#0F172A`…`#F8FAFC`,
acentos esmeralda `#10B981`, ámbar `#F59E0B` e índigo `#6366F1`; tipografía **Plus Jakarta Sans**;
controles 8 px, tarjetas 12 px, insignias píldora; barra lateral fija de 260 px + barra superior
en escritorio, riel de 72 px en tableta y cajón lateral en móvil.

### Reglas

- `.gitignore` (fase 0): `DESIGN.md` y `stitch_sistema_aphia_ui_ux/`. Son material de trabajo
  local, no se versionan. El HTML exportado es **referencia visual**, no código a copiar: la web
  sigue en CSS plano (sin Tailwind), la fuente se autoaloja y los iconos van como SVG en línea
  (la CSP `default-src 'self'` no permite Google Fonts ni CDN).
- `DESIGN.md` se **complementa** (fase 0) con tres secciones: «Mockups (Google Stitch)» (URL,
  inventario de las 13 pantallas con su ruta en la web, tabla de abajo), «Aplicación en el
  código» (tokens en `styles.css`, fuente, iconos, breakpoints, patrón de formularios) y
  «Decisiones» (adaptaciones y exclusiones de esta sección; se amplía en cada fase).
- El repositorio versiona los tokens en `apps/web/src/styles.css` (cabecera que cita el proyecto
  de Stitch como origen) y un resumen breve en `docs/diseno/README.md` (paleta, tipografía,
  layout, componentes, mapa de insignias, inventario de pantallas) para ser autosuficiente.
- Cada pantalla se construye siguiendo su mockup (estructura, jerarquía, componentes); el
  contenido se ajusta a los campos reales del modelo 3FN y a los requisitos. Lo que el mockup
  muestra y no está en el modelo ni en los requisitos se excluye (lista más abajo) y se anota
  en «Decisiones».

### Inventario de pantallas y correspondencia

| Mockup (`stitch_sistema_aphia_ui_ux/…`) | Ruta web | Fase | Qué se toma / qué se adapta |
| --- | --- | --- | --- |
| `aphia_autenticaci_n_y_login_seguro` | `/login` | 1 | Diseño partido: columna izquierda de marca (insignia «Portal administrativo», titular, dos tarjetas de datos tomadas de `/api/v1/resumen`) y tarjeta de acceso (logo, «Iniciar sesión», aviso «Máximo 3 intentos», Usuario, Contraseña con mostrar/ocultar, «Recordarme» = guardar el token en `localStorage` en vez de `sessionStorage`, botón rojo). **Se quita** el selector «Perfil de acceso» (el rol viene de la cuenta) y «¿Olvidaste tu contraseña?» enlaza a `/ayuda#inicio-de-sesion` («contacte al Administrador de Sistemas; el bloqueo expira en 15 min»). En móvil solo la tarjeta. |
| `aphia_tablero_principal_hub_de_m_dulos` | `/` (Inicio) | 1, crece en 2–4 | Saludo con nombre y fecha; 4 tarjetas KPI (Inmuebles total/ocupados/disponibles, Clientes por papel, Contratos vigentes, Vencimientos < 30 días con enlace a `/contratos?estado=por_vencer`); rejilla de tarjetas de módulo con conteos y flecha (Clientes, Propietarios, Codeudores, Inmuebles, Contratos, Usuarios solo admin); lista «Contratos que vencen pronto» en lugar de «Actividad operativa» (no hay bitácora). **Se excluyen** recaudo/cánones, distribución territorial, pólizas y la tarjeta hero. |
| `aphia_gesti_n_de_clientes` | `/clientes` | 2 | Cabecera con icono, título + chip de total, «Registrar cliente»; 4 KPI (Arrendatarios, Propietarios, Codeudores, Total); buscador + segmentos **Todos / Arrendatarios / Propietarios / Codeudores** (`?papel=`); tabla: avatar con iniciales + nombre + correo, identificación, teléfono, «Tipo de cliente» (insignias por papel), acciones ver/editar/eliminar; paginación con tamaño de página. **Se excluyen** «Exportar listado», columna Inmueble/Contrato y estado «En mora» (sin finanzas). |
| `aphia_gesti_n_de_propietarios` | `/propietarios` | 2 | Banner informativo «Un propietario con inmuebles vinculados no se puede eliminar»; KPI (Propietarios, Inmuebles vinculados, Cuentas bancarias registradas); buscador (nombre, identificación, correo); tabla: propietario (nombre, identificación, ciudad de la dirección), contacto (correo, teléfono), cuenta bancaria (banco, tipo, número enmascarado `•••• 4902`), chip «N inmuebles» / «Sin inmuebles», acciones. **Se excluyen** comisión, dispersión ACH, «Batch», tarjetas legales. |
| `aphia_gesti_n_de_inmuebles` | `/inmuebles` (+ `/inmuebles/nuevo`, `/inmuebles/:id/editar` como panel lateral) | 3 | Cabecera con migas, título, chip de total, «Registrar inmueble» que abre un **panel deslizante** derecho con secciones numeradas: 1 Identificación y localización (dirección, ciudad, matrícula), 2 Canon y titularidad (propietarios, canon COP, estado como botones de radio), 3 Cuentas de servicios públicos (tipo, proveedor, número); KPI (Total, Ocupados, Disponibles); filtros Estado / Ciudad / Propietario / búsqueda con chips de filtros aplicados y «Restablecer»; tabla: matrícula, dirección + ciudad, propietarios, canon (tabular), estado (punto + insignia), servicios (chips), acciones. **Se excluyen** fotos, tipo de inmueble, área, estrato, barrio, cuota de administración, observaciones, «Sincronizar catastro», «Exportar», selección múltiple (no están en el modelo; agregarlos exige migración y decisión). |
| `aphia_gesti_n_de_contratos_y_codeudores` | `/contratos` | 4 | Cabecera con migas, «Nuevo contrato»; banner rojo «Un contrato con dependencias no se puede modificar ni eliminar»; KPI (Contratos, Vigentes, Codeudores vinculados, Por vencer < 60 días); pestañas **Todos / Vigentes / Por vencer / Finalizados** (`?estado=`); buscador + rango de fechas + ciudad; tabla: nº y vigencia (id, fechas, «N días restantes»), inmueble, partes (Propietario(s), Arrendatario), codeudores (chips), canon, estado; acciones. «+ Asociar codeudor» vive en el detalle del contrato. **Se excluyen** pólizas/aseguradoras, minutas masivas, firma electrónica, reajuste IPC, recaudo. |
| `aphia_gesti_n_de_usuarios_y_roles_de_acceso_1` y `_2` | `/usuarios` | 1 | Cabecera «Usuarios y roles», «Registrar usuario»; banner «Suspensión automática tras 3 intentos fallidos»; KPI (Total, Activos, Bloqueados); **alerta por cada cuenta bloqueada** con botón «Desbloquear» (así se «informa al administrador»); buscador + chips de rol (`?rol=`) + estado (`?estado=`); tabla: usuario (iniciales, nombre, `@usuario`), documento, correo, rol (insignia), estado (conmutador Activo/Inactivo → `PUT activo`, «Bloqueada»), seguridad («N fallos» / «Desbloquear»), acciones editar/eliminar; tarjeta estática «Roles y alcance» (matriz de permisos) y tarjeta «Seguridad» (PBKDF2-SHA256, bloqueo 3/15). **Se excluyen** 2FA, auditoría de accesos, política criptográfica, último respaldo. |
| `aphia_recuperaci_n_de_contrase_a_y_desbloqueo` | — | — | **Excluida**: requiere correo/SMS (decisión 3). Su contenido útil pasa a `/ayuda#inicio-de-sesion` y al enlace del login. |
| `aphia_auditor_a_de_intentos_de_acceso_y_seguridad`, `aphia_exportar_reporte_forense_en_pdf`, `aphia_exportar_reporte_forense_en_csv_excel`, `aphia_confirmaci_n_y_descarga_de_paquete_zip_cifrado` | — | — | **Excluidas** de este plan: necesitan una bitácora de intentos/acciones (tabla nueva, decisión de negocio 10 «auditoría con actor y fecha») y generación de archivos. Quedan registradas como fase futura «Auditoría de accesos y exportaciones». |

### Cascarón común (todas las pantallas autenticadas)

- **Barra lateral** (260 px, blanca, borde derecho `#E2E8F0`): logo + «APHIA / Gestión
  inmobiliaria»; navegación con icono: Inicio, Clientes, Propietarios, Codeudores, Inmuebles,
  Contratos, Usuarios (solo admin), Ayuda; ítem activo con fondo `#FEE2E2`, texto rojo y barra
  izquierda roja; al pie tarjeta «Estado del sistema: En línea / Servidor en línea» alimentada
  por `useApiStatus`, enlaces «Documentación» (`/ayuda`) y «Salir». **Se excluye** el chip de
  sede «Edificio / Sede Central PH-01» (una sola sede).
- **Barra superior**: buscador global «Buscar inmueble, cliente, contrato, propietario…» (fase
  4, `GET /api/v1/buscar`; hasta entonces busca en clientes), botón «+ Nuevo inmueble»
  (ESCRITURA), chip con el rol del usuario, nombre + rol y menú con «Cerrar sesión». **Se
  excluye** la campana de notificaciones.
- 768–1279 px: riel de 72 px solo iconos (`aria-label`, `title`); < 768 px: barra superior con
  botón «Menú» y cajón lateral (`<dialog>`, cierre con Escape y al navegar, foco atrapado).
- **Plantilla de página**: migas (`APHIA › Módulo`), `.page-header` (icono, h1, chip de total,
  descripción, acciones a la derecha), banner de regla si aplica, fila de KPI (`.kpi-grid`,
  tarjetas con etiqueta en mayúsculas, cifra grande y subtexto), `.filters` (buscador,
  segmentos, selects, chips de filtros aplicados + «Restablecer»), tarjeta con tabla,
  paginación («Mostrando 1–20 de 57», tamaño de página 10/20/50, Anterior/Siguiente).
- **Formularios**: clientes/propietarios/codeudores, inmuebles y usuarios se editan en un
  **panel deslizante** derecho (`components/SlideOver.tsx`: `<dialog>` de 560–640 px anclado a
  la derecha, cabecera con icono/título/subtítulo y ×, secciones numeradas, pie con «Cancelar»
  y «Guardar»; pantalla completa en móvil) montado por rutas hijas (`/x/nuevo`,
  `/x/:id/editar`) sobre la lista, para conservar enlaces directos. Contratos usa página
  completa (texto largo). Confirmaciones de borrado con `window.confirm`.
- **KPI**: módulo `resumen` (`GET /api/v1/resumen`, LECTURA; fase 1 con usuarios y crece en
  2–4): `{personas: {total, propietarios, arrendatarios, codeudores}, inmuebles: {total,
  ocupados, disponibles}, contratos: {total, vigentes, por_vencer_30, por_vencer_60,
  finalizados, codeudores_vinculados}, usuarios: {total, activos, bloqueados}}` con una
  consulta de `COUNT` por bloque; `features/resumen/useResumen.ts`. Cada lista muestra sus
  tarjetas desde ahí.
- **Iconos**: `components/icons.tsx` con los SVG de Material Symbols Outlined que usan los
  mockups (`dashboard, groups, key, apartment, description, admin_panel_settings, help_outline,
  logout, search, add, edit, delete, visibility, close, chevron_left/right, expand_more, lock,
  check_circle, warning, info, verified, person_add, print, menu`), 20 px, `aria-hidden`.

### Traducción de `DESIGN.md` a la web (fase 0, `styles.css`)

| Ámbito | Decisión |
| --- | --- |
| Variables | `--color-primary #B70011`, `--color-accent #DC2626`, `--color-primary-dark #991B1B`, `--color-primary-light #FEE2E2`, `--slate-50…900`, `--status-active(-bg)`, `--status-pending(-bg)`, `--status-debtor(-bg)`, `--surface #FFFFFF`, `--bg #F8FAFC`, `--text #0F172A`, `--muted #475569`, `--border #E2E8F0`, `--radius 0.5rem`, `--radius-lg 0.75rem`, `--shadow-1 0 1px 2px rgba(15,23,42,.05)`, `--shadow-2 0 4px 6px -1px rgba(15,23,42,.08), 0 2px 4px -2px rgba(15,23,42,.04)`. Se elimina el tema oscuro (`prefers-color-scheme`): la identidad define solo tema claro. |
| Tipografía | `@fontsource-variable/plus-jakarta-sans` importado en `main.tsx` (autoalojada; la CSP `default-src 'self'` no permite Google Fonts). Escala: h1 32/40 700 (−0.02em; 26/34 en móvil), h2 24/32 600, títulos de tarjeta 20/28 600, `title-md` 16/24 600, cuerpo 16/24 y 14/20, `label-sm` 12/16 600 +0.02em (insignias), `table-header` 11/16 700 mayúsculas +0.05em pizarra 600, `.num` con `font-variant-numeric: tabular-nums` alineado a la derecha (canon, importes). |
| Botones | Primario rojo / hover `#991B1B` / anillo de foco `#FEE2E2` 2 px; `button.secondary` blanco con borde pizarra 200 y texto pizarra 700; `button.ghost` sin fondo; `button.danger` rojo con hover `#FEE2E2`. Altura mínima 40 px. |
| Campos | Borde `#E2E8F0`, hover `#CBD5E1`, foco borde `#DC2626` + anillo `3px rgba(220,38,38,.12)`, placeholder `#94A3B8`, error borde rojo + leyenda; casillas 16 px radio 4 px, marcadas en rojo. |
| Insignias (`.badge`) | píldora 12 px/600, padding 4×10, con borde 1 px: `badge-ok` esmeralda (`#ECFDF5`/`#10B981`/`#A7F3D0`), `badge-warn` ámbar (`#FFFBEB`/`#D97706`/`#FDE68A`), `badge-info` índigo (`#EEF2FF`/`#4F46E5`/`#C7D2FE`), `badge-muted` pizarra (`#F1F5F9`/`#475569`/`#E2E8F0`), `badge-error` rojo (`#FEE2E2`/`#991B1B`). Mapa: papel Propietario → rojo claro (marca), Arrendatario → esmeralda, Codeudor → índigo; inmueble Ocupado → esmeralda, Disponible → ámbar; usuario Activo → esmeralda, Inactivo → pizarra, Bloqueada → rojo. |
| Tablas | Cabecera `#F8FAFC` + `table-header`; filas con borde inferior `#F1F5F9`, hover `#F8FAFC`; números tabulares a la derecha; `.table-wrap` con desplazamiento horizontal en móvil. |
| Tarjetas | Blanco, borde `#E2E8F0`, radio 12 px, padding 1.5 rem, `--shadow-1`; cabecera con título 16/600 y acciones o insignia a la derecha. |
| Layout (`MainLayout`) | Según «Cascarón común»: barra lateral 260 px + barra superior (≥ 1280 px), riel 72 px (768–1279 px), cajón (< 768 px); área de trabajo con padding 2 rem (1 rem en móvil). `components/SlideOver.tsx`, `components/KpiCard.tsx`, `components/Segmented.tsx` (pestañas/segmentos de filtro), `components/Avatar.tsx` (iniciales). |
| Mensajes | `alert-success` esmeralda, `alert-error` rojo claro con «Código de soporte», `alert-warn` ámbar; `role` como hoy. |

Las secciones de las fases siguientes que dicen «menú», «badge» o «responsive» se entienden
con esta identidad; la fase 5 solo verifica y pule, no la introduce.

## Convenciones transversales

### Roles y grupos (`apps/api/src/modules/auth/schemas.py`, espejo en `apps/web/src/features/auth/roles.ts`)

| `Role` | `app_role.code` | nombre |
| --- | --- | --- |
| `ADMIN_SISTEMAS = "admin_sistemas"` | `ADMIN_SISTEMAS` | Administrador de Sistemas |
| `ADMINISTRATIVO = "administrativo"` | `ADMINISTRATIVO` | Administrativo |
| `ASESOR = "asesor"` | `ASESOR` | Asesor |

Grupos: `LECTURA` y `ESCRITURA` = los tres roles; `ELIMINACION` = admin_sistemas + administrativo;
`GESTION_USUARIOS` = admin_sistemas. Cada router de negocio lleva
`dependencies=[Depends(require_roles(*LECTURA))]` y cada `DELETE` añade
`require_roles(*ELIMINACION)`. `Role(code.lower())` ↔ `role.value.upper()`.

### Helpers SQL nuevos: `apps/api/src/db/sql.py`

`ER_DUP_ENTRY=1062`, `ER_ROW_IS_REFERENCED=1451`, `ER_NO_REFERENCED_ROW=1452`,
`mysql_error_code(exc) -> int | None`, `like_pattern(q)` (escapa `\ % _` y envuelve en `%…%`).
Idiomas: un hijo por persona en lecturas (`LEFT JOIN person_phone ph ON ph.phone_id = (SELECT
MIN(phone_id) FROM person_phone WHERE person_id = p.person_id)`); *buscar o crear* de `city`,
`financial_institution`, `service_provider` dentro de la transacción de escritura; papel
automático con `INSERT IGNORE INTO person_party_role … SELECT %s, party_role_id FROM party_role
WHERE code = %s`; listas `IN (...)` solo con placeholders.

### Códigos de error (subclases de `core.errors`, mensajes al usuario en español)

| Código | HTTP | Base |
| --- | --- | --- |
| `credenciales_invalidas` | 401 | AuthenticationRequiredError |
| `cuenta_bloqueada` (mensaje con minutos restantes) | 423 | AppError |
| `usuario_no_encontrado` / `persona_no_encontrada` / `inmueble_no_encontrado` / `contrato_no_encontrado` | 404 | NotFoundError |
| `usuario_duplicado`, `identificacion_duplicada`, `ultimo_administrador`, `usuario_actual` | 409 | ConflictError |
| `persona_con_dependencias` (mensaje dice qué la referencia), `papel_en_uso` | 409 | ConflictError |
| `inmueble_con_contratos`, `inmueble_sin_propietario`, `contrato_con_dependencias`, `registro_referenciado` (1451 genérico) | 409 | ConflictError |
| `catalogo_invalido` (código inexistente en un catálogo; `detalles` indica el campo) | 422 | AppError |

Cuentas inactivas reciben `credenciales_invalidas` (sin filtrar información).

### Piezas web compartidas (se crean en fase 0 y las usan todos los módulos)

| Archivo | Contenido |
| --- | --- |
| `components/Field.tsx` | extraído de `ClienteForm` (props `id,label,value,error,type,maxLength,onChange,required?,list?,inputMode?,autoComplete?,disabled?`) |
| `components/SelectField.tsx`, `components/TextAreaField.tsx` | mismo contrato de accesibilidad (`aria-invalid`, `aria-describedby`) |
| `components/Pagination.tsx` | «Anterior / Siguiente · 1–20 de 57» (`total, limit, offset, onChange`) |
| `hooks/usePagedList.ts` | `{items,total,limit,offset,loading,error,reload,setOffset}` sobre `fetcher(params, signal)`; filtros y `offset` en `useSearchParams` |
| `services/session.ts` | `getToken/setToken/clearToken` (`sessionStorage`, clave `aphia.token`) y `SESSION_EXPIRED_EVENT` |
| `features/shared/validation.ts` | `errorsFromApi<T>(details, campos)` genérico (reemplaza el de clientes) |
| `styles.css` | reescrito con los tokens de la identidad visual (tabla anterior) + `select, textarea`, `.badge-*`, `button.secondary/ghost/danger`, `.pagination`, `.filters`, `.actions`, `.form-grid` (2 col → 1 a 768 px), `.page-header`, `.choices`, `.num`, `@media print` |
| `layouts/MainLayout.tsx` + `components/icons.tsx` | cascarón con barra lateral / riel / cajón según la identidad; en fase 0 con los enlaces actuales, en fases 1–5 se vuelve consciente de roles |

Confirmaciones de borrado con `window.confirm(...)`; sin componente de diálogo.

---

## Fase 0 — Base (commit: «Agrega catálogos base, papeles de persona y columnas de bloqueo (fase 0)»)

### Paso previo: guardar este plan en el repositorio

- Copiar este documento a `docs/plan-de-implementacion.md` (versionado, en español) con una
  tabla de estado al inicio: fase, commit, estado (pendiente / en curso / hecha), fecha.
  Enlazarlo desde `docs/README.md` y mencionarlo en `AGENTS.md` («antes de implementar un
  módulo, lea el plan y sus criterios de aceptación»).
- Al cerrar cada fase se actualiza esa tabla y se anotan las desviaciones respecto al plan en
  una sección «Bitácora de decisiones» al final del documento. Así cualquier sesión futura
  retoma el trabajo desde el repo, sin depender del archivo local de planes.

### Migraciones (`database/migrations/`)

- `0008_catalogos_base.sql` (solo `INSERT`; valores de los que depende la API):
  `app_role` (ADMIN_SISTEMAS, ADMINISTRATIVO, ASESOR); `party_role` (OWNER «Propietario»,
  TENANT «Arrendatario», CO_DEBTOR «Codeudor»); `occupancy_state` (DISPONIBLE, OCUPADO);
  `currency` (COP); `document_type` (`issuer_scope='CO'`: CC, CE, NIT, PAS, TI);
  `agreement_category` (ARRENDAMIENTO, ADMINISTRACION); `bank_account_category` (AHORROS,
  CORRIENTE); `utility_type` (AGUA, ENERGIA, GAS, INTERNET, ASEO). No se crea `ASSOCIATED`.
- `0009_person_party_role.sql`: tabla `person_party_role(person_id, party_role_id)` PK
  compuesta, dos FK `RESTRICT` (`fk_person_party_role_1/2`), índice `ix_person_party_role_fk2`,
  `utf8mb4_0900_bin`.
- `0010_user_account_bloqueo.sql`: `ALTER TABLE user_account ADD COLUMN failed_login_attempts
  INT NOT NULL DEFAULT 0, ADD COLUMN locked_until DATETIME(6) NULL;` (una sentencia).

### Seeds (`database/seeds/`)

- `0002_catalogos_desarrollo.sql`: ids altos (9001…) e idempotentes (`AS nuevos ON DUPLICATE
  KEY UPDATE`): `city` (Bogotá, Medellín, Cali, Barranquilla, Bucaramanga, `country_code='CO'`),
  `financial_institution` (5 bancos), `service_provider` (5 proveedores).
- `0001_clientes_ficticios.sql` se conserva hasta la fase 2.

### API

- `core/config.py`: `AUTH_MODES` += `database`; `auth_secret` (`repr=False`) leído de
  `AUTH_SECRET`; `AUTH_MODE=database` exige secreto ≥ 32 caracteres (`ConfigurationError`).
- `modules/auth/schemas.py`: nuevo `Role`, grupos, `Principal.modo: Literal["development",
  "database"]`. `dependencies.py`: `DEVELOPMENT_PRINCIPAL.roles=[Role.ADMIN_SISTEMAS]`.
- `modules/clientes/router.py`: `require_roles(*LECTURA)` (temporal, se reescribe en fase 2).
- `db/sql.py` (arriba); `clientes/repository.py` usa `mysql_error_code`.
- Nuevo `modules/catalogos/` (`schemas.py`, `repository.py`, `router.py`; sin service):
  `GET /api/v1/catalogos` (LECTURA) → `{tipos_identificacion, papeles, roles, estados_ocupacion,
  tipos_contrato, tipos_cuenta_bancaria, tipos_servicio, monedas: Opcion[]; ciudades:
  {id,nombre}[]; bancos: str[]; proveedores_servicios: str[]}` con `Opcion{codigo, nombre}`.
  `papeles` traduce `OWNER→propietario`, `TENANT→arrendatario`, `CO_DEBTOR→codeudor`
  (constante `PAPEL_POR_CODIGO` en `modules/personas/schemas.py` desde la fase 2; en fase 0
  vive en catálogos). `get_catalogos_repository(db)` para overrides en pruebas. Registrar en
  `main.py`.

### Identidad visual

- `.gitignore`: añadir `DESIGN.md` y `stitch_sistema_aphia_ui_ux/`. Complementar `DESIGN.md`
  con las secciones «Mockups (Google Stitch)», «Aplicación en el código» y «Decisiones» (ver
  sección de identidad). Crear `docs/diseno/README.md` y enlazarlo desde `docs/README.md`.
- `apps/web/package.json`: dependencia `@fontsource-variable/plus-jakarta-sans` (solo
  activos estáticos); `import "@fontsource-variable/plus-jakarta-sans";` en `main.tsx`.
- `styles.css` reescrito con los tokens; `MainLayout` con barra lateral + barra superior /
  riel / cajón, `icons.tsx`, `SlideOver`, `KpiCard`, `Segmented`, `Avatar`. `HomePage`,
  `LoginPage` y `NotFoundPage` adoptan la plantilla de página. Las pruebas existentes
  (`HomePage.test.tsx`, `ProtectedRoute.test.tsx`) siguen buscando por rol y texto visible, así
  que solo cambian si cambia el texto.

### Web

- `types/auth.ts` (`Role`, `modo`), `features/auth/roles.ts`, `/panel` protegido con `LECTURA`.
- Componentes/hooks/CSS de la tabla anterior; `ClienteForm` pasa a usar `Field` y
  `errorsFromApi` genérico sin cambiar comportamiento (`ClienteForm.test.tsx` sigue verde).
- `types/catalogos.ts`, `services/catalogosService.ts` (`getCatalogos()` memorizado +
  `invalidateCatalogos()`), `features/catalogos/useCatalogos.ts`.
- `test/mockApi.ts`: `DEV_PRINCIPAL.roles=["admin_sistemas"]`, fixture `CATALOGOS`.

### Pruebas

- API unit: `tests/fakes.py` (todos los repositorios en memoria; `InMemoryClientesRepository`
  se mueve ahí); `test_auth.py` (nombres de rol; `test_modo_database_exige_auth_secret`;
  `auth_secret` no aparece en `repr`); `test_catalogos.py`; `test_sql_helpers.py`.
- API integración: `test_modelo_3fn.py` → `DATOS_BASE` deja de insertar `document_type`,
  `currency`, `agreement_category`, `party_role` y los toma con subconsultas por código
  (`OWNER` sustituye a `ASSOCIATED`); casos parametrizados reescritos igual; nuevos
  `test_person_party_role_tiene_dos_fk_restrict` y `test_catalogos_base_presentes`.
  `test_catalogos_mysql.py`.
- Web: `Field.test.tsx`, `Pagination.test.tsx`, `usePagedList.test.tsx`; `ProtectedRoute.test.tsx`
  con los roles nuevos; `HomePage.test.tsx` solo cambia `DEV_PRINCIPAL`.
- E2E: sin cambios funcionales (sigue `AUTH_MODE=development` hasta la fase 1).

### Configuración y documentación

- `.env.example` y `apps/api/.dev.vars.example`: `AUTH_SECRET=` (comentario: ≥ 32 caracteres,
  lo genera `pnpm env:init`). `scripts/lib/env.mjs`: `DEV_VARS_FILE`, `DEV_VARS_EXAMPLE`.
  `scripts/env-init.mjs`: `AUTH_SECRET` en `GENERATED`; crea `apps/api/.dev.vars` desde su
  ejemplo con el mismo valor si no existe; si `.env`/`.dev.vars` existen sin `AUTH_SECRET`,
  añade la línea (nunca sobrescribe valores).
- Docs: `AGENTS.md` (roles, `AUTH_MODE=database`, `person_party_role`), `modelo-de-datos.md`
  (sección «Migraciones 0008–0010»; decisiones 1, 2 y 10 marcadas como resueltas;
  `person_category` sin uso), `docs/desarrollo/migraciones.md`, `crear-modulo.md` (grupos de
  roles, `db/sql.py`, `tests/fakes.py`).

---

## Fase 1 — Usuarios y login (commit: «Implementa usuarios, inicio de sesión y bloqueo temporal (fase 1)»)

**Primer paso obligatorio:** con `pnpm --filter @aphia/api dev` comprobar que
`hashlib.pbkdf2_hmac` existe en Pyodide y medir `duration_ms` de `POST /api/v1/auth/login`
en el log. Ver riesgo 1 antes de fijar `PBKDF2_ITERATIONS`.

### `modules/auth`

- `passwords.py`: `PBKDF2_ITERATIONS = 100_000` (ajustable según la medición), sal de 16 bytes
  (`secrets.token_bytes`), `hash_password(clave, iterations=…)`,
  `verify_password(clave, almacenado)` (respeta las iteraciones guardadas; `hmac.compare_digest`;
  cadena malformada → `False`), `DUMMY_HASH` = **literal precalculado** (no se calcula al
  importar: evita CPU en el arranque del Worker) para verificar usuarios inexistentes/inactivos
  con tiempo constante.
- `tokens.py`: `TOKEN_TTL_SECONDS = 8*3600`; `TokenPayload(sub, nombre, roles, exp)`;
  `issue_token(secret, payload)` = `b64url(json compacto) + "." + b64url(hmac_sha256)`;
  `verify_token(secret, token) -> TokenPayload | None` (firma con `compare_digest`, `exp`
  vigente, roles válidos; cualquier excepción → `None`).
- `schemas.py` (+): `LoginRequest{usuario (1..255, strip), clave (1..128, sin strip)}`
  `extra="forbid"`; `LoginResponse{token, expira_en, principal}`.
- `repository.py` `AuthRepository(db)`: `find_for_login(user_name)` (JOIN `person`,
  `GROUP_CONCAT` de códigos de rol; comparación exacta de `user_name`),
  `register_failed_attempt(account_id, max, minutos, now) -> (intentos, locked_until)` en una
  transacción con `SELECT … FOR UPDATE` (si el bloqueo anterior ya venció, reinicia en 1; al
  llegar a `max` fija `locked_until = now + minutos`), `reset_attempts(account_id)`. Fechas
  naive → `tzinfo=UTC`.
- `service.py`: `AuthRepositoryPort`, `MAX_INTENTOS=3`, `MINUTOS_BLOQUEO=15`,
  `CredencialesInvalidasError`, `CuentaBloqueadaError(minutos)`, `AuthService(repo, secret,
  now=…)`. `login`: usuario inexistente → verificación con `DUMMY_HASH` + 401; bloqueada
  vigente → 423 con minutos restantes; inactiva → 401; clave incorrecta → registra intento,
  `log_event(WARNING, "login_failed", account_id, intentos)` y, si se bloquea,
  `log_event(WARNING, "cuenta_bloqueada", account_id, bloqueada_hasta)` + 423; éxito →
  `reset_attempts`, `Principal(sujeto=str(account_id), nombre, roles, modo="database")`,
  token, `log_event(INFO, "login_ok", account_id)`. Nunca se registran usuario, clave ni token.
- `dependencies.py` `get_current_principal`: `development` + local → ficticio; `database` →
  `Authorization: Bearer` verificado con `verify_token` → `Principal`, si no 401 «Inicie sesión
  para continuar.»; otro modo → 401. `get_auth_repository(db)`, `get_auth_service(repo,
  request)`.
- `router.py`: `POST /api/v1/auth/login` (público; 200 / 401 / 423 / 422) y `GET
  /api/v1/auth/me` (solo decodifica el token; los cambios de rol o desactivación aplican en el
  siguiente inicio de sesión o a las 8 h; documentado).

### `modules/usuarios` (`schemas.py`, `repository.py`, `service.py`, `router.py`)

- Schemas (`extra="forbid"`): `UsuarioCreate{usuario (3..50, `^[a-z0-9._-]+$`, minúsculas),
  nombre (2..255), tipo_identificacion (código de `document_type`), identificacion (3..50,
  `^[A-Za-z0-9-]+$`), correo (regex de clientes, minúsculas), clave (8..128, letra y dígito),
  rol: Role}`; `UsuarioUpdate` igual sin `usuario`, con `activo: bool` y `clave: str | None`
  (None = no cambia); `Usuario{id, usuario, nombre, tipo_identificacion, identificacion,
  correo, rol, activo, bloqueada, bloqueada_hasta, intentos_fallidos, creado_en}`;
  `UsuariosPage`.
- Repositorio: lectura con JOIN `person` + primer `person_document` + `document_type` +
  `GROUP_CONCAT` de roles; filtro `q` sobre `user_name` y `full_name` (`ai_ci`); orden
  `user_name`. **Crear:** si ya existe una persona con ese tipo+número de identificación, la
  cuenta se vincula a esa persona (una persona por identificación; un cliente puede pasar a
  ser usuario); si no, `INSERT person` + `person_document`; luego `user_account`
  (`login_email` = correo; 1062 → `usuario_duplicado`) + `user_role`. **Actualizar:** `person`,
  `person_document`, `user_account` (`login_email`, `is_active`, `hashed_password` opcional),
  reemplazo de `user_role`. **Eliminar:** `user_role` + `user_account`; la persona se conserva.
  `count_other_active_admins(account_id)`, `unlock(account_id)`. El hash se calcula en el
  service.
- Service: último `ADMIN_SISTEMAS` activo no se elimina, desactiva ni cambia de rol
  (`ultimo_administrador`); no se puede eliminar ni desactivar la cuenta propia
  (`usuario_actual`); `desbloquear` → `unlock` + `log_event(INFO, "usuario_desbloqueado",
  account_id, por=sujeto)`.
- Router (`require_roles(Role.ADMIN_SISTEMAS)` en todo el router):

| Método | Ruta | Respuestas |
| --- | --- | --- |
| GET | `/api/v1/usuarios?q&limit&offset` | 200 `UsuariosPage` |
| GET | `/api/v1/usuarios/{id}` | 200 / 404 |
| POST | `/api/v1/usuarios` | 201 / 409 `usuario_duplicado` / 422 |
| PUT | `/api/v1/usuarios/{id}` | 200 / 404 / 409 `ultimo_administrador`, `usuario_actual`, `usuario_duplicado` |
| DELETE | `/api/v1/usuarios/{id}` | 204 / 404 / 409 |
| POST | `/api/v1/usuarios/{id}/desbloquear` | 200 `Usuario` / 404 |

### Seed `database/seeds/0003_usuarios_desarrollo.sql`

Personas 9001–9003 con documentos `900000001…`, cuentas `admin`, `administrativo`, `asesor`
(`login_email` `<usuario>@example.test`), hash precalculado de `Aphia.2026` (generar una vez con
`uv run python -c "…hash_password('Aphia.2026')"` y pegar), `ON DUPLICATE KEY UPDATE` que
además desbloquea y reactiva; `user_role` con `INSERT IGNORE … SELECT role_id FROM app_role
WHERE code=…`. Contraseña documentada como exclusiva de desarrollo.

### Web

- `services/authService.ts`: `login(usuario, clave)`, `getCurrentPrincipal(signal)`.
- `services/apiClient.ts`: añade `Authorization: Bearer` si hay token; ante 401 en cualquier
  ruta distinta de `/api/v1/auth/login` → `clearToken()` + `dispatchEvent(SESSION_EXPIRED_EVENT)`
  y lanza `ApiError` como hoy.
- `features/auth/AuthProvider.tsx`: `{status, principal, login, logout, tiene(roles)}`; sin
  token → `anonimo` sin llamar a la API; con token → `/me`; escucha `SESSION_EXPIRED_EVENT`.
- `pages/LoginPage.tsx` según el mockup de login (ver inventario): formulario real
  (`autoComplete` username/current-password, botón mostrar/ocultar contraseña, «Recordarme» →
  `localStorage`); éxito → `navigate(state.from ?? "/")`; 401 → «Usuario o contraseña
  incorrectos.»; 423 → mensaje de la API con minutos; autenticado → `<Navigate to="/" />`.
- Módulo `resumen` (`modules/resumen/{schemas,repository,router}.py`, `GET /api/v1/resumen`,
  LECTURA): en esta fase devuelve `usuarios: {total, activos, bloqueados}` y ceros en los demás
  bloques; los repositorios de las fases 2–4 lo completan. `features/resumen/useResumen.ts`.
- `pages/HomePage.tsx` según el mockup del tablero: saludo con nombre y fecha, KPI desde
  `resumen`, rejilla de tarjetas de módulo con conteos (enlaces según rol), lista «Contratos que
  vencen pronto» (fase 4; hasta entonces oculta).
- `layouts/MainLayout.tsx`: navegación de la barra lateral según `useAuth()` (Inicio; módulos
  de negocio en fases 2–4; Usuarios solo `GESTION_USUARIOS`; Ayuda en fase 5); bloque de
  usuario al pie de la barra con nombre, rol y «Cerrar sesión» / «Iniciar sesión». La pantalla
  de login sigue el mockup de Stitch (tarjeta centrada sobre el lienzo `#F8FAFC`, marca,
  formulario, mensajes).
- Anónimo en `/` → tarjeta «Inicie sesión para continuar». La tarjeta demo de clientes se
  mantiene **solo** para usuarios autenticados hasta la fase 2 (así `clientes.spec.ts` sigue
  válido). Se elimina `/panel` y `PanelPage`.
- Usuarios según los dos mockups de usuarios: `types/usuario.ts`, `services/usuariosService.ts`
  (`listUsuarios({q, rol, estado, limit, offset})`), `features/usuarios/{useUsuarios,
  UsuarioForm, UsuariosTable, validation}`, `pages/UsuariosPage.tsx` (`/usuarios`: banner del
  protocolo de bloqueo, KPI, una alerta por cuenta bloqueada con «Desbloquear», buscador +
  chips de rol + estado, tabla con avatar, `@usuario`, documento, correo, insignia de rol,
  conmutador Activo/Inactivo (`PUT` con `activo`), columna Seguridad («N fallos» /
  «Bloqueada» + «Desbloquear»), editar/eliminar con confirmación; tarjetas «Roles y alcance» y
  «Seguridad») y `UsuarioForm` en `SlideOver` (`/usuarios/nuevo`, `/usuarios/:id/editar`).
  La API acepta `rol` y `estado` (`activo|inactivo|bloqueado`) como filtros del listado. Rutas
  bajo `ProtectedRoute roles={GESTION_USUARIOS}`.
- `test/mockApi.ts`: `LOGIN_OK`, `DB_PRINCIPAL`, fixture `usuario()`.

### Pruebas

- API unit: `test_passwords.py`, `test_tokens.py` (ida y vuelta, cuerpo/firma manipulados,
  expirado, otro secreto, nombre no ASCII), `test_auth.py` (+login ok, `/me` con y sin token,
  clave incorrecta, usuario inexistente, 3 intentos → 423, bloqueada con clave correcta → 423,
  tras vencer el bloqueo → 200 e intentos en 0, inactiva → 401, campo extra → 422),
  `test_usuarios.py` (CRUD, validaciones sin eco de la clave, duplicados, último admin, cuenta
  propia, desbloquear, 403 para administrativo/asesor, 401 sin token),
  `test_errores_y_seguridad.py` (+logs de login sin usuario ni clave). Fakes con
  `hash_password(..., iterations=1_000)`.
- API integración: `tests/integration/conftest.py` → variante `settings_for(params,
  auth_mode="database", auth_secret=…)` y limpieza ordenada (`user_role, user_account,
  person_email, person_phone, person_document, person, clientes`). `test_auth_mysql.py`
  (3 fallos persisten `failed_login_attempts=3` y `locked_until`; desbloquear los limpia),
  `test_usuarios_mysql.py` (crear vía API deja filas en `person`, `person_document`,
  `user_account`, `user_role`; crear con identificación de una persona existente la reutiliza).
- Web: `LoginPage.test.tsx`, `AuthProvider.test.tsx`, `apiClient.test.ts` (+Bearer, 401 limpia
  token, 401 de login no dispara evento), `MainLayout.test.tsx`, `UsuariosPage.test.tsx`,
  `UsuarioForm.test.tsx`, `ProtectedRoute.test.tsx` (`/usuarios` negado a asesor),
  `HomePage.test.tsx`.
- E2E: `tests/e2e/helpers.ts` → `iniciarSesion(page, usuario="admin", clave="Aphia.2026")`
  (login por `page.request` + `addInitScript` que guarda el token en `sessionStorage`);
  `auth.spec.ts` (login UI, logout, clave incorrecta, flujo de bloqueo y desbloqueo, asesor sin
  enlace «Usuarios» y 403 en la API); `usuarios.spec.ts` (crear, editar rol, eliminar);
  `clientes.spec.ts` con `beforeEach(iniciarSesion)` y sin la prueba de `/panel`.

### Configuración, CI y documentación

- `apps/api/wrangler.jsonc`: `AUTH_MODE: "database"` en local, staging y producción; secreto
  con `uv run pywrangler secret put AUTH_SECRET --env …`. `.env.example`: `AUTH_MODE=database`.
- `package.json`: `test:e2e` añade `pnpm db:seed` tras `db:migrate`. `ci.yml` (job e2e): paso
  `pnpm db:seed` y creación de `apps/api/.dev.vars` con un `AUTH_SECRET` generado en el momento.
- Docs: `docs/seguridad/README.md` (sustituye «No existe autenticación de producción» y la
  propuesta de Cloudflare Access por el diseño real: PBKDF2, token HMAC 8 h, política 3/15 min,
  matriz de roles, límites: cambios de rol aplican al siguiente login, rotar `AUTH_SECRET`
  cierra todas las sesiones; medición de `duration_ms`), `docs/despliegue/cloudflare-workers.md`
  (secreto), `README.md` (usuarios de desarrollo y `AUTH_SECRET`), `docs/requisitos/README.md`
  (roles definitivos), `docs/pruebas/README.md`, `modelo-de-datos.md` (formato de
  `hashed_password` resuelto), `AGENTS.md` («`development` solo para pruebas unitarias»).

---

## Fase 2 — Clientes, propietarios y codeudores sobre `person` (commit: «Implementa clientes, propietarios y codeudores sobre el modelo de personas (fase 2)»)

### Archivos

- Nuevo módulo compartido `apps/api/src/modules/personas/{schemas,repository,service,router}.py`.
- `modules/clientes/router.py` reescrito (fábrica); se eliminan `clientes/{schemas,service,repository}.py`.
- Nuevos `modules/propietarios/router.py` y `modules/codeudores/{__init__,router}.py`.
- `main.py` incluye `personas_router` (búsqueda), `clientes_router`, `propietarios_router`, `codeudores_router`.

### Schemas (`personas/schemas.py`)

- `Papel = Literal["propietario","arrendatario","codeudor"]`; `PAPEL_A_CODIGO`
  (`OWNER/TENANT/CO_DEBTOR`) y su inverso.
- `CuentaBancariaCreate{banco (1..255), tipo (código de `bank_account_category`), numero (1..50,
  `^[0-9-]+$`)}`, `CuentaBancaria(+id)`.
- `PersonaBase` (`extra="forbid"`, strip): `nombre (2..255, sin caracteres de control, espacios
  colapsados)`, `tipo_identificacion` (código de `document_type`), `identificacion (3..50,
  `^[A-Za-z0-9-]+$`)`, `telefono: str | None (7..50, `^[0-9+ ()-]+$`)`, `correo: str | None`
  (regex actual, minúsculas), `direccion: str | None (..255)`.
- `PersonaCreate(PersonaBase)`: `papeles: list[Papel]` (mín. 1, sin duplicados),
  `cuenta_bancaria: CuentaBancariaCreate | None`. `PersonaUpdate = PersonaCreate`.
- `PersonaResumen{id, nombre, tipo_identificacion, identificacion, telefono, correo}` (pickers y
  anidados); `Persona(PersonaBase){id, papeles, cuenta_bancaria}`.
- `InmuebleResumen{id, direccion, ciudad, estado}`, `ContratoResumen{id, tipo, fecha_inicio,
  fecha_fin, inmueble}` (definidos aquí para no importar módulos posteriores).
- `PersonaDetalle(Persona){inmuebles, contratos_como_propietario, contratos_como_arrendatario,
  contratos_como_codeudor, usuario: str | None}`; `PersonasPage`; dataclass
  `PersonaFiltros{q, correo, papel, contrato_id, solo_con_papel}`.

### Repositorio (`personas/repository.py`)

- `_SELECT` único: `person` + primer `person_document` (+`document_type`) + primer
  `person_phone` + primer `person_email` + primera `bank_account` (+categoría +
  `financial_institution`) con el idioma `MIN(id)`; `papeles` con `GROUP_CONCAT` de códigos de
  `party_role` vía `person_party_role`.
- Filtros como lista `(sql, params)` compartida por la página y el `COUNT(*)`:
  `solo_con_papel` → `EXISTS person_party_role`; `papel` → `EXISTS … pr.code=%s`; `q` →
  `(full_name ai_ci LIKE %s OR document_identifier LIKE %s)`; `correo` → `email ai_ci LIKE %s`;
  `contrato_id` → `EXISTS agreement_party … agreement_id=%s AND pr.code='CO_DEBTOR'`. Orden
  `person_id DESC`.
- Métodos: `listar`, `obtener`, `buscar_por_identificacion(tipo, numero)` (exacta),
  `crear(datos, papeles)` (transacción: `person` → `person_document` (`INSERT…SELECT` por
  código; rowcount 0 → `catalogo_invalido`; 1062 → `identificacion_duplicada`) → teléfono →
  correo → `INSERT IGNORE person_party_role` por papel → banco *buscar o crear* + `bank_account`
  → relectura), `actualizar(id, datos, papeles)` (UPDATE `person` (rowcount 0 → None);
  UPDATE/INSERT del documento usando tabla derivada para evitar el error 1093; borrar y
  reinsertar teléfono, correo y cuenta; `INSERT IGNORE` de papeles pedidos y `DELETE … NOT IN
  (placeholders)` de los quitados), `contar_dependencias(id) -> Dependencias{inmuebles,
  contratos, usuarios, por_papel}` (una consulta con subconsultas), `eliminar(id)` (hijas y
  `person`; 1451 → `persona_con_dependencias`), `detalle(id)` (`_SELECT` + inmuebles por
  `property_owner` + contratos por `agreement_party` con el código de papel, repartidos en
  Python en las tres listas + `user_name`).

### Service (`personas/service.py`)

`PersonasRepositoryPort`; `PersonasService`: `listar`, `obtener` (404), `buscar` (404),
`crear(datos, papel_fijo)` (añade el papel del router), `actualizar(id, datos, papel_fijo)`
(papeles quitados con dependencias → `papel_en_uso`), `eliminar(id)` (con dependencias → 409
`persona_con_dependencias` «No se puede eliminar: es propietaria de N inmueble(s), participa en
N contrato(s), tiene una cuenta de usuario.»; cubre «eliminar propietario excepto si tiene
inmuebles»).

### Routers

`personas/router.py`: `get_personas_repository(db)`, `get_personas_service(repo)` y
`build_personas_router(prefix, tag, papel: Papel | None)`:

| Método | Ruta (P = prefijo) | Roles | Respuestas |
| --- | --- | --- | --- |
| GET | `P?q&correo&contrato_id&papel&limit&offset` | LECTURA | 200 `PersonasPage` (propietarios/codeudores fijan `papel`; clientes usa `solo_con_papel=True` y acepta `?papel=` para los segmentos; las filas incluyen `inmuebles: int` para el chip de propietarios) |
| GET | `P/{id}` | LECTURA | 200 `PersonaDetalle` / 404 |
| POST | `P` | ESCRITURA | 201 `Persona` / 409 `identificacion_duplicada` / 422 |
| PUT | `P/{id}` | ESCRITURA | 200 / 404 / 409 `identificacion_duplicada`, `papel_en_uso` / 422 |
| DELETE | `P/{id}` | ELIMINACION | 204 / 404 / 409 `persona_con_dependencias` |

Además `GET /api/v1/personas/buscar?tipo_identificacion&identificacion` (LECTURA; 200
`Persona` / 404 / 422) para el selector. Routers delgados:
`clientes` = `build_personas_router("/api/v1/clientes", "clientes", None)`;
`propietarios` = `(…, "propietario")`; `codeudores` = `(…, "codeudor")`. `GET /clientes` lista
personas con al menos un papel; `/propietarios` solo OWNER; `/codeudores` solo CO_DEBTOR, con
`?contrato_id` (por contrato) y `?q=<identificación>`.

### Seeds

- Se elimina `0001_clientes_ficticios.sql`.
- `0004_personas_desarrollo.sql`: personas 9101–9106 (una propietaria, un arrendatario, uno
  propietario **y** codeudor, una arrendataria, dos codeudores), documentos CC `9101…`,
  teléfonos, correos `persona9101@example.test`, `person_party_role` con `INSERT IGNORE …
  SELECT`, `bank_account` 9101 (AHORROS, institución 9001). Idempotentes.

### Web

- `types/persona.ts`, `services/personasService.ts` (`listPersonas(api, params, signal)`,
  `getPersona`, `createPersona`, `updatePersona`, `deletePersona`, `buscarPersona(tipo, numero)`).
- `features/personas/modulos.ts`: `MODULOS = {clientes, propietarios, codeudores}` con
  `titulo, singular, ruta, api, papelFijo, filtros`.
- `features/personas/usePersonas.ts(modulo)` (sobre `usePagedList`, filtros en URL, acciones
  crear/actualizar/eliminar + `reload`).
- `PersonaForm.tsx` (`modo`, `modulo`, `inicial?`, `onSubmit`): nombre, tipo y número de
  identificación, teléfono, correo, dirección; **papeles**: al crear sin papel fijo un
  `SelectField` «Tipo de cliente» (uno); al editar casillas «Papeles» (el fijo marcado y
  deshabilitado); sección «Cuenta bancaria (opcional)» (banco con `datalist` de
  `catalogos.bancos`, tipo, número). Errores de API vía `errorsFromApi` (incluye
  `cuenta_bancaria.*`).
- `PersonasTable.tsx` (Identificación, Nombre, Teléfono, Correo, Papeles como `badge`,
  acciones Ver/Editar/Eliminar según `tiene(...)`).
- `PersonaPicker.tsx` (reutilizado por inmuebles y contratos): tipo + identificación + «Buscar»
  → encontrada: «Seleccionar»; 404: «Registrar nueva persona» (formulario mínimo nombre,
  teléfono, correo → `createPersona` con `papeles:[papel]`), oculto con `soloBuscar`; valor
  elegido como chip con «Cambiar». `PersonaListPicker.tsx` para listas (propietarios,
  codeudores) con «Quitar».
- Páginas parametrizadas por `modulo`, según los mockups de clientes y propietarios:
  `PersonasListPage` (`/clientes`, `/propietarios`, `/codeudores`: cabecera con icono, chip de
  total y «Registrar <singular>»; banner de regla en propietarios; KPI desde `resumen`;
  buscador + segmentos de papel (solo clientes) + filtro `correo` (propietarios) +
  `contrato_id` (codeudores); tabla con avatar de iniciales, nombre + correo, identificación,
  teléfono, insignias de papel, y en propietarios cuenta bancaria enmascarada y chip «N
  inmuebles»; paginación con tamaño de página), `PersonaForm` en `SlideOver` (`/…/nuevo`,
  `/…/:id/editar`), `PersonaDetallePage` (`/…/:id`: Datos, Papeles, Cuenta bancaria, Usuario
  del sistema, Inmuebles, Contratos como arrendatario/codeudor/propietario; enlaces a fases 3
  y 4). `resumen.personas` se completa en esta fase.
- Rutas bajo `ProtectedRoute roles={LECTURA}`; enlaces Clientes/Propietarios/Codeudores en el
  menú. Se eliminan `features/clientes/*`, `types/cliente.ts`, `services/clientesService.ts`,
  la tarjeta demo de `HomePage` y `mockApi.cliente()` (nuevo `persona()`).

### Pruebas

- API unit `test_personas.py` (fake `InMemoryPersonasRepository` con dependencias
  configurables; `conftest.app` sobreescribe `get_personas_repository`): crear y listar,
  identificación duplicada 409, validaciones parametrizadas (tipo inexistente, identificación
  con espacios, correo, teléfono con letras, `papeles: []`, nombre con `\x00`, campo extra,
  cuenta inválida) sin eco de valores, `POST /propietarios` y `/codeudores` añaden su papel,
  filtros (`q`, `correo`, `contrato_id`, propietarios solo OWNER, clientes excluye personas sin
  papel), quitar papel en uso 409, eliminar con inmuebles/usuario 409, eliminar como asesor
  403, 204 y luego 404, buscar 200/404/422, detalle con relaciones, paginación (movida de
  `test_clientes.py`, que se elimina). `test_errores_y_seguridad.py` pasa a sobreescribir
  `get_personas_repository`.
- API integración `test_personas_mysql.py` (limpieza ordenada en `conftest`: `file_agreement,
  file_person, file_property, file_record, financial_record, agreement_party,
  property_agreement, property_utility, property_owner, property, bank_account,
  person_party_role, user_role, user_account, person_email, person_phone, person_document,
  person, city, service_provider, financial_institution, clientes`): crear persiste en las
  tablas hijas y crea el banco una sola vez; `q` ignora mayúsculas y acentos; duplicado no deja
  filas parciales; actualizar deja un teléfono y un correo; eliminar borra hijas; propietario
  con inmueble → 409; detalle reparte contratos por papel; búsqueda exacta. Se mueven aquí las
  pruebas genéricas de `test_clientes_mysql.py` (persistencia entre instancias, transacción
  fallida, migraciones idempotentes, ready).
- Web: `PersonaForm.test.tsx`, `PersonaPicker.test.tsx` (encontrada / 404 → registro inline con
  `papeles:["propietario"]` / `soloBuscar`), `PersonasListPage.test.tsx` (filtro → `?q=`;
  asesor sin «Eliminar»; borrado con confirmación; 409 en `role="alert"`),
  `PersonaDetallePage.test.tsx`, `HomePage.test.tsx` reescrito. Se elimina `ClienteForm.test.tsx`.
- E2E (con `iniciarSesion`): `clientes.spec.ts` reescrito (crear con «Tipo de cliente =
  Arrendatario», fila visible en < 2 s tras el POST, filtrar por identificación, editar,
  detalle, eliminar; asesor sin «Eliminar»), `propietarios.spec.ts` (cuenta bancaria, filtro por
  correo), `codeudores.spec.ts` (crear, buscar por identificación).

### Docs

`modelo-de-datos.md` (pasos 1–2 de la tabla demo hechos; «una fila hija por campo del
formulario»; semántica de `person_party_role` y papeles automáticos), `crear-modulo.md`
(módulo de referencia `personas`, fábrica de routers, fakes), `docs/requisitos/README.md`
(Clientes/Propietarios/Codeudores → Implementado), `docs/pruebas/README.md`, `README.md`
(seeds), `AGENTS.md` (lista de módulos).

---

## Fase 3 — Inmuebles (commit: «Implementa inmuebles y elimina la tabla de demostración (fase 3)»)

### Migración

`0011_eliminar_tabla_clientes.sql`: `DROP TABLE IF EXISTS clientes;` (segundo paso del cambio
destructivo; la tabla no se usa desde la fase 2). Quitar `clientes` de la limpieza de
integración.

### API `modules/inmuebles/{schemas,repository,service,router}.py`

- Schemas: `ServicioPublicoCreate{tipo: str | None (código de `utility_type`), proveedor: str |
  None, numero_contrato (1..255)}`, `ServicioPublico(+id)`; `InmuebleCreate` (`extra="forbid"`):
  `direccion (3..255)`, `ciudad: str | None`, `matricula: str | None`, `canon: Decimal | None
  (ge=0, 12 dígitos, 2 decimales)`, `estado: str | None` (código de `occupancy_state`),
  `servicios: list[ServicioPublicoCreate]` (máx. 20), `propietarios_ids: list[int]` (mín. 1,
  sin duplicados); `InmuebleUpdate = InmuebleCreate`; `Inmueble{id, direccion, ciudad,
  matricula, canon (cadena JSON), moneda ("COP" si hay canon), estado, servicios,
  propietarios: list[PersonaResumen]}`; `InmueblesPage`; `InmuebleFiltros{estado, ciudad,
  propietario_id, q}`.
- Repositorio: `_SELECT` de `property` + `city` + `occupancy_state`; filtros `estado`
  (`os.code=%s`), `ciudad` (`c.name ai_ci LIKE`), `propietario_id` (`EXISTS property_owner`),
  `q` (dirección o matrícula); tras cargar la página, dos consultas por lote `IN (…)` para
  propietarios (resumen de persona con el idioma `MIN`) y servicios, agrupadas en Python.
  `crear` (transacción: ciudad *buscar o crear* (`name` + `country_code='CO'`) → `INSERT
  property` con `currency_code='COP'` solo si hay canon (cumple `ck_property_rental_currency`)
  y estado por subconsulta → `property_owner` por id (1452 → `persona_no_encontrada`) +
  `INSERT IGNORE person_party_role OWNER` (papel automático) → servicios con proveedor
  *buscar o crear* → relectura). `actualizar` (UPDATE; diff de propietarios con `DELETE … NOT
  IN` + `INSERT IGNORE` + papel OWNER; servicios borrar y reinsertar). Quitar un propietario
  **no** quita su papel (se quita a mano desde el cliente, bloqueado mientras posea algo).
  `contar_contratos(id)`; `eliminar(id)` (`property_utility`, `property_owner`, `property`;
  1451 → `registro_referenciado`).
- Service: `listar`, `obtener` (404 `inmueble_no_encontrado`), `crear`, `actualizar`,
  `eliminar` (contratos > 0 → 409 `inmueble_con_contratos` «…tiene N contrato(s). Elimine
  primero los contratos.»). `RegistroReferenciadoError` vive en `core/errors.py` (lo usan varios
  módulos).
- Router `prefix="/api/v1/inmuebles"`:

| Método | Ruta | Roles | Respuestas |
| --- | --- | --- | --- |
| GET | `/?estado&ciudad&propietario_id&q&limit&offset` | LECTURA | 200 `InmueblesPage` |
| GET | `/{id}` | LECTURA | 200 / 404 |
| POST | `/` | ESCRITURA | 201 / 404 `persona_no_encontrada` / 422 |
| PUT | `/{id}` | ESCRITURA | 200 / 404 / 422 |
| DELETE | `/{id}` | ELIMINACION | 204 / 404 / 409 `inmueble_con_contratos`, `registro_referenciado` |

### Seed `0005_inmuebles_desarrollo.sql`

`property` 9201 (Bogotá, matrícula `50C-9201`, canon 1 500 000 COP, DISPONIBLE), 9202
(Medellín, OCUPADO), 9203 (sin canon ni moneda); `property_owner` (9201→9101, 9202→9101,
9202→9103 copropiedad, 9203→9103) con `INSERT IGNORE`; `property_utility` 9201–9204 con
proveedores 9001/9002 y tipos por subconsulta.

### Web

- `types/inmueble.ts` (`canon: string | null`), `services/inmueblesService.ts`,
  `features/inmuebles/{useInmuebles, InmuebleForm, InmueblesTable, ServiciosEditor, validation}`.
- `InmuebleForm` en `SlideOver` («Registrar nuevo inmueble», según el mockup) con secciones
  numeradas: 1 Identificación y localización (dirección, ciudad con `datalist`, matrícula);
  2 Canon y titularidad (`PersonaListPicker papel="propietario"` mín. 1, canon
  `inputMode="decimal"` `^\d{1,10}([.,]\d{1,2})?$` normalizado a `.`, estado como botones de
  radio Disponible/Ocupado); 3 Cuentas de servicios públicos (`ServiciosEditor`: tipo,
  proveedor con `datalist`, número; Quitar/Agregar). Pie «Cancelar» / «Guardar inmueble». Tras
  guardar, `invalidateCatalogos()`.
- `InmueblesTable` según el mockup: Matrícula, Inmueble (dirección + ciudad), Propietarios
  (enlaces a `/propietarios/:id`), Canon mensual (COP, tabular, `Intl.NumberFormat("es-CO")`),
  Estado (punto + insignia), Servicios (chips tipo–número), acciones Editar / «Ver contratos»
  (`/contratos?inmueble_id=`) / Eliminar.
- `pages/InmueblesPage.tsx` (`/inmuebles`: migas, cabecera, KPI Total/Ocupados/Disponibles,
  filtros estado, ciudad, propietario con `PersonaPicker soloBuscar` → `propietario_id` en URL,
  `q`, chips de filtros aplicados + «Restablecer»); rutas hijas `/inmuebles/nuevo` y
  `/inmuebles/:id/editar` abren el panel sobre la lista. Enlace «Inmuebles» en el menú y «+
  Nuevo inmueble» de la barra superior. `resumen.inmuebles` se completa en esta fase.

### Pruebas

- API unit `test_inmuebles.py`: crear con dos propietarios y servicios (moneda COP), sin canon
  sin moneda, 422 parametrizados (canon negativo o con 3 decimales, sin propietarios, estado
  inexistente, servicio sin número, campo extra, dirección corta), propietario inexistente 404,
  filtros, actualizar reemplaza servicios/propietarios, eliminar con contratos 409 (mensaje con
  N), asesor 403, 204, 404.
- API integración `test_inmuebles_mysql.py`: la ciudad se crea una sola vez (y una grafía
  distinta crea otra: regla de nombre exacto documentada), canon→COP y sin canon→NULL,
  propietario recibe papel OWNER y aparece en `/propietarios`, eliminar bloqueado por contrato
  (insertado por SQL) y permitido tras borrarlo, detalle de propietario lista el inmueble;
  `test_migraciones_mysql.py` + «tabla `clientes` eliminada».
- Web: `InmuebleForm.test.tsx` (normalización de canon, propietario obligatorio, servicios,
  404 de persona), `InmueblesPage.test.tsx` (filtros → query, 409, asesor), `ServiciosEditor.test.tsx`.
- E2E `inmuebles.spec.ts` (propietario registrado inline desde el selector, filtros por estado y
  ciudad, editar canon y verlo formateado en < 2 s, eliminar); `propietarios.spec.ts` +
  «no se puede eliminar un propietario con inmuebles» y «el propietario inscrito desde el
  inmueble aparece en Propietarios».

### Docs

`modelo-de-datos.md` (0011; regla *buscar o crear*; papel OWNER nunca se quita solo),
`docs/requisitos/README.md` (Inmuebles → Implementado), `docs/pruebas/README.md`, `README.md`,
borrador de la sección «Inmuebles» de `docs/manual-usuario.md`.

---

## Fase 4 — Contratos (commit: «Implementa contratos con partes, filtros e impresión (fase 4)»)

### API `modules/contratos/{schemas,repository,service,router}.py`

- Schemas: `ContratoCreate` (`extra="forbid"`): `tipo` (código de `agreement_category`),
  `inmueble_id`, `fecha_inicio: date`, `fecha_fin: date | None`, `canon_pactado: Decimal | None
  (ge=0, 12/2)`, `condiciones: str | None (..20000)`, `texto: str | None (..1_000_000; solo
  `\n \r \t` como caracteres de control)`, `propietarios_ids: list[int] | None` (None = los
  `property_owner` actuales del inmueble; `[]` rechazado), `arrendatario_id: int | None`,
  `codeudores_ids: list[int]` (máx. 10). Validadores: `fecha_fin >= fecha_inicio`, el
  arrendatario no está entre los codeudores, listas sin duplicados. `ContratoUpdate` igual con
  `propietarios_ids` obligatorio. `ContratoListado{id, tipo, inmueble: InmuebleResumen,
  fecha_inicio, fecha_fin, canon_pactado, moneda, arrendatario: PersonaResumen | None,
  propietarios, codeudores}`; `Contrato(+condiciones, texto)`; `ContratosPage`;
  `ContratoFiltros{fecha_desde, fecha_hasta, inmueble_id, propietario_id, inquilino_id, tipo}`.
- Repositorio: `_SELECT` de `property_agreement` + `agreement_category` + `property` + `city`
  + `occupancy_state` (el listado omite `agreement_content`/`conditions`). Filtros:
  `fecha_desde` → `(end_date IS NULL OR end_date >= %s)`; `fecha_hasta` → `start_date <= %s`
  (juntos = solapamiento de vigencias); `inmueble_id`; `propietario_id` / `inquilino_id` →
  `EXISTS agreement_party … pr.code='OWNER'|'TENANT'`; `tipo`; `estado`
  (`vigente`: `start_date <= CURDATE() AND (end_date IS NULL OR end_date >= CURDATE())`;
  `por_vencer`: `end_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 60 DAY`; `finalizado`:
  `end_date < CURDATE()`); `q` (dirección del inmueble o nombre de una parte). El listado
  incluye `estado` calculado y `dias_restantes`. Orden `start_date DESC,
  agreement_id DESC` (usa `ix_agreement_property_dates`). Partes de la página en una consulta
  por lote (`IN (…)`) con el resumen de persona, repartidas en Python por código de papel.
  `propietarios_del_inmueble(inmueble_id) -> list[int] | None`. `crear` (transacción: `INSERT
  property_agreement` con categoría por subconsulta y `currency_code='COP'` solo si hay canon;
  `_insertar_partes` para OWNER, TENANT (opcional) y CO_DEBTOR con `INSERT … SELECT
  party_role_id` (1452 → `persona_no_encontrada`) + `INSERT IGNORE person_party_role` del mismo
  código (papel automático); relectura). `actualizar` (UPDATE; borrar y reinsertar partes).
  `contar_dependencias(id) -> (registros_financieros, archivos)`. `eliminar` (`agreement_party`
  + `property_agreement`; 1451 → `registro_referenciado`). El estado de ocupación **no** se
  cambia automáticamente (nota del modelo 3FN); la UI recuerda actualizarlo.
- Service: `crear` (propietarios = los pedidos o los del inmueble; inmueble inexistente → 404;
  sin propietarios → 409 `inmueble_sin_propietario`), `actualizar`/`eliminar` (dependencias > 0
  → 409 `contrato_con_dependencias`), `listar`, `obtener` (404).
- Router `prefix="/api/v1/contratos"`:

| Método | Ruta | Roles | Respuestas |
| --- | --- | --- | --- |
| GET | `/?fecha_desde&fecha_hasta&inmueble_id&propietario_id&inquilino_id&tipo&estado&q&limit&offset` | LECTURA | 200 `ContratosPage` (sin texto) / 422 |
| GET | `/{id}` | LECTURA | 200 `Contrato` / 404 |
| POST | `/` | ESCRITURA | 201 / 404 `inmueble_no_encontrado`, `persona_no_encontrada` / 409 `inmueble_sin_propietario` / 422 |
| PUT | `/{id}` | ESCRITURA | 200 / 404 / 409 `contrato_con_dependencias` / 422 |
| DELETE | `/{id}` | ELIMINACION | 204 / 404 / 409 `contrato_con_dependencias`, `registro_referenciado` |

Codeudores: «asociar varios» = `codeudores_ids`; «consultar por contrato» = `GET
/api/v1/codeudores?contrato_id=` (fase 2) y el detalle del contrato.

Búsqueda global de la barra superior: módulo `buscar` (`GET /api/v1/buscar?q=` LECTURA, 2–100
caracteres) → `{personas: PersonaResumen[≤5], inmuebles: InmuebleResumen[≤5], contratos:
ContratoResumen[≤5]}` con tres consultas `LIKE … ai_ci` (nombre/identificación; dirección/
matrícula; dirección del inmueble o nombre de parte). `components/BusquedaGlobal.tsx`: caja en
la barra superior, resultados en lista desplegable agrupada (`role="listbox"`), Enter abre el
primero, Escape cierra; navega a `/clientes/:id`, `/inmuebles/:id/editar`, `/contratos/:id`.
`resumen.contratos` se completa en esta fase.

### Seed `0006_contratos_desarrollo.sql`

`property_agreement` 9301 (ARRENDAMIENTO, inmueble 9202, 2026-01-01 → 2026-12-31, 1 500 000
COP, condiciones y texto ficticio **de una sola línea** sin `;` final ni `--` inicial) y 9302
(ADMINISTRACION, inmueble 9203, abierto, sin canon); `agreement_party` con `INSERT IGNORE …
SELECT … FROM party_role WHERE code=…` (9301: propietarios 9101 y 9103, arrendatario 9102,
codeudores 9105 y 9106; 9302: propietario 9103, arrendataria 9104, codeudor 9105) y los
`person_party_role` correspondientes.

### Web

- `types/contrato.ts`, `services/contratosService.ts`, `features/contratos/{useContratos,
  InmueblePicker, ContratoForm, ContratosTable, validation}`.
- `InmueblePicker` (buscar por dirección o matrícula con `listInmuebles({q, limit: 20})`, lista
  con «Seleccionar», chip con «Cambiar», modo `soloBuscar` para filtros).
- `ContratoForm`: tipo (`catalogos.tipos_contrato`), `InmueblePicker` (al elegir, precarga
  «Propietarios» con los dueños del inmueble), fechas `type="date"`, canon pactado,
  `PersonaListPicker papel="propietario"` (mín. 1), `PersonaPicker papel="arrendatario"`
  (opcional, «Sin arrendatario»), `PersonaListPicker papel="codeudor"`, `TextAreaField`
  condiciones y «Texto completo del contrato (para impresión)». Validación local de fechas y
  arrendatario≠codeudor. Al guardar: «Contrato guardado. Recuerde actualizar el estado de
  ocupación del inmueble si corresponde.» y navegar al detalle.
- `ContratosTable`: Tipo, Inmueble, Inicio, Fin («Indefinido»), Canon, Arrendatario,
  Codeudores (número), acciones Ver/Editar/Eliminar.
- `pages/ContratosPage.tsx` según el mockup (`/contratos`: migas, cabecera con «Nuevo
  contrato», banner rojo de la regla de dependencias, KPI desde `resumen`, pestañas de
  `estado` (`Segmented`), buscador `q`, fecha desde/hasta, tipo, inmueble (`InmueblePicker
  soloBuscar`, acepta `?inmueble_id=` desde Inmuebles), propietario e inquilino (`PersonaPicker
  soloBuscar`); tabla con nº y vigencia + «N días restantes», inmueble, partes, chips de
  codeudores, canon, insignia de estado), `pages/ContratoFormPage.tsx` (página completa; 409 con
  dependencias → alerta y formulario deshabilitado), `pages/ContratoDetallePage.tsx`
  (`/contratos/:id`: botones Editar / Eliminar / **«Imprimir / guardar PDF»** (`window.print()`,
  deshabilitado sin texto); tarjetas Datos y Condiciones; sección Codeudores con «Asociar
  codeudor» (`PersonaPicker papel="codeudor"` → `PUT` con la lista ampliada) y «Quitar»;
  `<section class="contrato-impresion">` con cabecera (APHIA S.A.S., tipo, inmueble, fechas,
  partes) y `<pre class="contrato-texto">`).
- `styles.css`: `@media print` oculta cabecera, pie, menú y acciones, quita bordes y
  márgenes; `.contrato-texto { white-space: pre-wrap; line-height: 1.6 }`; `@page { margin: 2cm }`.
- Rutas bajo LECTURA; enlace «Contratos»; se resuelven los enlaces pendientes de
  `PersonaDetallePage` e `InmueblesTable`.

### Pruebas

- API unit `test_contratos.py` (fake con inmuebles→dueños, personas y dependencias): toma
  propietarios del inmueble / explícitos, arrendatario + codeudores (fake registra papeles
  añadidos), 422 (fin < inicio, arrendatario entre codeudores, tipo inexistente, canon
  negativo, `propietarios_ids: []`, texto con `\x00`, campo extra, `fecha_desde` inválida),
  404 inmueble/persona, 409 sin propietarios, **matriz de solapamiento de fechas** (A
  2026-01-01→06-30, B 2026-09-01→∞: `desde=07-01` → B; `hasta=01-01` → A; `desde=06-30 &
  hasta=09-01` → ambos; `desde=2027-01-01` → B), filtros por inmueble/propietario/inquilino/
  tipo, listado sin texto y detalle con texto, actualizar reemplaza partes, 409 con
  dependencias en PUT y DELETE, asesor 403, 204, 404.
- API integración `test_contratos_mysql.py`: partes con los códigos correctos; papeles
  automáticos (`/codeudores?contrato_id=` devuelve exactamente los dos; volver a guardar no
  duplica); filtro por fechas sobre MySQL; eliminar bloqueado por `financial_record` (se
  insertan `financial_category`, `payment_state` y un registro por SQL → 409; tras borrarlos →
  204; añadir esas dos tablas a la limpieza); detalle de cliente clasifica el contrato; canon
  → COP / sin canon → NULL.
- Web: `ContratoForm.test.tsx` (precarga de propietarios, fechas, choque arrendatario/codeudor,
  cuerpo enviado), `InmueblePicker.test.tsx`, `ContratosPage.test.tsx` (filtros de URL →
  query), `ContratoDetallePage.test.tsx` (`vi.spyOn(window, "print")`; `pre` con el texto;
  botón deshabilitado sin texto; asesor sin Eliminar).
- E2E `contratos.spec.ts`: crear ARRENDAMIENTO con inmueble 9201 por matrícula, arrendatario
  9102 por búsqueda y un codeudor registrado inline; fila visible en < 2 s; filtros por fechas
  e `inmueble_id` desde Inmuebles; detalle: sustituir `window.print` por un *flag* con
  `page.evaluate` y comprobarlo al pulsar «Imprimir / guardar PDF»; `/codeudores?contrato_id=`
  lista el codeudor; editar fecha fin; eliminar. Segunda prueba: asesor crea pero no ve Eliminar.

### Docs

`modelo-de-datos.md` (ASSOCIATED→TENANT; ocupación manual; regla de dependencias),
`docs/requisitos/README.md` (Contratos y Codeudores → Implementado), `docs/pruebas/README.md`,
`README.md`, `docs/manual-usuario.md` sección «Contratos e impresión en PDF» («Guardar como PDF»
en el diálogo de impresión de Chrome, Firefox y Safari).

---

## Fase 5 — Ayuda, responsive, respaldo local y documentación (commit: «Agrega ayuda en línea, diseño adaptable, respaldo local y documentación final (fase 5)»)

### Ayuda en línea (web)

- `pages/AyudaPage.tsx` (`/ayuda`, pública, sin datos): índice y secciones con ids
  `inicio-de-sesion`, `clientes`, `propietarios`, `codeudores`, `inmuebles`, `contratos`,
  `usuarios`, `mensajes-de-error`, `navegadores-y-dispositivos`, `soporte`; contenido JSX
  espejo de `docs/manual-usuario.md` (sin librería de markdown); desplaza a `location.hash` al
  montar.
- `components/AyudaLink.tsx` (`<Link to="/ayuda#seccion">Ayuda</Link>` con `aria-label`) en
  cada `.page-header` y en la tarjeta de login. `MainLayout`: enlace «Ayuda» siempre visible;
  pie con entorno y versión de la API (`useApiStatus`).
- `components/ErrorAlert.tsx` compartido: añade «Código de soporte: <requestId>» cuando
  `ApiError.requestId` existe; lo usan listas y formularios.

### Responsive y consistencia (`styles.css`)

- Verificar los tres modos del cascarón (barra lateral ≥ 1280 px, riel 768–1279 px, cajón
  < 768 px) en todas las pantallas; el cajón se cierra al navegar y con Escape; foco atrapado
  mientras está abierto.
- `.filters`, `.actions`, `.page-header` con `flex-wrap`; `.form-grid` a una columna < 768 px.
- Tablas: `.table-wrap` con desplazamiento horizontal, `min-width: 480px`, primera columna
  `nowrap`, `.row-actions` apiladas en móvil. Objetivos táctiles `min-height: 40px`.
- Lista de consistencia aplicada a todas las páginas: `.page-header` (h1 + acciones + Ayuda) →
  `.filters` → tarjeta → `Pagination`; éxitos `alert-success role="status"`, errores
  `alert-error role="alert"`, destructivos `button.danger`; fechas y dinero con
  `utils/formato.ts` (`formatearFecha`, `formatearMoneda`, es-CO); insignias según el mapa de
  la identidad; contraste AA comprobado para texto sobre `#FEE2E2`, `#ECFDF5`, `#FFFBEB`,
  `#EEF2FF`.
- Revisión pantalla por pantalla contra `stitch_sistema_aphia_ui_ux/*/screen.png`; las
  diferencias deliberadas se anotan en la sección «Decisiones» de `DESIGN.md` y en
  `docs/diseno/README.md`. El tablero (`/`) recibe su versión final (KPI, módulos, vencimientos).
- Sin CSS más allá de flex/grid/`:focus-visible`; verificación manual a 375×740, 1024×768 y
  1440×900.

### Respaldo diario local (`infra/production/backup/backup.sh`)

- Nuevas variables `BACKUP_LOCAL_DIR` (por defecto `/var/backups/aphia`) y
  `BACKUP_LOCAL_RETENTION_DAYS` (14); `BACKUP_RCLONE_REMOTE` pasa a ser opcional
  (`BACKUP_AGE_RECIPIENT` sigue obligatorio).
- Tras cifrar: `install -d -m 700 "$BACKUP_LOCAL_DIR"`, `install -m 600 "$archive"
  "$BACKUP_LOCAL_DIR/"`, `find … -name 'aphia-*.tar.age' -mtime +N -delete`. Copia remota solo
  si hay remoto configurado; el log indica ruta local y si hubo copia externa.
- `backup.env.example` y `docs/despliegue/restauracion.md` (fila «Copia local cifrada»,
  ejemplo de restauración desde local, advertencia: la copia local no sobrevive a la pérdida del
  VPS; clave privada `age` sigue fuera del VPS). Cron diario ya documentado (03:15 UTC).

### Documentación

- `docs/manual-usuario.md` (nuevo): roles y qué puede hacer cada uno, inicio de sesión y
  bloqueo, navegación, una sección por módulo (registrar, buscar, ver, modificar, eliminar y sus
  restricciones), contratos e impresión en PDF, usuarios, mensajes de error frecuentes,
  navegadores y dispositivos, soporte. Sin credenciales.
- `docs/despliegue/instalacion-y-mantenimiento.md` (nuevo): instalación local, despliegue,
  **primer administrador en producción** (hash generado localmente con `hash_password` +
  `INSERT` en `person`, `person_document`, `user_account`, `user_role`; nunca por seeds),
  rotación de `AUTH_SECRET`, desbloqueo manual por SQL, respaldos y restauración, migraciones,
  qué vigilar en logs (`cuenta_bloqueada`, `login_failed`, `unhandled_exception`,
  `db_connect_failed`), actualización de dependencias.
- `docs/requisitos/README.md`: lista completa de requisitos con ids RF-01…RF-18 y RNF-01…RNF-12
  y **matriz de trazabilidad** Requisito → Endpoints → Pantallas → Pruebas (p. ej. RF-05 →
  `PUT/DELETE /propietarios/{id}` → `/propietarios/:id` → `test_delete_propietario_con_inmuebles…`,
  `propietarios.spec.ts`; RNF-02 → `reload()` tras escritura → `toBeVisible({timeout: 2000})`;
  RNF-05 → `backup.sh`; RNF-09 → proyectos Playwright chromium/firefox/webkit).
- También: `docs/pruebas/README.md` (conteos finales, proyectos Playwright),
  `docs/seguridad/README.md` (respaldo local, `AUTH_SECRET`, pendientes recortados),
  `docs/arquitectura/README.md` (flujo de autenticación), `docs/README.md` (manual y guía),
  `README.md` (estado, comandos, `test:e2e:install` con tres navegadores), `AGENTS.md` (módulos
  finales; «`manual-usuario.md` se actualiza con cada cambio de pantalla»).

### Pruebas

- Web: `AyudaPage.test.tsx`, `AyudaLink.test.tsx`, `MainLayout.test.tsx` (+Ayuda, pie),
  `ErrorAlert.test.tsx`.
- E2E: `ayuda.spec.ts` (desde `/clientes` llega a `#clientes`); `responsive.spec.ts` con
  `viewport 375×740` (login, menú visible, tabla con desplazamiento, formulario usable);
  `playwright.config.ts` añade proyectos `firefox` y `webkit` con `grep: /@smoke/` (etiquetar
  «login OK» y «lista de clientes»); `test:e2e:install` → `playwright install chromium firefox
  webkit` (CI con `--with-deps`).
- API integración `test_rendimiento_mysql.py`: inserta 500 personas con `executemany` y
  comprueba que `GET /clientes?q=`, `GET /propietarios` y `GET /contratos?fecha_desde=`
  responden en < 3 s (evidencia de RNF-01, no un *benchmark*).

---

## Criterios de aceptación por módulo

Cada criterio es comprobable y tiene una prueba automatizada asociada (unitaria, integración o
E2E) salvo donde se indica «manual». Un módulo se da por terminado cuando **todos** sus
criterios se cumplen y la «Definición de hecho» de su fase está completa.

### Definición de hecho (todas las fases)

- `pnpm lint && pnpm typecheck && pnpm test` en verde; `pnpm test:integration` en verde;
  `pnpm test:e2e` en verde (incluye el login real desde la fase 1).
- Ninguna petición de la UI termina en 500; la consola del navegador no muestra errores ni
  advertencias de React en los flujos E2E.
- Toda respuesta de error de la API cumple `{"error": {"codigo", "mensaje", "request_id"}}`
  con mensaje en español comprensible; la UI lo muestra en `role="alert"` sin pantalla en blanco.
- Nada de datos personales reales en seeds, pruebas o documentación (`example.test`).
- Documentación del cambio actualizada (`README.md`, `AGENTS.md`, `docs/` afectados,
  `docs/manual-usuario.md` desde la fase 2) y migraciones aplicables desde cero
  (`pnpm infra:reset --yes && pnpm db:migrate && pnpm db:seed`).

### Acceso y usuarios (fase 1)

| # | Criterio |
| --- | --- |
| A1 | Con usuario y contraseña correctos, `POST /api/v1/auth/login` responde 200 con token y principal; la UI redirige a la ruta de origen o a `/` y el menú muestra nombre y rol. |
| A2 | Con contraseña incorrecta responde 401 `credenciales_invalidas` y la UI muestra «Usuario o contraseña incorrectos.»; con usuario inexistente la respuesta es idéntica (sin revelar si existe). |
| A3 | Al tercer intento fallido consecutivo la cuenta queda bloqueada 15 minutos: la API responde 423 `cuenta_bloqueada` incluso con la contraseña correcta; `failed_login_attempts = 3` y `locked_until` quedan persistidos; el evento `cuenta_bloqueada` aparece en los logs sin usuario ni clave. |
| A4 | Un inicio de sesión correcto reinicia el contador a 0; vencidos los 15 minutos la cuenta vuelve a aceptar la contraseña correcta sin intervención. |
| A5 | El Administrador de Sistemas ve cada cuenta bloqueada en `/usuarios` (alerta + insignia «Bloqueada») y «Desbloquear» la habilita de inmediato (200 y `locked_until = NULL`). |
| A6 | Sin token, con token manipulado o expirado, cualquier endpoint protegido responde 401 con `WWW-Authenticate: Bearer`; la UI limpia la sesión y vuelve a `/login`. |
| A7 | Las contraseñas se guardan solo como `pbkdf2_sha256$…` (nunca en claro) y nunca se devuelven en respuestas ni logs; dos usuarios con la misma clave tienen hashes distintos. |
| A8 | Solo `admin_sistemas` accede a `/api/v1/usuarios*` (los demás roles reciben 403 y no ven el enlace «Usuarios»). |
| A9 | Crear usuario exige nombre de usuario (minúsculas, único), nombre, identificación, correo, clave (≥ 8, letra y dígito) y rol; los datos inválidos responden 422 indicando el campo; el nombre de usuario duplicado responde 409 `usuario_duplicado`. |
| A10 | Editar permite cambiar nombre, identificación, correo, rol, activo y, opcionalmente, la clave; una cuenta inactiva no puede iniciar sesión. |
| A11 | No se puede eliminar, desactivar ni degradar al último `admin_sistemas` activo (409 `ultimo_administrador`) ni eliminar/desactivar la cuenta propia (409 `usuario_actual`). |
| A12 | `AUTH_MODE=database` sin `AUTH_SECRET` (o con menos de 32 caracteres) impide arrancar la API con un mensaje de configuración claro; `AUTH_MODE=development` sigue rechazado fuera de development/test. |
| A13 | La pantalla de login respeta el mockup (columna de marca + tarjeta) y en móvil (375 px) el formulario es usable sin desplazamiento horizontal. |

### Clientes (fase 2)

| # | Criterio |
| --- | --- |
| C1 | Registrar un cliente con nombre, tipo y número de identificación, teléfono, correo y un tipo de cliente (papel) responde 201 y la fila aparece en la lista en menos de 2 s sin recargar la página. |
| C2 | Campos obligatorios vacíos, correo o teléfono con formato inválido, `papeles` vacío o campos desconocidos responden 422 con el campo señalado; la UI marca el campo (`aria-invalid`) y conserva lo escrito. |
| C3 | Una identificación ya registrada (mismo tipo y número) responde 409 `identificacion_duplicada` y la UI ofrece abrir la persona existente. |
| C4 | La lista se filtra por nombre o identificación (`q`) sin distinguir mayúsculas ni acentos, y por papel con los segmentos Todos / Arrendatarios / Propietarios / Codeudores; la paginación muestra «Mostrando a–b de N». |
| C5 | El detalle muestra datos, papeles, cuenta bancaria, usuario del sistema (si existe), inmuebles de los que es propietario y contratos separados por papel (propietario, arrendatario, codeudor). |
| C6 | Editar actualiza datos de contacto, papeles y cuenta bancaria en una sola transacción; quitar un papel que tiene vínculos (inmuebles o contratos) responde 409 `papel_en_uso`. |
| C7 | Eliminar una persona sin vínculos responde 204 y desaparece de la lista; con inmuebles, contratos o cuenta de usuario responde 409 `persona_con_dependencias` con un mensaje que dice cuáles. |
| C8 | `asesor` y `administrativo` pueden crear y editar; solo `administrativo` y `admin_sistemas` ven y pueden usar «Eliminar» (la API responde 403 al asesor). |
| C9 | Una misma persona puede tener a la vez los papeles propietario, arrendatario y codeudor y aparece en las tres listas. |

### Propietarios (fase 2)

| # | Criterio |
| --- | --- |
| P1 | Registrar un propietario exige nombre, identificación, dirección, teléfono, correo y cuenta bancaria (banco, tipo, número); responde 201 y la persona queda con el papel propietario. |
| P2 | La lista muestra solo personas con papel propietario, con cuenta bancaria enmascarada y el chip «N inmuebles» / «Sin inmuebles», y se filtra por nombre, identificación o correo. |
| P3 | Un propietario sin inmuebles se puede modificar y eliminar; con al menos un inmueble, eliminar responde 409 `persona_con_dependencias` («es propietaria de N inmueble(s)») y la UI lo muestra sin recargar. |
| P4 | Una persona registrada como cliente que se asocia como propietaria de un inmueble aparece automáticamente en Propietarios con ese papel. |
| P5 | El banco se escribe libremente con sugerencias; dos propietarios con el mismo nombre de banco comparten una sola fila en `financial_institution`. |

### Codeudores (fases 2 y 4)

| # | Criterio |
| --- | --- |
| D1 | Registrar, modificar y eliminar codeudores funciona con las mismas reglas que clientes; al registrar desde Codeudores la persona queda con el papel codeudor. |
| D2 | Un contrato acepta varios codeudores (hasta 10), todos distintos entre sí y distintos del arrendatario; cada uno queda en `agreement_party` con el código `CO_DEBTOR`. |
| D3 | Al asociar como codeudor a una persona que no tenía ese papel, el papel se agrega solo; volver a guardar el contrato no duplica filas. |
| D4 | `GET /api/v1/codeudores?contrato_id=` devuelve exactamente los codeudores de ese contrato y `?q=<identificación>` encuentra por número exacto o parcial; la UI permite ambas búsquedas. |
| D5 | Desde el selector del contrato se puede buscar un codeudor existente por identificación o registrarlo en el momento con nombre, teléfono y correo. |

### Inmuebles (fase 3)

| # | Criterio |
| --- | --- |
| I1 | Registrar un inmueble exige dirección y al menos un propietario; acepta ciudad, matrícula, canon (≥ 0, 2 decimales, moneda COP implícita), estado (Disponible/Ocupado) y una lista de contratos de servicios públicos (tipo, proveedor, número); responde 201 y aparece en la lista en menos de 2 s. |
| I2 | Canon negativo, con más de dos decimales, estado inexistente, lista de propietarios vacía o servicio sin número responden 422; un propietario inexistente responde 404 `persona_no_encontrada`. |
| I3 | La lista se filtra por estado, ciudad (sin distinguir mayúsculas ni acentos), propietario y texto (dirección o matrícula); los filtros aplicados se ven como chips y «Restablecer» los limpia; el canon se muestra en formato `es-CO`. |
| I4 | Editar reemplaza propietarios y servicios y conserva el identificador; quitar un propietario del inmueble no le quita su papel. |
| I5 | Eliminar un inmueble sin contratos responde 204; con contratos responde 409 `inmueble_con_contratos` con el número de contratos. |
| I6 | La ciudad se escribe con sugerencias; el mismo nombre exacto reutiliza la fila de `city` y un inmueble sin canon no guarda moneda. |
| I7 | El formulario se abre como panel lateral sobre la lista con URL propia (`/inmuebles/nuevo`, `/inmuebles/:id/editar`), se cierra con Escape o «Cancelar» y en móvil ocupa toda la pantalla. |

### Contratos (fase 4)

| # | Criterio |
| --- | --- |
| K1 | Registrar un contrato exige tipo, inmueble, fecha de inicio y al menos un propietario (por defecto los del inmueble); acepta fecha de fin, canon pactado, condiciones, texto completo, arrendatario opcional y codeudores; responde 201. |
| K2 | Fecha de fin anterior al inicio, arrendatario incluido entre los codeudores, tipo inexistente o canon negativo responden 422; inmueble inexistente responde 404; inmueble sin propietarios y sin lista explícita responde 409 `inmueble_sin_propietario`. |
| K3 | La lista se filtra por rango de fechas (solapamiento de vigencia, incluidos contratos sin fecha de fin), inmueble, propietario, inquilino, tipo y estado (Todos / Vigentes / Por vencer < 60 días / Finalizados); muestra días restantes. |
| K4 | El detalle muestra inmueble, partes con su papel en ese contrato, codeudores, fechas, canon, condiciones y el texto completo; «Imprimir / guardar PDF» abre el diálogo de impresión con una vista limpia (sin menú ni botones) y queda deshabilitado si no hay texto. |
| K5 | Modificar o eliminar un contrato con registros financieros o archivos asociados responde 409 `contrato_con_dependencias`; sin dependencias, editar reemplaza las partes y eliminar responde 204. |
| K6 | Desde el detalle se puede asociar o quitar un codeudor sin editar el resto del contrato. |
| K7 | Al consultar un cliente, el contrato aparece en la lista que corresponde a su papel (como propietario, arrendatario o codeudor) y no en las otras. |
| K8 | El estado de ocupación del inmueble no cambia solo; tras guardar un contrato la UI recuerda revisarlo. |

### Tablero, cascarón y búsqueda (fases 1–4)

| # | Criterio |
| --- | --- |
| T1 | El tablero muestra conteos reales (inmuebles total/ocupados/disponibles, clientes por papel, contratos vigentes, vencimientos < 30 días, usuarios) obtenidos de `GET /api/v1/resumen` en una sola petición, y tarjetas de módulo con enlaces según el rol. |
| T2 | La barra lateral marca la sección activa, muestra «Usuarios» solo a `admin_sistemas`, el estado de la API y «Salir»; en tableta pasa a riel de iconos con `aria-label` y en móvil a cajón accesible (Escape, foco atrapado, cierre al navegar). |
| T3 | La búsqueda global devuelve hasta 5 personas, 5 inmuebles y 5 contratos por texto, navegable con teclado, y abre el registro elegido. |
| T4 | Todas las páginas comparten la plantilla (migas, cabecera, KPI, filtros, tabla, paginación), las mismas insignias por estado y papel, y formatos de fecha y moneda `es-CO`. |

### Ayuda, documentación y no funcionales (fase 5)

| # | Criterio |
| --- | --- |
| N1 | `/ayuda` existe sin iniciar sesión, cubre cada módulo, el login y los mensajes de error, y cada pantalla enlaza a su sección; `docs/manual-usuario.md` tiene el mismo contenido. |
| N2 | Cada alerta de error de la API incluye el «Código de soporte» (`request_id`). |
| N3 | Los flujos E2E principales pasan en Chromium y las pruebas *smoke* en Firefox y WebKit; la vista a 375 px no tiene desplazamiento horizontal de página y las tablas se desplazan dentro de su contenedor. |
| N4 | `GET /clientes?q=`, `GET /propietarios` y `GET /contratos?fecha_desde=` responden en menos de 3 s con 500 personas de prueba (medición en `test_rendimiento_mysql.py`); las escrituras se reflejan en pantalla en menos de 2 s (E2E). |
| N5 | `backup.sh` deja una copia cifrada diaria en `BACKUP_LOCAL_DIR` con permisos 700/600 y retención configurable; la restauración desde esa copia está documentada y probada en la réplica local (manual). |
| N6 | Existe `docs/despliegue/instalacion-y-mantenimiento.md` con instalación, primer administrador, rotación de secreto, respaldos, migraciones y qué vigilar en logs; `docs/requisitos/README.md` contiene la matriz de trazabilidad completa. |
| N7 | La identidad visual coincide con los mockups en estructura, colores, tipografía y componentes; las diferencias deliberadas están anotadas en `DESIGN.md` → «Decisiones» y en `docs/diseno/README.md`. |

## Pruebas existentes que cambian

| Archivo | Fase | Cambio |
| --- | --- | --- |
| `apps/api/tests/conftest.py` | 0–4 | fakes a `tests/fakes.py`; `app` sobreescribe cada `get_*_repository` según aparece |
| `apps/api/tests/unit/test_auth.py` | 0, 1 | roles nuevos; secreto; login/bloqueo/token/`me` |
| `apps/api/tests/unit/test_clientes.py` | 2 | se elimina (casos a `test_personas.py`) |
| `apps/api/tests/unit/test_errores_y_seguridad.py` | 1, 2 | overrides sobre `get_personas_repository`; log de login |
| `apps/api/tests/unit/test_runtime_workers.py`, `test_migraciones.py` | — | sin cambios |
| `apps/api/tests/integration/conftest.py` | 1–4 | limpieza ordenada; variante `settings_for(auth_mode="database", auth_secret=…)` |
| `apps/api/tests/integration/test_modelo_3fn.py` | 0 | `DATOS_BASE` con subconsultas sobre catálogos sembrados; pruebas nuevas |
| `apps/api/tests/integration/test_clientes_mysql.py` | 2 | se elimina (genéricas a `test_personas_mysql.py`) |
| `apps/api/tests/integration/test_migraciones_mysql.py` | 3 | + tabla `clientes` eliminada |
| `apps/web/src/pages/HomePage.test.tsx` | 1, 2 | tarjetas de módulos / login; sin demo |
| `apps/web/src/routes/ProtectedRoute.test.tsx` | 0, 1 | roles; `/usuarios` negado a asesor |
| `apps/web/src/test/mockApi.ts` | 0–2 | `DEV_PRINCIPAL`, `DB_PRINCIPAL`, `LOGIN_OK`, `CATALOGOS`, `persona()`, `usuario()`; sin `cliente()` |
| `apps/web/src/features/clientes/ClienteForm.test.tsx` | 0, 2 | pasa con `Field` compartido; se elimina en fase 2 |
| `apps/web/src/services/apiClient.test.ts` | 1 | Bearer y 401 |
| `tests/e2e/clientes.spec.ts` | 1, 2 | `iniciarSesion`; sin `/panel`; reescrito para personas |
| `playwright.config.ts`, `package.json`, `ci.yml` | 1, 5 | `db:seed` y `.dev.vars` antes del e2e; proyectos firefox/webkit |

## Riesgos y puntos abiertos

1. **Coste de PBKDF2 frente al límite de CPU de Workers.** Plan gratuito ≈ 10 ms de CPU por
   solicitud; de pago 30 s. 100 000 iteraciones cuestan decenas de ms en nativo y más en WASM:
   el login **no cabe en el plan gratuito**. Primer paso de la fase 1: verificar que
   `hashlib.pbkdf2_hmac` existe en Pyodide y medir `duration_ms`. Si el proyecto va en el plan
   gratuito, las opciones son plan de pago (USD 5/mes) o servir la API con Uvicorn en el VPS
   (ruta alternativa ya prevista). Decisión del responsable; se documenta la medición.
2. **Colación binaria.** Los filtros de texto usan `ai_ci` y no aprovechan índices; aceptable
   para el volumen esperado. `user_name`, identificación y nombres de catálogo son exactos.
3. **Unicidad global de `person_document`.** Una identificación pertenece a una sola persona;
   el selector busca antes de registrar y la API devuelve 409 claro. Un usuario del sistema con
   la misma identificación que un cliente comparte la fila `person`.
4. **Tabla `clientes`.** Sin uso tras la fase 2, se elimina en la fase 3 (0011).
5. **`ASSOCIATED` → `TENANT`.** La app nunca crea `ASSOCIATED`; una carga histórica lo
   mapearía a `TENANT`. Queda en `modelo-de-datos.md`.
6. **Tokens sin estado.** Cambios de rol o desactivación aplican en el siguiente inicio de
   sesión o a las 8 h; rotar `AUTH_SECRET` cierra todas las sesiones; `sessionStorage` exige
   iniciar sesión en cada pestaña nueva.
7. **Ocupación manual.** No se deriva de los contratos (nota del modelo); recordatorio en la UI.
8. **Seeds.** Los textos no pueden tener líneas que terminen en `;` ni empiecen por `--`.
9. **Navegadores extra en CI.** Firefox/WebKit solo con dos pruebas *smoke*.
10. **Papel de propietario.** Quitar a alguien de un inmueble no le quita el papel; se quita a
    mano y está bloqueado mientras posea algo.
11. **Decisiones de negocio aún abiertas** (no bloquean): finanzas (`financial_record`),
    documentos adjuntos (`file_*`), tipos de contrato adicionales (migración nueva).
12. **Alcance de los mockups.** Cuatro pantallas (auditoría forense y exportaciones PDF/CSV/
    ZIP) y la recuperación por correo/SMS quedan fuera: exigen bitácora de accesos (tabla nueva
    y decisión de negocio 10), generación de archivos y proveedor de correo. Varios elementos
    decorativos o sin respaldo en el modelo (fotos, tipo/área/estrato de inmueble, pólizas,
    recaudo, mora, comisiones, 2FA, multi-sede, notificaciones) se excluyen y se documentan en
    `DESIGN.md` → «Decisiones». Si el responsable quiere alguno, es una fase posterior con
    migraciones propias.
13. **Fuente autoalojada.** `@fontsource-variable/plus-jakarta-sans` añade ~100 KB (woff2) al
    bundle; aceptable. Si se prefiere cero dependencias, se copian los `woff2` a
    `apps/web/public/fonts/` con un `@font-face` propio (misma CSP).
14. **Fidelidad visual.** Los mockups están hechos con Tailwind; la web usa CSS plano con los
    mismos tokens. Habrá diferencias de detalle (sombras, espaciados); lo que se preserva es la
    estructura, la jerarquía, los colores, la tipografía y los componentes.

## Verificación

Por fase, antes de cada commit:

```bash
pnpm lint && pnpm typecheck && pnpm test
pnpm test:integration          # SQL, migraciones y modelo 3FN sobre aphia_test
pnpm test:e2e                  # infra up + db:migrate + db:seed + Playwright
```

Comprobaciones manuales mínimas:

- Fase 0: `pnpm db:migrate` aplica 0008–0010 sobre una base con 0001–0007; `pnpm db:seed`.
- Fase 1: `pnpm dev`, `POST /api/v1/auth/login` con `admin`/`Aphia.2026` en Workers
  (`duration_ms` en el log) y con `pnpm dev:asgi`; tres fallos bloquean; «Desbloquear» en
  `/usuarios`; `wrangler` sin `.dev.vars` falla con el mensaje de configuración.
- Fases 2–4: flujo completo en el navegador: registrar cliente → convertirlo en propietario
  desde un inmueble → contrato con arrendatario nuevo registrado inline y dos codeudores →
  detalle del cliente muestra cada papel → imprimir contrato → intentos de borrado bloqueados
  con mensajes claros → borrado en orden correcto.
- Fase 5: `/ayuda` desde cada pantalla; vista a 375 px; `backup.sh` en la réplica local
  (`infra/production`) deja el archivo en `BACKUP_LOCAL_DIR` con permisos 600/700.

## Archivos críticos

- `apps/api/src/modules/auth/dependencies.py` — resolución del principal (`development` /
  `database`), `require_roles`, grupos de roles.
- `apps/api/src/modules/personas/repository.py` — SQL compartido de persona + documento /
  teléfono / correo / papeles / cuenta bancaria (clientes, propietarios, codeudores,
  selectores, detalle).
- `apps/api/src/core/config.py` — `AUTH_SECRET` y validación de `AUTH_MODE=database`.
- `apps/web/src/features/auth/AuthProvider.tsx` y `services/apiClient.ts` — login/logout,
  token y manejo de 401 del que dependen todas las pantallas.
- `apps/api/tests/integration/test_modelo_3fn.py` — debe adaptarse a los catálogos sembrados
  por 0008 antes de que `pnpm test:integration` vuelva a pasar.
- `database/migrations/0008–0011`, `database/seeds/0002–0006`.

## Bitácora de decisiones

| Fecha | Fase | Decisión o desviación respecto al plan |
| --- | --- | --- |
| 2026-10-28 | 0 | Iconos con `lucide-react` (SVG en línea, MIT) en lugar de Material Symbols: la CSP no permite la fuente de iconos de Google y así no hay dependencias externas en tiempo de ejecución. |
| 2026-10-28 | 0 | `PAPEL_POR_CODIGO` vive en `modules/catalogos/schemas.py` (módulo hoja); `personas` lo importará desde ahí en la fase 2. |
| 2026-10-28 | 0 | Los códigos de catálogo se validan contra la tabla en el repositorio (no con `Literal`), para que agregar un valor sea una migración y no un cambio de código. |
