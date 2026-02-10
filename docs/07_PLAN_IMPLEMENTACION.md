# SUB-PROMPT 07: PLAN DE IMPLEMENTACIÓN TÉCNICO

## CONTEXTO
Todos los sub-prompts anteriores han definido QUÉ construir.
Este documento define CÓMO construirlo en orden óptimo.

## OBJETIVO
Roadmap técnico que permite:
1. Tener un MVP funcional en 7 días
2. Iterar en bloques coherentes
3. Evitar refactorizaciones masivas

---

## FASE 0: SETUP INICIAL (DÍA 0 - 1 hora)

### Estructura de directorios
```bash
# /sistema_90d/setup.sh

mkdir -p sistema_90d/{data,static,templates,prompts/{templates,generated},respuestas_ia,tests}
cd sistema_90d

# Crear archivos base
touch app.py database.py motor_metricas.py generador_prompts.py parser_respuestas.py
touch static/style.css
touch data/.gitkeep  # Para versionado sin exponer DB

# Dependencias mínimas
cat > requirements.txt <<EOF
jinja2==3.1.2        # Templating (obligatorio)
# NO Flask, NO FastAPI, NO nada más
EOF

# Entorno virtual (opcional pero recomendado)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Decisión justificada:**
- **NO usar virtualenv:** Si el usuario tiene Python 3.11+ limpio, no es necesario
- **SÍ usar si existe riesgo de conflictos:** Mejor prevenir que depurar

---

## FASE 1: MVP CORE (DÍAS 1-3)

### DÍA 1: Base de datos + Servidor mínimo

**Objetivo:** Tener servidor corriendo con base de datos funcional.

**Tareas:**
1. Implementar `database.py`:
   ```python
   # /sistema_90d/database.py
   
   import sqlite3
   from pathlib import Path
   
   DB_PATH = 'data/sistema.db'
   
   def init_db():
       """Crea todas las tablas del sistema."""
       db = sqlite3.connect(DB_PATH)
       
       # Ejecutar schema.sql (lo creamos ahora)
       with open('schema.sql', 'r') as f:
           db.executescript(f.read())
       
       db.commit()
       db.close()
   
   def get_db() -> sqlite3.Connection:
       """Retorna conexión a DB con row_factory."""
       db = sqlite3.connect(DB_PATH)
       db.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
       return db
   ```

2. Crear `schema.sql` con todo el DDL del sub-prompt 02:
   ```sql
   -- /sistema_90d/schema.sql
   -- (Contenido completo del modelo de datos)
   ```

3. Implementar `app.py` básico:
   ```python
   # /sistema_90d/app.py
   
   from http.server import HTTPServer, BaseHTTPRequestHandler
   from urllib.parse import urlparse, parse_qs
   import json
   from pathlib import Path
   
   class SistemaHandler(BaseHTTPRequestHandler):
       def do_GET(self):
           url = urlparse(self.path)
           
           if url.path == '/':
               self.serve_template('dashboard.html')
           elif url.path.startswith('/static/'):
               self.serve_static(url.path[8:])
           else:
               self.send_error(404)
       
       def serve_template(self, template_name):
           # Renderizado simple (sin Jinja por ahora)
           template_path = Path('templates') / template_name
           
           if template_path.exists():
               self.send_response(200)
               self.send_header('Content-type', 'text/html')
               self.end_headers()
               
               with open(template_path, 'rb') as f:
                   self.wfile.write(f.read())
           else:
               self.send_error(404)
       
       def serve_static(self, file_path):
           static_path = Path('static') / file_path
           
           if static_path.exists():
               self.send_response(200)
               
               # Detectar content-type
               if file_path.endswith('.css'):
                   self.send_header('Content-type', 'text/css')
               elif file_path.endswith('.js'):
                   self.send_header('Content-type', 'application/javascript')
               
               self.end_headers()
               
               with open(static_path, 'rb') as f:
                   self.wfile.write(f.read())
           else:
               self.send_error(404)
   
   if __name__ == '__main__':
       from database import init_db
       
       # Inicializar DB si no existe
       if not Path('data/sistema.db').exists():
           print("Inicializando base de datos...")
           init_db()
       
       server = HTTPServer(('localhost', 8080), SistemaHandler)
       print("Sistema 90D corriendo en http://localhost:8080")
       server.serve_forever()
   ```

**Complejidad:**
- Código: ~150 líneas
- Tiempo: 2-3 horas

**Verificación:**
```bash
python app.py
# Abrir http://localhost:8080
# Debe mostrar HTML básico (aunque sin datos)
```

---

### DÍA 2: Templates HTML + CSS

**Objetivo:** UI visible y navegable.

**Tareas:**
1. Crear `templates/base.html` (layout común)
2. Crear `templates/dashboard.html` (vista principal)
3. Crear `templates/proyecto.html` (vista detalle)
4. Crear `static/style.css` (estilos del sub-prompt 03)

**CRÍTICO:** En este punto, los templates NO renderizan datos reales. Solo muestran estructura.

**Ejemplo de dashboard.html SIN datos:**
```html
<!-- /sistema_90d/templates/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header class="phase-banner phase-exploracion">
    <h1>Día X/90 — Fase: Exploración</h1>
  </header>
  
  <section>
    <h2>Proyectos Activos</h2>
    <table>
      <thead>
        <tr><th>Proyecto</th><th>Estado</th><th>Ingresos</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>Proyecto Demo</td>
          <td><span class="badge badge-active">active</span></td>
          <td>$0</td>
        </tr>
      </tbody>
    </table>
  </section>
</body>
</html>
```

**Complejidad:**
- Código: ~300 líneas HTML + 100 líneas CSS
- Tiempo: 3-4 horas

**Verificación:**
```bash
python app.py
# Dashboard debe verse correctamente formateado
# Colores, tipografía, layout responsive
```

---

### DÍA 3: Renderizado dinámico con Jinja2

**Objetivo:** Conectar templates con base de datos.

**Tareas:**
1. Reemplazar renderizado simple por Jinja2 en `app.py`:
   ```python
   # /sistema_90d/app.py (actualizado)
   
   from jinja2 import Environment, FileSystemLoader
   from database import get_db
   
   jinja_env = Environment(loader=FileSystemLoader('templates'))
   
   class SistemaHandler(BaseHTTPRequestHandler):
       def serve_template(self, template_name, context=None):
           template = jinja_env.get_template(template_name)
           html = template.render(context or {})
           
           self.send_response(200)
           self.send_header('Content-type', 'text/html; charset=utf-8')
           self.end_headers()
           self.wfile.write(html.encode('utf-8'))
       
       def do_GET(self):
           url = urlparse(self.path)
           
           if url.path == '/':
               db = get_db()
               
               # Obtener proyectos activos
               proyectos = db.execute("""
                   SELECT * FROM v_resumen_proyectos 
                   WHERE estado IN ('active', 'mvp')
               """).fetchall()
               
               # Calcular día actual del ciclo
               config = db.execute("""
                   SELECT valor FROM config_sistema 
                   WHERE clave = 'fecha_inicio_ciclo'
               """).fetchone()
               
               from datetime import datetime
               fecha_inicio = datetime.fromisoformat(config[0])
               dia_actual = (datetime.now() - fecha_inicio).days + 1
               
               self.serve_template('dashboard.html', {
                   'proyectos': proyectos,
                   'dia_actual': dia_actual,
                   'fase_actual': 'experimentacion'  # TODO: calcular dinámicamente
               })
   ```

2. Actualizar `templates/dashboard.html` para usar variables Jinja:
   ```html
   <h1>Día {{ dia_actual }}/90 — Fase: {{ fase_actual|title }}</h1>
   
   <tbody>
     {% for proyecto in proyectos %}
     <tr>
       <td>{{ proyecto.nombre }}</td>
       <td><span class="badge badge-{{ proyecto.estado }}">{{ proyecto.estado }}</span></td>
       <td>${{ proyecto.ingresos_total }}</td>
     </tr>
     {% endfor %}
   </tbody>
   ```

**Complejidad:**
- Código: +100 líneas en app.py
- Tiempo: 2-3 horas

**Verificación:**
```bash
# Insertar proyecto de prueba manualmente
sqlite3 data/sistema.db
> INSERT INTO proyectos (nombre, hipotesis, fecha_inicio) 
  VALUES ('Proyecto Test', 'Resolver X', unixepoch());
> .exit

python app.py
# Dashboard debe mostrar "Proyecto Test" con datos reales
```

---

## FASE 2: FUNCIONALIDAD CORE (DÍAS 4-5)

### DÍA 4: Formularios de entrada

**Objetivo:** Usuario puede crear proyectos y métricas.

**Tareas:**
1. Implementar rutas POST en `app.py`:
   ```python
   def do_POST(self):
       url = urlparse(self.path)
       
       if url.path == '/proyectos/nuevo':
           self.handle_nuevo_proyecto()
       elif url.path == '/metricas/guardar':
           self.handle_guardar_metrica()
   
   def handle_nuevo_proyecto(self):
       # Leer form data
       content_length = int(self.headers['Content-Length'])
       post_data = self.rfile.read(content_length)
       params = parse_qs(post_data.decode('utf-8'))
       
       nombre = params['nombre'][0]
       hipotesis = params['hipotesis'][0]
       
       db = get_db()
       db.execute("""
           INSERT INTO proyectos (nombre, hipotesis, fecha_inicio)
           VALUES (?, ?, unixepoch())
       """, (nombre, hipotesis))
       db.commit()
       
       # Redirect a dashboard
       self.send_response(303)
       self.send_header('Location', '/')
       self.end_headers()
   ```

2. Crear templates de formularios (ver sub-prompt 03)

**Complejidad:**
- Código: +200 líneas
- Tiempo: 3-4 horas

---

### DÍA 5: Motor de métricas básico

**Objetivo:** Detectar señales simples (kill sin ingresos).

**Tareas:**
1. Implementar `motor_metricas.py` (versión mínima con solo 2 reglas):
   - Regla 1: Sin ingresos en N días
   - Regla 2: Crecimiento consistente

2. Integrar en dashboard:
   ```python
   from motor_metricas import MotorMetricas
   
   motor = MotorMetricas('data/sistema.db')
   analisis = motor.analizar_todos_los_proyectos()
   
   alertas = []
   for proyecto_id, señales in analisis.items():
       for señal in señales:
           alertas.append({
               'tipo': señal.severidad,
               'mensaje': señal.mensaje
           })
   
   self.serve_template('dashboard.html', {
       'proyectos': proyectos,
       'alertas': alertas,
       # ...
   })
   ```

**Complejidad:**
- Código: ~300 líneas
- Tiempo: 4-5 horas

**Verificación:**
```bash
# Crear proyecto sin ingresos hace 30+ días
# Dashboard debe mostrar alerta: "⚠️ Proyecto X sin ingresos en 30 días"
```

---

## FASE 3: INTEGRACIÓN IA (DÍAS 6-7)

### DÍA 6: Generador de prompts

**Objetivo:** Usuario puede exportar análisis para IA.

**Tareas:**
1. Implementar `generador_prompts.py` (sub-prompt 05)
2. Crear template `prompts/templates/analisis_semanal.txt`
3. Agregar ruta `/exportar-ia` en app.py

**Complejidad:**
- Código: ~250 líneas
- Tiempo: 3-4 horas

---

### DÍA 7: Parser de respuestas

**Objetivo:** Usuario puede pegar respuesta de IA y registrarla.

**Tareas:**
1. Implementar `parser_respuestas.py`
2. Crear formulario en `templates/exportar_ia.html`
3. Agregar ruta POST `/ia/parsear-respuesta`

**Complejidad:**
- Código: ~150 líneas
- Tiempo: 2-3 horas

**HITO:** Al final del día 7, el MVP está completo y funcional.

---

## FASE 4: RITUALES Y PULIDO (DÍAS 8-10)

### DÍA 8: Ritual diario
- Implementar `/ritual-diario`
- Crear tabla `rituales_completados`
- Sistema de recordatorios

### DÍA 9: Ritual semanal
- Implementar `/ritual-semanal`
- Integrar con generador de prompts

### DÍA 10: Testing + documentación
- Casos de prueba manuales
- README con instrucciones de uso
- Script de demo con datos de ejemplo

---

## CHECKLIST DE ENTREGA MVP

```
□ Base de datos inicializada con schema completo
□ Servidor HTTP corriendo en localhost:8080
□ Dashboard muestra proyectos activos con métricas
□ Formulario de nuevo proyecto funcional
□ Formulario de registro de métricas funcional
□ Motor de métricas detecta al menos 2 señales
□ Generador de prompts exporta análisis semanal
□ Parser de respuestas valida JSON de IA
□ Ritual diario implementado y funcional
□ CSS aplicado correctamente (sin errores visuales)
□ Sistema corre con <128MB RAM (verificar con htop)
□ Base de datos <5MB con 10 proyectos y 100 métricas
```

---

## ESTIMACIÓN DE RECURSOS

### Tiempo total de desarrollo
- **Optimista (desarrollador senior):** 7 días @ 6h/día = 42 horas
- **Realista (desarrollador mid):** 10 días @ 6h/día = 60 horas
- **Pesimista (aprendiendo Python):** 15 días @ 8h/día = 120 horas

### Recursos de hardware
- **Desarrollo:** Cualquier laptop con Python 3.11+
- **Producción:** Mismo hardware (es local)

### Dependencias externas
- Python 3.11+ (stdlib)
- Jinja2 (14KB)
- **Total:** <1MB de dependencias

---

## PLAN DE CONTINGENCIA

### Si algo sale mal en Día 3
**Síntoma:** Templates no renderizan datos.
**Causa probable:** Error en queries SQL o row_factory.
**Solución:**
1. Testear queries en sqlite3 CLI directamente
2. Agregar logging en app.py:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logging.debug(f"Proyectos obtenidos: {proyectos}")
   ```

### Si algo sale mal en Día 5
**Síntoma:** Motor de métricas no detecta señales.
**Causa probable:** Umbrales muy altos o datos de prueba incorrectos.
**Solución:**
1. Verificar valores en `config_sistema`
2. Insertar métrica de prueba con fecha antigua:
   ```sql
   INSERT INTO metricas (proyecto_id, fecha, ingresos)
   VALUES (1, unixepoch('now', '-40 days'), 0);
   ```

---

## ROADMAP POST-MVP (OPCIONAL)

### Fase 5: Mejoras de UX (Días 11-14)
- [ ] Agregar htmx para formularios sin reload
- [ ] Gráficos SVG server-side para tendencias
- [ ] Dark mode (toggle CSS)

### Fase 6: Automatización (Días 15-20)
- [ ] Integración con Stripe API (métricas automáticas de ingresos)
- [ ] Webhooks para captura de conversiones
- [ ] Script de backup automático de DB

### Fase 7: Optimización (Días 21-30)
- [ ] Índices adicionales en DB si queries >100ms
- [ ] Compresión de archivos generados (prompts, respuestas)
- [ ] Tests unitarios con pytest

---

## MÉTRICAS DE ÉXITO DEL DESARROLLO

Al finalizar MVP, verificar:

```
✅ Código total: <2000 líneas
✅ Dependencias: <3 paquetes PyPI
✅ Tiempo de startup: <1 segundo
✅ Memoria en uso: <100MB
✅ Tamaño de repo: <5MB (sin DB de prueba)
✅ Tiempo de onboarding: <5 minutos (desde git clone hasta primer proyecto creado)
```

---

## SCRIPT DE INSTALACIÓN AUTOMATIZADO

```bash
#!/bin/bash
# /sistema_90d/install.sh

echo "🚀 Instalando Sistema 90D..."

# Verificar Python 3.11+
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$python_version < 3.11" | bc -l) )); then
    echo "❌ Error: Se requiere Python 3.11 o superior"
    exit 1
fi

# Crear estructura
mkdir -p data static templates prompts/{templates,generated} respuestas_ia tests

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python3 -c "from database import init_db; init_db()"

# Insertar datos de demo
sqlite3 data/sistema.db < demo_data.sql

echo "✅ Sistema instalado correctamente"
echo "▶️  Ejecuta: python3 app.py"
echo "🌐 Abre: http://localhost:8080"
```

---

## ENTREGABLE FINAL

```
/sistema_90d/
  README.md                  # Instrucciones de instalación y uso
  install.sh                 # Script de instalación automatizado
  requirements.txt           # Dependencias mínimas
  schema.sql                 # Schema completo de DB
  demo_data.sql              # Datos de ejemplo
  app.py                     # Servidor HTTP + rutas
  database.py                # Wrapper de SQLite
  motor_metricas.py          # Motor de análisis
  generador_prompts.py       # Generador de prompts IA
  parser_respuestas.py       # Parser de respuestas IA
  /static/
    style.css                # Estilos (<5KB)
  /templates/
    base.html
    dashboard.html
    proyecto.html
    metricas.html
    exportar_ia.html
    ritual_diario.html
    ritual_semanal.html
  /prompts/templates/
    analisis_semanal.txt     # Template Jinja2
  /tests/
    test_motor_metricas.py   # Tests unitarios
```

**Total estimado:** ~2500 líneas de código (Python + HTML + SQL + CSS).

---

**SIGUIENTE PASO:** Ejecutar este plan día por día, validando cada hito antes de avanzar.
