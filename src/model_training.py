from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import MODELS_DIR, PROCESSED_DIR, RANDOM_SEED


LOGGER = logging.getLogger("openlogi.model_training")

TARGET_COLUMN: str = "late_delivery_risk"

CATEGORICAL_FEATURES: list[str] = [
    "shipping_mode",
    "market",
    "order_region",
    "order_country",
    "order_city",
    "customer_segment",
    "category_name",
    "department_name",
    "product_id",
    "order_month",
    "order_day_of_week",
]

NUMERICAL_FEATURES: list[str] = [
    "days_shipping_scheduled",
    "quantity",
    "sales",
]

LEAKAGE_COLUMNS: list[str] = [
    "delivery_status",
    "days_shipping_real",
    "shipping_date",
    "order_status",
    "shipment_delay_delta",
]

MODEL_PATH: Path = MODELS_DIR / "late_delivery_model.joblib"
METRICS_PATH: Path = MODELS_DIR / "model_metrics.json"
FEATURE_IMPORTANCE_PATH: Path = MODELS_DIR / "feature_importance.csv"
PREDICTIONS_SAMPLE_PATH: Path = MODELS_DIR / "late_delivery_predictions_sample.csv"
FEATURE_SCHEMA_PATH: Path = MODELS_DIR / "feature_schema.json"


def configure_logging() -> None:
    """
    Configura la bitácora de eventos para el entrenamiento del modelo.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def validate_columns(df: pd.DataFrame, required_columns: list[str]) -> None:
    """
    Verifica que un DataFrame contenga las columnas requeridas.

    Args:
        df: DataFrame que será validado.
        required_columns: Lista de columnas obligatorias.

    Raises:
        ValueError: Si faltan columnas requeridas.
    """
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Faltan columnas requeridas para el modelo: {missing_text}")


def load_orders(path: Path) -> pd.DataFrame:
    """
    Carga el archivo de órdenes limpias para entrenamiento.

    Args:
        path: Ruta del archivo CSV de órdenes limpias.

    Returns:
        DataFrame con órdenes limpias.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el archivo está vacío o no contiene la variable objetivo.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de órdenes: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"El archivo está vacío: {path}")

    required_columns = CATEGORICAL_FEATURES + NUMERICAL_FEATURES + [TARGET_COLUMN]
    validate_columns(df, required_columns)

    LOGGER.info("Órdenes cargadas para entrenamiento: filas=%s", len(df))
    return df


def normalize_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza tipos y valores para las variables del modelo.

    Las variables categóricas se convierten a texto y las numéricas se convierten
    a valores flotantes. Los faltantes se imputan con valores simples y reproducibles
    para mantener un pipeline robusto en la demo.

    Args:
        df: DataFrame con variables originales.

    Returns:
        DataFrame normalizado con variables del modelo y objetivo.
    """
    result = df.copy()

    for column in CATEGORICAL_FEATURES:
        result[column] = result[column].fillna("UNKNOWN").astype(str).str.strip()
        result.loc[result[column] == "", column] = "UNKNOWN"
        result[column] = result[column].astype(object)

    for column in NUMERICAL_FEATURES:
        numeric = pd.to_numeric(result[column], errors="coerce")
        median_value = float(numeric.median()) if not numeric.dropna().empty else 0.0
        result[column] = numeric.fillna(median_value).astype(float)

    result[TARGET_COLUMN] = pd.to_numeric(result[TARGET_COLUMN], errors="coerce")

    if result[TARGET_COLUMN].isna().any():
        raise ValueError("La variable objetivo contiene valores inválidos.")

    result[TARGET_COLUMN] = result[TARGET_COLUMN].astype(int)

    invalid_targets = set(result[TARGET_COLUMN].unique()).difference({0, 1})
    if invalid_targets:
        raise ValueError(f"La variable objetivo contiene clases inválidas: {invalid_targets}")

    LOGGER.info("Frame de modelado normalizado correctamente.")
    return result


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Separa variables predictoras y variable objetivo.

    Args:
        df: DataFrame normalizado.

    Returns:
        Tupla con X e y.
    """
    feature_columns = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    x = df[feature_columns].copy()
    y = df[TARGET_COLUMN].copy()
    return x, y


def build_preprocessor() -> ColumnTransformer:
    """
    Construye el preprocesador de variables categóricas y numéricas.

    Returns:
        ColumnTransformer con OneHotEncoder para categóricas y StandardScaler
        para variables numéricas.
    """
    categorical_encoder = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        min_frequency=25,
        sparse_output=True,
    )

    numerical_scaler = StandardScaler()

    return ColumnTransformer(
        transformers=[
            ("categorical", categorical_encoder, CATEGORICAL_FEATURES),
            ("numerical", numerical_scaler, NUMERICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_model_pipeline() -> Pipeline:
    """
    Construye el pipeline de entrenamiento para riesgo de entrega tardía.

    Returns:
        Pipeline de scikit-learn con preprocesamiento y regresión logística.
    """
    classifier = LogisticRegression(
        max_iter=1000,
        solver="saga",
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("classifier", classifier),
        ]
    )

    return pipeline


def evaluate_model(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    """
    Evalúa el modelo entrenado sobre datos de prueba.

    Args:
        model: Pipeline entrenado.
        x_test: Variables predictoras de prueba.
        y_test: Variable objetivo de prueba.

    Returns:
        Diccionario con métricas de clasificación.
    """
    y_pred = model.predict(x_test)
    y_proba = model.predict_proba(x_test)[:, 1]

    matrix = confusion_matrix(y_test, y_pred, labels=[0, 1])

    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "confusion_matrix": {
            "labels": [0, 1],
            "matrix": matrix.astype(int).tolist(),
        },
    }

    LOGGER.info("Métricas calculadas: %s", metrics)
    return metrics


def extract_feature_importance(model: Pipeline) -> pd.DataFrame:
    """
    Extrae importancia aproximada de variables a partir de coeficientes absolutos.

    Args:
        model: Pipeline entrenado con regresión logística.

    Returns:
        DataFrame ordenado con importancia de características transformadas.
    """
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]

    feature_names = preprocessor.get_feature_names_out()
    coefficients = classifier.coef_[0]

    importance = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "abs_importance": np.abs(coefficients),
        }
    ).sort_values("abs_importance", ascending=False)

    importance["rank"] = np.arange(1, len(importance) + 1)
    return importance[["rank", "feature", "coefficient", "abs_importance"]]


def build_predictions_sample(
    model: Pipeline,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    sample_rows: int = 500,
) -> pd.DataFrame:
    """
    Construye una muestra de predicciones para revisión en la aplicación.

    Args:
        model: Pipeline entrenado.
        x_test: Variables predictoras de prueba.
        y_test: Variable objetivo de prueba.
        sample_rows: Número máximo de filas a exportar.

    Returns:
        DataFrame con variables, clase real, clase predicha y probabilidad.
    """
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = model.predict(x_test)

    sample = x_test.copy()
    sample["late_delivery_risk_real"] = y_test.to_numpy()
    sample["late_delivery_risk_pred"] = predictions
    sample["late_delivery_risk_probability"] = probabilities

    return sample.head(sample_rows).copy()


def build_feature_schema(df: pd.DataFrame) -> dict[str, Any]:
    """
    Construye un esquema de variables para alimentar el simulador en Streamlit.

    Args:
        df: DataFrame normalizado de entrenamiento.

    Returns:
        Diccionario con variables categóricas, numéricas, opciones y valores por defecto.
    """
    categorical_options: dict[str, list[str]] = {}
    categorical_defaults: dict[str, str] = {}

    for column in CATEGORICAL_FEATURES:
        value_counts = df[column].value_counts(dropna=True)
        options = value_counts.index.astype(str).tolist()

        if len(options) > 80:
            options = options[:80]

        categorical_options[column] = options
        categorical_defaults[column] = options[0] if options else "UNKNOWN"

    numerical_defaults: dict[str, float] = {}
    numerical_min: dict[str, float] = {}
    numerical_max: dict[str, float] = {}

    for column in NUMERICAL_FEATURES:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        numerical_defaults[column] = float(series.median()) if not series.empty else 0.0
        numerical_min[column] = float(series.min()) if not series.empty else 0.0
        numerical_max[column] = float(series.max()) if not series.empty else 1.0

    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_column": TARGET_COLUMN,
        "categorical_features": CATEGORICAL_FEATURES,
        "numerical_features": NUMERICAL_FEATURES,
        "leakage_columns_excluded": LEAKAGE_COLUMNS,
        "categorical_options": categorical_options,
        "categorical_defaults": categorical_defaults,
        "numerical_defaults": numerical_defaults,
        "numerical_min": numerical_min,
        "numerical_max": numerical_max,
        "model_type": "LogisticRegression + OneHotEncoder + StandardScaler",
        "random_seed": RANDOM_SEED,
    }


def save_json(data: dict[str, Any], path: Path) -> None:
    """
    Guarda un diccionario en formato JSON.

    Args:
        data: Diccionario a guardar.
        path: Ruta de salida.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("JSON guardado: %s", path)


def save_outputs(
    model: Pipeline,
    metrics: dict[str, Any],
    feature_importance: pd.DataFrame,
    predictions_sample: pd.DataFrame,
    feature_schema: dict[str, Any],
) -> None:
    """
    Guarda modelo, métricas, importancia, muestra de predicciones y esquema.

    Args:
        model: Pipeline entrenado.
        metrics: Métricas de evaluación.
        feature_importance: Importancia de características.
        predictions_sample: Muestra de predicciones.
        feature_schema: Esquema de variables para simulador.

    Returns:
        None.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    LOGGER.info("Modelo guardado: %s", MODEL_PATH)

    save_json(metrics, METRICS_PATH)
    save_json(feature_schema, FEATURE_SCHEMA_PATH)

    feature_importance.to_csv(FEATURE_IMPORTANCE_PATH, index=False)
    LOGGER.info("Importancia de variables guardada: %s", FEATURE_IMPORTANCE_PATH)

    predictions_sample.to_csv(PREDICTIONS_SAMPLE_PATH, index=False)
    LOGGER.info("Muestra de predicciones guardada: %s", PREDICTIONS_SAMPLE_PATH)


def build_console_report(metrics: dict[str, Any], train_rows: int, test_rows: int) -> str:
    """
    Construye un reporte textual de entrenamiento.

    Args:
        metrics: Métricas calculadas.
        train_rows: Número de registros de entrenamiento.
        test_rows: Número de registros de prueba.

    Returns:
        Reporte en formato texto.
    """
    return (
        "\n--- REPORTE FASE 5: MODELO DE RIESGO TARDÍO ---\n"
        f"Registros de entrenamiento: {train_rows:,}\n"
        f"Registros de prueba: {test_rows:,}\n"
        f"Accuracy: {metrics['accuracy']:.4f}\n"
        f"Precision: {metrics['precision']:.4f}\n"
        f"Recall: {metrics['recall']:.4f}\n"
        f"F1-score: {metrics['f1_score']:.4f}\n"
        f"ROC-AUC: {metrics['roc_auc']:.4f}\n"
        "Variables excluidas por fuga de información: "
        f"{', '.join(LEAKAGE_COLUMNS)}\n"
        "------------------------------------------------\n"
    )


def train_late_delivery_model(orders_path: Path) -> dict[str, Any]:
    """
    Entrena y guarda el modelo de riesgo de entrega tardía.

    Args:
        orders_path: Ruta del archivo orders_clean_sample.csv.

    Returns:
        Diccionario de métricas enriquecido con metadatos de entrenamiento.
    """
    raw_orders = load_orders(orders_path)
    model_frame = normalize_model_frame(raw_orders)
    x, y = split_features_target(model_frame)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        stratify=y,
        random_state=RANDOM_SEED,
    )

    model = build_model_pipeline()
    LOGGER.info("Inicio de entrenamiento del modelo.")
    model.fit(x_train, y_train)
    LOGGER.info("Entrenamiento finalizado.")

    metrics = evaluate_model(model, x_test, y_test)
    metrics.update(
        {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "model_name": "late_delivery_risk_logistic_regression",
            "target_column": TARGET_COLUMN,
            "train_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
            "total_rows": int(len(x)),
            "positive_class_rate_total": float(y.mean()),
            "positive_class_rate_train": float(y_train.mean()),
            "positive_class_rate_test": float(y_test.mean()),
            "features": {
                "categorical": CATEGORICAL_FEATURES,
                "numerical": NUMERICAL_FEATURES,
            },
            "leakage_columns_excluded": LEAKAGE_COLUMNS,
            "decision_threshold": 0.5,
        }
    )

    feature_importance = extract_feature_importance(model)
    predictions_sample = build_predictions_sample(model, x_test, y_test)
    feature_schema = build_feature_schema(model_frame)

    save_outputs(model, metrics, feature_importance, predictions_sample, feature_schema)

    report = build_console_report(metrics, len(x_train), len(x_test))
    print(report)
    LOGGER.info(report)

    return metrics


def parse_args() -> argparse.Namespace:
    """
    Procesa argumentos de línea de comandos.

    Returns:
        Namespace con argumentos del script.
    """
    parser = argparse.ArgumentParser(
        description="Entrena el modelo de riesgo de entrega tardía de OpenLogi."
    )
    parser.add_argument(
        "--orders",
        type=Path,
        default=PROCESSED_DIR / "orders_clean_sample.csv",
        help="Ruta al archivo orders_clean_sample.csv.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Ejecuta el flujo de entrenamiento de la Fase 5.

    Returns:
        None.
    """
    configure_logging()
    args = parse_args()

    try:
        train_late_delivery_model(args.orders)
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Error controlado en entrenamiento: %s", exc)
        raise
    except Exception as exc:
        LOGGER.exception("Error inesperado en entrenamiento: %s", exc)
        raise


if __name__ == "__main__":
    main()
