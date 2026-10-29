import { ListChecks, Pencil, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router";

import { AyudaLink } from "../components/AyudaLink";
import { Field } from "../components/Field";
import { Segmented } from "../components/Segmented";
import { CATALOGO_INICIAL, CATALOGOS } from "../features/administracion/etiquetas";
import {
  createItemCatalogo,
  deleteItemCatalogo,
  listItemsCatalogo,
  renameItemCatalogo,
} from "../services/administracionService";
import { errorMessage } from "../services/apiClient";
import { invalidateCatalogos } from "../services/catalogosService";
import type { CatalogoAdministrable, ItemCatalogo } from "../types/administracion";

export function CatalogosPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const actual = CATALOGOS.find((c) => c.value === searchParams.get("catalogo")) ?? CATALOGO_INICIAL;
  const [items, setItems] = useState<ItemCatalogo[] | null>(null);
  const [codigo, setCodigo] = useState("");
  const [nombre, setNombre] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const [ocupado, setOcupado] = useState(false);
  const enCurso = useRef(false); // el segundo clic de un doble clic llega antes de re-renderizar

  useEffect(() => {
    const controller = new AbortController();
    listItemsCatalogo(actual.value, controller.signal)
      .then(setItems)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(err));
      });
    return () => controller.abort();
  }, [actual.value, version]);

  const ejecutar = useCallback(async (accion: () => Promise<unknown>, exito: string) => {
    if (enCurso.current) return false;
    enCurso.current = true;
    setMensaje(null);
    setError(null);
    setOcupado(true);
    try {
      await accion();
      invalidateCatalogos(); // los formularios vuelven a pedir los catálogos
      setMensaje(exito);
      setVersion((v) => v + 1);
      return true;
    } catch (err) {
      setError(errorMessage(err));
      return false;
    } finally {
      enCurso.current = false;
      setOcupado(false);
    }
  }, []);

  function cambiarCatalogo(value: CatalogoAdministrable) {
    setItems(null); // tras agregar o renombrar se conserva la tabla mientras recarga
    setSearchParams({ catalogo: value });
    setMensaje(null);
    setError(null);
  }

  async function agregar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const datos = actual.conCodigo ? { codigo: codigo.trim(), nombre: nombre.trim() } : { nombre: nombre.trim() };
    if (await ejecutar(() => createItemCatalogo(actual.value, datos), `«${datos.nombre}» agregado.`)) {
      setCodigo("");
      setNombre("");
    }
  }

  function renombrar(item: ItemCatalogo) {
    const nuevo = window.prompt(`Nuevo nombre para «${item.nombre}»`, item.nombre)?.trim();
    if (!nuevo || nuevo === item.nombre) return;
    void ejecutar(() => renameItemCatalogo(actual.value, item.id, nuevo), `Renombrado a «${nuevo}».`);
  }

  function eliminar(item: ItemCatalogo) {
    if (!window.confirm(`¿Eliminar «${item.nombre}» del catálogo?`)) return;
    void ejecutar(() => deleteItemCatalogo(actual.value, item.id), `«${item.nombre}» eliminado.`);
  }

  return (
    <>
      <p className="breadcrumbs">
        <span>APHIA</span>
        <span>Sistema</span>
        <span>Catálogos</span>
      </p>
      <header className="page-header">
        <div className="page-header-title">
          <span className="icon-box" aria-hidden="true">
            <ListChecks size={20} />
          </span>
          <div>
            <h1>Catálogos</h1>
            <p>Valores que aparecen en las listas de los formularios. Un valor en uso se puede renombrar, no eliminar.</p>
          </div>
        </div>
        <div className="actions">
          <AyudaLink seccion="catalogos" etiqueta="los catálogos" />
        </div>
      </header>

      <div className="filters">
        <Segmented label="Catálogo" value={actual.value} options={CATALOGOS} onChange={cambiarCatalogo} />
      </div>

      {mensaje && (
        <p className="alert alert-success" role="status">
          {mensaje}
        </p>
      )}
      {error && (
        <p className="alert alert-error" role="alert">
          {error}
        </p>
      )}

      <section className="card" aria-labelledby="catalogo-titulo">
        <h2 id="catalogo-titulo">{actual.label}</h2>
        <form className="filters" onSubmit={(event) => void agregar(event)} aria-label={`Agregar a ${actual.label}`}>
          {actual.conCodigo && (
            <Field
              id="catalogo-codigo"
              label="Código"
              value={codigo}
              maxLength={30}
              hint="Letras, números o guion bajo"
              required
              onChange={(value) => setCodigo(value.toUpperCase())}
            />
          )}
          <Field
            id="catalogo-nombre"
            label="Nombre"
            value={nombre}
            maxLength={255}
            required
            className="filters-search"
            onChange={setNombre}
          />
          <button type="submit" disabled={ocupado || !nombre.trim() || (actual.conCodigo && !codigo.trim())}>
            <Plus size={16} aria-hidden="true" /> Agregar
          </button>
        </form>

        {items === null ? (
          <p className="muted" role="status">
            Cargando…
          </p>
        ) : items.length === 0 ? (
          <p className="empty-state">Este catálogo está vacío.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {actual.conCodigo && <th scope="col">Código</th>}
                  <th scope="col">Nombre</th>
                  <th scope="col">En uso</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    {actual.conCodigo && <td className="nowrap">{item.codigo}</td>}
                    <td>{item.nombre}</td>
                    <td className="num">{item.en_uso}</td>
                    <td>
                      <span className="row-actions">
                        <button
                          type="button"
                          className="secondary"
                          disabled={ocupado}
                          aria-label={`Renombrar ${item.nombre}`}
                          onClick={() => renombrar(item)}
                        >
                          <Pencil size={16} aria-hidden="true" /> Renombrar
                        </button>
                        <button
                          type="button"
                          className="danger"
                          aria-label={`Eliminar ${item.nombre}`}
                          disabled={ocupado || item.en_uso > 0}
                          title={item.en_uso > 0 ? "En uso: no se puede eliminar" : undefined}
                          onClick={() => eliminar(item)}
                        >
                          <Trash2 size={16} aria-hidden="true" /> Eliminar
                        </button>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
