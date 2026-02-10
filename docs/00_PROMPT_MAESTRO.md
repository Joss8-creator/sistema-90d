# PROMPT MAESTRO: Sistema Operativo de Emprendimiento 90D

## CONTEXTO INMUTABLE
Lee primero: `Documento_Base.md` — Es la ley del sistema.

## OBJETIVO
Diseñar e implementar un **sistema local mínimo viable** que ejecute la metodología 90D optimizada de Marc Lou para solopreneurs técnicos.

## RESTRICCIONES TÉCNICAS NO NEGOCIABLES
1. **Stack tecnológico**:
   - Backend: Python 3.11+ (stdlib + SQLite, cero frameworks pesados)
   - Frontend: HTML/CSS/JS vanilla + htmx (cero React/Vue/Angular)
   - Persistencia: SQLite (archivo único `.db`)
   - Deployment: Ejecutable local vía `python app.py` → http://localhost:8080

2. **Arquitectura de IA**:
   - NO integración API directa con LLMs
   - Sistema de **prompts exportables** (archivos `.md` editables)
   - Usuario copia/pega entre sistema y su IA preferida
   - IA retorna respuestas estructuradas (JSON/YAML) que el sistema parsea

3. **Eficiencia extrema**:
   - Aplicar **PROTOCOLO DE EFICIENCIA EXTREMA** del usuario
   - Justificar cada dependencia vs alternativa más ligera
   - Priorizar: rendimiento > comodidad de desarrollo

## ORDEN DE EJECUCIÓN
Completar sub-prompts en este orden estricto:

1. **docs/01_MVP_CORE.md** → Definir lo mínimo funcional (7 días max)
2. **docs/02_MODELO_DATOS.md** → Esquema SQLite con reglas de decisión
3. **docs/03_INTERFAZ_USUARIO.md** → UI básica (formularios + dashboards)
4. **docs/04_MOTOR_METRICAS.md** → Captura y análisis automatizado
5. **docs/05_SISTEMA_IA.md** → Generación de prompts intercambiables
6. **docs/06_FLUJOS_DIARIOS.md** → Rituales operativos del usuario
7. **docs/07_PLAN_IMPLEMENTACION.md** → Roadmap técnico de construcción

## CRITERIOS DE ÉXITO
- [ ] Usuario puede registrar una idea en <2 minutos
- [ ] Sistema sugiere kill/iterate/scale con datos, no intuición
- [ ] Detecta dependencias peligrosas (un canal, un cliente, etc.)
- [ ] Exporta prompt de análisis semanal listo para copiar/pegar
- [ ] Ejecutable en <128MB RAM con base de datos de 100 proyectos

## ANTI-PATRONES PROHIBIDOS
- ❌ Sugerir frameworks (Django, Flask, FastAPI)
- ❌ Usar npm/Node.js para cualquier cosa
- ❌ ORM automáticos (SQLAlchemy, etc.)
- ❌ Dashboards con bibliotecas de gráficos pesadas (Chart.js → usar SVG directo)
- ❌ Abstracciones prematuras ("para escalar luego")

## FORMATO DE ENTREGA PARA CADA SUB-PROMPT
Cada respuesta debe incluir:
1. **Código funcional** con rutas completas como comentarios
2. **Justificación de decisiones** técnicas vs alternativas
3. **Complejidad temporal/espacial** (solo si es relevante)
4. **Comparativa vs "solución moderna estándar"** (y por qué se descartó)
5. **Optimizaciones consideradas pero no aplicadas** (con razón)

---

**Próximo paso**: Ejecutar `01_MVP_CORE.md`
