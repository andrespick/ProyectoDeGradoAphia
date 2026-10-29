"""Bitácora de auditoría: quién inició sesión y quién creó, cambió o eliminó qué (tabla 0012).

Los routers registran cada escritura con ``Auditar`` (``modules.auth.dependencies``). El
registro es de mejor esfuerzo: si falla, se escribe un aviso en los logs y la operación ya
confirmada no se revierte. Nunca se guardan contraseñas, tokens ni datos del formulario.
"""
