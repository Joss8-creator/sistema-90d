#!/usr/bin/env python3
"""
test_mejoras.py - Script de prueba para mejoras críticas
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/test_mejoras.py

Prueba las mejoras implementadas en Fase 1:
1. Sistema de backup automático
2. Validación de datos en motor de métricas
"""

import database as db
import backup as bk
from datetime import date, timedelta

def test_validacion_datos():
    """Probar validación de datos en proyectos"""
    print("\n" + "="*80)
    print("TEST 1: Validación de Datos")
    print("="*80)
    
    # Crear proyecto de prueba
    proyecto_id = db.crear_proyecto(
        "Proyecto Test Validación",
        "Hipótesis de prueba",
        date.today().isoformat(),
        "mvp"
    )
    print(f"\n✓ Proyecto creado: ID {proyecto_id}")
    
    # Test 1: Sin métricas
    print("\n1. Validando proyecto SIN métricas...")
    validacion = db.validar_datos_proyecto(proyecto_id)
    print(f"   Válido: {validacion['valido']}")
    print(f"   Mensaje: {validacion['mensaje']}")
    assert not validacion['valido'], "Debería ser inválido sin métricas"
    assert validacion['tipo'] == 'datos_insuficientes'
    print("   ✓ PASS: Detecta datos insuficientes")
    
    # Test 2: Con 1 métrica (insuficiente)
    print("\n2. Agregando 1 métrica SIN tiempo...")
    db.crear_metrica(proyecto_id, date.today().isoformat(), 100, 0, 1, "Primera métrica sin tiempo")
    validacion = db.validar_datos_proyecto(proyecto_id)
    print(f"   Válido: {validacion['valido']}")
    print(f"   Mensaje: {validacion['mensaje']}")
    assert not validacion['valido'], "Debería ser inválido con solo 1 métrica"
    print("   ✓ PASS: Requiere mínimo 3 métricas")
    
    # Test 3: Con 3 métricas pero sin tiempo
    print("\n3. Agregando 2 métricas más SIN tiempo...")
    db.crear_metrica(proyecto_id, (date.today() - timedelta(days=1)).isoformat(), 50, 0, 0, "Sin tiempo")
    db.crear_metrica(proyecto_id, (date.today() - timedelta(days=2)).isoformat(), 75, 0, 1, "Sin tiempo")
    validacion = db.validar_datos_proyecto(proyecto_id)
    print(f"   Válido: {validacion['valido']}")
    print(f"   Mensaje: {validacion['mensaje']}")
    assert not validacion['valido'], "Debería ser inválido sin tiempo registrado"
    assert validacion['tipo'] == 'sin_tiempo_registrado'
    print("   ✓ PASS: Detecta falta de tiempo registrado")
    
    # Test 4: Con datos completos
    print("\n4. Agregando métrica CON tiempo...")
    db.crear_metrica(proyecto_id, (date.today() - timedelta(days=3)).isoformat(), 200, 5, 2, "Con tiempo")
    validacion = db.validar_datos_proyecto(proyecto_id)
    print(f"   Válido: {validacion['valido']}")
    print(f"   Mensaje: {validacion['mensaje']}")
    assert validacion['valido'], "Debería ser válido con 4 métricas y tiempo"
    print("   ✓ PASS: Datos válidos para análisis")
    
    # Test 5: Análisis con validación
    print("\n5. Probando análisis con validación...")
    analisis = db.analizar_proyecto_con_validacion(proyecto_id)
    print(f"   Estado: {analisis['estado']}")
    print(f"   Clasificación: {analisis.get('clasificacion', 'N/A')}")
    print(f"   Decisión sugerida: {analisis.get('decision_sugerida', 'N/A')}")
    print(f"   ROI: ${analisis.get('roi', 0):.2f}/h")
    assert analisis['estado'] == 'analizado', "Debería estar analizado"
    print("   ✓ PASS: Análisis completado")
    
    # Test 6: Estimación de tiempo
    print("\n6. Probando estimación de tiempo...")
    tiempo_estimado = db.estimar_tiempo_minimo(proyecto_id)
    print(f"   Tiempo estimado: {tiempo_estimado:.1f}h")
    print("   ✓ PASS: Estimación funciona")
    
    print("\n" + "="*80)
    print("✓ TODOS LOS TESTS DE VALIDACIÓN PASARON")
    print("="*80)


def test_sistema_backup():
    """Probar sistema de backup automático"""
    print("\n" + "="*80)
    print("TEST 2: Sistema de Backup")
    print("="*80)
    
    backup_sistema = bk.SistemaBackup(db.DB_PATH)
    
    # Test 1: Crear backup
    print("\n1. Creando backup manual...")
    backup_path = backup_sistema.crear_backup(comprimir=True)
    print(f"   Backup creado: {backup_path.name}")
    assert backup_path.exists(), "Backup debería existir"
    print("   ✓ PASS: Backup creado exitosamente")
    
    # Test 2: Listar backups
    print("\n2. Listando backups...")
    backups = backup_sistema.listar_backups()
    print(f"   Backups encontrados: {len(backups)}")
    for b in backups[:3]:  # Mostrar solo primeros 3
        print(f"   - {b['nombre']} ({b['tamaño_mb']:.2f} MB)")
    assert len(backups) > 0, "Debería haber al menos 1 backup"
    print("   ✓ PASS: Listado funciona")
    
    # Test 3: Estadísticas
    print("\n3. Obteniendo estadísticas...")
    stats = backup_sistema.obtener_estadisticas()
    print(f"   Número de backups: {stats['num_backups']}")
    print(f"   Espacio total: {stats['espacio_total_mb']:.2f} MB")
    if stats['ultimo_backup']:
        print(f"   Último backup: {stats['ultimo_backup'].strftime('%Y-%m-%d %H:%M:%S')}")
    assert stats['num_backups'] > 0, "Debería haber backups"
    print("   ✓ PASS: Estadísticas correctas")
    
    # Test 4: Backup automático (no debería crear otro inmediatamente)
    print("\n4. Probando backup automático...")
    creado = backup_sistema.backup_automatico_si_necesario(intervalo_horas=24)
    print(f"   Backup creado: {creado}")
    assert not creado, "No debería crear backup (muy reciente)"
    print("   ✓ PASS: No crea backups redundantes")
    
    # Test 5: Limpieza de backups antiguos
    print("\n5. Probando limpieza de backups...")
    backups_antes = len(backup_sistema.listar_backups())
    print(f"   Backups antes: {backups_antes}")
    backup_sistema.limpiar_backups_antiguos(max_backups=5)
    backups_despues = len(backup_sistema.listar_backups())
    print(f"   Backups después: {backups_despues}")
    assert backups_despues <= 5, "Debería mantener máximo 5 backups"
    print("   ✓ PASS: Limpieza funciona")
    
    print("\n" + "="*80)
    print("✓ TODOS LOS TESTS DE BACKUP PASARON")
    print("="*80)


def test_integracion():
    """Probar integración de mejoras"""
    print("\n" + "="*80)
    print("TEST 3: Integración de Mejoras")
    print("="*80)
    
    # Crear proyecto con datos progresivos
    print("\n1. Simulando evolución de proyecto...")
    proyecto_id = db.crear_proyecto(
        "Proyecto Integración",
        "Validar integración de mejoras",
        (date.today() - timedelta(days=10)).isoformat(),
        "idea"
    )
    
    # Día 1: Solo idea (sin métricas)
    print("\n   Día 1: Proyecto creado (idea)")
    analisis = db.analizar_proyecto_con_validacion(proyecto_id)
    print(f"   Estado: {analisis['estado']} - {analisis['mensaje']}")
    assert analisis['estado'] == 'advertencia'
    
    # Día 3: Primera métrica
    print("\n   Día 3: Primera métrica registrada")
    db.crear_metrica(proyecto_id, (date.today() - timedelta(days=7)).isoformat(), 0, 1, 0, "Investigación")
    analisis = db.analizar_proyecto_con_validacion(proyecto_id)
    print(f"   Estado: {analisis['estado']} - {analisis['mensaje']}")
    assert analisis['estado'] == 'advertencia'
    
    # Día 5: Segunda métrica
    print("\n   Día 5: Segunda métrica")
    db.crear_metrica(proyecto_id, (date.today() - timedelta(days=5)).isoformat(), 0, 2, 0, "Prototipo")
    analisis = db.analizar_proyecto_con_validacion(proyecto_id)
    print(f"   Estado: {analisis['estado']} - {analisis['mensaje']}")
    assert analisis['estado'] == 'advertencia'
    
    # Día 7: Tercera métrica (ahora sí analizable)
    print("\n   Día 7: Tercera métrica - ¡Datos suficientes!")
    db.crear_metrica(proyecto_id, (date.today() - timedelta(days=3)).isoformat(), 50, 3, 1, "Primera venta")
    analisis = db.analizar_proyecto_con_validacion(proyecto_id)
    print(f"   Estado: {analisis['estado']}")
    print(f"   Clasificación: {analisis['clasificacion']}")
    print(f"   ROI: ${analisis['roi']:.2f}/h")
    assert analisis['estado'] == 'analizado'
    
    # Día 10: Más tracción
    print("\n   Día 10: Más tracción")
    db.crear_metrica(proyecto_id, date.today().isoformat(), 200, 4, 3, "Crecimiento")
    analisis = db.analizar_proyecto_con_validacion(proyecto_id)
    print(f"   ROI actualizado: ${analisis['roi']:.2f}/h")
    print(f"   Decisión: {analisis['decision_sugerida']}")
    
    print("\n   ✓ Evolución del proyecto validada correctamente")
    
    # Crear backup final
    print("\n2. Creando backup final...")
    backup_sistema = bk.SistemaBackup(db.DB_PATH)
    backup_sistema.crear_backup()
    
    print("\n" + "="*80)
    print("✓ TEST DE INTEGRACIÓN COMPLETADO")
    print("="*80)


def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*80)
    print("PRUEBAS DE MEJORAS CRÍTICAS - FASE 1")
    print("="*80)
    print("\nProbando:")
    print("  1. Validación de datos en motor de métricas")
    print("  2. Sistema de backup automático")
    print("  3. Integración de mejoras")
    
    try:
        # Inicializar BD
        db.init_database()
        
        # Ejecutar tests
        test_validacion_datos()
        test_sistema_backup()
        test_integracion()
        
        print("\n" + "="*80)
        print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("="*80)
        print("\nMejoras implementadas:")
        print("  ✓ Validación de datos (evita falsos positivos)")
        print("  ✓ Sistema de backup automático (protege datos)")
        print("  ✓ Análisis con validación integrada")
        print("\nPróximos pasos:")
        print("  - Fase 2: Integración API opcional")
        print("  - Fase 2: Limpieza automática de alertas")
        print("  - Fase 3: Guía contextual")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
