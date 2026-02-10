#!/usr/bin/env python3
"""
rate_limiter.py - Rate limiting en memoria para el Sistema 90D
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/rate_limiter.py
"""

from collections import defaultdict
from time import time

class RateLimiter:
    """Implementación simple de Bucket/Ventana para un solo usuario."""
    
    def __init__(self):
        # {key: [timestamps]}
        self.historial = defaultdict(list)
    
    def permitir(self, accion: str, limite: int = 10, ventana: int = 60) -> bool:
        """
        Verifica si la acción está permitida bajo el límite.
        Por defecto: 10 acciones por minuto.
        """
        ahora = time()
        
        # Limpiar antiguos
        self.historial[accion] = [t for t in self.historial[accion] if ahora - t < ventana]
        
        if len(self.historial[accion]) >= limite:
            return False
            
        self.historial[accion].append(ahora)
        return True

# Instancia global
limiter = RateLimiter()
