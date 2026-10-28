"""Personas: clientes, propietarios y codeudores sobre ``person`` y sus tablas hijas.

Una fila en ``person`` por identificación. Los papeles (propietario, arrendatario, codeudor)
viven en ``person_party_role``; una persona puede tener varios a la vez. Los módulos
``clientes``, ``propietarios`` y ``codeudores`` son routers delgados sobre este servicio.
"""
