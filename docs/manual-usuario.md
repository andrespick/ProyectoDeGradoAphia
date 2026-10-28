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
