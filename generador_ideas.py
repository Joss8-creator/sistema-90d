from gemini_integration import GeminiCLI
from database import get_connection
import logging
from typing import Dict

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
        db = get_connection()
        try:
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
            try:
                # Check if razon_kill column exists, if not, handle gracefully
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
            except Exception:
                # Fallback if column doesn't exist yet
                proyectos_killed = []
                
            return {
                'tiene_proyectos': len(proyectos_activos) > 0,
                'proyectos_activos': proyectos_activos,
                'proyectos_killed': proyectos_killed
            }
        finally:
            db.close()
    
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
