# SUB-PROMPT 06: FLUJOS OPERATIVOS DIARIOS Y SEMANALES

## CONTEXTO
Sistema 90D local. Usuario es solopreneur con tiempo limitado.
**Principio:** Cada ritual debe tomar <15 minutos y generar valor inmediato.

## OBJETIVO
Definir rutinas operativas mínimas que:
1. Mantengan el sistema actualizado
2. Eviten acumulación de datos obsoletos
3. Fuercen decisiones regulares (anti-procrastinación)

---

## RITUALES OBLIGATORIOS

### 1. RITUAL DIARIO (5-10 minutos)
**Cuándo:** Final del día laboral (antes de cerrar computadora)

**Checklist:**
```
□ Registrar métrica del día (si aplica)
  - ¿Trabajé en algún proyecto hoy?
  - ¿Cuántas horas?
  - ¿Hubo ingresos?
  - ¿Conversiones?

□ Revisar alertas pendientes
  - ¿Hay señales críticas nuevas?
  - ¿Necesito tomar decisión urgente?

□ Actualizar estado de proyecto si cambió
  - ¿Lancé el MVP hoy? → cambiar de 'idea' a 'mvp'
  - ¿Pausé algo? → marcar como 'paused'
```

**Implementación en el sistema:**
```python
# /sistema_90d/app.py

@app.route('/ritual-diario')
def ritual_diario():
    """
    Pantalla guiada para completar ritual diario.
    """
    # Detectar proyectos con actividad reciente (última métrica <24h)
    cursor = db.execute("""
        SELECT DISTINCT p.id, p.nombre
        FROM proyectos p
        JOIN metricas m ON m.proyecto_id = p.id
        WHERE m.fecha >= unixepoch('now', '-1 day')
    """)
    proyectos_con_actividad = cursor.fetchall()
    
    # Proyectos activos SIN métrica hoy
    cursor = db.execute("""
        SELECT p.id, p.nombre
        FROM proyectos p
        WHERE p.estado IN ('active', 'mvp')
          AND NOT EXISTS (
            SELECT 1 FROM metricas m 
            WHERE m.proyecto_id = p.id 
              AND date(m.fecha, 'unixepoch') = date('now')
          )
    """)
    proyectos_sin_metrica_hoy = cursor.fetchall()
    
    # Alertas pendientes
    cursor = db.execute("""
        SELECT tipo, mensaje 
        FROM alertas 
        WHERE resuelta = 0
        ORDER BY fecha DESC
        LIMIT 5
    """)
    alertas = cursor.fetchall()
    
    return render_template('ritual_diario.html',
        proyectos_con_actividad=proyectos_con_actividad,
        proyectos_sin_metrica_hoy=proyectos_sin_metrica_hoy,
        alertas=alertas
    )
```

**HTML del ritual:**
```html
<!-- /sistema_90d/templates/ritual_diario.html -->
<h1>📋 Ritual Diario — {{ fecha_hoy }}</h1>

<section>
  <h2>1️⃣ ¿Trabajaste en algún proyecto hoy?</h2>
  
  {% if proyectos_sin_metrica_hoy %}
    <p>Estos proyectos activos no tienen métrica registrada hoy:</p>
    <ul>
      {% for id, nombre in proyectos_sin_metrica_hoy %}
      <li>
        <strong>{{ nombre }}</strong>
        <button hx-get="/metricas/nueva?proyecto_id={{ id }}&prefill_fecha=hoy" 
                hx-target="#modal" 
                class="btn-primary">Registrar métrica</button>
        <button hx-post="/proyectos/{{ id }}/marcar-sin-actividad-hoy" 
                class="btn-secondary">No trabajé en esto</button>
      </li>
      {% endfor %}
    </ul>
  {% else %}
    <p>✅ Todas las métricas al día.</p>
  {% endif %}
</section>

<section>
  <h2>2️⃣ Alertas Pendientes</h2>
  
  {% if alertas %}
    {% for tipo, mensaje in alertas %}
    <div class="alert alert-{{ tipo }}">
      {{ mensaje }}
      <button hx-post="/alertas/resolver/{{ loop.index }}" class="btn-sm">Resolver</button>
    </div>
    {% endfor %}
  {% else %}
    <p>✅ Sin alertas pendientes.</p>
  {% endif %}
</section>

<section>
  <h2>3️⃣ Cambios de Estado</h2>
  
  <p>¿Algún proyecto cambió de fase hoy?</p>
  <form hx-post="/proyectos/cambiar-estado">
    <select name="proyecto_id">
      {% for p in proyectos_activos %}
      <option value="{{ p.id }}">{{ p.nombre }} ({{ p.estado }})</option>
      {% endfor %}
    </select>
    
    <select name="nuevo_estado">
      <option value="idea">Idea</option>
      <option value="mvp">MVP</option>
      <option value="active">Activo</option>
      <option value="paused">Pausado</option>
      <option value="killed">Killed</option>
    </select>
    
    <button type="submit" class="btn-primary">Actualizar</button>
  </form>
</section>

<footer>
  <button hx-post="/ritual-diario/completar" 
          hx-target="body" 
          class="btn-success">✅ Completar Ritual</button>
</footer>
```

**Anti-patrón detectado:**
El sistema NO debe forzar registro de métricas si no hubo actividad. Eso genera datos falsos (métricas de $0 cuando simplemente no se trabajó en el proyecto).

**Solución:**
Botón "No trabajé en esto" que registra un flag sin crear métrica. Esto permite diferenciar:
- `sin_metrica_hoy + trabajé = olvidé registrar` (alerta)
- `sin_metrica_hoy + no_trabajé = correcto` (sin alerta)

---

### 2. RITUAL SEMANAL (15-30 minutos)
**Cuándo:** Domingo tarde o Lunes mañana (inicio de semana)

**Checklist:**
```
□ Generar análisis IA semanal
  - Exportar prompt
  - Pegar en IA
  - Revisar recomendaciones

□ Tomar decisión sobre al menos 1 proyecto
  - ¿Algo debe morir?
  - ¿Algo debe escalar?
  - ¿Algo necesita iteración?

□ Ajustar plan de la semana
  - ¿Qué proyecto es prioridad?
  - ¿Qué experimento lanzo?
  - ¿Qué métrica quiero mejorar?

□ Revisar alertas de riesgo
  - ¿Concentración de ingresos?
  - ¿Proyectos zombies (sin decisión hace >14 días)?
```

**Implementación:**
```python
# /sistema_90d/app.py

@app.route('/ritual-semanal')
def ritual_semanal():
    """
    Dashboard del ritual semanal.
    """
    from generador_prompts import GeneradorPrompts
    from motor_metricas import MotorMetricas
    
    # Generar análisis IA
    generador = GeneradorPrompts('data/sistema.db')
    prompt_ia = generador.generar_analisis_semanal()
    
    # Detectar proyectos sin decisión reciente
    cursor = db.execute("""
        SELECT p.id, p.nombre, 
               (unixepoch('now') - MAX(COALESCE(d.fecha, p.creado_en))) / 86400 AS dias_sin_decision
        FROM proyectos p
        LEFT JOIN decisiones d ON d.proyecto_id = p.id
        WHERE p.estado IN ('active', 'mvp')
        GROUP BY p.id
        HAVING dias_sin_decision > 14
    """)
    proyectos_zombies = cursor.fetchall()
    
    # Análisis de riesgos
    motor = MotorMetricas('data/sistema.db')
    analisis = motor.analizar_todos_los_proyectos()
    
    return render_template('ritual_semanal.html',
        prompt_ia=prompt_ia,
        proyectos_zombies=proyectos_zombies,
        analisis=analisis
    )
```

---

### 3. RITUAL DE FASE (Cada 15-30 días)
**Cuándo:** Al cambiar de fase del ciclo 90D

**Fases y sus rituales específicos:**

#### Fase 1 → Fase 2 (Día 15): Exploración → Experimentación
```
□ Seleccionar 2-3 ideas para convertir en MVPs
□ Definir criterio de kill para cada una
  - Ejemplo: "Si no genera $100 en 30 días → kill"
□ Configurar umbrales en config_sistema
□ Registrar hipótesis clara en cada proyecto
```

#### Fase 2 → Fase 3 (Día 46): Experimentación → Decisión
```
□ Clasificar TODOS los proyectos activos
  - ❌ Kill inmediato
  - 🔁 Iterate con plan concreto
  - 🚀 Candidatos a Winner
□ Ejecutar kills sin remordimiento
□ Documentar aprendizajes de cada kill
```

#### Fase 3 → Fase 4 (Día 76): Decisión → Consolidación
```
□ Declarar 1-2 Winners
□ Matar o pausar todo lo demás
□ Reducir exposición pública del winner
□ Crear plan de mejora técnica
□ Definir métricas de escalado (MRR objetivo, churn máximo, etc.)
```

**Implementación:**
```python
# /sistema_90d/app.py

@app.route('/ritual-fase')
def ritual_fase():
    """
    Wizard guiado para transiciones de fase.
    """
    contexto = obtener_contexto_ciclo()
    fase_actual = contexto['fase_actual']
    
    if fase_actual == 'exploracion':
        return render_template('ritual_fase_exploracion.html', **contexto)
    elif fase_actual == 'experimentacion':
        return render_template('ritual_fase_experimentacion.html', **contexto)
    # ... etc
```

---

## NOTIFICACIONES Y RECORDATORIOS

### Sistema de recordatorios (sin email)
```python
# /sistema_90d/recordatorios.py

class SistemaRecordatorios:
    """
    Detecta cuándo el usuario debe ejecutar un ritual.
    NO envía emails (complejidad innecesaria).
    """
    
    @staticmethod
    def debe_hacer_ritual_diario(db: sqlite3.Connection) -> bool:
        """Detecta si el ritual diario está pendiente hoy."""
        cursor = db.execute("""
            SELECT COUNT(*) FROM rituales_completados
            WHERE tipo = 'diario'
              AND date(fecha, 'unixepoch') = date('now')
        """)
        return cursor.fetchone()[0] == 0
    
    @staticmethod
    def debe_hacer_ritual_semanal(db: sqlite3.Connection) -> bool:
        """Detecta si el ritual semanal está pendiente esta semana."""
        cursor = db.execute("""
            SELECT COUNT(*) FROM rituales_completados
            WHERE tipo = 'semanal'
              AND strftime('%Y-%W', date(fecha, 'unixepoch')) = strftime('%Y-%W', 'now')
        """)
        return cursor.fetchone()[0] == 0
    
    @staticmethod
    def obtener_recordatorios(db: sqlite3.Connection) -> list[str]:
        """Retorna lista de recordatorios pendientes."""
        recordatorios = []
        
        if SistemaRecordatorios.debe_hacer_ritual_diario(db):
            recordatorios.append("⏰ Ritual diario pendiente")
        
        if SistemaRecordatorios.debe_hacer_ritual_semanal(db):
            recordatorios.append("📅 Ritual semanal pendiente")
        
        # Detectar si está cerca de cambio de fase
        cursor = db.execute("""
            SELECT (unixepoch('now') - unixepoch(valor)) / 86400 AS dia_actual
            FROM config_sistema WHERE clave = 'fecha_inicio_ciclo'
        """)
        dia_actual = int(cursor.fetchone()[0])
        
        # Avisar 2 días antes de transición de fase
        if dia_actual in [13, 43, 73]:
            recordatorios.append(f"🚨 Cambio de fase en 2 días (Día {dia_actual}/90)")
        
        return recordatorios
```

**Visualización en dashboard:**
```html
<!-- En templates/dashboard.html -->
{% set recordatorios = obtener_recordatorios() %}
{% if recordatorios %}
<aside class="recordatorios-panel">
  <h3>⏰ Recordatorios</h3>
  <ul>
    {% for recordatorio in recordatorios %}
    <li>{{ recordatorio }}</li>
    {% endfor %}
  </ul>
</aside>
{% endif %}
```

---

## TABLA DE RITUALES COMPLETADOS

```sql
-- Agregar a schema de base de datos
CREATE TABLE rituales_completados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tipo TEXT NOT NULL CHECK(tipo IN ('diario', 'semanal', 'fase')),
  fecha INTEGER NOT NULL DEFAULT (unixepoch()),
  notas TEXT
);

CREATE INDEX idx_rituales_tipo_fecha ON rituales_completados(tipo, fecha);
```

**Función de marcado:**
```python
def completar_ritual(tipo: str, notas: str = None):
    """Registra la completación de un ritual."""
    db.execute("""
        INSERT INTO rituales_completados (tipo, fecha, notas)
        VALUES (?, unixepoch('now'), ?)
    """, (tipo, notas))
    db.commit()
```

---

## ANTI-PATRONES A EVITAR

### ❌ NO HACER: Recordatorios por email
**Razón:** Requiere configuración SMTP, credenciales, manejo de spam. Overhead innecesario.
**Alternativa:** Notificación visual en dashboard cuando usuario abre el sistema.

### ❌ NO HACER: Gamificación (streaks, puntos)
**Razón:** El objetivo es tomar decisiones, no "sentirse productivo".
**Alternativa:** Métricas duras (ingresos, ROI) son la única gamificación necesaria.

### ❌ NO HACER: Rituales obligatorios bloqueantes
**Razón:** Si el usuario quiere saltearse un ritual, debe poder hacerlo.
**Alternativa:** Recordatorios visibles, pero nunca bloquear acceso al sistema.

---

## FLUJO DE UN DÍA TÍPICO

**Mañana (9:00 AM):**
```
1. Abrir http://localhost:8080
2. Ver banner: "Día 34/90 - Fase: Experimentación"
3. Ver recordatorio: "⏰ Ritual diario de ayer pendiente"
4. [Opcional] Completar ritual diario de ayer (si se olvidó)
5. Revisar dashboard de proyectos
6. Decidir en qué trabajar hoy
```

**Durante el día:**
```
[Trabajar en proyecto seleccionado]
[Sistema no interrumpe]
```

**Tarde (6:00 PM):**
```
1. Abrir /ritual-diario
2. Registrar métricas del día (2 minutos)
3. Revisar alertas (1 minuto)
4. Marcar ritual como completado
5. Cerrar sistema
```

**Domingo 8:00 PM (ritual semanal):**
```
1. Abrir /ritual-semanal
2. Generar prompt IA (clic)
3. Copiar → pegar en ChatGPT
4. Leer análisis de IA
5. Tomar decisión: kill 1 proyecto
6. Registrar decisión en sistema
7. Marcar ritual semanal como completado
```

---

## MÉTRICAS DE ADHERENCIA AL SISTEMA

```python
# /sistema_90d/metricas_adherencia.py

def calcular_adherencia(db: sqlite3.Connection) -> dict:
    """
    Calcula métricas de uso del sistema.
    Útil para detectar si el usuario está abandonando el sistema.
    """
    cursor = db.execute("""
        SELECT 
            COUNT(DISTINCT date(fecha, 'unixepoch')) AS dias_con_metricas_ultimos_30,
            COUNT(*) AS total_metricas_ultimos_30
        FROM metricas
        WHERE fecha >= unixepoch('now', '-30 days')
    """)
    dias_activos, total_metricas = cursor.fetchone()
    
    cursor = db.execute("""
        SELECT COUNT(*) FROM rituales_completados
        WHERE tipo = 'diario'
          AND fecha >= unixepoch('now', '-7 days')
    """)
    rituales_diarios_semana = cursor.fetchone()[0]
    
    # Adherencia diaria = % de días con actividad
    adherencia_diaria = (dias_activos / 30) * 100
    
    # Adherencia ritual = % de rituales completados
    adherencia_ritual = (rituales_diarios_semana / 7) * 100
    
    return {
        'adherencia_diaria_pct': adherencia_diaria,
        'adherencia_ritual_pct': adherencia_ritual,
        'dias_activos_ultimos_30': dias_activos,
        'alerta': adherencia_diaria < 50 or adherencia_ritual < 70
    }
```

**Alerta de abandono:**
Si `adherencia_diaria < 50%` → Mostrar mensaje:
> "⚠️ Has usado el sistema solo X días de los últimos 30. Si no estás registrando métricas, no puedes tomar decisiones basadas en datos. ¿Algo no está funcionando?"

---

## COMPARATIVA VS SOLUCIÓN "MODERNA"

### Stack moderno (Notion + Zapier + Calendly)
- Notion para proyectos + métricas
- Zapier para recordatorios
- Calendly para bloquear tiempo de rituales
- **Overhead:** 3 herramientas, sincronización manual, $20/mes

### Stack elegido (Sistema local integrado)
- Todo en un solo sistema
- Recordatorios automáticos sin email
- **Overhead:** Cero, gratis, offline

---

## ENTREGABLE ESPERADO

1. **Archivos HTML** de rituales:
   - ritual_diario.html
   - ritual_semanal.html
   - ritual_fase_exploracion.html, etc.

2. **Rutas en app.py**:
   ```python
   @app.route('/ritual-diario')
   @app.route('/ritual-semanal')
   @app.route('/ritual-fase')
   ```

3. **Tabla rituales_completados** en schema SQL

4. **Clase SistemaRecordatorios** con lógica de detección

**Siguiente paso:** Si flujos aprobados, ejecutar `07_PLAN_IMPLEMENTACION.md`
