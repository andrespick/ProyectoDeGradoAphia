# Manual de usuario de APHIA

Guía para el personal de APHIA S.A.S. El mismo contenido está disponible dentro de la
aplicación en **Ayuda** (`/ayuda`), sin necesidad de iniciar sesión; cada pantalla tiene un
enlace «Ayuda» que lleva a su sección. Al cambiar una pantalla, actualice este manual y la
página de ayuda.

## Roles

| Rol | Qué puede hacer |
| --- | --- |
| Administrador de Sistemas | Solo la gestión del sistema: estado del sistema y respaldos, usuarios y contraseñas, auditoría, catálogos, configuración (política de seguridad y datos de la empresa) y papelera. No ve clientes, inmuebles ni contratos; al entrar llega a Sistema |
| Administrativo | Consultar, registrar, modificar y eliminar clientes, propietarios, codeudores, inmuebles y contratos |
| Asesor | Consultar, registrar y modificar; **no** elimina |

## Inicio de sesión y bloqueo

1. Abra la aplicación e ingrese el usuario y la contraseña que le asignó el Administrador de
   Sistemas. «Recordarme en este equipo» mantiene la sesión al cerrar la pestaña; no lo use en
   equipos compartidos. La sesión dura 8 horas (valor por defecto; lo fija la política de
   seguridad).
2. Tras **3 intentos fallidos** la cuenta queda bloqueada **15 minutos** (valores por defecto;
   la pantalla de inicio de sesión muestra los vigentes). Espere o pida al Administrador de
   Sistemas que la desbloquee desde Usuarios. El mensaje indica los minutos que faltan.
3. No hay recuperación de contraseña por correo: el enlace «¿Olvidó su contraseña?» explica que
   el Administrador de Sistemas le genera una **clave temporal** desde Usuarios. Al entrar con
   ella, la aplicación le pide cambiarla antes de mostrar cualquier otra pantalla.
4. **Cambiar contraseña:** icono de llave junto a su nombre, en la barra superior. Pide la
   contraseña actual y la nueva dos veces; al guardarla se cierran sus sesiones en otros equipos.
5. Al entrar, cada persona llega siempre a su pantalla de inicio: el Administrador de Sistemas a
   Sistema y los demás roles al tablero de Inicio, sin importar qué pantalla estaba abierta antes
   (podía ser de otra persona). Si la sesión expira, vuelve al inicio de sesión. Si el
   Administrador de Sistemas cierra sus sesiones, cambia su rol o desactiva su cuenta, la sesión
   termina de inmediato.

## Navegación

- Barra lateral: Inicio, Clientes, Propietarios, Codeudores, Inmuebles, Contratos y Ayuda; el
  Administrador de Sistemas ve Sistema, Usuarios, Auditoría, Catálogos, Configuración, Papelera
  y Ayuda. Abajo, el estado del sistema y «Salir».
- En tabletas la barra se reduce a iconos; en el celular se abre con «Abrir menú» y se cierra
  con Escape, al tocar fuera o al navegar.
- La caja **Buscar inmueble, cliente, contrato…** de la barra superior (computador y tableta)
  muestra hasta cinco resultados por grupo; Enter abre el primero y Escape cierra la lista.
- **Inicio** resume inmuebles, clientes por papel, contratos vigentes y vencimientos en menos
  de 30 días, lista los contratos que vencen pronto y enlaza a cada módulo.
- Todas las listas comparten la misma estructura: cabecera con «Registrar…», indicadores,
  filtros (los aplicados aparecen como fichas con «Restablecer»), tabla y paginación
  («Mostrando a–b de N», tamaño de página 10/20/50).

## Clientes

Un cliente es cualquier persona registrada. Su **tipo de cliente** son los papeles que tiene:
propietario, arrendatario o codeudor. Al registrarlo se elige uno; los demás se agregan al
editarlo o, automáticamente, al asociarlo a un inmueble o a un contrato.

| Acción | Cómo |
| --- | --- |
| Registrar | «Registrar cliente»: nombre, tipo y número de identificación, teléfono, correo, dirección y tipo de cliente. La identificación no puede repetirse; si ya existe, el sistema lo informa y puede abrir la persona existente. |
| Buscar | Por nombre o identificación (sin importar mayúsculas ni tildes) y por papel con los segmentos Todos / Arrendatarios / Propietarios / Codeudores. |
| Ver | Datos, papeles, cuenta bancaria, usuario del sistema, inmuebles de los que es propietario y contratos separados por papel (propietario, arrendatario, codeudor), con enlaces. |
| Modificar | «Editar»: datos de contacto, papeles y cuenta bancaria. No se puede quitar un papel con inmuebles o contratos vinculados. |
| Eliminar | Solo si no tiene inmuebles, contratos ni cuenta de usuario; el mensaje indica qué lo impide. Lo eliminado va a la papelera: el Administrador de Sistemas puede restaurarlo. |

## Propietarios

- Registrar un propietario exige dirección, teléfono, correo y cuenta bancaria (banco con
  sugerencias, tipo y número). En las listas el número se muestra enmascarado (•••• 4902).
- La lista muestra solo personas con papel propietario, con la cuenta bancaria y el chip
  «N inmuebles» / «Sin inmuebles»; se filtra por nombre, identificación o correo.
- Un propietario con inmuebles **no se puede eliminar**: primero reasigne o elimine sus
  inmuebles.
- Quien se asocia como propietario desde un inmueble aparece aquí automáticamente.

## Codeudores

- Se registran, modifican y eliminan con las mismas reglas que los clientes y quedan con el
  papel codeudor.
- Filtre por identificación o por número de contrato para ver los codeudores de un contrato.
- Desde el formulario o el detalle de un contrato se busca un codeudor por identificación o se
  registra en el momento (nombre, teléfono y correo).

## Inmuebles

Menú **Inmuebles** (Asesor y Administrativo consultan, registran y editan;
solo Administrativo elimina).

### Consultar

- La lista muestra matrícula, dirección y ciudad, propietarios (enlace a su ficha), canon
  mensual en pesos, estado (Disponible / Ocupado), los contratos de servicios públicos y el
  enlace «Contratos (N)» que abre la lista de contratos del inmueble.
- Filtre por **estado**, **ciudad** (no importan mayúsculas ni tildes), **propietario** (busque
  por identificación en el selector) o escriba parte de la **dirección o matrícula** en «Buscar».
- Las tarjetas superiores muestran el total de inmuebles, los ocupados y los disponibles.

### Registrar

1. Pulse **Registrar inmueble**. Se abre un panel a la derecha (en el celular ocupa toda la pantalla).
2. **Identificación y localización:** dirección completa (obligatoria), ciudad (con sugerencias)
   y matrícula inmobiliaria.
3. **Canon y titularidad:** busque al propietario por identificación. Si no existe, pulse
   «Registrar nueva persona», complete nombre, teléfono y correo y quedará creado como
   propietario. Puede agregar varios propietarios. Escriba el canon en pesos (por ejemplo
   `1.500.000`) y marque el estado de ocupación.
4. **Cuentas de servicios públicos:** «Agregar servicio» por cada contrato (tipo, proveedor con
   sugerencias y número de contrato, obligatorio). «Quitar» elimina la fila.
5. **Guardar inmueble.** La fila aparece de inmediato en la lista.

### Modificar y eliminar

«Editar» permite cambiar cualquier dato, quitar o agregar propietarios y servicios. Quitar a un
propietario del inmueble **no** le quita su papel en Clientes; ese papel se retira desde su
ficha cuando ya no posea inmuebles. Un inmueble con contratos no se puede eliminar: el sistema
indica cuántos tiene.

## Contratos

Menú **Contratos** (Asesor y Administrativo consultan, registran y editan; solo
Administrativo elimina).

### Consultar

- Pestañas **Todos / Vigentes / Por vencer / Finalizados** («Por vencer»: terminan en menos de
  60 días). Cada fila muestra número y vigencia con los días restantes, inmueble, partes,
  codeudores, canon y estado.
- Filtros: texto (dirección del inmueble o nombre de una parte), **vigente desde / hasta** (se
  listan los contratos cuya vigencia se cruza con ese rango, incluidos los indefinidos), tipo,
  inmueble, propietario y arrendatario.

### Registrar

1. Pulse **Nuevo contrato**.
2. **Datos del contrato:** tipo, canon pactado, fecha de inicio (obligatoria) y fecha de fin
   (vacía = indefinido). Busque el inmueble por dirección o matrícula y pulse «Seleccionar»: sus
   propietarios quedan precargados como parte del contrato.
3. **Partes:** ajuste los propietarios si hace falta, busque al arrendatario por identificación
   (o regístrelo en el momento) y agregue hasta diez codeudores. Una misma persona no puede ser
   arrendataria y codeudora del mismo contrato. Cada parte recibe automáticamente su papel en
   Clientes.
4. **Condiciones y texto:** condiciones resumidas y el texto completo que se imprimirá.
5. **Guardar contrato.** Se abre el detalle con el recordatorio de revisar el estado de
   ocupación del inmueble: el sistema no lo cambia solo.

### Detalle, codeudores e impresión en PDF

- El detalle muestra inmueble, vigencia con días restantes, canon, condiciones, propietarios,
  arrendatario y codeudores con enlaces a sus fichas.
- **Asociar codeudor** busca o registra una persona y la vincula sin editar el resto del
  contrato; «Quitar» la desvincula.
- **Imprimir / guardar PDF** abre el diálogo de impresión del navegador con una vista limpia
  (encabezado de APHIA, partes y texto completo). Elija «Guardar como PDF» como destino en
  Chrome, Firefox o Safari. El botón se desactiva si el contrato no tiene texto completo.

### Modificar y eliminar

«Editar» permite cambiar cualquier dato y reemplaza las partes. Un contrato con registros
financieros o archivos asociados no se puede modificar ni eliminar: el mensaje indica cuántos
tiene. Los contratos, inmuebles y personas eliminados van a la papelera (ver «Papelera»).

## Usuarios (Administrador de Sistemas)

- «Registrar usuario»: nombre de usuario (minúsculas, único), nombre, identificación, correo,
  contraseña (con letra y dígito y el largo mínimo de la política; 8 por defecto) y rol. Si la
  identificación ya pertenece a un cliente, la cuenta se vincula a esa persona.
- Cada cuenta bloqueada aparece con una alerta y el botón «Desbloquear». El conmutador
  Activo/Inactivo impide iniciar sesión sin borrar la cuenta.
- «Editar» cambia nombre, identificación, correo, rol, estado y, si se indica, la contraseña.
  Cambiar el rol o la contraseña, o desactivar la cuenta, cierra de inmediato las sesiones
  abiertas de esa persona. La contraseña propia no se cambia aquí, sino con «Cambiar
  contraseña» (icono de llave).
- **Clave** genera una clave temporal: aparece una sola vez en el aviso verde; entréguela por un
  canal seguro. La cuenta se desbloquea, sus sesiones se cierran y, al entrar, se le pide
  cambiarla. La insignia «Clave temporal» indica que aún no la cambia.
- **Sesiones** cierra las sesiones abiertas de esa persona (por ejemplo, si perdió el equipo).
- No se puede eliminar, desactivar ni degradar al último administrador activo, ni eliminar,
  desactivar, restablecer la clave o cerrar las sesiones de la cuenta propia.

## Estado del sistema y respaldos (Administrador de Sistemas)

- **Sistema** es la pantalla de inicio del Administrador de Sistemas: versión y entorno de la
  API, si la base de datos responde (y en cuántos milisegundos), migraciones aplicadas, conteo
  de registros, tamaño de la base y último respaldo exitoso. «Actualizar» vuelve a consultar.
- Si no hay un respaldo exitoso en las últimas 26 horas aparece un aviso: revise la tarea
  programada del servidor.
- **Solicitar respaldo ahora** pide una copia adicional; el servidor la ejecuta en los minutos
  siguientes y el historial muestra su estado (Solicitado, En curso, Completado o Fallido),
  archivo, tamaño y si hubo copia externa. Los respaldos se restauran en el servidor, no desde
  la web.

## Auditoría (Administrador de Sistemas)

- Lista quién inició sesión (y los intentos fallidos y bloqueos) y quién creó, modificó,
  eliminó o restauró cada registro, con fecha y hora de Colombia.
- Filtros por usuario, acción, tipo de registro y rango de fechas (días de Colombia).
- Los intentos con un usuario inexistente o una cuenta inactiva, y los que llegan mientras la
  cuenta está bloqueada, no se guardan aquí (solo en los registros del servidor): así nadie
  puede llenar la auditoría probando usuarios. El bloqueo sí queda registrado.
- No guarda contraseñas ni los datos de los formularios; para ver el registro use su número.

## Catálogos (Administrador de Sistemas)

- Mantiene los valores de las listas: tipos de identificación, de contrato, de cuenta bancaria y
  de servicio público (con código), y ciudades, bancos y proveedores (solo nombre).
- «Agregar» crea un valor; «Renombrar» corrige el nombre (el código no cambia); «Eliminar» solo
  está disponible si ningún registro lo usa (columna «En uso»).
- Papeles, roles, estados de ocupación y monedas no se editan: la aplicación depende de ellos.

## Configuración (Administrador de Sistemas)

- **Política de seguridad:** intentos antes del bloqueo (3–10), duración del bloqueo (5–1440
  minutos), vigencia de la sesión (1–24 horas) y largo mínimo de la contraseña (8–64). Los
  cambios rigen desde el siguiente inicio de sesión.
- **Datos de la empresa:** razón social, NIT, dirección, ciudad, teléfono y correo. Aparecen en
  la impresión de los contratos y en el pie de página. El logotipo no se puede cambiar desde
  la aplicación.

## Papelera (Administrador de Sistemas)

- Guarda las personas, inmuebles y contratos que se eliminan, con quién y cuándo los eliminó.
- **Restaurar** los registra de nuevo con otro número. No es posible si, por ejemplo, la
  identificación ya se registró otra vez o el inmueble del contrato ya no existe; el mensaje lo
  indica y el registro sigue en la papelera.
- **Eliminar** los borra definitivamente. Contienen datos personales: vacíe la papelera de lo que
  ya no se necesite.

## Mensajes de error frecuentes

| Mensaje | Qué hacer |
| --- | --- |
| «Usuario o contraseña incorrectos.» | Revise los datos; tras tres fallos la cuenta se bloquea 15 minutos. |
| «La cuenta está bloqueada. Intente de nuevo en N minutos.» | Espere o pida el desbloqueo al Administrador de Sistemas. |
| «Inicie sesión para continuar.» | La sesión expiró (8 horas por defecto) o se cerró en otra pestaña. |
| «Su sesión se cerró. Inicie sesión de nuevo.» | El Administrador de Sistemas cerró sus sesiones, cambió su rol o su contraseña, o usted la cambió en otro equipo. |
| «Debe cambiar su contraseña antes de continuar.» | Tiene una clave temporal: cámbiela en la pantalla que se abre. |
| «La clave debe tener al menos N caracteres.» | La política de seguridad exige ese largo mínimo. |
| «No se puede restaurar: …» | El motivo indica qué falta (p. ej. el inmueble del contrato); el registro sigue en la papelera. |
| «No se puede eliminar: lo usan N registro(s).» (catálogos) | Renombre el valor en lugar de eliminarlo. |
| «Ya hay un respaldo solicitado o en curso.» | Espere a que termine el anterior. |
| «Ya existe una persona con esa identificación.» | Búsquela en Clientes y edítela o agréguele el papel que falta. |
| «No se puede eliminar…» (persona, inmueble, contrato) | El registro tiene vínculos; elimine o reasigne primero lo que indica el mensaje. |
| «No se puede quitar el papel…» | La persona tiene inmuebles o contratos con ese papel. |
| «Ingrese la dirección del inmueble.» / «Asocie al menos un propietario.» | Complete los datos obligatorios del inmueble. |
| «Ingrese el canon en pesos, con máximo dos decimales.» | Use solo dígitos, puntos de miles y coma decimal (`1.500.000,50`). |
| «La fecha de fin no puede ser anterior a la de inicio.» | Corrija las fechas o deje la de fin vacía. |
| «El arrendatario no puede ser también codeudor del contrato.» | Quite a esa persona de una de las dos listas. |
| «El inmueble no tiene propietarios registrados.» | Asócielos en Inmuebles o indíquelos en el contrato. |
| «No se puede modificar ni eliminar el contrato: tiene N registro(s)…» | Elimine primero esos registros o archivos. |
| «Código de soporte: …» | Acompaña a los errores de la API; cítelo al pedir ayuda. |
| «API sin conexión» (barra lateral) | El servidor no responde; espere y, si persiste, avise a soporte. |

## Navegadores y dispositivos

Funciona en las versiones vigentes de Chrome, Firefox y Safari, en computador, tableta y
celular. En pantallas angostas las tablas se desplazan dentro de su recuadro, los formularios
ocupan toda la pantalla y la búsqueda global se oculta (cada módulo conserva su buscador). Para
guardar un contrato en PDF use el diálogo de impresión del navegador.

## Soporte

Contacte al Administrador de Sistemas de APHIA. Indique qué intentaba hacer, el mensaje
recibido y, si aparece, el código de soporte. Los datos de los clientes son confidenciales: no
los comparta fuera de la empresa.
