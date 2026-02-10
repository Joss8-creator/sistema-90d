#!/usr/bin/env python3
"""
validadores.py - Validación de entradas para el Sistema 90D
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/validadores.py
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ErrorValidacion(Exception):
    """Excepción custom para errores de validación."""
    campo: str
    valor: any
    mensaje: str
    
    def __str__(self):
        return f"{self.campo}: {self.mensaje} (valor recibido: {self.valor})"

class ValidadorMetricas:
    """Valida datos de métricas antes de insertar en DB."""
    
    @staticmethod
    def validar_ingresos(valor: str) -> float:
        try:
            ingresos = float(valor)
        except (ValueError, TypeError):
            raise ErrorValidacion(campo='ingresos', valor=valor, mensaje='Debe ser un número válido')
        
        if ingresos > 1_000_000:
            raise ErrorValidacion(campo='ingresos', valor=valor, mensaje='Valor sospechosamente alto (>$1M). ¿Typo?')
        return ingresos
    
    @staticmethod
    def validar_tiempo(valor: str) -> float:
        try:
            horas = float(valor)
        except (ValueError, TypeError):
            raise ErrorValidacion(campo='tiempo_invertido', valor=valor, mensaje='Debe ser un número válido')
        
        if horas < 0:
            raise ErrorValidacion(campo='tiempo_invertido', valor=valor, mensaje='No puede ser negativo')
        if horas > 24:
            raise ErrorValidacion(campo='tiempo_invertido', valor=valor, mensaje='Máximo 24 horas/día. ¿Pusiste minutos en vez de horas?')
        return horas
    
    @staticmethod
    def validar_fecha(valor: str) -> str:
        try:
            fecha_dt = datetime.fromisoformat(valor)
        except ValueError:
            raise ErrorValidacion(campo='fecha', valor=valor, mensaje='Formato inválido. Usa YYYY-MM-DD')
        
        ahora = datetime.now()
        if fecha_dt > ahora:
            # Tolerancia de 1 hora por zona horaria
            if (fecha_dt - ahora).total_seconds() > 3600:
                raise ErrorValidacion(campo='fecha', valor=valor, mensaje='No puedes registrar métricas del futuro')
        
        return valor

    @staticmethod
    def validar_conversiones(valor: str) -> int:
        try:
            conversiones = int(valor)
        except (ValueError, TypeError):
            raise ErrorValidacion(campo='conversiones', valor=valor, mensaje='Debe ser un número entero')
        
        if conversiones < 0:
            raise ErrorValidacion(campo='conversiones', valor=valor, mensaje='No puede ser negativo')
        if conversiones > 10_000:
            raise ErrorValidacion(campo='conversiones', valor=valor, mensaje='Valor sospechosamente alto. ¿Typo?')
        return conversiones

class ValidadorProyectos:
    """Valida datos de proyectos."""
    
    @staticmethod
    def validar_nombre(valor: str) -> str:
        nombre = valor.strip()
        if not nombre:
            raise ErrorValidacion(campo='nombre', valor=valor, mensaje='El nombre no puede estar vacío')
        if len(nombre) > 100:
            raise ErrorValidacion(campo='nombre', valor=valor, mensaje='Máximo 100 caracteres')
        return nombre
    
    @staticmethod
    def validar_hipotesis(valor: str) -> str:
        hipotesis = valor.strip()
        if len(hipotesis) < 10:
            raise ErrorValidacion(campo='hipotesis', valor=valor, mensaje='La hipótesis debe tener al menos 10 caracteres.')
        if len(hipotesis) > 500:
            raise ErrorValidacion(campo='hipotesis', valor=valor, mensaje='Máximo 500 caracteres.')
        return hipotesis
