# ============================================================
# 04_APP_SALUD_CONTRATOS.py
# Dashboard de Monitoreo de Contratos ENAEX
# Pestaña: Salud de contratos
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
    page_title="04_SALUD_CONTRATOS | Dashboard Contratos ENAEX",
    page_icon="🩺",
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


def limpiar_estilo_grafico(ax) -> None:
    """Aplica formato visual limpio: sin grillas internas y sin bordes superiores/derechos."""
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
    Normaliza IDs de contrato/documento para cruces.

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


def limpiar_texto_serie(serie: pd.Series, quitar_decimal: bool = True) -> pd.Series:
    if quitar_decimal:
        return serie.apply(limpiar_id_contrato)

    serie_limpia = serie.astype(str).str.strip()
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


def validar_columnas(df: pd.DataFrame, columnas: list[str], nombre_df: str) -> list[str]:
    return [col for col in columnas if col not in df.columns]


# ============================================================
# Carga desde session_state
# ============================================================

render_logo()

st.markdown(
    "<div class='main-title'>Salud y vigencia de contratos</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>Estado de vigencia, cobertura ME5A y contratos por vencer por gestor.</div>",
    unsafe_allow_html=True,
)

if "dataframes_cargados" not in st.session_state:
    st.warning("Primero debes cargar los archivos en la pestaña 01_CARGA_ARCHIVOS.")
    st.stop()

dataframes = st.session_state["dataframes_cargados"]
DATAFRAMES_REQUERIDOS = ["df_bbdd_x_categoria", "df_me5a"]
faltantes_df = [nombre for nombre in DATAFRAMES_REQUERIDOS if nombre not in dataframes]

if faltantes_df:
    st.error(
        "Faltan DataFrames requeridos para esta pestaña: "
        + ", ".join(faltantes_df)
        + ". Vuelve a cargar los archivos en 01_CARGA_ARCHIVOS."
    )
    st.stop()

_df_bbdd_x_categoria = dataframes["df_bbdd_x_categoria"].copy()
_df_me5a = dataframes["df_me5a"].copy()

columnas_requeridas = {
    "df_bbdd_x_categoria": ["Contrato", "Gestor_Contrato"],
    "df_me5a": ["Documento_compras", "Fin_período_validez"],
}
validaciones = {
    "df_bbdd_x_categoria": validar_columnas(
        _df_bbdd_x_categoria, columnas_requeridas["df_bbdd_x_categoria"], "df_bbdd_x_categoria"
    ),
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
# Preparación: contratos y estado de vigencia
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_contratos_estado(
    df_bbdd_x_categoria: pd.DataFrame,
    df_me5a: pd.DataFrame,
    version_cache: str,
) -> pd.DataFrame:
    df_cat = df_bbdd_x_categoria.copy()
    df_m5 = df_me5a.copy()

    df_cat["Contrato_Original"] = df_cat["Contrato"]
    df_m5["Documento_Compras_Original_ME5A"] = df_m5["Documento_compras"]

    df_cat["Contrato"] = df_cat["Contrato"].apply(limpiar_id_contrato)
    df_m5["Documento_compras"] = df_m5["Documento_compras"].apply(limpiar_id_contrato)

    df_cat = df_cat.dropna(subset=["Contrato"]).copy()
    df_m5 = df_m5.dropna(subset=["Documento_compras"]).copy()

    df_cat["Contrato"] = df_cat["Contrato"].astype(str).str.strip()
    df_m5["Documento_compras"] = df_m5["Documento_compras"].astype(str).str.strip()

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
        .agg(
            Fin_período_validez=("Fin_período_validez", "max"),
            Documento_Compras_Original_ME5A=("Documento_Compras_Original_ME5A", "first"),
        )
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
    df_contratos_estado["Contrato"] = df_contratos_estado["Contrato"].apply(limpiar_id_contrato).astype(str)

    return df_contratos_estado


df_contratos_estado = preparar_contratos_estado(
    _df_bbdd_x_categoria,
    _df_me5a,
    VERSION_NORMALIZACION_IDS,
)

if df_contratos_estado.empty:
    st.warning("No hay contratos válidos para analizar.")
    st.stop()

# ============================================================
# Filtros de encabezado
# ============================================================

section_title("Filtros", "Selecciona uno o más gestores para actualizar el análisis contractual.")

gestores_disponibles = sorted(
    df_contratos_estado["Gestor_Contrato"].dropna().unique().tolist()
)

with st.container(border=True):
    gestores_sel = st.multiselect(
        "Gestor contrato",
        options=gestores_disponibles,
        default=gestores_disponibles,
    )

if gestores_sel:
    df_contratos_estado_filtrado = df_contratos_estado[
        df_contratos_estado["Gestor_Contrato"].isin(gestores_sel)
    ].copy()
else:
    df_contratos_estado_filtrado = df_contratos_estado.iloc[0:0].copy()

# ============================================================
# KPIs
# ============================================================

section_title("Indicadores principales", "Resumen ejecutivo de cobertura y vigencia contractual.")

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

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    kpi_card("N° contratos", formato_entero(recuento_contratos), "Contratos únicos filtrados")
with col_kpi2:
    kpi_card("Contratos con ME5A", formato_entero(contratos_cruzados_me5a), "Cruce por documento de compras")
with col_kpi3:
    kpi_card("Sin información ME5A", formato_entero(contratos_sin_me5a), "Contratos no encontrados en ME5A")
with col_kpi4:
    kpi_card("Por vencer", formato_entero(contratos_por_vencer), "Vencimiento dentro de los próximos tres meses")

# ============================================================
# Detalle contratos sin información ME5A
# ============================================================

df_sin_info_me5a = df_contratos_estado_filtrado[
    df_contratos_estado_filtrado["Estado"] == "Sin información ME5A"
].copy()

if not df_sin_info_me5a.empty:
    with st.expander("Ver detalle de contratos no encontrados en ME5A", expanded=False):
        st.caption(
            "Estos contratos existen en la base de contratos/categoría, pero no tuvieron coincidencia en ME5A mediante el campo Documento_compras."
        )

        df_sin_info_me5a["Contrato"] = df_sin_info_me5a["Contrato"].apply(limpiar_id_contrato).astype(str)

        columnas_sin_me5a = [
            col for col in [
                "Contrato",
                "Contrato_Original",
                "Gestor_Contrato",
                "Documento_compras",
                "Fin_período_validez",
                "Estado",
                "Fecha_Analisis",
            ] if col in df_sin_info_me5a.columns
        ]

        df_sin_info_me5a_tabla = (
            df_sin_info_me5a[columnas_sin_me5a]
            .drop_duplicates()
            .sort_values(["Gestor_Contrato", "Contrato"])
            .reset_index(drop=True)
        )

        col_sin_1, col_sin_2 = st.columns([0.8, 1.2])

        with col_sin_1:
            df_sin_me5a_resumen = (
                df_sin_info_me5a_tabla
                .groupby("Gestor_Contrato", as_index=False)["Contrato"]
                .nunique()
                .rename(columns={"Contrato": "Contratos_No_Encontrados_ME5A"})
                .sort_values("Contratos_No_Encontrados_ME5A", ascending=False)
            )

            st.markdown("##### Resumen por gestor")
            st.dataframe(
                df_sin_me5a_resumen,
                use_container_width=True,
                hide_index=True,
            )

        with col_sin_2:
            st.markdown("##### Contratos no encontrados")
            st.dataframe(
                df_sin_info_me5a_tabla,
                use_container_width=True,
                hide_index=True,
            )
else:
    st.success("Todos los contratos filtrados tienen información asociada en ME5A.")


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

    colores_estado_barras = {
        "Vencido": "#ef4444",
        "Por Vencer": "#f59e0b",
        "Vigente": "#22c55e",
        "Sin fecha": "#94a3b8",
        "Sin información ME5A": "#64748b",
    }

    colores_stack = [
        colores_estado_barras.get(col, "#cbd5e1")
        for col in df_plot_estado.columns
    ]

    fig, ax = plt.subplots(figsize=(12, max(6, 0.38 * len(df_plot_estado) + 2)))

    df_plot_estado.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        color=colores_stack,
        edgecolor="white",
        linewidth=0.8,
    )

    ax.set_title("Recuento de contratos por gestor y estado de vigencia", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Recuento de contratos")
    ax.set_ylabel("Gestor de contrato")
    ax.legend(title="Estado", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    limpiar_estilo_grafico(ax)

    max_total_contratos = df_pivot_estado["Total_Contratos"].max()
    margen_derecho = max(1, max_total_contratos * 0.22)

    ax.set_xlim(0, max_total_contratos + margen_derecho)

    for i, total in enumerate(df_pivot_estado["Total_Contratos"]):
        ax.text(
            total + margen_derecho * 0.08,
            i,
            str(int(total)),
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#111827",
        )

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

        colores_estado = {
            "Vencido": "#ef4444",
            "Por Vencer": "#f59e0b",
            "Vigente": "#22c55e",
            "Sin fecha": "#94a3b8",
            "Sin información ME5A": "#64748b",
        }

        colores_grafico = [
            colores_estado.get(estado, "#cbd5e1")
            for estado in df_estado_global["Estado"]
        ]

        fig, ax = plt.subplots(figsize=(5.8, 4.8))

        wedges, texts, autotexts = ax.pie(
            df_estado_global["Recuento_Contratos"],
            labels=None,
            autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
            startangle=90,
            pctdistance=0.78,
            colors=colores_grafico,
            wedgeprops={"width": 0.38, "edgecolor": "white"},
            textprops={"fontsize": 8, "fontweight": "bold", "color": "#111827"},
        )

        ax.text(
            0,
            0.05,
            f"{total_contratos:,.0f}",
            ha="center",
            va="center",
            fontsize=20,
            fontweight="bold",
        )
        ax.text(
            0,
            -0.13,
            "contratos",
            ha="center",
            va="center",
            fontsize=10,
        )

        ax.set_title("Distribución global", fontsize=13, fontweight="bold")

        leyenda_labels = [
            f"{row['Estado']} | {int(row['Recuento_Contratos'])} contratos | {row['Participacion_%']:.1f}%"
            for _, row in df_estado_global.iterrows()
        ]

        ax.legend(
            wedges,
            leyenda_labels,
            title="Estado",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=8,
            title_fontsize=9,
            frameon=False,
        )

        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

    with col_tabla:
        st.dataframe(df_estado_global, use_container_width=True, hide_index=True)


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

        im = ax.imshow(
            matriz,
            aspect="auto",
            cmap="YlGnBu",
        )

        ax.set_xticks(np.arange(len(df_heatmap_plot.columns)))
        ax.set_xticklabels(df_heatmap_plot.columns, rotation=45, ha="right")
        ax.set_yticks(np.arange(len(df_heatmap_plot.index)))
        ax.set_yticklabels(df_heatmap_plot.index)

        ax.set_title(
            "Mapa de calor de contratos por gestor y estado",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("Estado")
        ax.set_ylabel("Gestor de contrato")

        valor_maximo = matriz.max() if matriz.size > 0 else 0

        for i in range(matriz.shape[0]):
            for j in range(matriz.shape[1]):
                valor = matriz[i, j]

                if valor > 0:
                    color_texto = "white" if valor_maximo > 0 and valor >= valor_maximo * 0.65 else "#111827"

                    ax.text(
                        j,
                        i,
                        int(valor),
                        ha="center",
                        va="center",
                        fontsize=9,
                        fontweight="bold",
                        color=color_texto,
                    )

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("Recuento de contratos")

        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

        with st.expander("Ver tabla del mapa de calor"):
            st.dataframe(df_heatmap_plot, use_container_width=True)


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

    bars = ax.barh(
        df_top_por_vencer["Gestor_Contrato"],
        df_top_por_vencer["Contratos_Por_Vencer"],
        color="#f59e0b",
        edgecolor="#d97706",
        linewidth=0.8,
    )

    ax.set_title("Contratos por vencer por gestor", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Recuento de contratos por vencer")
    ax.set_ylabel("Gestor de contrato")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    limpiar_estilo_grafico(ax)

    max_por_vencer = df_top_por_vencer["Contratos_Por_Vencer"].max()
    margen_por_vencer = max(1, max_por_vencer * 0.22)

    ax.set_xlim(0, max_por_vencer + margen_por_vencer)

    for bar in bars:
        valor = bar.get_width()
        y_pos = bar.get_y() + bar.get_height() / 2

        ax.text(
            valor + margen_por_vencer * 0.08,
            y_pos,
            str(int(valor)),
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#111827",
        )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla de contratos por vencer"):
        st.dataframe(df_top_por_vencer, use_container_width=True, hide_index=True)


# ============================================================
# Tablas de apoyo y validaciones
# ============================================================

section_title("Tablas de apoyo", "Vistas acotadas para revisar cruces y validaciones contractuales.")

with st.expander("Contratos con estado de vigencia"):
    columnas_preview = [
        col for col in [
            "Contrato", "Contrato_Original", "Gestor_Contrato",
            "Documento_compras", "Documento_Compras_Original_ME5A",
            "Fin_período_validez", "Estado", "Fecha_Analisis",
        ] if col in df_contratos_estado.columns
    ]
    st.dataframe(
        df_contratos_estado[columnas_preview].head(500),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Resumen de validación"):
    st.write(f"- Total contratos únicos en df_bbdd_x_categoria: {df_contratos_estado['Contrato'].nunique():,.0f}")
    st.write(f"- Contratos únicos filtrados: {recuento_contratos:,.0f}")
    st.write(f"- Contratos filtrados cruzados con ME5A: {contratos_cruzados_me5a:,.0f}")
    st.write(f"- Contratos filtrados sin información en ME5A: {contratos_sin_me5a:,.0f}")
    st.write(f"- Fecha usada como TODAY(): {pd.Timestamp.today().normalize().date()}")
