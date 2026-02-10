#!/usr/bin/env python3
"""
app.py - Servidor HTTP para Sistema 90D
Ruta: /home/josuedgg/Documentos/Proyectos/Sistema Base/sistema_90d/app.py

Servidor web minimalista usando solo Python stdlib.
Sin frameworks (Flask/FastAPI). Máxima eficiencia y cero dependencias.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import re
import os
import json
import csv
import io
from datetime import date, datetime

import database as db
import prompt_generator as pg
import backup as bk  # Sistema de backup automático
from integracion_ia import IntegradorIA  # Integración opcional con APIs
import guia  # Guía contextual (NUEVO Fase 3)
import dashboard_data  # Datos para el dashboard unificado
from validadores import ValidadorMetricas, ValidadorProyectos, ErrorValidacion
from logger_config import configurar_logging, logger_app
from rate_limiter import limiter


# Configuración
HOST = 'localhost'
PORT = 8080
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


def _get_value(obj, key_path):
    """Auxiliar para obtener valores anidados de un objeto/diccionario."""
    parts = key_path.split('.')
    current = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, object) and hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current

def render_string(html: str, context: dict) -> str:
    """Procesa un string HTML con la lógica de plantillas (Soporta multi-línea)."""
    
    # 1. Manejar bloques {% include '...' %}
    def replace_include(match):
        inc_name = match.group(1).strip()
        template_path = os.path.join(TEMPLATES_DIR, inc_name)
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return render_string(content, context)
        return f"<!-- Include failed: {inc_name} -->"
    
    # Permitir saltos de línea con \s* y re.DOTALL
    html = re.sub(r"{%\s*include\s*['\"](.*?)['\"]\s*%}", replace_include, html, flags=re.DOTALL)

    # 2. Manejar bucles {% for item in list %} ... {% endfor %}
    def replace_for(match):
        item_name = match.group(1).strip()
        list_name = match.group(2).strip()
        inner_content = match.group(3)
        
        items = _get_value(context, list_name)
        if not items or not isinstance(items, (list, tuple)):
            return ""
            
        rendered_items = []
        for item in items:
            local_context = context.copy()
            local_context[item_name] = item
            rendered_items.append(render_string(inner_content, local_context))
        return "".join(rendered_items)

    html = re.sub(r"{%\s*for\s+([a-zA-Z0-9_]+)\s+in\s+([a-zA-Z0-9._]+)\s*%}(.*?){%\s*endfor\s*%}", 
                  replace_for, html, flags=re.DOTALL)

    # 3. Manejar condicionales {% if ... %} ... {% endif %}
    def replace_if(match):
        var_name = match.group(1).strip()
        content = match.group(2)
        val = _get_value(context, var_name)
        return render_string(content, context) if val else ""
        
    html = re.sub(r"{%\s*if\s+([^\s%]+)\s*%}(.*?){%\s*endif\s*%}", replace_if, html, flags=re.DOTALL)

    # 4. Reemplazar variables {{ ... }}
    def replace_var(match):
        key_path = match.group(1).strip()
        val = _get_value(context, key_path)
        return str(val) if val is not None else ""

    # Usar (.*?) con DOTALL para soportar variables divididas por el editor
    html = re.sub(r"\{\{\s*(.*?)\s*\}\}", replace_var, html, flags=re.DOTALL)
    
    return html

def render_template(template_name: str, context: dict) -> str:
    """Carga un archivo y lo renderiza."""
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    if not os.path.exists(template_path):
        return f"<!-- Template not found: {template_name} -->"
        
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    return render_string(html, context)


def parse_post_data(content: bytes) -> dict:
    """
    Parsear datos de formulario POST.
    
    Args:
        content: Bytes del body de la request
    
    Returns:
        dict: Datos parseados
    """
    content_str = content.decode('utf-8')
    parsed = parse_qs(content_str)
    
    # Convertir listas de 1 elemento a valores simples
    result = {}
    for key, value in parsed.items():
        result[key] = value[0] if len(value) == 1 else value
    
    return result


class Sistema90DHandler(BaseHTTPRequestHandler):
    """
    Request handler para el Sistema 90D.
    Maneja todas las rutas HTTP.
    """
    
    def do_GET(self):
        """Manejar requests GET"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Routing
        if path == '/':
            self.handle_dashboard()
        elif path == '/ayuda':
            self.handle_ayuda()
        elif path.startswith('/proyecto/'):
            proyecto_id = path.split('/')[-1]
            if proyecto_id.isdigit():
                self.handle_proyecto(int(proyecto_id))
            else:
                self.send_error(404, "Proyecto no encontrado")
        elif path == '/exportar-prompt':
            self.handle_exportar_prompt()
        elif path == '/exportar-csv':
            self.handle_exportar_csv()
        elif path == '/analizar-ia':
            self.handle_analizar_ia()
        elif path == '/health':
            self.handle_health()
        elif path.startswith('/static/'):
            self.handle_static(path)
        else:
            self.send_error(404, "Página no encontrada")
    
    def do_POST(self):
        """Manejar requests POST"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Leer body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = parse_post_data(post_data)
        
        # Routing
        if path == '/proyecto/nuevo':
            self.handle_crear_proyecto(data)
        elif path == '/metrica/nueva':
            self.handle_crear_metrica(data)
        elif path == '/decisiones/responder':
            self.handle_responder_decision(data)
        elif path == '/ciclo/iniciar':
            self.handle_iniciar_ciclo()
        elif path.startswith('/proyecto/') and path.endswith('/actualizar'):
            proyecto_id = path.split('/')[-2]
            if proyecto_id.isdigit():
                self.handle_actualizar_proyecto(int(proyecto_id), data)
            else:
                self.send_error(404)
        else:
            self.send_error(404, "Ruta no encontrada")
    
    # ========================================================================
    # HANDLERS - GET
    # ========================================================================
    
    def handle_dashboard(self):
        """Renderizar dashboard unificado de 4 cuadrantes."""
        try:
            # Verificar si hay ciclo iniciado
            tiene_ciclo = db.tiene_ciclo_iniciado()
            
            if not tiene_ciclo:
                # Mostrar pantalla de inicio
                context = {'tiene_ciclo': False}
                html = render_template('index.html', context)
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
                return
            
            # 1. Obtener datos de salud y estado
            estado = dashboard_data.obtener_estado_sistema()
            
            # 2. Resumen de proyectos
            proyectos = dashboard_data.obtener_proyectos_resumen()
            
            # 3. Siguiente acción sugerida
            siguiente = guia.obtener_siguiente_accion()
            
            # 4. Alertas globales
            alertas = db.obtener_todas_alertas_activas()
            
            # 5. Guía contextual (Fase 3 adaptada)
            guia_ctx = guia.obtener_guia_contextual(proyectos, estado['fase'])
            
            # 6. Datos adicionales (Comparativa y Hitos)
            comparacion = {
                'ingresos_cambio': 0,
                'ingresos_direccion': 'neutral',
                'ingresos_icono': '▬'
            }
            
            proximos_hitos = [
                {'fecha': 'Próximamente', 'descripcion': 'Revisión de ciclo'}
            ]
            
            context = {
                'tiene_ciclo': True,
                'estado': estado,
                'proyectos': proyectos,
                'siguiente_accion': siguiente,
                'alertas': alertas,
                'guia': guia_ctx,
                'comparacion': comparacion,
                'proximos_hitos': proximos_hitos,
                'limite_proyectos': 3,
                'fecha_hoy': date.today().isoformat()
            }
            
            html = render_template('index.html', context)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            logger_app.error(f"Error en dashboard: {e}", exc_info=True)
            self.send_error(500, "Error interno al cargar el dashboard")

    def handle_ayuda(self):
        """Renderizar centro de ayuda interactivo."""
        try:
            html = render_template('ayuda.html', {})
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            logger_app.error(f"Error en ayuda: {e}", exc_info=True)
            self.send_error(500, "Error interno al cargar la ayuda")
    
    def handle_proyecto(self, proyecto_id: int):
        """Renderizar vista de proyecto individual"""
        proyecto = db.obtener_proyecto(proyecto_id)
        if not proyecto:
            self.send_error(404, "Proyecto no encontrado")
            return
        
        dashboard = db.calcular_dashboard_proyecto(proyecto_id)
        metricas = db.obtener_metricas_proyecto(proyecto_id)
        decisiones = db.obtener_decisiones_proyecto(proyecto_id)
        alertas = db.obtener_alertas_proyecto(proyecto_id)
        
        # Construir alertas HTML
        alertas_html = ""
        if alertas:
            alertas_html = '<div class="alertas-container" style="margin-bottom: var(--spacing-md);">'
            for al in alertas:
                clase = f"alert-{al['severidad']}"
                alertas_html += f"""
                <div class="alert-box {clase}" style="padding: 10px; border-radius: 4px; border-left: 4px solid; margin-bottom: 5px; background: #fffbeb;">
                    <strong>⚠️ {al['tipo'].upper()}:</strong> {al['mensaje']}
                </div>
                """
            alertas_html += '</div>'
        if metricas:
            metricas_html = '<table class="metricas-table">\n'
            metricas_html += '<thead><tr><th>Fecha</th><th>Ingresos</th><th>Tiempo (h)</th><th>Conversiones</th><th>Notas</th></tr></thead>\n'
            metricas_html += '<tbody>\n'
            
            for m in metricas:
                notas = m['notas'] if m['notas'] else '-'
                metricas_html += f'<tr>\n'
                metricas_html += f'  <td>{m["fecha"]}</td>\n'
                metricas_html += f'  <td>${m["ingresos"]:.2f}</td>\n'
                metricas_html += f'  <td>{m["tiempo_horas"]:.1f}</td>\n'
                metricas_html += f'  <td>{m["conversiones"]}</td>\n'
                metricas_html += f'  <td>{notas}</td>\n'
                metricas_html += f'</tr>\n'
            
            metricas_html += '</tbody>\n</table>'
        else:
            metricas_html = '<p class="empty-state">No hay métricas registradas. ¡Registra la primera métrica abajo!</p>'
        
        # Construir historial de decisiones
        if decisiones:
            decisiones_html = '<div class="decisiones-historial">\n'
            for d in decisiones:
                clase = f"accion-{d['accion_tomada']}"
                razon = f"<p><strong>Razón rechazo:</strong> {d['razon_rechazo']}</p>" if d['razon_rechazo'] else ""
                decisiones_html += f"""
                <div class="decision-card {clase}">
                    <p><strong>Fecha:</strong> {d['fecha']}</p>
                    <p><strong>Acción:</strong> {d['accion_tomada'].upper()} - <strong>Tipo:</strong> {d['tipo'].upper()}</p>
                    <p><strong>Justificación:</strong> {d['justificacion']}</p>
                    {razon}
                </div>
                """
            decisiones_html += '</div>'
        else:
            decisiones_html = '<p class="empty-state">No hay decisiones registradas aún.</p>'
        
        # Opciones de estado para selector
        estados = ['idea', 'mvp', 'active', 'paused', 'killed', 'winner']
        estado_options = ''
        for estado in estados:
            selected = 'selected' if estado == proyecto['estado'] else ''
            estado_options += f'<option value="{estado}" {selected}>{estado}</option>\n'
        
        context = {
            'proyecto_id': proyecto_id,
            'proyecto_nombre': proyecto['nombre'],
            'proyecto_hipotesis': proyecto['hipotesis'],
            'proyecto_fecha_inicio': proyecto['fecha_inicio'],
            'proyecto_estado': proyecto['estado'],
            'total_ingresos': f"${dashboard['total_ingresos']:.2f}",
            'total_tiempo': f"{dashboard['total_tiempo']:.1f}",
            'roi': f"${dashboard['roi']:.2f}",
            'total_conversiones': dashboard['total_conversiones'],
            'num_metricas': dashboard['num_metricas'],
            'metricas_tabla': metricas_html,
            'alertas_html': alertas_html,
            'decisiones_historial': decisiones_html,
            'fecha_hoy': date.today().isoformat(),
            'estado_options': estado_options
        }
        
        html = render_template('proyecto.html', context)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_exportar_prompt(self):
        """Generar y descargar prompt de análisis"""
        prompt = pg.generar_prompt_analisis()
        
        # Guardar archivo
        fecha = date.today().isoformat()
        filename = f"analisis_{fecha}.md"
        filepath = pg.guardar_prompt_archivo(prompt, f"data/{filename}")
        
        # Enviar como descarga
        self.send_response(200)
        self.send_header('Content-Type', 'text/markdown; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(prompt.encode('utf-8'))

    def handle_analizar_ia(self):
        """Ejecuta análisis automático si hay API key, sino muestra el prompt."""
        ia = IntegradorIA()
        resultado = ia.analizar_automaticamente()
        
        # Enviar respuesta como JSON
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(resultado).encode('utf-8'))

    def handle_exportar_csv(self):
        """Generar y descargar CSV consolidado de métricas"""
        proyectos = db.obtener_todos_proyectos_con_metricas()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Proyecto', 'Estado', 'Hipotesis', 'Ingresos Totales', 'Tiempo Total (h)', 'ROI ($/h)', 'Conversiones', 'Num Metricas'])
        
        for p in proyectos:
            writer.writerow([
                p['nombre'], p['estado'], p['hipotesis'],
                f"{p['total_ingresos']:.2f}", f"{p['total_tiempo']:.1f}",
                f"{p['roi']:.2f}", p['total_conversiones'], p['num_metricas']
            ])
            
        content = output.getvalue()
        output.close()
        
        fecha = date.today().isoformat()
        filename = f"sistema_90d_datos_{fecha}.csv"
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def handle_static(self, path: str):
        """Servir archivos estáticos (CSS)"""
        filename = path.replace('/static/', '')
        filepath = os.path.join(STATIC_DIR, filename)
        
        if not os.path.exists(filepath):
            self.send_error(404, "Archivo no encontrado")
            return
        
        # Determinar content type
        if filename.endswith('.css'):
            content_type = 'text/css'
        elif filename.endswith('.js'):
            content_type = 'application/javascript'
        else:
            content_type = 'text/plain'
        
        with open(filepath, 'rb') as f:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(f.read())

    def handle_health(self):
        """Retorna estado de salud del sistema."""
        salud = verificar_salud()
        self.send_response(200 if salud["status"] == "healthy" else 500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(salud).encode('utf-8'))
    
    # ========================================================================
    # HANDLERS - POST
    # ========================================================================
    
    def handle_crear_proyecto(self, data: dict):
        """Crear nuevo proyecto con validación y rate limiting."""
        try:
            if not limiter.permitir('crear_proyecto', limite=3, ventana=60):
                self.send_error(429, "Demasiados proyectos creados. Espera un minuto.")
                return

            nombre = ValidadorProyectos.validar_nombre(data.get('nombre', ''))
            hipotesis = ValidadorProyectos.validar_hipotesis(data.get('hipotesis', ''))
            fecha_inicio = data.get('fecha_inicio', date.today().isoformat())
            estado = data.get('estado', 'idea')
            
            proyecto_id = db.crear_proyecto(nombre, hipotesis, fecha_inicio, estado)
            logger_app.info(f"Nuevo proyecto creado: {nombre} (ID: {proyecto_id})")
            
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
            
        except ErrorValidacion as e:
            self.send_error(400, f"Error de validación: {str(e)}")
        except Exception as e:
            logger_app.error(f"Error al crear proyecto: {e}", exc_info=True)
            self.send_error(500, "Error interno del servidor")
    
    def handle_crear_metrica(self, data: dict):
        """Crear nueva métrica con validación y rate limiting."""
        try:
            if not limiter.permitir('crear_metrica', limite=10, ventana=60):
                self.send_error(429, "Demasiadas métricas registradas. Espera un minuto.")
                return

            proyecto_id = int(data.get('proyecto_id', 0))
            fecha = ValidadorMetricas.validar_fecha(data.get('fecha', ''))
            ingresos = ValidadorMetricas.validar_ingresos(data.get('ingresos', '0'))
            tiempo_horas = ValidadorMetricas.validar_tiempo(data.get('tiempo_horas', '0'))
            conversiones = ValidadorMetricas.validar_conversiones(data.get('conversiones', '0'))
            notas = data.get('notas', '').strip()
            
            if proyecto_id <= 0:
                self.send_error(400, "Proyecto inválido")
                return
            
            db.crear_metrica(proyecto_id, fecha, ingresos, tiempo_horas, conversiones, notas)
            logger_app.info(f"Nueva métrica registrada para proyecto {proyecto_id}")
            
            self.send_response(303)
            self.send_header('Location', f'/proyecto/{proyecto_id}')
            self.end_headers()
            
        except ErrorValidacion as e:
            self.send_error(400, f"Error de validación: {str(e)}")
        except Exception as e:
            logger_app.error(f"Error al crear métrica: {e}", exc_info=True)
            self.send_error(500, "Error interno del servidor")
    
    def handle_actualizar_proyecto(self, proyecto_id: int, data: dict):
        """Actualizar estado de proyecto"""
        try:
            nuevo_estado = data.get('estado', '')
            
            if not nuevo_estado:
                self.send_error(400, "Estado requerido")
                return
            
            db.actualizar_estado_proyecto(proyecto_id, nuevo_estado)
            
            # Redirect a proyecto
            self.send_response(303)
            self.send_header('Location', f'/proyecto/{proyecto_id}')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Error al actualizar proyecto: {str(e)}")

    def handle_responder_decision(self, data: dict):
        """Registrar respuesta a sugerencia de IA"""
        try:
            proyecto_id = int(data.get('proyecto_id', 0))
            tipo = data.get('tipo', 'iterate') # kill, iterate, scale, pause
            justificacion = data.get('justificacion', '')
            accion = data.get('accion', 'aceptada') # aceptada, rechazada, pospuesta
            razon_rechazo = data.get('razon_rechazo', '')

            if proyecto_id <= 0:
                self.send_error(400, "Proyecto inválido")
                return

            # Registrar en tabla de decisiones
            db.registrar_decision(
                proyecto_id=proyecto_id,
                tipo=tipo,
                justificacion=justificacion,
                accion_tomada=accion,
                origen='ia',
                razon_rechazo=razon_rechazo if accion == 'rechazada' else None
            )

            # Si se acepta una decisión drástica, actualizar estado del proyecto
            if accion == 'aceptada':
                nuevo_estado = None
                if tipo == 'kill':
                    nuevo_estado = 'killed'
                elif tipo == 'scale':
                    nuevo_estado = 'winner'
                elif tipo == 'pause':
                    nuevo_estado = 'paused'
                elif tipo == 'iterate':
                    # Podría ser mvp o active, lo dejamos como active si ya empezó
                    # O simplemente no lo tocamos si ya está en un estado válido
                    pass

                if nuevo_estado:
                    db.actualizar_estado_proyecto(proyecto_id, nuevo_estado)

            # Redirect al proyecto
            self.send_response(303)
            self.send_header('Location', f'/proyecto/{proyecto_id}')
            self.end_headers()

        except Exception as e:
            self.send_error(500, f"Error al registrar decisión: {str(e)}")
    
    def handle_iniciar_ciclo(self):
        """Iniciar ciclo 90D manualmente."""
        try:
            # Crear nuevo ciclo
            ciclo_id = db.crear_ciclo_90d()
            logger_app.info(f"Ciclo 90D iniciado manualmente (ID: {ciclo_id})")
            
            # Redirigir al dashboard
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
            
        except Exception as e:
            logger_app.error(f"Error al iniciar ciclo: {e}", exc_info=True)
            self.send_error(500, f"Error al iniciar ciclo: {str(e)}")
    
    def log_message(self, format, *args):
        """Override para logging más limpio"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server():
    """Iniciar servidor HTTP"""
    # Inicializar base de datos si no existe
    db.init_database()
    
    # NO crear ciclo automáticamente - el usuario lo iniciará manualmente
    # desde la interfaz web cuando esté listo
    ciclo = db.obtener_ciclo_activo()
    if ciclo:
        fase = db.calcular_fase_actual(ciclo)
        print(f"✓ Ciclo activo: Día {fase['dia']}/90 - Fase: {fase['nombre']}")
    else:
        print("⏸️  No hay ciclo activo. Inicia tu ciclo desde la interfaz web.")
    
    # Sistema de backup automático
    print("\n🔒 Verificando backups...")
    backup_sistema = bk.SistemaBackup(db.DB_PATH)
    # Iniciar backup automático en hilo separado
    import threading
    threading.Thread(target=bk.ejecutar_backup_automatico, daemon=True).start()
    
    server = HTTPServer((HOST, PORT), Sistema90DHandler)
    logger_app.info(f"Servidor iniciado en http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger_app.info("Servidor detenido por el usuario")
        server.server_close()

if __name__ == '__main__':
    run_server()
