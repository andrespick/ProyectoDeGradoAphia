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
          mantiene la sesión al cerrar la pestaña; no lo use en equipos compartidos. La sesión dura 8 horas.
        </p>
        <ul>
          <li>
            Tras <strong>3 intentos fallidos</strong> la cuenta se bloquea <strong>15 minutos</strong>. Espere ese tiempo o
            pida al Administrador de Sistemas que la desbloquee desde Usuarios.
          </li>
          <li>
            ¿Olvidó su contraseña? No hay recuperación por correo: el Administrador de Sistemas le asigna una nueva desde
            Usuarios.
          </li>
          <li>Si la sesión expira, la aplicación vuelve a la pantalla de inicio de sesión sin perder la ruta.</li>
        </ul>
        <p>
          Roles: <strong>Administrador de Sistemas</strong> (todo, incluida la gestión de usuarios),{" "}
          <strong>Administrativo</strong> (crear, editar y eliminar en los módulos de negocio) y <strong>Asesor</strong>{" "}
          (crear y editar; no elimina).
        </p>
      </Seccion>

      <Seccion id="navegacion" titulo="Navegación">
        <ul>
          <li>La barra lateral lleva a Inicio, Clientes, Propietarios, Codeudores, Inmuebles, Contratos, Usuarios (solo administradores) y Ayuda.</li>
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
        </ul>
      </Seccion>

      <Seccion id="usuarios" titulo="Usuarios">
        <ul>
          <li>Solo el Administrador de Sistemas gestiona usuarios: nombre de usuario (minúsculas, único), nombre, identificación, correo, contraseña (mínimo 8 caracteres con letra y dígito) y rol.</li>
          <li>Cada cuenta bloqueada aparece con una alerta y el botón «Desbloquear». El conmutador Activo/Inactivo impide iniciar sesión sin borrar la cuenta.</li>
          <li>No se puede eliminar, desactivar ni degradar al último administrador activo, ni eliminar o desactivar la cuenta propia.</li>
        </ul>
      </Seccion>

      <Seccion id="mensajes-de-error" titulo="Mensajes de error">
        <ul>
          <li><strong>«Usuario o contraseña incorrectos.»</strong> Revise los datos; tras tres fallos la cuenta se bloquea 15 minutos.</li>
          <li><strong>«Ya existe una persona con esa identificación.»</strong> Búsquela en Clientes y edítela o agréguele el papel que falta.</li>
          <li><strong>«No se puede eliminar…»</strong> El registro tiene vínculos (inmuebles, contratos, cuenta de usuario, registros financieros). Elimine o reasigne primero lo que indica el mensaje.</li>
          <li><strong>«Inicie sesión para continuar.»</strong> La sesión expiró (8 horas) o se cerró en otra pestaña.</li>
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
