# ANÁLISIS CRÍTICO Y MEJORAS DEL SISTEMA 90D

## DEBILIDADES DETECTADAS EN EL DISEÑO ACTUAL

### 🚨 PROBLEMA 1: Fricción en el flujo de IA (CRÍTICO)

**Situación actual:**
```
Usuario → Generar prompt → Copiar → Pegar en ChatGPT → Esperar respuesta → 
Copiar JSON → Volver al sistema → Pegar → Validar → Guardar
```
**8 pasos manuales.** Esto viola el principio de "reducir fricción".

**Impacto:**
- Usuario lo hace 1-2 veces, luego abandona el ritual semanal
- El sistema se vuelve un "registro de métricas" sin análisis

**MEJORA PROPUESTA:**

#### Opción A: Integración API opcional (recomendada)
```python
# /sistema_90d/integracion_ia.py

class IntegradorIA:
    """
    Capa de abstracción que OPCIONALMENTE llama APIs.
    Si no hay API key configurada, genera prompt para copy/paste.
    """
    
    def __init__(self, db_path: str):
        self.db = db_path
        self.api_key = self._cargar_api_key()
        self.proveedor = self._detectar_proveedor()
    
    def _cargar_api_key(self) -> str | None:
        """Lee API key de variable de entorno o config."""
        import os
        return os.getenv('CLAUDE_API_KEY') or os.getenv('OPENAI_API_KEY')
    
    def _detectar_proveedor(self) -> str:
        """Detecta qué proveedor usar basado en API key."""
        import os
        if os.getenv('CLAUDE_API_KEY'):
            return 'anthropic'
        elif os.getenv('OPENAI_API_KEY'):
            return 'openai'
        return 'manual'  # Fallback a copy/paste
    
    def analizar(self, tipo: str = 'semanal') -> dict:
        """
        Ejecuta análisis. Si hay API key, llama automáticamente.
        Si no, retorna prompt para copy/paste.
        """
        from generador_prompts import GeneradorPrompts
        
        generador = GeneradorPrompts(self.db)
        prompt = generador.generar_analisis_semanal()
        
        if self.proveedor == 'manual':
            return {
                'modo': 'manual',
                'prompt': prompt,
                'instrucciones': 'Copia este prompt y pégalo en tu IA preferida'
            }
        
        # Llamada API automática
        if self.proveedor == 'anthropic':
            return self._llamar_claude(prompt)
        elif self.proveedor == 'openai':
            return self._llamar_openai(prompt)
    
    def _llamar_claude(self, prompt: str) -> dict:
        """Llama a Claude API."""
        import anthropic  # Dependencia OPCIONAL
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parsear JSON de la respuesta
        import json
        respuesta_json = response.content[0].text
        
        # Extraer JSON si está envuelto en markdown
        if '```json' in respuesta_json:
            respuesta_json = respuesta_json.split('```json')[1].split('```')[0]
        
        return {
            'modo': 'automatico',
            'proveedor': 'anthropic',
            'datos': json.loads(respuesta_json),
            'costo_estimado': len(prompt) * 0.000003  # $3 por millón tokens
        }
```

**Ventajas:**
- Mantiene flexibilidad (funciona sin API key)
- Reduce fricción de 8 pasos a 1 clic
- Usuario decide si gasta $ en APIs o usa gratis con copy/paste

**Desventajas agregadas:**
- +1 dependencia opcional (`anthropic` o `openai`)
- +~10MB si se instala SDK

**Mitigación:**
```python
# requirements.txt modificado
jinja2==3.1.2

# requirements-optional.txt (nuevo archivo)
anthropic==0.40.0  # Solo si usuario quiere integración automática
openai==1.54.0     # Alternativa
```

**Trade-off aceptable:** Usuario elige entre eficiencia (API) vs cero dependencias (manual).

---

### 🚨 PROBLEMA 2: Motor de métricas asume data completa (MEDIO)

**Código actual:**
```python
def detectar_kill_roi_negativo(proyecto_id, coste_hora_estimado, db):
    roi_por_hora = total_ingresos / total_horas
    
    if roi_por_hora < coste_hora_estimado:
        return Señal(..., decision_sugerida='kill')
```

**Fallo silencioso:**
Si `total_horas == 0` → Division by zero o señal nunca se dispara.

**Peor caso:**
Usuario registra proyecto pero nunca registra tiempo invertido → ROI parece infinito → Nunca sugiere kill aunque sea basura.

**MEJORA PROPUESTA:**

```python
def detectar_kill_roi_negativo(proyecto_id, coste_hora_estimado, db):
    cursor = db.execute("""
        SELECT 
            SUM(ingresos) AS total_ingresos,
            SUM(tiempo_invertido) AS total_horas,
            COUNT(*) AS metricas_registradas
        FROM metricas
        WHERE proyecto_id = ?
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    total_ingresos, total_horas, metricas_count = row
    
    # VALIDACIÓN 1: ¿Hay datos suficientes?
    if metricas_count < 3:
        return Señal(
            proyecto_id=proyecto_id,
            tipo="datos_insuficientes",
            severidad='info',
            mensaje=f"Solo {metricas_count} métricas registradas. Necesitas al menos 3 para análisis de ROI.",
            datos_soporte={'metricas_count': metricas_count},
            decision_sugerida='continuar'
        )
    
    # VALIDACIÓN 2: ¿Se registró tiempo?
    if total_horas == 0 or total_horas is None:
        return Señal(
            proyecto_id=proyecto_id,
            tipo="sin_tiempo_registrado",
            severidad='warning',
            mensaje="No has registrado tiempo invertido. Sin esto, no puedo calcular ROI real.",
            datos_soporte={'ingresos': total_ingresos},
            decision_sugerida='continuar'
        )
    
    # Análisis normal
    roi_por_hora = total_ingresos / total_horas
    
    if roi_por_hora < coste_hora_estimado:
        # ... (código original)
```

**Mejora adicional: Heurística de tiempo estimado**

Si usuario nunca registra tiempo pero tiene métricas:
```python
def estimar_tiempo_minimo(proyecto_id, db):
    """
    Estima tiempo mínimo basado en estado del proyecto.
    Útil cuando usuario olvida registrar horas.
    """
    cursor = db.execute("""
        SELECT estado, 
               (unixepoch('now') - fecha_inicio) / 86400 AS dias_desde_inicio
        FROM proyectos
        WHERE id = ?
    """, (proyecto_id,))
    
    estado, dias = cursor.fetchone()
    
    # Heurística conservadora
    if estado == 'idea':
        return dias * 0.5  # 30 min/día promedio en fase idea
    elif estado == 'mvp':
        return dias * 2    # 2 horas/día en desarrollo MVP
    elif estado == 'active':
        return dias * 1    # 1 hora/día mantenimiento
    
    return 0
```

---

### 🚨 PROBLEMA 3: Sin validación de reglas contradictorias (MEDIO)

**Escenario:**
```
Día 30: Sistema sugiere KILL (sin ingresos en 30 días)
Día 31: Usuario registra $500 de ingresos
Día 32: Sistema aún muestra alerta de KILL antigua
```

**Causa:** Las señales se generan en cada análisis pero las alertas viejas no se limpian.

**MEJORA PROPUESTA:**

```python
# /sistema_90d/motor_metricas.py

class MotorMetricas:
    def analizar_proyecto(self, proyecto_id: int) -> List[Señal]:
        señales = []
        
        # Ejecutar reglas...
        # ...
        
        # NUEVO: Limpiar alertas contradictorias
        self._limpiar_alertas_obsoletas(proyecto_id, señales)
        
        return señales
    
    def _limpiar_alertas_obsoletas(self, proyecto_id: int, señales_nuevas: List[Señal]):
        """
        Marca como resueltas alertas antiguas que ya no aplican.
        
        Ejemplo: Si antes había alerta "sin_ingresos" pero ahora hay ingresos,
        la alerta antigua se marca como resuelta automáticamente.
        """
        # Obtener alertas pendientes de este proyecto
        cursor = self.db.execute("""
            SELECT id, tipo FROM alertas
            WHERE proyecto_id = ? AND resuelta = 0
        """, (proyecto_id,))
        
        alertas_pendientes = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Tipos de señales actuales
        tipos_actuales = {s.tipo for s in señales_nuevas}
        
        # Marcar como resueltas las que ya no aplican
        for tipo_antiguo, alerta_id in alertas_pendientes.items():
            if tipo_antiguo not in tipos_actuales:
                self.db.execute("""
                    UPDATE alertas 
                    SET resuelta = 1, 
                        fecha_resolucion = unixepoch('now'),
                        resolucion_automatica = 1
                    WHERE id = ?
                """, (alerta_id,))
        
        self.db.commit()
```

**Schema update necesario:**
```sql
ALTER TABLE alertas ADD COLUMN fecha_resolucion INTEGER;
ALTER TABLE alertas ADD COLUMN resolucion_automatica INTEGER DEFAULT 0;
ALTER TABLE alertas ADD COLUMN proyecto_id INTEGER;  -- Si no existe
```

---

### 🚨 PROBLEMA 4: Falta de persistencia en decisiones del usuario (CRÍTICO)

**Situación actual:**
IA sugiere "KILL proyecto X" → Usuario ignora la sugerencia → Próxima semana, IA vuelve a sugerir lo mismo.

**Resultado:** Usuario se frustra con recomendaciones repetitivas.

**MEJORA PROPUESTA:**

```python
# Nuevo campo en tabla decisiones
CREATE TABLE decisiones (
    -- ... campos existentes ...
    accion_tomada TEXT CHECK(accion_tomada IN ('aceptada', 'rechazada', 'pospuesta')),
    razon_rechazo TEXT  -- Si usuario rechazó la sugerencia, ¿por qué?
);
```

**Flujo mejorado:**
```python
# En interfaz de ritual semanal
@app.route('/decisiones/responder', methods=['POST'])
def responder_decision_ia():
    """
    Usuario indica si acepta/rechaza sugerencia de IA.
    """
    proyecto_id = request.form['proyecto_id']
    decision_sugerida = request.form['decision']  # kill, iterate, scale
    accion = request.form['accion']  # aceptar, rechazar, posponer
    razon = request.form.get('razon', '')
    
    db = get_db()
    
    if accion == 'aceptar':
        # Ejecutar la decisión
        if decision_sugerida == 'kill':
            db.execute("""
                UPDATE proyectos 
                SET estado = 'killed', 
                    fecha_kill = unixepoch(),
                    razon_kill = ?
                WHERE id = ?
            """, (f"Aceptada sugerencia IA: {razon}", proyecto_id))
        
        # Registrar decisión
        db.execute("""
            INSERT INTO decisiones (proyecto_id, tipo, justificacion, origen, accion_tomada)
            VALUES (?, ?, ?, 'ia', 'aceptada')
        """, (proyecto_id, decision_sugerida, razon))
    
    elif accion == 'rechazar':
        # Registrar rechazo (evita que IA insista)
        db.execute("""
            INSERT INTO decisiones (proyecto_id, tipo, justificacion, origen, accion_tomada, razon_rechazo)
            VALUES (?, ?, ?, 'ia', 'rechazada', ?)
        """, (proyecto_id, decision_sugerida, 'Sugerencia rechazada por usuario', razon))
    
    db.commit()
    return redirect('/ritual-semanal')
```

**Generador de prompts mejorado:**
```python
def generar_analisis_semanal(self):
    # ... código existente ...
    
    # NUEVO: Incluir contexto de decisiones rechazadas
    cursor = self.db.execute("""
        SELECT p.nombre, d.tipo, d.razon_rechazo, d.fecha
        FROM decisiones d
        JOIN proyectos p ON p.id = d.proyecto_id
        WHERE d.origen = 'ia' 
          AND d.accion_tomada = 'rechazada'
          AND d.fecha >= unixepoch('now', '-30 days')
    """)
    
    decisiones_rechazadas = cursor.fetchall()
    
    contexto['decisiones_rechazadas_recientes'] = decisiones_rechazadas
    
    # El prompt incluirá:
    # "DECISIONES RECHAZADAS RECIENTEMENTE:
    #  - Proyecto X: Sugeriste KILL, usuario rechazó porque 'esperando contrato grande'
    #  → No vuelvas a sugerir KILL para este proyecto a menos que haya cambio drástico"
```

---

### 🚨 PROBLEMA 5: Sin backup automático de la base de datos (ALTO)

**Riesgo:**
Usuario trabaja 60 días registrando métricas → Corrupción de DB o eliminación accidental → Pierde todo.

**MEJORA PROPUESTA:**

```python
# /sistema_90d/backup.py

from pathlib import Path
from datetime import datetime
import shutil
import gzip

class SistemaBackup:
    """
    Gestiona backups automáticos de la base de datos.
    """
    
    def __init__(self, db_path: str, backup_dir: str = 'data/backups'):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def crear_backup(self, comprimir: bool = True) -> Path:
        """
        Crea backup de la DB con timestamp.
        
        Complejidad: O(n) donde n = tamaño de DB (típicamente <5MB)
        Tiempo: <100ms para DB de 5MB
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"sistema_{timestamp}.db"
        
        if comprimir:
            backup_name += '.gz'
        
        backup_path = self.backup_dir / backup_name
        
        if comprimir:
            with open(self.db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(self.db_path, backup_path)
        
        return backup_path
    
    def limpiar_backups_antiguos(self, max_backups: int = 30):
        """
        Mantiene solo los N backups más recientes.
        """
        backups = sorted(self.backup_dir.glob('sistema_*.db*'))
        
        if len(backups) > max_backups:
            for backup in backups[:-max_backups]:
                backup.unlink()
    
    def backup_automatico_si_necesario(self):
        """
        Crea backup solo si el último tiene >24 horas.
        Evita backups redundantes.
        """
        backups = sorted(self.backup_dir.glob('sistema_*.db*'))
        
        if not backups:
            self.crear_backup()
            return
        
        ultimo_backup = backups[-1]
        tiempo_desde_ultimo = datetime.now().timestamp() - ultimo_backup.stat().st_mtime
        
        # Si han pasado >24 horas, crear nuevo backup
        if tiempo_desde_ultimo > 86400:
            self.crear_backup()
            self.limpiar_backups_antiguos()
```

**Integración en app.py:**
```python
# Al iniciar el servidor
if __name__ == '__main__':
    from database import init_db
    from backup import SistemaBackup
    
    db_path = 'data/sistema.db'
    
    if not Path(db_path).exists():
        init_db()
    
    # Backup automático al iniciar
    backup = SistemaBackup(db_path)
    backup.backup_automatico_si_necesario()
    
    server = HTTPServer(('localhost', 8080), SistemaHandler)
    print("Sistema 90D corriendo en http://localhost:8080")
    print(f"Backups en: data/backups/")
    server.serve_forever()
```

**Overhead:** +50 líneas de código, <100ms al iniciar, ~1-2MB espacio por backup comprimido.

---

### 🚨 PROBLEMA 6: Interfaz no guía proactivamente (MEDIO)

**Situación actual:**
Usuario abre dashboard → Ve lista de proyectos → No sabe qué hacer ahora.

**Falta:** Guía contextual basada en fase y estado.

**MEJORA PROPUESTA:**

```python
# /sistema_90d/guia_contextual.py

class GuiaContextual:
    """
    Genera sugerencias de siguiente acción basadas en contexto.
    """
    
    @staticmethod
    def obtener_siguiente_accion(db: sqlite3.Connection) -> dict:
        """
        Retorna la acción más importante que el usuario debería hacer ahora.
        """
        # 1. ¿Ritual diario pendiente?
        cursor = db.execute("""
            SELECT COUNT(*) FROM rituales_completados
            WHERE tipo = 'diario' AND date(fecha, 'unixepoch') = date('now')
        """)
        if cursor.fetchone()[0] == 0:
            return {
                'tipo': 'ritual',
                'urgencia': 'alta',
                'titulo': '⏰ Ritual diario pendiente',
                'descripcion': 'Registra las métricas del día antes de continuar',
                'accion': '/ritual-diario',
                'tiempo_estimado': '5 minutos'
            }
        
        # 2. ¿Hay alertas críticas sin resolver?
        cursor = db.execute("""
            SELECT COUNT(*) FROM alertas
            WHERE resuelta = 0 AND severidad = 'critical'
        """)
        if cursor.fetchone()[0] > 0:
            return {
                'tipo': 'alerta',
                'urgencia': 'alta',
                'titulo': '🚨 Alertas críticas detectadas',
                'descripcion': 'Proyectos que necesitan decisión inmediata',
                'accion': '/alertas',
                'tiempo_estimado': '10 minutos'
            }
        
        # 3. ¿Proyectos sin métricas en >7 días?
        cursor = db.execute("""
            SELECT p.id, p.nombre FROM proyectos p
            WHERE p.estado IN ('active', 'mvp')
              AND NOT EXISTS (
                SELECT 1 FROM metricas m 
                WHERE m.proyecto_id = p.id 
                  AND m.fecha >= unixepoch('now', '-7 days')
              )
            LIMIT 1
        """)
        proyecto_abandonado = cursor.fetchone()
        if proyecto_abandonado:
            return {
                'tipo': 'proyecto_abandonado',
                'urgencia': 'media',
                'titulo': f'📊 {proyecto_abandonado[1]} sin actividad',
                'descripcion': 'Sin métricas en 7+ días. ¿Deberías pausarlo o matarlo?',
                'accion': f'/proyecto/{proyecto_abandonado[0]}',
                'tiempo_estimado': '2 minutos'
            }
        
        # 4. ¿Estás en límite de proyectos activos?
        cursor = db.execute("""
            SELECT COUNT(*) FROM proyectos WHERE estado IN ('active', 'mvp')
        """)
        proyectos_activos = cursor.fetchone()[0]
        
        cursor = db.execute("""
            SELECT valor FROM config_sistema WHERE clave = 'proyectos_activos_max'
        """)
        limite = int(cursor.fetchone()[0])
        
        if proyectos_activos >= limite:
            return {
                'tipo': 'limite_alcanzado',
                'urgencia': 'media',
                'titulo': f'⚠️ Límite de proyectos alcanzado ({proyectos_activos}/{limite})',
                'descripcion': 'Mata o pausa un proyecto antes de iniciar otro',
                'accion': '/proyectos',
                'tiempo_estimado': '15 minutos'
            }
        
        # 5. Default: Todo bien, continuar trabajando
        return {
            'tipo': 'normal',
            'urgencia': 'baja',
            'titulo': '✅ Todo al día',
            'descripcion': 'Continúa trabajando en tus proyectos activos',
            'accion': None,
            'tiempo_estimado': None
        }
```

**Integración en dashboard:**
```html
<!-- En templates/dashboard.html -->
{% set siguiente_accion = obtener_siguiente_accion() %}

<aside class="siguiente-accion siguiente-accion-{{ siguiente_accion.urgencia }}">
  <h2>{{ siguiente_accion.titulo }}</h2>
  <p>{{ siguiente_accion.descripcion }}</p>
  
  {% if siguiente_accion.accion %}
    <a href="{{ siguiente_accion.accion }}" class="btn-primary">
      Hacerlo ahora ({{ siguiente_accion.tiempo_estimado }})
    </a>
  {% endif %}
</aside>
```

---

## RESUMEN DE MEJORAS PROPUESTAS

| # | Mejora | Impacto | Complejidad | Prioridad |
|---|--------|---------|-------------|-----------|
| 1 | Integración API opcional | Alto (reduce fricción 8→1 pasos) | Media (+200 líneas) | 🔴 CRÍTICA |
| 2 | Validación de datos en motor | Alto (evita falsos positivos) | Baja (+50 líneas) | 🔴 CRÍTICA |
| 3 | Limpieza automática de alertas | Medio (menos ruido) | Baja (+30 líneas) | 🟡 IMPORTANTE |
| 4 | Persistencia de decisiones rechazadas | Alto (IA aprende) | Media (+100 líneas) | 🔴 CRÍTICA |
| 5 | Backup automático | Alto (protege datos) | Baja (+50 líneas) | 🟡 IMPORTANTE |
| 6 | Guía contextual | Medio (mejora UX) | Media (+150 líneas) | 🟢 DESEABLE |

**Total líneas adicionales:** ~580 líneas (~23% más código)

---

## MEJORAS ADICIONALES (BONUS)

### 7. Export de datos a CSV
```python
@app.route('/exportar/csv')
def exportar_csv():
    """Exporta métricas a CSV para análisis externo (Excel, Google Sheets)."""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    cursor = db.execute("""
        SELECT p.nombre, m.fecha, m.ingresos, m.tiempo_invertido, m.conversiones
        FROM metricas m
        JOIN proyectos p ON p.id = m.proyecto_id
        ORDER BY m.fecha DESC
    """)
    
    writer.writerow(['Proyecto', 'Fecha', 'Ingresos', 'Horas', 'Conversiones'])
    writer.writerows(cursor.fetchall())
    
    # Retornar como descarga
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=metricas.csv'
    return response
```

### 8. Detección de "proyectos zombie"
```python
def detectar_proyectos_zombie(db):
    """
    Proyectos activos sin decisión tomada en >30 días.
    Usuario está procrastinando kill/iterate/scale.
    """
    cursor = db.execute("""
        SELECT p.id, p.nombre, 
               (unixepoch('now') - MAX(COALESCE(d.fecha, p.creado_en))) / 86400 AS dias_sin_decision
        FROM proyectos p
        LEFT JOIN decisiones d ON d.proyecto_id = p.id
        WHERE p.estado IN ('active', 'mvp')
        GROUP BY p.id
        HAVING dias_sin_decision > 30
    """)
    
    return cursor.fetchall()
```

### 9. Simulador de escenarios
```python
def simular_roi_futuro(proyecto_id, meses=6):
    """
    Proyecta ROI futuro asumiendo crecimiento lineal actual.
    Útil para decidir si vale la pena escalar.
    """
    # Calcular tasa de crecimiento mensual
    # Proyectar ingresos futuros
    # Estimar tiempo invertido necesario
    # Retornar ROI proyectado
```

---

## PROPUESTA DE IMPLEMENTACIÓN DE MEJORAS

### FASE 1 (CRÍTICAS - Implementar YA)
1. Validación de datos en motor (2h)
2. Backup automático (1h)
3. Persistencia de decisiones rechazadas (3h)

**Total:** 6 horas de desarrollo adicional

### FASE 2 (IMPORTANTES - Implementar en Sprint 2)
4. Integración API opcional (6h)
5. Limpieza automática de alertas (2h)

**Total:** 8 horas

### FASE 3 (DESEABLES - Implementar si hay tiempo)
6. Guía contextual (4h)
7. Export CSV (1h)
8. Detección zombies (1h)

**Total:** 6 horas

---
