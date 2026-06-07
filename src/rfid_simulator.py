from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import PROCESSED_DIR, RANDOM_SEED


LOGGER = logging.getLogger("openlogi.rfid_simulator")

RFID_EVENT_SEQUENCE: list[str] = [
    "RECEIVED",
    "PICKED",
    "PACKED",
    "SHIPPED",
    "IN_TRANSIT_SCAN",
    "DELIVERED_OR_CLOSED",
]

READER_BY_EVENT: dict[str, str] = {
    "RECEIVED": "READER_WH_RECEIVING_01",
    "PICKED": "READER_WH_PICKING_01",
    "PACKED": "READER_PACKING_01",
    "SHIPPED": "READER_DOCK_01",
    "IN_TRANSIT_SCAN": "READER_TRANSIT_GATE_01",
    "DELIVERED_OR_CLOSED": "READER_LAST_MILE_01",
}

LOCATION_BY_EVENT: dict[str, str] = {
    "RECEIVED": "WAREHOUSE_RECEIVING",
    "PICKED": "WAREHOUSE_PICKING",
    "PACKED": "PACKING_AREA",
    "SHIPPED": "SHIPPING_DOCK",
    "IN_TRANSIT_SCAN": "TRANSIT_NODE",
    "DELIVERED_OR_CLOSED": "LAST_MILE_OR_CLOSED",
}


def configure_logging() -> None:
    """
    Configura logging para el simulador RFID.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_orders(path: Path) -> pd.DataFrame:
    """
    Carga el dataset de órdenes limpias.

    Args:
        path: Ruta del archivo CSV orders_clean_sample.csv.

    Returns:
        DataFrame de órdenes.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas o si el archivo está vacío.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de órdenes: {path}")

    orders = pd.read_csv(path, parse_dates=["order_date", "shipping_date"])

    required_columns = {
        "order_id",
        "order_item_id",
        "order_date",
        "shipping_date",
        "product_id",
        "product_name",
        "order_month",
        "days_shipping_real",
        "delivery_status",
    }

    missing = required_columns.difference(orders.columns)
    if missing:
        raise ValueError(
            "Faltan columnas para simular RFID: " + ", ".join(sorted(missing))
        )

    if orders.empty:
        raise ValueError("El archivo de órdenes está vacío.")

    LOGGER.info("Órdenes cargadas para RFID: filas=%s", len(orders))
    return orders


def build_epc(row: pd.Series) -> str:
    """
    Construye un código EPC sintético para una línea de pedido.

    Args:
        row: Fila de orden.

    Returns:
        EPC sintético reproducible.
    """
    return f"EPC-{int(row['product_id'])}-{int(row['order_id'])}-{int(row['order_item_id'])}"


def build_lot_id(row: pd.Series) -> str:
    """
    Construye un lote sintético a partir del producto y el mes de orden.

    Args:
        row: Fila de orden.

    Returns:
        Identificador de lote sintético.
    """
    month = str(row["order_month"]).replace("-", "")
    return f"LOT-{int(row['product_id'])}-{month}"


def calculate_event_timestamp(row: pd.Series, event_type: str, rng: np.random.Generator) -> pd.Timestamp:
    """
    Calcula una marca temporal sintética para un evento RFID.

    Args:
        row: Fila de orden.
        event_type: Tipo de evento RFID.
        rng: Generador aleatorio reproducible.

    Returns:
        Timestamp del evento.
    """
    order_date = pd.Timestamp(row["order_date"])
    shipping_date = pd.Timestamp(row["shipping_date"])
    days_shipping_real = max(float(row["days_shipping_real"]), 0.0)
    estimated_final = order_date + pd.Timedelta(days=days_shipping_real)

    if event_type == "RECEIVED":
        return order_date
    if event_type == "PICKED":
        return order_date + pd.Timedelta(minutes=int(rng.integers(15, 240)))
    if event_type == "PACKED":
        return order_date + pd.Timedelta(minutes=int(rng.integers(240, 720)))
    if event_type == "SHIPPED":
        return shipping_date
    if event_type == "IN_TRANSIT_SCAN":
        midpoint = order_date + (estimated_final - order_date) / 2
        return midpoint + pd.Timedelta(minutes=int(rng.integers(-180, 180)))
    if event_type == "DELIVERED_OR_CLOSED":
        return max(shipping_date, estimated_final)

    raise ValueError(f"Evento RFID no reconocido: {event_type}")


def generate_antenna_id(rng: np.random.Generator) -> str:
    """
    Genera un identificador sintético de antena.

    Args:
        rng: Generador aleatorio reproducible.

    Returns:
        Antena sintética.
    """
    antenna_number = int(rng.integers(1, 5))
    return f"ANT_{antenna_number:02d}"


def generate_rssi(rng: np.random.Generator) -> int:
    """
    Genera un valor RSSI sintético típico de lectura RFID.

    Args:
        rng: Generador aleatorio reproducible.

    Returns:
        RSSI en dBm.
    """
    return int(rng.integers(-78, -34))


def build_event_record(row: pd.Series, event_type: str, rng: np.random.Generator) -> dict[str, Any]:
    """
    Construye un registro RFID sintético.

    Args:
        row: Fila de orden.
        event_type: Tipo de evento.
        rng: Generador aleatorio reproducible.

    Returns:
        Registro RFID como diccionario.
    """
    return {
        "timestamp": calculate_event_timestamp(row, event_type, rng),
        "epc": build_epc(row),
        "order_id": int(row["order_id"]),
        "order_item_id": int(row["order_item_id"]),
        "product_id": int(row["product_id"]),
        "product_name": str(row["product_name"]),
        "lot_id": build_lot_id(row),
        "reader_id": READER_BY_EVENT[event_type],
        "antenna_id": generate_antenna_id(rng),
        "event_type": event_type,
        "location": LOCATION_BY_EVENT[event_type],
        "rssi": generate_rssi(rng),
    }


def generate_rfid_events(orders: pd.DataFrame, random_seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Genera eventos RFID sintéticos para cada línea de pedido.

    Args:
        orders: DataFrame de órdenes limpias.
        random_seed: Semilla para reproducibilidad.

    Returns:
        DataFrame de eventos RFID.
    """
    rng = np.random.default_rng(random_seed)
    records: list[dict[str, Any]] = []

    for _, row in orders.iterrows():
        for event_type in RFID_EVENT_SEQUENCE:
            records.append(build_event_record(row, event_type, rng))

    events = pd.DataFrame(records)
    events = events.sort_values(["timestamp", "order_id", "order_item_id"]).reset_index(drop=True)
    LOGGER.info("Eventos RFID generados: filas=%s", len(events))
    return events


def write_events(events: pd.DataFrame, path: Path) -> None:
    """
    Guarda eventos RFID como CSV.

    Args:
        events: DataFrame de eventos.
        path: Ruta de salida.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    events.to_csv(path, index=False)
    LOGGER.info("Archivo RFID escrito: %s | filas=%s", path, len(events))


def print_console_report(events: pd.DataFrame, path: Path) -> None:
    """
    Imprime resumen de la simulación RFID.

    Args:
        events: DataFrame de eventos.
        path: Ruta escrita.

    Returns:
        None.
    """
    print("\n" + "=" * 72)
    print("OPENLOGI | FASE 2 - SIMULACIÓN RFID")
    print("=" * 72)
    print(f"Eventos RFID generados        : {len(events):,}")
    print(f"EPC únicos                    : {events['epc'].nunique():,}")
    print(f"Pedidos cubiertos             : {events['order_id'].nunique():,}")
    print(f"Lectores simulados            : {events['reader_id'].nunique():,}")
    print(f"Salida                        : {path}")
    print("=" * 72 + "\n")


def run_pipeline(input_path: Path, output_path: Path, random_seed: int) -> pd.DataFrame:
    """
    Ejecuta el pipeline de simulación RFID.

    Args:
        input_path: Ruta de órdenes limpias.
        output_path: Ruta de salida de eventos RFID.
        random_seed: Semilla aleatoria.

    Returns:
        DataFrame de eventos RFID.
    """
    orders = load_orders(input_path)
    events = generate_rfid_events(orders, random_seed=random_seed)
    write_events(events, output_path)
    print_console_report(events, output_path)
    return events


def parse_args() -> argparse.Namespace:
    """
    Lee argumentos CLI.

    Returns:
        Namespace con rutas y semilla.
    """
    parser = argparse.ArgumentParser(description="Fase 2: simulación RFID para OpenLogi.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "orders_clean_sample.csv",
        help="Ruta del CSV de órdenes limpias.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "rfid_events_demo.csv",
        help="Ruta de salida de eventos RFID.",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Semilla aleatoria.")
    return parser.parse_args()


def main() -> None:
    """
    Orquesta la ejecución del simulador RFID con manejo de errores.

    Returns:
        None.
    """
    configure_logging()
    args = parse_args()

    try:
        run_pipeline(args.input, args.output, args.seed)
        LOGGER.info("Simulación RFID completada.")
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Error controlado en simulación RFID: %s", exc)
        print(f"Error de validación RFID: {exc}")
    except Exception as exc:
        LOGGER.exception("Error inesperado en simulación RFID.")
        print(f"Error inesperado RFID: {exc}")


if __name__ == "__main__":
    main()
