"""Papelera de personas, inmuebles y contratos eliminados (tabla ``deleted_record``, 0013).

Al eliminar, el repositorio de cada módulo guarda en la misma transacción una instantánea con
los datos de su esquema de creación (``PersonaCreate``, ``InmuebleCreate``, ``ContratoCreate``)
y borra el registro como siempre. Restaurar vuelve a crearlo con el servicio de su módulo (mismas
validaciones) y le asigna un identificador nuevo; si ya no es posible (por ejemplo, el inmueble
de un contrato también se eliminó) responde 409 con el motivo. Solo el Administrador de
Sistemas la consulta, restaura o vacía.
"""
