# Guía de despliegue web - OpenLogi RFID/IoT Demo

## Objetivo

Publicar la aplicación **OpenLogi RFID/IoT Demo** como demo web gratuita usando GitHub y Streamlit Community Cloud.

La versión de despliegue no necesita el archivo original `archive.zip`. La app debe publicarse con los datos ya procesados en `data/processed/`, el diccionario en `data/metadata/` y los artefactos del modelo en `models/`.

## Archivos que sí deben estar en el repositorio

```text
app.py
requirements.txt
.streamlit/config.toml
README.md
src/
tests/
docs/
data/processed/
data/metadata/
models/
```

## Archivos que no deben subirse

```text
.venv/
__pycache__/
.pytest_cache/
data/raw/archive.zip
*.zip
*.log
```

## Validación local antes de subir

Desde la raíz del proyecto:

```bash
python -m pytest
python -m src.deployment_checks
python -m streamlit run app.py
```

La aplicación debe abrir localmente en:

```text
http://localhost:8501
```

## Publicación en GitHub

1. Crear un repositorio público llamado `openlogi-rfid-iot-demo`.
2. Subir la estructura del proyecto.
3. Confirmar que `data/processed/` y `models/` están incluidos.
4. Confirmar que `data/raw/archive.zip` no está incluido.
5. Confirmar que `requirements.txt` está en la raíz del repositorio.

## Despliegue en Streamlit Community Cloud

1. Entrar a Streamlit Community Cloud.
2. Crear una nueva app.
3. Seleccionar el repositorio de GitHub.
4. Seleccionar la rama principal.
5. Definir el archivo principal como:

```text
app.py
```

6. En configuración avanzada, seleccionar una versión de Python compatible con las dependencias, preferentemente Python 3.11 o 3.12.
7. Desplegar.
8. Copiar el enlace público generado por Streamlit.

## Pruebas posteriores al despliegue

Validar en el navegador:

- La app abre sin error.
- Se visualiza el desplegable `Detalle del dataset y alcance del prototipo`.
- Aparecen las pestañas principales.
- La pestaña `Modelo predictivo` carga métricas, importancia de variables y simulador.
- Los filtros laterales actualizan las tablas.
- La descarga de pedidos filtrados funciona.
- No aparecen datos sensibles ni el dataset original crudo.

## Problemas frecuentes

### Error: falta un archivo CSV

Verificar que `data/processed/` esté subido al repositorio.

### Error: falta el modelo `.joblib`

Verificar que la carpeta `models/` esté subida al repositorio.

### Error de dependencias

Verificar `requirements.txt` y redeplegar. No agregar librerías de la biblioteca estándar como `json`, `logging` o `pathlib`.

### App pesada o lenta

Reducir el tamaño de `orders_clean_sample.csv` o limitar la cantidad de eventos simulados en RFID/IoT.

## Criterio de cierre de Fase 6

La fase queda cerrada cuando existen:

- Repositorio listo.
- Pruebas locales aprobadas.
- Validación `src.deployment_checks` aprobada.
- Demo local funcional.
- Demo web desplegada.
- Guion de presentación preparado.
