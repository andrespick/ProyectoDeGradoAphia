import type { RouteObject } from "react-router";

import { MainLayout } from "../layouts/MainLayout";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { PanelPage } from "../pages/PanelPage";
import { ProtectedRoute } from "./ProtectedRoute";

export const routes: RouteObject[] = [
  {
    element: <MainLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "login", element: <LoginPage /> },
      {
        element: <ProtectedRoute roles={["admin", "asesor"]} />,
        children: [{ path: "panel", element: <PanelPage /> }],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
