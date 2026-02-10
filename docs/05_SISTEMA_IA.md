# SUB-PROMPT 05: SISTEMA DE ABSTRACCIÓN DE IA

## CONTEXTO
Sistema 90D local sin integración API directa con LLMs.
**Principio:** Usuario controla qué IA usa, cuándo y cómo. El sistema solo genera prompts optimizados.

## OBJETIVO
Diseñar sistema que:
1. Genere prompts estructurados listos para copiar/pegar
2. Parse respuestas estructuradas de IAs (JSON/YAML)
3. Permita versionar y editar prompts sin tocar código

---

## ARQUITECTURA DEL SISTEMA

```
/sistema_90d
  /prompts
    /templates            # Plantillas Jinja2 de prompts
      analisis_semanal.txt
      decision_kill_iterate_scale.txt
      deteccion_riesgos.txt
      plan_proxima_semana.txt
    /generated           # Prompts generados (histórico)
      2025-02-02_analisis_semanal.txt
      ...
  /respuestas_ia         # Respuestas parseadas de IAs
    2025-02-02_analisis_semanal.json
    ...
  /generador_prompts.py  # Motor de generación
  /parser_respuestas.py  # Parser de respuestas estructuradas
```

---

## GENERADOR DE PROMPTS

### Plantilla base: Análisis Semanal
```jinja2
{# /sistema_90d/prompts/templates/analisis_semanal.txt #}

📘 DOCUMENTO BASE (INMUTABLE)
=============================
Lee y aplica estrictamente el contenido de este documento:

{{ documento_base_contenido }}

---

📊 CONTEXTO DEL CICLO 90D
=========================
- Día actual: {{ dia_actual }}/90
- Fase: {{ fase_actual }} ({{ fase_descripcion }})
- Fecha de análisis: {{ fecha_analisis }}

---

📈 PROYECTOS ACTIVOS
====================
{% for proyecto in proyectos_activos %}
{{ loop.index }}. **{{ proyecto.nombre }}**
   - Hipótesis: {{ proyecto.hipotesis }}
   - Estado: {{ proyecto.estado }}
   - Días desde inicio: {{ proyecto.dias_desde_inicio }}
   - Métricas totales:
     * Ingresos: ${{ proyecto.ingresos_total }}
     * Tiempo invertido: {{ proyecto.horas_total }}h
     * ROI/hora: ${{ proyecto.roi_por_hora }}/h
   - Última métrica: {{ proyecto.ultima_metrica_fecha }} (hace {{ proyecto.dias_desde_ultima_metrica }} días)
   {% if proyecto.señales_detectadas %}
   - ⚠️ Señales detectadas:
     {% for señal in proyecto.señales_detectadas %}
     * [{{ señal.severidad|upper }}] {{ señal.mensaje }}
     {% endfor %}
   {% endif %}

{% endfor %}

{% if proyectos_pausados %}
---

⏸️ PROYECTOS PAUSADOS
======================
{% for proyecto in proyectos_pausados %}
- {{ proyecto.nombre }}: Pausado hace {{ proyecto.dias_pausado }} días
{% endfor %}
{% endif %}

---

🎯 INSTRUCCIONES PARA LA IA
============================
Actúa como analista frío del sistema 90D. Tu tarea:

1. **Clasificar cada proyecto activo** en una de estas categorías:
   - ❌ KILL: Recomendar cancelación inmediata
   - 🔁 ITERATE: Requiere ajustes antes de decidir
   - 🚀 SCALE: Candidato a Winner
   - ⏸️ PAUSE: Congelar temporalmente

2. **Justificar con datos**, no con intuición. Referencia las métricas específicas.

3. **Detectar riesgos** no evidentes:
   - Concentración de ingresos
   - Dependencia de un solo canal
   - Deuda técnica acumulándose
   - Sesgo optimista del fundador

4. **Proponer siguiente acción concreta** para cada proyecto (máximo 1 acción por proyecto).

---

📋 FORMATO DE RESPUESTA OBLIGATORIO
====================================
Retorna tu análisis en este formato JSON:

```json
{
  "resumen_ejecutivo": "Breve resumen del estado general (máx 3 oraciones)",
  "proyectos": [
    {
      "id": <ID del proyecto>,
      "nombre": "<Nombre del proyecto>",
      "decision": "kill | iterate | scale | pause",
      "justificacion": "<Razones basadas en métricas>",
      "siguiente_accion": "<Acción específica y medible>",
      "metricas_clave": {
        "roi_hora": <número>,
        "dias_sin_ingresos": <número>,
        "tendencia": "creciendo | estable | decreciendo"
      }
    }
  ],
  "riesgos_detectados": [
    {
      "tipo": "concentracion | dependencia_canal | deuda_tecnica | otro",
      "descripcion": "<Descripción del riesgo>",
      "severidad": "baja | media | alta",
      "mitigacion_sugerida": "<Acción para mitigar>"
    }
  ],
  "recomendacion_proxima_semana": "<Foco principal para los próximos 7 días>"
}
```

---

⚠️ REGLAS ANTI-ALUCINACIÓN
===========================
- NO inventes métricas que no están en los datos
- NO asumas validación sin evidencia
- NO uses lenguaje motivacional; sé directo y técnico
- SI falta información crítica, solicítala explícitamente

---
FIN DEL PROMPT
```

**Decisiones de diseño:**
1. **Jinja2 para templating**: Estándar Python, cero dependencias extra
2. **JSON obligatorio en respuesta**: Parseable sin LLM adicional
3. **Documento Base embebido**: IA recibe contexto completo en cada análisis

---

### Código del generador
```python
# /sistema_90d/generador_prompts.py

from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from pathlib import Path
import sqlite3

class GeneradorPrompts:
    """
    Genera prompts intercambiables para análisis con IAs.
    """
    
    def __init__(self, db_path: str, templates_dir: str = 'prompts/templates'):
        self.db = sqlite3.connect(db_path)
        self.env = Environment(loader=FileSystemLoader(templates_dir))
    
    def _cargar_documento_base(self) -> str:
        """Lee el archivo Documento_Base.txt completo."""
        with open('Documento_Base.txt', 'r', encoding='utf-8') as f:
            return f.read()
    
    def _obtener_contexto_ciclo(self) -> dict:
        """Calcula día actual y fase del ciclo 90D."""
        cursor = self.db.execute("""
            SELECT valor FROM config_sistema 
            WHERE clave = 'fecha_inicio_ciclo'
        """)
        fecha_inicio = datetime.fromisoformat(cursor.fetchone()[0])
        
        hoy = datetime.now()
        dia_actual = (hoy - fecha_inicio).days + 1
        
        # Determinar fase
        if dia_actual <= 14:
            fase = 'exploracion'
            descripcion = 'Exploración y setup inicial'
        elif dia_actual <= 45:
            fase = 'experimentacion'
            descripcion = 'Experimentación rápida con MVPs'
        elif dia_actual <= 75:
            fase = 'decision'
            descripcion = 'Identificación de winners'
        else:
            fase = 'consolidacion'
            descripcion = 'Consolidación y preparación de escalado'
        
        return {
            'dia_actual': dia_actual,
            'fase_actual': fase,
            'fase_descripcion': descripcion,
            'fecha_analisis': hoy.isoformat()
        }
    
    def _obtener_proyectos_activos(self) -> list[dict]:
        """Obtiene datos de proyectos activos con métricas agregadas."""
        cursor = self.db.execute("""
            SELECT 
                p.id,
                p.nombre,
                p.hipotesis,
                p.estado,
                (unixepoch('now') - p.fecha_inicio) / 86400 AS dias_desde_inicio,
                COALESCE(SUM(m.ingresos), 0) AS ingresos_total,
                COALESCE(SUM(m.tiempo_invertido), 0) AS horas_total,
                CASE 
                    WHEN SUM(m.tiempo_invertido) > 0 
                    THEN ROUND(SUM(m.ingresos) / SUM(m.tiempo_invertido), 2)
                    ELSE 0 
                END AS roi_por_hora,
                MAX(m.fecha) AS ultima_metrica_timestamp
            FROM proyectos p
            LEFT JOIN metricas m ON m.proyecto_id = p.id
            WHERE p.estado IN ('active', 'mvp')
            GROUP BY p.id
        """)
        
        proyectos = []
        for row in cursor.fetchall():
            proyecto = {
                'id': row[0],
                'nombre': row[1],
                'hipotesis': row[2],
                'estado': row[3],
                'dias_desde_inicio': int(row[4]),
                'ingresos_total': float(row[5]),
                'horas_total': float(row[6]),
                'roi_por_hora': float(row[7]),
                'ultima_metrica_fecha': datetime.fromtimestamp(row[8]).strftime('%Y-%m-%d') if row[8] else 'Nunca',
                'dias_desde_ultima_metrica': (datetime.now() - datetime.fromtimestamp(row[8])).days if row[8] else 999
            }
            
            # Agregar señales detectadas por motor de métricas
            from motor_metricas import MotorMetricas
            motor = MotorMetricas(self.db)
            señales = motor.analizar_proyecto(proyecto['id'])
            
            proyecto['señales_detectadas'] = [
                {
                    'tipo': s.tipo,
                    'severidad': s.severidad,
                    'mensaje': s.mensaje
                }
                for s in señales
            ]
            
            proyectos.append(proyecto)
        
        return proyectos
    
    def generar_analisis_semanal(self) -> str:
        """
        Genera prompt de análisis semanal completo.
        
        Returns:
            str: Contenido del prompt listo para copiar/pegar
        """
        template = self.env.get_template('analisis_semanal.txt')
        
        contexto = {
            'documento_base_contenido': self._cargar_documento_base(),
            **self._obtener_contexto_ciclo(),
            'proyectos_activos': self._obtener_proyectos_activos(),
            'proyectos_pausados': []  # TODO: implementar si es necesario
        }
        
        prompt = template.render(**contexto)
        
        # Guardar histórico
        output_dir = Path('prompts/generated')
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M')}_analisis_semanal.txt"
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return prompt
```

**Complejidad:**
- Generación: O(n) donde n = proyectos activos (típicamente <10)
- Tiempo estimado: <100ms con 10 proyectos y 100 métricas totales

---

## PARSER DE RESPUESTAS IA

```python
# /sistema_90d/parser_respuestas.py

import json
from typing import Dict, List
from pathlib import Path

class ParserRespuestas:
    """
    Parsea respuestas JSON de IAs y las almacena estructuradamente.
    """
    
    @staticmethod
    def validar_formato(respuesta_json: str) -> Dict:
        """
        Valida que la respuesta tenga el formato esperado.
        
        Raises:
            ValueError: Si el formato es inválido
        """
        try:
            data = json.loads(respuesta_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}")
        
        # Validar campos obligatorios
        campos_requeridos = ['resumen_ejecutivo', 'proyectos', 'riesgos_detectados']
        faltantes = [c for c in campos_requeridos if c not in data]
        
        if faltantes:
            raise ValueError(f"Campos faltantes en respuesta: {faltantes}")
        
        # Validar estructura de proyectos
        for proyecto in data['proyectos']:
            campos_proyecto = ['id', 'nombre', 'decision', 'justificacion']
            faltantes_proy = [c for c in campos_proyecto if c not in proyecto]
            
            if faltantes_proy:
                raise ValueError(f"Proyecto {proyecto.get('nombre', '?')} falta campos: {faltantes_proy}")
            
            # Validar decisión válida
            if proyecto['decision'] not in ['kill', 'iterate', 'scale', 'pause']:
                raise ValueError(f"Decisión inválida: {proyecto['decision']}")
        
        return data
    
    @staticmethod
    def guardar_respuesta(respuesta: Dict, nombre_analisis: str) -> Path:
        """Guarda respuesta validada en archivo JSON."""
        output_dir = Path('respuestas_ia')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
        filename = f"{timestamp}_{nombre_analisis}.json"
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(respuesta, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    @staticmethod
    def aplicar_decisiones_a_db(respuesta: Dict, db_path: str) -> None:
        """
        Registra las decisiones sugeridas por la IA en la tabla `decisiones`.
        
        IMPORTANTE: Esto NO ejecuta automáticamente las decisiones (kill/scale).
        Solo las registra para revisión humana.
        """
        db = sqlite3.connect(db_path)
        
        for proyecto in respuesta['proyectos']:
            db.execute("""
                INSERT INTO decisiones (proyecto_id, tipo, justificacion, origen, fecha)
                VALUES (?, ?, ?, 'ia', unixepoch('now'))
            """, (
                proyecto['id'],
                proyecto['decision'],
                proyecto['justificacion']
            ))
        
        db.commit()
        db.close()
```

---

## FLUJO DE USO COMPLETO

### 1. Usuario genera prompt
```python
# En app.py o CLI
from generador_prompts import GeneradorPrompts

generador = GeneradorPrompts('data/sistema.db')
prompt = generador.generar_analisis_semanal()

print("=== PROMPT GENERADO ===")
print(prompt)
print("\n📋 Copia este texto y pégalo en ChatGPT/Claude/Gemini")
```

### 2. Usuario pega en su IA preferida
```
[Usuario copia prompt completo]
[Lo pega en Claude.ai, ChatGPT, o cualquier LLM]
[IA retorna JSON estructurado]
```

### 3. Usuario pega respuesta de vuelta en el sistema
```python
# En app.py o CLI
from parser_respuestas import ParserRespuestas

respuesta_ia = """
{
  "resumen_ejecutivo": "...",
  "proyectos": [...],
  "riesgos_detectados": [...]
}
"""

parser = ParserRespuestas()

# Validar formato
try:
    datos_validados = parser.validar_formato(respuesta_ia)
    
    # Guardar en histórico
    path = parser.guardar_respuesta(datos_validados, 'analisis_semanal')
    print(f"✅ Respuesta guardada en: {path}")
    
    # Registrar decisiones (sin ejecutar automáticamente)
    parser.aplicar_decisiones_a_db(datos_validados, 'data/sistema.db')
    print("✅ Decisiones registradas. Revísalas en el dashboard.")
    
except ValueError as e:
    print(f"❌ Error en respuesta IA: {e}")
```

---

## INTERFAZ WEB PARA COPIAR/PEGAR

```html
<!-- /sistema_90d/templates/exportar_ia.html -->
<h1>Generador de Prompts IA</h1>

<form hx-post="/ia/generar-prompt" hx-target="#prompt-output">
  <label>Tipo de análisis:</label>
  <select name="tipo_analisis">
    <option value="semanal">Análisis Semanal</option>
    <option value="decision">Decisión Kill/Iterate/Scale</option>
    <option value="riesgos">Detección de Riesgos</option>
  </select>
  
  <button type="submit" class="btn-primary">Generar Prompt</button>
</form>

<section id="prompt-output">
  <!-- Aquí se renderiza el prompt generado -->
  <textarea readonly rows="30" id="prompt-text">{{ prompt }}</textarea>
  
  <button onclick="navigator.clipboard.writeText(document.getElementById('prompt-text').value)" 
          class="btn-secondary">📋 Copiar</button>
  
  <a href="data:text/plain;charset=utf-8,{{ prompt_encoded }}" 
     download="prompt_{{ tipo }}_{{ fecha }}.txt" 
     class="btn-secondary">💾 Descargar</a>
</section>

<hr>

<h2>Pegar Respuesta de IA</h2>
<form hx-post="/ia/parsear-respuesta" hx-target="#resultado-parse">
  <textarea name="respuesta_ia" rows="20" placeholder="Pega aquí el JSON que te retornó la IA"></textarea>
  <button type="submit" class="btn-primary">Procesar Respuesta</button>
</form>

<div id="resultado-parse"></div>
```

---

## COMPARATIVA VS INTEGRACIÓN API DIRECTA

### Solución moderna (Anthropic SDK, OpenAI SDK)
- **Ventajas:**
  - Automatización completa
  - Sin copiar/pegar manual
- **Desventajas:**
  - Acoplamiento a un proveedor
  - Costos por API call ($0.01-$0.10 por análisis)
  - Requiere API keys, billing setup
  - Overhead: 10MB+ de SDK

### Solución elegida (Copy/Paste manual)
- **Ventajas:**
  - Libertad total de proveedor (Claude, GPT, Gemini, Llama local)
  - Costo $0 (usuario usa su cuenta personal)
  - Cero dependencias externas
  - Usuario revisa prompt antes de ejecutar (transparencia)
- **Desventajas:**
  - Fricción de 2 pasos (copiar → pegar)
  - No automatizable para análisis frecuentes

**Decisión:** Copy/paste en MVP. API opcional en Fase 2 si usuario lo pide.

---

## OPTIMIZACIONES CONSIDERADAS PERO NO APLICADAS

### 1. Interfaz web con iframe a ChatGPT
**Razón:** ChatGPT no permite embedding por CORS. No es técnicamente viable.

### 2. Plugin de navegador para auto-pegar
**Razón:** Complejidad fuera del scope del sistema local. Usuario puede usar macros de teclado si quiere.

### 3. LLM local (Ollama, Llama.cpp)
**Razón:** Requiere GPU/hardware específico. No es universal. Dejarlo como opción documentada, no default.

---

## ENTREGABLE ESPERADO

1. **Archivo generador_prompts.py** completo
2. **Archivo parser_respuestas.py** completo
3. **Plantilla analisis_semanal.txt** (Jinja2)
4. **Ruta /ia/generar-prompt en app.py**
5. **Ruta /ia/parsear-respuesta en app.py**

**Siguiente paso:** Si sistema IA aprobado, ejecutar `06_FLUJOS_DIARIOS.md`
