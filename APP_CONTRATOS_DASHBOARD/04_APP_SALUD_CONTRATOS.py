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

VERSION_NORMALIZACION_IDS = "v_2026_06_10_cobertura_me3n"


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
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }

        div[data-testid="stExpander"] {
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            background: #ffffff;
            overflow: hidden;
        }

        div[data-testid="stExpander"] summary {
            font-weight: 750;
            color: #111827;
        }

        .kpi-card {
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .kpi-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.07);
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
    """Tarjeta KPI personalizada."""
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
    """Renderiza título y descripción de sección."""
    st.markdown(
        f"<div class='section-title'>{title}</div>",
        unsafe_allow_html=True,
    )

    if caption:
        st.markdown(
            f"<div class='section-caption'>{caption}</div>",
            unsafe_allow_html=True,
        )


def limpiar_estilo_grafico(ax, eje_grilla: str | None = None) -> None:
    """Aplica un formato visual limpio y consistente a los gráficos."""
    ax.set_axisbelow(True)

    if eje_grilla in {"x", "y"}:
        ax.grid(
            axis=eje_grilla,
            color="#E5E7EB",
            linewidth=0.8,
            alpha=0.75,
        )
    else:
        ax.grid(False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")

    ax.tick_params(axis="x", colors="#374151", labelsize=9)
    ax.tick_params(axis="y", colors="#374151", labelsize=9)


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


def limpiar_texto_serie(
    serie: pd.Series,
    quitar_decimal: bool = True,
) -> pd.Series:
    """Limpia una serie textual."""
    if quitar_decimal:
        return serie.apply(limpiar_id_contrato)

    serie_limpia = serie.astype(str).str.strip()

    return serie_limpia.replace(
        ["", "nan", "NaN", "None", "none", "NULL", "null"],
        pd.NA,
    )


def formato_usd_compacto(x, pos=None) -> str:
    """Formato monetario abreviado."""
    if pd.isna(x):
        return "$0"

    if abs(x) >= 1_000_000_000:
        return f"${x / 1_000_000_000:.1f}B"

    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:.1f}M"

    if abs(x) >= 1_000:
        return f"${x / 1_000:.0f}K"

    return f"${x:,.0f}"


def formato_usd_largo(x) -> str:
    """Formato monetario con dos decimales."""
    if pd.isna(x):
        x = 0

    return f"US$ {x:,.2f}"


def formato_usd_millones(x) -> str:
    """Formato monetario expresado en millones."""
    if pd.isna(x):
        x = 0

    return f"US$ {x / 1_000_000:,.2f} MM"


def formato_entero(x) -> str:
    """Formato entero con separador de miles."""
    if pd.isna(x):
        x = 0

    return f"{int(round(x)):,.0f}"


def formato_porcentaje(x) -> str:
    """Formato porcentual sin decimales innecesarios."""
    if pd.isna(x):
        x = 0

    porcentaje = float(x) * 100

    if np.isclose(porcentaje, round(porcentaje)):
        return f"{porcentaje:.0f}%"

    return f"{porcentaje:.2f}%"


def validar_columnas(
    df: pd.DataFrame,
    columnas: list[str],
    nombre_df: str,
) -> list[str]:
    """Retorna las columnas faltantes."""
    return [columna for columna in columnas if columna not in df.columns]


# ============================================================
# Carga desde session_state
# ============================================================

render_logo()

st.markdown(
    "<div class='main-title'>Salud y vigencia de contratos</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='subtitle'>
        Estado de vigencia, cobertura ME3N y contratos por vencer por gestor.
    </div>
    """,
    unsafe_allow_html=True,
)

if "dataframes_cargados" not in st.session_state:
    st.warning("Primero debes cargar los archivos en la pestaña 01_CARGA_ARCHIVOS.")
    st.stop()

dataframes = st.session_state["dataframes_cargados"]

DATAFRAMES_REQUERIDOS = [
    "df_bbdd_x_categoria",
    "df_me3n",
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

_df_bbdd_x_categoria = dataframes["df_bbdd_x_categoria"].copy()
_df_me3n = dataframes["df_me3n"].copy()

columnas_requeridas = {
    "df_bbdd_x_categoria": [
        "Contrato",
        "Gestor_Contrato",
    ],
    "df_me3n": [
        "Documento_compras",
        "Fin_período_validez",
    ],
}

validaciones = {
    "df_bbdd_x_categoria": validar_columnas(
        _df_bbdd_x_categoria,
        columnas_requeridas["df_bbdd_x_categoria"],
        "df_bbdd_x_categoria",
    ),
    "df_me3n": validar_columnas(
        _df_me3n,
        columnas_requeridas["df_me3n"],
        "df_me3n",
    ),
}

errores_columnas = [
    f"{nombre}: {', '.join(columnas)}"
    for nombre, columnas in validaciones.items()
    if columnas
]

if errores_columnas:
    st.error("Hay columnas faltantes en los archivos cargados:")

    for error in errores_columnas:
        st.write(f"- {error}")

    st.stop()


# ============================================================
# Preparación: contratos, estado y cobertura ME3N
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_contratos_estado(
    df_bbdd_x_categoria: pd.DataFrame,
    df_me3n: pd.DataFrame,
    version_cache: str,
) -> pd.DataFrame:
    """
    Prepara la base consolidada de contratos.

    Cruce:
    - df_bbdd_x_categoria["Contrato"]
      contra df_me3n["Documento_compras"]
      para vigencia y cobertura ME3N.
    """
    df_cat = df_bbdd_x_categoria.copy()
    df_m3n = df_me3n.copy()

    # ----------------------------
    # Base contratos / categoría
    # ----------------------------
    df_cat["Contrato_Original"] = df_cat["Contrato"]
    df_cat["Contrato"] = df_cat["Contrato"].apply(limpiar_id_contrato)
    df_cat = df_cat.dropna(subset=["Contrato"]).copy()
    df_cat["Contrato"] = df_cat["Contrato"].astype(str).str.strip()

    df_cat["Gestor_Contrato"] = (
        df_cat["Gestor_Contrato"]
        .astype(str)
        .str.strip()
        .replace(
            ["", "nan", "NaN", "None", "none", "NULL", "null"],
            "Sin gestor",
        )
    )

    # ----------------------------
    # ME3N
    # ----------------------------
    df_m3n["Documento_Compras_Original_ME3N"] = df_m3n["Documento_compras"]
    df_m3n["Documento_compras"] = df_m3n["Documento_compras"].apply(limpiar_id_contrato)
    df_m3n = df_m3n.dropna(subset=["Documento_compras"]).copy()
    df_m3n["Documento_compras"] = df_m3n["Documento_compras"].astype(str).str.strip()

    df_m3n["Fin_período_validez"] = pd.to_datetime(
        df_m3n["Fin_período_validez"],
        errors="coerce",
    )

    hoy = pd.Timestamp.today().normalize()

    def clasificar_estado(fecha_fin):
        """Clasifica el contrato según la fecha fin ME3N."""
        if pd.isna(fecha_fin):
            return "Sin fecha"

        if fecha_fin < hoy:
            return "Vencido"

        meses_diferencia = (
            (fecha_fin.year - hoy.year) * 12
            + fecha_fin.month
            - hoy.month
        )

        if meses_diferencia <= 3:
            return "Por Vencer"

        return "Vigente"

    columna_proveedor = "Proveedor/Centro_suministrador"

    if columna_proveedor not in df_m3n.columns:
        df_m3n[columna_proveedor] = pd.NA

    df_m3n[columna_proveedor] = (
        df_m3n[columna_proveedor]
        .astype(str)
        .str.strip()
        .replace(
            ["", "nan", "NaN", "None", "none", "NULL", "null", "<NA>"],
            pd.NA,
        )
    )

    df_m3n_contrato = (
        df_m3n
        .groupby("Documento_compras", as_index=False)
        .agg(
            Fin_período_validez=("Fin_período_validez", "max"),
            Proveedor=("Proveedor/Centro_suministrador", "first"),
            Documento_Compras_Original_ME3N=(
                "Documento_Compras_Original_ME3N",
                "first",
            ),
        )
    )

    df_m3n_contrato["Estado"] = (
        df_m3n_contrato["Fin_período_validez"]
        .apply(clasificar_estado)
    )

    df_m3n_contrato = df_m3n_contrato.rename(
        columns={
            "Documento_compras": "Documento_compras_ME3N",
        }
    )

    # ----------------------------
    # Merge ME3N
    # ----------------------------
    df_contratos_estado = df_cat.merge(
        df_m3n_contrato,
        left_on="Contrato",
        right_on="Documento_compras_ME3N",
        how="left",
    )

    df_contratos_estado["Estado"] = (
        df_contratos_estado["Estado"]
        .fillna("Sin información ME3N")
    )

    df_contratos_estado["Validacion_Cobertura_ME3N"] = np.where(
        df_contratos_estado["Documento_compras_ME3N"].notna(),
        "Con cobertura ME3N",
        "Sin cobertura ME3N",
    )

    df_contratos_estado["Fecha_Analisis"] = hoy

    df_contratos_estado["Contrato"] = (
        df_contratos_estado["Contrato"]
        .apply(limpiar_id_contrato)
        .astype(str)
    )

    return df_contratos_estado


df_contratos_estado = preparar_contratos_estado(
    _df_bbdd_x_categoria,
    _df_me3n,
    VERSION_NORMALIZACION_IDS,
)

if df_contratos_estado.empty:
    st.warning("No hay contratos válidos para analizar.")
    st.stop()


# ============================================================
# Filtros globales
# ============================================================

section_title(
    "Filtros globales",
    (
        "Aplica los mismos criterios a indicadores, gráficos, mapas de calor "
        "y tablas de detalle."
    ),
)

gestores_disponibles = sorted(
    df_contratos_estado["Gestor_Contrato"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

estados_disponibles_globales = [
    estado
    for estado in [
        "Vencido",
        "Por Vencer",
        "Vigente",
        "Sin fecha",
        "Sin información ME3N",
    ]
    if estado in df_contratos_estado["Estado"].dropna().unique()
]

with st.container(border=True):
    gestores_sel = st.multiselect(
        "Gestor de contrato",
        options=gestores_disponibles,
        default=gestores_disponibles,
        key="salud_filtro_gestor_global",
    )

    col_filtro_1, col_filtro_2 = st.columns([1.25, 0.75])

    with col_filtro_1:
        estados_sel_globales = st.multiselect(
            "Estado de vigencia",
            options=estados_disponibles_globales,
            default=estados_disponibles_globales,
            key="salud_filtro_estado_global",
        )

    with col_filtro_2:
        cobertura_sel = st.selectbox(
            "Cobertura ME3N",
            options=[
                "Todos",
                "Con cobertura ME3N",
                "Sin cobertura ME3N",
            ],
            key="salud_filtro_cobertura_global",
        )

df_contratos_estado_filtrado = df_contratos_estado.copy()

if gestores_sel:
    df_contratos_estado_filtrado = df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Gestor_Contrato"].isin(gestores_sel)
    ]
else:
    df_contratos_estado_filtrado = df_contratos_estado_filtrado.iloc[0:0]

if estados_sel_globales:
    df_contratos_estado_filtrado = df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Estado"].isin(estados_sel_globales)
    ]
else:
    df_contratos_estado_filtrado = df_contratos_estado_filtrado.iloc[0:0]

if cobertura_sel != "Todos":
    df_contratos_estado_filtrado = df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Validacion_Cobertura_ME3N"] == cobertura_sel
    ]


# ============================================================
# Cálculo de indicadores
# ============================================================

recuento_contratos = (
    df_contratos_estado_filtrado["Contrato"]
    .nunique()
)

contratos_cruzados_me3n = (
    df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Documento_compras_ME3N"].notna()
    ]["Contrato"]
    .nunique()
)

contratos_sin_me3n = (
    df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Validacion_Cobertura_ME3N"]
        == "Sin cobertura ME3N"
    ]["Contrato"]
    .nunique()
)

contratos_por_vencer = (
    df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Estado"] == "Por Vencer"
    ]["Contrato"]
    .nunique()
)

cobertura_me3n = (
    contratos_cruzados_me3n / recuento_contratos
    if recuento_contratos > 0
    else 0
)

sin_cobertura_me3n = (
    contratos_sin_me3n / recuento_contratos
    if recuento_contratos > 0
    else 0
)


# ============================================================
# Indicadores principales
# ============================================================

section_title(
    "Indicadores principales",
    "Resumen ejecutivo de la cartera contractual filtrada.",
)

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    kpi_card(
        "N° contratos",
        formato_entero(recuento_contratos),
        "Contratos únicos filtrados",
    )

with col_kpi2:
    kpi_card(
        "Contratos con ME3N",
        formato_entero(contratos_cruzados_me3n),
        "Cruce contra ME3N",
    )

with col_kpi3:
    kpi_card(
        "Sin ME3N",
        formato_entero(contratos_sin_me3n),
        "Contratos sin coincidencia",
    )

with col_kpi4:
    kpi_card(
        "Por vencer",
        formato_entero(contratos_por_vencer),
        "Vencimiento dentro de los próximos tres meses",
    )


# ============================================================
# Agregaciones compartidas
# ============================================================

orden_estados = [
    "Vencido",
    "Por Vencer",
    "Vigente",
    "Sin fecha",
    "Sin información ME3N",
]

colores_estado = {
    "Vencido": "#ef4444",
    "Por Vencer": "#f59e0b",
    "Vigente": "#22c55e",
    "Sin fecha": "#94a3b8",
    "Sin información ME3N": "#64748b",
}

df_recuento_estado = (
    df_contratos_estado_filtrado
    .groupby(["Gestor_Contrato", "Estado"], as_index=False)["Contrato"]
    .nunique()
    .rename(columns={"Contrato": "Recuento_Contratos"})
)

df_estado_global = (
    df_contratos_estado_filtrado
    .groupby("Estado", as_index=False)["Contrato"]
    .nunique()
    .rename(columns={"Contrato": "Recuento_Contratos"})
)

mapa_orden_estados = {
    estado: indice
    for indice, estado in enumerate(orden_estados)
}

df_estado_global["Orden_Estado"] = (
    df_estado_global["Estado"]
    .map(mapa_orden_estados)
    .fillna(len(orden_estados))
)

df_estado_global = (
    df_estado_global
    .sort_values(
        ["Orden_Estado", "Recuento_Contratos"],
        ascending=[True, False],
    )
    .drop(columns="Orden_Estado")
    .reset_index(drop=True)
)

total_estado_global = df_estado_global["Recuento_Contratos"].sum()

if total_estado_global > 0:
    df_estado_global["Participacion_%"] = (
        df_estado_global["Recuento_Contratos"]
        / total_estado_global
        * 100
    )
else:
    df_estado_global["Participacion_%"] = 0.0


# ============================================================
# Distribución global por estado
# ============================================================

section_title(
    "Distribución global de contratos por estado",
    "Panorama general de la vigencia contractual para los gestores seleccionados.",
)

if df_estado_global.empty:
    st.info("No hay datos para graficar la distribución global por estado.")
else:
    col_donut, col_tabla = st.columns([0.95, 1.05])

    with col_donut:
        colores_grafico = [
            colores_estado.get(estado, "#cbd5e1")
            for estado in df_estado_global["Estado"]
        ]

        fig, ax = plt.subplots(figsize=(7.2, 5.8))

        wedges, _, _ = ax.pie(
            df_estado_global["Recuento_Contratos"],
            labels=None,
            autopct=lambda porcentaje: f"{porcentaje:.1f}%" if porcentaje >= 2.5 else "",
            startangle=90,
            counterclock=False,
            pctdistance=0.79,
            colors=colores_grafico,
            wedgeprops={
                "width": 0.40,
                "edgecolor": "white",
                "linewidth": 1.2,
            },
            textprops={
                "fontsize": 9,
                "fontweight": "bold",
                "color": "#111827",
            },
        )

        ax.text(
            0,
            0.06,
            f"{int(total_estado_global):,}",
            ha="center",
            va="center",
            fontsize=23,
            fontweight="bold",
            color="#111827",
        )

        ax.text(
            0,
            -0.13,
            "contratos",
            ha="center",
            va="center",
            fontsize=10,
            color="#6b7280",
        )

        ax.set_title(
            "Estado general de los contratos",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )

        leyenda_labels = [
            (
                f"{fila['Estado']} | "
                f"{int(fila['Recuento_Contratos'])} contratos | "
                f"{fila['Participacion_%']:.1f}%"
            )
            for _, fila in df_estado_global.iterrows()
        ]

        ax.legend(
            wedges,
            leyenda_labels,
            title="Estado",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=8.5,
            title_fontsize=9.5,
            frameon=False,
        )

        ax.axis("equal")
        fig.tight_layout()

        st.pyplot(fig, clear_figure=True)

    with col_tabla:
        df_estado_global_tabla = df_estado_global.copy()

        df_estado_global_tabla = (
            df_estado_global_tabla
            .rename(
                columns={
                    "Recuento_Contratos": "Contratos",
                    "Participacion_%": "Participación",
                }
            )
            [["Estado", "Contratos", "Participación"]]
        )

        st.markdown("##### Resumen por estado")

        st.dataframe(
            df_estado_global_tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Estado": st.column_config.TextColumn("Estado"),
                "Contratos": st.column_config.NumberColumn(
                    "Contratos",
                    format="%d",
                ),
                "Participación": st.column_config.ProgressColumn(
                    "Participación",
                    format="%.1f%%",
                    min_value=0.0,
                    max_value=100.0,
                ),
            },
        )


# ============================================================
# Mapa de calor único por gestor y estado
# ============================================================

section_title(
    "Mapa de calor de contratos por gestor y estado",
    (
        "Una única matriz compara Vencido, Por Vencer y Vigente. "
        "Cada columna utiliza su propia escala: rojo, amarillo y verde."
    ),
)

estados_mapa = ["Vencido", "Por Vencer", "Vigente"]

if df_recuento_estado.empty:
    st.info("No hay datos para construir el mapa de calor.")
else:
    df_heatmap = (
        df_recuento_estado[
            df_recuento_estado["Estado"].isin(estados_mapa)
        ]
        .pivot_table(
            index="Gestor_Contrato",
            columns="Estado",
            values="Recuento_Contratos",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=estados_mapa, fill_value=0)
    )

    df_heatmap["Total"] = df_heatmap[estados_mapa].sum(axis=1)
    df_heatmap = (
        df_heatmap
        .sort_values(
            ["Vencido", "Por Vencer", "Total"],
            ascending=[False, False, False],
        )
    )

    df_heatmap_plot = df_heatmap[estados_mapa]

    if df_heatmap_plot.empty:
        st.info("No hay datos para construir el mapa de calor.")
    else:
        from matplotlib import colors as mcolors
        from matplotlib import cm

        altura_figura = max(6.2, 0.42 * len(df_heatmap_plot) + 2.6)

        # GridSpec reserva una fila inferior con tres ejes del mismo ancho.
        # Así cada barra queda alineada exactamente con su columna.
        fig = plt.figure(figsize=(10.8, altura_figura))
        grid = fig.add_gridspec(
            nrows=2,
            ncols=3,
            height_ratios=[18, 1],
            hspace=0.28,
            wspace=0.08,
        )
        ax = fig.add_subplot(grid[0, :])

        mapas_color = {
            "Vencido": cm.Reds,
            "Por Vencer": cm.YlOrBr,
            "Vigente": cm.Greens,
        }

        matriz_rgba = np.ones(
            (len(df_heatmap_plot), len(estados_mapa), 4),
            dtype=float,
        )

        normalizadores = {}

        for columna_idx, estado in enumerate(estados_mapa):
            valores = df_heatmap_plot[estado].astype(float).to_numpy()
            maximo = max(float(valores.max()), 1.0)
            normalizador = mcolors.Normalize(vmin=0, vmax=maximo)
            normalizadores[estado] = normalizador

            colores_columna = mapas_color[estado](normalizador(valores))
            colores_columna[valores == 0, 3] = 0.16
            matriz_rgba[:, columna_idx, :] = colores_columna

        ax.imshow(
            matriz_rgba,
            aspect="auto",
            interpolation="nearest",
        )

        ax.set_xticks(np.arange(len(estados_mapa)))
        ax.set_xticklabels(estados_mapa, fontweight="bold")
        ax.set_yticks(np.arange(len(df_heatmap_plot.index)))
        ax.set_yticklabels(df_heatmap_plot.index)

        ax.set_xticks(
            np.arange(-0.5, len(estados_mapa), 1),
            minor=True,
        )
        ax.set_yticks(
            np.arange(-0.5, len(df_heatmap_plot.index), 1),
            minor=True,
        )
        ax.grid(
            which="minor",
            color="white",
            linestyle="-",
            linewidth=1.8,
        )
        ax.tick_params(which="minor", bottom=False, left=False)

        ax.set_title(
            "Concentración contractual por gestor",
            fontsize=14,
            fontweight="bold",
            pad=14,
            loc="left",
        )
        ax.set_xlabel("Estado de vigencia")
        ax.set_ylabel("Gestor de contrato")

        for fila_idx, (_, fila) in enumerate(df_heatmap_plot.iterrows()):
            for columna_idx, estado in enumerate(estados_mapa):
                valor = int(fila[estado])
                maximo = max(float(df_heatmap_plot[estado].max()), 1.0)
                intensidad = valor / maximo

                color_texto = "white" if intensidad >= 0.58 else "#111827"

                ax.text(
                    columna_idx,
                    fila_idx,
                    f"{valor:,}".replace(",", ".") if valor > 0 else "–",
                    ha="center",
                    va="center",
                    fontsize=9,
                    fontweight="bold" if valor > 0 else "normal",
                    color=color_texto if valor > 0 else "#6B7280",
                )

        for columna_idx, estado in enumerate(estados_mapa):
            eje_color = fig.add_subplot(grid[1, columna_idx])
            mapeable = cm.ScalarMappable(
                norm=normalizadores[estado],
                cmap=mapas_color[estado],
            )
            barra = fig.colorbar(
                mapeable,
                cax=eje_color,
                orientation="horizontal",
            )
            barra.ax.tick_params(labelsize=8, pad=2)
            barra.set_label(
                estado,
                fontsize=8,
                fontweight="bold",
                labelpad=2,
            )

        fig.subplots_adjust(
            left=0.25,
            right=0.98,
            top=0.92,
            bottom=0.08,
        )
        st.pyplot(fig, clear_figure=True)

        with st.expander("Ver tabla del mapa de calor", expanded=False):
            tabla_heatmap = df_heatmap.reset_index()[
                ["Gestor_Contrato", "Vencido", "Por Vencer", "Vigente", "Total"]
            ]

            st.dataframe(
                tabla_heatmap,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Gestor_Contrato": st.column_config.TextColumn(
                        "Gestor de contrato"
                    ),
                    "Vencido": st.column_config.NumberColumn(
                        "Vencido", format="%d"
                    ),
                    "Por Vencer": st.column_config.NumberColumn(
                        "Por vencer", format="%d"
                    ),
                    "Vigente": st.column_config.NumberColumn(
                        "Vigente", format="%d"
                    ),
                    "Total": st.column_config.NumberColumn(
                        "Total", format="%d"
                    ),
                },
            )


# ============================================================
# Contratos por gestor y estado
# ============================================================

section_title(
    "Contratos por gestor y estado de vigencia",
    "Desglose de la situación contractual para cada gestor seleccionado.",
)

if df_recuento_estado.empty:
    st.info("No hay contratos para los gestores seleccionados.")
else:
    df_pivot_estado = (
        df_recuento_estado
        .pivot_table(
            index="Gestor_Contrato",
            columns="Estado",
            values="Recuento_Contratos",
            aggfunc="sum",
            fill_value=0,
        )
    )

    columnas_presentes = [
        estado
        for estado in orden_estados
        if estado in df_pivot_estado.columns
    ]

    df_pivot_estado = df_pivot_estado[columnas_presentes]
    df_pivot_estado["Total_Contratos"] = df_pivot_estado.sum(axis=1)

    df_pivot_estado = (
        df_pivot_estado
        .sort_values("Total_Contratos", ascending=True)
    )

    df_plot_estado = df_pivot_estado.drop(columns="Total_Contratos")

    colores_stack = [
        colores_estado.get(columna, "#cbd5e1")
        for columna in df_plot_estado.columns
    ]

    altura_figura = max(6, 0.38 * len(df_plot_estado) + 2)

    fig, ax = plt.subplots(figsize=(12, altura_figura))

    df_plot_estado.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        color=colores_stack,
        edgecolor="white",
        linewidth=0.8,
    )

    ax.set_title(
        "Recuento de contratos por gestor y estado",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )

    ax.set_xlabel("Recuento de contratos")
    ax.set_ylabel("Gestor de contrato")

    ax.legend(
        title="Estado",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
    )

    ax.xaxis.set_major_locator(
        mticker.MaxNLocator(integer=True)
    )

    limpiar_estilo_grafico(ax, eje_grilla="x")

    for contenedor in ax.containers:
        etiquetas = [
            f"{int(valor)}" if valor >= 1 else ""
            for valor in contenedor.datavalues
        ]
        ax.bar_label(
            contenedor,
            labels=etiquetas,
            label_type="center",
            fontsize=8,
            fontweight="bold",
            color="#111827",
        )

    max_total_contratos = df_pivot_estado["Total_Contratos"].max()
    margen_derecho = max(1, max_total_contratos * 0.22)

    ax.set_xlim(
        0,
        max_total_contratos + margen_derecho,
    )

    for indice, total in enumerate(df_pivot_estado["Total_Contratos"]):
        ax.text(
            total + margen_derecho * 0.08,
            indice,
            str(int(total)),
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#111827",
        )

    fig.tight_layout()

    st.pyplot(fig, clear_figure=True)

    with st.expander(
        "Ver tabla de contratos por gestor y estado",
        expanded=True,
    ):
        tabla_estado_gestor = df_pivot_estado.reset_index()

        st.dataframe(
            tabla_estado_gestor,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Gestor_Contrato": st.column_config.TextColumn(
                    "Gestor de contrato"
                ),
                "Total_Contratos": st.column_config.NumberColumn(
                    "Total",
                    format="%d",
                ),
            },
        )


    # ========================================================
    # Detalle interactivo por gestor, estado y rango
    # ========================================================

    section_title(
        "Detalle de contratos por gestor y estado",
        (
            "Selecciona un gestor y un estado para revisar los contratos "
            "que componen el recuento anterior. Si seleccionas Por Vencer, "
            "puedes elegir el rango de vencimiento."
        ),
    )

    df_totales_gestor_detalle = (
        df_contratos_estado_filtrado
        .groupby("Gestor_Contrato", as_index=False)["Contrato"]
        .nunique()
        .rename(columns={"Contrato": "Total_Contratos"})
        .sort_values(
            ["Total_Contratos", "Gestor_Contrato"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )

    gestores_detalle = (
        df_totales_gestor_detalle["Gestor_Contrato"]
        .tolist()
    )

    gestor_mas_contratos = (
        gestores_detalle[0]
        if gestores_detalle
        else None
    )

    indice_gestor_default = (
        gestores_detalle.index(gestor_mas_contratos)
        if gestor_mas_contratos in gestores_detalle
        else 0
    )

    estados_detalle = orden_estados.copy()

    indice_estado_default = (
        estados_detalle.index("Por Vencer")
        if "Por Vencer" in estados_detalle
        else 0
    )

    rangos_vencimiento = [
        "Hasta 3 meses",
        "3 a 6 meses",
        "6 a 12 meses",
        "Superior a 1 año",
    ]

    with st.container(border=True):
        col_selector_gestor, col_selector_estado, col_selector_rango = st.columns(3)

        with col_selector_gestor:
            gestor_detalle_sel = st.selectbox(
                "Gestor de contrato",
                options=gestores_detalle,
                index=indice_gestor_default,
                key="selector_gestor_detalle_estado",
            )

        with col_selector_estado:
            estado_detalle_sel = st.selectbox(
                "Estado de vigencia",
                options=estados_detalle,
                index=indice_estado_default,
                key="selector_estado_detalle_gestor",
            )

        with col_selector_rango:
            if estado_detalle_sel == "Por Vencer":
                rango_vencimiento_sel = st.selectbox(
                    "Rango de vencimiento",
                    options=rangos_vencimiento,
                    index=0,
                    key="selector_rango_vencimiento_detalle",
                )
            else:
                rango_vencimiento_sel = None

                st.selectbox(
                    "Rango de vencimiento",
                    options=["No aplica para este estado"],
                    index=0,
                    disabled=True,
                    key="selector_rango_vencimiento_no_aplica",
                )

    hoy_detalle = pd.Timestamp.today().normalize()

    fecha_limite_3m = hoy_detalle + pd.DateOffset(months=3)
    fecha_limite_6m = hoy_detalle + pd.DateOffset(months=6)
    fecha_limite_12m = hoy_detalle + pd.DateOffset(months=12)

    if estado_detalle_sel == "Por Vencer":
        df_detalle_gestor_estado = (
            df_contratos_estado_filtrado[
                (
                    df_contratos_estado_filtrado["Gestor_Contrato"]
                    == gestor_detalle_sel
                )
                & (
                    df_contratos_estado_filtrado["Fin_período_validez"]
                    .notna()
                )
                & (
                    df_contratos_estado_filtrado["Fin_período_validez"]
                    >= hoy_detalle
                )
            ]
            .copy()
        )

        if rango_vencimiento_sel == "Hasta 3 meses":
            df_detalle_gestor_estado = (
                df_detalle_gestor_estado[
                    df_detalle_gestor_estado["Fin_período_validez"]
                    <= fecha_limite_3m
                ]
                .copy()
            )

            descripcion_rango = (
                f"vencen desde hoy hasta {fecha_limite_3m.date()}"
            )

        elif rango_vencimiento_sel == "3 a 6 meses":
            df_detalle_gestor_estado = (
                df_detalle_gestor_estado[
                    (
                        df_detalle_gestor_estado["Fin_período_validez"]
                        > fecha_limite_3m
                    )
                    & (
                        df_detalle_gestor_estado["Fin_período_validez"]
                        <= fecha_limite_6m
                    )
                ]
                .copy()
            )

            descripcion_rango = (
                f"vencen después de {fecha_limite_3m.date()} "
                f"y hasta {fecha_limite_6m.date()}"
            )

        elif rango_vencimiento_sel == "6 a 12 meses":
            df_detalle_gestor_estado = (
                df_detalle_gestor_estado[
                    (
                        df_detalle_gestor_estado["Fin_período_validez"]
                        > fecha_limite_6m
                    )
                    & (
                        df_detalle_gestor_estado["Fin_período_validez"]
                        <= fecha_limite_12m
                    )
                ]
                .copy()
            )

            descripcion_rango = (
                f"vencen después de {fecha_limite_6m.date()} "
                f"y hasta {fecha_limite_12m.date()}"
            )

        else:
            df_detalle_gestor_estado = (
                df_detalle_gestor_estado[
                    df_detalle_gestor_estado["Fin_período_validez"]
                    > fecha_limite_12m
                ]
                .copy()
            )

            descripcion_rango = (
                f"vencen después de {fecha_limite_12m.date()}"
            )

    else:
        df_detalle_gestor_estado = (
            df_contratos_estado_filtrado[
                (
                    df_contratos_estado_filtrado["Gestor_Contrato"]
                    == gestor_detalle_sel
                )
                & (
                    df_contratos_estado_filtrado["Estado"]
                    == estado_detalle_sel
                )
            ]
            .copy()
        )

        descripcion_rango = "sin filtro adicional de rango"

    columnas_detalle_gestor_estado = [
        columna
        for columna in [
            "Contrato",
            "Contrato_Original",
            "Gestor_Contrato",
            "Documento_compras_ME3N",
            "Documento_Compras_Original_ME3N",
            "Fin_período_validez",
            "Estado",
            "Validacion_Cobertura_ME3N",
            "Fecha_Analisis",
        ]
        if columna in df_detalle_gestor_estado.columns
    ]

    df_detalle_gestor_estado_tabla = (
        df_detalle_gestor_estado[columnas_detalle_gestor_estado]
        .drop_duplicates()
    )

    columnas_orden_detalle = [
        columna
        for columna in [
            "Fin_período_validez",
            "Contrato",
        ]
        if columna in df_detalle_gestor_estado_tabla.columns
    ]

    if columnas_orden_detalle:
        df_detalle_gestor_estado_tabla = (
            df_detalle_gestor_estado_tabla
            .sort_values(
                columnas_orden_detalle,
                ascending=True,
                na_position="last",
            )
        )

    df_detalle_gestor_estado_tabla = (
        df_detalle_gestor_estado_tabla
        .reset_index(drop=True)
    )

    contratos_detalle_seleccion = (
        df_detalle_gestor_estado["Contrato"]
        .nunique()
    )

    total_contratos_gestor_seleccionado = (
        df_contratos_estado_filtrado[
            df_contratos_estado_filtrado["Gestor_Contrato"]
            == gestor_detalle_sel
        ]["Contrato"]
        .nunique()
    )

    participacion_estado_gestor = (
        contratos_detalle_seleccion
        / total_contratos_gestor_seleccionado
        if total_contratos_gestor_seleccionado > 0
        else 0
    )

    col_detalle_kpi_1, col_detalle_kpi_2, col_detalle_kpi_3 = st.columns(3)

    with col_detalle_kpi_1:
        kpi_card(
            "Gestor seleccionado",
            gestor_detalle_sel,
            (
                f"{formato_entero(total_contratos_gestor_seleccionado)} "
                "contratos totales"
            ),
        )

    with col_detalle_kpi_2:
        kpi_card(
            "Estado seleccionado",
            estado_detalle_sel,
            (
                rango_vencimiento_sel
                if estado_detalle_sel == "Por Vencer"
                else "Clasificación de vigencia contractual"
            ),
        )

    with col_detalle_kpi_3:
        kpi_card(
            "Contratos encontrados",
            formato_entero(contratos_detalle_seleccion),
            (
                f"{formato_porcentaje(participacion_estado_gestor)} "
                "del total del gestor"
            ),
        )

    if df_detalle_gestor_estado_tabla.empty:
        if estado_detalle_sel == "Por Vencer":
            st.info(
                (
                    f"No existen contratos para el gestor “{gestor_detalle_sel}” "
                    f"en el rango “{rango_vencimiento_sel}”."
                )
            )
        else:
            st.info(
                (
                    f"No existen contratos para el gestor “{gestor_detalle_sel}” "
                    f"con estado “{estado_detalle_sel}”."
                )
            )

    else:
        if estado_detalle_sel == "Por Vencer":
            st.caption(
                (
                    f"Detalle de {contratos_detalle_seleccion:,.0f} contratos "
                    f"únicos del gestor “{gestor_detalle_sel}” que "
                    f"{descripcion_rango}."
                )
            )
        else:
            st.caption(
                (
                    f"Detalle de {contratos_detalle_seleccion:,.0f} contratos "
                    f"únicos del gestor “{gestor_detalle_sel}” clasificados "
                    f"como “{estado_detalle_sel}”."
                )
            )

        st.dataframe(
            df_detalle_gestor_estado_tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Contrato": st.column_config.TextColumn("Contrato"),
                "Contrato_Original": st.column_config.TextColumn("Contrato original"),
                "Gestor_Contrato": st.column_config.TextColumn("Gestor de contrato"),
                "Documento_compras_ME3N": st.column_config.TextColumn("Documento compras ME3N"),
                "Documento_Compras_Original_ME3N": st.column_config.TextColumn(
                    "Documento original ME3N"
                ),
                "Fin_período_validez": st.column_config.DateColumn(
                    "Fecha fin de validez",
                    format="DD/MM/YYYY",
                ),
                "Estado": st.column_config.TextColumn("Estado"),
                "Validacion_Cobertura_ME3N": st.column_config.TextColumn("Validación ME3N"),
                "Fecha_Analisis": st.column_config.DateColumn(
                    "Fecha de análisis",
                    format="DD/MM/YYYY",
                ),
            },
        )


# ============================================================
# Contratos por vencer por gestor
# ============================================================

section_title(
    "Contratos por vencer por gestor",
    (
        "Foco de riesgo: contratos cuya fecha de fin ocurre dentro "
        "de los próximos tres meses."
    ),
)

df_por_vencer = (
    df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Estado"] == "Por Vencer"
    ]
    .copy()
)

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
    altura_figura = max(5, 0.35 * len(df_top_por_vencer) + 2)

    fig, ax = plt.subplots(figsize=(10, altura_figura))

    bars = ax.barh(
        df_top_por_vencer["Gestor_Contrato"],
        df_top_por_vencer["Contratos_Por_Vencer"],
        color="#F59E0B",
        edgecolor="#B45309",
        linewidth=0.8,
    )

    ax.set_title(
        "Contratos por vencer durante los próximos tres meses",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )

    ax.set_xlabel("Recuento de contratos por vencer")
    ax.set_ylabel("Gestor de contrato")

    ax.xaxis.set_major_locator(
        mticker.MaxNLocator(integer=True)
    )

    limpiar_estilo_grafico(ax, eje_grilla="x")

    max_por_vencer = df_top_por_vencer["Contratos_Por_Vencer"].max()
    margen_por_vencer = max(1, max_por_vencer * 0.22)

    ax.set_xlim(
        0,
        max_por_vencer + margen_por_vencer,
    )

    for bar in bars:
        valor = bar.get_width()
        posicion_y = bar.get_y() + bar.get_height() / 2

        ax.text(
            valor + margen_por_vencer * 0.08,
            posicion_y,
            str(int(valor)),
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#111827",
        )

    fig.tight_layout()

    st.pyplot(fig, clear_figure=True)

    with st.expander(
        "Ver resumen de contratos por vencer",
        expanded=True,
    ):
        st.dataframe(
            df_top_por_vencer
            .sort_values("Contratos_Por_Vencer", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander(
        "Ver detalle individual de contratos por vencer",
        expanded=True,
    ):
        columnas_detalle_vencimiento = [
            columna
            for columna in [
                "Contrato",
                "Gestor_Contrato",
                "Documento_compras_ME3N",
                "Fin_período_validez",
                "Estado",
                "Validacion_Cobertura_ME3N",
            ]
            if columna in df_por_vencer.columns
        ]

        df_detalle_por_vencer = (
            df_por_vencer[columnas_detalle_vencimiento]
            .drop_duplicates()
            .sort_values(
                [
                    "Fin_período_validez",
                    "Gestor_Contrato",
                    "Contrato",
                ]
            )
            .reset_index(drop=True)
        )

        if "Fin_período_validez" in df_detalle_por_vencer.columns:
            df_detalle_por_vencer["Días para vencer"] = (
                df_detalle_por_vencer["Fin_período_validez"]
                - pd.Timestamp.today().normalize()
            ).dt.days.clip(lower=0)

        st.dataframe(
            df_detalle_por_vencer,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Contrato": st.column_config.TextColumn("Contrato"),
                "Gestor_Contrato": st.column_config.TextColumn("Gestor de contrato"),
                "Documento_compras_ME3N": st.column_config.TextColumn("Documento compras ME3N"),
                "Fin_período_validez": st.column_config.DateColumn(
                    "Fecha fin",
                    format="DD/MM/YYYY",
                ),
                "Estado": st.column_config.TextColumn("Estado"),
                "Validacion_Cobertura_ME3N": st.column_config.TextColumn("Validación ME3N"),
                "Días para vencer": st.column_config.ProgressColumn(
                    "Días para vencer",
                    format="%d días",
                    min_value=0,
                    max_value=92,
                ),
            },
        )


# ============================================================
# Validación de cobertura ME3N
# ============================================================

section_title(
    "Validación de cobertura ME3N",
    (
        "ME3N se valida contra la base df_bbdd_x_categoria "
        "usando el identificador de contrato/documento."
    ),
)

col_cobertura_1, col_cobertura_2, col_cobertura_3 = st.columns(3)

with col_cobertura_1:
    kpi_card(
        "Contratos analizados",
        formato_entero(recuento_contratos),
        "Contratos únicos según filtros",
    )

with col_cobertura_2:
    kpi_card(
        "Cobertura ME3N",
        formato_porcentaje(cobertura_me3n),
        f"{formato_entero(contratos_cruzados_me3n)} contratos con coincidencia",
    )

with col_cobertura_3:
    kpi_card(
        "Sin cobertura ME3N",
        formato_porcentaje(sin_cobertura_me3n),
        f"{formato_entero(contratos_sin_me3n)} contratos sin coincidencia",
    )


# ============================================================
# Detalle sin cobertura ME3N
# ============================================================

df_sin_info_me3n = (
    df_contratos_estado_filtrado[
        df_contratos_estado_filtrado["Validacion_Cobertura_ME3N"]
        == "Sin cobertura ME3N"
    ]
    .copy()
)

if df_sin_info_me3n.empty:
    st.success("Todos los contratos filtrados tienen información asociada en ME3N.")

else:
    df_sin_info_me3n["Contrato"] = (
        df_sin_info_me3n["Contrato"]
        .apply(limpiar_id_contrato)
        .astype(str)
    )

    columnas_sin_me3n = [
        columna
        for columna in [
            "Contrato",
            "Contrato_Original",
            "Gestor_Contrato",
            "Documento_compras_ME3N",
            "Documento_Compras_Original_ME3N",
            "Fin_período_validez",
            "Estado",
            "Validacion_Cobertura_ME3N",
            "Fecha_Analisis",
        ]
        if columna in df_sin_info_me3n.columns
    ]

    df_sin_info_me3n_tabla = (
        df_sin_info_me3n[columnas_sin_me3n]
        .drop_duplicates()
        .sort_values(["Gestor_Contrato", "Contrato"])
        .reset_index(drop=True)
    )

    df_sin_info_me3n_resumen = (
        df_sin_info_me3n_tabla
        .groupby("Gestor_Contrato", as_index=False)["Contrato"]
        .nunique()
        .rename(
            columns={
                "Contrato": "Contratos_No_Encontrados_ME3N",
            }
        )
        .sort_values(
            "Contratos_No_Encontrados_ME3N",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    st.warning(
        f"Se identificaron {contratos_sin_me3n:,.0f} contratos "
        "sin coincidencia en ME3N."
    )

    with st.expander(
        "Ver detalle de contratos no encontrados en ME3N",
        expanded=True,
    ):
        st.caption(
            "Estos contratos existen en df_bbdd_x_categoria, "
            "pero no tuvieron coincidencia en ME3N mediante Documento_compras."
        )

        col_sin_1, col_sin_2 = st.columns([0.8, 1.2])

        with col_sin_1:
            st.markdown("##### Resumen por gestor")

            st.dataframe(
                df_sin_info_me3n_resumen,
                use_container_width=True,
                hide_index=True,
            )

        with col_sin_2:
            st.markdown("##### Contratos no encontrados en ME3N")

            st.dataframe(
                df_sin_info_me3n_tabla,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Contrato": st.column_config.TextColumn("Contrato"),
                    "Contrato_Original": st.column_config.TextColumn("Contrato original"),
                    "Gestor_Contrato": st.column_config.TextColumn("Gestor de contrato"),
                    "Documento_compras_ME3N": st.column_config.TextColumn("Documento compras ME3N"),
                    "Documento_Compras_Original_ME3N": st.column_config.TextColumn("Documento original ME3N"),
                    "Fin_período_validez": st.column_config.DateColumn(
                        "Fecha fin",
                        format="DD/MM/YYYY",
                    ),
                    "Estado": st.column_config.TextColumn("Estado"),
                    "Validacion_Cobertura_ME3N": st.column_config.TextColumn("Validación ME3N"),
                    "Fecha_Analisis": st.column_config.DateColumn(
                        "Fecha de análisis",
                        format="DD/MM/YYYY",
                    ),
                },
            )


# ============================================================
# Tablas de apoyo y validaciones
# ============================================================

section_title(
    "Tablas de apoyo",
    (
        "Máximo nivel de detalle para revisar cruces, estados "
        "y validaciones contractuales."
    ),
)

with st.expander(
    "Contratos con estado de vigencia y validaciones",
    expanded=True,
):
    columnas_preview = [
        columna
        for columna in [
            "Contrato",
            "Contrato_Original",
            "Gestor_Contrato",
            "Documento_compras_ME3N",
            "Documento_Compras_Original_ME3N",
            "Fin_período_validez",
            "Estado",
            "Validacion_Cobertura_ME3N",
            "Fecha_Analisis",
        ]
        if columna in df_contratos_estado_filtrado.columns
    ]

    columnas_orden_preview = [
        columna
        for columna in [
            "Gestor_Contrato",
            "Estado",
            "Contrato",
        ]
        if columna in columnas_preview
    ]

    df_preview = (
        df_contratos_estado_filtrado[columnas_preview]
        .drop_duplicates()
    )

    if columnas_orden_preview:
        df_preview = df_preview.sort_values(columnas_orden_preview)

    df_preview = (
        df_preview
        .head(500)
        .reset_index(drop=True)
    )

    st.caption(
        "La tabla muestra como máximo 500 registros correspondientes "
        "a los filtros actualmente seleccionados."
    )

    st.dataframe(
        df_preview,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Contrato": st.column_config.TextColumn("Contrato"),
            "Contrato_Original": st.column_config.TextColumn("Contrato original"),
            "Gestor_Contrato": st.column_config.TextColumn("Gestor de contrato"),
            "Documento_compras_ME3N": st.column_config.TextColumn("Documento compras ME3N"),
            "Documento_Compras_Original_ME3N": st.column_config.TextColumn(
                "Documento original ME3N"
            ),
            "Fin_período_validez": st.column_config.DateColumn(
                "Fecha fin",
                format="DD/MM/YYYY",
            ),
            "Estado": st.column_config.TextColumn("Estado"),
            "Validacion_Cobertura_ME3N": st.column_config.TextColumn("Validación ME3N"),
            "Fecha_Analisis": st.column_config.DateColumn(
                "Fecha de análisis",
                format="DD/MM/YYYY",
            ),
        },
    )

with st.expander(
    "Resumen de validación",
    expanded=True,
):
    total_base = df_contratos_estado["Contrato"].nunique()

    porcentaje_por_vencer = (
        contratos_por_vencer / recuento_contratos
        if recuento_contratos > 0
        else 0
    )

    st.write(
        "- Total contratos únicos en df_bbdd_x_categoria: "
        f"{total_base:,.0f}"
    )

    st.write(
        "- Contratos únicos filtrados: "
        f"{recuento_contratos:,.0f}"
    )

    st.write(
        "- Contratos filtrados cruzados con ME3N: "
        f"{contratos_cruzados_me3n:,.0f}"
    )

    st.write(
        "- Cobertura ME3N sobre contratos filtrados: "
        + formato_porcentaje(cobertura_me3n)
    )

    st.write(
        "- Contratos filtrados sin información en ME3N: "
        f"{contratos_sin_me3n:,.0f}"
    )

    st.write(
        "- Participación sin información ME3N: "
        + formato_porcentaje(sin_cobertura_me3n)
    )

    st.write(
        "- Contratos filtrados por vencer: "
        f"{contratos_por_vencer:,.0f}"
    )

    st.write(
        "- Participación de contratos por vencer: "
        + formato_porcentaje(porcentaje_por_vencer)
    )

    st.write(
        "- Fecha usada como TODAY(): "
        f"{pd.Timestamp.today().normalize().date()}"
    )


# ============================================================
# Índice de Salud contractual y priorización
# Trasladado desde 02_APP_AHORRO
# ============================================================

st.divider()
section_title(
    "Índice de Salud contractual",
    "Compara el saldo pendiente con el tiempo restante para priorizar contratos vigentes.",
)


def convertir_numero_salud(valor):
    """Convierte montos ME3N con formatos locales sin alterar su moneda."""
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip()
    if texto == "" or texto.lower() in {"nan", "none", "null"}:
        return np.nan

    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    return pd.to_numeric(texto, errors="coerce")


def clasificar_indice_salud(row: pd.Series) -> pd.Series:
    """Clasifica con tres estados operativos y estados administrativos separados."""
    fecha_inicio = row.get("Fecha_Inicio")
    fecha_fin = row.get("Fecha_Fin")
    saldo = row.get("Saldo_Restante_%")
    tiempo = row.get("Tiempo_Restante_%")
    indice = row.get("Indice_Salud")
    fecha_hoy = pd.Timestamp.today().normalize()

    if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
        return pd.Series([
            "Sin datos",
            "No evaluable",
            "Faltan fechas de vigencia.",
            "Completar o corregir las fechas contractuales.",
        ])

    if fecha_fin < fecha_hoy:
        return pd.Series([
            "Vencido",
            "Fuera de vigencia",
            "El período contractual ya terminó.",
            "Revisar cierre, renovación o regularización.",
        ])

    if fecha_inicio > fecha_hoy:
        return pd.Series([
            "No iniciado",
            "Pendiente de inicio",
            "El contrato todavía no entra en vigencia.",
            "Confirmar necesidad y fecha de inicio.",
        ])

    if pd.isna(saldo) or pd.isna(tiempo) or pd.isna(indice):
        return pd.Series([
            "Sin datos",
            "No evaluable",
            "No fue posible calcular el indicador con datos válidos.",
            "Revisar montos y duración contractual.",
        ])

    if saldo < 0:
        return pd.Series([
            "Crítico",
            "Saldo negativo",
            "El valor pendiente informado es menor que cero.",
            "Validar consumos, ampliaciones y datos de origen.",
        ])

    if saldo >= 0.98 and tiempo <= 0.10:
        return pd.Series([
            "Crítico",
            "Sin uso relevante",
            "Está próximo a vencer y conserva prácticamente todo el saldo.",
            "Definir continuidad, extensión o cierre.",
        ])

    if indice < 0.60:
        return pd.Series([
            "Crítico",
            "Consumo muy acelerado",
            "El saldo puede ser insuficiente para el plazo restante.",
            "Proyectar consumo y evaluar ampliación o reemplazo.",
        ])

    if indice < 0.85:
        return pd.Series([
            "Revisar",
            "Consumo acelerado",
            "El presupuesto se consume más rápido que el plazo.",
            "Actualizar la proyección de consumo.",
        ])

    if indice <= 1.30:
        return pd.Series([
            "Equilibrado",
            "Ritmo esperado",
            "Saldo y tiempo restante evolucionan de forma alineada.",
            "Mantener seguimiento normal.",
        ])

    if indice <= 2.00:
        return pd.Series([
            "Revisar",
            "Baja ejecución",
            "El consumo es menor que el esperado para el plazo transcurrido.",
            "Revisar demanda, planificación y vigencia.",
        ])

    return pd.Series([
        "Crítico",
        "Ejecución muy baja",
        "Existe mucho saldo en relación con el plazo restante.",
        "Definir plan de uso, extensión o cierre.",
    ])


columnas_indice_requeridas = [
    "Documento_compras",
    "In.período_validez",
    "Fin_período_validez",
    "Valor_previsto",
    "Valor_pendiente_total",
]
columnas_indice_faltantes = [
    columna for columna in columnas_indice_requeridas
    if columna not in _df_me3n.columns
]

if columnas_indice_faltantes:
    st.error(
        "No es posible calcular el Índice de Salud. Faltan columnas ME3N: "
        + ", ".join(columnas_indice_faltantes)
    )
else:
    df_salud_posiciones = _df_me3n.copy()
    df_salud_posiciones["Documento_compras"] = (
        df_salud_posiciones["Documento_compras"]
        .apply(limpiar_id_contrato)
        .astype("string")
    )
    df_salud_posiciones["Fecha_Inicio"] = pd.to_datetime(
        df_salud_posiciones["In.período_validez"],
        errors="coerce",
        dayfirst=True,
    )
    df_salud_posiciones["Fecha_Fin"] = pd.to_datetime(
        df_salud_posiciones["Fin_período_validez"],
        errors="coerce",
        dayfirst=True,
    )
    df_salud_posiciones["Valor_Previsto_num"] = (
        df_salud_posiciones["Valor_previsto"].apply(convertir_numero_salud)
    )
    df_salud_posiciones["Valor_Pendiente_num"] = (
        df_salud_posiciones["Valor_pendiente_total"].apply(convertir_numero_salud)
    )

    agregaciones_salud = {
        "Fecha_Inicio": "min",
        "Fecha_Fin": "max",
        # ME3N repite datos de cabecera por posición; no se deben sumar.
        "Valor_Previsto_num": "first",
        "Valor_Pendiente_num": "first",
    }
    for columna_opcional in [
        "Texto_breve",
        "Proveedor/Centro_suministrador",
        "Moneda",
    ]:
        if columna_opcional in df_salud_posiciones.columns:
            agregaciones_salud[columna_opcional] = "first"

    df_indice_salud = (
        df_salud_posiciones
        .dropna(subset=["Documento_compras"])
        .groupby("Documento_compras", as_index=False)
        .agg(agregaciones_salud)
    )

    hoy_indice = pd.Timestamp.today().normalize()
    df_indice_salud["Duracion_Total_Dias"] = (
        df_indice_salud["Fecha_Fin"] - df_indice_salud["Fecha_Inicio"]
    ).dt.days
    df_indice_salud["Tiempo_Restante_Dias"] = (
        df_indice_salud["Fecha_Fin"] - hoy_indice
    ).dt.days

    df_indice_salud["Tiempo_Restante_%"] = np.where(
        df_indice_salud["Duracion_Total_Dias"] > 0,
        df_indice_salud["Tiempo_Restante_Dias"]
        / df_indice_salud["Duracion_Total_Dias"],
        np.nan,
    )
    df_indice_salud["Saldo_Restante_%"] = np.where(
        df_indice_salud["Valor_Previsto_num"] > 0,
        df_indice_salud["Valor_Pendiente_num"]
        / df_indice_salud["Valor_Previsto_num"],
        np.nan,
    )
    df_indice_salud["Indice_Salud"] = np.where(
        df_indice_salud["Tiempo_Restante_%"] > 0,
        df_indice_salud["Saldo_Restante_%"]
        / df_indice_salud["Tiempo_Restante_%"],
        np.nan,
    )
    df_indice_salud["Saldo_Restante_pct"] = (
        df_indice_salud["Saldo_Restante_%"] * 100
    )
    df_indice_salud["Tiempo_Restante_pct"] = (
        df_indice_salud["Tiempo_Restante_%"] * 100
    )

    df_indice_salud[
        ["Estado_Salud", "Tendencia", "Diagnostico", "Accion_Sugerida"]
    ] = df_indice_salud.apply(clasificar_indice_salud, axis=1)

    with st.expander("Cómo se calcula e interpreta", expanded=False):
        st.markdown(
            """
            **1. Saldo restante** = Valor pendiente / Valor previsto  
            **2. Tiempo restante** = (Fin de vigencia − Hoy) / (Fin de vigencia − Inicio)  
            **3. Índice de Salud** = % saldo restante / % tiempo restante
            """
        )
        st.dataframe(
            pd.DataFrame(
                [
                    ["< 0,60", "Crítico", "Consumo muy acelerado."],
                    ["0,60 a 0,84", "Revisar", "Consumo más rápido que el plazo."],
                    ["0,85 a 1,30", "Equilibrado", "Ritmo razonablemente alineado."],
                    ["1,31 a 2,00", "Revisar", "Ejecución menor que la esperada."],
                    ["> 2,00", "Crítico", "Ejecución muy baja respecto del plazo."],
                ],
                columns=["Índice", "Estado", "Lectura"],
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Saldo negativo o contrato casi sin uso próximo a vencer se clasifican "
            "como Crítico. El índice es una señal de gestión, no una decisión automática."
        )

    if df_indice_salud.empty:
        st.info("No hay documentos de compra disponibles para analizar.")
    else:
        contratos_vigentes_indice = df_indice_salud[
            (df_indice_salud["Fecha_Inicio"] <= hoy_indice)
            & (df_indice_salud["Fecha_Fin"] >= hoy_indice)
        ].copy()

        total_equilibrados = int(
            (contratos_vigentes_indice["Estado_Salud"] == "Equilibrado").sum()
        )
        total_revisar = int(
            (contratos_vigentes_indice["Estado_Salud"] == "Revisar").sum()
        )
        total_criticos = int(
            (contratos_vigentes_indice["Estado_Salud"] == "Crítico").sum()
        )
        total_vencidos_indice = int(
            (df_indice_salud["Estado_Salud"] == "Vencido").sum()
        )

        col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
        with col_i1:
            kpi_card(
                "Contratos vigentes",
                formato_entero(len(contratos_vigentes_indice)),
                "Documentos vigentes en ME3N",
            )
        with col_i2:
            kpi_card(
                "Equilibrados",
                formato_entero(total_equilibrados),
                "Seguimiento normal",
            )
        with col_i3:
            kpi_card(
                "Por revisar",
                formato_entero(total_revisar),
                "Requieren análisis",
            )
        with col_i4:
            kpi_card(
                "Críticos",
                formato_entero(total_criticos),
                "Acción prioritaria",
            )
        with col_i5:
            kpi_card(
                "Vencidos",
                formato_entero(total_vencidos_indice),
                "Fuera de vigencia",
            )

        orden_estados_indice = [
            "Crítico",
            "Revisar",
            "Equilibrado",
            "No iniciado",
            "Vencido",
            "Sin datos",
        ]
        df_distribucion_indice = (
            df_indice_salud
            .groupby("Estado_Salud", as_index=False)
            .size()
            .rename(columns={"size": "Contratos"})
        )
        df_distribucion_indice["Orden"] = (
            df_distribucion_indice["Estado_Salud"]
            .map({estado: i for i, estado in enumerate(orden_estados_indice)})
            .fillna(999)
        )
        df_distribucion_indice = df_distribucion_indice.sort_values(
            "Orden", ascending=False
        )

        col_grafico_indice, col_lectura_indice = st.columns([1.08, 0.92])
        with col_grafico_indice:
            fig, ax = plt.subplots(figsize=(10.8, 5.4))
            barras = ax.barh(
                df_distribucion_indice["Estado_Salud"],
                df_distribucion_indice["Contratos"],
            )
            ax.set_title(
                "Distribución por estado contractual",
                loc="left",
                fontweight="bold",
            )
            ax.set_xlabel("Documentos de compra")
            limpiar_estilo_grafico(ax, eje_grilla="x")
            max_contratos = max(
                float(df_distribucion_indice["Contratos"].max()),
                1,
            )
            margen = max(max_contratos * 0.12, 1)
            ax.set_xlim(0, max_contratos + margen)
            for barra in barras:
                ax.text(
                    barra.get_width() + margen * 0.08,
                    barra.get_y() + barra.get_height() / 2,
                    formato_entero(barra.get_width()),
                    va="center",
                    fontweight="bold",
                )
            fig.tight_layout()
            st.pyplot(fig, clear_figure=True)

        with col_lectura_indice:
            st.markdown("#### Lectura rápida")
            st.dataframe(
                pd.DataFrame(
                    [
                        ["Equilibrado", "Saldo y plazo avanzan a ritmo similar.", "Seguimiento normal."],
                        ["Revisar", "Existe una desviación moderada.", "Validar proyección y necesidad."],
                        ["Crítico", "La desviación puede afectar continuidad o ejecución.", "Definir acción y responsable."],
                        ["No iniciado", "Todavía no entra en vigencia.", "Confirmar planificación."],
                        ["Vencido", "El período terminó.", "Cerrar, renovar o regularizar."],
                        ["Sin datos", "Información insuficiente.", "Corregir origen."],
                    ],
                    columns=["Estado", "Qué significa", "Acción"],
                ),
                use_container_width=True,
                hide_index=True,
                height=300,
            )

        # ========================================================
        # Detalle y priorización contractual
        # ========================================================

        section_title(
            "Detalle y priorización contractual",
            "Filtra y ordena documentos según urgencia de gestión.",
        )

        proveedores_indice_disponibles = (
            sorted(
                df_indice_salud["Proveedor/Centro_suministrador"]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .unique()
                .tolist()
            )
            if "Proveedor/Centro_suministrador" in df_indice_salud.columns
            else []
        )

        col_filtro_1, col_filtro_2 = st.columns([1.0, 1.35])

        with col_filtro_1:
            estados_disponibles_indice = [
                estado for estado in orden_estados_indice
                if estado in df_indice_salud["Estado_Salud"].unique()
            ]
            estados_seleccionados_indice = st.multiselect(
                "Estado",
                options=estados_disponibles_indice,
                default=estados_disponibles_indice,
                key="estados_indice_salud",
            )

        with col_filtro_2:
            proveedor_indice_sel = st.selectbox(
                "Proveedor",
                options=["Todos"] + proveedores_indice_disponibles,
                index=0,
                key="proveedor_indice_salud",
                help="Escribe dentro del selector para buscar un proveedor.",
            )

        col_filtro_3, col_filtro_4 = st.columns([1.45, 0.75])

        with col_filtro_3:
            busqueda_indice = st.text_input(
                "Buscar documento o descripción",
                key="busqueda_indice_salud",
                placeholder="Ej.: 4600012345 o servicio de transporte",
            ).strip().casefold()

        with col_filtro_4:
            solo_vigentes_indice = st.checkbox(
                "Solo vigentes",
                value=True,
                key="solo_vigentes_indice_salud",
            )

        df_detalle_indice = df_indice_salud.copy()
        if estados_seleccionados_indice:
            df_detalle_indice = df_detalle_indice[
                df_detalle_indice["Estado_Salud"].isin(
                    estados_seleccionados_indice
                )
            ]
        if proveedor_indice_sel != "Todos":
            df_detalle_indice = df_detalle_indice[
                df_detalle_indice["Proveedor/Centro_suministrador"]
                .fillna("")
                .astype(str)
                .str.strip()
                == proveedor_indice_sel
            ]

        if solo_vigentes_indice:
            df_detalle_indice = df_detalle_indice[
                (df_detalle_indice["Fecha_Inicio"] <= hoy_indice)
                & (df_detalle_indice["Fecha_Fin"] >= hoy_indice)
            ]

        if busqueda_indice:
            mascara_busqueda = pd.Series(False, index=df_detalle_indice.index)
            for campo in [
                "Documento_compras",
                "Texto_breve",
            ]:
                if campo in df_detalle_indice.columns:
                    mascara_busqueda |= (
                        df_detalle_indice[campo]
                        .fillna("")
                        .astype(str)
                        .str.casefold()
                        .str.contains(busqueda_indice, regex=False)
                    )
            df_detalle_indice = df_detalle_indice[mascara_busqueda]

        prioridad_indice = {
            "Crítico": 0,
            "Revisar": 1,
            "Equilibrado": 2,
            "No iniciado": 3,
            "Vencido": 4,
            "Sin datos": 5,
        }
        df_detalle_indice["Prioridad"] = (
            df_detalle_indice["Estado_Salud"]
            .map(prioridad_indice)
            .fillna(999)
        )
        df_detalle_indice = df_detalle_indice.sort_values(
            ["Prioridad", "Fecha_Fin", "Indice_Salud"],
            ascending=[True, True, True],
        )

        # Columnas visuales: separador de miles y sin decimales.
        df_detalle_indice["Valor_Previsto_fmt"] = (
            df_detalle_indice["Valor_Previsto_num"].apply(
                lambda valor: "" if pd.isna(valor)
                else f"{float(valor):,.0f}".replace(",", ".")
            )
        )
        df_detalle_indice["Valor_Pendiente_fmt"] = (
            df_detalle_indice["Valor_Pendiente_num"].apply(
                lambda valor: "" if pd.isna(valor)
                else f"{float(valor):,.0f}".replace(",", ".")
            )
        )

        columnas_detalle_indice = [
            "Documento_compras",
            "Texto_breve",
            "Proveedor/Centro_suministrador",
            "Fecha_Fin",
            "Valor_Previsto_fmt",
            "Valor_Pendiente_fmt",
            "Tiempo_Restante_Dias",
            "Saldo_Restante_pct",
            "Tiempo_Restante_pct",
            "Indice_Salud",
            "Estado_Salud",
            "Tendencia",
            "Accion_Sugerida",
        ]
        columnas_detalle_indice = [
            columna for columna in columnas_detalle_indice
            if columna in df_detalle_indice.columns
        ]

        tabla_detalle_indice = df_detalle_indice[
            columnas_detalle_indice
        ].rename(
            columns={
                "Documento_compras": "Documento",
                "Texto_breve": "Descripción",
                "Proveedor/Centro_suministrador": "Proveedor",
                "Fecha_Fin": "Fin validez",
                "Valor_Previsto_fmt": "Valor previsto",
                "Valor_Pendiente_fmt": "Valor pendiente",
                "Tiempo_Restante_Dias": "Días restantes",
                "Saldo_Restante_pct": "% saldo",
                "Tiempo_Restante_pct": "% tiempo",
                "Indice_Salud": "Índice",
                "Estado_Salud": "Estado",
                "Tendencia": "Lectura",
                "Accion_Sugerida": "Acción sugerida",
            }
        )

        st.dataframe(
            tabla_detalle_indice,
            use_container_width=True,
            hide_index=True,
            height=560,
            column_config={
                "Fin validez": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Días restantes": st.column_config.NumberColumn(format="%.0f"),
                "% saldo": st.column_config.NumberColumn(format="%.0f%%"),
                "% tiempo": st.column_config.NumberColumn(format="%.0f%%"),
                "Índice": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.caption(
            "Los montos se muestran con separador de miles y sin decimales. "
            "Conservan la moneda original de ME3N."
        )

