# Validación de la base

Entorno probado: Linux, Python 3.12.14, PyQt6 6.11.0, Qt 6.11.0, Flex 2.6.4 y GCC.
La GUI se ejecutó con Qt offscreen y se revisaron las capturas generadas.

Resultado: **20 pruebas aprobadas, 0 fallos, 0 omitidas** con Flex/GCC disponibles.

- Arranque de las tres pestañas.
- Botón Analizar de Python: actualización de tablas y limpieza al editar.
- Ausencia simulada de Flex: mensaje comprensible y Python sigue disponible.
- Análisis Python de un programa conocido y errores por caracteres inválidos.
- Ejecución de los ejemplos Python recibidos sin fallo de integración.
- Lectura de Grammar con sus objetos Symbol y Production.
- Rechazo de símbolos desconocidos y símbolo inicial inválido.
- FOLLOW esperado para expresiones, D -> D D, arreglos S -> T V ; y sufijos anulables.
- Validación del contrato de FIRST con terminales incorrectos.
- Lectura de TSV sin interpretar comillas de lexemas como comillas CSV.
- Compilación real de la fuente Flex incluida y ejecución del ejemplo recibido.
- Análisis sucesivos sin reciclar TSV anteriores.
- Error controlado al superar 5000 tokens.
- Tabulación dentro de cadena sin desplazar columnas de resultados.
- Error de compilación que impide usar un ejecutable anterior en esa sesión.

También se verificó el flujo real Compilar/Analizar de la pestaña Flex, con el
programa iniciado desde un directorio diferente a la raíz del proyecto. Se
capturaron las tres pestañas en `capturas/`. Se comprobó la sintaxis de los
archivos Python.

Límites: no se probó en el equipo Windows ni se auditó toda la
semántica léxica de Pascal. Los FIRST utilizados en las pruebas de
FOLLOW son conjuntos esperados escritos explícitamente para esas gramáticas.

Comando reproducible (desde la raíz del proyecto):

```bash
python -m unittest discover -s TESTS -v
```
