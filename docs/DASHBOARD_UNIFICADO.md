# DASHBOARD UNIFICADO DEL SISTEMA 90D

## CONCEPTO: CENTRO DE COMANDO OPERATIVO

El dashboard actual es pasivo (solo muestra datos). Necesitamos un **hub activo** que:
1. Muestre estado del sistema en tiempo real
2. Permita ejecutar todas las herramientas desde un solo lugar
3. Guíe proactivamente al usuario según contexto
4. Sea el "home" del que nunca necesitas salir

---

## ARQUITECTURA DEL NUEVO DASHBOARD

### Layout en 4 cuadrantes

```
┌─────────────────────────────────────────────────────┐
│ [HEADER] Día 34/90 - Fase: Experimentación         │
│ Siguiente acción: ⏰ Ritual diario pendiente        │
├──────────────────────┬──────────────────────────────┤
│                      │                              │
│  CUADRANTE 1         │    CUADRANTE 2               │
│  Estado del Sistema  │    Acciones Rápidas          │
│  (read-only)         │    (botones ejecutables)     │
│                      │                              │
├──────────────────────┼──────────────────────────────┤
│                      │                              │
│  CUADRANTE 3         │    CUADRANTE 4               │
│  Proyectos Activos   │    Análisis y Alertas        │
│  (tabla interactiva) │    (insights de IA)          │
│                      │                              │
└──────────────────────┴──────────────────────────────┘
```

---

## IMPLEMENTACIÓN DETALLADA

### CUADRANTE 1: Estado del Sistema (Monitoring)

```python
# /sistema_90d/dashboard_data.py

from datetime import datetime
from database import get_db
from health import verificar_salud_sistema
from motor_metricas import MotorMetricas

def obtener_estado_sistema() -> dict:
    """
    Recopila todas las métricas del sistema en un solo objeto.
    
    Complejidad: O(n) donde n = proyectos + métricas (típicamente <100ms)
    """
    db = get_db()
    
    # 1. Ciclo 90D
    cursor = db.execute("""
        SELECT valor FROM config_sistema WHERE clave = 'fecha_inicio_ciclo'
    """)
    fecha_inicio = datetime.fromisoformat(cursor.fetchone()[0])
    dia_actual = (datetime.now() - fecha_inicio).days + 1
    dias_restantes = 90 - dia_actual
    progreso_pct = (dia_actual / 90) * 100
    
    # Determinar fase
    if dia_actual <= 14:
        fase = {'nombre': 'Exploración', 'color': 'blue', 'icono': '🔍'}
    elif dia_actual <= 45:
        fase = {'nombre': 'Experimentación', 'color': 'orange', 'icono': '🧪'}
    elif dia_actual <= 75:
        fase = {'nombre': 'Decisión', 'color': 'red', 'icono': '🎯'}
    else:
        fase = {'nombre': 'Consolidación', 'color': 'green', 'icono': '🚀'}
    
    # 2. Proyectos
    cursor = db.execute("""
        SELECT 
            COUNT(CASE WHEN estado IN ('active', 'mvp') THEN 1 END) as activos,
            COUNT(CASE WHEN estado = 'winner' THEN 1 END) as winners,
            COUNT(CASE WHEN estado = 'killed' THEN 1 END) as killed,
            COUNT(CASE WHEN estado = 'paused' THEN 1 END) as pausados
        FROM proyectos
    """)
    proyectos = cursor.fetchone()
    
    # 3. Métricas agregadas
    cursor = db.execute("""
        SELECT 
            SUM(ingresos) as ingresos_totales,
            SUM(tiempo_invertido) as horas_totales,
            COUNT(DISTINCT proyecto_id) as proyectos_con_metricas,
            MAX(fecha) as ultima_metrica
        FROM metricas
        WHERE fecha >= unixepoch('now', '-30 days')
    """)
    metricas = cursor.fetchone()
    
    roi_global = (metricas[0] / metricas[1]) if metricas[1] > 0 else 0
    
    # 4. Salud del sistema
    salud = verificar_salud_sistema()
    
    # 5. Adherencia (uso del sistema)
    cursor = db.execute("""
        SELECT 
            COUNT(DISTINCT date(fecha, 'unixepoch')) as dias_activos
        FROM metricas
        WHERE fecha >= unixepoch('now', '-30 days')
    """)
    dias_activos = cursor.fetchone()[0]
    adherencia_pct = (dias_activos / 30) * 100
    
    # 6. Rituales completados
    cursor = db.execute("""
        SELECT 
            COUNT(CASE WHEN tipo = 'diario' THEN 1 END) as diarios,
            COUNT(CASE WHEN tipo = 'semanal' THEN 1 END) as semanales
        FROM rituales_completados
        WHERE fecha >= unixepoch('now', '-30 days')
    """)
    rituales = cursor.fetchone()
    
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
            'activos': proyectos[0],
            'winners': proyectos[1],
            'killed': proyectos[2],
            'pausados': proyectos[3],
            'total': sum(proyectos)
        },
        'metricas_30d': {
            'ingresos_totales': round(metricas[0] or 0, 2),
            'horas_totales': round(metricas[1] or 0, 1),
            'roi_por_hora': round(roi_global, 2),
            'proyectos_con_metricas': metricas[2],
            'ultima_metrica_fecha': datetime.fromtimestamp(metricas[3]).strftime('%Y-%m-%d') if metricas[3] else 'Nunca'
        },
        'adherencia': {
            'dias_activos': dias_activos,
            'porcentaje': round(adherencia_pct, 1),
            'status': 'excelente' if adherencia_pct >= 80 else 'buena' if adherencia_pct >= 50 else 'baja'
        },
        'rituales': {
            'diarios_completados': rituales[0],
            'semanales_completados': rituales[1],
            'diarios_esperados': 30,
            'semanales_esperados': 4
        },
        'salud': salud
    }
```

**HTML del Cuadrante 1:**

```html
<!-- /sistema_90d/templates/components/estado_sistema.html -->

<div class="cuadrante cuadrante-estado">
    <h2>📊 Estado del Sistema</h2>
    
    <!-- Ciclo 90D -->
    <div class="widget widget-ciclo">
        <div class="widget-header">
            <span class="fase-badge fase-{{ estado.fase.color }}">
                {{ estado.fase.icono }} {{ estado.fase.nombre }}
            </span>
            <span class="dia-badge">Día {{ estado.ciclo.dia_actual }}/90</span>
        </div>
        
        <!-- Barra de progreso -->
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ estado.ciclo.progreso_pct }}%"></div>
        </div>
        <p class="progress-text">{{ estado.ciclo.dias_restantes }} días restantes</p>
    </div>
    
    <!-- Proyectos -->
    <div class="widget widget-proyectos">
        <h3>Proyectos</h3>
        <div class="stats-grid">
            <div class="stat">
                <span class="stat-valor">{{ estado.proyectos.activos }}</span>
                <span class="stat-label">Activos</span>
            </div>
            <div class="stat stat-winner">
                <span class="stat-valor">{{ estado.proyectos.winners }}</span>
                <span class="stat-label">Winners</span>
            </div>
            <div class="stat stat-killed">
                <span class="stat-valor">{{ estado.proyectos.killed }}</span>
                <span class="stat-label">Killed</span>
            </div>
            <div class="stat">
                <span class="stat-valor">{{ estado.proyectos.total }}</span>
                <span class="stat-label">Total</span>
            </div>
        </div>
    </div>
    
    <!-- Métricas últimos 30 días -->
    <div class="widget widget-metricas">
        <h3>Últimos 30 días</h3>
        <div class="metric-row">
            <span class="metric-icon">💰</span>
            <span class="metric-label">Ingresos</span>
            <span class="metric-valor">${{ estado.metricas_30d.ingresos_totales }}</span>
        </div>
        <div class="metric-row">
            <span class="metric-icon">⏱️</span>
            <span class="metric-label">Horas</span>
            <span class="metric-valor">{{ estado.metricas_30d.horas_totales }}h</span>
        </div>
        <div class="metric-row metric-destacada">
            <span class="metric-icon">📈</span>
            <span class="metric-label">ROI/hora</span>
            <span class="metric-valor">${{ estado.metricas_30d.roi_por_hora }}/h</span>
        </div>
    </div>
    
    <!-- Adherencia -->
    <div class="widget widget-adherencia">
        <h3>Adherencia al Sistema</h3>
        <div class="adherencia-score adherencia-{{ estado.adherencia.status }}">
            <span class="score-numero">{{ estado.adherencia.porcentaje }}%</span>
            <span class="score-label">{{ estado.adherencia.dias_activos }}/30 días activos</span>
        </div>
        
        <div class="rituales-stats">
            <div class="ritual-stat">
                <span>📅 Rituales diarios:</span>
                <span>{{ estado.rituales.diarios_completados }}/{{ estado.rituales.diarios_esperados }}</span>
            </div>
            <div class="ritual-stat">
                <span>📊 Rituales semanales:</span>
                <span>{{ estado.rituales.semanales_completados }}/{{ estado.rituales.semanales_esperados }}</span>
            </div>
        </div>
    </div>
    
    <!-- Salud del sistema -->
    <div class="widget widget-salud">
        <div class="salud-header">
            <h3>Salud del Sistema</h3>
            <span class="salud-badge salud-{{ estado.salud.status }}">
                {{ estado.salud.status }}
            </span>
        </div>
        
        <div class="salud-componentes">
            {% for nombre, componente in estado.salud.componentes.items() %}
            <div class="componente-salud">
                <span class="componente-nombre">{{ nombre }}</span>
                <span class="componente-status status-{{ componente.status }}">
                    {{ componente.status }}
                </span>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
```

---

### CUADRANTE 2: Acciones Rápidas (Command Center)

```html
<!-- /sistema_90d/templates/components/acciones_rapidas.html -->

<div class="cuadrante cuadrante-acciones">
    <h2>⚡ Acciones Rápidas</h2>
    
    <!-- Guía contextual (lo más importante ahora) -->
    {% set siguiente = obtener_siguiente_accion() %}
    <div class="accion-destacada accion-urgencia-{{ siguiente.urgencia }}">
        <div class="accion-header">
            <h3>{{ siguiente.titulo }}</h3>
            {% if siguiente.tiempo_estimado %}
            <span class="tiempo-estimado">⏱️ {{ siguiente.tiempo_estimado }}</span>
            {% endif %}
        </div>
        <p class="accion-descripcion">{{ siguiente.descripcion }}</p>
        {% if siguiente.accion %}
        <a href="{{ siguiente.accion }}" class="btn btn-primary btn-lg">
            Hacerlo ahora →
        </a>
        {% endif %}
    </div>
    
    <!-- Acciones organizadas por categoría -->
    <div class="acciones-categorias">
        
        <!-- Registros diarios -->
        <div class="categoria-acciones">
            <h3>📝 Registros</h3>
            <div class="acciones-grid">
                <button hx-get="/metricas/nueva" 
                        hx-target="#modal" 
                        class="accion-btn">
                    <span class="accion-icono">💰</span>
                    <span class="accion-texto">Registrar Métrica</span>
                </button>
                
                <button hx-get="/proyectos/nuevo" 
                        hx-target="#modal" 
                        class="accion-btn">
                    <span class="accion-icono">➕</span>
                    <span class="accion-texto">Nuevo Proyecto</span>
                </button>
                
                <a href="/ritual-diario" class="accion-btn">
                    <span class="accion-icono">📋</span>
                    <span class="accion-texto">Ritual Diario</span>
                </a>
            </div>
        </div>
        
        <!-- Análisis -->
        <div class="categoria-acciones">
            <h3>🤖 Análisis IA</h3>
            <div class="acciones-grid">
                <button hx-post="/ia/generar-prompt/semanal" 
                        hx-target="#modal-ia" 
                        class="accion-btn accion-ia">
                    <span class="accion-icono">📊</span>
                    <span class="accion-texto">Análisis Semanal</span>
                </button>
                
                <button hx-post="/ia/generar-prompt/decision" 
                        hx-target="#modal-ia" 
                        class="accion-btn accion-ia">
                    <span class="accion-icono">🎯</span>
                    <span class="accion-texto">Decisión Kill/Scale</span>
                </button>
                
                <button hx-post="/ia/generar-prompt/riesgos" 
                        hx-target="#modal-ia" 
                        class="accion-btn accion-ia">
                    <span class="accion-icono">⚠️</span>
                    <span class="accion-texto">Detección de Riesgos</span>
                </button>
                
                <button hx-get="/ia/parsear-respuesta" 
                        hx-target="#modal" 
                        class="accion-btn accion-ia-secondary">
                    <span class="accion-icono">📥</span>
                    <span class="accion-texto">Pegar Respuesta IA</span>
                </button>
            </div>
        </div>
        
        <!-- Gestión de proyectos -->
        <div class="categoria-acciones">
            <h3>🎯 Gestión</h3>
            <div class="acciones-grid">
                <button hx-get="/proyectos/clasificar" 
                        hx-target="#modal" 
                        class="accion-btn">
                    <span class="accion-icono">🏷️</span>
                    <span class="accion-texto">Clasificar Proyectos</span>
                </button>
                
                <button hx-post="/motor-metricas/ejecutar" 
                        hx-target="#alertas-container" 
                        class="accion-btn">
                    <span class="accion-icono">🔍</span>
                    <span class="accion-texto">Analizar Métricas</span>
                </button>
                
                <a href="/ritual-semanal" class="accion-btn">
                    <span class="accion-icono">📅</span>
                    <span class="accion-texto">Ritual Semanal</span>
                </a>
            </div>
        </div>
        
        <!-- Exportación y backups -->
        <div class="categoria-acciones">
            <h3>💾 Datos</h3>
            <div class="acciones-grid">
                <button hx-post="/backup/crear" 
                        hx-target="#notificacion" 
                        class="accion-btn">
                    <span class="accion-icono">💾</span>
                    <span class="accion-texto">Crear Backup</span>
                </button>
                
                <a href="/exportar/csv" download class="accion-btn">
                    <span class="accion-icono">📄</span>
                    <span class="accion-texto">Exportar CSV</span>
                </a>
                
                <button hx-get="/config/editar" 
                        hx-target="#modal" 
                        class="accion-btn">
                    <span class="accion-icono">⚙️</span>
                    <span class="accion-texto">Configuración</span>
                </button>
                
                <button hx-post="/sistema/reparar" 
                        hx-target="#notificacion" 
                        class="accion-btn accion-warning">
                    <span class="accion-icono">🔧</span>
                    <span class="accion-texto">Auto-reparar DB</span>
                </button>
            </div>
        </div>
    </div>
</div>
```

---

### CUADRANTE 3: Proyectos Activos (Tabla Interactiva)

```html
<!-- /sistema_90d/templates/components/proyectos_activos.html -->

<div class="cuadrante cuadrante-proyectos">
    <div class="cuadrante-header">
        <h2>🎯 Proyectos Activos</h2>
        <div class="filtros-proyectos">
            <button class="filtro activo" data-filtro="active,mvp">Activos</button>
            <button class="filtro" data-filtro="winner">Winners</button>
            <button class="filtro" data-filtro="paused">Pausados</button>
            <button class="filtro" data-filtro="killed">Killed</button>
            <button class="filtro" data-filtro="all">Todos</button>
        </div>
    </div>
    
    <div class="tabla-container">
        <table class="tabla-proyectos" id="tabla-proyectos">
            <thead>
                <tr>
                    <th class="sortable" data-sort="nombre">Proyecto</th>
                    <th class="sortable" data-sort="estado">Estado</th>
                    <th class="sortable" data-sort="dias">Días</th>
                    <th class="sortable numeric" data-sort="ingresos">Ingresos</th>
                    <th class="sortable numeric" data-sort="horas">Horas</th>
                    <th class="sortable numeric" data-sort="roi">ROI/h</th>
                    <th class="sortable" data-sort="ultima">Última Métrica</th>
                    <th>Señales</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for proyecto in proyectos %}
                <tr class="proyecto-row" 
                    data-estado="{{ proyecto.estado }}"
                    data-id="{{ proyecto.id }}">
                    
                    <td class="proyecto-nombre">
                        <a href="/proyecto/{{ proyecto.id }}">{{ proyecto.nombre }}</a>
                    </td>
                    
                    <td>
                        <span class="badge badge-{{ proyecto.estado }}">
                            {{ proyecto.estado }}
                        </span>
                    </td>
                    
                    <td class="numeric">{{ proyecto.dias_desde_inicio }}</td>
                    
                    <td class="numeric moneda">
                        ${{ proyecto.ingresos_total }}
                    </td>
                    
                    <td class="numeric">{{ proyecto.horas_total }}h</td>
                    
                    <td class="numeric moneda roi-cell" 
                        data-roi="{{ proyecto.roi_por_hora }}">
                        <span class="roi-valor">${{ proyecto.roi_por_hora }}/h</span>
                        {% if proyecto.roi_por_hora > 50 %}
                        <span class="roi-indicator roi-good">▲</span>
                        {% elif proyecto.roi_por_hora < 10 %}
                        <span class="roi-indicator roi-bad">▼</span>
                        {% endif %}
                    </td>
                    
                    <td>
                        <span class="fecha-relativa" data-fecha="{{ proyecto.ultima_metrica_timestamp }}">
                            {{ proyecto.ultima_metrica_hace }}
                        </span>
                    </td>
                    
                    <td class="senales-cell">
                        {% if proyecto.senales %}
                        <div class="senales-container">
                            {% for senal in proyecto.senales %}
                            <span class="senal senal-{{ senal.severidad }}" 
                                  title="{{ senal.mensaje }}">
                                {{ senal.tipo_icono }}
                            </span>
                            {% endfor %}
                        </div>
                        {% else %}
                        <span class="sin-senales">✓</span>
                        {% endif %}
                    </td>
                    
                    <td class="acciones-cell">
                        <div class="acciones-proyecto">
                            <!-- Menú desplegable -->
                            <button class="btn-menu" onclick="toggleMenu({{ proyecto.id }})">
                                ⋮
                            </button>
                            <div class="menu-acciones" id="menu-{{ proyecto.id }}" style="display:none;">
                                <a href="/proyecto/{{ proyecto.id }}" class="menu-item">
                                    👁️ Ver detalles
                                </a>
                                <button hx-get="/metricas/nueva?proyecto_id={{ proyecto.id }}" 
                                        hx-target="#modal" 
                                        class="menu-item">
                                    ➕ Registrar métrica
                                </button>
                                <hr>
                                <button hx-post="/proyecto/{{ proyecto.id }}/decision/iterate" 
                                        hx-confirm="¿Iterar este proyecto?"
                                        class="menu-item">
                                    🔁 Marcar como Iterate
                                </button>
                                <button hx-post="/proyecto/{{ proyecto.id }}/decision/scale" 
                                        hx-confirm="¿Escalar este proyecto a Winner?"
                                        class="menu-item menu-success">
                                    🚀 Escalar a Winner
                                </button>
                                <hr>
                                <button hx-post="/proyecto/{{ proyecto.id }}/pause" 
                                        hx-confirm="¿Pausar este proyecto?"
                                        class="menu-item menu-warning">
                                    ⏸️ Pausar
                                </button>
                                <button hx-post="/proyecto/{{ proyecto.id }}/decision/kill" 
                                        hx-prompt="¿Por qué matas este proyecto?"
                                        class="menu-item menu-danger">
                                    ❌ Kill
                                </button>
                            </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        {% if not proyectos %}
        <div class="empty-state">
            <p>No hay proyectos activos</p>
            <button hx-get="/proyectos/nuevo" 
                    hx-target="#modal" 
                    class="btn btn-primary">
                Crear tu primer proyecto
            </button>
        </div>
        {% endif %}
    </div>
</div>

<script>
// Ordenamiento de tabla
function sortTable(column) {
    // Implementación de ordenamiento client-side
}

// Toggle de menú
function toggleMenu(projectId) {
    const menu = document.getElementById(`menu-${projectId}`);
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

// Filtrado de proyectos
document.querySelectorAll('.filtro').forEach(btn => {
    btn.addEventListener('click', function() {
        const filtro = this.dataset.filtro;
        const estados = filtro.split(',');
        
        document.querySelectorAll('.proyecto-row').forEach(row => {
            const estado = row.dataset.estado;
            if (filtro === 'all' || estados.includes(estado)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        // Actualizar botón activo
        document.querySelectorAll('.filtro').forEach(b => b.classList.remove('activo'));
        this.classList.add('activo');
    });
});
</script>
```

---

### CUADRANTE 4: Análisis y Alertas

```html
<!-- /sistema_90d/templates/components/analisis_alertas.html -->

<div class="cuadrante cuadrante-analisis">
    <h2>🔔 Análisis y Alertas</h2>
    
    <!-- Alertas críticas -->
    <div class="alertas-container" id="alertas-container">
        {% if alertas_criticas %}
        <div class="alertas-section">
            <h3>🚨 Alertas Críticas</h3>
            {% for alerta in alertas_criticas %}
            <div class="alerta alerta-{{ alerta.severidad }}">
                <div class="alerta-header">
                    <span class="alerta-tipo">{{ alerta.tipo_icono }} {{ alerta.tipo }}</span>
                    <button hx-post="/alertas/{{ alerta.id }}/resolver" 
                            hx-swap="outerHTML" 
                            hx-target="closest .alerta"
                            class="btn-resolver">
                        ✓
                    </button>
                </div>
                <p class="alerta-mensaje">{{ alerta.mensaje }}</p>
                {% if alerta.proyecto %}
                <a href="/proyecto/{{ alerta.proyecto_id }}" class="alerta-link">
                    Ver proyecto →
                </a>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <!-- Insights de IA (últimas decisiones sugeridas) -->
        {% if decisiones_ia_recientes %}
        <div class="insights-section">
            <h3>🤖 Insights de IA</h3>
            {% for decision in decisiones_ia_recientes %}
            <div class="insight-card">
                <div class="insight-header">
                    <span class="insight-proyecto">{{ decision.proyecto_nombre }}</span>
                    <span class="insight-decision decision-{{ decision.tipo }}">
                        {{ decision.tipo }}
                    </span>
                </div>
                <p class="insight-justificacion">{{ decision.justificacion }}</p>
                <div class="insight-acciones">
                    <button hx-post="/decisiones/{{ decision.id }}/aceptar" 
                            class="btn btn-sm btn-success">
                        ✓ Aceptar
                    </button>
                    <button hx-get="/decisiones/{{ decision.id }}/rechazar" 
                            hx-target="#modal"
                            class="btn btn-sm btn-danger">
                        ✗ Rechazar
                    </button>
                    <button class="btn btn-sm btn-secondary">
                        ⏭️ Posponer
                    </button>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <!-- Tendencias y patrones -->
        <div class="tendencias-section">
            <h3>📈 Tendencias</h3>
            
            <!-- Gráfico simple de ingresos últimos 7 días (SVG) -->
            <div class="grafico-simple">
                {{ generar_sparkline_ingresos() | safe }}
            </div>
            
            <!-- Métricas comparativas -->
            <div class="metricas-comparativas">
                <div class="metrica-comp">
                    <span class="comp-label">Esta semana vs anterior</span>
                    <span class="comp-valor comp-{{ comparacion.ingresos_direccion }}">
                        {{ comparacion.ingresos_cambio }}%
                        {{ comparacion.ingresos_icono }}
                    </span>
                </div>
                <div class="metrica-comp">
                    <span class="comp-label">Proyectos activos</span>
                    <span class="comp-valor">
                        {{ estado.proyectos.activos }}/{{ limite_proyectos }}
                    </span>
                </div>
            </div>
        </div>
        
        <!-- Próximos hitos -->
        <div class="hitos-section">
            <h3>🎯 Próximos Hitos</h3>
            <div class="hitos-lista">
                {% for hito in proximos_hitos %}
                <div class="hito-item">
                    <span class="hito-fecha">{{ hito.fecha }}</span>
                    <span class="hito-descripcion">{{ hito.descripcion }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
```

---

## FUNCIONALIDADES AVANZADAS DEL DASHBOARD

### 1. Modal Universal para Formularios

```html
<!-- /sistema_90d/templates/components/modal.html -->

<div id="modal" class="modal" style="display:none;">
    <div class="modal-overlay" onclick="cerrarModal()"></div>
    <div class="modal-content">
        <button class="modal-cerrar" onclick="cerrarModal()">✕</button>
        <div id="modal-body">
            <!-- Contenido dinámico vía htmx -->
        </div>
    </div>
</div>

<script>
function cerrarModal() {
    document.getElementById('modal').style.display = 'none';
}

// Auto-abrir cuando htmx carga contenido
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'modal-body') {
        document.getElementById('modal').style.display = 'flex';
    }
});
</script>
```

### 2. Modal IA con Copy/Paste Integrado

```html
<!-- /sistema_90d/templates/components/modal_ia.html -->

<div id="modal-ia" class="modal modal-ia" style="display:none;">
    <div class="modal-overlay" onclick="cerrarModalIA()"></div>
    <div class="modal-content modal-ia-content">
        <div class="modal-header">
            <h2>🤖 Análisis con IA</h2>
            <button class="modal-cerrar" onclick="cerrarModalIA()">✕</button>
        </div>
        
        <div class="modal-body">
            <!-- Paso 1: Prompt generado -->
            <div class="ia-paso ia-paso-1">
                <h3>Paso 1: Copiar Prompt</h3>
                <textarea id="prompt-generado" readonly rows="20">
                    {{ prompt_generado }}
                </textarea>
                <div class="ia-acciones">
                    <button onclick="copiarPrompt()" class="btn btn-primary">
                        📋 Copiar al Portapapeles
                    </button>
                    <a href="data:text/plain;charset=utf-8,{{ prompt_encoded }}" 
                       download="prompt_{{ tipo }}.txt" 
                       class="btn btn-secondary">
                        💾 Descargar TXT
                    </a>
                </div>
                <p class="ia-instruccion">
                    Copia este prompt y pégalo en:
                    <a href="https://claude.ai" target="_blank">Claude</a>,
                    <a href="https://chat.openai.com" target="_blank">ChatGPT</a>, o
                    <a href="https://gemini.google.com" target="_blank">Gemini</a>
                </p>
            </div>
            
            <!-- Paso 2: Pegar respuesta -->
            <div class="ia-paso ia-paso-2">
                <h3>Paso 2: Pegar Respuesta de IA</h3>
                <textarea id="respuesta-ia" 
                          placeholder="Pega aquí el JSON que te retornó la IA..."
                          rows="15"></textarea>
                <button hx-post="/ia/parsear-respuesta" 
                        hx-include="#respuesta-ia"
                        hx-target="#resultado-parse"
                        class="btn btn-primary">
                    Procesar Respuesta
                </button>
                <div id="resultado-parse"></div>
            </div>
        </div>
    </div>
</div>

<script>
function copiarPrompt() {
    const textarea = document.getElementById('prompt-generado');
    textarea.select();
    document.execCommand('copy');
    
    // Feedback visual
    const btn = event.target;
    const textoOriginal = btn.textContent;
    btn.textContent = '✓ Copiado!';
    setTimeout(() => btn.textContent = textoOriginal, 2000);
}

function cerrarModalIA() {
    document.getElementById('modal-ia').style.display = 'none';
}
</script>
```

### 3. Notificaciones Toast

```html
<!-- /sistema_90d/templates/components/notificaciones.html -->

<div id="notificaciones-container"></div>

<script>
function mostrarNotificacion(mensaje, tipo = 'info') {
    const container = document.getElementById('notificaciones-container');
    
    const notif = document.createElement('div');
    notif.className = `notificacion notificacion-${tipo}`;
    notif.textContent = mensaje;
    
    container.appendChild(notif);
    
    // Auto-remover después de 3 segundos
    setTimeout(() => {
        notif.classList.add('fade-out');
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}

// Escuchar eventos de htmx para mostrar notificaciones
document.body.addEventListener('htmx:afterRequest', function(evt) {
    const response = JSON.parse(evt.detail.xhr.response);
    if (response.mensaje) {
        mostrarNotificacion(response.mensaje, response.status);
    }
});
</script>
```

---

## CSS COMPLETO DEL DASHBOARD

```css
/* /sistema_90d/static/dashboard.css */

/* Layout del dashboard */
.dashboard-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr 1fr;
    gap: 20px;
    height: 100vh;
    padding: 20px;
    background: #f5f5f5;
}

/* Header ocupa todo el ancho */
.dashboard-header {
    grid-column: 1 / -1;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Cuadrantes */
.cuadrante {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    overflow-y: auto;
}

/* Widgets del cuadrante 1 */
.widget {
    margin-bottom: 20px;
    padding: 15px;
    background: #f9f9f9;
    border-radius: 6px;
}

.widget h3 {
    margin-bottom: 10px;
    font-size: 14px;
    color: #666;
    text-transform: uppercase;
}

/* Barra de progreso del ciclo */
.progress-bar {
    width: 100%;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin: 10px 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.3s ease;
}

/* Stats grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.stat {
    text-align: center;
    padding: 10px;
    background: white;
    border-radius: 4px;
}

.stat-valor {
    display: block;
    font-size: 24px;
    font-weight: bold;
    color: #333;
}

.stat-label {
    display: block;
    font-size: 12px;
    color: #666;
    margin-top: 5px;
}

.stat-winner .stat-valor { color: #4CAF50; }
.stat-killed .stat-valor { color: #f44336; }

/* Acciones rápidas */
.acciones-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-top: 10px;
}

.accion-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 15px;
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.accion-btn:hover {
    border-color: #2196F3;
    background: #f0f8ff;
    transform: translateY(-2px);
}

.accion-icono {
    font-size: 24px;
}

.accion-texto {
    font-size: 13px;
    font-weight: 500;
    text-align: center;
}

/* Tabla de proyectos */
.tabla-proyectos {
    width: 100%;
    border-collapse: collapse;
}

.tabla-proyectos th {
    background: #f5f5f5;
    padding: 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
}

.tabla-proyectos td {
    padding: 12px;
    border-bottom: 1px solid #f0f0f0;
}

.tabla-proyectos tr:hover {
    background: #f9f9f9;
}

/* Señales en tabla */
.senales-container {
    display: flex;
    gap: 5px;
}

.senal {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}

.senal-critical { background: #ffebee; color: #c62828; }
.senal-warning { background: #fff3e0; color: #ef6c00; }
.senal-info { background: #e3f2fd; color: #1976d2; }

/* Modal */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
}

.modal-content {
    position: relative;
    background: white;
    padding: 30px;
    border-radius: 8px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    z-index: 1001;
}

/* Notificaciones toast */
.notificacion {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideIn 0.3s ease;
    z-index: 2000;
}

.notificacion-success {
    border-left: 4px solid #4CAF50;
}

.notificacion-error {
    border-left: 4px solid #f44336;
}

.notificacion-warning {
    border-left: 4px solid #ff9800;
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.fade-out {
    animation: fadeOut 0.3s ease forwards;
}

@keyframes fadeOut {
    to {
        opacity: 0;
        transform: translateX(400px);
    }
}

/* Responsive */
@media (max-width: 1024px) {
    .dashboard-container {
        grid-template-columns: 1fr;
    }
    
    .acciones-grid {
        grid-template-columns: 1fr;
    }
}
```

---

## BACKEND: RUTAS ADICIONALES

```python
# /sistema_90d/app.py (rutas adicionales)

@app.route('/dashboard')
def dashboard():
    """Dashboard unificado con todos los cuadrantes."""
    from dashboard_data import obtener_estado_sistema
    from guia_contextual import obtener_siguiente_accion
    from motor_metricas import MotorMetricas
    
    # Recopilar datos de todos los cuadrantes
    estado = obtener_estado_sistema()
    siguiente_accion = obtener_siguiente_accion()
    
    # Proyectos con señales
    db = get_db()
    cursor = db.execute("""
        SELECT * FROM v_resumen_proyectos
        WHERE estado IN ('active', 'mvp', 'winner')
        ORDER BY 
            CASE estado
                WHEN 'winner' THEN 1
                WHEN 'active' THEN 2
                WHEN 'mvp' THEN 3
            END,
            ingresos_total DESC
    """)
    proyectos = cursor.fetchall()
    
    # Agregar señales a cada proyecto
    motor = MotorMetricas('data/sistema.db')
    for proyecto in proyectos:
        señales = motor.analizar_proyecto(proyecto['id'])
        proyecto['senales'] = señales
    
    # Alertas críticas
    cursor = db.execute("""
        SELECT * FROM alertas
        WHERE resuelta = 0 AND severidad = 'critical'
        ORDER BY fecha DESC
        LIMIT 5
    """)
    alertas_criticas = cursor.fetchall()
    
    # Decisiones IA recientes
    cursor = db.execute("""
        SELECT d.*, p.nombre as proyecto_nombre
        FROM decisiones d
        JOIN proyectos p ON p.id = d.proyecto_id
        WHERE d.origen = 'ia'
          AND d.accion_tomada IS NULL
        ORDER BY d.fecha DESC
        LIMIT 3
    """)
    decisiones_ia = cursor.fetchall()
    
    # Próximos hitos
    proximos_hitos = calcular_proximos_hitos(estado['ciclo']['dia_actual'])
    
    return render_template('dashboard.html',
        estado=estado,
        siguiente_accion=siguiente_accion,
        proyectos=proyectos,
        alertas_criticas=alertas_criticas,
        decisiones_ia=decisiones_ia,
        proximos_hitos=proximos_hitos
    )

@app.route('/ia/generar-prompt/<tipo>', methods=['POST'])
def generar_prompt_ia(tipo):
    """Genera prompt para análisis de IA."""
    from generador_prompts import GeneradorPrompts
    
    generador = GeneradorPrompts('data/sistema.db')
    
    if tipo == 'semanal':
        prompt = generador.generar_analisis_semanal()
    elif tipo == 'decision':
        prompt = generador.generar_decision_kill_scale()
    elif tipo == 'riesgos':
        prompt = generador.generar_deteccion_riesgos()
    else:
        return {'error': 'Tipo de prompt inválido'}, 400
    
    # Encodear para data URL
    import urllib.parse
    prompt_encoded = urllib.parse.quote(prompt)
    
    return render_template('components/modal_ia_content.html',
        prompt_generado=prompt,
        prompt_encoded=prompt_encoded,
        tipo=tipo
    )

@app.route('/motor-metricas/ejecutar', methods=['POST'])
def ejecutar_motor_metricas():
    """Ejecuta análisis de todas las métricas manualmente."""
    from motor_metricas import MotorMetricas
    
    motor = MotorMetricas('data/sistema.db')
    analisis = motor.analizar_todos_los_proyectos()
    
    # Convertir señales en alertas HTML
    alertas_html = render_template('components/alertas_resultado.html',
        analisis=analisis
    )
    
    return alertas_html

@app.route('/backup/crear', methods=['POST'])
def crear_backup():
    """Crea backup manual de la DB."""
    from backup import SistemaBackup
    
    backup = SistemaBackup('data/sistema.db')
    ruta = backup.crear_backup(comprimir=True)
    
    return {
        'status': 'success',
        'mensaje': f'Backup creado: {ruta.name}',
        'ruta': str(ruta)
    }

@app.route('/sistema/reparar', methods=['POST'])
def reparar_sistema():
    """Ejecuta auto-reparación manual."""
    from auto_repair import reparar_estados_inconsistentes
    
    with transaccion_segura() as db:
        reparaciones = reparar_estados_inconsistentes(db)
    
    if reparaciones:
        return {
            'status': 'success',
            'mensaje': f'{len(reparaciones)} inconsistencias reparadas',
            'detalles': reparaciones
        }
    else:
        return {
            'status': 'info',
            'mensaje': 'No se encontraron inconsistencias'
        }
```

---

## TEMPLATE COMPLETO DEL DASHBOARD

```html
<!-- /sistema_90d/templates/dashboard.html -->

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema 90D - Dashboard</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/dashboard.css">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body>
    <div class="dashboard-container">
        
        <!-- Header -->
        <div class="dashboard-header">
            <div class="header-content">
                <h1>Sistema 90D - Centro de Comando</h1>
                <div class="header-stats">
                    <span>Día {{ estado.ciclo.dia_actual }}/90</span>
                    <span class="separator">•</span>
                    <span>{{ estado.fase.icono }} {{ estado.fase.nombre }}</span>
                    <span class="separator">•</span>
                    <span>{{ estado.proyectos.activos }} proyectos activos</span>
                </div>
            </div>
        </div>
        
        <!-- Cuadrante 1: Estado del Sistema -->
        {% include 'components/estado_sistema.html' %}
        
        <!-- Cuadrante 2: Acciones Rápidas -->
        {% include 'components/acciones_rapidas.html' %}
        
        <!-- Cuadrante 3: Proyectos Activos -->
        {% include 'components/proyectos_activos.html' %}
        
        <!-- Cuadrante 4: Análisis y Alertas -->
        {% include 'components/analisis_alertas.html' %}
        
    </div>
    
    <!-- Modales -->
    {% include 'components/modal.html' %}
    {% include 'components/modal_ia.html' %}
    
    <!-- Notificaciones -->
    <div id="notificaciones-container"></div>
    
    <script src="/static/dashboard.js"></script>
</body>
</html>
```

---

## RESUMEN DE MEJORAS DEL DASHBOARD

| Característica | Antes | Después |
|----------------|-------|---------|
| **Información visible** | Solo proyectos | 4 cuadrantes completos |
| **Acciones ejecutables** | 2-3 botones | 20+ acciones categorizadas |
| **Guía contextual** | Ninguna | Siguiente acción sugerida |
| **Análisis IA** | Página separada | Integrado con modal |
| **Alertas** | Banner simple | Panel dedicado con priorización |
| **Interactividad** | Tabla estática | Filtros, ordenamiento, menús |
| **Monitoreo** | Ninguno | Salud sistema + adherencia |

**Código adicional:** ~1200 líneas (HTML + CSS + JS + Python)

---

## PREGUNTA PARA TI

¿Implemento este dashboard completo con código funcional ahora?

Incluiría:
- ✅ 4 cuadrantes con HTML completo
- ✅ CSS responsive del dashboard
- ✅ JavaScript para interactividad
- ✅ Rutas backend Python
- ✅ Modales universales
- ✅ Sistema de notificaciones

O prefieres que simplifique algún cuadrante primero?
