#!/usr/bin/env python3
"""
test_fase2.py - Verificación de Alertas Inteligentes e Integración IA
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/test_fase2.py
"""

import database as db
from integracion_ia import IntegradorIA
import os

def test_alertas_sistema():
    print("\n" + "="*80)
    print("TEST: Sistema de Alertas Inteligentes")
    print("="*80)

    db.init_database()
    pid = db.crear_proyecto("Proyecto Alertas", "Testear fase 2", "2026-02-01", "mvp")
    print(f"✓ Proyecto creado: ID {pid}")

    # 1. Ejecutar análisis (debería generar alerta de datos insuficientes)
    print("\n1. Ejecutando análisis inicial...")
    analisis = db.analizar_proyecto_con_validacion(pid)
    assert analisis['estado'] == 'advertencia'
    
    alertas = db.obtener_alertas_proyecto(pid)
    assert len(alertas) == 1
    assert alertas[0]['tipo'] == 'datos_insuficientes'
    print(f"✓ Alerta creada: {alertas[0]['tipo']} - {alertas[0]['mensaje']}")

    # 2. Agregar métricas pero sin tiempo (debería cambiar el tipo de alerta)
    print("\n2. Agregando métricas sin tiempo...")
    for i in range(3):
        db.crear_metrica(pid, f"2026-02-0{i+1}", 0, 0, 0, "Test")
    
    analisis = db.analizar_proyecto_con_validacion(pid)
    assert analisis['tipo'] == 'sin_tiempo_registrado'
    
    alertas_activas = db.obtener_alertas_proyecto(pid, solo_activas=True)
    assert len(alertas_activas) == 1
    assert alertas_activas[0]['tipo'] == 'sin_tiempo_registrado'
    
    # Verificar que la anterior se resolvió automáticamente
    alertas_todas = db.obtener_alertas_proyecto(pid, solo_activas=False)
    assert any(a['tipo'] == 'datos_insuficientes' and a['resuelta'] == 1 for a in alertas_todas)
    print("✓ Limpieza automática: alerta obsoleta resuelta.")

    # 3. Cumplir requisitos (deberían resolverse todas)
    print("\n3. Cumpliendo requisitos de datos...")
    db.crear_metrica(pid, "2026-02-05", 100, 5, 2, "Venta real")
    
    db.analizar_proyecto_con_validacion(pid)
    alertas_finales = db.obtener_alertas_proyecto(pid, solo_activas=True)
    assert len(alertas_finales) == 0
    print("✓ Todas las alertas resueltas tras validación exitosa.")

def test_integracion_ia_mock():
    print("\n" + "="*80)
    print("TEST: Integración IA (Modo Manual/Mock)")
    print("="*80)

    ia = IntegradorIA()
    print(f"Proveedor detectado: {ia.proveedor}")
    
    resultado = ia.analizar_automaticamente()
    assert resultado['modo'] in ['manual', 'automatico', 'error']
    print(f"Modo de análisis: {resultado['modo']}")
    
    if resultado['modo'] == 'manual':
        assert 'prompt' in resultado
        print("✓ Modo manual correcto: ofrece el prompt para copiar/pegar.")
    
    print("\n" + "="*80)
    print("✅ TEST DE FASE 2 COMPLETADO")
    print("="*80)

if __name__ == '__main__':
    test_alertas_sistema()
    test_integracion_ia_mock()
