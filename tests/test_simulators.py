from __future__ import annotations

import pandas as pd

from src.inventory_simulator import classify_inventory_status
from src.rfid_simulator import build_epc, build_lot_id


def test_build_epc() -> None:
    """Valida construcción de EPC sintético."""
    row = pd.Series({"product_id": 10, "order_id": 20, "order_item_id": 30})
    assert build_epc(row) == "EPC-10-20-30"


def test_build_lot_id() -> None:
    """Valida construcción de lote sintético."""
    row = pd.Series({"product_id": 10, "order_month": "2026-06"})
    assert build_lot_id(row) == "LOT-10-202606"


def test_classify_inventory_status() -> None:
    """Valida clasificación básica de inventario."""
    assert classify_inventory_status(5, 10) == "LOW_STOCK"
    assert classify_inventory_status(12, 10) == "WATCH"
    assert classify_inventory_status(20, 10) == "NORMAL"
