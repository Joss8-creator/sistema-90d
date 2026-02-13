from gemini_integration import GeminiCLI
from database import get_db
import logging
from datetime import datetime

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
    
    def generar_ideas(self, cantidad: int = 5) -> dict:
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
                        'razon_sugerencia': str,
                        'puntuacion_viabilidad': int (1-10)
                    }
                ],
                'contexto': 'con_proyectos' | 'sin_proyectos',
                'error': str | None
            }
        """
        # Limitar cantidad
        cantidad = max(1, min(10, cantidad))
        
        logger.info(f"Generando {cantidad} ideas de proyectos")
        
        # Obtener contexto de proyectos existentes
        contexto = self._obtener_contexto_proyectos()
        
        # Generar prompt según contexto
        if contexto['tiene_proyectos']:
            prompt = self._prompt_ideas_relacionadas(contexto, cantidad)
            tipo_contexto = 'con_proyectos'
        else:
            prompt = self._prompt_ideas_nuevas(cantidad)
            tipo_contexto = 'sin_proyectos'
        
        logger.info(f"Contexto: {tipo_contexto}")
        
        # Ejecutar en Gemini
        resultado = self.gemini.ejecutar_con_json(prompt, timeout=120)
        
        if not resultado['success']:
            logger.error(f"Gemini falló generando ideas: {resultado['error']}")
            return {
                'success': False,
                'ideas': [],
                'contexto': tipo_contexto,
                'error': resultado['error']
            }
        
        if not resultado.get('respuesta_parseada'):
            logger.error("Respuesta no es JSON válido")
            return {
                'success': False,
                'ideas': [],
                'contexto': tipo_contexto,
                'error': 'Respuesta no es JSON válido',
                'respuesta_raw': resultado['respuesta']
            }
        
        # CORRECCIÓN: Manejar tanto array directo como objeto {ideas: [...]}
        json_data = resultado['json']
        
        if isinstance(json_data, list):
            # Gemini retornó array directo: [{idea1}, {idea2}, ...]
            ideas = json_data
            logger.info(f"Gemini retornó array directo con {len(ideas)} ideas")
        elif isinstance(json_data, dict) and 'ideas' in json_data:
            # Gemini retornó objeto: {ideas: [{idea1}, {idea2}, ...]}
            ideas = json_data['ideas']
            logger.info(f"Gemini retornó objeto con {len(ideas)} ideas")
        else:
            # Formato inesperado
            logger.error(f"Formato JSON inesperado: {type(json_data)}")
            return {
                'success': False,
                'ideas': [],
                'contexto': tipo_contexto,
                'error': f'Formato JSON inesperado. Recibido: {type(json_data).__name__}'
            }
        
        logger.info(f"Generadas {len(ideas)} ideas exitosamente")
        
        # Validar y enriquecer ideas
        ideas_validadas = []
        for i, idea in enumerate(ideas, 1):
            if self._validar_estructura_idea(idea):
                # Agregar puntuación de viabilidad si no existe
                if 'puntuacion_viabilidad' not in idea:
                    idea['puntuacion_viabilidad'] = self._calcular_viabilidad(idea)
                ideas_validadas.append(idea)
            else:
                logger.warning(f"Idea {i} descartada por estructura inválida")
        
        return {
            'success': True,
            'ideas': ideas_validadas,
            'contexto': tipo_contexto,
            'error': None
        }
    
    def _obtener_contexto_proyectos(self) -> dict:
        """Obtiene información de proyectos existentes."""
        db = get_db()
        
        # Proyectos activos/winners
        cursor = db.execute("""
            SELECT 
                p.id,
                p.nombre,
                p.hipotesis,
                p.estado,
                COALESCE(SUM(m.ingresos), 0) as ingresos_total,
                (julianday('now') - julianday(p.fecha_inicio)) as dias_activo
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
                'ingresos': float(row[4]),
                'dias_activo': int(row[5])
            }
            for row in cursor.fetchall()
        ]
        
        # Proyectos killed (aprendizajes)
        cursor = db.execute("""
            SELECT nombre, razon_kill
            FROM proyectos
            WHERE estado = 'killed'
              AND razon_kill IS NOT NULL
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
    
    def _prompt_ideas_relacionadas(self, contexto: dict, cantidad: int) -> str:
        """Genera prompt para ideas relacionadas a proyectos existentes."""
        
        proyectos_desc = "\n".join([
            f"- {p['nombre']}: {p['hipotesis']}"
            for p in contexto['proyectos_activos']
        ])
        
        return f"""GENERA UN ARRAY JSON CON EXACTAMENTE {cantidad} IDEAS SAAS.
BASADAS EN ESTOS PROYECTOS EXISTENTES PARA CREAR UN ECOSISTEMA:
{proyectos_desc}

PARA CADA IDEA, DEBES INCLUIR OBLIGATORIAMENTE TODOS ESTOS CAMPOS:
[
  {{
    "nombre": "Nombre corto y pegadizo",
    "descripcion": "Explicación de 1 frase",
    "hipotesis": "Si [acción], entonces [resultado esperado] porque [razón]",
    "mercado_objetivo": "Perfil específico (ej. Dueños de agencias Shopify)",
    "dificultad": "baja" o "media" o "alta",
    "tiempo_estimado_mvp": "Ej. 2 semanas",
    "razon_sugerencia": "Por qué conecta con los proyectos actuales",
    "puntuacion_viabilidad": 1-10
  }}
]
RESPONDE ÚNICAMENTE EL ARRAY JSON, SIN TEXTO ADICIONAL NI COMENTARIOS."""
    
    def _prompt_ideas_nuevas(self, cantidad: int) -> str:
        """Genera prompt para ideas completamente nuevas."""
        return f"""GENERA UN ARRAY JSON CON EXACTAMENTE {cantidad} IDEAS SAAS PARA SOLOPRENEURS.

PARA CADA IDEA, DEBES INCLUIR OBLIGATORIAMENTE TODOS ESTOS CAMPOS:
[
  {{
    "nombre": "Nombre corto y pegadizo",
    "descripcion": "Explicación de 1 frase",
    "hipotesis": "Si [acción], entonces [resultado esperado] porque [razón]",
    "mercado_objetivo": "Perfil específico (ej. Creadores de contenido en X)",
    "dificultad": "baja" o "media" o "alta",
    "tiempo_estimado_mvp": "Ej. 3 semanas",
    "razon_sugerencia": "Por qué es una buena oportunidad ahora",
    "puntuacion_viabilidad": 1-10
  }}
]
RESPONDE ÚNICAMENTE EL ARRAY JSON, SIN TEXTO ADICIONAL NI COMENTARIOS."""
    
    def _validar_estructura_idea(self, idea: dict) -> bool:
        """Valida que una idea tenga la estructura correcta."""
        # Campos críticos sin los cuales la idea no sirve
        campos_criticos = ['nombre', 'descripcion', 'hipotesis']
        
        # Verificar campos críticos
        if not all(campo in idea for campo in campos_criticos):
            campos_faltantes = [c for c in campos_criticos if c not in idea]
            logger.warning(f"Idea '{idea.get('nombre', 'sin nombre')}' faltante campos críticos: {campos_faltantes}")
            return False
            
        # Rellenar campos opcionales con valores por defecto si faltan
        defaults = {
            'mercado_objetivo': 'Solopreneurs y emprendedores',
            'dificultad': 'media',
            'tiempo_estimado_mvp': '2-4 semanas',
            'razon_sugerencia': 'Oportunidad de mercado detectada',
            'puntuacion_viabilidad': 7
        }
        
        for campo, valor in defaults.items():
            if campo not in idea or not idea[campo]:
                idea[campo] = valor
                logger.debug(f"Campo '{campo}' rellenado con default para idea '{idea['nombre']}'")
        
        # Validar dificultad
        if idea['dificultad'].lower() not in ['baja', 'media', 'alta']:
            idea['dificultad'] = 'media'
        
        return True
    
    def _calcular_viabilidad(self, idea: dict) -> int:
        """
        Calcula puntuación de viabilidad (1-10) basada en características.
        
        Factores:
        - Dificultad (baja = +3, media = +2, alta = +1)
        - Tiempo MVP (<15 días = +3, <30 días = +2, >30 días = +1)
        - Especificidad del mercado (mencionado específico = +2)
        - Hipótesis clara con precio = +2
        """
        puntuacion = 0
        
        # Factor 1: Dificultad
        if idea['dificultad'] == 'baja':
            puntuacion += 3
        elif idea['dificultad'] == 'media':
            puntuacion += 2
        else:
            puntuacion += 1
        
        # Factor 2: Tiempo MVP
        tiempo = idea['tiempo_estimado_mvp'].lower()
        if 'día' in tiempo or 'day' in tiempo:
            dias = int(''.join(filter(str.isdigit, tiempo)) or '30')
            if dias <= 15:
                puntuacion += 3
            elif dias <= 30:
                puntuacion += 2
            else:
                puntuacion += 1
        elif 'semana' in tiempo or 'week' in tiempo:
            semanas = int(''.join(filter(str.isdigit, tiempo)) or '4')
            if semanas <= 2:
                puntuacion += 2
            else:
                puntuacion += 1
        
        # Factor 3: Mercado específico
        mercado = idea['mercado_objetivo'].lower()
        if any(palabra in mercado for palabra in ['cto', 'ceo', 'developer', 'diseñador', 'consultor']):
            puntuacion += 2
        
        # Factor 4: Precio en hipótesis
        if '$' in idea['hipotesis'] or 'pagan' in idea['hipotesis'].lower():
            puntuacion += 2
        
        # Normalizar a 1-10
        return min(10, max(1, puntuacion))


# Test
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    generador = GeneradorIdeas('data/sistema.db')
    
    print("Generando 3 ideas...")
    resultado = generador.generar_ideas(3)
    
    if resultado['success']:
        print(f"\n[OK] Generadas {len(resultado['ideas'])} ideas:")
        for i, idea in enumerate(resultado['ideas'], 1):
            print(f"\n{i}. {idea['nombre']}")
            print(f"   Descripción: {idea['descripcion']}")
            print(f"   Hipótesis: {idea['hipotesis']}")
            print(f"   Viabilidad: {idea.get('puntuacion_viabilidad', 'N/A')}/10")
    else:
        print(f"\n[ERROR] Error: {resultado['error']}")