from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import altair as alt
import joblib
import pandas as pd
import streamlit as st


LOGGER = logging.getLogger("openlogi.app")

PROJECT_ROOT: Path = Path(__file__).resolve().parent
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
METADATA_DIR: Path = PROJECT_ROOT / "data" / "metadata"
MODELS_DIR: Path = PROJECT_ROOT / "models"

DATA_FILES: dict[str, Path] = {
    "orders": PROCESSED_DIR / "orders_clean_sample.csv",
    "orders_daily": PROCESSED_DIR / "orders_agg_daily.csv",
    "rfid": PROCESSED_DIR / "rfid_events_demo.csv",
    "iot": PROCESSED_DIR / "iot_events_demo.csv",
    "inventory": PROCESSED_DIR / "inventory_snapshot_demo.csv",
    "quality": PROCESSED_DIR / "phase_01_data_quality_report.json",
    "dictionary": METADATA_DIR / "data_dictionary.csv",
}

MODEL_FILES: dict[str, Path] = {
    "model": MODELS_DIR / "late_delivery_model.joblib",
    "metrics": MODELS_DIR / "model_metrics.json",
    "importance": MODELS_DIR / "feature_importance.csv",
    "schema": MODELS_DIR / "feature_schema.json",
    "predictions_sample": MODELS_DIR / "late_delivery_predictions_sample.csv",
}


def configure_logging() -> None:
    """
    Configura la bitácora básica de la aplicación Streamlit.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def validate_file(path: Path) -> None:
    """
    Valida que un archivo exista antes de cargarlo.

    Args:
        path: Ruta del archivo.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo requerido: {path}")


@st.cache_data(show_spinner=False)
def load_csv(path_text: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    """
    Carga un archivo CSV con cache de Streamlit.

    Args:
        path_text: Ruta del archivo como texto.
        parse_dates: Columnas a interpretar como fecha.

    Returns:
        DataFrame cargado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el CSV está vacío.
    """
    path = Path(path_text)
    validate_file(path)

    df = pd.read_csv(path, parse_dates=parse_dates)

    if df.empty:
        raise ValueError(f"El archivo está vacío: {path}")

    LOGGER.info("CSV cargado: %s | filas=%s", path.name, len(df))
    return df


@st.cache_data(show_spinner=False)
def load_quality_report(path_text: str) -> dict[str, Any]:
    """
    Carga un archivo JSON con métricas o metadatos.

    Args:
        path_text: Ruta del JSON.

    Returns:
        Diccionario con métricas o metadatos del pipeline.
    """
    path = Path(path_text)
    validate_file(path)
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def load_model(path_text: str) -> Any:
    """
    Carga el modelo entrenado de riesgo de entrega tardía.

    Args:
        path_text: Ruta del archivo joblib del modelo.

    Returns:
        Modelo entrenado compatible con predict_proba.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    path = Path(path_text)
    validate_file(path)
    model = joblib.load(path)
    LOGGER.info("Modelo cargado: %s", path.name)
    return model


def load_model_artifacts() -> dict[str, Any]:
    """
    Carga métricas, importancia de variables, esquema y modelo predictivo.

    Returns:
        Diccionario con artefactos de la Fase 5.
    """
    artifacts: dict[str, Any] = {
        "model": load_model(str(MODEL_FILES["model"])),
        "metrics": load_quality_report(str(MODEL_FILES["metrics"])),
        "importance": load_csv(str(MODEL_FILES["importance"])),
        "schema": load_quality_report(str(MODEL_FILES["schema"])),
        "predictions_sample": load_csv(str(MODEL_FILES["predictions_sample"])),
    }
    return artifacts


def load_all_data() -> dict[str, pd.DataFrame | dict[str, Any]]:
    """
    Carga todos los datasets procesados del demo.

    Returns:
        Diccionario con DataFrames y reporte JSON.
    """
    data: dict[str, pd.DataFrame | dict[str, Any]] = {
        "orders": load_csv(str(DATA_FILES["orders"]), ["order_date", "shipping_date"]),
        "orders_daily": load_csv(str(DATA_FILES["orders_daily"]), ["order_date_day"]),
        "rfid": load_csv(str(DATA_FILES["rfid"]), ["timestamp"]),
        "iot": load_csv(str(DATA_FILES["iot"]), ["timestamp"]),
        "inventory": load_csv(str(DATA_FILES["inventory"])),
        "dictionary": load_csv(str(DATA_FILES["dictionary"])),
        "quality": load_quality_report(str(DATA_FILES["quality"])),
    }
    return data


def apply_sidebar_filters(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica filtros laterales al dataset de órdenes.

    Args:
        orders: DataFrame de órdenes.

    Returns:
        DataFrame filtrado.
    """
    st.sidebar.header("Filtros")

    markets = sorted(orders["market"].dropna().unique().tolist())
    selected_markets = st.sidebar.multiselect("Mercado", markets, default=markets)

    shipping_modes = sorted(orders["shipping_mode"].dropna().unique().tolist())
    selected_shipping = st.sidebar.multiselect(
        "Modo de envío",
        shipping_modes,
        default=shipping_modes,
    )

    categories = sorted(orders["category_name"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Categoría",
        categories,
        default=categories[: min(len(categories), 10)],
    )

    if len(selected_markets) == 0 or len(selected_shipping) == 0 or len(selected_categories) == 0:
        return orders.iloc[0:0].copy()

    filtered = orders[
        orders["market"].isin(selected_markets)
        & orders["shipping_mode"].isin(selected_shipping)
        & orders["category_name"].isin(selected_categories)
    ].copy()

    LOGGER.info("Órdenes filtradas: filas=%s", len(filtered))
    return filtered


def render_kpis(orders: pd.DataFrame, rfid: pd.DataFrame, iot: pd.DataFrame, inventory: pd.DataFrame) -> None:
    """
    Renderiza KPIs ejecutivos.

    Args:
        orders: Órdenes filtradas.
        rfid: Eventos RFID.
        iot: Eventos IoT.
        inventory: Inventario simulado.

    Returns:
        None.
    """
    total_orders = int(orders["order_id"].nunique())
    total_sales = float(orders["sales"].sum())
    late_rate = float(orders["late_delivery_risk"].mean()) if len(orders) > 0 else 0.0
    low_stock = int((inventory["inventory_status"] == "LOW_STOCK").sum())
    iot_alerts = int((iot["iot_status"] != "NORMAL").sum())
    rfid_events = int(len(rfid))

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Órdenes", f"{total_orders:,}")
    col2.metric("Ventas", f"${total_sales:,.0f}")
    col3.metric("Riesgo tardío", f"{late_rate:.1%}")
    col4.metric("Eventos RFID", f"{rfid_events:,}")
    col5.metric("Alertas IoT", f"{iot_alerts:,}")
    col6.metric("LOW_STOCK", f"{low_stock:,}")


def build_orders_by_month_chart(orders: pd.DataFrame) -> alt.Chart:
    """
    Construye gráfica de órdenes por mes.

    Args:
        orders: DataFrame de órdenes filtradas.

    Returns:
        Gráfica Altair.
    """
    monthly = (
        orders.groupby("order_month", as_index=False)
        .agg(order_count=("order_id", "nunique"), sales=("sales", "sum"))
        .sort_values("order_month")
    )

    return (
        alt.Chart(monthly)
        .mark_line(point=True)
        .encode(
            x=alt.X("order_month:N", title="Mes"),
            y=alt.Y("order_count:Q", title="Órdenes"),
            tooltip=["order_month", "order_count", alt.Tooltip("sales:Q", format=",.2f")],
        )
        .properties(height=320)
    )


def build_late_risk_by_shipping_chart(orders: pd.DataFrame) -> alt.Chart:
    """
    Construye gráfica de riesgo tardío por modo de envío.

    Args:
        orders: DataFrame de órdenes filtradas.

    Returns:
        Gráfica Altair.
    """
    grouped = (
        orders.groupby("shipping_mode", as_index=False)
        .agg(late_delivery_rate=("late_delivery_risk", "mean"), order_count=("order_id", "nunique"))
        .sort_values("late_delivery_rate", ascending=False)
    )

    return (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("shipping_mode:N", title="Modo de envío"),
            y=alt.Y("late_delivery_rate:Q", title="Tasa de riesgo tardío", axis=alt.Axis(format="%")),
            tooltip=["shipping_mode", alt.Tooltip("late_delivery_rate:Q", format=".2%"), "order_count"],
        )
        .properties(height=320)
    )


def render_summary_tab(orders: pd.DataFrame, rfid: pd.DataFrame, iot: pd.DataFrame, inventory: pd.DataFrame) -> None:
    """
    Renderiza pestaña resumen.

    Args:
        orders: Órdenes filtradas.
        rfid: Eventos RFID.
        iot: Eventos IoT.
        inventory: Inventario.

    Returns:
        None.
    """
    render_kpis(orders, rfid, iot, inventory)

    if orders.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Órdenes por mes")
        st.altair_chart(build_orders_by_month_chart(orders), width="stretch")

    with col2:
        st.subheader("Riesgo tardío por modo de envío")
        st.altair_chart(build_late_risk_by_shipping_chart(orders), width="stretch")


def render_orders_tab(orders: pd.DataFrame) -> None:
    """
    Renderiza análisis de pedidos y entregas.

    Args:
        orders: Órdenes filtradas.

    Returns:
        None.
    """
    st.subheader("Pedidos y entregas")

    if orders.empty:
        st.warning("No hay órdenes con los filtros actuales.")
        return

    grouped = (
        orders.groupby(["market", "order_region", "shipping_mode"], as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            sales=("sales", "sum"),
            late_delivery_rate=("late_delivery_risk", "mean"),
            avg_days_real=("days_shipping_real", "mean"),
        )
        .sort_values("late_delivery_rate", ascending=False)
    )

    st.dataframe(grouped, width="stretch")
    st.download_button(
        "Descargar pedidos filtrados",
        data=orders.to_csv(index=False).encode("utf-8"),
        file_name="openlogi_orders_filtered.csv",
        mime="text/csv",
    )


def render_rfid_tab(rfid: pd.DataFrame, orders: pd.DataFrame) -> None:
    """
    Renderiza trazabilidad RFID simulada.

    Args:
        rfid: DataFrame de eventos RFID.
        orders: DataFrame de órdenes filtradas.

    Returns:
        None.
    """
    st.subheader("Trazabilidad RFID simulada")

    if orders.empty:
        st.warning("Seleccione filtros con órdenes disponibles.")
        return

    candidate_orders = sorted(orders["order_id"].dropna().astype(int).unique().tolist())
    selected_order = st.selectbox("Seleccionar order_id", candidate_orders)

    selected_events = rfid[rfid["order_id"] == selected_order].sort_values("timestamp")

    if selected_events.empty:
        st.warning("No hay eventos RFID para el pedido seleccionado.")
        return

    st.dataframe(selected_events, width="stretch")

    timeline = (
        alt.Chart(selected_events)
        .mark_circle(size=100)
        .encode(
            x=alt.X("timestamp:T", title="Tiempo"),
            y=alt.Y("event_type:N", title="Evento"),
            tooltip=["timestamp", "epc", "reader_id", "antenna_id", "location", "rssi"],
        )
        .properties(height=320)
    )
    st.altair_chart(timeline, width="stretch")


def render_iot_tab(iot: pd.DataFrame, orders: pd.DataFrame) -> None:
    """
    Renderiza monitoreo IoT simulado.

    Args:
        iot: Eventos IoT.
        orders: Órdenes filtradas.

    Returns:
        None.
    """
    st.subheader("Monitoreo IoT simulado")

    valid_orders = set(orders["order_id"].dropna().astype(int).unique().tolist())
    filtered_iot = iot[iot["order_id"].isin(valid_orders)].copy()

    if filtered_iot.empty:
        st.warning("No hay eventos IoT para los filtros actuales.")
        return

    alerts = filtered_iot[filtered_iot["iot_status"] != "NORMAL"].copy()

    status_summary = (
        filtered_iot.groupby("iot_status", as_index=False)
        .agg(events=("iot_status", "count"))
        .sort_values("events", ascending=False)
    )

    chart = (
        alt.Chart(status_summary)
        .mark_bar()
        .encode(
            x=alt.X("iot_status:N", title="Estado IoT"),
            y=alt.Y("events:Q", title="Eventos"),
            tooltip=["iot_status", "events"],
        )
        .properties(height=300)
    )

    st.altair_chart(chart, width="stretch")
    st.subheader("Alertas IoT")
    st.dataframe(alerts.head(500), width="stretch")


def render_inventory_tab(inventory: pd.DataFrame) -> None:
    """
    Renderiza inventario y reorden.

    Args:
        inventory: Inventario simulado.

    Returns:
        None.
    """
    st.subheader("Inventario WMS sintético")

    status_filter = st.multiselect(
        "Estado de inventario",
        sorted(inventory["inventory_status"].unique().tolist()),
        default=sorted(inventory["inventory_status"].unique().tolist()),
    )

    if len(status_filter) == 0:
        st.warning("Seleccione al menos un estado.")
        return

    filtered = inventory[inventory["inventory_status"].isin(status_filter)].copy()
    st.dataframe(filtered, width="stretch")

    top_reorder = filtered.sort_values("recommended_order_qty", ascending=False).head(20)

    chart = (
        alt.Chart(top_reorder)
        .mark_bar()
        .encode(
            x=alt.X("recommended_order_qty:Q", title="Cantidad sugerida"),
            y=alt.Y("product_name:N", title="Producto", sort="-x"),
            tooltip=["product_id", "product_name", "warehouse_id", "recommended_order_qty", "inventory_status"],
        )
        .properties(height=420)
    )
    st.altair_chart(chart, width="stretch")



def format_feature_label(feature_name: str) -> str:
    """
    Convierte un nombre técnico de variable en una etiqueta legible.

    Args:
        feature_name: Nombre técnico en snake_case.

    Returns:
        Etiqueta legible para la interfaz.
    """
    labels: dict[str, str] = {
        "shipping_mode": "Modo de envío",
        "market": "Mercado",
        "order_region": "Región",
        "order_country": "País destino",
        "order_city": "Ciudad destino",
        "customer_segment": "Segmento de cliente",
        "category_name": "Categoría",
        "department_name": "Departamento",
        "product_id": "ID de producto",
        "order_month": "Mes de orden",
        "order_day_of_week": "Día de la semana",
        "days_shipping_scheduled": "Días programados de envío",
        "quantity": "Cantidad",
        "sales": "Venta",
    }
    return labels.get(feature_name, feature_name.replace("_", " ").title())


def build_metrics_dataframe(metrics: dict[str, Any]) -> pd.DataFrame:
    """
    Construye una tabla resumen de métricas del modelo.

    Args:
        metrics: Diccionario con métricas del modelo.

    Returns:
        DataFrame con métricas principales.
    """
    metric_names = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    rows: list[dict[str, Any]] = []

    for metric_name in metric_names:
        value = float(metrics.get(metric_name, 0.0))
        rows.append(
            {
                "metric": metric_name,
                "value": value,
                "value_percent": f"{value:.2%}",
            }
        )

    return pd.DataFrame(rows)


def build_confusion_matrix_dataframe(metrics: dict[str, Any]) -> pd.DataFrame:
    """
    Construye una matriz de confusión en formato tabular.

    Args:
        metrics: Diccionario con métricas y matriz de confusión.

    Returns:
        DataFrame con matriz de confusión.
    """
    matrix_payload = metrics.get("confusion_matrix", {})
    matrix = matrix_payload.get("matrix", [[0, 0], [0, 0]])

    return pd.DataFrame(
        matrix,
        index=["Real 0: sin riesgo", "Real 1: riesgo tardío"],
        columns=["Pred 0: sin riesgo", "Pred 1: riesgo tardío"],
    )


def build_feature_importance_chart(feature_importance: pd.DataFrame, top_n: int = 20) -> alt.Chart:
    """
    Construye una gráfica de importancia de variables del modelo.

    Args:
        feature_importance: DataFrame con importancia de características.
        top_n: Número de variables a mostrar.

    Returns:
        Gráfica Altair.
    """
    required_columns = {"feature", "abs_importance"}

    if not required_columns.issubset(feature_importance.columns):
        raise ValueError("La importancia de variables no contiene las columnas esperadas.")

    top_features = feature_importance.sort_values("abs_importance", ascending=False).head(top_n).copy()

    return (
        alt.Chart(top_features)
        .mark_bar()
        .encode(
            x=alt.X("abs_importance:Q", title="Importancia absoluta"),
            y=alt.Y("feature:N", title="Variable transformada", sort="-x"),
            tooltip=[
                "rank",
                "feature",
                alt.Tooltip("coefficient:Q", format=".4f"),
                alt.Tooltip("abs_importance:Q", format=".4f"),
            ],
        )
        .properties(height=520)
    )


def prepare_prediction_input(input_values: dict[str, Any], schema: dict[str, Any]) -> pd.DataFrame:
    """
    Prepara una fila de entrada para el modelo predictivo.

    Args:
        input_values: Valores capturados desde la interfaz.
        schema: Esquema de variables del modelo.

    Returns:
        DataFrame con una sola fila compatible con el modelo.
    """
    categorical_features = schema.get("categorical_features", [])
    numerical_features = schema.get("numerical_features", [])

    row: dict[str, Any] = {}

    for feature in categorical_features:
        row[feature] = str(input_values.get(feature, "UNKNOWN"))

    for feature in numerical_features:
        try:
            row[feature] = float(input_values.get(feature, 0.0))
        except (TypeError, ValueError):
            row[feature] = 0.0

    return pd.DataFrame([row])


def get_selectbox_options(schema: dict[str, Any], feature: str) -> list[str]:
    """
    Obtiene opciones categóricas para el simulador del modelo.

    Args:
        schema: Esquema de variables del modelo.
        feature: Variable categórica.

    Returns:
        Lista de opciones.
    """
    options_by_feature = schema.get("categorical_options", {})
    options = options_by_feature.get(feature, [])

    if not isinstance(options, list) or len(options) == 0:
        return ["UNKNOWN"]

    return [str(option) for option in options]


def render_model_metrics(metrics: dict[str, Any]) -> None:
    """
    Renderiza KPIs y tablas de métricas del modelo.

    Args:
        metrics: Diccionario con métricas del modelo.

    Returns:
        None.
    """
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Accuracy", f"{float(metrics.get('accuracy', 0.0)):.1%}")
    col2.metric("Precision", f"{float(metrics.get('precision', 0.0)):.1%}")
    col3.metric("Recall", f"{float(metrics.get('recall', 0.0)):.1%}")
    col4.metric("F1-score", f"{float(metrics.get('f1_score', 0.0)):.1%}")
    col5.metric("ROC-AUC", f"{float(metrics.get('roc_auc', 0.0)):.1%}")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Métricas del modelo")
        st.dataframe(build_metrics_dataframe(metrics), width="stretch")

    with col_right:
        st.subheader("Matriz de confusión")
        st.dataframe(build_confusion_matrix_dataframe(metrics), width="stretch")


def render_prediction_simulator(model: Any, schema: dict[str, Any]) -> None:
    """
    Renderiza un simulador interactivo de riesgo de entrega tardía.

    Args:
        model: Modelo entrenado con método predict_proba.
        schema: Esquema de variables del modelo.

    Returns:
        None.
    """
    st.subheader("Simulador de riesgo de entrega tardía")
    st.caption(
        "El simulador usa solo variables disponibles antes de conocer el resultado final "
        "de la entrega; por eso excluye estado de entrega, días reales de envío y fecha final."
    )

    categorical_features: list[str] = list(schema.get("categorical_features", []))
    numerical_features: list[str] = list(schema.get("numerical_features", []))
    categorical_defaults: dict[str, str] = dict(schema.get("categorical_defaults", {}))
    numerical_defaults: dict[str, float] = dict(schema.get("numerical_defaults", {}))

    input_values: dict[str, Any] = {}

    with st.form("late_delivery_risk_simulator"):
        st.markdown("**Variables categóricas**")
        categorical_columns = st.columns(3)

        for index, feature in enumerate(categorical_features):
            options = get_selectbox_options(schema, feature)
            default = str(categorical_defaults.get(feature, options[0]))

            if default not in options:
                options.insert(0, default)

            default_index = options.index(default)

            with categorical_columns[index % 3]:
                input_values[feature] = st.selectbox(
                    format_feature_label(feature),
                    options=options,
                    index=default_index,
                    key=f"sim_{feature}",
                )

        st.markdown("**Variables numéricas**")
        numerical_columns = st.columns(max(1, len(numerical_features)))

        for index, feature in enumerate(numerical_features):
            default_value = float(numerical_defaults.get(feature, 0.0))

            with numerical_columns[index % len(numerical_columns)]:
                input_values[feature] = st.number_input(
                    format_feature_label(feature),
                    min_value=0.0,
                    value=default_value,
                    step=1.0,
                    key=f"sim_{feature}",
                )

        submitted = st.form_submit_button("Calcular riesgo")

    if submitted:
        prediction_input = prepare_prediction_input(input_values, schema)

        try:
            probability = float(model.predict_proba(prediction_input)[0, 1])
            predicted_class = int(probability >= 0.5)

            col_prob, col_class = st.columns(2)
            col_prob.metric("Probabilidad de riesgo tardío", f"{probability:.1%}")
            col_class.metric("Clase estimada", "Riesgo tardío" if predicted_class == 1 else "Sin riesgo tardío")

            if predicted_class == 1:
                st.error("El escenario tiene probabilidad alta de entrega tardía.")
            else:
                st.success("El escenario tiene probabilidad baja de entrega tardía.")

            with st.expander("Ver variables enviadas al modelo", expanded=False):
                st.dataframe(prediction_input, width="stretch")

        except Exception as exc:
            LOGGER.exception("Error al calcular predicción: %s", exc)
            st.error(f"No fue posible calcular la predicción: {exc}")


def render_model_tab(
    metrics: dict[str, Any],
    feature_importance: pd.DataFrame,
    predictions_sample: pd.DataFrame,
    model: Any,
    schema: dict[str, Any],
) -> None:
    """
    Renderiza la pestaña del modelo predictivo de riesgo de entrega tardía.

    Args:
        metrics: Métricas de evaluación.
        feature_importance: Importancia de variables.
        predictions_sample: Muestra de predicciones.
        model: Modelo entrenado.
        schema: Esquema de variables del modelo.

    Returns:
        None.
    """
    st.subheader("Modelo predictivo de riesgo de entrega tardía")

    st.markdown(
        """
        Esta fase incorpora un modelo supervisado para estimar la probabilidad de
        **late_delivery_risk**. El modelo se entrena con variables disponibles antes
        de conocer el resultado final de la entrega y excluye variables que provocarían
        fuga de información, como estado final de entrega, días reales de envío,
        fecha de envío y estado final de la orden.
        """
    )

    render_model_metrics(metrics)

    st.subheader("Importancia aproximada de variables")
    st.altair_chart(build_feature_importance_chart(feature_importance), width="stretch")

    with st.expander("Ver tabla de importancia de variables", expanded=False):
        st.dataframe(feature_importance.head(100), width="stretch")

    st.subheader("Muestra de predicciones de prueba")
    st.dataframe(predictions_sample.head(200), width="stretch")

    with st.expander("Detalle técnico del entrenamiento", expanded=False):
        st.json(
            {
                "modelo": metrics.get("model_name"),
                "filas_entrenamiento": metrics.get("train_rows"),
                "filas_prueba": metrics.get("test_rows"),
                "tasa_clase_positiva_total": metrics.get("positive_class_rate_total"),
                "umbral_decisión": metrics.get("decision_threshold"),
                "columnas_excluidas_por_fuga": metrics.get("leakage_columns_excluded"),
                "variables_categóricas": schema.get("categorical_features"),
                "variables_numéricas": schema.get("numerical_features"),
            }
        )

    render_prediction_simulator(model, schema)



def render_project_intro() -> None:
    """
    Renderiza la descripción, el propósito, el origen del dataset y el alcance del prototipo.

    La información se presenta dentro de un contenedor desplegable para no saturar
    la pantalla inicial del dashboard. El bloque distingue los datos reales derivados
    del dataset DataCo y las capas simuladas generadas por OpenLogi.

    Returns:
        None.
    """
    with st.expander("Detalle del dataset y alcance del prototipo", expanded=False):
        st.markdown(
            """
            ### Descripción, propósito y origen del dataset

            **OpenLogi RFID/IoT Demo** es un prototipo web de torre de control
            logística desarrollado con recursos abiertos y gratuitos. La aplicación
            permite explorar una operación de **e-commerce / retail supply chain**
            mediante indicadores de pedidos, entregas, modos de envío, riesgo de
            entrega tardía, trazabilidad RFID simulada, monitoreo IoT simulado e
            inventario WMS sintético.

            El propósito de la aplicación es demostrar cómo una organización puede
            pasar de datos logísticos dispersos a una vista integrada de control
            operativo, trazabilidad y analítica básica para apoyar la toma de
            decisiones.

            **Origen del dataset:** el prototipo utiliza como referencia el dataset
            público **DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS**, publicado
            en Kaggle y asociado a datos de cadena de suministro, pedidos, productos,
            ventas, distribución comercial y registros de navegación/clickstream.

            | Elemento | Detalle |
            |---|---|
            | Tipo de solución | Demo web de torre de control logística |
            | Caso de uso | E-commerce / retail supply chain |
            | Dataset base | DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS |
            | Datos reales usados | Pedidos, productos, ventas, envíos, regiones, modos de envío y riesgo de entrega tardía |
            | Capas simuladas | RFID, IoT e inventario WMS |
            | Alcance | Prototipo académico y técnico, no sistema productivo |
            | Recursos | Python, pandas, Altair, Streamlit y archivos CSV procesados |

            **Datos reales usados en la demo:**

            - Pedidos y líneas de pedido.
            - Productos, categorías y departamentos.
            - Ventas y utilidad.
            - Fechas de orden y envío.
            - Modos de envío.
            - Estados de entrega.
            - Riesgo de entrega tardía.
            - Mercado, región, país y ciudad destino.

            **Capas simuladas generadas por OpenLogi:**

            - Eventos RFID por pedido, producto, lector, antena, ubicación y RSSI.
            - Eventos IoT de temperatura, humedad, vibración y estado operativo.
            - Inventario WMS sintético con stock, demanda promedio, punto de reorden
              y cantidad sugerida de reabastecimiento.

            **Alcance del prototipo:** esta aplicación es una demo académica y
            técnica. No sustituye un WMS, TMS, sistema RFID industrial ni plataforma
            IoT productiva. Su valor está en demostrar la arquitectura funcional de
            una torre de control logística usando datos abiertos, simulaciones
            reproducibles y visualización web.
            """
        )

        st.info(
            "Datos reales: pedidos, productos, envíos, ventas y riesgo de entrega tardía. "
            "Capas simuladas: RFID, IoT e inventario WMS."
        )


def render_quality_tab(quality: dict[str, Any], dictionary: pd.DataFrame) -> None:
    """
    Renderiza documentación técnica de datos.

    Args:
        quality: Reporte JSON de calidad.
        dictionary: Diccionario de datos.

    Returns:
        None.
    """
    st.subheader("Dataset y documentación técnica")
    st.json(quality)
    st.subheader("Diccionario de datos")
    st.dataframe(dictionary, width="stretch")

    st.info(
        "Datos reales usados: pedidos, productos, envíos y riesgo de entrega tardía. "
        "Capas simuladas: RFID, IoT e inventario WMS."
    )


def main() -> None:
    """
    Ejecuta la aplicación OpenLogi RFID/IoT Demo.

    Returns:
        None.
    """
    configure_logging()
    st.set_page_config(page_title="OpenLogi RFID/IoT Demo", layout="wide")
    st.title("OpenLogi RFID/IoT Demo")
    st.caption("Torre de control logística abierta con DataCo, RFID simulado, IoT simulado e inventario WMS sintético.")
    render_project_intro()

    try:
        data = load_all_data()
        orders = data["orders"]
        rfid = data["rfid"]
        iot = data["iot"]
        inventory = data["inventory"]
        dictionary = data["dictionary"]
        quality = data["quality"]
        model_artifacts = load_model_artifacts()

        model = model_artifacts["model"]
        metrics = model_artifacts["metrics"]
        feature_importance = model_artifacts["importance"]
        schema = model_artifacts["schema"]
        predictions_sample = model_artifacts["predictions_sample"]

        if not isinstance(orders, pd.DataFrame) or not isinstance(rfid, pd.DataFrame):
            raise ValueError("Carga de datos inválida.")
        if not isinstance(iot, pd.DataFrame) or not isinstance(inventory, pd.DataFrame):
            raise ValueError("Carga de datos inválida.")
        if not isinstance(dictionary, pd.DataFrame) or not isinstance(quality, dict):
            raise ValueError("Carga de metadatos inválida.")
        if not isinstance(metrics, dict) or not isinstance(schema, dict):
            raise ValueError("Carga de artefactos del modelo inválida.")
        if not isinstance(feature_importance, pd.DataFrame) or not isinstance(predictions_sample, pd.DataFrame):
            raise ValueError("Carga de tablas del modelo inválida.")

        filtered_orders = apply_sidebar_filters(orders)

        tabs = st.tabs(
            [
                "Resumen",
                "Pedidos y entregas",
                "RFID simulado",
                "IoT simulado",
                "Inventario",
                "Modelo predictivo",
                "Dataset y documentación",
            ]
        )

        with tabs[0]:
            render_summary_tab(filtered_orders, rfid, iot, inventory)

        with tabs[1]:
            render_orders_tab(filtered_orders)

        with tabs[2]:
            render_rfid_tab(rfid, filtered_orders)

        with tabs[3]:
            render_iot_tab(iot, filtered_orders)

        with tabs[4]:
            render_inventory_tab(inventory)

        with tabs[5]:
            render_model_tab(metrics, feature_importance, predictions_sample, model, schema)

        with tabs[6]:
            render_quality_tab(quality, dictionary)

    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Error controlado en app: %s", exc)
        st.error(f"Error de validación: {exc}")
    except Exception as exc:
        LOGGER.exception("Error inesperado en app.")
        st.error(f"Error inesperado: {exc}")


if __name__ == "__main__":
    main()
