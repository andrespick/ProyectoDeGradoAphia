# Identidad visual

Origen: proyecto de Google Stitch «Sistema APHIA UI/UX»
(<https://stitch.google.com/projects/8942478746065544413>). La exportación completa
(`DESIGN.md` con los tokens y `stitch_sistema_aphia_ui_ux/` con 13 pantallas en PNG y HTML)
se conserva en la raíz del repositorio **sin versionar** (`.gitignore`); este documento resume
lo que el código aplica, de modo que el repositorio sea autosuficiente.

## Tokens (`apps/web/src/styles.css`)

| Grupo | Valores |
| --- | --- |
| Rojo institucional | `--color-primary #B70011` (marca, botones primarios, ítem activo), `--color-accent #DC2626` (foco, error), `--color-primary-dark #991B1B` (hover), `--color-primary-light #FEE2E2` (fondos suaves) |
| Neutros pizarra | `--slate-50 #F8FAFC` (lienzo), `--slate-100 #F1F5F9`, `--slate-200 #E2E8F0` (bordes), `--slate-300 #CBD5E1`, `--slate-400 #94A3B8` (placeholder), `--slate-600 #475569` (texto secundario), `--slate-700 #334155`, `--slate-900 #0F172A` (texto) |
| Acentos | Esmeralda `#10B981` / `#ECFDF5` (activo, vigente, ocupado), ámbar `#F59E0B` / `#FFFBEB` (pendiente, por vencer, disponible), índigo `#6366F1` / `#EEF2FF` (codeudor) |
| Tipografía | **Plus Jakarta Sans** autoalojada (`@fontsource-variable/plus-jakarta-sans`); h1 1.75 rem/700, h2 1.25 rem/600, cuerpo 1 rem, cabeceras de tabla 0.7 rem mayúsculas +0.05em, cifras con `tabular-nums` (`.num`) |
| Formas | Controles y botones 0.5 rem; tarjetas y paneles 0.75 rem; insignias píldora (9999px) |
| Elevación | Tarjetas: borde `#E2E8F0` + `--shadow-1`; desplegables `--shadow-2`; paneles y cajón `--shadow-3` |

Solo existe tema claro (la identidad no define uno oscuro).

## Cascarón

- **≥ 1280 px:** barra lateral fija de 260 px (marca, navegación con icono, estado del
  sistema y «Salir») + barra superior (menú móvil, búsqueda global, acciones y usuario).
- **768–1279 px:** riel de 72 px solo con iconos (`title` y `aria-label`).
- **< 768 px:** barra superior con botón «Menú» y cajón lateral (cierre con Escape y al navegar).
- Plantilla de página: migas → `.page-header` (icono, título, chip de total, acciones) →
  banner de regla → `.kpi-grid` → `.filters` → tarjeta con tabla → `Pagination`.
- Formularios cortos y medios en `SlideOver` (panel derecho con secciones numeradas);
  contratos en página completa.

## Componentes (`apps/web/src/components`)

`Field`, `SelectField`, `TextAreaField` (etiqueta, pista y error accesibles), `Pagination`,
`Segmented` (segmentos de filtro), `KpiCard`, `Avatar` (iniciales), `SlideOver`,
`StatusIndicator`. Iconos: `lucide-react` (SVG en línea, 20 px, `aria-hidden`).

## Mapa de insignias

| Insignia | Clase | Uso |
| --- | --- | --- |
| Rojo claro | `badge-primary` / `badge-error` | papel Propietario; cuenta bloqueada |
| Esmeralda | `badge-ok` | papel Arrendatario; inmueble Ocupado; usuario Activo; contrato Vigente |
| Índigo | `badge-info` | papel Codeudor |
| Ámbar | `badge-warn` | inmueble Disponible; contrato Por vencer |
| Pizarra | `badge-muted` | usuario Inactivo; contrato Finalizado |

## Pantallas del mockup y su ruta

| Mockup | Ruta | Fase |
| --- | --- | --- |
| Autenticación y login seguro | `/login` | 1 |
| Tablero principal (hub de módulos) | `/` | 1–4 |
| Gestión de clientes | `/clientes` | 2 |
| Gestión de propietarios | `/propietarios` | 2 |
| Gestión de inmuebles (con panel «Registrar nuevo inmueble») | `/inmuebles` | 3 |
| Gestión de contratos y codeudores | `/contratos`, `/codeudores` | 2 y 4 |
| Gestión de usuarios y roles (1 y 2) | `/usuarios` | 1 |
| Recuperación de contraseña y desbloqueo | — (se cubre con `/ayuda#inicio-de-sesion` y el desbloqueo desde Usuarios) | — |
| Auditoría de intentos de acceso; exportar reporte forense (PDF, CSV/Excel); paquete ZIP cifrado | — (fase futura: requiere bitácora de accesos y generación de archivos) | — |

## Adaptaciones respecto al mockup

- Sin selector de «perfil de acceso» en el login (el rol viene de la cuenta); sin recuperación
  por correo/SMS ni 2FA (no hay proveedor de correo; decisión del responsable).
- Sin chip de sede, campana de notificaciones, fotos de inmuebles, tipo/área/estrato,
  pólizas, recaudo, mora ni comisiones: no existen en el modelo 3FN ni en los requisitos.
- Los mockups usan Tailwind; la web usa CSS plano con los mismos tokens, por lo que hay
  diferencias de detalle en sombras y espaciados.
