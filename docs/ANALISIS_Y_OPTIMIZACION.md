# ANÁLISIS Y OPTIMIZACIÓN DEL PROMPT ORIGINAL

## RESUMEN EJECUTIVO

Tu prompt original buscaba diseñar un "software local con IA" para ejecutar un programa de emprendimiento de 90 días. Sin embargo, contenía **ambigüedades técnicas críticas** que impedirían su realización directa.

He **reescrito completamente el prompt**, dividiéndolo en **7 sub-prompts ejecutables** que llevan desde el concepto hasta código funcional en 7-10 días.

---

## PROBLEMAS DETECTADOS EN EL PROMPT ORIGINAL

### 1. Abstracción IA mal definida ❌
**Original:** "El sistema debe usar documentos de comandos para comunicarse con distintas IAs"
- ¿Cómo se ejecutan estos "documentos de comandos"?
- ¿Son archivos que el usuario copia/pega manualmente?
- ¿O hay integración API automática?

**Solución aplicada:** Sistema de copy/paste con prompts generados automáticamente. Usuario controla qué IA usa (ChatGPT, Claude, Llama local, etc.) sin acoplamiento técnico.

---

### 2. Stack tecnológico no especificado ❌
**Original:** "Software 100% local (desktop o local web)"
- ¿Python? ¿Electron? ¿Java?
- ¿Base de datos: SQLite, PostgreSQL, archivos JSON?
- ¿Framework: Flask, FastAPI, ninguno?

**Solución aplicada:**
- **Backend:** Python stdlib + servidor HTTP básico (cero frameworks pesados)
- **DB:** SQLite (archivo único, cero configuración)
- **Frontend:** HTML + htmx (14KB total, sin React/Vue)
- **Justificación:** Cumple con tu PROTOCOLO DE EFICIENCIA EXTREMA

---

### 3. Sobrecarga de features sin priorización ❌
**Original:** Motor de métricas + IA + build-in-public mitigation + múltiples dashboards
- No define MVP vs nice-to-have
- Sin roadmap de implementación
- Riesgo de feature creep y nunca terminar

**Solución aplicada:**
- **MVP Core (Días 1-3):** Solo registro de proyectos + métricas + dashboard básico
- **Fase 2 (Días 4-5):** Motor de análisis con 2 reglas simples
- **Fase 3 (Días 6-7):** Integración IA via copy/paste
- **Resto:** Post-MVP opcional

---

### 4. Confusión entre sistema y metodología ❌
**Original:** Mezcla especificación de software con explicación de la metodología Marc Lou
- El 40% del prompt explica la metodología (debilidades, fortalezas)
- Solo el 30% define requerimientos técnicos concretos

**Solución aplicada:**
- **Documento_Base.txt** contiene la metodología (es input, no output)
- Los sub-prompts se enfocan 100% en especificación técnica
- Sistema embebe Documento_Base en prompts generados para IA

---

### 5. Métricas sin instrumentación ❌
**Original:** "El sistema debe incluir: Ingresos, Conversión, Churn, Esfuerzo de soporte"
- No define cómo se capturan automáticamente
- Asume integraciones (Stripe, Analytics) sin especificarlas

**Solución aplicada:**
- **MVP:** Registro manual de métricas (formulario simple)
- **Post-MVP:** Webhooks opcionales de Stripe/GA
- **Razón:** Automatización requiere APIs externas → complejidad prematura

---

## CÓMO HE OPTIMIZADO EL PROMPT

### Estrategia aplicada: División en capas ejecutables

```
Documento_Base.txt (metodología)
    ↓
00_PROMPT_MAESTRO.md (orquestador)
    ↓
01_MVP_CORE.md → Define lo mínimo funcional
    ↓
02_MODELO_DATOS.md → Schema SQLite + reglas
    ↓
03_INTERFAZ_USUARIO.md → HTML/CSS minimalista
    ↓
04_MOTOR_METRICAS.md → Análisis automatizado
    ↓
05_SISTEMA_IA.md → Generación de prompts
    ↓
06_FLUJOS_DIARIOS.md → Rituales operativos
    ↓
07_PLAN_IMPLEMENTACION.md → Roadmap técnico
```

Cada sub-prompt es **autocontenido** y **ejecutable por separado**.

---

## CAMBIOS CRÍTICOS APLICADOS

### ❌ ELIMINADO del prompt original

1. **"Abstracción de IA" vaga**
   - Reemplazado por: Sistema de templates Jinja2 + copy/paste manual
   - Razón: "Abstracción" sin definir cómo se ejecuta no es implementable

2. **"Minimización de debilidades de Marc Lou" genérica**
   - Reemplazado por: Reglas concretas en motor de métricas
   - Ejemplo: Trigger SQL que alerta si >80% ingresos en un proyecto

3. **"Software 100% local"**
   - Reemplazado por: Especificación técnica exacta (Python + SQLite + HTTP server)
   - Razón: "Local" puede ser Electron (500MB) o Python (50MB). Enorme diferencia.

4. **"Múltiples IAs sin casarse con una"**
   - Reemplazado por: Prompts exportables en .txt
   - Razón: Integrar múltiples APIs (OpenAI + Anthropic + Google) es complejidad innecesaria

---

### ✅ AGREGADO que faltaba

1. **Modelo de datos completo**
   - Tablas, índices, triggers, vistas SQL
   - Constraints para evitar estados inválidos
   - Justificación de cada decisión técnica

2. **Flujos operativos diarios**
   - Ritual diario (<10 min)
   - Ritual semanal (15-30 min)
   - Rituales de transición de fase
   - **Crítico:** Sin esto, el sistema no se usa consistentemente

3. **Plan de implementación con tiempos**
   - Día 1: DB + servidor
   - Día 2: Templates
   - Día 3: Renderizado dinámico
   - ...
   - Día 7: MVP completo

4. **Criterios de aceptación medibles**
   - ✅ Dashboard carga en <100ms
   - ✅ Sistema usa <128MB RAM
   - ✅ Proyecto registrado en <2 minutos

---

## COMPARATIVA: PROMPT ORIGINAL vs OPTIMIZADO

| Aspecto | Original | Optimizado |
|---------|----------|------------|
| **Claridad técnica** | Ambigua ("software local", "IA abstracta") | Exacta (Python + SQLite + htmx) |
| **Ejecutabilidad** | Imposible sin 20+ preguntas de clarificación | Directamente implementable |
| **Scope** | Difuso (todo al mismo tiempo) | Priorizado (MVP en 7 días, resto opcional) |
| **Tamaño** | 150 líneas, 40% metodología, 30% técnico | 7 documentos, 100% técnico |
| **Dependencias** | No especificadas | Explícitas (Jinja2, cero frameworks) |
| **Stack** | No definido | Python stdlib + SQLite + HTML/htmx |
| **Complejidad estimada** | Desconocida | 2500 líneas código, 42-120h desarrollo |

---

## DECISIONES TÉCNICAS CLAVE (SEGÚN TU PROTOCOLO DE EFICIENCIA)

### 1. ¿Por qué NO Flask/FastAPI?
**Alternativa moderna:** Flask (framework web estándar)
- **Overhead:** 5MB dependencias mínimas
- **Complejidad:** ORM (SQLAlchemy), blueprints, extensiones

**Elegido:** http.server (stdlib Python)
- **Overhead:** 0 bytes (viene con Python)
- **Complejidad:** 150 líneas de código para servidor básico
- **Trade-off:** Sin routing automático, pero para 10 rutas es manejable

**Veredicto:** stdlib suficiente para localhost. Flask solo si escalas a multi-usuario (fuera de scope).

---

### 2. ¿Por qué SQLite vs PostgreSQL?
**Alternativa moderna:** PostgreSQL (DB robusta)
- **Overhead:** Servidor externo, configuración, puerto 5432
- **Backup:** dump/restore manual
- **Concurrencia:** Excelente (irrelevante: 1 usuario)

**Elegido:** SQLite
- **Overhead:** Archivo único (<5MB con 100 proyectos)
- **Backup:** `cp sistema.db sistema.backup.db`
- **Concurrencia:** Limitada (irrelevante: solopreneur = 1 usuario)

**Veredicto:** SQLite cumple todos los requisitos. PostgreSQL es overkill.

---

### 3. ¿Por qué templates HTML vs React?
**Alternativa moderna:** React SPA
- **Bundle size:** 500KB mínimo (React + ReactDOM + bundler)
- **Build time:** 10-30 segundos por cambio
- **Dependencias:** 200+ paquetes npm
- **Complejidad:** Webpack/Vite, JSX, state management

**Elegido:** HTML + htmx
- **Bundle size:** 14KB (solo htmx)
- **Build time:** 0 segundos (es HTML puro)
- **Dependencias:** 1 (htmx via CDN)
- **Complejidad:** Request/response HTTP estándar

**Veredicto:** React es overengineering para formularios simples. htmx da 80% de interactividad con 5% de complejidad.

---

## VALIDACIÓN CONTRA EL DOCUMENTO_BASE.TXT

He verificado que el sistema optimizado cumple con **todos** los principios del Documento Base:

✅ **Velocidad > perfección:** MVP en 7 días, no 3 meses  
✅ **Aprendizaje medido:** Motor de métricas fuerza registro de datos  
✅ **Múltiples experimentos:** Límite de 3 proyectos activos simultáneos  
✅ **IA como analista frío:** Prompts obligan a justificar con métricas  
✅ **Sin procesos burocráticos:** Registro de métrica <1 minuto  
✅ **Sin equipos grandes:** Sistema diseñado para 1 usuario  
✅ **Decisiones con umbrales:** Config editable sin tocar código  

---

## PRÓXIMOS PASOS RECOMENDADOS

### Opción A: Ejecutar tú mismo
1. Leer `00_PROMPT_MAESTRO.md`
2. Ejecutar sub-prompts 01-07 en orden
3. Validar cada hito antes de avanzar
4. Tiempo estimado: 7-15 días @ 6h/día

### Opción B: Delegar a otra IA
1. Tomar `01_MVP_CORE.md`
2. Pegarlo en Claude/ChatGPT/Cursor
3. Pedirle: "Implementa este sub-prompt completo con código funcional"
4. Repetir con 02, 03, etc.

### Opción C: Contratar desarrollador
1. Mostrarle `07_PLAN_IMPLEMENTACION.md`
2. Negociar presupuesto basado en 42-60 horas
3. Usar sub-prompts como spec técnica exacta

---

## ARCHIVOS GENERADOS

He creado estos archivos en `/home/claude/`:

```
00_PROMPT_MAESTRO.md          → Coordina todos los sub-prompts
01_MVP_CORE.md                → Define funcionalidades mínimas
02_MODELO_DATOS.md            → Schema completo de base de datos
03_INTERFAZ_USUARIO.md        → HTML/CSS minimalista
04_MOTOR_METRICAS.md          → Reglas de decisión automatizadas
05_SISTEMA_IA.md              → Generación de prompts intercambiables
06_FLUJOS_DIARIOS.md          → Rituales operativos del usuario
07_PLAN_IMPLEMENTACION.md    → Roadmap técnico día por día
```

**Ahora necesito moverlos a `/mnt/user-data/outputs/` para que puedas descargarlos.**

---

## CRÍTICA FINAL AL PROMPT ORIGINAL

Tu prompt era **conceptualmente sólido** pero **técnicamente inexecutable** tal como estaba escrito. Los problemas principales:

1. **Demasiado abstracto:** "IA abstracta", "software local", "comandos intercambiables" no son specs técnicas
2. **Sin priorización:** Todo parecía crítico, nada era MVP
3. **Mezclaba contexto con requerimientos:** 40% del prompt era background de Marc Lou, no specs

**Sin embargo**, la intención era clara: sistema local, eficiente, que integre IA sin acoplarse, y que ejecute metodología 90D.

**Lo que hice:** Conservé la intención, eliminé ambigüedades, agregué especificación técnica exacta, y dividí en bloques ejecutables.

**Resultado:** Ahora tienes un plan que puede implementarse en 7-10 días con código funcional.

---

## PREGUNTA PARA TI

¿Quieres que implemente directamente el **sub-prompt 01 (MVP Core)** con código funcional?

Es decir, ¿genero ahora mismo los archivos `database.py`, `app.py`, `schema.sql`, etc. con código que funcione?

O prefieres primero revisar los sub-prompts y validar que estás de acuerdo con el enfoque antes de que escriba código?
