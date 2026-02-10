# INTEGRACIÓN GEMINI CLI + GENERADOR DE IDEAS

## ANÁLISIS DEL COMANDO GEMINI

Del output que proporcionaste:
```bash
gemini -y -p "Dame el resultado de 5 + 7"
```

Flags detectados:
- `-y`: YOLO mode (auto-aprueba tool calls)
- `-p`: Prompt inline

## IMPLEMENTACIÓN

### 1. Wrapper de Gemini CLI

```python
# /sistema_90d/gemini_integration.py

import subprocess
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger('gemini_integration')

class GeminiCLI:
    """
    Wrapper para Gemini CLI.
    Ejecuta prompts y parsea respuestas automáticamente.
    """
    
    def __init__(self, yolo_mode: bool = True):
        """
        Args:
            yolo_mode: Si True, usa -y para auto-aprobar tool calls
        """
        self.yolo_mode = yolo_mode
        self._verificar_instalacion()
    
    def _verificar_instalacion(self) -> bool:
        """Verifica que gemini CLI esté instalado."""
        try:
            result = subprocess.run(
                ['gemini', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Gemini CLI encontrado: {result.stdout.strip()}")
                return True
            else:
                raise RuntimeError("Gemini CLI no responde correctamente")
        except FileNotFoundError:
            raise RuntimeError(
                "Gemini CLI no encontrado. Instalar con: pip install gemini-cli"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Gemini CLI timeout en verificación")
    
    def ejecutar_prompt(self, prompt: str, timeout: int = 60) -> Dict:
        """
        Ejecuta un prompt en Gemini CLI y retorna respuesta parseada.
        
        Args:
            prompt: Texto del prompt
            timeout: Segundos máximos de espera
            
        Returns:
            {
                'success': bool,
                'respuesta': str,
                'error': str | None,
                'stderr': str (para debug)
            }
        """
        # Construir comando
        cmd = ['gemini']
        
        if self.yolo_mode:
            cmd.append('-y')
        
        cmd.extend(['-p', prompt])
        
        logger.info(f"Ejecutando Gemini CLI: {' '.join(cmd[:3])}... (prompt truncado)")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                # Limpiar output (remover mensajes de sistema)
                respuesta_limpia = self._limpiar_output(result.stdout)
                
                logger.info(f"Gemini respondió exitosamente ({len(respuesta_limpia)} chars)")
                
                return {
                    'success': True,
                    'respuesta': respuesta_limpia,
                    'error': None,
                    'stderr': result.stderr
                }
            else:
                logger.error(f"Gemini CLI error: {result.stderr}")
                return {
                    'success': False,
                    'respuesta': '',
                    'error': result.stderr,
                    'stderr': result.stderr
                }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Gemini CLI timeout después de {timeout}s")
            return {
                'success': False,
                'respuesta': '',
                'error': f'Timeout después de {timeout} segundos',
                'stderr': ''
            }
        
        except Exception as e:
            logger.error(f"Error ejecutando Gemini CLI: {e}", exc_info=True)
            return {
                'success': False,
                'respuesta': '',
                'error': str(e),
                'stderr': ''
            }
    
    def _limpiar_output(self, raw_output: str) -> str:
        """
        Limpia el output de Gemini CLI removiendo mensajes de sistema.
        
        Basado en tu ejemplo:
        - "YOLO mode is enabled..."
        - "Loaded cached credentials..."
        - "Hook registry initialized..."
        
        Solo queremos la respuesta real.
        """
        lineas = raw_output.strip().split('\n')
        
        # Filtrar líneas de sistema conocidas
        mensajes_sistema = [
            'YOLO mode is enabled',
            'Loaded cached credentials',
            'Hook registry initialized',
            'All tool calls will be automatically approved'
        ]
        
        lineas_limpias = []
        for linea in lineas:
            # Saltar si es mensaje de sistema
            if any(msg in linea for msg in mensajes_sistema):
                continue
            
            # Saltar líneas vacías
            if not linea.strip():
                continue
            
            lineas_limpias.append(linea)
        
        return '\n'.join(lineas_limpias).strip()
    
    def ejecutar_con_json(self, prompt: str, timeout: int = 60) -> Dict:
        """
        Ejecuta prompt que espera respuesta en JSON.
        
        Agrega instrucción para forzar JSON en la respuesta.
        """
        prompt_json = f"""{prompt}

IMPORTANTE: Retorna tu respuesta ÚNICAMENTE en formato JSON válido, sin texto adicional antes o después.
"""
        
        resultado = self.ejecutar_prompt(prompt_json, timeout)
        
        if not resultado['success']:
            return resultado
        
        # Intentar parsear JSON
        try:
            # Extraer JSON si está envuelto en markdown
            respuesta = resultado['respuesta']
            
            if '```json' in respuesta:
                # Extraer JSON de bloque markdown
                inicio = respuesta.find('```json') + 7
                fin = respuesta.find('```', inicio)
                respuesta = respuesta[inicio:fin].strip()
            elif '```' in respuesta:
                # Bloque de código sin especificar json
                inicio = respuesta.find('```') + 3
                fin = respuesta.find('```', inicio)
                respuesta = respuesta[inicio:fin].strip()
            
            # Parsear JSON
            datos_json = json.loads(respuesta)
            
            resultado['json'] = datos_json
            resultado['respuesta_parseada'] = True
            
        except json.JSONDecodeError as e:
            logger.warning(f"Respuesta no es JSON válido: {e}")
            resultado['json'] = None
            resultado['respuesta_parseada'] = False
            resultado['parse_error'] = str(e)
        
        return resultado


# Test de integración
if __name__ == '__main__':
    gemini = GeminiCLI()
    
    # Test simple
    resultado = gemini.ejecutar_prompt("Dame el resultado de 5 + 7")
    print("Respuesta:", resultado['respuesta'])
    
    # Test con JSON
    resultado = gemini.ejecutar_con_json("""
    Retorna un JSON con:
    - nombre: "Test"
    - valor: 42
    """)
    print("JSON:", resultado.get('json'))
```

---

### 2. Integración en el Sistema de Análisis

```python
# /sistema_90d/analisis_ia_gemini.py

from gemini_integration import GeminiCLI
from generador_prompts import GeneradorPrompts
from database import get_db, transaccion_segura
import logging

logger = logging.getLogger('analisis_ia_gemini')

class AnalizadorGemini:
    """
    Ejecuta análisis usando Gemini CLI automáticamente.
    Reemplaza el flujo manual de copy/paste.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.gemini = GeminiCLI(yolo_mode=True)
        self.generador = GeneradorPrompts(db_path)
    
    def analisis_semanal_automatico(self) -> Dict:
        """
        Ejecuta análisis semanal completo automáticamente.
        
        Returns:
            {
                'success': bool,
                'analisis': dict (JSON parseado de Gemini),
                'prompt_usado': str,
                'tiempo_ejecucion': float,
                'error': str | None
            }
        """
        import time
        
        logger.info("Iniciando análisis semanal automático con Gemini")
        inicio = time.time()
        
        # 1. Generar prompt
        prompt = self.generador.generar_analisis_semanal()
        logger.debug(f"Prompt generado: {len(prompt)} caracteres")
        
        # 2. Ejecutar en Gemini
        resultado = self.gemini.ejecutar_con_json(prompt, timeout=120)
        
        if not resultado['success']:
            logger.error(f"Gemini falló: {resultado['error']}")
            return {
                'success': False,
                'analisis': None,
                'prompt_usado': prompt,
                'tiempo_ejecucion': time.time() - inicio,
                'error': resultado['error']
            }
        
        if not resultado.get('respuesta_parseada'):
            logger.warning("Gemini no retornó JSON válido")
            return {
                'success': False,
                'analisis': None,
                'prompt_usado': prompt,
                'tiempo_ejecucion': time.time() - inicio,
                'error': 'Respuesta no es JSON válido',
                'respuesta_raw': resultado['respuesta']
            }
        
        # 3. Validar estructura del JSON
        analisis = resultado['json']
        
        if not self._validar_estructura_analisis(analisis):
            logger.error("Estructura de análisis inválida")
            return {
                'success': False,
                'analisis': analisis,
                'prompt_usado': prompt,
                'tiempo_ejecucion': time.time() - inicio,
                'error': 'Estructura de respuesta inválida'
            }
        
        # 4. Guardar decisiones en DB
        self._guardar_decisiones_ia(analisis)
        
        tiempo_total = time.time() - inicio
        logger.info(f"Análisis completado en {tiempo_total:.2f}s")
        
        return {
            'success': True,
            'analisis': analisis,
            'prompt_usado': prompt,
            'tiempo_ejecucion': tiempo_total,
            'error': None
        }
    
    def _validar_estructura_analisis(self, analisis: dict) -> bool:
        """Valida que el JSON tenga la estructura esperada."""
        campos_requeridos = ['resumen_ejecutivo', 'proyectos', 'riesgos_detectados']
        
        if not all(campo in analisis for campo in campos_requeridos):
            return False
        
        # Validar que proyectos sea lista
        if not isinstance(analisis['proyectos'], list):
            return False
        
        # Validar estructura de cada proyecto
        for proyecto in analisis['proyectos']:
            if not all(k in proyecto for k in ['id', 'decision', 'justificacion']):
                return False
        
        return True
    
    def _guardar_decisiones_ia(self, analisis: dict):
        """Guarda las decisiones de IA en la base de datos."""
        with transaccion_segura() as db:
            for proyecto in analisis['proyectos']:
                db.execute("""
                    INSERT INTO decisiones (proyecto_id, tipo, justificacion, origen, fecha)
                    VALUES (?, ?, ?, 'ia_gemini', unixepoch('now'))
                """, (
                    proyecto['id'],
                    proyecto['decision'],
                    proyecto['justificacion']
                ))
            
            logger.info(f"Guardadas {len(analisis['proyectos'])} decisiones de IA")
```

---

### 3. Sistema de Generación de Ideas

```python
# /sistema_90d/generador_ideas.py

from gemini_integration import GeminiCLI
from database import get_db
import logging

logger = logging.getLogger('generador_ideas')

class GeneradorIdeas:
    """
    Genera ideas de proyectos usando Gemini CLI.
    
    - Si hay proyectos existentes: Ideas relacionadas/complementarias
    - Si no hay proyectos: Ideas nuevas según tendencias
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.gemini = GeminiCLI(yolo_mode=True)
    
    def generar_ideas(self, cantidad: int = 5) -> Dict:
        """
        Genera ideas de proyectos.
        
        Args:
            cantidad: Número de ideas a generar (1-10)
            
        Returns:
            {
                'success': bool,
                'ideas': [
                    {
                        'nombre': str,
                        'descripcion': str,
                        'hipotesis': str,
                        'mercado_objetivo': str,
                        'dificultad': 'baja' | 'media' | 'alta',
                        'tiempo_estimado_mvp': str,
                        'razon_sugerencia': str
                    }
                ],
                'contexto': 'con_proyectos' | 'sin_proyectos',
                'error': str | None
            }
        """
        # Limitar cantidad
        cantidad = max(1, min(10, cantidad))
        
        # Obtener contexto de proyectos existentes
        contexto = self._obtener_contexto_proyectos()
        
        # Generar prompt según contexto
        if contexto['tiene_proyectos']:
            prompt = self._prompt_ideas_relacionadas(contexto, cantidad)
        else:
            prompt = self._prompt_ideas_nuevas(cantidad)
        
        # Ejecutar en Gemini
        resultado = self.gemini.ejecutar_con_json(prompt, timeout=90)
        
        if not resultado['success']:
            logger.error(f"Gemini falló generando ideas: {resultado['error']}")
            return {
                'success': False,
                'ideas': [],
                'contexto': 'con_proyectos' if contexto['tiene_proyectos'] else 'sin_proyectos',
                'error': resultado['error']
            }
        
        if not resultado.get('respuesta_parseada'):
            return {
                'success': False,
                'ideas': [],
                'contexto': 'con_proyectos' if contexto['tiene_proyectos'] else 'sin_proyectos',
                'error': 'Respuesta no es JSON válido'
            }
        
        ideas = resultado['json'].get('ideas', [])
        
        return {
            'success': True,
            'ideas': ideas,
            'contexto': 'con_proyectos' if contexto['tiene_proyectos'] else 'sin_proyectos',
            'error': None
        }
    
    def _obtener_contexto_proyectos(self) -> Dict:
        """Obtiene información de proyectos existentes."""
        db = get_db()
        
        # Proyectos activos/winners
        cursor = db.execute("""
            SELECT 
                p.id,
                p.nombre,
                p.hipotesis,
                p.estado,
                COALESCE(SUM(m.ingresos), 0) as ingresos_total
            FROM proyectos p
            LEFT JOIN metricas m ON m.proyecto_id = p.id
            WHERE p.estado IN ('active', 'mvp', 'winner')
            GROUP BY p.id
            ORDER BY ingresos_total DESC
            LIMIT 5
        """)
        
        proyectos_activos = [
            {
                'nombre': row[1],
                'hipotesis': row[2],
                'estado': row[3],
                'ingresos': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Proyectos killed (aprendizajes)
        cursor = db.execute("""
            SELECT nombre, razon_kill
            FROM proyectos
            WHERE estado = 'killed'
            ORDER BY fecha_kill DESC
            LIMIT 3
        """)
        
        proyectos_killed = [
            {'nombre': row[0], 'razon': row[1]}
            for row in cursor.fetchall()
        ]
        
        return {
            'tiene_proyectos': len(proyectos_activos) > 0,
            'proyectos_activos': proyectos_activos,
            'proyectos_killed': proyectos_killed
        }
    
    def _prompt_ideas_relacionadas(self, contexto: Dict, cantidad: int) -> str:
        """Genera prompt para ideas relacionadas a proyectos existentes."""
        
        proyectos_desc = "\n".join([
            f"- {p['nombre']}: {p['hipotesis']} (Estado: {p['estado']}, Ingresos: ${p['ingresos']})"
            for p in contexto['proyectos_activos']
        ])
        
        aprendizajes = ""
        if contexto['proyectos_killed']:
            aprendizajes = "\n\nProyectos killed (aprendizajes):\n" + "\n".join([
                f"- {p['nombre']}: {p['razon']}"
                for p in contexto['proyectos_killed']
            ])
        
        return f"""Eres un experto en emprendimiento SaaS y productos digitales.

PROYECTOS ACTUALES DEL USUARIO:
{proyectos_desc}
{aprendizajes}

TAREA:
Genera {cantidad} ideas de NUEVOS proyectos que:
1. Sean complementarios o relacionados a los proyectos actuales
2. Aprovechen aprendizajes de proyectos killed (evitar mismos errores)
3. Sean viables para un solopreneur técnico
4. Puedan lanzar MVP en <30 días
5. Tengan potencial de monetización temprana

CRITERIOS OBLIGATORIOS:
- NO sugerir lo que ya está haciendo
- Priorizar ideas que aprovechen assets/conocimiento existente
- Considerar cross-selling o bundling con proyectos exitosos
- Evitar ideas similares a proyectos killed

FORMATO DE RESPUESTA (JSON):
{{
  "ideas": [
    {{
      "nombre": "Nombre descriptivo del proyecto",
      "descripcion": "Qué es y qué hace (1-2 oraciones)",
      "hipotesis": "Quién paga y cuánto por qué problema",
      "mercado_objetivo": "Segmento específico de usuarios",
      "dificultad": "baja" | "media" | "alta",
      "tiempo_estimado_mvp": "Días estimados para MVP funcional",
      "razon_sugerencia": "Por qué es buena idea dado el contexto actual"
    }}
  ]
}}

Retorna SOLO el JSON, sin texto adicional.
"""
    
    def _prompt_ideas_nuevas(self, cantidad: int) -> str:
        """Genera prompt para ideas completamente nuevas."""
        
        from datetime import datetime
        año_actual = datetime.now().year
        
        return f"""Eres un experto en emprendimiento SaaS y productos digitales.

CONTEXTO:
El usuario es un solopreneur técnico que está empezando su primer ciclo de 90 días.
NO tiene proyectos activos actualmente.

TAREA:
Genera {cantidad} ideas de proyectos SaaS/productos digitales que:
1. Sean viables para un solopreneur sin capital inicial
2. Puedan lanzar MVP en <30 días
3. Tengan demanda validada en {año_actual}
4. Permitan monetización desde día 1
5. NO requieran equipo grande

TENDENCIAS A CONSIDERAR ({año_actual}):
- IA generativa (ChatGPT, Claude, etc.)
- Automatización con IA
- Herramientas para creadores de contenido
- Productividad personal
- Micro-SaaS verticales (nichos específicos)

CRITERIOS:
- Priorizar ideas con competencia existente (valida demanda)
- Evitar "marketplaces" o "redes sociales" (requieren masa crítica)
- Enfocarse en resolver 1 problema específico muy bien

FORMATO DE RESPUESTA (JSON):
{{
  "ideas": [
    {{
      "nombre": "Nombre descriptivo del proyecto",
      "descripcion": "Qué es y qué hace (1-2 oraciones)",
      "hipotesis": "Quién paga y cuánto por qué problema",
      "mercado_objetivo": "Segmento específico de usuarios",
      "dificultad": "baja" | "media" | "alta",
      "tiempo_estimado_mvp": "Días estimados para MVP funcional",
      "razon_sugerencia": "Por qué es buena idea para un solopreneur en {año_actual}"
    }}
  ]
}}

Retorna SOLO el JSON, sin texto adicional.
"""
```

---

### 4. Rutas en app.py

```python
# /sistema_90d/app.py (agregar estas rutas)

from analisis_ia_gemini import AnalizadorGemini
from generador_ideas import GeneradorIdeas

@app.route('/ia/analisis-automatico', methods=['POST'])
def analisis_automatico():
    """
    Ejecuta análisis semanal automáticamente con Gemini CLI.
    NO requiere copy/paste manual.
    """
    try:
        analizador = AnalizadorGemini('data/sistema.db')
        resultado = analizador.analisis_semanal_automatico()
        
        if resultado['success']:
            return render_template('components/analisis_resultado.html',
                analisis=resultado['analisis'],
                tiempo=resultado['tiempo_ejecucion']
            )
        else:
            return {
                'status': 'error',
                'mensaje': resultado['error']
            }, 500
    
    except RuntimeError as e:
        # Gemini CLI no instalado
        return {
            'status': 'error',
            'mensaje': f'Error de configuración: {str(e)}',
            'solucion': 'Instala Gemini CLI con: pip install gemini-cli'
        }, 500
    
    except Exception as e:
        logger.error(f"Error en análisis automático: {e}", exc_info=True)
        return {
            'status': 'error',
            'mensaje': 'Error interno del servidor'
        }, 500


@app.route('/ideas/generar', methods=['POST'])
def generar_ideas():
    """
    Genera ideas de proyectos con Gemini.
    """
    cantidad = int(request.form.get('cantidad', 5))
    
    try:
        generador = GeneradorIdeas('data/sistema.db')
        resultado = generador.generar_ideas(cantidad)
        
        if resultado['success']:
            return render_template('components/ideas_generadas.html',
                ideas=resultado['ideas'],
                contexto=resultado['contexto']
            )
        else:
            return {
                'status': 'error',
                'mensaje': resultado['error']
            }, 500
    
    except Exception as e:
        logger.error(f"Error generando ideas: {e}", exc_info=True)
        return {
            'status': 'error',
            'mensaje': 'Error interno del servidor'
        }, 500


@app.route('/ideas')
def pagina_ideas():
    """
    Página dedicada a generación de ideas.
    """
    return render_template('ideas.html')
```

---

### 5. Templates HTML

```html
<!-- /sistema_90d/templates/ideas.html -->

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Generador de Ideas - Sistema 90D</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/ideas.css">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body>
    <div class="ideas-container">
        
        <header class="ideas-header">
            <h1>💡 Generador de Ideas de Proyectos</h1>
            <a href="/" class="btn-volver">← Dashboard</a>
        </header>

        <section class="generador-seccion">
            <div class="generador-card">
                <h2>Generar Nuevas Ideas</h2>
                <p>Usa IA para generar ideas de proyectos basadas en tu contexto actual.</p>
                
                <form hx-post="/ideas/generar" 
                      hx-target="#ideas-resultado"
                      hx-indicator="#loading">
                    
                    <label for="cantidad">¿Cuántas ideas generar?</label>
                    <select name="cantidad" id="cantidad">
                        <option value="3">3 ideas</option>
                        <option value="5" selected>5 ideas</option>
                        <option value="7">7 ideas</option>
                        <option value="10">10 ideas</option>
                    </select>
                    
                    <button type="submit" class="btn-primary btn-lg">
                        🤖 Generar Ideas con IA
                    </button>
                    
                    <div id="loading" class="htmx-indicator">
                        <div class="spinner"></div>
                        <p>Generando ideas con Gemini... (puede tomar 30-60s)</p>
                    </div>
                </form>
            </div>
        </section>

        <section id="ideas-resultado" class="ideas-resultado">
            <!-- Aquí se cargarán las ideas generadas -->
            <div class="placeholder">
                <p>👆 Genera ideas para ver resultados aquí</p>
            </div>
        </section>

    </div>
</body>
</html>
```

```html
<!-- /sistema_90d/templates/components/ideas_generadas.html -->

<div class="ideas-generadas">
    <div class="ideas-header">
        <h2>💡 Ideas Generadas</h2>
        <span class="ideas-badge">
            {{ ideas|length }} ideas 
            {% if contexto == 'con_proyectos' %}
            (relacionadas a tus proyectos)
            {% else %}
            (ideas nuevas)
            {% endif %}
        </span>
    </div>

    <div class="ideas-grid">
        {% for idea in ideas %}
        <div class="idea-card idea-dificultad-{{ idea.dificultad }}">
            <div class="idea-header">
                <h3>{{ idea.nombre }}</h3>
                <span class="dificultad-badge badge-{{ idea.dificultad }}">
                    {{ idea.dificultad }}
                </span>
            </div>
            
            <p class="idea-descripcion">{{ idea.descripcion }}</p>
            
            <div class="idea-detalles">
                <div class="detalle-item">
                    <strong>💰 Hipótesis:</strong>
                    <p>{{ idea.hipotesis }}</p>
                </div>
                
                <div class="detalle-item">
                    <strong>🎯 Mercado:</strong>
                    <p>{{ idea.mercado_objetivo }}</p>
                </div>
                
                <div class="detalle-item">
                    <strong>⏱️ Tiempo estimado MVP:</strong>
                    <p>{{ idea.tiempo_estimado_mvp }}</p>
                </div>
                
                <div class="detalle-item">
                    <strong>✨ Por qué esta idea:</strong>
                    <p>{{ idea.razon_sugerencia }}</p>
                </div>
            </div>
            
            <div class="idea-acciones">
                <button hx-post="/proyectos/crear-desde-idea" 
                        hx-vals='{"nombre": "{{ idea.nombre }}", "hipotesis": "{{ idea.hipotesis }}"}'
                        hx-target="#modal"
                        class="btn-primary">
                    ➕ Crear Proyecto
                </button>
                <button class="btn-secondary" onclick="copiarIdea(this)">
                    📋 Copiar
                </button>
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<script>
function copiarIdea(button) {
    const card = button.closest('.idea-card');
    const nombre = card.querySelector('h3').textContent;
    const descripcion = card.querySelector('.idea-descripcion').textContent;
    const hipotesis = card.querySelectorAll('.detalle-item p')[0].textContent;
    
    const texto = `${nombre}\n\n${descripcion}\n\nHipótesis: ${hipotesis}`;
    
    navigator.clipboard.writeText(texto).then(() => {
        button.textContent = '✓ Copiado';
        setTimeout(() => button.textContent = '📋 Copiar', 2000);
    });
}
</script>
```

---

### 6. Agregar al Dashboard

```html
<!-- En templates/components/acciones_rapidas.html, agregar: -->

<div class="categoria-acciones">
    <h3>💡 Ideas</h3>
    <div class="acciones-grid">
        <a href="/ideas" class="accion-btn accion-ideas">
            <span class="accion-icono">💡</span>
            <span class="accion-texto">Generar Ideas</span>
        </a>
        
        <button hx-post="/ia/analisis-automatico" 
                hx-target="#modal"
                hx-indicator="#loading-analisis"
                class="accion-btn accion-ia">
            <span class="accion-icono">🤖</span>
            <span class="accion-texto">Análisis Automático</span>
        </button>
    </div>
</div>
```

---

## INSTALACIÓN DE GEMINI CLI

```bash
# Instalar Gemini CLI
npm install -g @google/gemini-cli@latest

# Configurar (primera vez)
gemini setup

# Verificar instalación
gemini --version
```

---

## COMPARATIVA: MANUAL vs AUTOMÁTICO

| Aspecto | Copy/Paste Manual | Gemini CLI Auto |
|---------|-------------------|-----------------|
| Pasos del usuario | 8 (generar, copiar, abrir IA, pegar, copiar respuesta, volver, pegar, procesar) | 1 (clic en botón) |
| Tiempo | 3-5 minutos | 30-60 segundos |
| Flexibilidad IA | Total (cualquier IA) | Solo Gemini |
| Costo | $0 (usa cuenta personal) | $0 (usa Gemini CLI) |
| Requiere internet | Sí | Sí |
| Setup inicial | Ninguno | `gemini setup` |

---

## VENTAJAS DE ESTA IMPLEMENTACIÓN

✅ **Automático**: 1 clic → respuesta completa  
✅ **Integrado**: Sin salir del sistema  
✅ **Generador de ideas**: Novedad útil  
✅ **Fallback**: Si Gemini falla, sigue funcionando copy/paste manual  
✅ **Logging**: Todas las interacciones quedan registradas  

¿Quieres que genere el código completo funcional de todos estos archivos ahora?
