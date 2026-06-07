# OpenLogi RFID/IoT Demo

**OpenLogi RFID/IoT Demo** es una torre de control logística abierta para e-commerce/retail. La app usa datos reales procesados del dataset DataCo y agrega capas simuladas de RFID, IoT e inventario WMS para demostrar trazabilidad, visibilidad operativa, alertas y analítica predictiva sin hardware físico ni sistemas comerciales.

## Estado del proyecto

| Fase | Estado | Resultado |
|---|---:|---|
| Fase 0 | Implementada | Estructura del proyecto |
| Fase 1 | Implementada | Curación y anonimización de datos DataCo |
| Fase 2 | Implementada | Eventos RFID simulados |
| Fase 3 | Implementada | Eventos IoT simulados |
| Fase 4 | Implementada | Inventario WMS sintético |
| Fase 5 | Implementada | Modelo predictivo de riesgo de entrega tardía |
| Fase 6 | Implementada | Preparación para presentación y despliegue web |

## Datos reales vs. simulados

**Datos reales derivados del dataset DataCo:**

- Pedidos y líneas de pedido.
- Productos, categorías y departamentos.
- Ventas y utilidad.
- Fechas de orden y envío.
- Modos de envío.
- Estados de entrega.
- Riesgo de entrega tardía.
- Mercado, región, país y ciudad destino.

**Capas simuladas por OpenLogi:**

- Eventos RFID.
- EPC, lectores, antenas y RSSI.
- Eventos IoT de temperatura, humedad y vibración.
- Inventario físico, punto de reorden y reabastecimiento sugerido.

## Estructura principal

```text
openlogi-rfid-iot-demo/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── data/
│   ├── processed/
│   └── metadata/
├── docs/
│   ├── architecture.md
│   ├── deployment_guide.md
│   ├── model_card_late_delivery.md
│   ├── presentation_script.md
│   └── release_checklist.md
├── models/
├── src/
└── tests/
```

## Instalación local

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
python -m streamlit run app.py
```

## Validar antes de presentar

```bash
python -m pytest
python -m src.deployment_checks
```

## Despliegue web

La guía completa está en:

```text
docs/deployment_guide.md
```

Resumen:

1. Crear repositorio en GitHub.
2. Subir el proyecto sin `data/raw/archive.zip`.
3. Verificar que `data/processed/`, `data/metadata/` y `models/` estén incluidos.
4. Entrar a Streamlit Community Cloud.
5. Crear una nueva app apuntando a `app.py`.
6. Elegir Python 3.11 o 3.12 en configuración avanzada.
7. Publicar la demo.

## Guion de presentación

El guion está en:

```text
docs/presentation_script.md
```

También aparece dentro de la app en el desplegable:

```text
Guion sugerido para presentar la demo
```

## Regenerar datos desde el ZIP original

Coloque el archivo original en:

```text
data/raw/archive.zip
```

Luego ejecute:

```bash
python -m src.run_foundation_pipeline --archive data/raw/archive.zip
```

## Reentrenar el modelo

```bash
python -m src.model_training --orders data/processed/orders_clean_sample.csv
```

## Notas de alcance

OpenLogi es una demo académica/técnica. No reemplaza un WMS, TMS, lector RFID físico, middleware RFID industrial ni plataforma IoT productiva. Su propósito es demostrar una arquitectura funcional y reproducible de visibilidad logística con recursos abiertos y gratuitos.
