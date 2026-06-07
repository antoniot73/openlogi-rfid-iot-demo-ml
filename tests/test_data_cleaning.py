from __future__ import annotations

import pandas as pd

from src.data_cleaning import hash_identifier, normalize_column_name, normalize_columns


def test_normalize_column_name() -> None:
    """Valida conversión simple a snake_case."""
    assert normalize_column_name("Order Date (DateOrders)") == "order_date_dateorders"


def test_hash_identifier_is_deterministic() -> None:
    """Valida que el hash anónimo sea determinístico y no vacío."""
    first = hash_identifier(123)
    second = hash_identifier(123)
    assert first == second
    assert first.startswith("cust_")
    assert len(first) > len("cust_")


def test_normalize_columns() -> None:
    """Valida normalización de columnas en DataFrame."""
    df = pd.DataFrame({"Column A": [1], "Column-B": [2]})
    normalized = normalize_columns(df)
    assert list(normalized.columns) == ["column_a", "column_b"]
