# USER_GUIDE.md — OpenLogi RFID IoT ML

**Aplicación web:** https://openlogi-rfid-iot-demo-ml.streamlit.app/  
**Repositorio:** https://github.com/antoniot73/openlogi-rfid-iot-demo-ml  
**Proyecto:** OpenLogi RFID/IoT Demo  
**Caso de uso:** e-commerce / retail supply chain  
**Tipo de solución:** demo académica y técnica de torre de control logística con analítica predictiva.  
**Autor:** Antonio Nicolás Toro González  
**Programa académico:** Maestría en Inteligencia Artificial para la Transformación Digital

---

## 1. Propósito de la aplicación

**OpenLogi RFID IoT ML** es una aplicación web desarrollada en Streamlit para demostrar cómo una operación logística de e-commerce/retail puede visualizarse como una torre de control integrada.

La aplicación combina:

- datos reales procesados del dataset **DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS**;
- eventos RFID simulados;
- eventos IoT simulados;
- inventario WMS sintético;
- visualizaciones ejecutivas;
- un modelo de Machine Learning para estimar riesgo de entrega tardía.

El objetivo no es reemplazar un sistema productivo WMS, TMS, RFID o IoT, sino demostrar una arquitectura funcional, reproducible y desplegada en la web con recursos abiertos y gratuitos.

---

## 2. Alcance funcional

La aplicación permite explorar una operación logística mediante siete bloques principales:

1. **Resumen ejecutivo**
2. **Pedidos y entregas**
3. **RFID simulado**
4. **IoT simulado**
5. **Inventario**
6. **Modelo predictivo**
7. **Dataset y documentación**

Cada bloque aparece como una pestaña independiente dentro de la aplicación.

---

## 3. Datos reales y capas simuladas

### 3.1 Datos reales derivados del dataset DataCo

La aplicación utiliza datos procesados relacionados con:

- pedidos;
- líneas de pedido;
- productos;
- categorías;
- departamentos;
- ventas;
- utilidad;
- fechas de orden;
- fechas de envío;
- modos de envío;
- estados de entrega;
- riesgo de entrega tardía;
- mercado;
- región;
- país;
- ciudad destino.

Estos datos alimentan las vistas de pedidos, ventas, entregas, riesgo tardío y el modelo predictivo.

### 3.2 Capas simuladas generadas por OpenLogi

Como el dataset original no contiene eventos RFID reales, sensores IoT reales ni stock físico real, OpenLogi genera capas sintéticas para representar la lógica funcional de esas tecnologías:

| Capa simulada | Propósito |
|---|---|
| RFID simulado | Representar trazabilidad por pedido, producto, lector, antena, ubicación y RSSI. |
| IoT simulado | Representar monitoreo de temperatura, humedad, vibración y alertas operativas. |
| Inventario WMS sintético | Representar stock, demanda promedio, punto de reorden y reabastecimiento sugerido. |

---

## 4. Archivos que alimentan la aplicación

La aplicación carga los siguientes archivos desde el repositorio:

### 4.1 Datos procesados

```text
data/processed/orders_clean_sample.csv
data/processed/orders_agg_daily.csv
data/processed/rfid_events_demo.csv
data/processed/iot_events_demo.csv
data/processed/inventory_snapshot_demo.csv
data/processed/phase_01_data_quality_report.json
data/metadata/data_dictionary.csv
```

### 4.2 Artefactos del modelo predictivo

```text
models/late_delivery_model.joblib
models/model_metrics.json
models/feature_importance.csv
models/feature_schema.json
models/late_delivery_predictions_sample.csv
```

Estos artefactos permiten cargar el modelo entrenado, mostrar sus métricas y ejecutar el simulador interactivo de riesgo de entrega tardía.

---

## 5. Acceso a la aplicación

La aplicación se puede usar directamente desde:

```text
https://openlogi-rfid-iot-demo-ml.streamlit.app/
```

Al abrir la app, el usuario verá:

- título del proyecto;
- descripción breve;
- desplegable de detalle del dataset y alcance del prototipo;
- barra lateral de filtros;
- pestañas funcionales.

---

## 6. Sección inicial: Detalle del dataset y alcance del prototipo

Al inicio de la aplicación aparece un botón desplegable llamado:

```text
Detalle del dataset y alcance del prototipo
```

Esta sección explica:

- qué es OpenLogi;
- cuál es el propósito de la demo;
- cuál es el origen del dataset;
- qué datos son reales;
- qué capas son simuladas;
- cuáles son las limitaciones del prototipo.

### Uso recomendado

Antes de analizar las pestañas, abra este desplegable para entender el alcance correcto de la aplicación.

### Interpretación importante

La aplicación debe interpretarse como una **demo técnica y académica**, no como una solución industrial conectada a dispositivos físicos.

---

## 7. Barra lateral de filtros

La barra lateral permite filtrar las órdenes usando tres criterios:

| Filtro | Descripción |
|---|---|
| Mercado | Filtra pedidos por mercado logístico/comercial. |
| Modo de envío | Filtra pedidos según tipo de envío. |
| Categoría | Filtra pedidos según categoría de producto. |

### 7.1 Filtro Mercado

Permite seleccionar uno o varios mercados disponibles en el dataset.

Ejemplo de uso:

- seleccionar solo un mercado para enfocar el análisis;
- comparar resultados al incluir todos los mercados;
- reducir el volumen de órdenes mostrado.

### 7.2 Filtro Modo de envío

Permite filtrar las órdenes por modalidad logística.

Este filtro es especialmente útil para analizar el riesgo de entrega tardía por tipo de envío.

### 7.3 Filtro Categoría

Permite seleccionar categorías de producto. Por defecto, la aplicación carga un subconjunto inicial de categorías para mantener el dashboard manejable.

### 7.4 Comportamiento si no se selecciona nada

Si el usuario deja vacío algún filtro obligatorio, la aplicación devuelve una vista sin datos y muestra advertencias como:

```text
No hay datos para los filtros seleccionados.
No hay órdenes con los filtros actuales.
Seleccione filtros con órdenes disponibles.
```

### 7.5 Alcance de los filtros

Los filtros afectan principalmente:

- el resumen de órdenes, ventas y riesgo tardío;
- la tabla de pedidos y entregas;
- la selección de pedidos para RFID;
- los eventos IoT asociados a órdenes filtradas.

No todas las métricas globales se recalculan con los filtros. En particular, los indicadores globales de eventos RFID, alertas IoT e inventario pueden representar el universo completo de datos cargados, según la sección consultada.

---

## 8. Pestaña Resumen

La pestaña **Resumen** ofrece una vista ejecutiva de la operación.

### 8.1 KPIs principales

La aplicación muestra seis indicadores:

| KPI | Significado |
|---|---|
| Órdenes | Número de órdenes únicas dentro del filtro aplicado. |
| Ventas | Suma de ventas de las órdenes filtradas. |
| Riesgo tardío | Promedio de la variable `late_delivery_risk` para las órdenes filtradas. |
| Eventos RFID | Número total de eventos RFID simulados cargados. |
| Alertas IoT | Número de eventos IoT simulados cuyo estado no es `NORMAL`. |
| LOW_STOCK | Número de productos en inventario sintético con estado `LOW_STOCK`. |

### 8.2 Gráfica Órdenes por mes

Muestra la evolución mensual de órdenes.

Uso recomendado:

- identificar meses con mayor actividad;
- detectar estacionalidad;
- observar concentración temporal de pedidos.

### 8.3 Gráfica Riesgo tardío por modo de envío

Muestra la tasa promedio de riesgo tardío agrupada por modo de envío.

Uso recomendado:

- comparar modalidades logísticas;
- identificar modos con mayor probabilidad de retraso;
- orientar decisiones de priorización operativa.

### 8.4 Cómo interpretar esta pestaña

Esta pestaña sirve para responder preguntas como:

- ¿cuántas órdenes estoy analizando?
- ¿cuánto representan en ventas?
- ¿qué tan alto es el riesgo de entrega tardía?
- ¿qué modos de envío presentan mayor riesgo?
- ¿existen señales operativas simuladas relevantes en RFID, IoT o inventario?

---

## 9. Pestaña Pedidos y entregas

La pestaña **Pedidos y entregas** resume el desempeño logístico de las órdenes filtradas.

### 9.1 Tabla agrupada

La aplicación agrupa la información por:

```text
market
order_region
shipping_mode
```

Y calcula:

| Columna | Significado |
|---|---|
| orders | Número de órdenes únicas. |
| sales | Ventas acumuladas. |
| late_delivery_rate | Promedio de riesgo de entrega tardía. |
| avg_days_real | Promedio de días reales de envío. |

### 9.2 Ordenamiento de la tabla

La tabla se ordena de mayor a menor tasa de riesgo tardío. Esto permite identificar rápidamente los segmentos logísticos más problemáticos.

### 9.3 Botón Descargar pedidos filtrados

La pestaña incluye el botón:

```text
Descargar pedidos filtrados
```

Este botón exporta las órdenes filtradas en formato CSV con el nombre:

```text
openlogi_orders_filtered.csv
```

### 9.4 Uso recomendado

Esta sección sirve para:

- identificar regiones con alto riesgo;
- comparar modos de envío;
- analizar ventas asociadas a segmentos logísticos;
- descargar datos para análisis externo;
- construir reportes complementarios.

---

## 10. Pestaña RFID simulado

La pestaña **RFID simulado** permite revisar la trazabilidad sintética de un pedido.

### 10.1 Selector de pedido

La aplicación muestra un selector:

```text
Seleccionar order_id
```

Este selector lista pedidos disponibles según los filtros aplicados en la barra lateral.

### 10.2 Tabla de eventos RFID

Después de seleccionar un pedido, la aplicación muestra los eventos RFID simulados asociados.

Campos típicos:

| Campo | Descripción |
|---|---|
| timestamp | Momento simulado del evento. |
| epc | Código electrónico de producto simulado. |
| order_id | Identificador del pedido. |
| order_item_id | Identificador de línea de pedido. |
| product_id | Identificador del producto. |
| product_name | Nombre del producto. |
| lot_id | Lote sintético. |
| reader_id | Lector RFID simulado. |
| antenna_id | Antena simulada. |
| event_type | Tipo de evento logístico. |
| location | Ubicación simulada. |
| rssi | Intensidad de señal simulada. |

### 10.3 Línea de tiempo RFID

La aplicación genera una gráfica temporal con:

- eje X: tiempo;
- eje Y: tipo de evento;
- tooltip: timestamp, EPC, lector, antena, ubicación y RSSI.

### 10.4 Interpretación operativa

Esta pestaña permite simular una ruta lógica del pedido, por ejemplo:

```text
RECEIVED → PICKED → PACKED → SHIPPED → IN_TRANSIT_SCAN → DELIVERED_OR_CLOSED
```

El objetivo es representar cómo RFID puede apoyar trazabilidad por producto y pedido.

### 10.5 Limitación importante

Los eventos RFID son simulados. La aplicación no está conectada a lectores RFID físicos, antenas reales ni middleware RFID industrial.

---

## 11. Pestaña IoT simulado

La pestaña **IoT simulado** muestra eventos ambientales y de condición operativa asociados a los pedidos filtrados.

### 11.1 Filtrado interno

La aplicación identifica los `order_id` válidos después de aplicar filtros laterales y conserva solo los eventos IoT relacionados con esas órdenes.

### 11.2 Gráfica de estados IoT

La app agrupa los eventos por `iot_status` y muestra el conteo de eventos por estado.

Estados esperados:

| Estado | Interpretación |
|---|---|
| NORMAL | Condición simulada dentro de rango. |
| TEMP_ALERT | Alerta simulada por temperatura. |
| HUMIDITY_ALERT | Alerta simulada por humedad. |
| VIBRATION_ALERT | Alerta simulada por vibración. |
| MULTI_ALERT | Evento con más de una anomalía. |

Los nombres exactos dependen de los valores generados en `iot_events_demo.csv`.

### 11.3 Tabla de alertas IoT

La aplicación muestra hasta 500 eventos cuyo estado no es `NORMAL`.

Esta tabla permite revisar:

- qué pedido presenta alerta;
- qué sensor generó el evento;
- qué variable está fuera de condición normal;
- en qué momento ocurrió;
- qué ubicación simulada se asocia al evento.

### 11.4 Uso recomendado

Esta pestaña permite demostrar el valor de IoT en logística:

- monitoreo de condiciones de transporte;
- detección de anomalías;
- priorización de eventos críticos;
- vinculación entre riesgo logístico y señales ambientales simuladas.

### 11.5 Limitación importante

Los sensores IoT son simulados. No hay conexión a hardware real, MQTT, telemetría en vivo ni GPS operativo.

---

## 12. Pestaña Inventario

La pestaña **Inventario** muestra un snapshot de inventario WMS sintético.

### 12.1 Filtro Estado de inventario

La pestaña incluye un multiselect:

```text
Estado de inventario
```

Permite filtrar productos por estado.

Estados típicos:

| Estado | Interpretación |
|---|---|
| LOW_STOCK | Producto con inventario bajo o por debajo del punto de reorden. |
| WATCH | Producto bajo observación. |
| NORMAL | Producto con inventario aceptable. |

Los valores exactos dependen del archivo `inventory_snapshot_demo.csv`.

### 12.2 Tabla de inventario

La tabla muestra información como:

| Campo | Descripción |
|---|---|
| product_id | Identificador del producto. |
| product_name | Nombre del producto. |
| category_name | Categoría. |
| department_name | Departamento. |
| warehouse_id | Almacén sintético. |
| stock_on_hand | Stock sintético disponible. |
| avg_daily_demand | Demanda promedio diaria estimada. |
| reorder_point | Punto de reorden calculado. |
| safety_stock | Stock de seguridad. |
| inventory_status | Estado del inventario. |
| recommended_order_qty | Cantidad sugerida de reabastecimiento. |

### 12.3 Gráfica de reorden sugerido

La aplicación ordena los productos por `recommended_order_qty` y muestra los 20 productos con mayor cantidad sugerida.

### 12.4 Uso recomendado

Esta pestaña permite responder:

- ¿qué productos requieren reabastecimiento?
- ¿qué productos tienen mayor cantidad sugerida?
- ¿qué productos deben vigilarse?
- ¿cómo se relaciona la demanda promedio con el stock disponible?

### 12.5 Limitación importante

El inventario es sintético y derivado de reglas de simulación. No representa un inventario físico real ni una conciliación WMS productiva.

---

## 13. Pestaña Modelo predictivo

La pestaña **Modelo predictivo** presenta el modelo de Machine Learning para estimar riesgo de entrega tardía.

### 13.1 Objetivo del modelo

El modelo estima la probabilidad de:

```text
late_delivery_risk = 1
```

Es decir, riesgo de entrega tardía.

### 13.2 Prevención de fuga de información

La aplicación indica que el modelo excluye variables que podrían revelar el resultado final de la entrega, como:

- estado final de entrega;
- días reales de envío;
- fecha de envío;
- estado final de la orden.

Esto hace que el modelo sea más honesto desde el punto de vista predictivo.

### 13.3 KPIs del modelo

La aplicación muestra cinco métricas:

| Métrica | Interpretación |
|---|---|
| Accuracy | Porcentaje total de predicciones correctas. |
| Precision | Qué proporción de predicciones de riesgo realmente fueron riesgo. |
| Recall | Qué proporción de casos reales de riesgo fueron detectados. |
| F1-score | Balance entre precision y recall. |
| ROC-AUC | Capacidad de discriminación entre riesgo y no riesgo. |

### 13.4 Tabla de métricas

Muestra las métricas del modelo en formato tabular para revisión técnica.

### 13.5 Matriz de confusión

Permite comparar predicciones contra resultados reales.

Interpretación básica:

| Elemento | Significado |
|---|---|
| Verdaderos positivos | Casos con riesgo real correctamente detectados. |
| Verdaderos negativos | Casos sin riesgo correctamente detectados. |
| Falsos positivos | Casos marcados como riesgo aunque no lo eran. |
| Falsos negativos | Casos con riesgo que el modelo no detectó. |

### 13.6 Importancia aproximada de variables

La aplicación muestra una gráfica de las variables más influyentes del modelo.

Uso recomendado:

- entender qué variables pesan más en la estimación;
- identificar factores logísticos relevantes;
- apoyar la explicación del modelo ante usuarios no técnicos.

### 13.7 Tabla de importancia de variables

En el desplegable:

```text
Ver tabla de importancia de variables
```

se puede consultar una tabla más extensa con las primeras variables ordenadas por importancia.

### 13.8 Muestra de predicciones de prueba

La aplicación muestra una muestra de hasta 200 predicciones.

Esta tabla permite revisar:

- probabilidad estimada;
- clase real;
- clase predicha;
- variables asociadas al ejemplo.

### 13.9 Detalle técnico del entrenamiento

En el desplegable:

```text
Detalle técnico del entrenamiento
```

la aplicación muestra un JSON con:

- nombre del modelo;
- filas de entrenamiento;
- filas de prueba;
- tasa de clase positiva;
- umbral de decisión;
- columnas excluidas por fuga;
- variables categóricas;
- variables numéricas.

### 13.10 Simulador de riesgo de entrega tardía

El simulador permite ingresar valores para variables categóricas y numéricas y calcular una probabilidad estimada de riesgo tardío.

Flujo de uso:

1. Seleccione valores en las variables categóricas.
2. Ajuste valores numéricos.
3. Presione:

```text
Calcular riesgo
```

4. Revise la probabilidad estimada.
5. Revise la clase estimada:

```text
Riesgo tardío
```

o

```text
Sin riesgo tardío
```

### 13.11 Ver variables enviadas al modelo

Después de calcular una predicción, el desplegable:

```text
Ver variables enviadas al modelo
```

permite inspeccionar exactamente qué entrada fue enviada al modelo.

### 13.12 Limitación del modelo

El modelo es demostrativo. No debe usarse para decisiones reales sin:

- validación con datos actuales;
- monitoreo de deriva;
- calibración;
- revisión de sesgos;
- validación operativa;
- pruebas con datos productivos.

---

## 14. Pestaña Dataset y documentación

La pestaña **Dataset y documentación** permite revisar información técnica de los datos.

### 14.1 Reporte de calidad

La aplicación muestra el archivo:

```text
phase_01_data_quality_report.json
```

Este reporte contiene metadatos y resultados de la fase de curación.

### 14.2 Diccionario de datos

La aplicación muestra el archivo:

```text
data_dictionary.csv
```

Este diccionario ayuda a entender las columnas utilizadas en la demo.

### 14.3 Recordatorio de alcance

La pestaña refuerza la distinción entre:

```text
Datos reales: pedidos, productos, envíos y riesgo de entrega tardía.
Capas simuladas: RFID, IoT e inventario WMS.
```

### 14.4 Uso recomendado

Esta pestaña debe consultarse cuando:

- se quiera explicar el origen de los datos;
- se necesite justificar la estructura del dataset;
- se revise la calidad del pipeline;
- se documente la aplicación para presentación académica.

---

## 15. Ruta recomendada para una demostración

Para presentar la aplicación en vivo, se recomienda seguir este orden:

### Paso 1. Abrir la app

```text
https://openlogi-rfid-iot-demo-ml.streamlit.app/
```

### Paso 2. Abrir el detalle del dataset

Explicar que la app usa DataCo como base y que RFID, IoT e inventario son simulados.

### Paso 3. Revisar Resumen

Mostrar:

- órdenes;
- ventas;
- riesgo tardío;
- eventos RFID;
- alertas IoT;
- LOW_STOCK.

### Paso 4. Ajustar filtros

Seleccionar un mercado, modo de envío o categoría para mostrar cómo cambian los resultados.

### Paso 5. Revisar Pedidos y entregas

Identificar regiones o modos de envío con mayor riesgo tardío.

### Paso 6. Revisar RFID simulado

Seleccionar un `order_id` y mostrar la línea de tiempo.

### Paso 7. Revisar IoT simulado

Mostrar estados IoT y alertas.

### Paso 8. Revisar Inventario

Filtrar `LOW_STOCK` y mostrar productos con reorden sugerido.

### Paso 9. Revisar Modelo predictivo

Mostrar métricas, importancia de variables y ejecutar el simulador.

### Paso 10. Cerrar en Dataset y documentación

Explicar calidad, diccionario de datos y alcance del prototipo.

---

## 16. Interpretación de alertas y estados

### 16.1 Riesgo tardío

El riesgo tardío representa la probabilidad o indicador de que una entrega se retrase.

En las vistas descriptivas, se calcula como promedio de la variable `late_delivery_risk`.

En el modelo predictivo, se estima con Machine Learning.

### 16.2 Alertas IoT

Las alertas IoT son eventos simulados donde `iot_status` no es `NORMAL`.

Sirven para demostrar cómo sensores podrían apoyar la visibilidad de condiciones logísticas.

### 16.3 LOW_STOCK

`LOW_STOCK` indica que un producto en el inventario sintético requiere atención por bajo stock o punto de reorden.

### 16.4 Reorden sugerido

`recommended_order_qty` representa una cantidad sugerida de reabastecimiento calculada con reglas de simulación.

---

## 17. Qué puede hacer el usuario final

Un usuario final puede:

- filtrar órdenes por mercado, modo de envío y categoría;
- visualizar KPIs ejecutivos;
- analizar riesgo tardío por modo de envío;
- descargar pedidos filtrados;
- consultar trazabilidad RFID simulada por pedido;
- revisar eventos IoT simulados;
- identificar productos con bajo inventario;
- revisar recomendaciones de reorden;
- consultar métricas del modelo;
- probar escenarios de riesgo con el simulador;
- revisar reporte de calidad y diccionario de datos.

---

## 18. Qué no hace la aplicación

La aplicación no realiza:

- lectura RFID física;
- conexión a antenas o lectores reales;
- monitoreo IoT en tiempo real;
- conexión MQTT o streaming;
- integración con ERP;
- integración con WMS productivo;
- integración con TMS productivo;
- gestión de rutas reales;
- cálculo de ETA real;
- conciliación de inventario físico;
- emisión de órdenes de compra reales;
- cumplimiento regulatorio o fiscal;
- operación logística productiva.

---

## 19. Instalación local

Para ejecutar el proyecto localmente, clone el repositorio:

```bash
git clone https://github.com/antoniot73/openlogi-rfid-iot-demo-ml.git
cd openlogi-rfid-iot-demo-ml
```

Cree un entorno virtual:

```bash
python -m venv .venv
```

Active el entorno:

En Linux/macOS:

```bash
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale dependencias:

```bash
python -m pip install -r requirements.txt
```

Ejecute la aplicación:

```bash
python -m streamlit run app.py
```

---

## 20. Validación del proyecto

Antes de presentar o desplegar, ejecute:

```bash
python -m pytest
python -m src.deployment_checks
```

La primera instrucción ejecuta pruebas automatizadas.  
La segunda valida artefactos necesarios para el despliegue.

---

## 21. Reentrenar el modelo

Para reentrenar el modelo predictivo:

```bash
python -m src.model_training --orders data/processed/orders_clean_sample.csv
```

Este proceso actualiza artefactos en la carpeta:

```text
models/
```

---

## 22. Regenerar datos procesados

Si se dispone del archivo original:

```text
data/raw/archive.zip
```

se pueden regenerar los datos fundacionales con:

```bash
python -m src.run_foundation_pipeline --archive data/raw/archive.zip
```

En despliegue web no se requiere subir `data/raw/archive.zip`. La app opera con los archivos ya procesados.

---

## 23. Solución de problemas

### 23.1 La app muestra “No hay datos para los filtros seleccionados”

Causa probable:

- no hay combinación válida de mercado, modo de envío y categoría.

Solución:

- seleccione más categorías;
- active todos los mercados;
- active todos los modos de envío.

### 23.2 La pestaña RFID no muestra eventos

Causa probable:

- el pedido seleccionado no tiene eventos RFID simulados;
- los filtros dejaron un conjunto de órdenes sin eventos asociados.

Solución:

- seleccione otro `order_id`;
- amplíe filtros en la barra lateral.

### 23.3 La pestaña IoT no muestra eventos

Causa probable:

- no hay eventos IoT relacionados con las órdenes filtradas.

Solución:

- seleccione más categorías o mercados;
- cambie el modo de envío.

### 23.4 El simulador predictivo no calcula

Causa probable:

- artefactos del modelo faltantes;
- archivo `feature_schema.json` inconsistente;
- incompatibilidad de versión de `scikit-learn`.

Solución:

- ejecute `python -m src.model_training --orders data/processed/orders_clean_sample.csv`;
- reinstale dependencias;
- valide con `python -m src.deployment_checks`.

### 23.5 Error de validación por archivo faltante

Causa probable:

- falta algún CSV en `data/processed`;
- falta `data_dictionary.csv`;
- faltan artefactos en `models`.

Solución:

- revise que existan todos los archivos requeridos;
- regenere datos o recupere archivos del repositorio.

---

## 24. Buenas prácticas de uso

- Use los filtros para construir escenarios de análisis específicos.
- No interprete las capas RFID, IoT o inventario como datos reales de operación.
- Use la pestaña de documentación para explicar el origen y alcance de los datos.
- Use el modelo como demostración predictiva, no como motor de decisión productivo.
- Reentrene el modelo si cambia el dataset.
- Mantenga separados los datos crudos y los datos procesados.
- No suba archivos sensibles ni datos personales reales al repositorio público.

---

## 25. Glosario

| Término | Definición |
|---|---|
| DataCo | Dataset público usado como base de pedidos y logística. |
| RFID | Tecnología de identificación por radiofrecuencia. En la app se simula funcionalmente. |
| EPC | Código electrónico de producto. En la app es sintético. |
| RSSI | Indicador de intensidad de señal. En la app es simulado. |
| IoT | Internet de las cosas. En la app representa sensores simulados. |
| WMS | Sistema de gestión de almacenes. En la app se representa con inventario sintético. |
| TMS | Sistema de gestión de transporte. En la app se aproxima mediante modos de envío y riesgo tardío. |
| late_delivery_risk | Variable objetivo para riesgo de entrega tardía. |
| LOW_STOCK | Estado sintético que indica bajo inventario. |
| Reorder point | Punto de reorden calculado para sugerir reabastecimiento. |
| Streamlit | Framework usado para construir la app web. |
| Altair | Librería usada para visualizaciones declarativas. |
| scikit-learn | Librería usada para el modelo predictivo. |

---

## 26. Lectura final del alcance

OpenLogi RFID IoT ML debe entenderse como una prueba conceptual de transformación logística digital. Su valor está en mostrar, de manera integrada, cómo los datos de pedidos y entregas pueden combinarse con simulación RFID, simulación IoT, inventario sintético y Machine Learning para crear una experiencia de torre de control logística.

La aplicación es adecuada para:

- demostraciones académicas;
- presentaciones de prototipos;
- explicación de arquitectura logística digital;
- enseñanza de ciencia de datos aplicada;
- validación conceptual de un flujo DataCo → ETL → simulación → dashboard → ML.

No es adecuada para operación productiva sin rediseño, integración con sistemas reales, monitoreo en tiempo real, validación industrial y controles de seguridad adicionales.

---

## 27. Créditos del proyecto

**Autor:** Antonio Nicolás Toro González  

**Programa académico:** Maestría en Inteligencia Artificial para la Transformación Digital  

**Proyecto:** OpenLogi RFID IoT ML  

**Aplicación web:** https://openlogi-rfid-iot-demo-ml.streamlit.app/  

**Repositorio:** https://github.com/antoniot73/openlogi-rfid-iot-demo-ml

