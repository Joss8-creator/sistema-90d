# 🚀 Sistema 90D - Contexto del Proyecto

Este proyecto es un "Centro de Comando para Solopreneurs" diseñado para validar ideas y construir proyectos rentables siguiendo la metodología de ciclos de 90 días.

## 🛠️ Tecnologías Principales

- **Lenguaje:** Python 3.11+ (Cero dependencias externas para el núcleo).
- **Servidor Web:** `http.server` (Python stdlib).
- **Base de Datos:** SQLite con modo WAL y claves foráneas habilitadas.
- **Frontend:** HTML5, CSS3 (Vanilla), y HTMX (para interactividad ligera).
- **IA:** Integración opcional con **Gemini CLI** para análisis y generación de ideas.

## 🏗️ Arquitectura y Estructura

El proyecto sigue una arquitectura monolítica minimalista centrada en la eficiencia:

- `app.py`: Punto de entrada principal y lógica del servidor HTTP.
- `database.py`: Gestión de la persistencia con SQLite sin ORM.
- `dashboard_data.py`: Procesamiento de métricas para la visualización del dashboard.
- `gemini_integration.py`: Wrapper robusto para interactuar con Gemini CLI.
- `templates/`: Sistema de plantillas personalizado que soporta variables, bucles, condicionales e inclusiones.
- `static/`: Archivos CSS estáticos.
- `data/`: Directorio que contiene la base de datos `sistema.db` y backups.

## 🚀 Comandos Clave

### Ejecución
- **Iniciar servidor:** `python app.py` (Disponible en `http://localhost:8080`)
- **Configurar IA (Opcional):** `pip install gemini-cli` y luego `gemini setup`.

### Testing
Existen varios scripts de prueba para verificar la robustez del sistema:
- `python test_sistema.py` (Test general)
- `python test_dashboard.py`
- `python test_decisiones.py`
- `python test_robustez.py`

## 📏 Convenciones de Desarrollo

1. **Zero Dependencies:** No añadir librerías externas a menos que sea estrictamente necesario para funciones opcionales. Todo el núcleo debe funcionar con la librería estándar de Python.
2. **Eficiencia:** El código debe ser ligero. Las consultas SQL son directas para evitar el overhead de un ORM.
3. **Validación:** Usar `validadores.py` para asegurar la integridad de los datos antes de insertarlos en la BD.
4. **Logging:** Utilizar el logger configurado en `logger_config.py` en lugar de `print` para trazabilidad.
5. **Templates:** El motor de plantillas en `app.py` procesa etiquetas como `{{ var }}`, `{% for ... %}`, `{% if ... %}` y `{% include '...' %}`.

## 🤖 Integración con Gemini

El sistema utiliza Gemini CLI para:
- **Análisis Semanal:** Evalúa métricas y sugiere decisiones (Kill/Iterate/Winner).
- **Generador de Ideas:** Sugiere nuevos proyectos basados en el contexto actual del usuario.

Los prompts se gestionan a través de `prompt_generator.py` y se ejecutan mediante `gemini_integration.py`.
