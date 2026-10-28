import type { RouteObject } from "react-router";

import { GESTION_USUARIOS, LECTURA } from "../features/auth/roles";
import { type Modulo, MODULOS } from "../features/personas/modulos";
import { MainLayout } from "../layouts/MainLayout";
import { ContratoDetallePage } from "../pages/ContratoDetallePage";
import { ContratoFormPage } from "../pages/ContratoFormPage";
import { ContratosPage } from "../pages/ContratosPage";
import { HomePage } from "../pages/HomePage";
import { InmuebleFormPage } from "../pages/InmuebleFormPage";
import { InmueblesPage } from "../pages/InmueblesPage";
import { LoginPage } from "../pages/LoginPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { PersonaDetallePage } from "../pages/PersonaDetallePage";
import { PersonaFormPage } from "../pages/PersonaFormPage";
import { PersonasListPage } from "../pages/PersonasListPage";
import { UsuarioFormPage } from "../pages/UsuarioFormPage";
import { UsuariosPage } from "../pages/UsuariosPage";
import { ProtectedRoute } from "./ProtectedRoute";

function rutasDePersonas(modulo: Modulo): RouteObject[] {
  const base = MODULOS[modulo].ruta.slice(1);
  return [
    {
      path: base,
      element: <PersonasListPage modulo={modulo} />,
      children: [
        { path: "nuevo", element: <PersonaFormPage modulo={modulo} modo="crear" /> },
        { path: ":id/editar", element: <PersonaFormPage modulo={modulo} modo="editar" /> },
      ],
    },
    { path: `${base}/:id`, element: <PersonaDetallePage modulo={modulo} /> },
  ];
}

export const routes: RouteObject[] = [
  {
    element: <MainLayout />,
    children: [
      { path: "login", element: <LoginPage /> },
      {
        element: <ProtectedRoute roles={LECTURA} />,
        children: [
          { index: true, element: <HomePage /> },
          ...rutasDePersonas("clientes"),
          ...rutasDePersonas("propietarios"),
          ...rutasDePersonas("codeudores"),
          {
            path: "inmuebles",
            element: <InmueblesPage />,
            children: [
              { path: "nuevo", element: <InmuebleFormPage modo="crear" /> },
              { path: ":id/editar", element: <InmuebleFormPage modo="editar" /> },
            ],
          },
          { path: "contratos", element: <ContratosPage /> },
          { path: "contratos/nuevo", element: <ContratoFormPage modo="crear" /> },
          { path: "contratos/:id", element: <ContratoDetallePage /> },
          { path: "contratos/:id/editar", element: <ContratoFormPage modo="editar" /> },
        ],
      },
      {
        element: <ProtectedRoute roles={GESTION_USUARIOS} />,
        children: [
          {
            path: "usuarios",
            element: <UsuariosPage />,
            children: [
              { path: "nuevo", element: <UsuarioFormPage modo="crear" /> },
              { path: ":id/editar", element: <UsuarioFormPage modo="editar" /> },
            ],
          },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
