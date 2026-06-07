from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path


LOGGER = logging.getLogger("openlogi.deployment_checks")

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RequiredArtifact:
    """
    Representa un artefacto requerido para despliegue.

    Attributes:
        relative_path: Ruta relativa desde la raíz del proyecto.
        description: Descripción funcional del artefacto.
        min_size_bytes: Tamaño mínimo esperado para detectar archivos vacíos.
    """

    relative_path: str
    description: str
    min_size_bytes: int = 1


REQUIRED_ARTIFACTS: list[RequiredArtifact] = [
    RequiredArtifact("app.py", "Aplicación Streamlit principal"),
    RequiredArtifact("requirements.txt", "Dependencias Python"),
    RequiredArtifact(".streamlit/config.toml", "Configuración visual y operativa de Streamlit"),
    RequiredArtifact("data/processed/orders_clean_sample.csv", "Órdenes limpias y anonimizadas"),
    RequiredArtifact("data/processed/rfid_events_demo.csv", "Eventos RFID simulados"),
    RequiredArtifact("data/processed/iot_events_demo.csv", "Eventos IoT simulados"),
    RequiredArtifact("data/processed/inventory_snapshot_demo.csv", "Inventario WMS sintético"),
    RequiredArtifact("data/metadata/data_dictionary.csv", "Diccionario de datos"),
    RequiredArtifact("models/late_delivery_model.joblib", "Modelo entrenado de riesgo tardío"),
    RequiredArtifact("models/model_metrics.json", "Métricas del modelo"),
    RequiredArtifact("models/feature_schema.json", "Esquema de variables del modelo"),
    RequiredArtifact("models/feature_importance.csv", "Importancia de variables"),
    RequiredArtifact("docs/deployment_guide.md", "Guía de despliegue"),
    RequiredArtifact("docs/presentation_script.md", "Guion de presentación"),
    RequiredArtifact("docs/release_checklist.md", "Checklist de liberación"),
]


def configure_logging() -> None:
    """
    Configura la bitácora de validación de despliegue.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def validate_artifact(artifact: RequiredArtifact, project_root: Path) -> tuple[bool, str]:
    """
    Valida existencia y tamaño mínimo de un artefacto.

    Args:
        artifact: Artefacto requerido.
        project_root: Ruta raíz del proyecto.

    Returns:
        Tupla con estado booleano y mensaje descriptivo.
    """
    path = project_root / artifact.relative_path

    if not path.exists():
        return False, f"FALTA: {artifact.relative_path} | {artifact.description}"

    if path.is_file() and path.stat().st_size < artifact.min_size_bytes:
        return False, f"VACÍO: {artifact.relative_path} | {artifact.description}"

    return True, f"OK: {artifact.relative_path} | {artifact.description}"


def run_deployment_checks(project_root: Path = PROJECT_ROOT) -> bool:
    """
    Ejecuta validaciones mínimas antes de subir el proyecto a GitHub/Streamlit.

    Args:
        project_root: Ruta raíz del proyecto.

    Returns:
        True si todos los artefactos requeridos están presentes; False en caso contrario.
    """
    failures: list[str] = []

    print("\n--- OPENLOGI | VALIDACIÓN DE DESPLIEGUE ---")
    print(f"Raíz del proyecto: {project_root}")

    for artifact in REQUIRED_ARTIFACTS:
        ok, message = validate_artifact(artifact, project_root)
        print(message)

        if not ok:
            failures.append(message)

    if len(failures) == 0:
        LOGGER.info("Validación de despliegue completada sin errores.")
        print("\nResultado: APROBADO PARA PRESENTACIÓN Y DESPLIEGUE.")
        return True

    LOGGER.error("Validación fallida. Total errores: %s", len(failures))
    print("\nResultado: NO APROBADO. Corrija los artefactos faltantes o vacíos.")
    return False


def main() -> None:
    """
    Punto de entrada para ejecución por consola.

    Returns:
        None.
    """
    configure_logging()

    try:
        success = run_deployment_checks()
        if not success:
            raise SystemExit(1)
    except Exception as exc:
        LOGGER.exception("Error inesperado durante la validación.")
        print(f"Error inesperado durante la validación: {exc}")
        raise


if __name__ == "__main__":
    main()
