# 🚀 GEMINI.md - Sistema 90D

Este archivo proporciona contexto estratégico e instrucciones técnicas para trabajar en el proyecto **Sistema 90D**, un centro de comando para solopreneurs basado en la metodología de ciclos de 90 días.

## 📌 Visión General del Proyecto
- **Propósito**: Validar ideas de negocio, registrar métricas y tomar decisiones estratégicas (Kill, Iterate, Winner) basadas en datos y análisis de IA.
- **Filosofía**: **Zero Dependencies**. El proyecto utiliza exclusivamente la librería estándar de Python 3.11+ para garantizar máxima portabilidad, velocidad y facilidad de mantenimiento.
- **Arquitectura**:
  - **Backend**: Servidor HTTP minimalista basado en `http.server`.
  - **Base de Datos**: SQLite con transacciones ACID, modo WAL y claves foráneas habilitadas.
  - **Frontend**: HTML vanilla con **HTMX** para interactividad y un motor de plantillas personalizado definido en `app.py`.
  - **IA**: Generador de prompts estructurados para análisis externo (ChatGPT/Claude) e integración opcional vía API.

## 🛠️ Comandos Clave

### Ejecución y Desarrollo
- **Iniciar Servidor**: `python app.py` (Disponible en `http://localhost:8080`)
- **Inicializar BD**: Se realiza automáticamente al arrancar `app.py`, pero puede forzarse con `python database.py`.
- **Exportar Datos**: 
  - CSV: `curl http://localhost:8080/exportar-csv > datos.csv`
  - Prompt IA: `curl http://localhost:8080/exportar-prompt > prompt.md`

### Testing
El proyecto cuenta con múltiples suites de test para validar la robustez:
- `python test_sistema.py` (Test general y generador de datos de prueba)
- `python test_dashboard.py` (Validación de lógica de negocio del dashboard)
- `python test_decisiones.py` (Lógica de clasificación de proyectos)
- `python test_robustez.py` (Pruebas de carga y manejo de errores)

## 📐 Convenciones de Desarrollo

### 1. Cero Dependencias Externas
- **REGLA DE ORO**: No añadir librerías al `requirements.txt`. Cualquier funcionalidad debe implementarse usando `stdlib` de Python.
- Las dependencias opcionales (ej. para APIs de IA externas) van en `requirements-optional.txt`.

### 2. Motor de Plantillas Personalizado
Ubicado en `app.py`, soporta la siguiente sintaxis:
- **Variables**: `{{ variable.atributo }}`
- **Condicionales**: `{% if condicion %} ... {% endif %}`
- **Bucles**: `{% for item in lista %} ... {% endfor %}`
- **Includes**: `{% include 'componente.html' %}`

### 3. Gestión de Base de Datos
- Usar siempre el context manager `transaccion_segura()` de `database.py` para operaciones de escritura.
- Las consultas complejas deben preferirse en vistas (ej. `v_resumen_proyectos`).
- Seguir el patrón de **Optimistic Locking** usando la columna `version` en la tabla `proyectos`.

### 4. Estilo de Código
- Documentar funciones críticas (docstrings).
- Usar `logger_app` y `logger_db` para el registro de eventos y errores.
- Las validaciones de entrada deben residir en `validadores.py`.

## 📂 Estructura Crítica
- `app.py`: Punto de entrada, routing y motor de renderizado.
- `database.py`: Esquema y operaciones CRUD core.
- `dashboard_data.py`: Lógica de agregación para la interfaz de usuario.
- `prompt_generator.py`: Ingeniería de prompts para el análisis estratégico.
- `guia.py`: Lógica de fases del ciclo (Exploración, Experimentación, Decisión, Consolidación).
- `templates/`: Plantillas HTML y componentes reutilizables.
- `data/`: Contiene `sistema.db` y backups automáticos.

## 🎯 Metodología de Ciclos 90D
El sistema opera bajo 4 fases automáticas basadas en el día del ciclo:
1. **Exploración (Días 1-14)**: Foco en hipótesis y diseño de experimentos.
2. **Experimentación (Días 15-45)**: Lanzamiento de MVPs y captura de tracción.
3. **Decisión (Días 46-75)**: Clasificación crítica de proyectos.
4. **Consolidación (Días 76-90)**: Escalamiento de "Winners" y cierre de ciclo.
