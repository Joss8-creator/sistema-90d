import subprocess
import json
import re
import sys
import os
import shutil
from typing import Dict, List, Optional, Union, Any, Tuple

# Intentar usar logger centralizado, fallback a logging estándar
try:
    from logger_config import logger_app
    logger = logger_app.getChild('gemini_integration')
except (ImportError, AttributeError):
    import logging
    logger = logging.getLogger('gemini_integration')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] gemini: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

class GeminiCLI:
    """
    Wrapper robusto y fiable para Gemini CLI (Versión npm y pip).
    """
    
    # Patrones de "ruido" detectados en la versión npm que deben ser filtrados
    NOISE_PATTERNS = [
        r"YOLO mode is enabled",
        r"Loaded cached credentials",
        r"Hook registry initialized",
        r"All tool calls will be automatically approved",
        r"Project hooks disabled",
        r"Update available",
        r"Checking for updates",
        r"^\[\d{2}:\d{2}:\d{2}\]", 
        r"Processing instructions",
        r"Approval mode overridden",
        r"folder is not trusted",
        r"Using model:",
        r"tokens used",
        r"Entendido,?\s+Josu[ée]",  # Filtrar saludos personalizados
        r"Estoy listo para",
        r"Quedo a la espera",
        # Patrones adicionales opcionales:
        r"Generating response",
        r"Streaming",
        r"^Done\.",
        r"^$"  # Líneas vacías
    ]

    ERROR_MAPPING = {
        'metaclasses with custom tp_new': ('Incompatibilidad detectada entre Protobuf y tu versión de Python.', 'ENV_COMPATIBILITY_ERROR'),
        '429': ('Has excedido la cuota de la API de Gemini.', 'RATE_LIMIT'),
        '401': ('Error de autenticación. Verifica tu API Key.', 'AUTH_ERROR'),
        '500': ('Error interno de Google Gemini.', 'SERVER_ERROR'),
        'connection': ('Error de conexión a internet.', 'NETWORK_ERROR'),
        'timeout': ('La solicitud ha excedido el tiempo de espera.', 'TIMEOUT')
    }

    def __init__(self, yolo_mode: bool = True):
        self.yolo_mode = yolo_mode
        self.ejecutable = self._encontrar_ejecutable()
        self._verificar_instalacion()
    
    def _encontrar_ejecutable(self) -> str:
        # Prioridad 1: Versión npm (la que usa el usuario)
        npm_gemini = shutil.which('gemini')
        if npm_gemini:
            logger.debug(f"Usando Gemini CLI npm: {npm_gemini}")
            return npm_gemini

        # Prioridad 2: Python 3.13 fallback
        py313 = r'C:\Python313\python.exe'
        if os.path.exists(py313):
            logger.debug(f"Usando Gemini CLI Python 3.13: {py313}")
            return f"{py313} -m gemini_cli"
        
        logger.debug("Usando comando 'gemini' por defecto")
        return 'gemini'

    def _verificar_instalacion(self) -> None:
        try:
            is_windows = sys.platform == 'win32'
            base_cmd = self.ejecutable.split() if ' ' in self.ejecutable else [self.ejecutable]
            # Verificación rápida con ayuda (-h)
            result = subprocess.run(
                base_cmd + ['-h'], 
                capture_output=True, 
                timeout=10, 
                shell=is_windows
            )
            if result.returncode != 0:
                raise RuntimeError(f"Gemini CLI retornó código {result.returncode}")
            logger.info("[OK] Gemini CLI verificado correctamente")
        except Exception as e:
            logger.error(f"[ERROR] Gemini CLI no funcional: {e}")
            raise RuntimeError("Gemini CLI no encontrado o no funcional en el sistema.")

    def ejecutar_prompt(self, prompt: str, timeout: int = 60) -> Dict[str, Any]:
        base_cmd = self.ejecutable.split() if ' ' in self.ejecutable else [self.ejecutable]
        cmd = base_cmd.copy()
        
        # Flags para versión npm/estándar
        if self.yolo_mode:
            cmd.append('-y')
        cmd.extend(['-p', prompt])
        
        logger.info(f"Enviando prompt a Gemini ({len(prompt)} caracteres)...")
        
        try:
            is_windows = sys.platform == 'win32'
            # Forzar UTF-8 y limpiar ANSI al leer
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=is_windows,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                respuesta_limpia = self._limpiar_output(result.stdout)
                logger.info(f"[OK] Gemini respondió ({len(respuesta_limpia)} caracteres)")
                return {
                    'success': True,
                    'respuesta': respuesta_limpia,
                    'error': None
                }
            else:
                msg, code = self._analizar_error(result.stderr)
                logger.error(f"[ERROR] Gemini error: {msg} (código: {code})")
                return {
                    'success': False, 
                    'respuesta': '', 
                    'error': msg, 
                    'codigo_error': code
                }
        except subprocess.TimeoutExpired:
            logger.error(f"[ERROR] Timeout después de {timeout}s")
            return {
                'success': False, 
                'respuesta': '', 
                'error': f'Timeout después de {timeout} segundos', 
                'codigo_error': 'TIMEOUT'
            }
        except Exception as e:
            logger.error(f"[ERROR] Excepción: {e}")
            return {
                'success': False, 
                'respuesta': '', 
                'error': str(e), 
                'codigo_error': 'EXCEPTION'
            }

    def ejecutar_con_json(self, prompt: str, timeout: int = 60) -> Dict[str, Any]:
        """Ejecuta un prompt esperando una respuesta JSON."""
        # Volvemos a usar ejecutar_prompt estándar pero con mejor extracción
        resultado = self.ejecutar_prompt(prompt, timeout)
        
        if not resultado['success']:
            return resultado
        
        respuesta = resultado['respuesta']
        json_data = self._extraer_json(respuesta)
        
        if json_data is not None:
            return {
                'success': True,
                'json': json_data,
                'respuesta': respuesta,
                'respuesta_parseada': True,
                'error': None
            }
        
        # Si falló el parseo, intentar una vez más con un prompt de "solo JSON"
        # pero por ahora devolvemos el error para no entrar en bucles
        logger.warning(f"[WARN] Falló extracción de JSON. Respuesta recibida: {respuesta[:200]}...")
        return {
            'success': False,
            'respuesta': respuesta,
            'error': "La respuesta no pudo ser convertida a JSON válido",
            'codigo_error': 'INVALID_JSON',
            'respuesta_parseada': False
        }

    def _limpiar_output(self, raw_output: str) -> str:
        """
        Limpia output de Gemini CLI eliminando:
        - Códigos ANSI (colores)
        - Mensajes de sistema (YOLO mode, hooks, etc.)
        - Líneas vacías
        """
        # Eliminar códigos ANSI (colores)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        texto = ansi_escape.sub('', raw_output)
        
        lines = texto.splitlines()
        clean_lines = []
        
        for line in lines:
            if not line.strip():
                continue
            
            # Filtrar líneas que coinciden con patrones de ruido
            if any(re.search(p, line, re.IGNORECASE) for p in self.NOISE_PATTERNS):
                continue
            
            clean_lines.append(line)
        
        resultado = '\n'.join(clean_lines).strip()
        
        # Debug: Si limpiamos demasiado, advertir
        if not resultado and raw_output:
            logger.warning(f"[WARN] Limpieza de output resultó en cadena vacía. Output original ({len(raw_output)} chars):\n{raw_output}")
        
        return resultado

    def _extraer_json(self, texto: str) -> Optional[Union[Dict, List]]:
        """
        Extrae JSON de texto que puede contener markdown, texto adicional, etc.
        """
        if not texto:
            return None

        # Guardar copia del texto original para log en caso de error
        texto_original = texto

        # 1. Buscar bloques Markdown ```json o ```
        bloques = re.findall(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", texto, re.DOTALL)
        for b in bloques:
            try:
                # Limpiar posibles caracteres invisibles o comentarios si fuera necesario
                return json.loads(b.strip())
            except Exception as e:
                logger.debug(f"Fallo al parsear bloque JSON: {e}")
                continue

        # 2. Intentar parsear el texto completo (por si Gemini solo devolvió el JSON)
        try:
            return json.loads(texto.strip())
        except:
            pass

        # 3. Buscar por delimitadores extremos { } o [ ]
        try:
            s_obj = texto.find('{')
            s_arr = texto.find('[')
            
            if s_obj == -1 and s_arr == -1:
                return None
            
            # ... resto de la lógica ...
            if s_obj != -1 and (s_arr == -1 or s_obj < s_arr):
                start = s_obj
                end = texto.rfind('}')
            else:
                start = s_arr
                end = texto.rfind(']')
            
            if start != -1 and end != -1 and end > start:
                json_str = texto[start:end+1]
                return json.loads(json_str)
        except Exception as e:
            logger.debug(f"Fallo en búsqueda por delimitadores: {e}")

        logger.warning(f"[ERROR] No se pudo extraer JSON de la respuesta: {texto_original[:200]}...")
        return None

    def _analizar_error(self, stderr: str) -> Tuple[str, str]:
        """
        Analiza stderr y retorna mensaje amigable + código de error.
        """
        if not stderr:
            return ("Error desconocido", "UNKNOWN")
        
        err = stderr.lower()
        
        for patron, (msg, code) in self.ERROR_MAPPING.items():
            if patron in err:
                return (msg, code)
        
        # Error no mapeado - retornar stderr truncado
        return (f"Error de la CLI: {stderr[:200]}", "CLI_ERROR")


# Test de integración
if __name__ == '__main__':
    print("=== Test de Gemini CLI Integration ===\n")
    
    try:
        cli = GeminiCLI()
        print(f"[OK] Usando: {cli.ejecutable}\n")
        
        # Test 1: Prompt simple
        print("Test 1: Prompt simple")
        res = cli.ejecutar_prompt("Dame el resultado de 5 + 7")
        if res['success']:
            print(f"[OK] Respuesta: {res['respuesta']}\n")
        else:
            print(f"[ERROR] Error: {res['error']}\n")
        
        # Test 2: JSON
        print("Test 2: Respuesta JSON")
        res = cli.ejecutar_con_json("""
Retorna un array JSON con 2 objetos de prueba.
Formato: [{"nombre": "Test1", "valor": 1}, {"nombre": "Test2", "valor": 2}]
Retorna SOLO el array, sin explicaciones.
        """)
        
        if res['success'] and res['respuesta_parseada']:
            print(f"[OK] JSON parseado correctamente:")
            print(f"   Tipo: {type(res['json']).__name__}")
            print(f"   Contenido: {res['json']}\n")
        else:
            print(f"[ERROR] Error: {res.get('error', 'Unknown')}\n")
            if 'respuesta' in res:
                print(f"   Respuesta raw: {res['respuesta'][:200]}\n")
        
        print("=== Tests completados ===")
        
    except RuntimeError as e:
        print(f"❌ Error de configuración: {e}")
        print("\nSolución:")
        print("  npm install -g @google/generative-ai-cli")
        print("  gemini setup")