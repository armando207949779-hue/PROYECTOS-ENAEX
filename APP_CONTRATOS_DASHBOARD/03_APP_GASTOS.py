# ============================================================
# 03_APP_GASTOS.py
# Dashboard de Monitoreo de Contratos ENAEX
# Pestaña: Gastos
# ============================================================

from pathlib import Path
import base64

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="03_GASTOS | Dashboard Contratos ENAEX",
    page_icon="📊",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilos
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2.8rem;
            padding-bottom: 2.5rem;
        }

        .enaex-logo-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 26px;
            margin-bottom: 18px;
            padding-top: 8px;
        }

        .enaex-logo-wrapper img {
            width: 240px;
            max-width: 70%;
            height: auto;
        }

        .main-title {
            text-align: center;
            font-size: 2.15rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 1.02rem;
            margin-bottom: 1.6rem;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 800;
            margin-top: 1.4rem;
            margin-bottom: 0.55rem;
        }

        .section-caption {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 0.75rem;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 18px 18px 16px 18px;
            min-height: 116px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }

        .kpi-label {
            font-size: 0.82rem;
            color: #6b7280;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            margin-bottom: 0.35rem;
            line-height: 1.2;
        }

        .kpi-value {
            font-size: 1.55rem;
            font-weight: 850;
            color: #111827;
            line-height: 1.12;
            word-break: break-word;
        }

        .kpi-help {
            color: #6b7280;
            font-size: 0.78rem;
            margin-top: 0.42rem;
            line-height: 1.25;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Utilidades visuales
# ============================================================

def render_logo() -> None:
    """Renderiza el logo SVG si existe."""
    if not LOGO_PATH.exists():
        return

    svg_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div class="enaex-logo-wrapper">
            <img src="data:image/svg+xml;base64,{svg_b64}" alt="ENAEX Logo">
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, help_text: str = "") -> None:
    """Tarjeta KPI personalizada para evitar cortes visuales de st.metric."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, caption: str | None = None) -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div class='section-caption'>{caption}</div>", unsafe_allow_html=True)


# ============================================================
# Utilidades de datos
# ============================================================

def convertir_numero(valor):
    """Convierte números con formatos 1.234,56 / 1234,56 / 1234.56."""
    if pd.isna(valor):
        return np.nan

    s = str(valor).strip()

    if s == "" or s.lower() in ["nan", "none", "null"]:
        return np.nan

    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    return pd.to_numeric(s, errors="coerce")


def limpiar_texto_serie(serie: pd.Series, quitar_decimal: bool = True) -> pd.Series:
    serie_limpia = serie.astype(str).str.strip()
    if quitar_decimal:
        serie_limpia = serie_limpia.str.replace(".0", "", regex=False)
    return serie_limpia.replace(["", "nan", "NaN", "None", "none", "NULL", "null"], pd.NA)


def formato_usd_compacto(x, pos=None) -> str:
    if pd.isna(x):
        return "$0"
    if abs(x) >= 1_000_000_000:
        return f"${x/1_000_000_000:.1f}B"
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:,.0f}"


def formato_usd_largo(x) -> str:
    if pd.isna(x):
        x = 0
    return f"US$ {x:,.2f}"


def formato_entero(x) -> str:
    if pd.isna(x):
        x = 0
    return f"{int(round(x)):,.0f}"


def formato_porcentaje(x) -> str:
    if pd.isna(x):
        x = 0
    return f"{x:.2%}"


def validar_columnas(df: pd.DataFrame, columnas: list[str], nombre_df: str) -> list[str]:
    return [col for col in columnas if col not in df.columns]


# ============================================================
# Carga desde session_state
# ============================================================

render_logo()

st.markdown(
    "<div class='main-title'>Gastos y vigencia de contratos</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>Análisis de órdenes de compra, gasto convertido a USD y estado de contratos por gestor.</div>",
    unsafe_allow_html=True,
)

if "dataframes_cargados" not in st.session_state:
    st.warning("Primero debes cargar los archivos en la pestaña 01_CARGA_ARCHIVOS.")
    st.stop()

dataframes = st.session_state["dataframes_cargados"]

DATAFRAMES_REQUERIDOS = [
    "df_moneda_cambio",
    "df_ordenes",
    "df_bbdd_x_categoria",
    "df_me5a",
]

faltantes_df = [nombre for nombre in DATAFRAMES_REQUERIDOS if nombre not in dataframes]

if faltantes_df:
    st.error(
        "Faltan DataFrames requeridos para esta pestaña: "
        + ", ".join(faltantes_df)
        + ". Vuelve a cargar los archivos en 01_CARGA_ARCHIVOS."
    )
    st.stop()

# Copias locales
_df_moneda_cambio = dataframes["df_moneda_cambio"].copy()
_df_ordenes = dataframes["df_ordenes"].copy()
_df_bbdd_x_categoria = dataframes["df_bbdd_x_categoria"].copy()
_df_me5a = dataframes["df_me5a"].copy()

columnas_requeridas = {
    "df_ordenes": ["Documento_compras", "Fecha_documento", "Moneda", "Precio_neto"],
    "df_moneda_cambio": ["Moneda", "Factor_USD_por_Unidad", "Valor_CLP_por_Unidad", "Fecha_Conversion"],
    "df_bbdd_x_categoria": ["Contrato", "Gestor_Contrato"],
    "df_me5a": ["Documento_compras", "Fin_período_validez"],
}

validaciones = {
    "df_ordenes": validar_columnas(_df_ordenes, columnas_requeridas["df_ordenes"], "df_ordenes"),
    "df_moneda_cambio": validar_columnas(_df_moneda_cambio, columnas_requeridas["df_moneda_cambio"], "df_moneda_cambio"),
    "df_bbdd_x_categoria": validar_columnas(_df_bbdd_x_categoria, columnas_requeridas["df_bbdd_x_categoria"], "df_bbdd_x_categoria"),
    "df_me5a": validar_columnas(_df_me5a, columnas_requeridas["df_me5a"], "df_me5a"),
}

errores_columnas = [
    f"{nombre}: {', '.join(cols)}"
    for nombre, cols in validaciones.items()
    if cols
]

if errores_columnas:
    st.error("Hay columnas faltantes en los archivos cargados:")
    for error in errores_columnas:
        st.write(f"- {error}")
    st.stop()


# ============================================================
# Preparación: órdenes a USD
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_ordenes_usd(df_ordenes: pd.DataFrame, df_moneda_cambio: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df_ordenes_usd = df_ordenes.copy()
    df_cambio = df_moneda_cambio.copy()

    df_ordenes_usd["Moneda"] = df_ordenes_usd["Moneda"].astype(str).str.strip().str.upper()
    df_cambio["Moneda"] = df_cambio["Moneda"].astype(str).str.strip().str.upper()

    df_ordenes_usd["Precio_neto_num"] = df_ordenes_usd["Precio_neto"].apply(convertir_numero)
    df_cambio["Factor_USD_por_Unidad"] = df_cambio["Factor_USD_por_Unidad"].apply(convertir_numero)

    monedas_registros = set(df_ordenes_usd["Moneda"].dropna().unique())
    monedas_tabla = set(df_cambio["Moneda"].dropna().unique())
    monedas_faltantes = sorted(monedas_registros - monedas_tabla)

    columnas_cambio = [
        "Moneda",
        "Factor_USD_por_Unidad",
        "Valor_CLP_por_Unidad",
        "Fecha_Conversion",
    ]

    df_ordenes_usd = df_ordenes_usd.merge(
        df_cambio[columnas_cambio].drop_duplicates(subset=["Moneda"]),
        on="Moneda",
        how="left",
    )

    df_ordenes_usd["Precio_neto_USD"] = (
        df_ordenes_usd["Precio_neto_num"] * df_ordenes_usd["Factor_USD_por_Unidad"]
    )

    df_ordenes_usd["Documento_Compras_Texto"] = limpiar_texto_serie(
        df_ordenes_usd["Documento_compras"], quitar_decimal=True
    )

    df_ordenes_usd["Tipo_Orden_Compra"] = pd.to_numeric(
        df_ordenes_usd["Documento_Compras_Texto"].str[:2],
        errors="coerce",
    )

    df_ordenes_usd["Monto_OC_USD"] = pd.to_numeric(
        df_ordenes_usd["Precio_neto_USD"],
        errors="coerce",
    ).fillna(0)

    df_ordenes_usd["Fecha_documento"] = pd.to_datetime(
        df_ordenes_usd["Fecha_documento"],
        errors="coerce",
    )

    df_ordenes_usd = df_ordenes_usd.dropna(subset=["Fecha_documento"]).copy()

    if not df_ordenes_usd.empty:
        df_ordenes_usd["Año"] = df_ordenes_usd["Fecha_documento"].dt.year
        df_ordenes_usd["Mes"] = df_ordenes_usd["Fecha_documento"].dt.month
        df_ordenes_usd["AñoMes"] = df_ordenes_usd["Fecha_documento"].dt.strftime("%Y-%m")
        df_ordenes_usd["InicioMes"] = df_ordenes_usd["Fecha_documento"].dt.to_period("M").dt.to_timestamp()
    else:
        df_ordenes_usd["Año"] = pd.Series(dtype="int64")
        df_ordenes_usd["Mes"] = pd.Series(dtype="int64")
        df_ordenes_usd["AñoMes"] = pd.Series(dtype="object")
        df_ordenes_usd["InicioMes"] = pd.Series(dtype="datetime64[ns]")

    monto_total_oc_usd = df_ordenes_usd["Monto_OC_USD"].sum()
    df_ordenes_usd["Participacion_OC"] = (
        df_ordenes_usd["Monto_OC_USD"] / monto_total_oc_usd
        if monto_total_oc_usd != 0
        else 0
    )

    return df_ordenes_usd, monedas_faltantes


@st.cache_data(show_spinner=False)
def preparar_contratos_estado(df_bbdd_x_categoria: pd.DataFrame, df_me5a: pd.DataFrame) -> pd.DataFrame:
    df_cat = df_bbdd_x_categoria.copy()
    df_m5 = df_me5a.copy()

    df_cat["Contrato"] = limpiar_texto_serie(df_cat["Contrato"], quitar_decimal=True)
    df_m5["Documento_compras"] = limpiar_texto_serie(df_m5["Documento_compras"], quitar_decimal=True)

    df_cat = df_cat.dropna(subset=["Contrato"]).copy()
    df_m5 = df_m5.dropna(subset=["Documento_compras"]).copy()

    df_cat["Gestor_Contrato"] = (
        df_cat["Gestor_Contrato"]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "NaN", "None", "none", "NULL", "null"], "Sin gestor")
    )

    df_m5["Fin_período_validez"] = pd.to_datetime(
        df_m5["Fin_período_validez"],
        errors="coerce",
    )

    hoy = pd.Timestamp.today().normalize()

    def clasificar_estado(fecha_fin):
        if pd.isna(fecha_fin):
            return "Sin fecha"
        if fecha_fin < hoy:
            return "Vencido"

        meses_diferencia = (fecha_fin.year - hoy.year) * 12 + (fecha_fin.month - hoy.month)
        if meses_diferencia <= 3:
            return "Por Vencer"
        return "Vigente"

    df_m5_contrato = (
        df_m5
        .groupby("Documento_compras", as_index=False)
        .agg({"Fin_período_validez": "max"})
    )

    df_m5_contrato["Estado"] = df_m5_contrato["Fin_período_validez"].apply(clasificar_estado)

    df_contratos_estado = df_cat.merge(
        df_m5_contrato,
        left_on="Contrato",
        right_on="Documento_compras",
        how="left",
    )

    df_contratos_estado["Estado"] = df_contratos_estado["Estado"].fillna("Sin información ME5A")
    df_contratos_estado["Fecha_Analisis"] = hoy

    return df_contratos_estado


df_ordenes_usd, monedas_faltantes = preparar_ordenes_usd(_df_ordenes, _df_moneda_cambio)
df_contratos_estado = preparar_contratos_estado(_df_bbdd_x_categoria, _df_me5a)

if monedas_faltantes:
    st.warning(
        "Faltan monedas en df_moneda_cambio: " + ", ".join(monedas_faltantes)
    )

if df_ordenes_usd.empty:
    st.warning("No hay órdenes con Fecha_documento válida para analizar.")
    st.stop()


# ============================================================
# Filtros de encabezado
# ============================================================

section_title("Filtros", "Selecciona el periodo, tipo de OC, moneda y gestor para actualizar el análisis.")

with st.container(border=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1.2])

    min_fecha = df_ordenes_usd["Fecha_documento"].min().date()
    max_fecha = df_ordenes_usd["Fecha_documento"].max().date()

    with col_f1:
        rango_fechas = st.date_input(
            "Periodo de documentos",
            value=(min_fecha, max_fecha),
            min_value=min_fecha,
            max_value=max_fecha,
        )

    with col_f2:
        tipos_oc_disponibles = sorted(
            [int(x) for x in df_ordenes_usd["Tipo_Orden_Compra"].dropna().unique()]
        )
        tipos_oc_sel = st.multiselect(
            "Tipo de OC",
            options=tipos_oc_disponibles,
            default=tipos_oc_disponibles,
        )

    with col_f3:
        monedas_disponibles = sorted(df_ordenes_usd["Moneda"].dropna().unique().tolist())
        monedas_sel = st.multiselect(
            "Moneda",
            options=monedas_disponibles,
            default=monedas_disponibles,
        )

    with col_f4:
        gestores_disponibles = sorted(df_contratos_estado["Gestor_Contrato"].dropna().unique().tolist())
        gestores_sel = st.multiselect(
            "Gestor contrato",
            options=gestores_disponibles,
            default=gestores_disponibles,
        )

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas
else:
    fecha_inicio, fecha_fin = min_fecha, max_fecha

fecha_inicio_ts = pd.Timestamp(fecha_inicio)
fecha_fin_ts = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

mask_ordenes = (
    (df_ordenes_usd["Fecha_documento"] >= fecha_inicio_ts)
    & (df_ordenes_usd["Fecha_documento"] <= fecha_fin_ts)
)

if tipos_oc_sel:
    mask_ordenes &= df_ordenes_usd["Tipo_Orden_Compra"].isin(tipos_oc_sel)

if monedas_sel:
    mask_ordenes &= df_ordenes_usd["Moneda"].isin(monedas_sel)

if gestores_sel:
    df_contratos_estado_filtrado = df_contratos_estado[
        df_contratos_estado["Gestor_Contrato"].isin(gestores_sel)
    ].copy()
else:
    df_contratos_estado_filtrado = df_contratos_estado.iloc[0:0].copy()

df_ordenes_filtrado = df_ordenes_usd[mask_ordenes].copy()

if df_ordenes_filtrado.empty:
    st.info("No hay órdenes para los filtros seleccionados.")


# ============================================================
# KPIs
# ============================================================

section_title("Indicadores principales", "Resumen ejecutivo del gasto y de la vigencia contractual.")

recuento_contratos = df_contratos_estado_filtrado["Contrato"].nunique()
contratos_cruzados_me5a = df_contratos_estado_filtrado[
    df_contratos_estado_filtrado["Documento_compras"].notna()
]["Contrato"].nunique()
contratos_sin_me5a = df_contratos_estado_filtrado[
    df_contratos_estado_filtrado["Estado"] == "Sin información ME5A"
]["Contrato"].nunique()
contratos_por_vencer = df_contratos_estado_filtrado[
    df_contratos_estado_filtrado["Estado"] == "Por Vencer"
]["Contrato"].nunique()

monto_total_oc_usd = df_ordenes_filtrado["Monto_OC_USD"].sum()
monto_oc_tipo_44_usd = df_ordenes_filtrado.loc[
    df_ordenes_filtrado["Tipo_Orden_Compra"] == 44,
    "Monto_OC_USD",
].sum()
participacion_oc_tipo_44 = (
    monto_oc_tipo_44_usd / monto_total_oc_usd
    if monto_total_oc_usd != 0
    else 0
)

ordenes_unicas = df_ordenes_filtrado["Documento_Compras_Texto"].nunique()
monedas_unicas = df_ordenes_filtrado["Moneda"].nunique()

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    kpi_card("Gasto total OC", formato_usd_largo(monto_total_oc_usd), "Monto convertido a USD")
with col_kpi2:
    kpi_card("OC tipo 44", formato_usd_largo(monto_oc_tipo_44_usd), f"Participación: {formato_porcentaje(participacion_oc_tipo_44)}")
with col_kpi3:
    kpi_card("N° órdenes", formato_entero(ordenes_unicas), f"Monedas analizadas: {monedas_unicas}")
with col_kpi4:
    kpi_card("N° contratos", formato_entero(recuento_contratos), f"Por vencer: {formato_entero(contratos_por_vencer)}")

col_kpi5, col_kpi6, col_kpi7, col_kpi8 = st.columns(4)
with col_kpi5:
    kpi_card("Contratos con ME5A", formato_entero(contratos_cruzados_me5a), "Cruce por documento de compras")
with col_kpi6:
    kpi_card("Sin información ME5A", formato_entero(contratos_sin_me5a), "Contratos no encontrados en ME5A")
with col_kpi7:
    kpi_card("Periodo desde", str(fecha_inicio), "Fecha documento mínima filtrada")
with col_kpi8:
    kpi_card("Periodo hasta", str(fecha_fin), "Fecha documento máxima filtrada")


# ============================================================
# Gasto anual
# ============================================================

section_title("Gasto total por año", "Suma anual del gasto de órdenes de compra convertido a USD.")

df_gasto_anual = (
    df_ordenes_filtrado
    .groupby("Año", as_index=False)["Monto_OC_USD"]
    .sum()
    .rename(columns={"Monto_OC_USD": "Gasto_Total_USD"})
    .sort_values("Año")
)

if df_gasto_anual.empty:
    st.info("No hay datos para graficar gasto anual.")
else:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df_gasto_anual["Año"].astype(str), df_gasto_anual["Gasto_Total_USD"])
    ax.set_title("Total gasto por año", fontsize=14, fontweight="bold")
    ax.set_xlabel("Año")
    ax.set_ylabel("Gasto total [USD]")
    ax.grid(axis="y", alpha=0.25)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(formato_usd_compacto))

    for i, valor in enumerate(df_gasto_anual["Gasto_Total_USD"]):
        ax.text(
            i,
            valor,
            formato_usd_compacto(valor),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla de gasto anual"):
        st.dataframe(df_gasto_anual, use_container_width=True, hide_index=True)


# ============================================================
# Gasto mensual
# ============================================================

section_title("Gasto mensual", "Desglose mensual y evolución del gasto en órdenes de compra.")

df_gasto_mensual = (
    df_ordenes_filtrado
    .groupby(["InicioMes", "AñoMes"], as_index=False)["Monto_OC_USD"]
    .sum()
    .rename(columns={"Monto_OC_USD": "Gasto_Mensual_USD"})
    .sort_values("InicioMes")
    .reset_index(drop=True)
)

if df_gasto_mensual.empty:
    st.info("No hay datos para graficar gasto mensual.")
else:
    df_gasto_mensual_plot = df_gasto_mensual.copy()
    top_indices = df_gasto_mensual_plot["Gasto_Mensual_USD"].nlargest(5).index

    fig, ax = plt.subplots(figsize=(15, 6))
    ax.bar(df_gasto_mensual_plot["AñoMes"], df_gasto_mensual_plot["Gasto_Mensual_USD"])
    ax.set_title("Gasto mensual en órdenes de compra", fontsize=15, fontweight="bold")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Gasto mensual [USD]")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(formato_usd_compacto))

    for i in top_indices:
        valor = df_gasto_mensual_plot.loc[i, "Gasto_Mensual_USD"]
        ax.text(
            i,
            valor,
            formato_usd_compacto(valor),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    fig, ax = plt.subplots(figsize=(15, 6))
    ax.plot(
        df_gasto_mensual_plot["AñoMes"],
        df_gasto_mensual_plot["Gasto_Mensual_USD"],
        marker="o",
        linewidth=2.5,
    )
    ax.set_title("Evolución mensual del gasto en órdenes de compra", fontsize=15, fontweight="bold")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Gasto mensual [USD]")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(formato_usd_compacto))

    idx_max = df_gasto_mensual_plot["Gasto_Mensual_USD"].idxmax()
    idx_last = df_gasto_mensual_plot.index[-1]

    for i in sorted(set([idx_max, idx_last])):
        valor = df_gasto_mensual_plot.loc[i, "Gasto_Mensual_USD"]
        mes = df_gasto_mensual_plot.loc[i, "AñoMes"]
        ax.text(
            i,
            valor,
            f"{mes}\n{formato_usd_compacto(valor)}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla de gasto mensual"):
        st.dataframe(df_gasto_mensual, use_container_width=True, hide_index=True)


# ============================================================
# Participación por tipo de OC
# ============================================================

section_title("Participación por tipo de orden de compra", "Distribución del gasto total según los dos primeros dígitos del documento de compras.")

df_tipo_oc = (
    df_ordenes_filtrado
    .groupby("Tipo_Orden_Compra", as_index=False)
    .agg(
        Monto_OC_USD=("Monto_OC_USD", "sum"),
        Ordenes=("Documento_Compras_Texto", "nunique"),
    )
    .sort_values("Monto_OC_USD", ascending=False)
)

df_tipo_oc["Participacion"] = (
    df_tipo_oc["Monto_OC_USD"] / df_tipo_oc["Monto_OC_USD"].sum()
    if df_tipo_oc["Monto_OC_USD"].sum() != 0
    else 0
)

if df_tipo_oc.empty:
    st.info("No hay datos para analizar tipos de orden de compra.")
else:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(df_tipo_oc["Tipo_Orden_Compra"].astype(str), df_tipo_oc["Monto_OC_USD"])
    ax.set_title("Gasto por tipo de OC", fontsize=14, fontweight="bold")
    ax.set_xlabel("Tipo de OC")
    ax.set_ylabel("Gasto [USD]")
    ax.grid(axis="y", alpha=0.25)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(formato_usd_compacto))

    for i, valor in enumerate(df_tipo_oc["Monto_OC_USD"]):
        ax.text(i, valor, formato_usd_compacto(valor), ha="center", va="bottom", fontsize=9, fontweight="bold")

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla por tipo de OC"):
        st.dataframe(df_tipo_oc, use_container_width=True, hide_index=True)


# ============================================================
# Contratos por gestor y estado
# ============================================================

section_title("Contratos por gestor y estado de vigencia", "Clasificación de contratos usando la fecha de fin de validez en ME5A.")

orden_estados = [
    "Vencido",
    "Por Vencer",
    "Vigente",
    "Sin fecha",
    "Sin información ME5A",
]

df_recuento_estado = (
    df_contratos_estado_filtrado
    .groupby(["Gestor_Contrato", "Estado"], as_index=False)["Contrato"]
    .nunique()
    .rename(columns={"Contrato": "Recuento_Contratos"})
)

if df_recuento_estado.empty:
    st.info("No hay contratos para los gestores seleccionados.")
else:
    df_pivot_estado = df_recuento_estado.pivot_table(
        index="Gestor_Contrato",
        columns="Estado",
        values="Recuento_Contratos",
        aggfunc="sum",
        fill_value=0,
    )

    columnas_presentes = [col for col in orden_estados if col in df_pivot_estado.columns]
    df_pivot_estado = df_pivot_estado[columnas_presentes]
    df_pivot_estado["Total_Contratos"] = df_pivot_estado.sum(axis=1)
    df_pivot_estado = df_pivot_estado.sort_values("Total_Contratos", ascending=True)
    df_plot_estado = df_pivot_estado.drop(columns="Total_Contratos")

    fig, ax = plt.subplots(figsize=(12, max(6, 0.38 * len(df_plot_estado) + 2)))
    df_plot_estado.plot(kind="barh", stacked=True, ax=ax)

    ax.set_title("Recuento de contratos por gestor y estado de vigencia", fontsize=14, fontweight="bold")
    ax.set_xlabel("Recuento de contratos")
    ax.set_ylabel("Gestor de contrato")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(title="Estado", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    for i, total in enumerate(df_pivot_estado["Total_Contratos"]):
        ax.text(total + 0.3, i, str(int(total)), va="center", fontsize=9, fontweight="bold")

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla de contratos por gestor y estado"):
        st.dataframe(df_pivot_estado.reset_index(), use_container_width=True, hide_index=True)


# ============================================================
# Distribución global por estado
# ============================================================

section_title("Distribución global de contratos por estado", "Resumen global de vigencia contractual para los gestores seleccionados.")

df_estado_global = (
    df_contratos_estado_filtrado
    .groupby("Estado", as_index=False)["Contrato"]
    .nunique()
    .rename(columns={"Contrato": "Recuento_Contratos"})
    .sort_values("Recuento_Contratos", ascending=False)
)

df_estado_global["Participacion_%"] = (
    df_estado_global["Recuento_Contratos"] / df_estado_global["Recuento_Contratos"].sum() * 100
    if df_estado_global["Recuento_Contratos"].sum() != 0
    else 0
)

if df_estado_global.empty:
    st.info("No hay datos para graficar distribución global por estado.")
else:
    col_donut, col_tabla = st.columns([0.9, 1.1])

    with col_donut:
        total_contratos = df_estado_global["Recuento_Contratos"].sum()
        fig, ax = plt.subplots(figsize=(4.8, 4.4))
        ax.pie(
            df_estado_global["Recuento_Contratos"],
            labels=None,
            autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
            startangle=90,
            pctdistance=0.78,
            wedgeprops={"width": 0.38, "edgecolor": "white"},
            textprops={"fontsize": 8},
        )
        ax.text(0, 0.05, f"{total_contratos:,.0f}", ha="center", va="center", fontsize=20, fontweight="bold")
        ax.text(0, -0.13, "contratos", ha="center", va="center", fontsize=10)
        ax.set_title("Distribución global", fontsize=13, fontweight="bold")
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

    with col_tabla:
        st.dataframe(df_estado_global, use_container_width=True, hide_index=True)


# ============================================================
# Contratos por vencer por gestor
# ============================================================

section_title("Contratos por vencer por gestor", "Contratos cuya fecha de fin de validez ocurre dentro de los próximos tres meses.")

df_por_vencer = df_contratos_estado_filtrado[
    df_contratos_estado_filtrado["Estado"] == "Por Vencer"
].copy()

df_top_por_vencer = (
    df_por_vencer
    .groupby("Gestor_Contrato", as_index=False)["Contrato"]
    .nunique()
    .rename(columns={"Contrato": "Contratos_Por_Vencer"})
    .sort_values("Contratos_Por_Vencer", ascending=True)
)

if df_top_por_vencer.empty:
    st.info("No hay contratos por vencer para los filtros seleccionados.")
else:
    fig, ax = plt.subplots(figsize=(10, max(5, 0.35 * len(df_top_por_vencer) + 2)))
    ax.barh(df_top_por_vencer["Gestor_Contrato"], df_top_por_vencer["Contratos_Por_Vencer"])
    ax.set_title("Contratos por vencer por gestor", fontsize=14, fontweight="bold")
    ax.set_xlabel("Recuento de contratos por vencer")
    ax.set_ylabel("Gestor de contrato")
    ax.grid(axis="x", alpha=0.25)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    for i, valor in enumerate(df_top_por_vencer["Contratos_Por_Vencer"]):
        ax.text(valor + 0.1, i, str(int(valor)), va="center", fontsize=9, fontweight="bold")

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla de contratos por vencer"):
        st.dataframe(df_top_por_vencer, use_container_width=True, hide_index=True)


# ============================================================
# Mapa de calor
# ============================================================

section_title("Mapa de calor de contratos por gestor y estado", "Vista cruzada para identificar concentración de contratos por estado.")

if df_recuento_estado.empty:
    st.info("No hay datos para construir el mapa de calor.")
else:
    df_heatmap_pivot = df_recuento_estado.pivot_table(
        index="Gestor_Contrato",
        columns="Estado",
        values="Recuento_Contratos",
        aggfunc="sum",
        fill_value=0,
    )

    columnas_presentes = [col for col in orden_estados if col in df_heatmap_pivot.columns]
    df_heatmap_pivot = df_heatmap_pivot[columnas_presentes]
    df_heatmap_pivot["Total"] = df_heatmap_pivot.sum(axis=1)
    df_heatmap_pivot = df_heatmap_pivot.sort_values("Total", ascending=False)
    df_heatmap_plot = df_heatmap_pivot.drop(columns="Total")

    if df_heatmap_plot.empty:
        st.info("No hay datos para construir el mapa de calor.")
    else:
        fig, ax = plt.subplots(figsize=(10, max(6, 0.38 * len(df_heatmap_plot) + 2)))
        matriz = df_heatmap_plot.values
        im = ax.imshow(matriz, aspect="auto")

        ax.set_xticks(np.arange(len(df_heatmap_plot.columns)))
        ax.set_xticklabels(df_heatmap_plot.columns, rotation=45, ha="right")
        ax.set_yticks(np.arange(len(df_heatmap_plot.index)))
        ax.set_yticklabels(df_heatmap_plot.index)

        ax.set_title("Mapa de calor de contratos por gestor y estado", fontsize=14, fontweight="bold")
        ax.set_xlabel("Estado")
        ax.set_ylabel("Gestor de contrato")

        for i in range(matriz.shape[0]):
            for j in range(matriz.shape[1]):
                valor = matriz[i, j]
                if valor > 0:
                    ax.text(j, i, int(valor), ha="center", va="center", fontsize=9, fontweight="bold")

        fig.colorbar(im, ax=ax, label="Recuento de contratos")
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

        with st.expander("Ver tabla del mapa de calor"):
            st.dataframe(df_heatmap_plot, use_container_width=True)


# ============================================================
# Tablas de apoyo y validaciones
# ============================================================

section_title("Tablas de apoyo", "Vistas acotadas para revisar datos base, cruces y validaciones.")

with st.expander("Monedas únicas en órdenes"):
    df_monedas_unicas = (
        pd.DataFrame({"Moneda": sorted(df_ordenes_usd["Moneda"].dropna().unique())})
        .reset_index(drop=True)
    )
    st.dataframe(df_monedas_unicas, use_container_width=True, hide_index=True)

with st.expander("Órdenes convertidas a USD"):
    columnas_preview = [
        col for col in [
            "Documento_compras",
            "Fecha_documento",
            "Moneda",
            "Precio_neto",
            "Precio_neto_num",
            "Factor_USD_por_Unidad",
            "Precio_neto_USD",
            "Tipo_Orden_Compra",
            "Participacion_OC",
        ] if col in df_ordenes_usd.columns
    ]
    st.dataframe(df_ordenes_usd[columnas_preview].head(500), use_container_width=True, hide_index=True)

with st.expander("Contratos con estado de vigencia"):
    columnas_preview = [
        col for col in [
            "Contrato",
            "Gestor_Contrato",
            "Documento_compras",
            "Fin_período_validez",
            "Estado",
        ] if col in df_contratos_estado.columns
    ]
    st.dataframe(df_contratos_estado[columnas_preview].head(500), use_container_width=True, hide_index=True)

with st.expander("Resumen de validación"):
    st.write("**Validación de contratos**")
    st.write(f"- Total contratos únicos en df_bbdd_x_categoria: {df_contratos_estado['Contrato'].nunique():,.0f}")
    st.write(f"- Contratos únicos cruzados con ME5A: {contratos_cruzados_me5a:,.0f}")
    st.write(f"- Contratos sin información en ME5A: {contratos_sin_me5a:,.0f}")
    st.write(f"- Fecha usada como TODAY(): {pd.Timestamp.today().normalize().date()}")

    st.write("**Validación de monedas**")
    if monedas_faltantes:
        st.write("- Monedas faltantes en df_moneda_cambio: " + ", ".join(monedas_faltantes))
    else:
        st.write("- Todas las monedas de df_ordenes existen en df_moneda_cambio.")
