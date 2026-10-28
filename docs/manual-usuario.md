# Manual de usuario de APHIA

Guía para el personal de APHIA S.A.S. El mismo contenido está disponible dentro de la
aplicación en **Ayuda** (`/ayuda`), sin necesidad de iniciar sesión; cada pantalla tiene un
enlace «Ayuda» que lleva a su sección. Al cambiar una pantalla, actualice este manual y la
página de ayuda.

## Roles

| Rol | Qué puede hacer |
| --- | --- |
| Administrador de Sistemas | Todo, incluida la gestión de usuarios y el desbloqueo de cuentas |
| Administrativo | Consultar, registrar, modificar y eliminar clientes, propietarios, codeudores, inmuebles y contratos |
| Asesor | Consultar, registrar y modificar; **no** elimina |

## Inicio de sesión y bloqueo

1. Abra la aplicación e ingrese el usuario y la contraseña que le asignó el Administrador de
   Sistemas. «Recordarme en este equipo» mantiene la sesión al cerrar la pestaña; no lo use en
   equipos compartidos. La sesión dura 8 horas.
2. Tras **3 intentos fallidos** la cuenta queda bloqueada **15 minutos**. Espere o pida al
   Administrador de Sistemas que la desbloquee desde Usuarios. El mensaje indica los minutos
   que faltan.
3. No hay recuperación de contraseña por correo: el enlace «¿Olvidó su contraseña?» explica que
   el Administrador de Sistemas le asigna una nueva desde Usuarios.
4. Si la sesión expira, la aplicación vuelve al inicio de sesión y, al entrar, lo lleva a la
   pantalla donde estaba.

## Navegación

- Barra lateral: Inicio, Clientes, Propietarios, Codeudores, Inmuebles, Contratos, Usuarios
  (solo Administrador de Sistemas) y Ayuda; abajo, el estado del sistema y «Salir».
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
| Eliminar | Solo si no tiene inmuebles, contratos ni cuenta de usuario; el mensaje indica qué lo impide. |

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

Menú **Inmuebles** (todos los roles consultan; Asesor y Administrativo registran y editan;
solo Administrativo y Administrador de Sistemas eliminan).

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

Menú **Contratos** (todos los roles consultan; Asesor y Administrativo registran y editan; solo
Administrativo y Administrador de Sistemas eliminan).

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
tiene.

## Usuarios (Administrador de Sistemas)

- «Registrar usuario»: nombre de usuario (minúsculas, único), nombre, identificación, correo,
  contraseña (mínimo 8 caracteres con letra y dígito) y rol. Si la identificación ya pertenece
  a un cliente, la cuenta se vincula a esa persona.
- Cada cuenta bloqueada aparece con una alerta y el botón «Desbloquear». El conmutador
  Activo/Inactivo impide iniciar sesión sin borrar la cuenta.
- «Editar» cambia nombre, identificación, correo, rol, estado y, si se indica, la contraseña.
  Los cambios de rol aplican en el siguiente inicio de sesión del usuario.
- No se puede eliminar, desactivar ni degradar al último administrador activo, ni eliminar o
  desactivar la cuenta propia.

## Mensajes de error frecuentes

| Mensaje | Qué hacer |
| --- | --- |
| «Usuario o contraseña incorrectos.» | Revise los datos; tras tres fallos la cuenta se bloquea 15 minutos. |
| «La cuenta está bloqueada. Intente de nuevo en N minutos.» | Espere o pida el desbloqueo al Administrador de Sistemas. |
| «Inicie sesión para continuar.» | La sesión expiró (8 horas) o se cerró en otra pestaña. |
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
