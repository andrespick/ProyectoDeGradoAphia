"""Autenticación y autorización por roles.

Modos (``AUTH_MODE``):

- ``development``: usuario ficticio con rol ``admin_sistemas``; solo en development/test.
- ``database``: usuarios de MySQL (``user_account``) con contraseña y token firmado
  (se implementa en la fase 1 del plan; ver docs/plan-de-implementacion.md).
- ``disabled``: todo endpoint protegido responde 401.

Los routers declaran roles con ``require_roles`` y los grupos de ``schemas.py``.
"""
