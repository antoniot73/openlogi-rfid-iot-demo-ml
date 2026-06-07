# Arquitectura de OpenLogi RFID/IoT Demo

## Flujo de datos

```text
archive.zip
  ├── DataCoSupplyChainDataset.csv
  ├── tokenized_access_logs.csv
  └── DescriptionDataCoSupplyChain.csv
        ↓
src/data_cleaning.py
        ↓
orders_clean_sample.csv
orders_agg_daily.csv
web_demand_daily.csv
phase_01_data_quality_report.json
        ↓
src/rfid_simulator.py
src/iot_simulator.py
src/inventory_simulator.py
        ↓
rfid_events_demo.csv
iot_events_demo.csv
inventory_snapshot_demo.csv
        ↓
app.py
        ↓
Streamlit Dashboard
```

## Principios técnicos

- Recursos abiertos y gratuitos.
- Datos sensibles excluidos.
- Cliente anonimizado con hash.
- RFID e IoT simulados de forma explícita.
- Pipeline reproducible.
- Programación estructurada.
- Logging y manejo de excepciones.
- Reportes en consola.
- Documentación por docstrings.
