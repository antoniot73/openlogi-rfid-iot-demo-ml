# Model Card: Late Delivery Risk

## Objetivo

El modelo estima la probabilidad de `late_delivery_risk` para apoyar el análisis de riesgo logístico dentro de OpenLogi RFID/IoT Demo.

## Datos de entrenamiento

- Archivo base: `data/processed/orders_clean_sample.csv`
- Registros totales: 50,000
- Registros de entrenamiento: 37,500
- Registros de prueba: 12,500
- Tasa de clase positiva total: 54.88%

## Variables usadas

### Categóricas

- `shipping_mode`
- `market`
- `order_region`
- `order_country`
- `order_city`
- `customer_segment`
- `category_name`
- `department_name`
- `product_id`
- `order_month`
- `order_day_of_week`

### Numéricas

- `days_shipping_scheduled`
- `quantity`
- `sales`

## Variables excluidas por fuga de información

- `delivery_status`
- `days_shipping_real`
- `shipping_date`
- `order_status`
- `shipment_delay_delta`

## Modelo

- Tipo: `LogisticRegression`
- Preprocesamiento categórico: `OneHotEncoder`
- Preprocesamiento numérico: `StandardScaler`
- Umbral de decisión: 0.5

## Métricas de prueba

| Métrica | Valor |
|---|---:|
| Accuracy | 0.6889 |
| Precision | 0.8266 |
| Recall | 0.5481 |
| F1-score | 0.6591 |
| ROC-AUC | 0.7302 |

## Limitaciones

El modelo es demostrativo. No debe usarse como sistema productivo de decisión logística sin validación adicional, calibración con datos operativos reales, monitoreo de drift y revisión de variables por parte del negocio.
