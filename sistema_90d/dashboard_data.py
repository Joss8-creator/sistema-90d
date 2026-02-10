#!/usr/bin/env python3
"""
dashboard_data.py - Lógica de recopilación de datos para el Dashboard Unificado.
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/dashboard_data.py
"""

import sqlite3
from datetime import datetime, timedelta, date
from database import DB_PATH, get_connection
from health import verificar_salud

def obtener_estado_sistema() -> dict:
    """
    Recopila todas las métricas del sistema para el Dashboard.
    """
    conn = get_connection()
    
    # 1. Ciclo 90D
    cursor = conn.execute("SELECT valor FROM config_sistema WHERE clave = 'fecha_inicio_ciclo'")
    fecha_val = cursor.fetchone()
    if not fecha_val:
        conn.execute("INSERT INTO config_sistema (clave, valor) VALUES (?, ?)", 
                     ('fecha_inicio_ciclo', date.today().isoformat()))
        conn.commit()
        fecha_val = [date.today().isoformat()]
        
    fecha_inicio = datetime.fromisoformat(fecha_val[0])
    dia_actual = (datetime.now() - fecha_inicio).days + 1
    dias_restantes = max(0, 90 - dia_actual)
    progreso_pct = min(100.0, (dia_actual / 90) * 100)
    
    # Determinar fase
    if dia_actual <= 14:
        fase = {'nombre': 'Exploración', 'color': 'blue', 'icono': '🔍'}
    elif dia_actual <= 45:
        fase = {'nombre': 'Experimentación', 'color': 'orange', 'icono': '🧪'}
    elif dia_actual <= 75:
        fase = {'nombre': 'Decisión', 'color': 'red', 'icono': '🎯'}
    else:
        fase = {'nombre': 'Consolidación', 'color': 'green', 'icono': '🚀'}
    
    # 2. Proyectos Stats
    cursor = conn.execute("""
        SELECT 
            COUNT(CASE WHEN estado IN ('active', 'mvp') THEN 1 END) as activos,
            COUNT(CASE WHEN estado = 'winner' THEN 1 END) as winners,
            COUNT(CASE WHEN estado = 'killed' THEN 1 END) as killed,
            COUNT(CASE WHEN estado = 'paused' THEN 1 END) as pausados
        FROM proyectos
    """)
    proyectos_res = cursor.fetchone()
    
    # 3. Métricas últimos 30 días
    cursor = conn.execute("""
        SELECT 
            SUM(ingresos) as ingresos_totales,
            SUM(tiempo_horas) as horas_totales,
            COUNT(DISTINCT proyecto_id) as proyectos_con_metricas,
            MAX(fecha) as ultima_metrica
        FROM metricas
        WHERE fecha >= date('now', '-30 days')
    """)
    metricas_res = cursor.fetchone()
    
    ingresos_30 = metricas_res[0] or 0
    horas_30 = metricas_res[1] or 0
    roi_global_30 = (ingresos_30 / horas_30) if horas_30 > 0 else 0
    
    # 4. Salud del sistema (reusando health.py)
    salud_res = verificar_salud()
    
    # 5. Adherencia (uso del sistema últimos 30 días)
    cursor = conn.execute("""
        SELECT COUNT(DISTINCT fecha) FROM metricas
        WHERE fecha >= date('now', '-30 days')
    """)
    dias_activos = cursor.fetchone()[0]
    adherencia_pct = (dias_activos / 30) * 100
    
    # 6. Rituales
    cursor = conn.execute("""
        SELECT 
            COUNT(CASE WHEN tipo = 'diario' THEN 1 END) as diarios,
            COUNT(CASE WHEN tipo = 'semanal' THEN 1 END) as semanales
        FROM rituales_completados
        WHERE fecha >= date('now', '-30 days')
    """)
    rituales_res = cursor.fetchone()
    
    conn.close()
    
    return {
        'ciclo': {
            'dia_actual': dia_actual,
            'dias_restantes': dias_restantes,
            'progreso_pct': round(progreso_pct, 1),
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': (fecha_inicio + timedelta(days=90)).strftime('%Y-%m-%d')
        },
        'fase': fase,
        'proyectos': {
            'activos': proyectos_res[0],
            'winners': proyectos_res[1],
            'killed': proyectos_res[2],
            'pausados': proyectos_res[3],
            'total': sum(proyectos_res)
        },
        'metricas_30d': {
            'ingresos_totales': round(ingresos_30, 2),
            'horas_totales': round(horas_30, 1),
            'roi_por_hora': round(roi_global_30, 2),
            'proyectos_con_metricas': metricas_res[2],
            'ultima_metrica_fecha': metricas_res[3] if metricas_res[3] else 'Nunca'
        },
        'adherencia': {
            'dias_activos': dias_activos,
            'porcentaje': round(adherencia_pct, 1),
            'status': 'excelente' if adherencia_pct >= 80 else 'buena' if adherencia_pct >= 50 else 'baja'
        },
        'rituales': {
            'diarios_completados': rituales_res[0],
            'semanales_completados': rituales_res[1],
            'diarios_esperados': 30,
            'semanales_esperados': 4
        },
        'salud': salud_res
    }

def obtener_proyectos_resumen():
    """Obtiene datos de la vista v_resumen_proyectos y añade flags para UI."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM v_resumen_proyectos")
    proyectos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Enriquecer datos para simplificar templates
    for p in proyectos:
        p['es_activo'] = p['estado'] in ['active', 'mvp', 'idea']
        p['dias_display'] = int(p['dias_desde_inicio']) if p['dias_desde_inicio'] else 0
        p['ultima_metrica_display'] = p['ultima_metrica_fecha'] if p['ultima_metrica_fecha'] else '-'
        
    return proyectos
