#!/usr/bin/env python3
"""
database.py - Wrapper SQLite para Sistema 90D
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/database.py

Gestión de base de datos sin ORM. Queries directas para máxima eficiencia.
Complejidad: O(1) inserciones, O(n) consultas donde n = proyectos activos (<20 esperado)
"""

import sqlite3
import os
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager
from logger_config import logger_db

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'sistema.db')

# Asegurar que el directorio data existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Obtener conexión a SQLite con configuraciones robustas."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Robustez Fase 4
    conn.execute("PRAGMA journal_mode=WAL")      # Previene corrupción
    conn.execute("PRAGMA synchronous=NORMAL")   # Balance seguridad/velocidad en WAL
    conn.execute("PRAGMA foreign_keys = ON")     # Mantener integridad referencial
    
    return conn

# Alias para compatibilidad con otros módulos
get_db = get_connection

@contextmanager
def transaccion_segura():
    """Context manager para garantizar transacciones ACID y cierre de conexión."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger_db.error(f"Error en transacción: {e}", exc_info=True)
        raise
    finally:
        conn.close()


def init_database() -> None:
    """
    Inicializar base de datos con esquema completo.
    Idempotente: se puede ejecutar múltiples veces sin errores.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de ciclos 90D
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ciclos_90d (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT NOT NULL,
            activo INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            hipotesis TEXT NOT NULL,
            fecha_inicio TEXT NOT NULL,
            estado TEXT NOT NULL CHECK(estado IN ('idea', 'mvp', 'active', 'paused', 'killed', 'winner')),
            ciclo_id INTEGER,
            version INTEGER DEFAULT 1, -- Optimistic Locking
            razon_kill TEXT,
            fecha_kill TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ciclo_id) REFERENCES ciclos_90d(id)
        )
    """)
    
    # Tabla de métricas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metricas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            ingresos REAL DEFAULT 0,
            tiempo_horas REAL DEFAULT 0,
            conversiones INTEGER DEFAULT 0,
            notas TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    # Tabla de decisiones (NUEVO: Mejora Fase 1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL, -- kill, iterate, scale, pause
            justificacion TEXT,
            origen TEXT DEFAULT 'ia', -- ia, manual
            accion_tomada TEXT NOT NULL CHECK(accion_tomada IN ('aceptada', 'rechazada', 'pospuesta')),
            razon_rechazo TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)

    # Tabla de alertas (NUEVO: Mejora Fase 2)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL, -- datos_insuficientes, sin_tiempo, roi_bajo, etc.
            severidad TEXT DEFAULT 'info', -- info, warning, critical
            mensaje TEXT NOT NULL,
            resuelta INTEGER DEFAULT 0,
            fecha_resolucion TEXT,
            resolucion_automatica INTEGER DEFAULT 0,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    # Tabla de rituales (Fase Dashboard)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rituales_completados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL, -- diario, semanal
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de configuración (Fase Dashboard)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_sistema (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """)
    
    # Inicializar fecha de inicio de ciclo si no existe
    cursor.execute("INSERT OR IGNORE INTO config_sistema (clave, valor) VALUES (?, ?)", 
                   ('fecha_inicio_ciclo', date.today().isoformat()))

    # Vista consolidada para el dashboard (simplifica queries)
    cursor.execute("DROP VIEW IF EXISTS v_resumen_proyectos")
    cursor.execute("""
        CREATE VIEW v_resumen_proyectos AS
        SELECT 
            p.id, 
            p.nombre, 
            p.estado,
            p.version,
            p.hipotesis,
            p.fecha_inicio,
            (julianday('now') - julianday(p.fecha_inicio)) as dias_desde_inicio,
            COALESCE(SUM(m.ingresos), 0) as ingresos_total,
            COALESCE(SUM(m.tiempo_horas), 0) as horas_total,
            COALESCE(SUM(m.conversiones), 0) as conversiones_total,
            CASE 
                WHEN SUM(m.tiempo_horas) > 0 THEN ROUND(SUM(m.ingresos) / SUM(m.tiempo_horas), 2)
                ELSE 0 
            END as roi_por_hora,
            MAX(m.fecha) as ultima_metrica_fecha,
            (julianday('now') - julianday(MAX(m.fecha))) as dias_desde_ultima_metrica
        FROM proyectos p
        LEFT JOIN metricas m ON p.id = m.proyecto_id
        GROUP BY p.id
    """)
    
    # Índices para optimización
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metricas_proyecto ON metricas(proyecto_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metricas_fecha ON metricas(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proyectos_estado ON proyectos(estado)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisiones_proyecto ON decisiones(proyecto_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisiones_fecha ON decisiones(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alertas_proyecto ON alertas(proyecto_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alertas_resuelta ON alertas(resuelta)")
    
    conn.commit()
    conn.close()


# ============================================================================
# FUNCIONES CRUD - CICLOS 90D
# ============================================================================

def crear_ciclo_90d(fecha_inicio: Optional[str] = None) -> int:
    """
    Crear nuevo ciclo 90D y desactivar ciclos anteriores.
    
    Args:
        fecha_inicio: Fecha en formato ISO (YYYY-MM-DD). Si es None, usa fecha actual.
    
    Returns:
        int: ID del ciclo creado
    """
    if fecha_inicio is None:
        fecha_inicio = date.today().isoformat()
    
    # Calcular fecha fin (90 días después)
    fecha_inicio_obj = date.fromisoformat(fecha_inicio)
    fecha_fin = (fecha_inicio_obj + timedelta(days=90)).isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Desactivar ciclos anteriores
    cursor.execute("UPDATE ciclos_90d SET activo = 0 WHERE activo = 1")
    
    # Crear nuevo ciclo
    cursor.execute("""
        INSERT INTO ciclos_90d (fecha_inicio, fecha_fin, activo)
        VALUES (?, ?, 1)
    """, (fecha_inicio, fecha_fin))
    
    ciclo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return ciclo_id


def obtener_ciclo_activo() -> Optional[Dict]:
    """
    Obtener el ciclo 90D actualmente activo.
    
    Returns:
        Dict con datos del ciclo o None si no hay ciclo activo
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, fecha_inicio, fecha_fin, created_at
        FROM ciclos_90d
        WHERE activo = 1
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def tiene_ciclo_iniciado() -> bool:
    """
    Verificar si existe un ciclo 90D iniciado.
    
    Returns:
        bool: True si existe un ciclo activo, False en caso contrario
    """
    ciclo = obtener_ciclo_activo()
    return ciclo is not None


def calcular_fase_actual(ciclo: Dict) -> Dict:
    """
    Calcular fase actual del ciclo 90D según día.
    
    Fases:
    - Días 1-14: Exploración
    - Días 15-45: Experimentación
    - Días 46-75: Decisión
    - Días 76-90: Consolidación
    
    Args:
        ciclo: Diccionario con datos del ciclo (debe tener 'fecha_inicio')
    
    Returns:
        Dict con 'nombre', 'dia', 'dias_restantes', 'tareas_sugeridas'
    """
    fecha_inicio = date.fromisoformat(ciclo['fecha_inicio'])
    hoy = date.today()
    dia_actual = (hoy - fecha_inicio).days + 1  # Día 1-indexed
    dias_restantes = 90 - dia_actual + 1
    
    # Determinar fase y tareas sugeridas
    if dia_actual <= 14:
        fase = 'Exploración'
        tareas = [
            'Formular hipótesis claras para nuevas ideas',
            'Diseñar experimentos baratos de validación',
            'Definir métricas mínimas de éxito',
            'Investigar competencia y mercado'
        ]
    elif dia_actual <= 45:
        fase = 'Experimentación'
        tareas = [
            'Lanzar MVPs funcionales',
            'Medir conversiones reales',
            'Registrar feedback utilizable',
            'Iterar rápidamente según datos'
        ]
    elif dia_actual <= 75:
        fase = 'Decisión'
        tareas = [
            'Clasificar proyectos: Kill / Iterate / Winner',
            'Justificar decisiones con métricas',
            'Eliminar proyectos sin tracción',
            'Doblar apuesta en winners'
        ]
    else:
        fase = 'Consolidación'
        tareas = [
            'Reducir exposición pública innecesaria',
            'Mejorar onboarding de usuarios',
            'Minimizar soporte manual',
            'Fortalecer ventaja competitiva'
        ]
    
    return {
        'nombre': fase,
        'dia': dia_actual,
        'dias_restantes': max(0, dias_restantes),
        'tareas_sugeridas': tareas
    }


# ============================================================================
# FUNCIONES CRUD - PROYECTOS
# ============================================================================

def crear_proyecto(nombre: str, hipotesis: str, fecha_inicio: str, estado: str = 'idea') -> int:
    """
    Crear nuevo proyecto.
    
    Args:
        nombre: Nombre del proyecto
        hipotesis: Hipótesis a validar
        fecha_inicio: Fecha en formato ISO (YYYY-MM-DD)
        estado: Estado inicial (idea|mvp|active|paused|killed|winner)
    
    Returns:
        int: ID del proyecto creado
    
    Raises:
        ValueError: Si el estado no es válido
    """
    estados_validos = ['idea', 'mvp', 'active', 'paused', 'killed', 'winner']
    if estado not in estados_validos:
        raise ValueError(f"Estado inválido: {estado}. Debe ser uno de {estados_validos}")
    
    with transaccion_segura() as conn:
        # Obtener ciclo activo
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ciclos_90d WHERE activo = 1 ORDER BY fecha_inicio DESC LIMIT 1")
        row = cursor.fetchone()
        ciclo_id = row['id'] if row else None
        
        cursor.execute("""
            INSERT INTO proyectos (nombre, hipotesis, fecha_inicio, estado, ciclo_id)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, hipotesis, fecha_inicio, estado, ciclo_id))
        
        return cursor.lastrowid


def obtener_proyectos(estado: Optional[str] = None) -> List[Dict]:
    """
    Obtener lista de proyectos, opcionalmente filtrados por estado.
    
    Args:
        estado: Filtrar por estado específico (None = todos)
    
    Returns:
        List[Dict]: Lista de proyectos
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if estado:
        cursor.execute("""
            SELECT id, nombre, hipotesis, fecha_inicio, estado, created_at
            FROM proyectos
            WHERE estado = ?
            ORDER BY created_at DESC
        """, (estado,))
    else:
        cursor.execute("""
            SELECT id, nombre, hipotesis, fecha_inicio, estado, created_at
            FROM proyectos
            ORDER BY created_at DESC
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def obtener_proyecto(proyecto_id: int) -> Optional[Dict]:
    """
    Obtener proyecto específico por ID.
    
    Args:
        proyecto_id: ID del proyecto
    
    Returns:
        Dict con datos del proyecto o None si no existe
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nombre, hipotesis, fecha_inicio, estado, version, created_at
        FROM proyectos
        WHERE id = ?
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def actualizar_estado_proyecto(proyecto_id: int, nuevo_estado: str) -> bool:
    """Actualiza el estado de un proyecto con atomicidad."""
    estados_validos = ['idea', 'mvp', 'active', 'paused', 'killed', 'winner']
    if nuevo_estado not in estados_validos:
        raise ValueError(f"Estado inválido: {nuevo_estado}")
    with transaccion_segura() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE proyectos 
            SET estado = ?, version = version + 1 
            WHERE id = ?
        """, (nuevo_estado, proyecto_id))
        return cursor.rowcount > 0


# ============================================================================
# FUNCIONES CRUD - MÉTRICAS
# ============================================================================

def crear_metrica(proyecto_id: int, fecha: str, ingresos: float = 0.0, 
                  tiempo_horas: float = 0.0, conversiones: int = 0, 
                  notas: str = '') -> int:
    """Registrar nueva métrica para un proyecto con atomicidad."""
    with transaccion_segura() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metricas (proyecto_id, fecha, ingresos, tiempo_horas, conversiones, notas)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (proyecto_id, fecha, ingresos, tiempo_horas, conversiones, notas))
        return cursor.lastrowid


def obtener_metricas_proyecto(proyecto_id: int) -> List[Dict]:
    """
    Obtener historial de métricas de un proyecto.
    
    Args:
        proyecto_id: ID del proyecto
    
    Returns:
        List[Dict]: Lista de métricas ordenadas por fecha (más reciente primero)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, fecha, ingresos, tiempo_horas, conversiones, notas, created_at
        FROM metricas
        WHERE proyecto_id = ?
        ORDER BY fecha DESC, created_at DESC
    """, (proyecto_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def calcular_dashboard_proyecto(proyecto_id: int) -> Dict:
    """
    Calcular métricas agregadas para dashboard de proyecto.
    
    Args:
        proyecto_id: ID del proyecto
    
    Returns:
        Dict con: total_ingresos, total_tiempo, roi, num_metricas, ultima_metrica
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Agregaciones
    cursor.execute("""
        SELECT 
            COALESCE(SUM(ingresos), 0) as total_ingresos,
            COALESCE(SUM(tiempo_horas), 0) as total_tiempo,
            COALESCE(SUM(conversiones), 0) as total_conversiones,
            COUNT(*) as num_metricas,
            MAX(fecha) as ultima_fecha
        FROM metricas
        WHERE proyecto_id = ?
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        data = dict(row)
        # Calcular ROI ($/hora)
        if data['total_tiempo'] > 0:
            data['roi'] = data['total_ingresos'] / data['total_tiempo']
        else:
            data['roi'] = 0.0
        
        return data
    
    return {
        'total_ingresos': 0.0,
        'total_tiempo': 0.0,
        'total_conversiones': 0,
        'roi': 0.0,
        'num_metricas': 0,
        'ultima_fecha': None
    }


def obtener_todos_proyectos_con_metricas() -> List[Dict]:
    """
    Obtener todos los proyectos con sus métricas agregadas.
    Usado para dashboard principal y generación de prompts.
    
    Returns:
        List[Dict]: Proyectos con métricas calculadas
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.id,
            p.nombre,
            p.hipotesis,
            p.fecha_inicio,
            p.estado,
            COALESCE(SUM(m.ingresos), 0) as total_ingresos,
            COALESCE(SUM(m.tiempo_horas), 0) as total_tiempo,
            COALESCE(SUM(m.conversiones), 0) as total_conversiones,
            COUNT(m.id) as num_metricas,
            MAX(m.fecha) as ultima_metrica
        FROM proyectos p
        LEFT JOIN metricas m ON p.id = m.proyecto_id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    proyectos = []
    for row in rows:
        data = dict(row)
        # Calcular ROI
        if data['total_tiempo'] > 0:
            data['roi'] = data['total_ingresos'] / data['total_tiempo']
        else:
            data['roi'] = 0.0
        proyectos.append(data)
    
    return proyectos


# ============================================================================
# FUNCIONES CRUD - DECISIONES
# ============================================================================

def registrar_decision(proyecto_id: int, tipo: str, justificacion: str, 
                       accion_tomada: str, origen: str = 'ia', 
                       razon_rechazo: Optional[str] = None) -> int:
    """
    Registrar una decisión tomada (o rechazada) sobre un proyecto.
    
    Args:
        proyecto_id: ID del proyecto
        tipo: Tipo de decisión (kill, iterate, scale, pause)
        justificacion: Texto explicativo de la recomendación
        accion_tomada: aceptada, rechazada, pospuesta
        origen: ia o manual
        razon_rechazo: Si es rechazada, por qué
        
    Returns:
        int: ID de la decisión registrada
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO decisiones (proyecto_id, tipo, justificacion, origen, accion_tomada, razon_rechazo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (proyecto_id, tipo, justificacion, origen, accion_tomada, razon_rechazo))
    
    decision_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return decision_id


def obtener_decisiones_proyecto(proyecto_id: int) -> List[Dict]:
    """Obtener el historial de decisiones de un proyecto."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, tipo, justificacion, origen, accion_tomada, razon_rechazo, fecha
        FROM decisiones
        WHERE proyecto_id = ?
        ORDER BY fecha DESC
    """, (proyecto_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def obtener_decisiones_rechazadas_recientes(dias: int = 30) -> List[Dict]:
    """
    Obtener decisiones rechazadas recientemente para dar contexto a la IA.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.nombre as proyecto_nombre, d.tipo, d.justificacion, d.razon_rechazo, d.fecha
        FROM decisiones d
        JOIN proyectos p ON p.id = d.proyecto_id
        WHERE d.accion_tomada = 'rechazada'
          AND d.fecha >= datetime('now', ?)
    """, (f'-{dias} days',))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# ============================================================================
# FUNCIONES CRUD - ALERTAS (NUEVO Fase 2)
# ============================================================================

def crear_alerta(proyecto_id: int, tipo: str, mensaje: str, severidad: str = 'info') -> int:
    """Registrar una nueva alerta."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alertas (proyecto_id, tipo, mensaje, severidad)
        VALUES (?, ?, ?, ?)
    """, (proyecto_id, tipo, mensaje, severidad))
    alerta_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alerta_id

def obtener_alertas_proyecto(proyecto_id: int, solo_activas: bool = True) -> List[Dict]:
    """Obtener alertas de un proyecto."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM alertas WHERE proyecto_id = ?"
    if solo_activas:
        query += " AND resuelta = 0"
    query += " ORDER BY fecha DESC"
    cursor.execute(query, (proyecto_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def resolver_alerta(alerta_id: int, automatica: bool = False) -> bool:
    """Marcar una alerta como resuelta."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alertas 
        SET resuelta = 1, fecha_resolucion = CURRENT_TIMESTAMP, resolucion_automatica = ?
        WHERE id = ?
    """, (1 if automatica else 0, alerta_id))
    actualizado = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return actualizado

def limpiar_alertas_obsoletas(proyecto_id: int, tipos_actuales: List[str]):
    """Resolver automáticamente alertas que ya no están presentes en el análisis."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener IDs de alertas activas del proyecto
    cursor.execute("""
        SELECT id, tipo FROM alertas 
        WHERE proyecto_id = ? AND resuelta = 0
    """, (proyecto_id,))
    alertas_pendientes = cursor.fetchall()
    
    for alerta in alertas_pendientes:
        al_id, al_tipo = alerta
        if al_tipo not in tipos_actuales:
            cursor.execute("""
                UPDATE alertas 
                SET resuelta = 1, fecha_resolucion = CURRENT_TIMESTAMP, resolucion_automatica = 1
                WHERE id = ?
            """, (al_id,))
            
    conn.commit()
    conn.close()


def detectar_proyectos_zombie(dias_inactividad: int = 4) -> List[int]:
    """
    Identifica proyectos activos/mvp que no han tenido actividad reciente.
    Retorna lista de IDs de proyectos zombie.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Proyectos en estado fluido (no terminados)
    cursor.execute("""
        SELECT id, nombre FROM proyectos 
        WHERE estado IN ('active', 'mvp', 'idea')
    """)
    candidatos = cursor.fetchall()
    zombies = []
    
    for c in candidatos:
        pid = c['id']
        
        # Verificar última métrica
        cursor.execute("SELECT MAX(fecha) FROM metricas WHERE proyecto_id = ?", (pid,))
        ultima_metrica = cursor.fetchone()[0]
        
        # Verificar última decisión
        cursor.execute("SELECT MAX(fecha) FROM decisiones WHERE proyecto_id = ?", (pid,))
        ultima_decision = cursor.fetchone()[0]
        
        # Fecha más reciente de actividad
        fechas = [f for f in [ultima_metrica, ultima_decision] if f is not None]
        
        if not fechas:
            # Si no hay nada, verificar fecha de creación del proyecto
            cursor.execute("SELECT fecha_inicio FROM proyectos WHERE id = ?", (pid,))
            f_ini = cursor.fetchone()
            ultima_actividad = f_ini[0] if f_ini else date.today().isoformat()
        else:
            ultima_actividad = max(fechas)
            
        # Calcular días de inactividad
        try:
            # Quitamos la Z o microsegundos si existen para el parseo simple
            fecha_limpia = ultima_actividad.split(' ')[0].split('T')[0]
            ua_dt = datetime.strptime(fecha_limpia, '%Y-%m-%d')
            hoy = datetime.now()
            dias = (hoy - ua_dt).days
            
            if dias >= dias_inactividad:
                zombies.append(pid)
        except Exception as e:
            # print(f"Error parseando fecha {ultima_actividad}: {e}")
            pass
            
    conn.close()
    return zombies


# ============================================================================
# VALIDACIÓN Y ANÁLISIS DE DATOS
# ============================================================================

def validar_datos_proyecto(proyecto_id: int) -> Dict:
    """
    Validar que un proyecto tiene datos suficientes para análisis.
    
    Args:
        proyecto_id: ID del proyecto
    
    Returns:
        Dict con: valido (bool), mensaje (str), datos (dict)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener métricas del proyecto
    cursor.execute("""
        SELECT 
            COUNT(*) as num_metricas,
            SUM(ingresos) as total_ingresos,
            SUM(tiempo_horas) as total_tiempo,
            SUM(conversiones) as total_conversiones
        FROM metricas
        WHERE proyecto_id = ?
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {
            'valido': False,
            'mensaje': 'No se encontraron datos del proyecto',
            'datos': {}
        }
    
    datos = dict(row)
    
    # Validación 1: ¿Hay métricas suficientes?
    if datos['num_metricas'] < 3:
        return {
            'valido': False,
            'tipo': 'datos_insuficientes',
            'mensaje': f"Solo {datos['num_metricas']} métricas registradas. Se necesitan al menos 3 para análisis confiable.",
            'datos': datos
        }
    
    # Validación 2: ¿Se registró tiempo?
    if datos['total_tiempo'] is None or datos['total_tiempo'] == 0:
        return {
            'valido': False,
            'tipo': 'sin_tiempo_registrado',
            'mensaje': 'No se ha registrado tiempo invertido. Sin esto, no se puede calcular ROI real.',
            'datos': datos
        }
    
    # Datos válidos
    return {
        'valido': True,
        'mensaje': 'Datos suficientes para análisis',
        'datos': datos
    }


def estimar_tiempo_minimo(proyecto_id: int) -> float:
    """
    Estimar tiempo mínimo invertido basado en estado del proyecto.
    Útil cuando usuario olvida registrar horas.
    
    Args:
        proyecto_id: ID del proyecto
    
    Returns:
        float: Horas estimadas
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            estado,
            (julianday('now') - julianday(fecha_inicio)) AS dias_desde_inicio
        FROM proyectos
        WHERE id = ?
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return 0.0
    
    estado, dias = row['estado'], row['dias_desde_inicio']
    
    # Heurística conservadora basada en estado
    if estado == 'idea':
        return dias * 0.5  # 30 min/día promedio en fase idea
    elif estado == 'mvp':
        return dias * 2.0  # 2 horas/día en desarrollo MVP
    elif estado == 'active':
        return dias * 1.0  # 1 hora/día mantenimiento
    elif estado == 'paused':
        return 0.0  # No se cuenta tiempo en pausa
    
    return 0.0


def analizar_proyecto_con_validacion(proyecto_id: int) -> Dict:
    """
    Analizar proyecto con validación de datos.
    Retorna análisis o advertencias si datos insuficientes.
    
    Args:
        proyecto_id: ID del proyecto
    
    Returns:
        Dict con análisis o advertencias
    """
    # Validar datos
    validacion = validar_datos_proyecto(proyecto_id)
    tipos_alertas_presentes = []
    
    if not validacion['valido']:
        tipo_alerta = validacion.get('tipo', 'error')
        mensaje = validacion['mensaje']
        tipos_alertas_presentes.append(tipo_alerta)
        
        # Registrar alerta si no existe ya una activa del mismo tipo
        alertas_existentes = obtener_alertas_proyecto(proyecto_id)
        if not any(a['tipo'] == tipo_alerta for a in alertas_existentes):
            crear_alerta(proyecto_id, tipo_alerta, mensaje, 'warning' if tipo_alerta == 'sin_tiempo_registrado' else 'info')
        
        # Limpiar obsoletas
        limpiar_alertas_obsoletas(proyecto_id, tipos_alertas_presentes)
        
        return {
            'proyecto_id': proyecto_id,
            'estado': 'advertencia',
            'tipo': tipo_alerta,
            'mensaje': mensaje,
            'datos': validacion['datos']
        }
    
    # Si llegamos aquí, los datos son válidos
    # Limpiar todas las alertas de validación
    limpiar_alertas_obsoletas(proyecto_id, [])
    
    # Datos válidos, calcular análisis
    datos = validacion['datos']
    dashboard = calcular_dashboard_proyecto(proyecto_id)
    
    # Calcular ROI
    roi = dashboard['roi']
    
    # Clasificación básica
    if roi > 50:
        clasificacion = 'winner'
        decision = 'scale'
    elif roi > 10:
        clasificacion = 'prometedor'
        decision = 'iterate'
    elif roi > 0:
        clasificacion = 'viable'
        decision = 'iterate'
    else:
        clasificacion = 'no_viable'
        decision = 'kill'
    
    return {
        'proyecto_id': proyecto_id,
        'estado': 'analizado',
        'clasificacion': clasificacion,
        'decision_sugerida': decision,
        'roi': roi,
        'datos': dashboard
    }


# ============================================================================
# INICIALIZACIÓN
# ============================================================================
def obtener_todas_alertas_activas() -> List[Dict]:
    """Obtiene todas las alertas no resueltas de todos los proyectos."""
    conn = get_connection()
    cursor = conn.execute("""
        SELECT a.*, p.nombre as proyecto_nombre 
        FROM alertas a
        JOIN proyectos p ON a.proyecto_id = p.id
        WHERE a.resuelta = 0 
        ORDER BY a.fecha DESC
    """)
    alertas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alertas

if __name__ == '__main__':
    """
    Script de inicialización: crear BD y ciclo inicial si no existen.
    """
    print("Inicializando base de datos...")
    init_database()
    print(f"[OK] Base de datos creada en: {DB_PATH}")
    
    # Verificar si existe ciclo activo
    ciclo = obtener_ciclo_activo()
    if not ciclo:
        print("\nNo hay ciclo activo. Creando ciclo 90D...")
        ciclo_id = crear_ciclo_90d()
        ciclo = obtener_ciclo_activo()
        print(f"[OK] Ciclo creado: {ciclo['fecha_inicio']} -> {ciclo['fecha_fin']}")
    else:
        print(f"\n[OK] Ciclo activo: {ciclo['fecha_inicio']} -> {ciclo['fecha_fin']}")
    
    # Mostrar fase actual
    fase = calcular_fase_actual(ciclo)
    print(f"\n[FASE] Día {fase['dia']}/90 - Fase: {fase['nombre']}")
    print(f"   Días restantes: {fase['dias_restantes']}")
    
    print("\n[OK] Sistema listo para usar")
