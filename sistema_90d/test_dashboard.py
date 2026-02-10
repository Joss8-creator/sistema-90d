#!/usr/bin/env python3
"""
test_dashboard.py - Verificación del Dashboard Unificado.
"""

from app import render_template
import dashboard_data
import database as db
import guia
import os

def test_data_collection():
    print("TEST: Recopilación de datos del dashboard...")
    db.init_database()
    estado = dashboard_data.obtener_estado_sistema()
    print(f"Fase detectada: {estado['fase']['nombre']}")
    assert 'ciclo' in estado
    assert 'fase' in estado
    assert 'proyectos' in estado
    print("✓ Datos de estado recopilados.")

def test_render():
    print("TEST: Renderizado del dashboard...")
    # Mock context
    estado = dashboard_data.obtener_estado_sistema()
    proyectos = dashboard_data.obtener_proyectos_resumen()
    siguiente = guia.obtener_siguiente_accion()
    alertas = db.obtener_todas_alertas_activas()
    guia_ctx = guia.obtener_guia_contextual(proyectos, estado['fase'])
    
    context = {
        'estado': estado,
        'proyectos': proyectos,
        'siguiente_accion': siguiente,
        'alertas': alertas,
        'guia': guia_ctx
    }
    
    html = render_template('index.html', context)
    assert 'Centro de Comando' in html
    assert estado['fase']['nombre'] in html
    # Verificar que las variables anidadas funcionaron
    assert f"Día {estado['ciclo']['dia_actual']}/90" in html
    print("✓ Renderizado exitoso con variables anidadas.")

if __name__ == '__main__':
    test_data_collection()
    test_render()
    print("\n✅ DASHBOARD VERIFICADO")
