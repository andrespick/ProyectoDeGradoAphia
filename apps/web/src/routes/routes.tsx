import type { RouteObject } from "react-router";

import { GESTION_USUARIOS, LECTURA } from "../features/auth/roles";
import { MainLayout } from "../layouts/MainLayout";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { UsuarioFormPage } from "../pages/UsuarioFormPage";
import { UsuariosPage } from "../pages/UsuariosPage";
import { ProtectedRoute } from "./ProtectedRoute";

export const routes: RouteObject[] = [
  {
    element: <MainLayout />,
    children: [
      { path: "login", element: <LoginPage /> },
      {
        element: <ProtectedRoute roles={LECTURA} />,
        children: [{ index: true, element: <HomePage /> }],
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
