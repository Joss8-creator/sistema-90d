# SUB-PROMPT 03: INTERFAZ DE USUARIO (UI MINIMALISTA)

## CONTEXTO
Sistema 90D local. Backend Python. Frontend HTML + htmx (14KB).
**Principio rector:** Cada interacción debe ser <3 clics.

## OBJETIVO
Diseñar interfaz que:
1. Minimice fricción de entrada de datos
2. Muestre información crítica sin scroll
3. Evite JavaScript complejo (usar htmx para interactividad)

---

## ARQUITECTURA DE PLANTILLAS

```
/sistema_90d/templates/
  base.html           # Layout común (header, nav, footer)
  dashboard.html      # Vista principal (resumen de proyectos)
  proyecto.html       # Vista detallada de un proyecto
  metricas.html       # Formulario de registro de métricas
  config.html         # Edición de parámetros del sistema
  exportar_ia.html    # Generador de prompts
```

---

## DISEÑO DE CADA PANTALLA

### 1. `dashboard.html` — Vista Principal
**Objetivo:** Responder en <3 segundos:
- ¿En qué día estoy del ciclo 90D?
- ¿Qué proyectos están activos?
- ¿Cuál es el más prometedor?

**Layout:**
```html
<!-- /sistema_90d/templates/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Sistema 90D</title>
  <link rel="stylesheet" href="/static/style.css">
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body>
  <!-- Banner de fase actual -->
  <header class="phase-banner phase-{{fase_actual}}">
    <h1>Día {{dia_actual}}/90 — Fase: {{fase_nombre}}</h1>
    <p>{{fase_descripcion}}</p>
  </header>

  <!-- Alertas críticas -->
  {{#alertas}}
  <div class="alert alert-{{tipo}}">
    <strong>⚠️ {{mensaje}}</strong>
    <button hx-post="/alertas/{{id}}/resolver" hx-swap="outerHTML">Marcar resuelta</button>
  </div>
  {{/alertas}}

  <!-- Resumen de proyectos -->
  <section class="proyectos-grid">
    <h2>Proyectos Activos ({{proyectos_activos_count}}/{{proyectos_max}})</h2>
    
    <table>
      <thead>
        <tr>
          <th>Proyecto</th>
          <th>Estado</th>
          <th>Ingresos</th>
          <th>Horas</th>
          <th>ROI/h</th>
          <th>Última métrica</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {{#proyectos}}
        <tr class="proyecto-row proyecto-{{estado}}">
          <td><a href="/proyecto/{{id}}">{{nombre}}</a></td>
          <td><span class="badge badge-{{estado}}">{{estado}}</span></td>
          <td>${{ingresos_total}}</td>
          <td>{{horas_total}}h</td>
          <td>${{roi_por_hora}}/h</td>
          <td>{{ultima_metrica_fecha_humanizada}}</td>
          <td>
            <button hx-post="/proyecto/{{id}}/kill" 
                    hx-confirm="¿Seguro? Esto marcará el proyecto como muerto."
                    class="btn-danger">Kill</button>
          </td>
        </tr>
        {{/proyectos}}
      </tbody>
    </table>

    <!-- Botón de nuevo proyecto (solo si no está en límite) -->
    {{#puede_crear_proyecto}}
    <a href="/proyecto/nuevo" class="btn-primary">+ Nuevo Proyecto</a>
    {{/puede_crear_proyecto}}
    {{^puede_crear_proyecto}}
    <p class="warning">⚠️ Límite de {{proyectos_max}} proyectos activos alcanzado. Mata o pausa uno antes de crear otro.</p>
    {{/puede_crear_proyecto}}
  </section>

  <!-- Botón de análisis IA -->
  <footer>
    <a href="/exportar-ia" class="btn-secondary">📋 Generar Análisis IA</a>
  </footer>
</body>
</html>
```

**Decisiones de diseño:**
- **htmx para kill button:** Evita full page reload. Respuesta: HTML partial que reemplaza la fila.
- **Tabla vs cards:** Tabla = más densidad de información. Cards = más scroll.
- **Color-coding de estados:** `badge-active` (verde), `badge-paused` (amarillo), `badge-killed` (rojo).

**Complejidad de renderizado:** O(n) donde n = proyectos activos (asumido <10).

---

### 2. `proyecto.html` — Vista Detallada
**Objetivo:** Ver histórico de métricas y tomar decisión.

```html
<!-- /sistema_90d/templates/proyecto.html -->
<header>
  <h1>{{proyecto.nombre}}</h1>
  <p><strong>Hipótesis:</strong> {{proyecto.hipotesis}}</p>
  <p><strong>Estado:</strong> <span class="badge badge-{{proyecto.estado}}">{{proyecto.estado}}</span></p>
</header>

<!-- Métricas en tabla (sin gráfico en MVP) -->
<section>
  <h2>Histórico de Métricas</h2>
  <table>
    <thead>
      <tr>
        <th>Fecha</th>
        <th>Ingresos</th>
        <th>Horas</th>
        <th>Conversiones</th>
        <th>Fuente Tráfico</th>
      </tr>
    </thead>
    <tbody>
      {{#metricas}}
      <tr>
        <td>{{fecha_humanizada}}</td>
        <td>${{ingresos}}</td>
        <td>{{tiempo_invertido}}h</td>
        <td>{{conversiones}}</td>
        <td>{{trafico_fuente}}</td>
      </tr>
      {{/metricas}}
    </tbody>
  </table>
  
  <a href="/metricas/nueva?proyecto_id={{proyecto.id}}" class="btn-primary">+ Registrar Métrica</a>
</section>

<!-- Decisiones pasadas -->
<section>
  <h2>Decisiones Tomadas</h2>
  {{#decisiones}}
  <div class="decision-card decision-{{tipo}}">
    <strong>{{tipo_humanizado}}</strong> — {{fecha_humanizada}}
    <p>{{justificacion}}</p>
    <small>Origen: {{origen}}</small>
  </div>
  {{/decisiones}}
</section>

<!-- Acciones rápidas -->
<footer>
  <button hx-post="/proyecto/{{proyecto.id}}/decision/kill" 
          hx-prompt="¿Por qué matas este proyecto? (obligatorio)"
          class="btn-danger">Kill</button>
  <button hx-post="/proyecto/{{proyecto.id}}/decision/iterate" 
          hx-prompt="¿Qué cambiarás en la iteración?"
          class="btn-warning">Iterate</button>
  <button hx-post="/proyecto/{{proyecto.id}}/decision/scale" 
          hx-prompt="¿Qué métricas justifican el scale?"
          class="btn-success">Scale → Winner</button>
</footer>
```

**Por qué `hx-prompt`:**
Obliga a documentar razón de la decisión. Se inserta directamente en tabla `decisiones`.

---

### 3. `metricas.html` — Formulario de Registro
**Objetivo:** Registrar métrica en <60 segundos.

```html
<!-- /sistema_90d/templates/metricas.html -->
<form hx-post="/metricas/guardar" hx-target="#resultado" hx-swap="innerHTML">
  <label for="proyecto_id">Proyecto:</label>
  <select name="proyecto_id" required>
    {{#proyectos_activos}}
    <option value="{{id}}">{{nombre}}</option>
    {{/proyectos_activos}}
  </select>

  <label for="fecha">Fecha:</label>
  <input type="date" name="fecha" value="{{hoy}}" required>

  <label for="ingresos">Ingresos ($):</label>
  <input type="number" step="0.01" name="ingresos" value="0">

  <label for="tiempo_invertido">Tiempo (horas):</label>
  <input type="number" step="0.5" name="tiempo_invertido" value="0">

  <label for="conversiones">Conversiones:</label>
  <input type="number" name="conversiones" value="0">

  <label for="trafico_fuente">Fuente Tráfico:</label>
  <select name="trafico_fuente">
    <option value="organic">Orgánico</option>
    <option value="paid">Pagado</option>
    <option value="referral">Referral</option>
    <option value="direct">Directo</option>
  </select>

  <label for="friccion_principal">Fricción Principal (opcional):</label>
  <textarea name="friccion_principal" rows="3" placeholder="Ej: usuarios no entienden el onboarding"></textarea>

  <button type="submit" class="btn-primary">Guardar Métrica</button>
</form>

<div id="resultado"></div>
```

**Por qué htmx aquí:**
Al guardar, el servidor retorna `<p class="success">✅ Métrica guardada</p>` que reemplaza `#resultado`. Sin reload.

---

### 4. `exportar_ia.html` — Generador de Prompts
**Objetivo:** Exportar contexto listo para copiar/pegar en cualquier IA.

```html
<!-- /sistema_90d/templates/exportar_ia.html -->
<header>
  <h1>Exportar Análisis para IA</h1>
  <p>Copia este texto y pégalo en ChatGPT, Claude, o tu IA preferida.</p>
</header>

<section>
  <label for="tipo_analisis">Tipo de Análisis:</label>
  <select id="tipo_analisis" hx-get="/exportar-ia/generar" hx-target="#prompt-output" hx-include="this">
    <option value="semanal">Análisis Semanal</option>
    <option value="decision">Decisión Kill/Iterate/Scale</option>
    <option value="riesgos">Detección de Riesgos</option>
  </select>

  <textarea id="prompt-output" rows="20" readonly>{{prompt_generado}}</textarea>
  
  <button onclick="navigator.clipboard.writeText(document.getElementById('prompt-output').value)" 
          class="btn-primary">📋 Copiar al Portapapeles</button>
  
  <a href="data:text/plain;charset=utf-8,{{prompt_generado_encoded}}" 
     download="analisis_90d_{{fecha_actual}}.txt" 
     class="btn-secondary">💾 Descargar TXT</a>
</section>
```

**Abstracción de IA:**
El sistema NO ejecuta la IA. Solo genera el texto. Usuario decide dónde pegarlo.

---

## ESTILO CSS MINIMALISTA

```css
/* /sistema_90d/static/style.css */

/* Reset básico */
* { margin: 0; padding: 0; box-sizing: border-box; }
body { 
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.6;
  color: #333;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* Banner de fase */
.phase-banner {
  padding: 20px;
  margin-bottom: 20px;
  border-left: 5px solid;
}
.phase-exploracion { border-color: #3498db; background: #ecf0f1; }
.phase-experimentacion { border-color: #f39c12; background: #fef5e7; }
.phase-decision { border-color: #e74c3c; background: #fadbd8; }
.phase-consolidacion { border-color: #27ae60; background: #d5f4e6; }

/* Alertas */
.alert { 
  padding: 15px; 
  margin-bottom: 15px; 
  border-radius: 4px; 
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.alert-warning { background: #fff3cd; border-left: 4px solid #ffc107; }
.alert-danger { background: #f8d7da; border-left: 4px solid #dc3545; }

/* Tabla de proyectos */
table { 
  width: 100%; 
  border-collapse: collapse; 
  margin: 20px 0; 
}
th, td { 
  padding: 12px; 
  text-align: left; 
  border-bottom: 1px solid #ddd; 
}
th { 
  background: #f8f9fa; 
  font-weight: 600; 
}

/* Badges de estado */
.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}
.badge-active { background: #d4edda; color: #155724; }
.badge-paused { background: #fff3cd; color: #856404; }
.badge-killed { background: #f8d7da; color: #721c24; }
.badge-winner { background: #d1ecf1; color: #0c5460; }

/* Botones */
button, .btn-primary, .btn-secondary, .btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  margin: 5px;
}
.btn-primary { background: #007bff; color: white; }
.btn-primary:hover { background: #0056b3; }
.btn-secondary { background: #6c757d; color: white; }
.btn-danger { background: #dc3545; color: white; }

/* Formularios */
form { max-width: 600px; }
label { 
  display: block; 
  margin-top: 15px; 
  font-weight: 500; 
}
input, select, textarea { 
  width: 100%; 
  padding: 8px; 
  margin-top: 5px; 
  border: 1px solid #ced4da; 
  border-radius: 4px; 
}

/* Optimización para móvil */
@media (max-width: 768px) {
  table { font-size: 12px; }
  th, td { padding: 8px; }
}
```

**Tamaño total:** <3KB sin comprimir. Sin dependencias externas salvo htmx (14KB).

---

## COMPARATIVA VS SOLUCIÓN "MODERNA"

### Stack moderno (React + Tailwind + Recharts)
- **Bundle size:** ~500KB min (200KB gzipped)
- **Build time:** 10-30 segundos
- **Dependencias:** 200+ paquetes npm
- **Complejidad:** State management, hooks, virtual DOM

### Stack elegido (HTML + htmx + CSS vanilla)
- **Bundle size:** <20KB total
- **Build time:** 0 segundos (es HTML estático)
- **Dependencias:** 1 (htmx)
- **Complejidad:** Request/response HTTP estándar

**Trade-off:**
- Perdemos: Animaciones sofisticadas, SPA fluido
- Ganamos: Velocidad de carga, debuggabilidad, longevidad (HTML siempre funciona)

---

## OPTIMIZACIONES CONSIDERADAS PERO NO APLICADAS

### 1. Gráficos con Chart.js
**Razón:** 200KB para mostrar tendencias que una tabla revela igual. En fase 2, usar SVG server-side con Python.

### 2. Alpine.js para interactividad ligera
**Razón:** htmx cubre 90% de casos. Agregar Alpine = más complejidad.

### 3. CSS framework (Bootstrap, Bulma)
**Razón:** 150KB+ para estilos que no usaremos. CSS custom = <3KB.

---

## ENTREGABLE ESPERADO

1. **Archivos HTML** completos (base.html, dashboard.html, proyecto.html)
2. **Archivo CSS** completo (style.css)
3. **Ejemplos de htmx** en formularios y botones

**Formato:** Código funcional con rutas como comentarios.

**Siguiente paso:** Si UI aprobada, ejecutar `04_MOTOR_METRICAS.md`
