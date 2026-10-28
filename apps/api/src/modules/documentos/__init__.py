"""Documentos (contratos, PDF, imágenes).

Los archivos viven en el servicio privado ``apps/files`` del VPS; MySQL guardará solo
metadatos y la referencia (``file_id``). Este módulo todavía no expone endpoints:
``ports.py`` define el contrato que implementará el adaptador hacia ese servicio.
Ver docs/arquitectura/README.md, sección "Documentos".
"""
