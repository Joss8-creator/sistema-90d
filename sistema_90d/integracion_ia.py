#!/usr/bin/env python3
"""
integracion_ia.py - Integración opcional con APIs de LLMs (Anthropic/OpenAI)
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/integracion_ia.py
"""

import os
import json
from typing import Dict, Optional
import prompt_generator as pg

# Intentar importar SDKs (opcionales)
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class IntegradorIA:
    """
    Capa de abstracción que OPCIONALMENTE llama APIs.
    Si no hay API key configurada o SDK instalado, retorna modo manual.
    """
    
    def __init__(self):
        self.api_key_anthropic = os.getenv('CLAUDE_API_KEY')
        self.api_key_openai = os.getenv('OPENAI_API_KEY')
        self.proveedor = self._detectar_proveedor()
    
    def _detectar_proveedor(self) -> str:
        """Determina qué proveedor usar basado en disponibilidad y configuración."""
        if self.api_key_anthropic and HAS_ANTHROPIC:
            return 'anthropic'
        elif self.api_key_openai and HAS_OPENAI:
            return 'openai'
        return 'manual'

    def analizar_automaticamente(self) -> Dict:
        """
        Ejecuta análisis. Si hay API key y SDK, llama automáticamente.
        Si no, indica que se debe hacer manualmente.
        """
        prompt = pg.generar_prompt_analisis()
        
        if self.proveedor == 'manual':
            return {
                'modo': 'manual',
                'prompt': prompt,
                'mensaje': 'No se detectó API Key o SDK instalado. Usa el modo copy/paste.'
            }
        
        try:
            if self.proveedor == 'anthropic':
                return self._llamar_anthropic(prompt)
            elif self.proveedor == 'openai':
                return self._llamar_openai(prompt)
        except Exception as e:
            return {
                'modo': 'error',
                'mensaje': f'Error al llamar a la API de {self.proveedor}: {str(e)}',
                'prompt': prompt
            }
        
        return {'modo': 'manual', 'prompt': prompt}

    def _llamar_anthropic(self, prompt: str) -> Dict:
        """Llama a la API de Claude."""
        client = anthropic.Anthropic(api_key=self.api_key_anthropic)
        
        # Usamos un modelo balanceado para análisis estratégico
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        texto_respuesta = response.content[0].text
        return self._procesar_respuesta_ia(texto_respuesta, 'anthropic')

    def _llamar_openai(self, prompt: str) -> Dict:
        """Llama a la API de OpenAI."""
        client = OpenAI(api_key=self.api_key_openai)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" } if "JSON" in prompt.upper() or "YAML" in prompt.upper() else None
        )
        
        texto_respuesta = response.choices[0].message.content
        return self._procesar_respuesta_ia(texto_respuesta, 'openai')

    def _procesar_respuesta_ia(self, texto: str, proveedor: str) -> Dict:
        """Limpia y estructura la respuesta de la IA."""
        # Tenta extraer JSON si la IA lo envió entre bloques
        json_limpio = texto
        if '```json' in texto:
            json_limpio = texto.split('```json')[1].split('```')[0].strip()
        elif '```' in texto:
            json_limpio = texto.split('```')[1].split('```')[0].strip()
            
        try:
            # Intentar parsear como JSON si el formato parece JSON
            if json_limpio.strip().startswith('{') or json_limpio.strip().startswith('['):
                datos = json.loads(json_limpio)
                return {
                    'modo': 'automatico',
                    'proveedor': proveedor,
                    'datos': datos,
                    'texto_completo': texto
                }
        except:
            pass
            
        return {
            'modo': 'automatico',
            'proveedor': proveedor,
            'texto_completo': texto,
            'mensaje': 'Respuesta recibida pero no se pudo parsear como JSON estructurado.'
        }
