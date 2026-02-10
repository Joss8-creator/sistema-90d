#!/usr/bin/env python3
"""
guia.py - Sistema de guía contextual para el Sistema 90D
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/guia.py
"""

from typing import Dict, List
import random

CONSEJOS = {
    "IDEACIÓN": [
        "No te enamores de la solución, enamórate del problema.",
        "Habla con al menos 5 clientes potenciales antes de escribir una línea de código.",
        "Define el umbral de éxito: ¿Qué número validaría tu idea en 7 días?",
        "Si no puedes explicar tu idea en un tweet, es demasiado compleja."
    ],
    "MVP / VALIDACIÓN": [
        "Si no te avergüenza tu primera versión, lanzaste demasiado tarde.",
        "Mide solo lo que importa: ¿Alguien está dispuesto a pagar/suscribirse?",
        "No construyas automatizaciones hasta que lo hayas hecho 10 veces manual.",
        "El objetivo del MVP no es ganar dinero, es reducir la incertidumbre."
    ],
    "LANZAMIENTO / TRACCIÓN": [
        "Céntrate en un solo canal de adquisición hasta que funcione.",
        "Pide feedback brutalmente honesto, no busques cumplidos.",
        "Observa lo que los usuarios HACEN, no lo que DICEN.",
        "La retención es más importante que la adquisición en esta etapa."
    ],
    "ESCALADO / CIERRE": [
        "Un 'Winner' se siente diferente: la demanda supera tu capacidad.",
        "Si el ROI es bajo después de 3 pivotes, cárgalo (KILL) sin piedad.",
        "Documenta tus aprendizajes de los proyectos fallidos; son tu activo más valioso.",
        "Escalar un producto roto solo lo rompe más rápido."
    ]
}

def obtener_consejo_por_fase(fase_nombre: str) -> str:
    """Retorna un consejo aleatorio basado en la fase actual."""
    # Mapear nombres de fase del sistema a las categorías de consejos
    fase_nombre = fase_nombre.upper()
    categoria = "IDEACIÓN"
    
    if "MVP" in fase_nombre or "VALIDACIÓN" in fase_nombre:
        categoria = "MVP / VALIDACIÓN"
    elif "LANZAMIENTO" in fase_nombre or "TRACCIÓN" in fase_nombre:
        categoria = "LANZAMIENTO / TRACCIÓN"
    elif "ESCALADO" in fase_nombre or "CIERRE" in fase_nombre or "OPTIMIZACIÓN" in fase_nombre:
        categoria = "ESCALADO / CIERRE"
        
    consejos = CONSEJOS.get(categoria, CONSEJOS["IDEACIÓN"])
    return random.choice(consejos)

def obtener_guia_contextual(proyectos: List[Dict], fase: Dict) -> Dict:
    """
    Genera un resumen de guía basado en el estado actual del sistema.
    """
    num_proyectos = len([p for p in proyectos if p['estado'] not in ['killed', 'winner']])
    consejo = obtener_consejo_por_fase(fase['nombre'])
    
    alertas_locales = []
    if num_proyectos > 3:
        alertas_locales.append("⚠️ Tienes demasiados proyectos activos. Recomendación Marc Lou: Máximo 3 para enfocar energía.")
    elif num_proyectos == 0:
        alertas_locales.append("💡 Dashboard vacío. ¡Es hora de sembrar una nueva idea!")
        
    return {
        "consejo": consejo,
        "fase_nombre": fase['nombre'],
        "recomendaciones": alertas_locales,
        "num_activos": num_proyectos
    }
def obtener_siguiente_accion() -> dict:
    """Implementa la lógica del Cuadrante 2: ¿Qué debo hacer ahora?"""
    from database import get_connection
    conn = get_connection()
    
    # 1. Verificar si hay ritual diario hoy
    cursor = conn.execute("SELECT id FROM rituales_completados WHERE tipo='diario' AND date(fecha) = date('now')")
    ritual_hoy = cursor.fetchone()
    if not ritual_hoy:
        conn.close()
        return {
            'titulo': '⏰ Ritual Diario Pendiente',
            'descripcion': 'No has registrado tus métricas de hoy. Tómate 2 minutos para mantener el pulso del sistema.',
            'urgencia': 'high',
            'tiempo_estimado': '2 min',
            'accion': '/ritual-diario'
        }
        
    # 2. Verificar proyectos sin métricas recientes (> 48h)
    cursor = conn.execute("""
        SELECT p.id, p.nombre FROM proyectos p
        LEFT JOIN metricas m ON p.id = m.proyecto_id
        WHERE p.estado IN ('active', 'mvp')
        GROUP BY p.id
        HAVING (julianday('now') - julianday(MAX(m.fecha))) > 2 OR MAX(m.fecha) IS NULL
        LIMIT 1
    """)
    proyecto_abandonado = cursor.fetchone()
    if proyecto_abandonado:
        conn.close()
        return {
            'titulo': f'🧟 Proyecto "{proyecto_abandonado["nombre"]}" estancado',
            'descripcion': 'Han pasado más de 48h sin datos. ¿Sigue vivo este experimento?',
            'urgencia': 'medium',
            'tiempo_estimado': '5 min',
            'accion': f'/proyecto/{proyecto_abandonado["id"]}'
        }
        
    # 3. Acción por defecto: Exploración/Mejora
    conn.close()
    return {
        'titulo': '🧪 Explora un nuevo canal',
        'descripcion': 'El sistema está al día. ¿Qué pequeño experimento podrías lanzar hoy para aumentar tu tracción?',
        'urgencia': 'low',
        'tiempo_estimado': '30 min',
        'accion': None
    }
