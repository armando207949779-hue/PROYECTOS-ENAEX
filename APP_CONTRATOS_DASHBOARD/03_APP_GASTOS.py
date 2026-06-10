# ============================================================
# 03_APP_GASTOS.py
# Dashboard de Monitoreo de Contratos ENAEX
# Pestaña: Gastos
# ============================================================

from pathlib import Path
import base64
import re

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

VERSION_NORMALIZACION_IDS = "v_2026_06_10_separacion_gastos_salud_contratos"


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
    """Tarjeta KPI personalizada para evitar cortes visuales."""
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
    st.markdown(
        f"<div class='section-title'>{title}</div>",
        unsafe_allow_html=True,
    )

    if caption:
        st.markdown(
            f"<div class='section-caption'>{caption}</div>",
            unsafe_allow_html=True,
        )


def limpiar_estilo_grafico(ax) -> None:
    """Aplica formato visual limpio al gráfico."""
    ax.grid(False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d1d5db")
    ax.spines["bottom"].set_color("#d1d5db")

    ax.tick_params(axis="x", colors="#374151")
    ax.tick_params(axis="y", colors="#374151")


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


def limpiar_id_contrato(valor):
    """
    Normaliza IDs de contrato o documento de compras.

    Corrige casos como:
    - 4600003868.0
    - 4600003868.00
    - 4600003868,0
    - 4600003868,00
    - 4.600.003.868
    - 4,600,003,868
    """
    if pd.isna(valor):
        return pd.NA

    s = str(valor).strip()

    if s == "" or s.lower() in ["nan", "none", "null", "<na>"]:
        return pd.NA

    s = s.replace("\u00a0", "").strip()

    s = re.sub(r"([,.]0+)$", "", s)

    if re.fullmatch(r"[0-9.,]+", s):
        s = re.sub(r"[.,]", "", s)

    solo_digitos = re.sub(r"\D", "", s)

    if solo_digitos:
        s = solo_digitos

    return s


def limpiar_texto_serie(
    serie: pd.Series,
    quitar_decimal: bool = True,
) -> pd.Series:
    if quitar_decimal:
        return serie.apply(limpiar_id_contrato)

    serie_limpia = serie.astype(str).str.strip()

    return serie_limpia.replace(
        ["", "nan", "NaN", "None", "none", "NULL", "null"],
        pd.NA,
    )


def formato_usd_compacto(x, pos=None) -> str:
    """Formato USD compacto sin decimales."""
    if pd.isna(x):
        return "$0"

    if abs(x) >= 1_000_000_000:
        return f"${x / 1_000_000_000:.1f}B"

    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:.1f}M"

    if abs(x) >= 1_000:
        return f"${x / 1_000:.0f}K"

    return f"${x:,.0f}"


def formato_usd_compacto_2_decimales(x, pos=None) -> str:
    """Formato USD compacto conservando dos decimales."""
    if pd.isna(x):
        return "$0.00"

    if abs(x) >= 1_000_000_000:
        return f"${x / 1_000_000_000:.2f}B"

    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:.2f}M"

    if abs(x) >= 1_000:
        return f"${x / 1_000:.2f}K"

    return f"${x:,.2f}"


def formato_usd_largo(x) -> str:
    if pd.isna(x):
        x = 0

    return f"US$ {x:,.2f}"


def formato_usd_millones(x) -> str:
    if pd.isna(x):
        x = 0

    return f"US$ {x / 1_000_000:,.2f} MM"


def formato_entero(x) -> str:
    if pd.isna(x):
        x = 0

    return f"{int(round(x)):,.0f}"


def formato_porcentaje(x) -> str:
    if pd.isna(x):
        x = 0

    return f"{x:.2%}"


def validar_columnas(
    df: pd.DataFrame,
    columnas: list[str],
    nombre_df: str,
) -> list[str]:
    return [col for col in columnas if col not in df.columns]


# ============================================================
# Carga desde session_state
# ============================================================

render_logo()

st.markdown(
    "<div class='main-title'>Gastos de órdenes de compra</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='subtitle'>
        Análisis de órdenes de compra y gasto convertido a USD.
    </div>
    """,
    unsafe_allow_html=True,
)

if "dataframes_cargados" not in st.session_state:
    st.warning(
        "Primero debes cargar los archivos en la pestaña "
        "01_CARGA_ARCHIVOS."
    )
    st.stop()

dataframes = st.session_state["dataframes_cargados"]

DATAFRAMES_REQUERIDOS = [
    "df_moneda_cambio",
    "df_ordenes",
]

faltantes_df = [
    nombre
    for nombre in DATAFRAMES_REQUERIDOS
    if nombre not in dataframes
]

if faltantes_df:
    st.error(
        "Faltan DataFrames requeridos para esta pestaña: "
        + ", ".join(faltantes_df)
        + ". Vuelve a cargar los archivos en 01_CARGA_ARCHIVOS."
    )
    st.stop()

_df_moneda_cambio = dataframes["df_moneda_cambio"].copy()
_df_ordenes = dataframes["df_ordenes"].copy()

columnas_requeridas = {
    "df_ordenes": [
        "Documento_compras",
        "Fecha_documento",
        "Moneda",
        "Precio_neto",
    ],
    "df_moneda_cambio": [
        "Moneda",
        "Factor_USD_por_Unidad",
        "Valor_CLP_por_Unidad",
        "Fecha_Conversion",
    ],
}

validaciones = {
    nombre: validar_columnas(
        df,
        columnas_requeridas[nombre],
        nombre,
    )
    for nombre, df in {
        "df_ordenes": _df_ordenes,
        "df_moneda_cambio": _df_moneda_cambio,
    }.items()
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
def preparar_ordenes_usd(
    df_ordenes: pd.DataFrame,
    df_moneda_cambio: pd.DataFrame,
    version_cache: str,
) -> tuple[pd.DataFrame, list[str]]:
    df_ordenes_usd = df_ordenes.copy()
    df_cambio = df_moneda_cambio.copy()

    df_ordenes_usd["Moneda"] = (
        df_ordenes_usd["Moneda"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_cambio["Moneda"] = (
        df_cambio["Moneda"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_ordenes_usd["Precio_neto_num"] = (
        df_ordenes_usd["Precio_neto"]
        .apply(convertir_numero)
    )

    df_cambio["Factor_USD_por_Unidad"] = (
        df_cambio["Factor_USD_por_Unidad"]
        .apply(convertir_numero)
    )

    monedas_registros = set(
        df_ordenes_usd["Moneda"].dropna().unique()
    )

    monedas_tabla = set(
        df_cambio["Moneda"].dropna().unique()
    )

    monedas_faltantes = sorted(
        monedas_registros - monedas_tabla
    )

    columnas_cambio = [
        "Moneda",
        "Factor_USD_por_Unidad",
        "Valor_CLP_por_Unidad",
        "Fecha_Conversion",
    ]

    df_ordenes_usd = df_ordenes_usd.merge(
        df_cambio[columnas_cambio].drop_duplicates(
            subset=["Moneda"]
        ),
        on="Moneda",
        how="left",
    )

    df_ordenes_usd["Precio_neto_USD"] = (
        df_ordenes_usd["Precio_neto_num"]
        * df_ordenes_usd["Factor_USD_por_Unidad"]
    )

    df_ordenes_usd["Documento_Compras_Texto"] = (
        limpiar_texto_serie(
            df_ordenes_usd["Documento_compras"],
            quitar_decimal=True,
        )
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

    df_ordenes_usd = df_ordenes_usd.dropna(
        subset=["Fecha_documento"]
    ).copy()

    if not df_ordenes_usd.empty:
        df_ordenes_usd["Año"] = (
            df_ordenes_usd["Fecha_documento"].dt.year
        )

        df_ordenes_usd["Mes"] = (
            df_ordenes_usd["Fecha_documento"].dt.month
        )

        df_ordenes_usd["AñoMes"] = (
            df_ordenes_usd["Fecha_documento"]
            .dt.strftime("%Y-%m")
        )

        df_ordenes_usd["InicioMes"] = (
            df_ordenes_usd["Fecha_documento"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
    else:
        df_ordenes_usd["Año"] = pd.Series(
            dtype="int64"
        )

        df_ordenes_usd["Mes"] = pd.Series(
            dtype="int64"
        )

        df_ordenes_usd["AñoMes"] = pd.Series(
            dtype="object"
        )

        df_ordenes_usd["InicioMes"] = pd.Series(
            dtype="datetime64[ns]"
        )

    monto_total_oc_usd = (
        df_ordenes_usd["Monto_OC_USD"].sum()
    )

    df_ordenes_usd["Participacion_OC"] = (
        df_ordenes_usd["Monto_OC_USD"]
        / monto_total_oc_usd
        if monto_total_oc_usd != 0
        else 0
    )

    return df_ordenes_usd, monedas_faltantes


df_ordenes_usd, monedas_faltantes = preparar_ordenes_usd(
    _df_ordenes,
    _df_moneda_cambio,
    VERSION_NORMALIZACION_IDS,
)

if monedas_faltantes:
    st.warning(
        "Faltan monedas en df_moneda_cambio: "
        + ", ".join(monedas_faltantes)
    )

if df_ordenes_usd.empty:
    st.warning(
        "No hay órdenes con Fecha_documento válida para analizar."
    )
    st.stop()


# ============================================================
# Filtros de encabezado
# ============================================================

section_title(
    "Filtros",
    "Selecciona las fechas, el tipo de OC y la moneda "
    "para actualizar el análisis.",
)

with st.container(border=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    min_fecha = (
        df_ordenes_usd["Fecha_documento"]
        .min()
        .date()
    )

    max_fecha = (
        df_ordenes_usd["Fecha_documento"]
        .max()
        .date()
    )

    with col_f1:
        fecha_inicio = st.date_input(
            "Fecha inicial",
            value=min_fecha,
            min_value=min_fecha,
            max_value=max_fecha,
        )

    with col_f2:
        fecha_fin = st.date_input(
            "Fecha final",
            value=max_fecha,
            min_value=min_fecha,
            max_value=max_fecha,
        )

    with col_f3:
        tipos_oc_disponibles = sorted(
            [
                int(x)
                for x in (
                    df_ordenes_usd["Tipo_Orden_Compra"]
                    .dropna()
                    .unique()
                )
            ]
        )

        tipos_oc_sel = st.multiselect(
            "Tipo de OC",
            options=tipos_oc_disponibles,
            default=tipos_oc_disponibles,
        )

    with col_f4:
        monedas_disponibles = sorted(
            df_ordenes_usd["Moneda"]
            .dropna()
            .unique()
            .tolist()
        )

        monedas_sel = st.multiselect(
            "Moneda",
            options=monedas_disponibles,
            default=monedas_disponibles,
        )

if fecha_inicio > fecha_fin:
    st.error(
        "La fecha inicial no puede ser posterior a la fecha final."
    )
    st.stop()

fecha_inicio_ts = pd.Timestamp(fecha_inicio)

fecha_fin_ts = (
    pd.Timestamp(fecha_fin)
    + pd.Timedelta(days=1)
    - pd.Timedelta(seconds=1)
)

mask_ordenes = (
    (
        df_ordenes_usd["Fecha_documento"]
        >= fecha_inicio_ts
    )
    & (
        df_ordenes_usd["Fecha_documento"]
        <= fecha_fin_ts
    )
)

if tipos_oc_sel:
    mask_ordenes &= (
        df_ordenes_usd["Tipo_Orden_Compra"]
        .isin(tipos_oc_sel)
    )

if monedas_sel:
    mask_ordenes &= (
        df_ordenes_usd["Moneda"]
        .isin(monedas_sel)
    )

df_ordenes_filtrado = (
    df_ordenes_usd[mask_ordenes]
    .copy()
)

if df_ordenes_filtrado.empty:
    st.info(
        "No hay órdenes para los filtros seleccionados."
    )


# ============================================================
# KPIs
# ============================================================

section_title(
    "Indicadores principales",
    "Resumen ejecutivo del gasto filtrado.",
)

monto_total_oc_usd = (
    df_ordenes_filtrado["Monto_OC_USD"].sum()
)

monto_oc_tipo_44_usd = df_ordenes_filtrado.loc[
    df_ordenes_filtrado["Tipo_Orden_Compra"] == 44,
    "Monto_OC_USD",
].sum()

participacion_oc_tipo_44 = (
    monto_oc_tipo_44_usd / monto_total_oc_usd
    if monto_total_oc_usd != 0
    else 0
)

ordenes_unicas = (
    df_ordenes_filtrado["Documento_Compras_Texto"]
    .nunique()
)

monedas_unicas = (
    df_ordenes_filtrado["Moneda"]
    .nunique()
)

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    kpi_card(
        "Gasto total OC",
        formato_usd_largo(monto_total_oc_usd),
        (
            "Equivalente: "
            f"{formato_usd_millones(monto_total_oc_usd)}"
        ),
    )

with col_kpi2:
    kpi_card(
        "OC tipo 44",
        formato_usd_largo(monto_oc_tipo_44_usd),
        (
            f"{formato_usd_millones(monto_oc_tipo_44_usd)}"
            " | Participación: "
            f"{formato_porcentaje(participacion_oc_tipo_44)}"
        ),
    )

with col_kpi3:
    kpi_card(
        "N° órdenes",
        formato_entero(ordenes_unicas),
        f"Monedas analizadas: {monedas_unicas}",
    )

col_kpi4, col_kpi5 = st.columns(2)

with col_kpi4:
    kpi_card(
        "Periodo inicial",
        str(fecha_inicio),
        "Fecha inicial seleccionada",
    )

with col_kpi5:
    kpi_card(
        "Periodo final",
        str(fecha_fin),
        "Fecha final seleccionada",
    )


# ============================================================
# Gasto anual
# ============================================================

section_title(
    "Gasto total por año",
    "Suma anual del gasto de órdenes de compra convertido a USD.",
)

df_gasto_anual = (
    df_ordenes_filtrado
    .groupby(
        "Año",
        as_index=False,
    )["Monto_OC_USD"]
    .sum()
    .rename(
        columns={
            "Monto_OC_USD": "Gasto_Total_USD"
        }
    )
    .sort_values("Año")
)

if df_gasto_anual.empty:
    st.info(
        "No hay datos para graficar gasto anual."
    )
else:
    fig, ax = plt.subplots(
        figsize=(9, 5)
    )

    bars = ax.bar(
        df_gasto_anual["Año"].astype(str),
        df_gasto_anual["Gasto_Total_USD"],
        color="#2563eb",
        edgecolor="#1d4ed8",
        linewidth=0.8,
    )

    ax.set_title(
        "Total gasto por año",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )

    ax.set_xlabel("Año")
    ax.set_ylabel("Gasto total [USD]")

    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            formato_usd_compacto
        )
    )

    limpiar_estilo_grafico(ax)

    max_valor = (
        df_gasto_anual["Gasto_Total_USD"]
        .max()
    )

    margen_superior = (
        max_valor * 0.18
        if max_valor > 0
        else 1
    )

    ax.set_ylim(
        0,
        max_valor + margen_superior,
    )

    for bar in bars:
        valor = bar.get_height()

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            valor + margen_superior * 0.06,
            formato_usd_compacto(valor),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="#111827",
        )

    fig.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
    )

    with st.expander(
        "Ver tabla de gasto anual"
    ):
        st.dataframe(
            df_gasto_anual,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Gasto mensual
# ============================================================

section_title(
    "Gasto mensual",
    (
        "Desglose mensual del gasto en órdenes de compra. "
        "Selecciona un mes para revisar el detalle de registros."
    ),
)

df_gasto_mensual = (
    df_ordenes_filtrado
    .groupby(
        ["InicioMes", "AñoMes"],
        as_index=False,
    )["Monto_OC_USD"]
    .sum()
    .rename(
        columns={
            "Monto_OC_USD": "Gasto_Mensual_USD"
        }
    )
    .sort_values("InicioMes")
    .reset_index(drop=True)
)

if df_gasto_mensual.empty:
    st.info(
        "No hay datos para graficar gasto mensual."
    )
else:
    df_gasto_mensual_plot = (
        df_gasto_mensual.copy()
    )

    top_indices = (
        df_gasto_mensual_plot[
            "Gasto_Mensual_USD"
        ]
        .nlargest(5)
        .index
    )

    alto_grafico = max(
        6,
        0.42 * len(df_gasto_mensual_plot) + 2,
    )

    fig, ax = plt.subplots(
        figsize=(14, alto_grafico)
    )

    bars = ax.barh(
        df_gasto_mensual_plot["AñoMes"],
        df_gasto_mensual_plot["Gasto_Mensual_USD"],
        color="#2563eb",
        edgecolor="#1d4ed8",
        linewidth=0.8,
    )

    ax.set_title(
        "Gasto mensual en órdenes de compra",
        fontsize=15,
        fontweight="bold",
        pad=14,
    )

    ax.set_xlabel(
        "Gasto mensual [USD]"
    )

    ax.set_ylabel("Mes")

    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(
            formato_usd_compacto_2_decimales
        )
    )

    limpiar_estilo_grafico(ax)

    max_valor = (
        df_gasto_mensual_plot[
            "Gasto_Mensual_USD"
        ]
        .max()
    )

    margen_derecho = (
        max_valor * 0.24
        if max_valor > 0
        else 1
    )

    ax.set_xlim(
        0,
        max_valor + margen_derecho,
    )

    for i in top_indices:
        bar = bars[i]

        valor = df_gasto_mensual_plot.loc[
            i,
            "Gasto_Mensual_USD",
        ]

        ax.text(
            valor + margen_derecho * 0.04,
            bar.get_y() + bar.get_height() / 2,
            formato_usd_compacto_2_decimales(
                valor
            ),
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#111827",
        )

    fig.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
    )

    st.markdown(
        "#### Detalle del gasto mensual"
    )

    meses_disponibles = (
        df_gasto_mensual_plot["AñoMes"]
        .tolist()
    )

    mes_default_idx = (
        len(meses_disponibles) - 1
    )

    if not df_gasto_mensual_plot.empty:
        mes_default_idx = int(
            df_gasto_mensual_plot[
                "Gasto_Mensual_USD"
            ]
            .idxmax()
        )

    mes_seleccionado = st.selectbox(
        (
            "Selecciona un mes para visualizar "
            "el detalle de registros"
        ),
        options=meses_disponibles,
        index=mes_default_idx,
    )

    df_detalle_mes = df_ordenes_filtrado[
        df_ordenes_filtrado["AñoMes"]
        == mes_seleccionado
    ].copy()

    monto_mes_usd = (
        df_detalle_mes["Monto_OC_USD"]
        .sum()
    )

    ordenes_mes = (
        df_detalle_mes[
            "Documento_Compras_Texto"
        ]
        .nunique()
    )

    registros_mes = len(
        df_detalle_mes
    )

    monedas_mes = (
        df_detalle_mes["Moneda"]
        .nunique()
    )

    col_mes1, col_mes2, col_mes3, col_mes4 = (
        st.columns(4)
    )

    with col_mes1:
        kpi_card(
            "Gasto del mes",
            formato_usd_largo(monto_mes_usd),
            (
                f"{formato_usd_millones(monto_mes_usd)}"
                f" | Mes seleccionado: {mes_seleccionado}"
            ),
        )

    with col_mes2:
        kpi_card(
            "Órdenes únicas",
            formato_entero(ordenes_mes),
            "Documento de compras único",
        )

    with col_mes3:
        kpi_card(
            "Registros",
            formato_entero(registros_mes),
            "Líneas o registros del mes",
        )

    with col_mes4:
        kpi_card(
            "Monedas",
            formato_entero(monedas_mes),
            "Monedas presentes en el mes",
        )

    df_resumen_mes_tipo = (
        df_detalle_mes
        .groupby(
            "Tipo_Orden_Compra",
            as_index=False,
        )
        .agg(
            Monto_USD=(
                "Monto_OC_USD",
                "sum",
            ),
            Ordenes=(
                "Documento_Compras_Texto",
                "nunique",
            ),
            Registros=(
                "Documento_Compras_Texto",
                "count",
            ),
        )
        .sort_values(
            "Monto_USD",
            ascending=False,
        )
    )

    if not df_resumen_mes_tipo.empty:
        total_resumen_mes = (
            df_resumen_mes_tipo[
                "Monto_USD"
            ]
            .sum()
        )

        df_resumen_mes_tipo[
            "Participacion_%"
        ] = (
            df_resumen_mes_tipo["Monto_USD"]
            / total_resumen_mes
            * 100
            if total_resumen_mes != 0
            else 0
        )

    col_resumen_mes, col_detalle_mes = (
        st.columns([0.9, 1.6])
    )

    with col_resumen_mes:
        st.markdown(
            "##### Resumen por tipo de OC"
        )

        st.dataframe(
            df_resumen_mes_tipo,
            use_container_width=True,
            hide_index=True,
        )

    with col_detalle_mes:
        st.markdown(
            "##### Registros del mes seleccionado"
        )

        columnas_detalle_mes = [
            col
            for col in [
                "Documento_compras",
                "Documento_Compras_Texto",
                "Fecha_documento",
                "Texto_breve",
                "Moneda",
                "Precio_neto",
                "Precio_neto_num",
                "Factor_USD_por_Unidad",
                "Precio_neto_USD",
                "Monto_OC_USD",
                "Tipo_Orden_Compra",
                "Participacion_OC",
            ]
            if col in df_detalle_mes.columns
        ]

        df_detalle_mes_tabla = (
            df_detalle_mes[
                columnas_detalle_mes
            ]
            .sort_values(
                "Monto_OC_USD",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        st.dataframe(
            df_detalle_mes_tabla,
            use_container_width=True,
            hide_index=True,
        )

    with st.expander(
        "Ver tabla completa de gasto mensual"
    ):
        st.dataframe(
            df_gasto_mensual,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Participación por tipo de OC
# ============================================================

section_title(
    "Participación por tipo de orden de compra",
    (
        "Distribución del gasto total según los dos primeros "
        "dígitos del documento de compras."
    ),
)

df_tipo_oc = (
    df_ordenes_filtrado
    .groupby(
        "Tipo_Orden_Compra",
        as_index=False,
    )
    .agg(
        Monto_OC_USD=(
            "Monto_OC_USD",
            "sum",
        ),
        Ordenes=(
            "Documento_Compras_Texto",
            "nunique",
        ),
    )
    .sort_values(
        "Monto_OC_USD",
        ascending=False,
    )
)

total_tipo_oc = (
    df_tipo_oc["Monto_OC_USD"]
    .sum()
)

df_tipo_oc["Participacion"] = (
    df_tipo_oc["Monto_OC_USD"]
    / total_tipo_oc
    if total_tipo_oc != 0
    else 0
)

if df_tipo_oc.empty:
    st.info(
        "No hay datos para analizar tipos de orden de compra."
    )
else:
    fig, ax = plt.subplots(
        figsize=(11, 5.5)
    )

    bars = ax.bar(
        df_tipo_oc[
            "Tipo_Orden_Compra"
        ].astype(str),
        df_tipo_oc[
            "Monto_OC_USD"
        ],
        color="#2563eb",
        edgecolor="#1d4ed8",
        linewidth=0.8,
    )

    ax.set_title(
        "Gasto por tipo de OC",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )

    ax.set_xlabel(
        "Tipo de OC"
    )

    ax.set_ylabel(
        "Gasto [USD]"
    )

    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            formato_usd_compacto
        )
    )

    limpiar_estilo_grafico(ax)

    max_valor = (
        df_tipo_oc[
            "Monto_OC_USD"
        ]
        .max()
    )

    margen_superior = (
        max_valor * 0.18
        if max_valor > 0
        else 1
    )

    ax.set_ylim(
        0,
        max_valor + margen_superior,
    )

    for bar in bars:
        valor = bar.get_height()

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            valor + margen_superior * 0.06,
            formato_usd_compacto(valor),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="#111827",
        )

    fig.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
    )

    with st.expander(
        "Ver tabla por tipo de OC"
    ):
        st.dataframe(
            df_tipo_oc,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Tablas de apoyo y validaciones
# ============================================================

section_title(
    "Tablas de apoyo",
    "Vistas acotadas para revisar conversiones "
    "y validaciones de gasto.",
)

with st.expander(
    "Monedas únicas en órdenes"
):
    df_monedas_unicas = pd.DataFrame(
        {
            "Moneda": sorted(
                df_ordenes_usd[
                    "Moneda"
                ]
                .dropna()
                .unique()
            )
        }
    ).reset_index(drop=True)

    st.dataframe(
        df_monedas_unicas,
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Órdenes convertidas a USD"
):
    columnas_preview = [
        col
        for col in [
            "Documento_compras",
            "Documento_Compras_Texto",
            "Fecha_documento",
            "Texto_breve",
            "Moneda",
            "Precio_neto",
            "Precio_neto_num",
            "Factor_USD_por_Unidad",
            "Precio_neto_USD",
            "Tipo_Orden_Compra",
            "Participacion_OC",
        ]
        if col in df_ordenes_usd.columns
    ]

    st.dataframe(
        df_ordenes_usd[
            columnas_preview
        ].head(500),
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Resumen de validación"
):
    if not monedas_faltantes:
        st.success(
            "Todas las monedas de df_ordenes "
            "existen en df_moneda_cambio."
        )
    else:
        st.warning(
            "Hay monedas de df_ordenes que no fueron "
            "encontradas en df_moneda_cambio."
        )

        st.write(
            ", ".join(monedas_faltantes)
        )

    st.write(
        "- Órdenes únicas filtradas: "
        f"{ordenes_unicas:,.0f}"
    )

    st.write(
        "- Gasto total filtrado: "
        f"{formato_usd_largo(monto_total_oc_usd)}"
    )
