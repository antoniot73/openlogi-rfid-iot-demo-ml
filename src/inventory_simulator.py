from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import PROCESSED_DIR, RANDOM_SEED


LOGGER = logging.getLogger("openlogi.inventory_simulator")


def configure_logging() -> None:
    """
    Configura logging para el simulador de inventario.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_orders_daily(path: Path) -> pd.DataFrame:
    """
    Carga agregados diarios de órdenes.

    Args:
        path: Ruta del archivo orders_agg_daily.csv.

    Returns:
        DataFrame de agregados diarios.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de agregados diarios: {path}")

    df = pd.read_csv(path, parse_dates=["order_date_day"])

    required_columns = {
        "order_date_day",
        "product_id",
        "product_name",
        "category_name",
        "department_name",
        "quantity",
    }

    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(
            "Faltan columnas para inventario: " + ", ".join(sorted(missing))
        )

    if df.empty:
        raise ValueError("El archivo de agregados diarios está vacío.")

    LOGGER.info("Agregados diarios cargados: filas=%s", len(df))
    return df


def calculate_product_demand(orders_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula demanda promedio diaria por producto.

    Args:
        orders_daily: DataFrame agregado por día y producto.

    Returns:
        DataFrame de demanda por producto.
    """
    product_daily = (
        orders_daily.groupby(
            ["order_date_day", "product_id", "product_name", "category_name", "department_name"],
            dropna=False,
        )
        .agg(quantity=("quantity", "sum"))
        .reset_index()
    )

    total_days = max(int(product_daily["order_date_day"].nunique()), 1)

    demand = (
        product_daily.groupby(["product_id", "product_name", "category_name", "department_name"], dropna=False)
        .agg(
            total_quantity=("quantity", "sum"),
            active_days=("order_date_day", "nunique"),
            max_daily_demand=("quantity", "max"),
        )
        .reset_index()
    )

    demand["avg_daily_demand"] = demand["total_quantity"] / total_days
    demand["avg_active_day_demand"] = demand["total_quantity"] / demand["active_days"].clip(lower=1)

    return demand


def assign_warehouse(product_id: int) -> str:
    """
    Asigna una bodega simulada a un producto.

    Args:
        product_id: Identificador de producto.

    Returns:
        Identificador de bodega.
    """
    warehouses = ["WH_NORTH", "WH_CENTER", "WH_SOUTH", "WH_ECOMMERCE"]
    return warehouses[int(product_id) % len(warehouses)]


def classify_inventory_status(stock_on_hand: int, reorder_point: float) -> str:
    """
    Clasifica el estado del inventario.

    Args:
        stock_on_hand: Stock disponible simulado.
        reorder_point: Punto de reorden.

    Returns:
        Estado del inventario.
    """
    if stock_on_hand <= reorder_point:
        return "LOW_STOCK"
    elif stock_on_hand <= reorder_point * 1.25:
        return "WATCH"
    else:
        return "NORMAL"


def build_inventory_record(row: pd.Series, rng: np.random.Generator) -> dict[str, Any]:
    """
    Construye un registro de inventario simulado.

    Args:
        row: Fila de demanda por producto.
        rng: Generador aleatorio.

    Returns:
        Registro de inventario.
    """
    product_id = int(row["product_id"])
    avg_daily_demand = float(row["avg_daily_demand"])
    lead_time_days = int(rng.integers(3, 15))
    safety_stock = max(avg_daily_demand * 3.0, 5.0)
    reorder_point = avg_daily_demand * lead_time_days + safety_stock

    stock_multiplier = float(rng.uniform(0.4, 2.4))
    stock_on_hand = int(max(reorder_point * stock_multiplier, 0))

    recommended_order_qty = int(max((avg_daily_demand * lead_time_days * 1.2 + safety_stock) - stock_on_hand, 0))
    inventory_status = classify_inventory_status(stock_on_hand, reorder_point)

    return {
        "product_id": product_id,
        "product_name": str(row["product_name"]),
        "category_name": str(row["category_name"]),
        "department_name": str(row["department_name"]),
        "warehouse_id": assign_warehouse(product_id),
        "stock_on_hand": stock_on_hand,
        "avg_daily_demand": round(avg_daily_demand, 4),
        "avg_active_day_demand": round(float(row["avg_active_day_demand"]), 4),
        "lead_time_days": lead_time_days,
        "safety_stock": int(round(safety_stock, 0)),
        "reorder_point": int(round(reorder_point, 0)),
        "recommended_order_qty": recommended_order_qty,
        "inventory_status": inventory_status,
    }


def generate_inventory_snapshot(
    orders_daily: pd.DataFrame,
    random_seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Genera snapshot de inventario sintético a partir de demanda histórica.

    Args:
        orders_daily: Agregados diarios.
        random_seed: Semilla aleatoria.

    Returns:
        DataFrame de inventario.
    """
    rng = np.random.default_rng(random_seed)
    demand = calculate_product_demand(orders_daily)
    records: list[dict[str, Any]] = []

    for _, row in demand.iterrows():
        records.append(build_inventory_record(row, rng))

    inventory = pd.DataFrame(records)
    inventory = inventory.sort_values(["inventory_status", "recommended_order_qty"], ascending=[True, False])
    LOGGER.info("Inventario simulado generado: filas=%s", len(inventory))
    return inventory


def write_inventory(inventory: pd.DataFrame, path: Path) -> None:
    """
    Guarda inventario simulado como CSV.

    Args:
        inventory: DataFrame de inventario.
        path: Ruta de salida.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(path, index=False)
    LOGGER.info("Archivo de inventario escrito: %s | filas=%s", path, len(inventory))


def print_console_report(inventory: pd.DataFrame, path: Path) -> None:
    """
    Imprime reporte de inventario.

    Args:
        inventory: DataFrame de inventario.
        path: Ruta escrita.

    Returns:
        None.
    """
    low_stock = int((inventory["inventory_status"] == "LOW_STOCK").sum())
    watch = int((inventory["inventory_status"] == "WATCH").sum())

    print("\n" + "=" * 72)
    print("OPENLOGI | FASE 4 - INVENTARIO WMS SINTÉTICO")
    print("=" * 72)
    print(f"Productos simulados           : {len(inventory):,}")
    print(f"Productos LOW_STOCK           : {low_stock:,}")
    print(f"Productos WATCH               : {watch:,}")
    print(f"Stock total simulado          : {int(inventory['stock_on_hand'].sum()):,}")
    print(f"Salida                        : {path}")
    print("=" * 72 + "\n")


def run_pipeline(input_path: Path, output_path: Path, random_seed: int) -> pd.DataFrame:
    """
    Ejecuta el pipeline de inventario.

    Args:
        input_path: Ruta de agregados diarios.
        output_path: Ruta de salida.
        random_seed: Semilla aleatoria.

    Returns:
        DataFrame de inventario.
    """
    orders_daily = load_orders_daily(input_path)
    inventory = generate_inventory_snapshot(orders_daily, random_seed=random_seed)
    write_inventory(inventory, output_path)
    print_console_report(inventory, output_path)
    return inventory


def parse_args() -> argparse.Namespace:
    """
    Lee argumentos CLI.

    Returns:
        Namespace con rutas y semilla.
    """
    parser = argparse.ArgumentParser(description="Fase 4: inventario sintético para OpenLogi.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "orders_agg_daily.csv",
        help="Ruta del CSV de agregados diarios.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "inventory_snapshot_demo.csv",
        help="Ruta de salida del inventario simulado.",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Semilla aleatoria.")
    return parser.parse_args()


def main() -> None:
    """
    Orquesta la ejecución del simulador de inventario con manejo de excepciones.

    Returns:
        None.
    """
    configure_logging()
    args = parse_args()

    try:
        run_pipeline(args.input, args.output, args.seed)
        LOGGER.info("Inventario simulado completado.")
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Error controlado en inventario: %s", exc)
        print(f"Error de validación inventario: {exc}")
    except Exception as exc:
        LOGGER.exception("Error inesperado en inventario.")
        print(f"Error inesperado inventario: {exc}")


if __name__ == "__main__":
    main()
