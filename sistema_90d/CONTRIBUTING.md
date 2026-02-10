# Contribuyendo al Sistema 90D

¡Gracias por tu interés en contribuir al Sistema 90D! Este documento proporciona pautas para contribuir al proyecto.

## 🎯 Filosofía del Proyecto

El Sistema 90D se basa en estos principios:

1. **Zero Dependencies**: Solo Python 3.11+ stdlib
2. **Velocidad > Perfección**: Código simple y directo
3. **Minimalismo**: Solo funcionalidades esenciales
4. **Eficiencia**: Bajo uso de recursos

## 🐛 Reportar Bugs

Si encuentras un bug, por favor abre un issue con:

- **Descripción clara** del problema
- **Pasos para reproducir** el bug
- **Comportamiento esperado** vs comportamiento actual
- **Versión de Python** que estás usando
- **Sistema operativo**

## 💡 Proponer Features

Antes de proponer un nuevo feature:

1. **Verifica** que no exista ya un issue similar
2. **Considera** si el feature es esencial para la metodología 90D
3. **Evalúa** si puede implementarse sin dependencias externas

Abre un issue describiendo:
- **Problema** que resuelve el feature
- **Solución propuesta**
- **Alternativas** consideradas
- **Impacto** en el rendimiento/complejidad

## 🔧 Pull Requests

### Proceso

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/mi-feature`)
3. **Implementa** tus cambios
4. **Prueba** que todo funciona correctamente
5. **Commit** con mensajes descriptivos
6. **Push** a tu fork
7. **Abre** un Pull Request

### Estándares de Código

- **PEP 8**: Sigue las convenciones de Python
- **Type Hints**: Usa type hints donde sea posible
- **Docstrings**: Documenta funciones y clases
- **Comentarios**: Explica el "por qué", no el "qué"
- **Tests**: Agrega tests para nuevas funcionalidades

### Ejemplo de Commit

```
feat: agregar exportación de métricas en JSON

- Implementa función exportar_json() en database.py
- Agrega ruta /exportar-json en app.py
- Actualiza documentación en README.md

Closes #42
```

### Tipos de Commits

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formato, sin cambios en código
- `refactor`: Refactorización de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

## 🧪 Testing

Antes de enviar un PR:

```bash
# Ejecutar tests existentes
python3 test_sistema.py
python3 test_dashboard.py
python3 test_decisiones.py

# Verificar que el servidor inicia
python3 app.py &
sleep 2
curl http://localhost:8080
pkill -f "python3 app.py"
```

## 📝 Documentación

Si tu cambio afecta la funcionalidad:

- Actualiza el `README.md`
- Agrega ejemplos de uso si es necesario
- Actualiza docstrings en el código

## ❌ Qué NO Aceptamos

- Dependencias externas (excepto en `requirements-optional.txt`)
- Frameworks pesados (React, Vue, etc.)
- Funcionalidades que complican el flujo básico
- Código sin documentación
- Changes que rompen la compatibilidad sin justificación

## ✅ Qué Buscamos

- Mejoras de rendimiento
- Correcciones de bugs
- Mejoras en la UX
- Mejor documentación
- Tests adicionales
- Optimizaciones de queries SQL

## 🤝 Código de Conducta

- Sé respetuoso y constructivo
- Acepta críticas constructivas
- Enfócate en el código, no en las personas
- Ayuda a otros contribuidores

## 📞 Contacto

Si tienes preguntas, abre un issue con la etiqueta `question`.

---

**¡Gracias por contribuir al Sistema 90D!** 🚀
