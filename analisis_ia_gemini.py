from gemini_integration import GeminiCLI
from prompt_generator import GeneradorPrompts
from database import get_db, transaccion_segura
import logging
from typing import Dict

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
        # Se requiere importar desde el propio modulo para usar la transaccion en contexto
        # pero para simplificar, usaremos la importada arriba
        with transaccion_segura() as db:
            for proyecto in analisis['proyectos']:
                # Verificar si ya existe decisión pendiente para este proyecto hoy?
                # Por ahora simplificamos insertando siempre
                try:
                    db.execute("""
                        INSERT INTO decisiones (proyecto_id, tipo, justificacion, origen, fecha)
                        VALUES (?, ?, ?, 'ia_gemini', date('now'))
                    """, (
                        proyecto['id'],
                        proyecto['decision'],
                        proyecto['justificacion']
                    ))
                except Exception as e:
                    logger.warning(f"Error guardando decisión para proyecto {proyecto['id']}: {e}")
            
            logger.info(f"Guardadas {len(analisis['proyectos'])} decisiones de IA")
