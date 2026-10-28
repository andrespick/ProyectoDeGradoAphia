import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter } from "react-router";
import { RouterProvider } from "react-router/dom";

import { AuthProvider } from "./features/auth/AuthProvider";
import { routes } from "./routes/routes";
import "./styles.css";

const container = document.getElementById("root");
if (!container) throw new Error("No se encontró el elemento #root.");

const router = createBrowserRouter(routes);

createRoot(container).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
);
