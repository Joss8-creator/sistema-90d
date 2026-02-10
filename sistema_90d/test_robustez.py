#!/usr/bin/env python3
"""
test_robustez.py - Verificación de Seguridad, Logs y Transacciones
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/test_robustez.py
"""

import database as db
from validadores import ValidadorMetricas, ErrorValidacion
from rate_limiter import limiter
from health import verificar_salud
import os
import time

def test_transacciones_acid():
    print("\n" + "="*80)
    print("TEST: Transacciones ACID y Modo WAL")
    print("="*80)
    
    db.init_database()
    
    # Verificar modo WAL
    conn = db.get_connection()
    journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
    print(f"Modo Journal: {journal}")
    assert journal == 'wal'
    conn.close()

    # Test de rollback en error
    try:
        with db.transaccion_segura() as conn:
            conn.execute("INSERT INTO proyectos (nombre, hipotesis, fecha_inicio, estado) VALUES (?,?,?,?)", 
                         ("TEST ACID", "HIPOTESIS", "2025-01-01", "idea"))
            raise RuntimeError("CRASH SIMULADO")
    except RuntimeError:
        print("✓ Crash simulado capturado.")
    
    # Verificar que NO se insertó
    conn = db.get_connection()
    res = conn.execute("SELECT COUNT(*) FROM proyectos WHERE nombre = 'TEST ACID'").fetchone()[0]
    assert res == 0
    print("✓ Rollback confirmado: No se guardaron datos tras el crash.")
    conn.close()

def test_validadores():
    print("\n" + "="*80)
    print("TEST: Validadores (Server-Side)")
    print("="*80)
    
    # 1. Ingresos inválidos
    try:
        ValidadorMetricas.validar_ingresos("millonario")
        assert False, "Debería haber fallado"
    except ErrorValidacion:
        print("✓ Capturó error: ingresos no numéricos.")
        
    # 2. Tiempo excesivo
    try:
        ValidadorMetricas.validar_tiempo("25")
        assert False, "Debería haber fallado"
    except ErrorValidacion:
        print("✓ Capturó error: tiempo > 24h.")
        
    # 3. Fecha futura
    try:
        ValidadorMetricas.validar_fecha("2099-01-01")
        assert False, "Debería haber fallado"
    except ErrorValidacion:
        print("✓ Capturó error: fecha futura.")

def test_rate_limiting():
    print("\n" + "="*80)
    print("TEST: Rate Limiting")
    print("="*80)
    
    limit = 3
    action = "test_action"
    
    for i in range(limit):
        assert limiter.permitir(action, limite=limit, ventana=5)
    
    # El 4to debe fallar
    assert not limiter.permitir(action, limite=limit, ventana=5)
    print(f"✓ Rate limit funcionó tras {limit} intentos.")

def test_health_check():
    print("\n" + "="*80)
    print("TEST: Health Check")
    print("="*80)
    
    salud = verificar_salud()
    print(f"Estado general: {salud['status']}")
    assert salud['status'] in ['healthy', 'degraded']
    print(f"Detalles DB: {salud['database']}")
    print("✓ Health check generado correctamente.")

if __name__ == '__main__':
    test_transacciones_acid()
    test_validadores()
    test_rate_limiting()
    test_health_check()
    print("\n" + "="*80)
    print("✅ TEST DE ROBUSTEZ COMPLETADO")
    print("="*80)
