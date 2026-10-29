"""Autenticación y autorización por roles.

Modos (``AUTH_MODE``):

- ``database`` (local, staging, producción): usuarios de MySQL (``user_account``) con
  contraseña PBKDF2-SHA256 (``passwords.py``) y token de sesión HMAC (``tokens.py``);
  bloqueo de 15 minutos tras 3 intentos fallidos (``service.py``).
- ``development``: usuario ficticio con roles ``admin_sistemas`` y ``administrativo``;
  solo pruebas unitarias.
- ``disabled``: todo endpoint protegido responde 401.

Los routers declaran roles con ``require_roles`` y los grupos de ``schemas.py``.
"""
