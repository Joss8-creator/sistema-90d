# 🚀 Sistema 90D - Centro de Comando para Solopreneurs

> Sistema operativo de emprendimiento basado en la metodología Marc Lou optimizada. Valida ideas, construye proyectos rentables y toma decisiones basadas en datos en ciclos de 90 días.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-green.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Características

- ✅ **Gestión de Ciclos 90D** - Inicio manual del ciclo cuando estés listo
- ✅ **Registro de Proyectos** - Hipótesis claras y estados definidos
- ✅ **Captura de Métricas** - Ingresos, tiempo, conversiones y notas
- ✅ **Dashboard Unificado** - Vista de 4 cuadrantes con toda la información
- ✅ **Visualización de Fases** - Tareas sugeridas según el día del ciclo
- ✅ **Generador de Prompts IA** - Análisis automático con ChatGPT/Claude
- ✅ **Exportación CSV** - Datos listos para análisis externo
- ✅ **Sistema de Alertas** - Detección de proyectos zombie y métricas insuficientes
- ✅ **Zero Dependencies** - Solo Python 3.11+ stdlib
- ✅ **Integración Gemini CLI** - Análisis automático y generación de ideas (Opcional)

---

## 🎯 ¿Qué es el Sistema 90D?

El Sistema 90D es tu centro de comando para validar ideas y construir proyectos rentables siguiendo la metodología de **experimentación rápida** y **decisiones basadas en datos**.

### Fases del Ciclo 90D

| Fase | Días | Enfoque | Acciones Clave |
|------|------|---------|----------------|
| 🔍 **Exploración** | 1-14 | Formular hipótesis | Diseñar experimentos baratos |
| ⚡ **Experimentación** | 15-45 | Lanzar MVPs | Medir tracción real |
| ⚖️ **Decisión** | 46-75 | Clasificar proyectos | Kill, Iterate o Winner |
| 📈 **Consolidación** | 76-90 | Escalar winners | Minimizar fricción |

### Principios

- **Velocidad > Perfección** - Lanza rápido, aprende más rápido
- **Datos > Intuición** - Mide todo, decide con evidencia
- **Múltiples experimentos** - Pocos ganadores, muchos aprendizajes
- **Fallar rápido es correcto** - Kill proyectos sin tracción

---

## 🚀 Inicio Rápido

### Requisitos

- **Python 3.11 o superior**
- Navegador web moderno
- Navegador web moderno
- **Ninguna dependencia externa** 🎉 (para funciones base)
- **Gemini CLI** (opcional, para funciones de IA)

### Instalación

```bash
# Clonar o descargar el proyecto
# Clonar o descargar el proyecto
git clone https://github.com/tu-usuario/sistema-90d.git
cd sistema-90d

# (Opcional) Instalar Gemini CLI para funciones de IA
pip install gemini-cli --break-system-packages
gemini setup  # Configurar API Key

# Iniciar servidor (¡así de simple!)
python3 app.py
```

El servidor estará disponible en: **http://localhost:8080**

### Primer Uso

1. **Abre** http://localhost:8080 en tu navegador
2. **Lee** la pantalla de bienvenida que explica el sistema
3. **Haz clic** en "🚀 Iniciar Mi Ciclo 90D" cuando estés listo
4. **Comienza** a registrar proyectos y métricas

---

## 📖 Guía de Uso

### 1. Iniciar tu Ciclo 90D

Al abrir el sistema por primera vez, verás una pantalla de bienvenida. Haz clic en el botón **"🚀 Iniciar Mi Ciclo 90D"** para comenzar el conteo de 90 días.

> ⚠️ **Importante**: El ciclo solo se inicia una vez. Asegúrate de estar listo para dar seguimiento a tus proyectos antes de iniciarlo.

### 2. Crear un Proyecto

Desde el dashboard, en el cuadrante "⚡ Acciones Rápidas":

1. Haz clic en **"➕ Nuevo Proyecto"**
2. Llena el formulario:
   - **Nombre**: Nombre descriptivo (ej: "SaaS de Gestión de Tareas")
   - **Hipótesis**: Qué estás validando (ej: "Los freelancers pagarían $10/mes por tracking de tiempo simple")
   - **Fecha inicio**: Cuándo empezaste (por defecto: hoy)
   - **Estado**: idea | mvp | active | paused
3. Haz clic en **"Guardar Proyecto"**

### 3. Registrar Métricas

Desde el dashboard o desde la vista de un proyecto:

1. Haz clic en **"💰 Registrar Métrica"**
2. Selecciona el proyecto
3. Llena los campos:
   - **Fecha**: Día de la métrica
   - **Ingresos**: USD generados
   - **Tiempo**: Horas invertidas
   - **Conversiones**: Número de conversiones
   - **Notas**: Contexto adicional (opcional)
4. Haz clic en **"Registrar Métrica"**

### 4. Exportar Análisis para IA

1. Haz clic en **"🤖 Prompt IA"** en el header
2. Se descargará un archivo `.md` con:
   - Contexto del ciclo 90D
   - Métricas de todos los proyectos
   - Prompt estructurado para IA
3. Copia el contenido y pégalo en ChatGPT/Claude/Gemini
4. La IA te dará recomendaciones: **kill** | **iterate** | **winner**

### 5. Registrar Decisiones

Después de recibir recomendaciones de la IA:

1. Ve a la vista del proyecto
2. Baja a la sección **"Registrar Decisión de IA"**
3. Llena el formulario con la recomendación recibida
4. Acepta, rechaza o pospone la decisión
5. El sistema actualizará el estado del proyecto automáticamente

### 6. Funciones de IA con Gemini CLI

Si tienes instalado y configurado `gemini-cli`, puedes acceder a funciones avanzadas:

#### 💡 Generador de Ideas
1. Ve a **"💡 Generar Ideas"** en Acciones Rápidas.
2. Selecciona cuántas ideas quieres generar.
3. El sistema analizará tus proyectos actuales para sugerir ideas complementarias o nuevas tendencias.
4. Puedes crear un proyecto directamente desde la idea generada.

#### 🤖 Análisis Automático
1. Ve a **"🤖 Analizar (Gemini)"** en Acciones Rápidas.
2. El sistema ejecutará un análisis profundo de todos tus proyectos, métricas y decisiones recientes.
3. Recibirás un resumen ejecutivo, decisiones sugeridas (Kill/Iterate/Winner) y riesgos detectados.
4. Puedes aceptar o rechazar las decisiones con un clic.


---

## 📁 Estructura del Proyecto

```
sistema_90d/
├── app.py                      # Servidor HTTP (stdlib)
├── database.py                 # Gestión de SQLite
├── dashboard_data.py           # Datos para el dashboard
├── prompt_generator.py         # Generador de prompts IA
├── analisis_ia_gemini.py       # Análisis automático (Gemini CLI)
├── generador_ideas.py          # Generador de ideas (Gemini CLI)
├── gemini_integration.py       # Wrapper para Gemini CLI
├── guia.py                     # Guía contextual
├── backup.py                   # Sistema de backups automáticos
├── validadores.py              # Validación de datos
├── logger_config.py            # Configuración de logging
├── rate_limiter.py             # Rate limiting
├── health.py                   # Health checks
├── integracion_ia.py           # Integración opcional con APIs
├── static/
│   ├── style.css               # Estilos base
│   └── dashboard.css           # Estilos del dashboard
├── templates/
│   ├── index.html              # Dashboard principal
│   ├── proyecto.html           # Vista de proyecto
│   ├── ayuda.html              # Centro de ayuda
│   └── components/             # Componentes reutilizables
│       ├── estado_sistema.html
│       ├── acciones_rapidas.html
│       ├── proyectos_activos.html
│       ├── analisis_alertas.html
│       ├── inicio_ciclo.html
│       ├── modal_nuevo_proyecto.html
│       └── modal_nueva_metrica.html
├── data/
│   └── sistema.db              # Base de datos SQLite
├── test_*.py                   # Tests del sistema
├── README.md                   # Este archivo
├── LICENSE                     # Licencia MIT
├── CONTRIBUTING.md             # Guía de contribución
├── requirements.txt            # Sin dependencias
└── requirements-optional.txt   # Dependencias opcionales
```

---

## 🏗️ Arquitectura

### Stack Tecnológico

| Componente | Solución | Justificación |
|------------|----------|---------------|
| **Backend** | Python stdlib | 0 dependencias vs 5-50MB |
| **Base de datos** | SQLite | Archivo único, cero configuración |
| **Frontend** | HTML + htmx | 14KB vs 3MB bundle |
| **CSS** | Vanilla | <5KB vs 3MB CDN |
| **Servidor** | http.server | Incluido en Python |

### Decisiones de Diseño

#### ¿Por qué NO usamos frameworks?

1. **Velocidad de setup**: 0 segundos vs 30-60 minutos
2. **Portabilidad**: Un solo comando vs Docker + K8s
3. **Eficiencia**: 15MB RAM vs 500MB+
4. **Mantenibilidad**: 0 dependencias que actualizar

#### Sistema de Templates

Implementamos un motor de templates minimalista que soporta:
- Variables: `{{ variable }}`
- Condicionales: `{% if condition %} ... {% endif %}`
- Bucles: `{% for item in list %} ... {% endfor %}`
- Includes: `{% include 'file.html' %}`

#### Base de Datos

SQLite con:
- **WAL mode**: Previene corrupción
- **Foreign keys**: Integridad referencial
- **Índices optimizados**: Queries rápidas
- **Vistas**: Simplifica consultas complejas

---

## ⚡ Performance

Todos los criterios de aceptación MVP cumplidos:

- ✅ Proyecto registrado en <2 minutos
- ✅ Métrica ingresada en <1 minuto
- ✅ Dashboard carga en <100ms (medido: ~0.6ms)
- ✅ Prompt exportado en <5 segundos (medido: ~0.001s)
- ✅ Ejecutable con solo `python3 app.py`
- ✅ Uso de memoria <128MB (medido: ~15MB)

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests del sistema completo
python3 test_sistema.py

# Tests del dashboard
python3 test_dashboard.py

# Tests de decisiones
python3 test_decisiones.py

# Tests de mejoras
python3 test_mejoras.py

# Tests de robustez
python3 test_robustez.py
```

### Datos de Prueba

Para probar el sistema con datos de ejemplo:

```bash
python3 test_sistema.py
```

Esto creará 4 proyectos con diferentes estados y métricas.

---

## 🔒 Seguridad y Robustez

- **Rate Limiting**: Previene abuso de endpoints
- **Validación de Datos**: Validadores para proyectos y métricas
- **Transacciones ACID**: Garantiza consistencia de datos
- **Backups Automáticos**: Sistema de respaldo cada 24 horas
- **Health Checks**: Endpoint `/health` para monitoreo
- **Logging**: Registro de errores y actividad

---

## 📊 Exportación de Datos

### CSV

Exporta todos tus proyectos y métricas en formato CSV:

```bash
# Desde la interfaz web
Dashboard → 📊 CSV

# O directamente
curl http://localhost:8080/exportar-csv > datos.csv
```

### Prompt para IA

Genera un análisis completo para IA externa:

```bash
# Desde la interfaz web
Dashboard → 🤖 Prompt IA

# O directamente
curl http://localhost:8080/exportar-prompt > analisis.md
```

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) para conocer las pautas.

### Áreas de Contribución

- 🐛 Reportar bugs
- 💡 Proponer features
- 📝 Mejorar documentación
- 🧪 Agregar tests
- ⚡ Optimizar performance

---

## 📝 Próximos Pasos (Post-MVP)

Funcionalidades **NO** incluidas intencionalmente:

- ❌ Automatización de métricas (Stripe, analytics)
- ❌ Gráficos interactivos (Chart.js)
- ❌ Sistema de tareas/TODOs
- ❌ Multi-usuario / Sync cloud
- ❌ Alertas automáticas por email

**Cuándo agregarlas**: Solo si el MVP demuestra uso consistente por >3 meses.

---

## ❓ FAQ

### ¿Puedo reiniciar el ciclo 90D?

Actualmente no hay una opción en la interfaz. Si necesitas reiniciar, elimina la base de datos:

```bash
rm data/sistema.db
python3 app.py
```

### ¿Cómo hago backup de mis datos?

El sistema crea backups automáticos cada 24 horas en la carpeta `backups/`. También puedes:

```bash
# Backup manual
cp data/sistema.db backups/manual_$(date +%Y%m%d).db
```

### ¿Puedo usar el sistema sin internet?

¡Sí! El sistema funciona 100% offline. Solo necesitas internet si quieres:
- Usar la integración opcional con APIs de IA
- Descargar htmx (ya incluido en los templates)

### ¿Cómo cambio el puerto del servidor?

Edita `app.py` y cambia la variable `PORT`:

```python
PORT = 8080  # Cambia a tu puerto preferido
```

### ¿Puedo ejecutar múltiples instancias?

Sí, pero cada instancia necesita su propia base de datos y puerto:

```bash
# Instancia 1
python3 app.py  # Puerto 8080

# Instancia 2 (en otra terminal)
PORT=8081 python3 app.py
```

---

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

**Uso libre para solopreneurs. Construye tu imperio.** 🚀

---

## 🙏 Agradecimientos

- **Marc Lou** - Por la metodología original de ciclos 90D
- **Comunidad de Indie Hackers** - Por el feedback y las ideas
- **Python Software Foundation** - Por un lenguaje increíble

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/sistema-90d/issues)
- **Documentación**: Lee el `Documento_Base.md` para entender la metodología completa
- **Ayuda**: Endpoint `/ayuda` en la interfaz web

---

**¿Preguntas?** Abre un issue o consulta la [guía de ayuda](http://localhost:8080/ayuda) en la interfaz web.

---

<div align="center">

**Hecho con ❤️ para solopreneurs que construyen en público**

[⭐ Star en GitHub](https://github.com/tu-usuario/sistema-90d) • [🐛 Reportar Bug](https://github.com/tu-usuario/sistema-90d/issues) • [💡 Solicitar Feature](https://github.com/tu-usuario/sistema-90d/issues)

</div>
