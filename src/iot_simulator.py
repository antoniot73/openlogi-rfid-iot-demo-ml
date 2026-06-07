from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import PROCESSED_DIR, RANDOM_SEED


LOGGER = logging.getLogger("openlogi.iot_simulator")

SHIPPING_MODE_EVENT_COUNTS: dict[str, int] = {
    "Same Day": 2,
    "First Class": 3,
    "Second Class": 3,
    "Standard Class": 4,
}


def configure_logging() -> None:
    """
    Configura logging para el simulador IoT.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_orders(path: Path) -> pd.DataFrame:
    """
    Carga órdenes limpias para simular sensores IoT.

    Args:
        path: Ruta del CSV de órdenes.

    Returns:
        DataFrame de órdenes.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de órdenes: {path}")

    orders = pd.read_csv(path, parse_dates=["order_date", "shipping_date"])
    required_columns = {
        "order_id",
        "product_id",
        "shipping_mode",
        "late_delivery_risk",
        "days_shipping_real",
        "order_date",
        "shipping_date",
        "market",
        "order_region",
    }

    missing = required_columns.difference(orders.columns)
    if missing:
        raise ValueError(
            "Faltan columnas para simular IoT: " + ", ".join(sorted(missing))
        )

    if orders.empty:
        raise ValueError("El archivo de órdenes está vacío.")

    LOGGER.info("Órdenes cargadas para IoT: filas=%s", len(orders))
    return orders


def get_event_count(shipping_mode: str) -> int:
    """
    Obtiene el número de eventos IoT según el modo de envío.

    Args:
        shipping_mode: Modo de envío.

    Returns:
        Número de eventos por envío.
    """
    return SHIPPING_MODE_EVENT_COUNTS.get(str(shipping_mode), 3)


def calculate_iot_timestamp(row: pd.Series, event_index: int, total_events: int) -> pd.Timestamp:
    """
    Calcula un timestamp IoT distribuido entre orden y entrega estimada.

    Args:
        row: Fila de orden.
        event_index: Índice del evento.
        total_events: Total de eventos simulados.

    Returns:
        Timestamp del evento.
    """
    start = pd.Timestamp(row["shipping_date"])
    days_shipping_real = max(float(row["days_shipping_real"]), 0.25)
    end = pd.Timestamp(row["order_date"]) + pd.Timedelta(days=days_shipping_real)

    if end <= start:
        end = start + pd.Timedelta(hours=6)

    if total_events <= 1:
        return start

    fraction = event_index / max(total_events - 1, 1)
    return start + (end - start) * fraction


def anomaly_probability(row: pd.Series) -> float:
    """
    Calcula probabilidad de anomalía IoT según riesgo tardío y modo de envío.

    Args:
        row: Fila de orden.

    Returns:
        Probabilidad de anomalía entre 0 y 1.
    """
    base = 0.04
    late_risk = int(row["late_delivery_risk"])

    if late_risk == 1:
        base += 0.12

    shipping_mode = str(row["shipping_mode"])
    if shipping_mode == "Standard Class":
        base += 0.05
    elif shipping_mode == "Same Day":
        base -= 0.02
    else:
        base += 0.00

    return min(max(base, 0.01), 0.35)


def generate_sensor_values(row: pd.Series, rng: np.random.Generator) -> tuple[float, float, float, str]:
    """
    Genera temperatura, humedad, vibración y estado IoT sintéticos.

    Args:
        row: Fila de orden.
        rng: Generador aleatorio.

    Returns:
        Tupla con temperatura, humedad, vibración y estado.
    """
    probability = anomaly_probability(row)
    has_anomaly = bool(rng.random() < probability)

    temperature = float(rng.normal(22.0, 3.0))
    humidity = float(rng.normal(55.0, 10.0))
    vibration = float(abs(rng.normal(0.25, 0.12)))
    status = "NORMAL"

    if has_anomaly:
        anomaly_type = rng.choice(["TEMP_ALERT", "HUMIDITY_ALERT", "VIBRATION_ALERT", "MULTI_ALERT"])
        status = str(anomaly_type)

        if status == "TEMP_ALERT":
            temperature += float(rng.choice([-12.0, 14.0]))
        elif status == "HUMIDITY_ALERT":
            humidity += float(rng.choice([-30.0, 35.0]))
        elif status == "VIBRATION_ALERT":
            vibration += float(rng.uniform(0.7, 1.6))
        elif status == "MULTI_ALERT":
            temperature += float(rng.choice([-10.0, 12.0]))
            humidity += float(rng.choice([-25.0, 30.0]))
            vibration += float(rng.uniform(0.5, 1.4))

    temperature = round(temperature, 2)
    humidity = round(min(max(humidity, 0.0), 100.0), 2)
    vibration = round(max(vibration, 0.0), 3)

    return temperature, humidity, vibration, status


def build_iot_record(
    row: pd.Series,
    event_index: int,
    total_events: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """
    Construye un registro IoT sintético.

    Args:
        row: Fila de orden.
        event_index: Índice del evento.
        total_events: Total de eventos del envío.
        rng: Generador aleatorio.

    Returns:
        Registro IoT como diccionario.
    """
    temperature, humidity, vibration, status = generate_sensor_values(row, rng)
    order_id = int(row["order_id"])
    product_id = int(row["product_id"])

    return {
        "timestamp": calculate_iot_timestamp(row, event_index, total_events),
        "shipment_id": f"SHP-{order_id}",
        "order_id": order_id,
        "product_id": product_id,
        "sensor_id": f"SENSOR-{order_id % 1000:04d}",
        "temperature_c": temperature,
        "humidity_pct": humidity,
        "vibration_g": vibration,
        "location": f"{row['market']} | {row['order_region']}",
        "shipping_mode": str(row["shipping_mode"]),
        "late_delivery_risk": int(row["late_delivery_risk"]),
        "iot_status": status,
    }


def generate_iot_events(orders: pd.DataFrame, random_seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Genera eventos IoT para envíos usando reglas reproducibles.

    Args:
        orders: DataFrame de órdenes limpias.
        random_seed: Semilla aleatoria.

    Returns:
        DataFrame de eventos IoT.
    """
    rng = np.random.default_rng(random_seed)
    records: list[dict[str, Any]] = []

    unique_shipments = (
        orders.sort_values(["order_id", "product_id"])
        .drop_duplicates(subset=["order_id", "product_id"])
        .reset_index(drop=True)
    )

    for _, row in unique_shipments.iterrows():
        total_events = get_event_count(str(row["shipping_mode"]))
        for event_index in range(total_events):
            records.append(build_iot_record(row, event_index, total_events, rng))

    events = pd.DataFrame(records)
    events = events.sort_values(["timestamp", "order_id", "product_id"]).reset_index(drop=True)
    LOGGER.info("Eventos IoT generados: filas=%s", len(events))
    return events


def write_events(events: pd.DataFrame, path: Path) -> None:
    """
    Guarda eventos IoT como CSV.

    Args:
        events: DataFrame de eventos.
        path: Ruta de salida.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    events.to_csv(path, index=False)
    LOGGER.info("Archivo IoT escrito: %s | filas=%s", path, len(events))


def print_console_report(events: pd.DataFrame, path: Path) -> None:
    """
    Imprime reporte de simulación IoT.

    Args:
        events: DataFrame de eventos.
        path: Ruta escrita.

    Returns:
        None.
    """
    alert_count = int((events["iot_status"] != "NORMAL").sum())

    print("\n" + "=" * 72)
    print("OPENLOGI | FASE 3 - SIMULACIÓN IoT")
    print("=" * 72)
    print(f"Eventos IoT generados         : {len(events):,}")
    print(f"Envíos cubiertos              : {events['shipment_id'].nunique():,}")
    print(f"Alertas IoT simuladas         : {alert_count:,}")
    print(f"Tasa de alertas IoT           : {alert_count / max(len(events), 1):.2%}")
    print(f"Salida                        : {path}")
    print("=" * 72 + "\n")


def run_pipeline(input_path: Path, output_path: Path, random_seed: int) -> pd.DataFrame:
    """
    Ejecuta el pipeline de simulación IoT.

    Args:
        input_path: Ruta de órdenes limpias.
        output_path: Ruta de salida.
        random_seed: Semilla aleatoria.

    Returns:
        DataFrame de eventos IoT.
    """
    orders = load_orders(input_path)
    events = generate_iot_events(orders, random_seed=random_seed)
    write_events(events, output_path)
    print_console_report(events, output_path)
    return events


def parse_args() -> argparse.Namespace:
    """
    Lee argumentos CLI.

    Returns:
        Namespace con rutas y semilla.
    """
    parser = argparse.ArgumentParser(description="Fase 3: simulación IoT para OpenLogi.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "orders_clean_sample.csv",
        help="Ruta del CSV de órdenes limpias.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "iot_events_demo.csv",
        help="Ruta de salida de eventos IoT.",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Semilla aleatoria.")
    return parser.parse_args()


def main() -> None:
    """
    Orquesta la ejecución del simulador IoT con manejo de excepciones.

    Returns:
        None.
    """
    configure_logging()
    args = parse_args()

    try:
        run_pipeline(args.input, args.output, args.seed)
        LOGGER.info("Simulación IoT completada.")
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Error controlado en simulación IoT: %s", exc)
        print(f"Error de validación IoT: {exc}")
    except Exception as exc:
        LOGGER.exception("Error inesperado en simulación IoT.")
        print(f"Error inesperado IoT: {exc}")


if __name__ == "__main__":
    main()
