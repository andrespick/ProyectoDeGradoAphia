"""Autenticación y autorización por roles.

ESTADO ACTUAL: NO HAY AUTENTICACIÓN DE PRODUCCIÓN.

Solo existe ``AUTH_MODE=development``: entrega un usuario ficticio con rol ``admin``
y únicamente cuando ``APP_ENV`` es ``development`` o ``test``. En cualquier otro caso
los endpoints protegidos responden 401. La autenticación real (proveedor de identidad,
sesiones o JWT) es una tarea pendiente documentada en docs/seguridad/.
"""
