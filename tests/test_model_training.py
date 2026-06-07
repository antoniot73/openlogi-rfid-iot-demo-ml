from __future__ import annotations

import pandas as pd
from sklearn.pipeline import Pipeline

from src.model_training import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
    build_model_pipeline,
    normalize_model_frame,
    split_features_target,
)


def build_minimal_model_frame() -> pd.DataFrame:
    """
    Construye un DataFrame mínimo para validar funciones de entrenamiento.

    Returns:
        DataFrame con columnas requeridas.
    """
    rows: list[dict[str, object]] = []

    for index in range(6):
        row: dict[str, object] = {
            "shipping_mode": "Standard Class" if index % 2 == 0 else "Second Class",
            "market": "LATAM",
            "order_region": "South America",
            "order_country": "Brasil",
            "order_city": "São Paulo",
            "customer_segment": "Consumer",
            "category_name": "Cleats",
            "department_name": "Apparel",
            "product_id": 365,
            "order_month": "2015-01",
            "order_day_of_week": "Thursday",
            "days_shipping_scheduled": 4,
            "quantity": index + 1,
            "sales": 100.0 + index,
            "late_delivery_risk": index % 2,
        }
        rows.append(row)

    return pd.DataFrame(rows)


def test_normalize_model_frame_returns_expected_types() -> None:
    """
    Valida normalización de categóricas, numéricas y objetivo.
    """
    df = build_minimal_model_frame()
    normalized = normalize_model_frame(df)

    for column in CATEGORICAL_FEATURES:
        assert normalized[column].dtype == object

    for column in NUMERICAL_FEATURES:
        assert str(normalized[column].dtype).startswith("float")

    assert set(normalized[TARGET_COLUMN].unique()) == {0, 1}


def test_split_features_target_uses_allowed_columns() -> None:
    """
    Valida separación de X e y con columnas permitidas.
    """
    df = normalize_model_frame(build_minimal_model_frame())
    x, y = split_features_target(df)

    assert list(x.columns) == CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    assert y.name == TARGET_COLUMN


def test_build_model_pipeline_returns_pipeline() -> None:
    """
    Valida construcción del pipeline de scikit-learn.
    """
    pipeline = build_model_pipeline()

    assert isinstance(pipeline, Pipeline)
    assert "preprocessor" in pipeline.named_steps
    assert "classifier" in pipeline.named_steps
