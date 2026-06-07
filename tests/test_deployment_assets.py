from __future__ import annotations

from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


def test_phase_6_assets_exist() -> None:
    """
    Valida que los artefactos de presentación y despliegue de Fase 6 existan.
    """
    required_paths = [
        PROJECT_ROOT / ".streamlit" / "config.toml",
        PROJECT_ROOT / "docs" / "deployment_guide.md",
        PROJECT_ROOT / "docs" / "presentation_script.md",
        PROJECT_ROOT / "docs" / "release_checklist.md",
        PROJECT_ROOT / "src" / "deployment_checks.py",
    ]

    for path in required_paths:
        assert path.exists(), f"No existe el artefacto requerido: {path}"
        assert path.stat().st_size > 0, f"El artefacto está vacío: {path}"


def test_raw_archive_is_not_required_for_deploy() -> None:
    """
    Verifica que la app desplegada no dependa del ZIP original.

    El archivo data/raw/archive.zip puede existir en desarrollo local para regenerar
    datos, pero no debe ser requerido por app.py ni por la validación de despliegue.
    """
    processed_orders = PROJECT_ROOT / "data" / "processed" / "orders_clean_sample.csv"
    app_path = PROJECT_ROOT / "app.py"
    gitignore_path = PROJECT_ROOT / ".gitignore"

    assert processed_orders.exists(), "Falta el dataset procesado requerido para la demo."
    assert app_path.exists(), "Falta app.py."

    app_text = app_path.read_text(encoding="utf-8")
    assert "data/raw/archive.zip" not in app_text
    assert "archive.zip" not in app_text

    if gitignore_path.exists():
        gitignore_text = gitignore_path.read_text(encoding="utf-8")
        assert "data/raw/*" in gitignore_text
        assert "*.zip" in gitignore_text
