# SUB-PROMPT 01: MVP CORE (Mínimo Viable Producto)

## CONTEXTO
Sistema local para solopreneur técnico ejecutando metodología 90D.
Stack: Python stdlib + SQLite + HTML/htmx.

## OBJETIVO
Definir el **núcleo absoluto mínimo** que permite empezar a usar el sistema hoy.
Si no está en esta lista, NO se implementa en el MVP.

## FUNCIONALIDADES CORE (PRIORIZADAS)

### 1. Registro de Ideas/Proyectos (P0 - Crítico)
**Qué hace:**
- Usuario registra: Nombre, Hipótesis, Fecha inicio, Estado inicial
- Estados posibles: `idea | mvp | active | paused | killed | winner`

**Por qué es P0:**
Sin esto, no hay sistema. Todo lo demás depende de tener proyectos registrados.

**Interfaz mínima:**
- Formulario con 4 campos
- Botón "Guardar"
- Lista de proyectos (tabla HTML sin JS)

---

### 2. Registro Manual de Métricas (P0 - Crítico)
**Qué hace:**
- Usuario ingresa: Fecha, Ingresos, Tiempo invertido (horas), Conversiones
- Se asocia a un proyecto existente

**Por qué es P0:**
Sin métricas, no hay decisiones. Es la diferencia entre opinión y dato.

**Interfaz mínima:**
- Formulario con 4 campos + selector de proyecto
- Tabla histórica de métricas por proyecto

---

### 3. Visor de Fase Actual (P0 - Crítico)
**Qué hace:**
- Calcula qué día del ciclo 90D está el usuario
- Muestra fase actual: Exploración | Experimentación | Decisión | Consolidación
- Lista de tareas sugeridas para esa fase (hardcoded al inicio)

**Por qué es P0:**
El sistema 90D no funciona si el usuario no sabe en qué fase está.

**Interfaz mínima:**
- Banner superior con: "Día 23/90 - Fase: Experimentación"
- Lista estática de 3-5 tareas típicas de esa fase

---

### 4. Dashboard Básico de Proyecto (P1 - Importante)
**Qué hace:**
- Por cada proyecto, muestra:
  - Ingresos totales
  - Tiempo total invertido
  - ROI básico (ingresos / tiempo estimado en $)
  - Última métrica registrada

**Por qué es P1:**
Permite comparar proyectos sin análisis complejo. Se puede lanzar sin esto, pero pierde valor rápido.

**Interfaz mínima:**
- Tabla con columnas calculadas desde SQLite
- Sin gráficos (texto/números solamente)

---

### 5. Exportador de Prompt IA (P1 - Importante)
**Qué hace:**
- Botón "Generar Análisis Semanal"
- Genera archivo `.md` con:
  ```
  CONTEXTO DEL SISTEMA 90D
  ========================
  Día: X/90
  Fase actual: [Fase]
  
  PROYECTOS ACTIVOS
  ==================
  1. [Nombre]: $X ingresos, Y horas, Estado: [Estado]
  2. ...
  
  PROMPT PARA IA
  ==============
  Analiza estos datos según las reglas del Documento Base.
  Recomienda: kill, iterate o scale para cada proyecto.
  Justifica con métricas, no intuición.
  ```

**Por qué es P1:**
Es el puente con la IA sin acoplarse a ninguna API. Usuario copia/pega manual.

**Interfaz mínima:**
- Botón que genera archivo descargable
- Textarea con preview del prompt generado

---

## FUNCIONALIDADES EXCLUIDAS DEL MVP (EXPLÍCITAMENTE)

### Automatización de métricas
**Por qué NO:** Requiere integraciones (Stripe, analytics) que agregan complejidad. 
**Cuándo sí:** Fase 2, solo si el MVP demuestra uso consistente.

### Gráficos interactivos
**Por qué NO:** Bibliotecas pesadas (Chart.js = 200KB min). SVG estático es suficiente.
**Cuándo sí:** Nunca. Si se necesita visualización, generar SVG server-side.

### Sistema de tareas/TODOs
**Por qué NO:** Ya existen herramientas mejores (Notion, Todoist). No competir.
**Cuándo sí:** Solo si se demuestra que la integración de tareas con métricas es crítica.

### Multi-usuario / Sync cloud
**Por qué NO:** Solopreneur = 1 usuario. Complejidad innecesaria.
**Cuándo sí:** Nunca en este sistema. Es un constraint de diseño.

### Alertas automáticas
**Por qué NO:** Requieren proceso en background. Complejidad prematura.
**Cuándo sí:** Fase 3, si usuario demuestra disciplina con análisis manual.

---

## ESPECIFICACIÓN TÉCNICA MÍNIMA

### Arquitectura
```
/sistema_90d
  /app.py              # Servidor HTTP básico (stdlib.http.server)
  /database.py         # Wrapper SQLite con queries directas
  /static
    /style.css         # Estilos mínimos (<5KB)
  /templates
    /index.html        # Dashboard principal
    /proyecto.html     # Vista de proyecto individual
  /data
    /sistema.db        # Base de datos SQLite
```

### Stack justificado
- **Python stdlib.http.server**: 0 dependencias. Suficiente para localhost.
  - Alternativa descartada: Flask (5MB de dependencias para servir HTML)
- **SQLite**: Archivo único, cero configuración, <500KB overhead.
  - Alternativa descartada: PostgreSQL (servidor externo, overkill)
- **HTML + htmx**: Interactividad sin JS complejo. htmx = 14KB.
  - Alternativa descartada: React (3MB min bundle)

### Complejidad esperada
- Inserciones: O(1) por registro de métrica
- Consultas dashboard: O(n) donde n = proyectos activos (asumido <20)
- Generación de prompts: O(n) lectura lineal de métricas

---

## CRITERIOS DE ACEPTACIÓN MVP

- [ ] Proyecto registrado en <2 minutos
- [ ] Métrica ingresada en <1 minuto
- [ ] Dashboard carga en <100ms con 10 proyectos y 100 métricas
- [ ] Prompt exportado en <5 segundos
- [ ] Ejecutable en cualquier máquina con Python 3.11+
- [ ] Cero setup salvo `python app.py`

---

## ENTREGABLE ESPERADO

1. **Esquema de base de datos** (tablas, campos, relaciones)
2. **Código de app.py** con rutas HTTP básicas
3. **HTML de formularios** (sin CSS por ahora)
4. **Función de generación de prompts** con ejemplo de output

**Formato:** Código funcional con comentarios de ruta completa.

**Siguiente paso:** Si apruebas este MVP, ejecutar `02_MODELO_DATOS.md`
