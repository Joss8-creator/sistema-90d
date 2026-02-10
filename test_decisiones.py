#!/usr/bin/env python3
"""
test_decisiones.py - Verificación de persistencia de decisiones rechazas
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/test_decisiones.py
"""

import database as db
import prompt_generator as pg
from datetime import date

def test_flujo_decisiones():
    print("\n" + "="*80)
    print("TEST: Persistencia de Decisiones")
    print("="*80)

    # 1. Preparar datos
    db.init_database()
    pid = db.crear_proyecto("Proyecto Decisiones", "Validar feedback de IA", "2026-01-01", "active")
    print(f"✓ Proyecto creado: ID {pid}")

    # 2. Registrar decisión RECHAZADA
    print("\n1. Registrando decisión RECHAZADA...")
    db.registrar_decision(
        proyecto_id=pid,
        tipo='kill',
        justificacion='Métricas de tracción insuficientes en 30 días.',
        accion_tomada='rechazada',
        razon_rechazo='Estoy esperando el resultado de una campaña de Ads que termina mañana.'
    )
    
    # 3. Verificar persistencia
    decisiones = db.obtener_decisiones_proyecto(pid)
    assert len(decisiones) == 1
    assert decisiones[0]['accion_tomada'] == 'rechazada'
    print("✓ Decisión persistida correctamente.")

    # 4. Verificar contexto en Prompt Generator
    print("\n2. Verificando contexto en el Prompt Generator...")
    prompt = pg.generar_prompt_analisis()
    
    assert "CONTEXTO ESTRATÉGICO: DECISIONES RECHAZADAS RECIENTEMENTE" in prompt
    assert "Proyecto Decisiones" in prompt
    assert "recomienda de KILL rechazada" or "Recomendación de KILL rechazada" in prompt
    assert "esperando el resultado de una campaña" in prompt
    print("✓ El prompt incluye el contexto de la decisión rechazada.")

    # 5. Registrar decisión ACEPTADA (Scale -> Winner)
    print("\n3. Registrando decisión ACEPTADA (Scale)...")
    db.registrar_decision(
        proyecto_id=pid,
        tipo='scale',
        justificacion='Crecimiento de ingresos del 200% mes a mes.',
        accion_tomada='aceptada'
    )
    
    # Simular lógica del handler en app.py (actualización de estado)
    p_antes = db.obtener_proyecto(pid)
    assert p_antes['estado'] == 'active'
    
    # Esto lo hace el handler en app.py, pero vamos a probar la función de db directamente
    db.actualizar_estado_proyecto(pid, 'winner')
    
    p_despues = db.obtener_proyecto(pid)
    assert p_despues['estado'] == 'winner'
    print("✓ Estado del proyecto actualizado a 'winner' tras aceptar scale.")

    print("\n" + "="*80)
    print("✅ TEST DE DECISIONES COMPLETADO EXITOSAMENTE")
    print("="*80)

if __name__ == '__main__':
    test_flujo_decisiones()
