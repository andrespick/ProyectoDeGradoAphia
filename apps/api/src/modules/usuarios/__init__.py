"""Usuarios del sistema y sus roles (solo Administrador de Sistemas).

Una cuenta (``user_account``) pertenece a una persona (``person``): si ya existe una persona
con la misma identificación (por ejemplo un cliente), la cuenta se vincula a ella en lugar de
duplicarla. Al eliminar la cuenta, la persona se conserva.
"""
