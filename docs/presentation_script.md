# Guion de presentación - OpenLogi RFID/IoT Demo

## Duración sugerida

Entre 5 y 7 minutos.

## 1. Apertura

**Mensaje:**  
OpenLogi RFID/IoT Demo es una torre de control logística abierta para mostrar cómo una operación de e-commerce/retail puede integrar pedidos, entregas, trazabilidad simulada, sensores simulados, inventario sintético y analítica predictiva.

## 2. Problema

Muchas operaciones logísticas trabajan con datos dispersos, baja trazabilidad y procesos desconectados. Esto dificulta anticipar entregas tardías, controlar inventarios, detectar anomalías y generar decisiones oportunas.

## 3. Dataset y alcance

Abrir el desplegable:

```text
Detalle del dataset y alcance del prototipo
```

Explicar:

- La base real viene del dataset DataCo.
- Los datos reales son pedidos, productos, ventas, envíos, regiones, modos de envío y riesgo de entrega tardía.
- RFID, IoT e inventario WMS son capas simuladas para representar la función logística de esas tecnologías.
- La demo no es un WMS/TMS productivo ni un sistema RFID físico.

## 4. Resumen ejecutivo

Ir a la pestaña:

```text
Resumen
```

Mostrar:

- Órdenes.
- Ventas.
- Riesgo tardío.
- Eventos RFID simulados.
- Alertas IoT.
- Productos en bajo inventario.

## 5. Pedidos y entregas

Ir a:

```text
Pedidos y entregas
```

Mostrar:

- Filtros por mercado, modo de envío y categoría.
- Tasa de riesgo tardío por región y modo de envío.
- Descarga de pedidos filtrados.

## 6. RFID simulado

Ir a:

```text
RFID simulado
```

Seleccionar un `order_id` y explicar:

- EPC simulado.
- Lector.
- Antena.
- Ubicación.
- Evento logístico.
- RSSI simulado.

Mensaje clave: se demuestra trazabilidad funcional sin hardware físico.

## 7. IoT simulado

Ir a:

```text
IoT simulado
```

Mostrar:

- Estados IoT.
- Alertas por temperatura, humedad o vibración.
- Relación entre eventos simulados y operación logística.

## 8. Inventario

Ir a:

```text
Inventario
```

Mostrar:

- Stock simulado.
- Demanda promedio.
- Punto de reorden.
- Cantidad sugerida de reabastecimiento.

## 9. Modelo predictivo

Ir a:

```text
Modelo predictivo
```

Mostrar:

- Métricas del modelo.
- Importancia de variables.
- Simulador de riesgo de entrega tardía.

Mensaje clave: el modelo es una capa de inteligencia operativa sobre datos ya estructurados.

## 10. Cierre

**Mensaje final:**  
OpenLogi demuestra que una organización puede iniciar su transformación logística con recursos abiertos, datos curados, simulaciones reproducibles y una app web gratuita. El prototipo no reemplaza plataformas industriales, pero sí valida la arquitectura funcional de una torre de control antes de invertir en hardware o sistemas comerciales.
