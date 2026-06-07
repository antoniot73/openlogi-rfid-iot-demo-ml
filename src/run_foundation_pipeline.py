from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import DEFAULT_ARCHIVE_PATH, PROCESSED_DIR, RANDOM_SEED
from src.data_cleaning import run_pipeline as run_data_cleaning
from src.inventory_simulator import run_pipeline as run_inventory
from src.iot_simulator import run_pipeline as run_iot
from src.rfid_simulator import run_pipeline as run_rfid


LOGGER = logging.getLogger("openlogi.foundation_pipeline")


def configure_logging() -> None:
    """
    Configura la bitácora general del pipeline fundacional.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def validate_archive_path(archive_path: Path) -> None:
    """
    Valida existencia del archivo ZIP de entrada.

    Args:
        archive_path: Ruta del ZIP.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"No existe el archivo ZIP de entrada: {archive_path}")


def print_phase_header(phase_name: str) -> None:
    """
    Imprime encabezado de fase en consola.

    Args:
        phase_name: Nombre de la fase.

    Returns:
        None.
    """
    print("\n" + "#" * 80)
    print(f"# {phase_name}")
    print("#" * 80)


def run_foundation_pipeline(archive_path: Path, processed_dir: Path, random_seed: int) -> None:
    """
    Ejecuta las fases fundacionales 1 a 4 del MVP.

    Args:
        archive_path: Ruta del archive.zip con los datos originales.
        processed_dir: Carpeta de salida procesada.
        random_seed: Semilla aleatoria.

    Returns:
        None.
    """
    validate_archive_path(archive_path)

    print_phase_header("FASE 1 | Curación de DataCo")
    run_data_cleaning(archive_path=archive_path, processed_dir=processed_dir)

    print_phase_header("FASE 2 | Simulación RFID")
    run_rfid(
        input_path=processed_dir / "orders_clean_sample.csv",
        output_path=processed_dir / "rfid_events_demo.csv",
        random_seed=random_seed,
    )

    print_phase_header("FASE 3 | Simulación IoT")
    run_iot(
        input_path=processed_dir / "orders_clean_sample.csv",
        output_path=processed_dir / "iot_events_demo.csv",
        random_seed=random_seed,
    )

    print_phase_header("FASE 4 | Inventario WMS sintético")
    run_inventory(
        input_path=processed_dir / "orders_agg_daily.csv",
        output_path=processed_dir / "inventory_snapshot_demo.csv",
        random_seed=random_seed,
    )

    LOGGER.info("Pipeline fundacional completado.")


def parse_args() -> argparse.Namespace:
    """
    Lee argumentos CLI del pipeline fundacional.

    Returns:
        Namespace con rutas y semilla.
    """
    parser = argparse.ArgumentParser(description="Ejecuta Fases 1 a 4 de OpenLogi.")
    parser.add_argument(
        "--archive",
        type=Path,
        default=DEFAULT_ARCHIVE_PATH,
        help="Ruta del archivo archive.zip.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=PROCESSED_DIR,
        help="Directorio de salida.",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Semilla aleatoria.")
    return parser.parse_args()


def main() -> None:
    """
    Punto de entrada del pipeline fundacional.

    Returns:
        None.
    """
    configure_logging()
    args = parse_args()

    try:
        run_foundation_pipeline(args.archive, args.processed_dir, args.seed)
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Error controlado en pipeline fundacional: %s", exc)
        print(f"Error de validación: {exc}")
    except Exception as exc:
        LOGGER.exception("Error inesperado en pipeline fundacional.")
        print(f"Error inesperado: {exc}")


if __name__ == "__main__":
    main()
