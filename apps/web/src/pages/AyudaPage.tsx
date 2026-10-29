import { CircleHelp } from "lucide-react";
import { useEffect } from "react";
import { Link, useLocation } from "react-router";

// Espejo de docs/manual-usuario.md: al cambiar una pantalla, actualice ambos.
const SECCIONES = [
  { id: "inicio-de-sesion", titulo: "Inicio de sesión y bloqueo" },
  { id: "navegacion", titulo: "Navegación" },
  { id: "clientes", titulo: "Clientes" },
  { id: "propietarios", titulo: "Propietarios" },
  { id: "codeudores", titulo: "Codeudores" },
  { id: "inmuebles", titulo: "Inmuebles" },
  { id: "contratos", titulo: "Contratos" },
  { id: "usuarios", titulo: "Usuarios" },
  { id: "sistema", titulo: "Estado del sistema y respaldos" },
  { id: "auditoria", titulo: "Auditoría" },
  { id: "catalogos", titulo: "Catálogos" },
  { id: "configuracion", titulo: "Configuración" },
  { id: "papelera", titulo: "Papelera" },
  { id: "mensajes-de-error", titulo: "Mensajes de error" },
  { id: "navegadores-y-dispositivos", titulo: "Navegadores y dispositivos" },
  { id: "soporte", titulo: "Soporte" },
] as const;

export function AyudaPage() {
  const { hash } = useLocation();

  useEffect(() => {
    const id = hash.replace("#", "");
    const destino = id ? document.getElementById(id) : null;
    if (destino) {
      destino.scrollIntoView({ block: "start" });
      destino.focus({ preventScroll: true });
    } else {
      window.scrollTo(0, 0);
    }
  }, [hash]);

  return (
    <article className="ayuda">
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <CircleHelp size={20} />
          </span>
          <div>
            <h1>Ayuda de APHIA</h1>
            <p>Guía breve de cada módulo. La versión completa está en el manual de usuario del proyecto.</p>
          </div>
        </div>
      </header>

      <nav className="card ayuda-indice" aria-label="Índice de la ayuda">
        <ol>
          {SECCIONES.map((s) => (
            <li key={s.id}>
              <Link to={`/ayuda#${s.id}`}>{s.titulo}</Link>
            </li>
          ))}
        </ol>
      </nav>

      <Seccion id="inicio-de-sesion" titulo="Inicio de sesión y bloqueo">
        <p>
          Ingrese con el usuario y la contraseña que le asignó el Administrador de Sistemas. «Recordarme en este equipo»
          mantiene la sesión al cerrar la pestaña; no lo use en equipos compartidos. La sesión dura 8 horas (valor por
          defecto de la política de seguridad).
        </p>
        <ul>
          <li>
            Tras <strong>3 intentos fallidos</strong> la cuenta se bloquea <strong>15 minutos</strong> (valores por defecto; la
            pantalla de inicio de sesión muestra los vigentes). Espere ese tiempo o pida al Administrador de Sistemas que la
            desbloquee desde Usuarios.
          </li>
          <li>
            ¿Olvidó su contraseña? No hay recuperación por correo: el Administrador de Sistemas le genera una clave temporal
            desde Usuarios y, al entrar con ella, la aplicación le pide cambiarla.
          </li>
          <li>
            <strong>Cambiar contraseña:</strong> icono de llave junto a su nombre en la barra superior. Al cambiarla se
            cierran sus sesiones en otros equipos.
          </li>
          <li>
            Al entrar, cada persona llega siempre a su pantalla de inicio (Sistema para el Administrador de Sistemas,
            Inicio para los demás), sin importar qué pantalla estaba abierta antes. Si el Administrador de Sistemas
            cierra sus sesiones, cambia su rol o desactiva su cuenta, la sesión termina de inmediato.
          </li>
        </ul>
        <p>
          Roles: <strong>Administrador de Sistemas</strong> (solo la gestión del sistema: estado y respaldos, usuarios y
          contraseñas, auditoría, catálogos, configuración y papelera; no ve clientes, inmuebles ni contratos),{" "}
          <strong>Administrativo</strong> (crear, editar y eliminar en los módulos de negocio) y <strong>Asesor</strong>{" "}
          (crear y editar; no elimina).
        </p>
      </Seccion>

      <Seccion id="navegacion" titulo="Navegación">
        <ul>
          <li>La barra lateral lleva a Inicio, Clientes, Propietarios, Codeudores, Inmuebles, Contratos y Ayuda; el Administrador de Sistemas ve Sistema, Usuarios, Auditoría, Catálogos, Configuración, Papelera y Ayuda.</li>
          <li>En tabletas la barra se reduce a iconos; en el celular se abre con el botón «Abrir menú».</li>
          <li>La caja «Buscar inmueble, cliente, contrato…» de la barra superior muestra hasta cinco resultados por grupo. Enter abre el primero y Escape cierra la lista.</li>
          <li>El tablero de Inicio resume inmuebles, clientes, contratos vigentes y vencimientos próximos; cada tarjeta abre su módulo.</li>
          <li>Cada lista comparte la misma estructura: cabecera con «Registrar…», indicadores, filtros, tabla y paginación («Mostrando a–b de N», tamaño de página 10/20/50).</li>
        </ul>
      </Seccion>

      <Seccion id="clientes" titulo="Clientes">
        <p>
          Un cliente es cualquier persona registrada. Su <strong>tipo de cliente</strong> son los papeles que tiene:
          propietario, arrendatario o codeudor. Al registrarlo elige uno; los demás se agregan editándolo o,
          automáticamente, al asociarlo a un inmueble o a un contrato.
        </p>
        <ul>
          <li><strong>Registrar:</strong> nombre, tipo y número de identificación, teléfono, correo, dirección y tipo de cliente. La identificación no puede repetirse: si ya existe, el sistema lo informa.</li>
          <li><strong>Buscar:</strong> por nombre o identificación (sin importar mayúsculas ni tildes) y por papel con los segmentos Todos / Arrendatarios / Propietarios / Codeudores.</li>
          <li><strong>Ver:</strong> datos, papeles, cuenta bancaria, usuario del sistema, inmuebles de los que es propietario y contratos separados por papel.</li>
          <li><strong>Modificar:</strong> datos de contacto, papeles y cuenta bancaria. No se puede quitar un papel que tenga inmuebles o contratos vinculados.</li>
          <li><strong>Eliminar:</strong> solo si no tiene inmuebles, contratos ni cuenta de usuario; el mensaje indica qué lo impide.</li>
        </ul>
      </Seccion>

      <Seccion id="propietarios" titulo="Propietarios">
        <ul>
          <li>Registrar un propietario exige dirección, teléfono, correo y cuenta bancaria (banco con sugerencias, tipo y número). El número se muestra enmascarado (•••• 4902).</li>
          <li>La lista muestra solo personas con papel propietario, con la cuenta bancaria y el chip «N inmuebles» / «Sin inmuebles»; se filtra por nombre, identificación o correo.</li>
          <li>Un propietario con inmuebles no se puede eliminar: primero reasigne o elimine sus inmuebles.</li>
          <li>Quien se asocia como propietario desde un inmueble aparece aquí automáticamente.</li>
        </ul>
      </Seccion>

      <Seccion id="codeudores" titulo="Codeudores">
        <ul>
          <li>Se registran, modifican y eliminan con las mismas reglas que los clientes; quedan con el papel codeudor.</li>
          <li>Filtre por identificación o por número de contrato para ver los codeudores de un contrato.</li>
          <li>Desde el formulario o el detalle de un contrato puede buscar un codeudor existente por identificación o registrarlo en el momento.</li>
        </ul>
      </Seccion>

      <Seccion id="inmuebles" titulo="Inmuebles">
        <ul>
          <li><strong>Registrar inmueble</strong> abre un panel lateral con tres pasos: identificación y localización (dirección obligatoria, ciudad con sugerencias, matrícula), canon y titularidad (propietarios, canon en pesos, estado Disponible/Ocupado) y cuentas de servicios públicos (tipo, proveedor, número de contrato).</li>
          <li>Si el propietario no existe, «Registrar nueva persona» lo crea desde el selector con nombre, teléfono y correo.</li>
          <li>Filtre por estado, ciudad, propietario o texto (dirección o matrícula). Los filtros activos aparecen como fichas; «Restablecer filtros» los quita.</li>
          <li>Quitar a un propietario del inmueble no le quita su papel; ese papel se retira desde su ficha cuando ya no posea inmuebles.</li>
          <li>Un inmueble con contratos no se puede eliminar; el mensaje indica cuántos tiene.</li>
        </ul>
      </Seccion>

      <Seccion id="contratos" titulo="Contratos">
        <ul>
          <li>Pestañas Todos / Vigentes / Por vencer (terminan en menos de 60 días) / Finalizados; filtros por texto, vigencia desde/hasta (contratos cuya vigencia se cruza con el rango), tipo, inmueble, propietario y arrendatario.</li>
          <li><strong>Nuevo contrato:</strong> tipo, canon, fechas (fin vacío = indefinido), inmueble (sus propietarios se precargan), arrendatario, hasta diez codeudores, condiciones y texto completo. El arrendatario no puede ser codeudor del mismo contrato.</li>
          <li>Al guardar se abre el detalle con el recordatorio de revisar el estado de ocupación del inmueble: el sistema no lo cambia solo.</li>
          <li><strong>Asociar codeudor</strong> y «Quitar» en el detalle cambian solo los codeudores.</li>
          <li><strong>Imprimir / guardar PDF</strong> abre el diálogo de impresión con una vista limpia; elija «Guardar como PDF». Se desactiva si el contrato no tiene texto.</li>
          <li>Un contrato con registros financieros o archivos asociados no se puede modificar ni eliminar.</li>
          <li>Las personas, inmuebles y contratos eliminados van a la papelera; el Administrador de Sistemas puede restaurarlos.</li>
        </ul>
      </Seccion>

      <Seccion id="usuarios" titulo="Usuarios">
        <ul>
          <li>Solo el Administrador de Sistemas gestiona usuarios: nombre de usuario (minúsculas, único), nombre, identificación, correo, contraseña (con letra y dígito y el largo mínimo de la política; 8 por defecto) y rol.</li>
          <li>Cada cuenta bloqueada aparece con una alerta y el botón «Desbloquear». El conmutador Activo/Inactivo impide iniciar sesión sin borrar la cuenta.</li>
          <li>Cambiar el rol o la contraseña, o desactivar la cuenta, cierra de inmediato las sesiones abiertas de esa persona. La contraseña propia se cambia con «Cambiar contraseña» (icono de llave), no aquí.</li>
          <li><strong>Clave</strong> genera una clave temporal que aparece una sola vez: entréguela por un canal seguro. La persona deberá cambiarla al entrar; mientras tanto la tabla muestra «Clave temporal».</li>
          <li><strong>Sesiones</strong> cierra las sesiones abiertas de esa persona (por ejemplo, si perdió el equipo).</li>
          <li>No se puede eliminar, desactivar ni degradar al último administrador activo, ni eliminar, desactivar, restablecer la clave o cerrar las sesiones de la cuenta propia.</li>
        </ul>
      </Seccion>

      <Seccion id="sistema" titulo="Estado del sistema y respaldos">
        <ul>
          <li>Es la pantalla de inicio del Administrador de Sistemas: versión y entorno de la API, si la base de datos responde, migraciones aplicadas, conteo de registros, tamaño de la base y último respaldo exitoso.</li>
          <li>Si no hay un respaldo exitoso en las últimas 26 horas aparece un aviso: revise la tarea programada del servidor.</li>
          <li><strong>Solicitar respaldo ahora</strong> pide una copia adicional que el servidor ejecuta en los minutos siguientes; el historial muestra su estado, archivo, tamaño y si hubo copia externa. Los respaldos se restauran en el servidor, no desde la web.</li>
        </ul>
      </Seccion>

      <Seccion id="auditoria" titulo="Auditoría">
        <ul>
          <li>Lista los inicios de sesión, intentos fallidos y bloqueos, y quién creó, modificó, eliminó o restauró cada registro, con fecha y hora de Colombia.</li>
          <li>Filtre por usuario, acción, tipo de registro y rango de fechas (días de Colombia).</li>
          <li>Los intentos con un usuario inexistente o una cuenta inactiva, y los que llegan con la cuenta bloqueada, no se guardan aquí (solo en los registros del servidor); el bloqueo sí queda registrado.</li>
          <li>No guarda contraseñas ni los datos de los formularios.</li>
        </ul>
      </Seccion>

      <Seccion id="catalogos" titulo="Catálogos">
        <ul>
          <li>Tipos de identificación, de contrato, de cuenta bancaria y de servicio público (con código), y ciudades, bancos y proveedores (solo nombre).</li>
          <li>«Agregar» crea un valor, «Renombrar» corrige el nombre y «Eliminar» solo está disponible si ningún registro lo usa (columna «En uso»).</li>
          <li>Papeles, roles, estados de ocupación y monedas no se editan: la aplicación depende de ellos.</li>
        </ul>
      </Seccion>

      <Seccion id="configuracion" titulo="Configuración">
        <ul>
          <li><strong>Política de seguridad:</strong> intentos antes del bloqueo (3–10), duración del bloqueo (5–1440 minutos), vigencia de la sesión (1–24 horas) y largo mínimo de la contraseña (8–64). Rige desde el siguiente inicio de sesión.</li>
          <li><strong>Datos de la empresa:</strong> razón social, NIT, dirección, ciudad, teléfono y correo; aparecen al imprimir contratos y en el pie de página. El logotipo no se puede cambiar desde la aplicación.</li>
        </ul>
      </Seccion>

      <Seccion id="papelera" titulo="Papelera">
        <ul>
          <li>Guarda las personas, inmuebles y contratos eliminados, con quién y cuándo los eliminó.</li>
          <li><strong>Restaurar</strong> los registra de nuevo con otro número. Si no es posible (por ejemplo, la identificación ya se registró otra vez o el inmueble del contrato ya no existe), el mensaje lo indica y el registro sigue en la papelera.</li>
          <li><strong>Eliminar</strong> los borra definitivamente. Contienen datos personales: vacíe lo que ya no se necesite.</li>
        </ul>
      </Seccion>

      <Seccion id="mensajes-de-error" titulo="Mensajes de error">
        <ul>
          <li><strong>«Usuario o contraseña incorrectos.»</strong> Revise los datos; tras tres fallos la cuenta se bloquea 15 minutos.</li>
          <li><strong>«Ya existe una persona con esa identificación.»</strong> Búsquela en Clientes y edítela o agréguele el papel que falta.</li>
          <li><strong>«No se puede eliminar…»</strong> El registro tiene vínculos (inmuebles, contratos, cuenta de usuario, registros financieros). Elimine o reasigne primero lo que indica el mensaje.</li>
          <li><strong>«Inicie sesión para continuar.»</strong> La sesión expiró (8 horas por defecto) o se cerró en otra pestaña.</li>
          <li><strong>«Su sesión se cerró. Inicie sesión de nuevo.»</strong> El Administrador de Sistemas cerró sus sesiones o cambió su rol o su contraseña, o usted la cambió en otro equipo.</li>
          <li><strong>«Debe cambiar su contraseña antes de continuar.»</strong> Tiene una clave temporal: cámbiela en la pantalla que se abre.</li>
          <li><strong>«No se puede restaurar: …»</strong> El motivo indica qué falta; el registro sigue en la papelera.</li>
          <li><strong>«Código de soporte: …»</strong> Acompaña a los errores de la API; cítelo al pedir ayuda para localizar el registro en los logs.</li>
          <li><strong>«API sin conexión» en la barra lateral.</strong> El servidor no responde; espere un momento y, si persiste, avise a soporte.</li>
        </ul>
      </Seccion>

      <Seccion id="navegadores-y-dispositivos" titulo="Navegadores y dispositivos">
        <p>
          Funciona en las versiones vigentes de Chrome, Firefox y Safari, en computador, tableta y celular. En pantallas
          angostas las tablas se desplazan dentro de su recuadro y los formularios ocupan toda la pantalla. Para guardar
          un contrato en PDF use el diálogo de impresión del navegador.
        </p>
      </Seccion>

      <Seccion id="soporte" titulo="Soporte">
        <p>
          Contacte al Administrador de Sistemas de APHIA. Indique qué intentaba hacer, el mensaje recibido y, si aparece,
          el código de soporte. Los datos de los clientes son confidenciales: no los comparta fuera de la empresa.
        </p>
      </Seccion>
    </article>
  );
}

function Seccion({ id, titulo, children }: { id: string; titulo: string; children: React.ReactNode }) {
  return (
    <section className="card ayuda-seccion" id={id} tabIndex={-1} aria-labelledby={`${id}-titulo`}>
      <h2 id={`${id}-titulo`}>{titulo}</h2>
      {children}
    </section>
  );
}
