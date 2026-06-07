# Checklist de liberación - Fase 6

## Validación técnica

- [ ] `python -m pytest` ejecuta sin fallos.
- [ ] `python -m src.deployment_checks` aprueba.
- [ ] `python -m streamlit run app.py` abre localmente.
- [ ] No aparecen advertencias de `use_container_width`.
- [ ] La pestaña `Modelo predictivo` carga correctamente.
- [ ] El simulador del modelo devuelve una probabilidad.

## Validación de datos

- [ ] `data/processed/orders_clean_sample.csv` existe.
- [ ] `data/processed/rfid_events_demo.csv` existe.
- [ ] `data/processed/iot_events_demo.csv` existe.
- [ ] `data/processed/inventory_snapshot_demo.csv` existe.
- [ ] `data/metadata/data_dictionary.csv` existe.
- [ ] `data/raw/archive.zip` no se sube al repositorio público.
- [ ] No hay columnas sensibles visibles en la demo.

## Validación de modelo

- [ ] `models/late_delivery_model.joblib` existe.
- [ ] `models/model_metrics.json` existe.
- [ ] `models/feature_schema.json` existe.
- [ ] `models/feature_importance.csv` existe.
- [ ] `models/late_delivery_predictions_sample.csv` existe.

## Validación de presentación

- [ ] El desplegable `Detalle del dataset y alcance del prototipo` está visible.
- [ ] El desplegable `Guion sugerido para presentar la demo` está visible.
- [ ] El texto distingue datos reales vs. capas simuladas.
- [ ] El tablero puede explicarse en 5-7 minutos.
- [ ] El mensaje final aclara que es un prototipo académico/técnico.

## Validación de despliegue

- [ ] Repositorio GitHub creado.
- [ ] `requirements.txt` está en la raíz.
- [ ] `.streamlit/config.toml` está incluido.
- [ ] Streamlit Community Cloud apunta a `app.py`.
- [ ] La app pública abre sin instalación local.
- [ ] El enlace público fue documentado en el README.
