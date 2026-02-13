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
