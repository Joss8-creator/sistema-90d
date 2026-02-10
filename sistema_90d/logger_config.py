#!/usr/bin/env python3
"""
logger_config.py - Configuración de logging estructurado
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/logger_config.py
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

def configurar_logging():
    log_dir = Path('data/logs')
    log_dir.mkdir(exist_ok=True, parents=True)
    
    log_file = log_dir / 'sistema.log'
    
    # Formato: [2025-02-03 18:10:00] [ERROR] database: Mensaje de error
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    
    # Handler: Archivo con rotación (1MB cada uno, máximo 5 archivos)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000, 
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Handler: Consola (solo WARNING y superior)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Loggers específicos
    logging.getLogger('database').setLevel(logging.INFO)
    logging.getLogger('app').setLevel(logging.INFO)

# Instanciar loggers para uso en módulos
logger_db = logging.getLogger('database')
logger_app = logging.getLogger('app')
