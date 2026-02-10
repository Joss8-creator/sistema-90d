# SUB-PROMPT 04: MOTOR DE MÉTRICAS Y ANÁLISIS AUTOMATIZADO

## CONTEXTO
Sistema 90D local. Base de datos SQLite con métricas temporales.
**Principio:** El sistema SUGIERE decisiones basadas en datos, NO las toma automáticamente.

## OBJETIVO
Implementar motor que:
1. Analice métricas en tiempo real
2. Detecte señales de kill/iterate/scale
3. Genere alertas accionables
4. Evite falsos positivos que erosionen confianza del usuario

---

## ARQUITECTURA DEL MOTOR

```python
# /sistema_90d/motor_metricas.py

from typing import Dict, List, Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3

DecisionType = Literal['kill', 'iterate', 'scale', 'continuar']

@dataclass
class Señal:
    """Representa una señal detectada en las métricas."""
    proyecto_id: int
    tipo: str                    # Ej: "sin_ingresos", "crecimiento_constante"
    severidad: Literal['info', 'warning', 'critical']
    mensaje: str
    datos_soporte: Dict          # Métricas que justifican la señal
    decision_sugerida: DecisionType
```

---

## REGLAS DE DECISIÓN (HEURÍSTICAS)

### Regla 1: KILL — Sin ingresos en N días
```python
def detectar_kill_sin_ingresos(
    proyecto_id: int,
    umbral_dias: int,
    db: sqlite3.Connection
) -> Señal | None:
    """
    Detecta si un proyecto no ha generado ingresos en N días consecutivos.
    
    Complejidad: O(n) donde n = métricas recientes del proyecto (típicamente <100)
    """
    cursor = db.execute("""
        SELECT COUNT(*) AS metricas_con_ingresos
        FROM metricas
        WHERE proyecto_id = ?
          AND fecha >= unixepoch('now', '-' || ? || ' days')
          AND ingresos > 0
    """, (proyecto_id, umbral_dias))
    
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Obtener última métrica para contexto
        cursor = db.execute("""
            SELECT fecha, tiempo_invertido 
            FROM metricas 
            WHERE proyecto_id = ? 
            ORDER BY fecha DESC LIMIT 1
        """, (proyecto_id,))
        
        ultima_metrica = cursor.fetchone()
        dias_desde_ultima = (datetime.now() - datetime.fromtimestamp(ultima_metrica[0])).days
        
        return Señal(
            proyecto_id=proyecto_id,
            tipo="sin_ingresos",
            severidad='critical',
            mensaje=f"Sin ingresos en {umbral_dias} días. Última métrica hace {dias_desde_ultima} días.",
            datos_soporte={
                'umbral_dias': umbral_dias,
                'tiempo_invertido_total': ultima_metrica[1]
            },
            decision_sugerida='kill'
        )
    
    return None
```

**Justificación vs alternativa:**
- Alternativa: Trigger SQL automático que mata el proyecto
- Elegida: Sugerencia humana final. Evita kills prematuros en proyectos con ingresos irregulares legítimos.

---

### Regla 2: KILL — ROI negativo persistente
```python
def detectar_kill_roi_negativo(
    proyecto_id: int,
    coste_hora_estimado: float,  # Ej: $50/hora
    db: sqlite3.Connection
) -> Señal | None:
    """
    Detecta si el proyecto consume tiempo sin generar retorno mínimo.
    
    ROI negativo = (ingresos / horas) < coste_hora_estimado
    """
    cursor = db.execute("""
        SELECT 
            SUM(ingresos) AS total_ingresos,
            SUM(tiempo_invertido) AS total_horas
        FROM metricas
        WHERE proyecto_id = ?
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    total_ingresos, total_horas = row
    
    if total_horas == 0:
        return None  # No hay datos suficientes
    
    roi_por_hora = total_ingresos / total_horas
    
    if roi_por_hora < coste_hora_estimado:
        deficit = (coste_hora_estimado - roi_por_hora) * total_horas
        
        return Señal(
            proyecto_id=proyecto_id,
            tipo="roi_negativo",
            severidad='warning',
            mensaje=f"ROI de ${roi_por_hora:.2f}/h está por debajo de tu coste de oportunidad (${coste_hora_estimado}/h). Déficit acumulado: ${deficit:.2f}",
            datos_soporte={
                'roi_por_hora': roi_por_hora,
                'coste_hora_estimado': coste_hora_estimado,
                'deficit_total': deficit
            },
            decision_sugerida='kill'
        )
    
    return None
```

**Crítica a esta regla:**
- **Problema:** En fase temprana, ROI negativo es esperado
- **Solución:** Aplicar solo si `dias_desde_inicio > 45` (pasada fase de experimentación)

```python
def detectar_kill_roi_negativo(proyecto_id: int, ...) -> Señal | None:
    # ... (código anterior)
    
    # Obtener días desde inicio
    cursor = db.execute("""
        SELECT (unixepoch('now') - fecha_inicio) / 86400 AS dias
        FROM proyectos WHERE id = ?
    """, (proyecto_id,))
    dias_desde_inicio = cursor.fetchone()[0]
    
    # Solo aplicar después de 45 días
    if dias_desde_inicio < 45:
        return None
    
    # ... (resto del código)
```

---

### Regla 3: SCALE — Crecimiento consistente de ingresos
```python
def detectar_scale_crecimiento_consistente(
    proyecto_id: int,
    ventana_dias: int = 30,
    umbral_crecimiento: float = 0.20,  # 20% MoM
    db: sqlite3.Connection
) -> Señal | None:
    """
    Detecta crecimiento mensual sostenido.
    
    Crecimiento = (ingresos_mes_actual - ingresos_mes_anterior) / ingresos_mes_anterior
    """
    cursor = db.execute("""
        SELECT 
            strftime('%Y-%m', datetime(fecha, 'unixepoch')) AS mes,
            SUM(ingresos) AS ingresos_mes
        FROM metricas
        WHERE proyecto_id = ?
          AND fecha >= unixepoch('now', '-90 days')
        GROUP BY mes
        ORDER BY mes ASC
    """, (proyecto_id,))
    
    meses = cursor.fetchall()
    
    if len(meses) < 2:
        return None  # No hay datos suficientes para comparar
    
    # Calcular crecimiento mes a mes
    crecimientos = []
    for i in range(1, len(meses)):
        mes_anterior = meses[i-1][1]
        mes_actual = meses[i][1]
        
        if mes_anterior == 0:
            continue
        
        crecimiento = (mes_actual - mes_anterior) / mes_anterior
        crecimientos.append(crecimiento)
    
    if not crecimientos:
        return None
    
    # Crecimiento promedio
    crecimiento_promedio = sum(crecimientos) / len(crecimientos)
    
    # Detectar si todos los crecimientos son positivos (sin retrocesos)
    todos_positivos = all(c > 0 for c in crecimientos)
    
    if crecimiento_promedio >= umbral_crecimiento and todos_positivos:
        return Señal(
            proyecto_id=proyecto_id,
            tipo="crecimiento_consistente",
            severidad='info',
            mensaje=f"Crecimiento promedio de {crecimiento_promedio*100:.1f}% MoM sin retrocesos. Candidato a Winner.",
            datos_soporte={
                'crecimiento_promedio': crecimiento_promedio,
                'meses_consecutivos': len(crecimientos),
                'ultimo_mes_ingresos': meses[-1][1]
            },
            decision_sugerida='scale'
        )
    
    return None
```

**Complejidad:** O(m) donde m = meses con datos (máximo 3 en ventana de 90 días).

---

### Regla 4: ITERATE — Conversión baja con tráfico alto
```python
def detectar_iterate_conversion_baja(
    proyecto_id: int,
    umbral_conversion: float = 0.02,  # 2%
    umbral_trafico_min: int = 100,
    db: sqlite3.Connection
) -> Señal | None:
    """
    Detecta tráfico significativo pero conversión baja.
    Indica problema en onboarding/pricing, no en distribución.
    """
    cursor = db.execute("""
        SELECT 
            SUM(conversiones) AS total_conversiones,
            -- Asumimos que 'trafico' es una columna que agregaremos
            -- Por ahora, inferimos trafico de número de métricas registradas
            COUNT(*) AS proxies_trafico
        FROM metricas
        WHERE proyecto_id = ?
          AND fecha >= unixepoch('now', '-30 days')
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    total_conversiones, proxies_trafico = row
    
    # Heurística: si hay >10 métricas en 30 días, asumimos tráfico significativo
    if proxies_trafico < 10:
        return None
    
    # Conversion rate aproximado
    # NOTA: Esto es una simplificación. En producción, necesitarías una columna 'visitas'
    conversion_estimada = total_conversiones / (proxies_trafico * 10)  # Asumiendo 10 visitas/día
    
    if conversion_estimada < umbral_conversion:
        return Señal(
            proyecto_id=proyecto_id,
            tipo="conversion_baja",
            severidad='warning',
            mensaje=f"Conversión estimada de {conversion_estimada*100:.2f}% está por debajo del {umbral_conversion*100}%. Revisa onboarding o pricing.",
            datos_soporte={
                'conversion_estimada': conversion_estimada,
                'total_conversiones': total_conversiones
            },
            decision_sugerida='iterate'
        )
    
    return None
```

**PROBLEMA DETECTADO:** Esta regla asume una columna `visitas` que no existe en el modelo de datos actual.

**SOLUCIÓN:** 
1. **Opción A (MVP):** Eliminar esta regla hasta tener datos de tráfico reales
2. **Opción B (recomendada):** Agregar columna `visitas` en tabla `metricas`

```sql
-- Migración para agregar columna
ALTER TABLE metricas ADD COLUMN visitas INTEGER DEFAULT 0;
```

**Decisión:** Implementar Opción A en MVP. Regla se activa en Fase 2.

---

### Regla 5: ALERTA — Concentración de ingresos >80%
```python
def detectar_riesgo_concentracion(
    umbral: float = 0.80,
    db: sqlite3.Connection
) -> List[Señal]:
    """
    Detecta si un proyecto representa >80% de ingresos totales.
    Riesgo: dependencia excesiva de un solo producto.
    """
    cursor = db.execute("""
        SELECT 
            p.id,
            p.nombre,
            SUM(m.ingresos) AS ingresos_proyecto,
            (SELECT SUM(ingresos) FROM metricas) AS ingresos_totales
        FROM proyectos p
        JOIN metricas m ON m.proyecto_id = p.id
        WHERE p.estado IN ('active', 'winner')
        GROUP BY p.id
    """)
    
    señales = []
    for row in cursor.fetchall():
        proyecto_id, nombre, ingresos_proyecto, ingresos_totales = row
        
        if ingresos_totales == 0:
            continue
        
        concentracion = ingresos_proyecto / ingresos_totales
        
        if concentracion > umbral:
            señales.append(Señal(
                proyecto_id=proyecto_id,
                tipo="concentracion_ingresos",
                severidad='warning',
                mensaje=f"{nombre} representa {concentracion*100:.1f}% de tus ingresos totales. Considera diversificar.",
                datos_soporte={
                    'concentracion': concentracion,
                    'ingresos_proyecto': ingresos_proyecto,
                    'ingresos_totales': ingresos_totales
                },
                decision_sugerida='continuar'  # No es kill, es alerta
            ))
    
    return señales
```

---

## MOTOR DE ANÁLISIS COMPLETO

```python
# /sistema_90d/motor_metricas.py

class MotorMetricas:
    """
    Motor central de análisis de métricas.
    Ejecuta todas las reglas y retorna señales detectadas.
    """
    
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.config = self._cargar_config()
    
    def _cargar_config(self) -> Dict:
        """Carga parámetros configurables desde la DB."""
        cursor = self.db.execute("SELECT clave, valor FROM config_sistema")
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def analizar_proyecto(self, proyecto_id: int) -> List[Señal]:
        """
        Ejecuta todas las reglas sobre un proyecto específico.
        
        Complejidad: O(n*r) donde n=métricas, r=reglas (típicamente <10)
        En la práctica: <50ms con 100 métricas y 5 reglas
        """
        señales = []
        
        # Regla 1: Sin ingresos
        señal = detectar_kill_sin_ingresos(
            proyecto_id, 
            int(self.config['umbral_kill_dias']),
            self.db
        )
        if señal:
            señales.append(señal)
        
        # Regla 2: ROI negativo (solo después de 45 días)
        señal = detectar_kill_roi_negativo(
            proyecto_id,
            float(self.config.get('coste_hora_estimado', 50)),
            self.db
        )
        if señal:
            señales.append(señal)
        
        # Regla 3: Crecimiento consistente
        señal = detectar_scale_crecimiento_consistente(
            proyecto_id,
            db=self.db
        )
        if señal:
            señales.append(señal)
        
        # (Regla 4 excluida del MVP)
        
        return señales
    
    def analizar_todos_los_proyectos(self) -> Dict[int, List[Señal]]:
        """
        Ejecuta análisis sobre todos los proyectos activos.
        Retorna diccionario {proyecto_id: [señales]}
        """
        cursor = self.db.execute("""
            SELECT id FROM proyectos 
            WHERE estado IN ('active', 'mvp', 'idea')
        """)
        
        resultados = {}
        for (proyecto_id,) in cursor.fetchall():
            señales = self.analizar_proyecto(proyecto_id)
            if señales:
                resultados[proyecto_id] = señales
        
        # Análisis globales (concentración, etc.)
        señales_globales = detectar_riesgo_concentracion(db=self.db)
        if señales_globales:
            resultados['global'] = señales_globales
        
        return resultados
```

---

## INTEGRACIÓN CON UI

```python
# /sistema_90d/app.py (fragmento)

from motor_metricas import MotorMetricas

@app.route('/dashboard')
def dashboard():
    motor = MotorMetricas('data/sistema.db')
    analisis = motor.analizar_todos_los_proyectos()
    
    # Convertir señales en alertas visibles
    alertas = []
    for proyecto_id, señales in analisis.items():
        for señal in señales:
            alertas.append({
                'proyecto_id': proyecto_id,
                'tipo': señal.severidad,
                'mensaje': señal.mensaje,
                'decision_sugerida': señal.decision_sugerida
            })
    
    return render_template('dashboard.html', alertas=alertas, ...)
```

---

## COMPARATIVA VS SOLUCIÓN "MODERNA"

### Stack moderno (ML-based prediction)
- Usar scikit-learn para predecir éxito de proyecto
- Requiere: 100+ proyectos históricos, feature engineering, retraining
- **Overhead:** 50MB+ de dependencias

### Stack elegido (Heurísticas explícitas)
- Reglas if/else basadas en umbrales configurables
- **Ventajas:**
  - 100% explicable (usuario entiende por qué se sugiere kill)
  - Cero dependencias ML
  - Ajustable sin reentrenar
- **Desventajas:**
  - No aprende de errores pasados (mitigable con tabla `decisiones`)

**Decisión:** Heurísticas en MVP. ML solo si se acumulan >50 proyectos con decisiones etiquetadas.

---

## OPTIMIZACIONES CONSIDERADAS PERO NO APLICADAS

### 1. Caché de análisis recientes
**Razón:** Análisis <50ms. Caché agregaría complejidad sin beneficio medible.

### 2. Análisis asíncrono con workers
**Razón:** Solopreneur = 1 usuario. No hay concurrencia real.

### 3. Integración con webhooks (Stripe, Google Analytics)
**Razón:** MVP requiere input manual. Automatización en Fase 2.

---

## ENTREGABLE ESPERADO

1. **Archivo motor_metricas.py** completo con:
   - Clase `MotorMetricas`
   - Funciones de detección de señales
   - Comentarios de complejidad

2. **Tests unitarios** para cada regla:
   ```python
   # /tests/test_motor_metricas.py
   def test_detectar_kill_sin_ingresos():
       # Crear DB en memoria
       db = sqlite3.connect(':memory:')
       # Insertar proyecto sin ingresos
       # Ejecutar regla
       # Assert señal detectada
   ```

**Siguiente paso:** Si motor aprobado, ejecutar `05_SISTEMA_IA.md`
