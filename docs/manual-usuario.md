# Manual de usuario de APHIA

> Borrador en construcción: cada fase del [plan de implementación](plan-de-implementacion.md)
> agrega la sección de su módulo. La versión completa (inicio de sesión, clientes, propietarios,
> codeudores, contratos, usuarios, mensajes de error y soporte) se cierra en la fase 5 y se
> publica también como ayuda en línea en `/ayuda`.

## Inmuebles

Menú **Inmuebles** (todos los roles pueden consultar; Asesor y Administrativo registran y
editan; solo Administrativo y Administrador de Sistemas eliminan).

### Consultar

- La lista muestra matrícula, dirección y ciudad, propietarios (enlace a su ficha), canon
  mensual en pesos, estado (Disponible / Ocupado) y los contratos de servicios públicos.
- Filtre por **estado**, **ciudad** (no importan mayúsculas ni tildes), **propietario** (busque
  por identificación en el selector) o escriba parte de la **dirección o matrícula** en «Buscar».
  Los filtros activos aparecen como fichas; «Restablecer filtros» los quita todos.
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

### Modificar

Pulse **Editar** en la fila. Puede cambiar cualquier dato, quitar o agregar propietarios y
servicios. Quitar a un propietario del inmueble **no** le quita su papel de propietario en
Clientes; ese papel se retira desde su ficha cuando ya no posea inmuebles.

### Eliminar

Pulse **Eliminar** y confirme. Un inmueble con contratos no se puede eliminar: el sistema indica
cuántos contratos tiene; elimínelos primero desde Contratos.

### Mensajes frecuentes

| Mensaje | Qué hacer |
| --- | --- |
| «Ingrese la dirección del inmueble.» | La dirección es obligatoria (mínimo 3 caracteres). |
| «Asocie al menos un propietario.» | Todo inmueble necesita un propietario; búsquelo o regístrelo en el selector. |
| «Ingrese el canon en pesos, con máximo dos decimales.» | Use solo dígitos, puntos de miles y coma decimal (`1.500.000,50`). |
| «No se puede eliminar el inmueble: tiene N contrato(s).» | Elimine o reasigne primero esos contratos. |
| «La persona N no existe.» | El propietario fue eliminado mientras editaba; vuelva a buscarlo. |

## Contratos

Menú **Contratos** (todos los roles consultan; Asesor y Administrativo registran y editan; solo
Administrativo y Administrador de Sistemas eliminan).

### Consultar

- Pestañas **Todos / Vigentes / Por vencer / Finalizados** («Por vencer»: terminan en menos de
  60 días). Cada fila muestra número y vigencia con los días restantes, inmueble, partes,
  codeudores, canon y estado.
- Filtros: texto (dirección del inmueble o nombre de una parte), **vigente desde / hasta** (se
  listan los contratos cuya vigencia se cruza con ese rango, incluidos los indefinidos), tipo,
  inmueble, propietario y arrendatario. Desde Inmuebles, el enlace «Contratos (N)» abre la lista
  filtrada por ese inmueble.
- La caja **Buscar inmueble, cliente, contrato…** de la barra superior muestra hasta cinco
  resultados por grupo; Enter abre el primero y Escape cierra la lista.

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

### Mensajes frecuentes

| Mensaje | Qué hacer |
| --- | --- |
| «Seleccione el inmueble del contrato.» | Busque el inmueble por dirección o matrícula y pulse «Seleccionar». |
| «La fecha de fin no puede ser anterior a la de inicio.» | Corrija las fechas o deje la de fin vacía. |
| «El arrendatario no puede ser también codeudor del contrato.» | Quite a esa persona de una de las dos listas. |
| «El inmueble no tiene propietarios registrados.» | Asócielos en Inmuebles o indíquelos en el contrato. |
| «No se puede modificar ni eliminar el contrato: tiene N registro(s) financiero(s)…» | Elimine primero esos registros o archivos. |
