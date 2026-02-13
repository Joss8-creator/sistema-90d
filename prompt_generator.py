#!/usr/bin/env python3
"""
prompt_generator.py - Generador de prompts para análisis con IA externa
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/prompt_generator.py

Genera prompts estructurados en formato Markdown que el usuario puede copiar/pegar
en su IA preferida (ChatGPT, Claude, etc.) para obtener análisis estratégico.
"""

from datetime import date
from typing import Dict, List
import database as db


def generar_prompt_analisis(formato_json: bool = False) -> str:
    """
    Generar prompt completo de análisis semanal del Sistema 90D.
    
    Args:
        formato_json: Si es True, solicita la respuesta estrictamente en JSON.
    
    Returns:
        str: Contenido markdown o estructurado para IA
    """
    # ... (código existente hasta la construcción del prompt) ...
    # Obtener datos del sistema
    ciclo = db.obtener_ciclo_activo()
    if not ciclo:
        return "⚠️ ERROR: No hay ciclo 90D activo. Ejecuta `python database.py` para crear uno."
    
    fase = db.calcular_fase_actual(ciclo)
    proyectos = db.obtener_todos_proyectos_con_metricas()
    
    # NUEVO: Obtener decisiones rechazadas recientemente
    rechazadas = db.obtener_decisiones_rechazadas_recientes(30)
    
    # Construir prompt
    prompt = f"# ANÁLISIS SISTEMA 90D - {date.today().isoformat()}\n\n"
    prompt += "## CONTEXTO DEL CICLO\n"
    prompt += f"- Día actual: {fase['dia']}/90\n"
    prompt += f"- Fase: {fase['nombre']}\n"
    prompt += f"- Días restantes: {fase['dias_restantes']}\n"
    prompt += f"- Fecha inicio ciclo: {ciclo['fecha_inicio']}\n\n" # Added this line back from original
    
    if rechazadas:
        prompt += "## CONTEXTO ESTRATÉGICO: DECISIONES RECHAZADAS RECIENTEMENTE\n"
        prompt += "IMPORTANTE: El usuario ha rechazado previamente estas sugerencias. NO vuelvas a proponer la misma decisión a menos que haya un cambio drástico en las métricas.\n\n"
        for r in rechazadas:
            prompt += f"- **{r['proyecto_nombre']}**: Recomendación de {r['tipo'].upper()} rechazada.\n"
            prompt += f"  - Razón del rechazo: {r['razon_rechazo']}\n"
            prompt += f"  - Fecha: {r['fecha']}\n"
        prompt += "\n"
    
    prompt += "### Tareas sugeridas para esta fase:\n"
    
    for i, tarea in enumerate(fase['tareas_sugeridas'], 1):
        prompt += f"{i}. {tarea}\n"
    
    prompt += "\n---\n\n## PROYECTOS REGISTRADOS\n\n"
    
    if not proyectos:
        prompt += "_No hay proyectos registrados aún._\n\n"
    else:
        for i, p in enumerate(proyectos, 1):
            prompt += f"### {i}. {p['nombre']}\n\n"
            prompt += f"- **Hipótesis**: {p['hipotesis']}\n"
            prompt += f"- **Estado**: `{p['estado']}`\n"
            prompt += f"- **Fecha inicio**: {p['fecha_inicio']}\n"
            prompt += f"- **Métricas consolidadas**:\n"
            prompt += f"  - Ingresos totales: ${p['total_ingresos']:.2f}\n"
            prompt += f"  - Tiempo invertido: {p['total_tiempo']:.1f} horas\n"
            prompt += f"  - ROI: ${p['roi']:.2f}/hora\n"
            prompt += f"  - Conversiones totales: {p['total_conversiones']}\n"
            prompt += f"  - Registros de métricas: {p['num_metricas']}\n"
            
            if p['ultima_metrica']:
                prompt += f"  - Última actividad: {p['ultima_metrica']}\n"
            else:
                prompt += f"  - ⚠️ Sin métricas registradas\n"
            
            prompt += "\n"
    
    # ... (código previo)
    
    if formato_json:
        prompt += """---

## PROMPT PARA IA (FORMATO AUTOMÁTICO)

Actúa como analista estratégico del Sistema 90D. Analiza los datos proporcionados y genera una respuesta ESTRICTAMENTE en formato JSON.

FORMATO JSON ESPERADO:
{
  "resumen_ejecutivo": "Resumen breve de la situación actual",
  "proyectos": [
    {
      "id": [ID numérico],
      "nombre": "[Nombre]",
      "decision": "kill|iterate|winner",
      "justificacion": "Basada en métricas",
      "acciones": ["acción 1", "acción 2"],
      "riesgos": ["riesgo 1"]
    }
  ],
  "riesgos_detectados": ["riesgo global 1"]
}

IMPORTANTE: Responde ÚNICAMENTE con el objeto JSON. Sin texto antes ni después.
"""
    else:
        prompt += """---

## PROMPT PARA IA

Actúa como **analista estratégico** siguiendo las reglas del **Documento Base del Sistema 90D**.

### Tu tarea:

1. **Analizar cada proyecto** según métricas objetivas, NO intuición
2. **Clasificar** cada uno como:
   - ❌ **KILL**: Cancelar sin remordimiento
   - 🔁 **ITERATE**: Ajustar hipótesis y continuar experimentando
   - 🚀 **WINNER**: Doblar apuesta y escalar
3. **Justificar** cada decisión con datos específicos
4. **Identificar riesgos**:
   - Dependencias peligrosas (un solo canal, un cliente, etc.)
   - Métricas infladas sin monetización real
   - Uso artificial (solo amigos/curiosos)
   - Falta de datos críticos
5. **Sugerir acciones concretas** para la próxima semana

### Reglas obligatorias:

- ✅ Basar decisiones en métricas reales
- ✅ Señalar falta de datos críticos
- ✅ Priorizar velocidad de decisión
- ❌ NO inventar métricas
- ❌ NO asumir validación sin evidencia
- ❌ NO proponer "darle más tiempo" sin umbral concreto
- ❌ NO usar discurso motivacional

### Formato de respuesta esperado:

```yaml
proyectos:
  - nombre: [Nombre del proyecto]
    decision: [kill|iterate|winner]
    justificacion: |
      [Explicación basada en métricas específicas]
    acciones_proxima_semana:
      - [Acción concreta 1]
      - [Acción concreta 2]
    riesgos_detectados:
      - [Riesgo 1]
      - [Riesgo 2]
    metricas_faltantes:
      - [Dato que se necesita medir]

resumen_general:
  proyectos_kill: [número]
  proyectos_iterate: [número]
  proyectos_winner: [número]
  recomendacion_principal: |
    [Consejo estratégico más importante para esta semana]
```

---

**IMPORTANTE**: Sé brutalmente honesto. El objetivo es **decidir mejor y más rápido**, no sentirse ocupado.
"""
    
    return prompt


def guardar_prompt_archivo(contenido: str, ruta: str = None) -> str:
    """
    Guardar prompt en archivo .md para fácil acceso.
    
    Args:
        contenido: Contenido del prompt
        ruta: Ruta del archivo (None = generar automáticamente)
    
    Returns:
        str: Ruta del archivo guardado
    """
    if ruta is None:
        fecha = date.today().isoformat()
        ruta = f"data/analisis_{fecha}.md"
    
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    return ruta


def generar_prompt_proyecto_individual(proyecto_id: int) -> str:
    """
    Generar prompt de análisis para un proyecto específico.
    Útil para análisis profundo de un solo proyecto.
    
    Args:
        proyecto_id: ID del proyecto
    
    Returns:
        str: Prompt markdown específico del proyecto
    """
    proyecto = db.obtener_proyecto(proyecto_id)
    if not proyecto:
        return f"⚠️ ERROR: Proyecto {proyecto_id} no encontrado."
    
    metricas = db.obtener_metricas_proyecto(proyecto_id)
    dashboard = db.calcular_dashboard_proyecto(proyecto_id)
    
    prompt = f"""# ANÁLISIS PROFUNDO: {proyecto['nombre']}

## INFORMACIÓN DEL PROYECTO

- **Hipótesis original**: {proyecto['hipotesis']}
- **Fecha inicio**: {proyecto['fecha_inicio']}
- **Estado actual**: `{proyecto['estado']}`

## MÉTRICAS CONSOLIDADAS

- **Ingresos totales**: ${dashboard['total_ingresos']:.2f}
- **Tiempo invertido**: {dashboard['total_tiempo']:.1f} horas
- **ROI**: ${dashboard['roi']:.2f}/hora
- **Conversiones totales**: {dashboard['total_conversiones']}
- **Registros de métricas**: {dashboard['num_metricas']}

## HISTORIAL DE MÉTRICAS

"""
    
    if not metricas:
        prompt += "_No hay métricas registradas para este proyecto._\n\n"
    else:
        prompt += "| Fecha | Ingresos | Tiempo (h) | Conversiones | Notas |\n"
        prompt += "|-------|----------|------------|--------------|-------|\n"
        
        for m in metricas:
            notas = m['notas'] if m['notas'] else '-'
            prompt += f"| {m['fecha']} | ${m['ingresos']:.2f} | {m['tiempo_horas']:.1f} | {m['conversiones']} | {notas} |\n"
        
        prompt += "\n"
    
    prompt += """---

## PROMPT PARA IA

Analiza este proyecto en profundidad según las reglas del Sistema 90D.

### Preguntas clave a responder:

1. **Validación de hipótesis**: ¿Los datos confirman o refutan la hipótesis original?
2. **Tracción real**: ¿Hay evidencia de demanda genuina o solo curiosidad?
3. **Tendencia**: ¿Las métricas mejoran, empeoran o están estancadas?
4. **Eficiencia**: ¿El ROI justifica continuar invirtiendo tiempo?
5. **Riesgos**: ¿Qué dependencias peligrosas existen?

### Tu análisis debe incluir:

- **Decisión**: ❌ KILL | 🔁 ITERATE | 🚀 WINNER
- **Justificación**: Basada en datos específicos del historial
- **Acciones concretas**: Qué hacer en los próximos 7 días
- **Métricas a vigilar**: Qué medir para la próxima decisión
- **Umbral de decisión**: Qué número/evento dispararía kill o scale

**Formato esperado**: Respuesta estructurada en YAML o JSON.
"""
    
    return prompt


if __name__ == '__main__':
    """
    Script de prueba: generar prompt y guardarlo.
    """
    print("Generando prompt de análisis semanal...\n")
    
    prompt = generar_prompt_analisis()
    print(prompt)
    
    print("\n" + "="*80)
    print("GUARDANDO ARCHIVO...")
    
    ruta = guardar_prompt_archivo(prompt)
    print(f"\n[OK] Prompt guardado en: {ruta}")
    print("\nPuedes copiar el contenido y pegarlo en tu IA preferida.")
