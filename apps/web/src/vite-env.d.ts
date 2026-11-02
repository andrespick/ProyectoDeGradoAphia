/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base de la API, sin barra final. Ej.: http://localhost:8000 */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
