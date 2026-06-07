from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import zipfile
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from src.config import (
    DEFAULT_ARCHIVE_PATH,
    ENCODING,
    FIGURES_DIR,
    METADATA_DIR,
    ORDER_SAMPLE_ROWS,
    PROCESSED_DIR,
    RANDOM_SEED,
)


LOGGER = logging.getLogger("openlogi.data_cleaning")

ORDER_RAW_FILE: str = "DataCoSupplyChainDataset.csv"
LOG_RAW_FILE: str = "tokenized_access_logs.csv"
DESCRIPTION_RAW_FILE: str = "DescriptionDataCoSupplyChain.csv"

SENSITIVE_COLUMNS: set[str] = {
    "customer_email",
    "customer_fname",
    "customer_lname",
    "customer_password",
    "customer_street",
    "customer_zipcode",
    "latitude",
    "longitude",
    "ip",
    "url",
}

OPERATIVE_COLUMNS: list[str] = [
    "order_id",
    "order_item_id",
    "order_date",
    "shipping_date",
    "customer_id_hash",
    "customer_segment",
    "product_id",
    "product_name",
    "category_id",
    "category_name",
    "department_id",
    "department_name",
    "quantity",
    "sales",
    "order_item_total",
    "profit",
    "shipping_mode",
    "delivery_status",
    "late_delivery_risk",
    "order_status",
    "market",
    "order_region",
    "order_country",
    "order_city",
    "days_shipping_real",
    "days_shipping_scheduled",
]

REQUIRED_ORDER_COLUMNS: set[str] = {
    "order_id",
    "order_item_id",
    "order_date",
    "shipping_date",
    "product_id",
    "product_name",
    "quantity",
    "sales",
    "profit",
    "shipping_mode",
    "delivery_status",
    "late_delivery_risk",
    "market",
    "order_region",
    "order_country",
    "order_city",
    "days_shipping_real",
    "days_shipping_scheduled",
}


def configure_logging() -> None:
    """
    Configura la bitácora de eventos del pipeline de curación de datos.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def normalize_column_name(column_name: str) -> str:
    """
    Convierte un nombre de columna al estilo snake_case.

    Args:
        column_name: Nombre original de la columna.

    Returns:
        Nombre normalizado.
    """
    cleaned = column_name.strip()
    cleaned = re.sub(r"[\s\-/()]+", "_", cleaned)
    cleaned = re.sub(r"[^0-9a-zA-Z_]+", "", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_").lower()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza los nombres de columnas de un DataFrame.

    Args:
        df: DataFrame de entrada.

    Returns:
        Copia del DataFrame con columnas en snake_case.

    Raises:
        ValueError: Si el DataFrame está vacío.
    """
    if df.empty:
        raise ValueError("El DataFrame está vacío; no se pueden normalizar columnas.")

    result = df.copy()
    result.columns = [normalize_column_name(col) for col in result.columns]
    return result


def open_csv_from_archive(archive_path: Path, member_name: str) -> pd.DataFrame:
    """
    Lee un CSV desde un archivo ZIP.

    Args:
        archive_path: Ruta del archivo ZIP.
        member_name: Nombre del CSV dentro del ZIP.

    Returns:
        DataFrame leído con codificación latin1.

    Raises:
        FileNotFoundError: Si el ZIP no existe.
        ValueError: Si el miembro no está en el ZIP o si no puede leerse.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"No existe el archivo ZIP: {archive_path}")

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            if member_name not in archive.namelist():
                available = ", ".join(archive.namelist())
                raise ValueError(
                    f"No se encontró {member_name} dentro del ZIP. Disponibles: {available}"
                )

            with archive.open(member_name) as csv_file:
                df = pd.read_csv(csv_file, encoding=ENCODING)
                LOGGER.info("Archivo leído desde ZIP: %s | filas=%s", member_name, len(df))
                return df
    except zipfile.BadZipFile as exc:
        raise ValueError(f"El archivo no es un ZIP válido: {archive_path}") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"No fue posible parsear {member_name}: {exc}") from exc


def parse_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte las columnas de fecha del dataset principal.

    Args:
        df: DataFrame con columnas normalizadas.

    Returns:
        DataFrame con columnas de fecha convertidas.

    Raises:
        ValueError: Si no se pueden interpretar fechas obligatorias.
    """
    result = df.copy()
    rename_map = {
        "order_date_dateorders": "order_date",
        "shipping_date_dateorders": "shipping_date",
    }
    result = result.rename(columns=rename_map)

    for column in ["order_date", "shipping_date"]:
        if column not in result.columns:
            raise ValueError(f"Falta columna de fecha obligatoria: {column}")
        result[column] = pd.to_datetime(result[column], errors="coerce")

    if result[["order_date", "shipping_date"]].isna().any().any():
        bad_rows = int(result[["order_date", "shipping_date"]].isna().any(axis=1).sum())
        raise ValueError(f"Existen {bad_rows} filas con fechas inválidas.")

    return result


def hash_identifier(value: Any) -> str:
    """
    Genera un identificador anónimo y determinístico a partir de un valor.

    Args:
        value: Valor original a anonimizar.

    Returns:
        Identificador hash truncado para uso demo.
    """
    text = str(value).strip()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"cust_{digest[:16]}"


def clean_orders_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia, anonimiza y selecciona columnas logísticas del dataset DataCo.

    Args:
        raw_df: DataFrame original del archivo DataCoSupplyChainDataset.csv.

    Returns:
        DataFrame curado listo para dashboard y modelado.

    Raises:
        ValueError: Si faltan columnas requeridas o si hay tipos inválidos.
    """
    df = normalize_columns(raw_df)
    df = parse_datetime_columns(df)

    rename_map = {
        "product_card_id": "product_id",
        "order_item_quantity": "quantity",
        "order_profit_per_order": "profit",
        "days_for_shipping_real": "days_shipping_real",
        "days_for_shipment_scheduled": "days_shipping_scheduled",
    }
    df = df.rename(columns=rename_map)

    if "customer_id" not in df.columns:
        raise ValueError("Falta columna customer_id para generar hash anónimo.")

    df["customer_id_hash"] = df["customer_id"].apply(hash_identifier)

    numeric_columns: list[str] = [
        "order_id",
        "order_item_id",
        "product_id",
        "category_id",
        "department_id",
        "quantity",
        "sales",
        "order_item_total",
        "profit",
        "late_delivery_risk",
        "days_shipping_real",
        "days_shipping_scheduled",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    missing_operational = set(OPERATIVE_COLUMNS).difference(df.columns)
    if missing_operational:
        raise ValueError(
            "Faltan columnas operativas después de la limpieza: "
            + ", ".join(sorted(missing_operational))
        )

    orders = df[OPERATIVE_COLUMNS].copy()
    orders = orders.dropna(subset=list(REQUIRED_ORDER_COLUMNS))

    text_columns = orders.select_dtypes(include=["object"]).columns.tolist()
    for column in text_columns:
        orders[column] = orders[column].astype(str).str.strip()
        orders[column] = orders[column].replace({"": "UNKNOWN", "nan": "UNKNOWN"})

    orders["order_date_day"] = orders["order_date"].dt.date.astype(str)
    orders["order_month"] = orders["order_date"].dt.to_period("M").astype(str)
    orders["order_day_of_week"] = orders["order_date"].dt.day_name()
    orders["shipment_delay_delta"] = (
        orders["days_shipping_real"] - orders["days_shipping_scheduled"]
    )

    LOGGER.info("Órdenes limpias: filas=%s columnas=%s", len(orders), len(orders.columns))
    return orders


def create_orders_sample(orders: pd.DataFrame, sample_rows: int, random_seed: int) -> pd.DataFrame:
    """
    Crea una muestra reproducible del dataset limpio para despliegue web ligero.

    Args:
        orders: DataFrame de órdenes limpias.
        sample_rows: Número máximo de filas.
        random_seed: Semilla de muestreo.

    Returns:
        DataFrame muestreado y ordenado por fecha.
    """
    if len(orders) <= sample_rows:
        sample = orders.copy()
    else:
        sample = orders.sample(n=sample_rows, random_state=random_seed)

    sample = sample.sort_values(["order_date", "order_id", "order_item_id"]).reset_index(drop=True)
    return sample


def build_orders_daily_aggregation(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Construye agregados diarios para análisis ejecutivo.

    Args:
        orders: DataFrame de órdenes limpias.

    Returns:
        DataFrame agregado por fecha, producto, categoría, modo de envío, mercado y región.
    """
    group_columns: list[str] = [
        "order_date_day",
        "product_id",
        "product_name",
        "category_name",
        "department_name",
        "shipping_mode",
        "market",
        "order_region",
    ]

    aggregated = (
        orders.groupby(group_columns, dropna=False)
        .agg(
            order_count=("order_id", "nunique"),
            line_count=("order_item_id", "count"),
            quantity=("quantity", "sum"),
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            late_delivery_rate=("late_delivery_risk", "mean"),
            avg_days_shipping_real=("days_shipping_real", "mean"),
            avg_days_shipping_scheduled=("days_shipping_scheduled", "mean"),
        )
        .reset_index()
    )

    aggregated["order_date_day"] = pd.to_datetime(aggregated["order_date_day"])
    aggregated = aggregated.sort_values(["order_date_day", "product_id"]).reset_index(drop=True)
    return aggregated


def clean_access_logs_dataframe(raw_logs: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y agrega señales digitales de demanda desde los access logs.

    Args:
        raw_logs: DataFrame original de tokenized_access_logs.csv.

    Returns:
        DataFrame agregado por fecha, producto, categoría, departamento y hora.

    Raises:
        ValueError: Si faltan columnas mínimas.
    """
    logs = normalize_columns(raw_logs)

    required = {"product", "category", "date", "month", "hour", "department"}
    missing = required.difference(logs.columns)
    if missing:
        raise ValueError(
            "Faltan columnas obligatorias en access logs: "
            + ", ".join(sorted(missing))
        )

    logs = logs.drop(columns=[col for col in SENSITIVE_COLUMNS if col in logs.columns])
    logs["date"] = pd.to_datetime(logs["date"], errors="coerce")
    logs = logs.dropna(subset=["date"])

    for column in ["product", "category", "department", "month"]:
        logs[column] = logs[column].astype(str).str.strip()
        logs[column] = logs[column].replace({"": "UNKNOWN", "nan": "UNKNOWN"})

    logs["date_day"] = logs["date"].dt.date.astype(str)
    logs["hour"] = pd.to_numeric(logs["hour"], errors="coerce").fillna(-1).astype(int)

    aggregated_logs = (
        logs.groupby(["date_day", "product", "category", "department", "hour"], dropna=False)
        .agg(page_views=("product", "count"))
        .reset_index()
        .sort_values(["date_day", "page_views"], ascending=[True, False])
    )

    LOGGER.info("Access logs agregados: filas=%s", len(aggregated_logs))
    return aggregated_logs


def build_data_dictionary() -> pd.DataFrame:
    """
    Construye un diccionario de datos del dataset procesado.

    Returns:
        DataFrame con nombre de columna, descripción y origen.
    """
    descriptions: dict[str, tuple[str, str]] = {
        "order_id": ("Identificador de pedido.", "DataCo"),
        "order_item_id": ("Identificador de línea de pedido.", "DataCo"),
        "order_date": ("Fecha y hora de creación de la orden.", "DataCo"),
        "shipping_date": ("Fecha y hora de envío.", "DataCo"),
        "customer_id_hash": ("Cliente anonimizado con SHA-256 truncado.", "Derivado"),
        "customer_segment": ("Segmento de cliente.", "DataCo"),
        "product_id": ("Identificador de producto usado como SKU base.", "DataCo"),
        "product_name": ("Nombre del producto.", "DataCo"),
        "category_id": ("Identificador de categoría.", "DataCo"),
        "category_name": ("Nombre de categoría.", "DataCo"),
        "department_id": ("Identificador de departamento.", "DataCo"),
        "department_name": ("Nombre de departamento.", "DataCo"),
        "quantity": ("Cantidad solicitada en la línea de pedido.", "DataCo"),
        "sales": ("Venta bruta asociada a la línea.", "DataCo"),
        "order_item_total": ("Venta neta o total de línea.", "DataCo"),
        "profit": ("Utilidad de la orden/línea.", "DataCo"),
        "shipping_mode": ("Modo de envío.", "DataCo"),
        "delivery_status": ("Estado de entrega observado.", "DataCo"),
        "late_delivery_risk": ("Indicador objetivo de riesgo de entrega tardía.", "DataCo"),
        "order_status": ("Estado operativo de la orden.", "DataCo"),
        "market": ("Mercado logístico.", "DataCo"),
        "order_region": ("Región logística destino.", "DataCo"),
        "order_country": ("País destino.", "DataCo"),
        "order_city": ("Ciudad destino.", "DataCo"),
        "days_shipping_real": ("Días reales de envío.", "DataCo"),
        "days_shipping_scheduled": ("Días programados para el envío.", "DataCo"),
        "order_date_day": ("Fecha calendario de la orden.", "Derivado"),
        "order_month": ("Mes de la orden.", "Derivado"),
        "order_day_of_week": ("Día de la semana de la orden.", "Derivado"),
        "shipment_delay_delta": ("Diferencia entre días reales y programados.", "Derivado"),
    }

    rows: list[dict[str, str]] = []
    for column, (description, source) in descriptions.items():
        rows.append(
            {
                "column_name": column,
                "description": description,
                "source": source,
                "privacy_level": "anonymized" if column == "customer_id_hash" else "non_sensitive",
            }
        )

    return pd.DataFrame(rows)


def write_dataframe(df: pd.DataFrame, path: Path) -> None:
    """
    Guarda un DataFrame como CSV creando directorios si no existen.

    Args:
        df: DataFrame a escribir.
        path: Ruta destino del CSV.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    LOGGER.info("Archivo escrito: %s | filas=%s", path, len(df))


def build_quality_report(raw_orders: pd.DataFrame, clean_orders: pd.DataFrame) -> dict[str, Any]:
    """
    Construye un reporte JSON de calidad y curación de datos.

    Args:
        raw_orders: DataFrame original.
        clean_orders: DataFrame limpio.

    Returns:
        Diccionario con métricas de calidad.
    """
    missing_pct = (
        raw_orders.isna().mean().sort_values(ascending=False).head(20).round(4).to_dict()
    )

    report: dict[str, Any] = {
        "raw_rows": int(len(raw_orders)),
        "raw_columns": int(len(raw_orders.columns)),
        "clean_rows": int(len(clean_orders)),
        "clean_columns": int(len(clean_orders.columns)),
        "unique_orders": int(clean_orders["order_id"].nunique()),
        "unique_products": int(clean_orders["product_id"].nunique()),
        "unique_countries": int(clean_orders["order_country"].nunique()),
        "date_min": str(clean_orders["order_date"].min()),
        "date_max": str(clean_orders["order_date"].max()),
        "late_delivery_risk_rate": float(clean_orders["late_delivery_risk"].mean()),
        "top_missing_raw_columns_pct": missing_pct,
        "sensitive_columns_removed": sorted(SENSITIVE_COLUMNS),
    }

    return report


def save_json(data: dict[str, Any], path: Path) -> None:
    """
    Guarda un diccionario como archivo JSON.

    Args:
        data: Diccionario serializable.
        path: Ruta de salida.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("JSON escrito: %s", path)


def plot_monthly_orders(orders: pd.DataFrame, output_path: Path) -> None:
    """
    Genera una gráfica básica de pedidos por mes para validación visual del pipeline.

    Args:
        orders: DataFrame de órdenes limpias.
        output_path: Ruta PNG de salida.

    Returns:
        None.
    """
    monthly = (
        orders.groupby("order_month")
        .agg(order_count=("order_id", "nunique"))
        .reset_index()
        .sort_values("order_month")
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly["order_month"], monthly["order_count"], marker="o")
    ax.set_title("Pedidos únicos por mes")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Pedidos únicos")
    ax.tick_params(axis="x", rotation=90)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    LOGGER.info("Gráfica escrita: %s", output_path)


def print_console_report(report: dict[str, Any], output_dir: Path) -> None:
    """
    Imprime un reporte de ejecución en consola.

    Args:
        report: Reporte de calidad.
        output_dir: Carpeta de salida.

    Returns:
        None.
    """
    print("\n" + "=" * 72)
    print("OPENLOGI | FASE 1 - CURACIÓN DEL DATASET DATACO")
    print("=" * 72)
    print(f"Filas originales                 : {report['raw_rows']:,}")
    print(f"Columnas originales              : {report['raw_columns']:,}")
    print(f"Filas limpias                    : {report['clean_rows']:,}")
    print(f"Columnas limpias                 : {report['clean_columns']:,}")
    print(f"Órdenes únicas                   : {report['unique_orders']:,}")
    print(f"Productos únicos                 : {report['unique_products']:,}")
    print(f"Países destino                   : {report['unique_countries']:,}")
    print(f"Periodo                          : {report['date_min']} → {report['date_max']}")
    print(f"Tasa media de riesgo tardío      : {report['late_delivery_risk_rate']:.2%}")
    print(f"Salida                           : {output_dir}")
    print("=" * 72 + "\n")


def run_pipeline(archive_path: Path, processed_dir: Path) -> dict[str, Any]:
    """
    Ejecuta la fase 1 completa: lectura, limpieza, anonimización, agregación y reporte.

    Args:
        archive_path: Ruta del archivo archive.zip con los CSV originales.
        processed_dir: Carpeta donde se escribirán los CSV procesados.

    Returns:
        Reporte de calidad como diccionario.

    Raises:
        Exception: Propaga errores críticos ya registrados para fallar de forma trazable.
    """
    LOGGER.info("Inicio de pipeline de curación. ZIP=%s", archive_path)

    raw_orders = open_csv_from_archive(archive_path, ORDER_RAW_FILE)
    clean_orders = clean_orders_dataframe(raw_orders)
    orders_sample = create_orders_sample(clean_orders, ORDER_SAMPLE_ROWS, RANDOM_SEED)
    orders_daily = build_orders_daily_aggregation(clean_orders)

    raw_logs = open_csv_from_archive(archive_path, LOG_RAW_FILE)
    web_demand_daily = clean_access_logs_dataframe(raw_logs)

    data_dictionary = build_data_dictionary()
    quality_report = build_quality_report(raw_orders, clean_orders)

    write_dataframe(orders_sample, processed_dir / "orders_clean_sample.csv")
    write_dataframe(orders_daily, processed_dir / "orders_agg_daily.csv")
    write_dataframe(web_demand_daily, processed_dir / "web_demand_daily.csv")
    write_dataframe(data_dictionary, METADATA_DIR / "data_dictionary.csv")

    save_json(quality_report, processed_dir / "phase_01_data_quality_report.json")
    plot_monthly_orders(clean_orders, FIGURES_DIR / "orders_by_month.png")
    print_console_report(quality_report, processed_dir)

    return quality_report


def parse_args() -> argparse.Namespace:
    """
    Lee argumentos de línea de comandos.

    Returns:
        Namespace con rutas de entrada y salida.
    """
    parser = argparse.ArgumentParser(
        description="Fase 1: curación de DataCo para OpenLogi RFID/IoT Demo."
    )
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
        help="Carpeta de salida para datasets procesados.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Orquesta la ejecución del pipeline de curación con manejo de excepciones.

    Returns:
        None.
    """
    configure_logging()
    args = parse_args()

    try:
        run_pipeline(args.archive, args.processed_dir)
        LOGGER.info("Pipeline de curación completado correctamente.")
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Error controlado en Fase 1: %s", exc)
        print(f"Error de validación: {exc}")
    except Exception as exc:
        LOGGER.exception("Error inesperado en Fase 1.")
        print(f"Error inesperado: {exc}")


if __name__ == "__main__":
    main()
