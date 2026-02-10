#!/usr/bin/env python3
"""
health.py - Health checks para el Sistema 90D
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/health.py
"""

import sqlite3
import os
from pathlib import Path
from database import DB_PATH

def verificar_salud() -> dict:
    salud = {
        "status": "healthy",
        "database": {"status": "ok"},
        "filesystem": {"status": "ok"}
    }
    
    # 1. Base de datos
    try:
        conn = sqlite3.connect(DB_PATH)
        # Integrity check
        res = conn.execute("PRAGMA integrity_check").fetchone()
        if res[0] != 'ok':
            salud["database"]["status"] = "corrupt"
            salud["status"] = "unhealthy"
        
        # Modo WAL check
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        salud["database"]["journal_mode"] = journal
        conn.close()
    except Exception as e:
        salud["database"]["status"] = "error"
        salud["database"]["error"] = str(e)
        salud["status"] = "unhealthy"
        
    # 2. Filesystem
    try:
        data_dir = os.path.dirname(DB_PATH)
        dirs = ['logs', 'backups']
        for d in dirs:
            path = os.path.join(data_dir, d)
            if not os.path.exists(path):
                salud["filesystem"][d] = "missing"
                salud["status"] = "degraded"
            elif not os.access(path, os.W_OK):
                salud["filesystem"][d] = "read-only"
                salud["status"] = "unhealthy"
    except Exception as e:
        salud["filesystem"]["status"] = "error"
        salud["filesystem"]["error"] = str(e)
        salud["status"] = "unhealthy"
        
    return salud
