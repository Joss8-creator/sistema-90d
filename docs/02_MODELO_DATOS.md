# SUB-PROMPT 02: MODELO DE DATOS Y REGLAS DE DECISIÓN

## CONTEXTO
Sistema 90D local. Persistencia en SQLite. Enfoque eficiencia extrema.

## OBJETIVO
Diseñar esquema de base de datos que:
1. Minimice redundancia sin sacrificar queries rápidas
2. Embeba reglas de decisión como constraints y triggers
3. Permita evolución sin migraciones complejas

---

## ESQUEMA DE DATOS

### Tabla: `config_sistema`
**Propósito:** Configuración global, ciclo 90D actual.

```sql
CREATE TABLE config_sistema (
  clave TEXT PRIMARY KEY,
  valor TEXT NOT NULL,
  actualizado_en INTEGER DEFAULT (unixepoch())
);

-- Datos iniciales obligatorios
INSERT INTO config_sistema (clave, valor) VALUES 
  ('fecha_inicio_ciclo', '2025-01-01'),  -- ISO 8601
  ('proyectos_activos_max', '3'),        -- Límite hard
  ('umbral_kill_dias', '30'),            -- Sin ingresos en X días → kill
  ('umbral_winner_mrr', '1000');         -- MRR mínimo para "winner"
```

**Justificación vs alternativa:**
- Alternativa: Variables en código Python → No editable sin recompilar
- Elegida: Tabla editable → Usuario ajusta umbrales sin tocar código

---

### Tabla: `proyectos`
**Propósito:** Registro maestro de ideas/productos.

```sql
CREATE TABLE proyectos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL UNIQUE,
  hipotesis TEXT NOT NULL,            -- ¿Qué problema resuelve?
  estado TEXT NOT NULL DEFAULT 'idea' 
    CHECK(estado IN ('idea','mvp','active','paused','killed','winner')),
  fecha_inicio INTEGER NOT NULL,      -- unixepoch()
  fecha_kill INTEGER,                 -- NULL si no está killed
  razon_kill TEXT,                    -- Obligatorio si estado=killed
  creado_en INTEGER DEFAULT (unixepoch()),
  
  -- Constraints de negocio
  CHECK(
    (estado = 'killed' AND fecha_kill IS NOT NULL AND razon_kill IS NOT NULL)
    OR
    (estado != 'killed' AND fecha_kill IS NULL)
  )
);

-- Índices para queries frecuentes
CREATE INDEX idx_proyectos_estado ON proyectos(estado);
CREATE INDEX idx_proyectos_fecha_inicio ON proyectos(fecha_inicio);
```

**Decisiones clave:**
1. **Estado como ENUM simulado**: Check constraint evita estados inválidos
2. **Constraint de kill**: Fuerza documentar razón (anti-alucinación)
3. **Fechas en unixepoch**: Comparaciones numéricas rápidas, cero parsing

**Complejidad:** 
- Inserción: O(1)
- Filtro por estado: O(log n) con índice

---

### Tabla: `metricas`
**Propósito:** Series temporales de métricas por proyecto.

```sql
CREATE TABLE metricas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proyecto_id INTEGER NOT NULL,
  fecha INTEGER NOT NULL,             -- unixepoch()
  ingresos REAL DEFAULT 0,            -- USD (o moneda base)
  tiempo_invertido REAL DEFAULT 0,    -- Horas
  conversiones INTEGER DEFAULT 0,     -- Número de conversiones
  trafico_fuente TEXT,                -- 'organic', 'paid', 'referral', etc.
  friccion_principal TEXT,            -- Texto libre (para análisis IA)
  registrado_en INTEGER DEFAULT (unixepoch()),
  
  FOREIGN KEY(proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  
  -- Evitar duplicados accidentales (mismo día, mismo proyecto)
  UNIQUE(proyecto_id, fecha)
);

CREATE INDEX idx_metricas_proyecto ON metricas(proyecto_id);
CREATE INDEX idx_metricas_fecha ON metricas(fecha);
```

**Decisiones clave:**
1. **Granularidad diaria**: UNIQUE por (proyecto, fecha) evita datos duplicados
2. **CASCADE delete**: Si matas proyecto, limpias métricas automáticamente
3. **Campos opcionales con DEFAULT 0**: Permite registro parcial sin NULLs

**Complejidad:**
- Inserción: O(1)
- Agregación por proyecto: O(n) donde n = métricas del proyecto (asumido <100)

---

### Tabla: `decisiones`
**Propósito:** Log inmutable de decisiones tomadas (humano + IA).

```sql
CREATE TABLE decisiones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proyecto_id INTEGER NOT NULL,
  tipo TEXT NOT NULL CHECK(tipo IN ('kill','iterate','scale','pause')),
  justificacion TEXT NOT NULL,       -- Métricas que llevaron a la decisión
  origen TEXT NOT NULL CHECK(origen IN ('humano','ia','mixto')),
  fecha INTEGER NOT NULL DEFAULT (unixepoch()),
  
  FOREIGN KEY(proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
);

CREATE INDEX idx_decisiones_proyecto ON decisiones(proyecto_id);
```

**Por qué existe:**
- Anti-alucinación: Obliga a documentar RAZONES, no solo conclusiones
- Auditoría: Permite ver historial de decisiones erróneas
- Aprendizaje: Entrenamiento futuro de heurísticas

**Complejidad:** O(1) inserción, O(n) lectura (n = decisiones por proyecto, asumido <10)

---

### Tabla: `prompts_ia` (Opcional en MVP, crítico en Fase 2)
**Propósito:** Versionado de prompts exportables.

```sql
CREATE TABLE prompts_ia (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL UNIQUE,       -- Ej: "analisis_semanal_v1"
  contenido TEXT NOT NULL,           -- Template con {{variables}}
  activo INTEGER DEFAULT 1,          -- 0 = deprecated
  creado_en INTEGER DEFAULT (unixepoch())
);

-- Prompt inicial hardcoded
INSERT INTO prompts_ia (nombre, contenido) VALUES 
('analisis_semanal_v1', 
'CONTEXTO DEL SISTEMA 90D
========================
Día: {{dia_actual}}/90
Fase: {{fase_actual}}

PROYECTOS ACTIVOS
==================
{{#proyectos}}
- {{nombre}}: ${{ingresos_total}} en {{horas_total}}h
  Estado: {{estado}}
  Última métrica: {{ultima_fecha}}
{{/proyectos}}

INSTRUCCIÓN
===========
Analiza según Documento_Base.txt.
Recomienda kill/iterate/scale con datos, no intuición.
');
```

**Por qué diferible:**
En MVP, el template puede estar hardcoded en Python. Solo se mueve a DB si usuario quiere editar prompts sin tocar código.

---

## REGLAS DE DECISIÓN EMBEBIDAS (TRIGGERS)

### Trigger: Auto-kill si sin ingresos en N días
```sql
CREATE TRIGGER auto_kill_sin_ingresos
AFTER INSERT ON metricas
FOR EACH ROW
WHEN (
  SELECT COUNT(*) FROM metricas m
  WHERE m.proyecto_id = NEW.proyecto_id
    AND m.fecha >= (unixepoch() - (SELECT valor FROM config_sistema WHERE clave='umbral_kill_dias') * 86400)
    AND m.ingresos > 0
) = 0
BEGIN
  UPDATE proyectos 
  SET estado = 'killed',
      fecha_kill = unixepoch(),
      razon_kill = 'Auto-kill: Sin ingresos en ' || (SELECT valor FROM config_sistema WHERE clave='umbral_kill_dias') || ' días'
  WHERE id = NEW.proyecto_id
    AND estado NOT IN ('killed', 'winner');
END;
```

**Crítica a esta decisión:**
- **PRO:** Automatiza decisión obvia, reduce carga mental
- **CONTRA:** Puede matar proyectos con ingresos irregulares legítimos
- **SOLUCIÓN:** Usuario puede:
  1. Ajustar `umbral_kill_dias` en config
  2. Revertir manualmente el estado a `paused` si fue error

**Complejidad:** O(n) por cada inserción de métrica (n = métricas recientes del proyecto)

---

### Trigger: Alerta si concentración de ingresos >80% en un proyecto
```sql
CREATE TRIGGER alerta_concentracion
AFTER UPDATE ON metricas
BEGIN
  SELECT RAISE(ABORT, 'ALERTA: >80% ingresos en un proyecto')
  WHERE (
    SELECT MAX(ingresos_proyecto) * 1.0 / SUM(ingresos_proyecto)
    FROM (
      SELECT SUM(m.ingresos) AS ingresos_proyecto
      FROM metricas m
      JOIN proyectos p ON p.id = m.proyecto_id
      WHERE p.estado IN ('active','winner')
      GROUP BY m.proyecto_id
    )
  ) > 0.8;
END;
```

**PROBLEMA DETECTADO:** RAISE(ABORT) frena la inserción. 
**SOLUCIÓN MEJOR:** Crear tabla `alertas` y registrar sin bloquear.

```sql
-- Versión corregida
CREATE TABLE alertas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tipo TEXT NOT NULL,
  mensaje TEXT NOT NULL,
  fecha INTEGER DEFAULT (unixepoch()),
  resuelta INTEGER DEFAULT 0
);

CREATE TRIGGER alerta_concentracion
AFTER UPDATE ON metricas
BEGIN
  INSERT INTO alertas (tipo, mensaje)
  SELECT 'concentracion_ingresos', 
         'Proyecto ' || p.nombre || ' representa ' || 
         CAST(ROUND(ingresos_proyecto * 100.0 / total, 2) AS TEXT) || '% de ingresos totales'
  FROM (
    SELECT m.proyecto_id, p.nombre, SUM(m.ingresos) AS ingresos_proyecto,
           (SELECT SUM(ingresos) FROM metricas) AS total
    FROM metricas m
    JOIN proyectos p ON p.id = m.proyecto_id
    WHERE p.estado IN ('active','winner')
    GROUP BY m.proyecto_id
  ) AS stats
  WHERE ingresos_proyecto * 1.0 / total > 0.8;
END;
```

---

## VISTAS CALCULADAS (PERFORMANCE)

### Vista: Resumen de proyectos
```sql
CREATE VIEW v_resumen_proyectos AS
SELECT 
  p.id,
  p.nombre,
  p.estado,
  COALESCE(SUM(m.ingresos), 0) AS ingresos_total,
  COALESCE(SUM(m.tiempo_invertido), 0) AS horas_total,
  CASE 
    WHEN SUM(m.tiempo_invertido) > 0 
    THEN ROUND(SUM(m.ingresos) / SUM(m.tiempo_invertido), 2)
    ELSE 0 
  END AS roi_por_hora,
  COUNT(m.id) AS metricas_registradas,
  MAX(m.fecha) AS ultima_metrica_fecha
FROM proyectos p
LEFT JOIN metricas m ON m.proyecto_id = p.id
GROUP BY p.id;
```

**Justificación:**
- Evita queries complejas en Python
- Dashboard usa `SELECT * FROM v_resumen_proyectos WHERE estado='active'`

**Complejidad:** O(n*m) donde n=proyectos, m=métricas. Acceptable con índices.

---

## COMPARATIVA VS SOLUCIÓN "MODERNA"

### Solución estándar (Django + PostgreSQL + ORM)
- **Ventajas:** Migraciones automáticas, admin panel
- **Desventajas:** 
  - 50MB+ de dependencias
  - Servidor DB externo
  - ORM overhead en queries simples (2-3x más lento)

### Solución elegida (SQLite + SQL directo)
- **Ventajas:**
  - Archivo único (<1MB con 1000 registros)
  - Queries óptimas escritas a mano
  - Cero configuración
- **Desventajas:**
  - Sin migraciones automáticas (requiere scripting manual)
  - Sin concurrencia (irrelevante: 1 usuario)

---

## OPTIMIZACIONES CONSIDERADAS PERO NO APLICADAS

### 1. Particionado de tabla `metricas` por fecha
**Razón:** SQLite no soporta particiones nativas. Complejidad no justificada para <10K registros.

### 2. Índices compuestos en (proyecto_id, fecha)
**Razón:** Índices separados son suficientes. Query planner de SQLite es eficiente.

### 3. Desnormalización de `ingresos_total` en `proyectos`
**Razón:** Agregación en tiempo real es <10ms. Mantener consistencia es más crítico.

---

## ENTREGABLE ESPERADO

1. **Script SQL completo** con:
   - DDL (CREATE TABLE)
   - Índices
   - Triggers
   - Vistas
   - Datos iniciales

2. **Script Python `database.py`** con funciones:
   ```python
   # /sistema_90d/database.py
   def init_db(db_path: str) -> None
   def insert_proyecto(...) -> int
   def insert_metrica(...) -> None
   def get_proyectos_activos() -> list[dict]
   def get_alertas_pendientes() -> list[dict]
   ```

**Siguiente paso:** Si este modelo es aprobado, ejecutar `03_INTERFAZ_USUARIO.md`
