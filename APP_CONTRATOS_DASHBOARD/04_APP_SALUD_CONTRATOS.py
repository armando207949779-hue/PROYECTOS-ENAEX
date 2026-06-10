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
    """Formato porcentual."""
    if pd.isna(x):
        x = 0

    return f"{x:.2%}"


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

    df_m3n_contrato = (
        df_m3n
        .groupby("Documento_compras", as_index=False)
        .agg(
            Fin_período_validez=("Fin_período_validez", "max"),
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
# Filtros de encabezado
# ============================================================

section_title(
    "Filtros",
    "Selecciona uno o más gestores para actualizar el análisis contractual.",
)

gestores_disponibles = sorted(
    df_contratos_estado["Gestor_Contrato"]
    .dropna()
    .unique()
    .tolist()
)

with st.container(border=True):
    gestores_sel = st.multiselect(
        "Gestor contrato",
        options=gestores_disponibles,
        default=gestores_disponibles,
    )

if gestores_sel:
    df_contratos_estado_filtrado = (
        df_contratos_estado[
            df_contratos_estado["Gestor_Contrato"].isin(gestores_sel)
        ]
        .copy()
    )
else:
    df_contratos_estado_filtrado = df_contratos_estado.iloc[0:0].copy()


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
        expanded=False,
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
# Indicadores principales
# ============================================================

section_title(
    "Indicadores principales",
    "Resumen ejecutivo de cobertura y vigencia contractual.",
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

        fig, ax = plt.subplots(figsize=(6.3, 5.1))

        wedges, _, _ = ax.pie(
            df_estado_global["Recuento_Contratos"],
            labels=None,
            autopct=lambda porcentaje: f"{porcentaje:.1f}%" if porcentaje >= 3 else "",
            startangle=90,
            counterclock=False,
            pctdistance=0.79,
            colors=colores_grafico,
            wedgeprops={
                "width": 0.38,
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
            fontsize=21,
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
            bbox_to_anchor=(1.00, 0.5),
            fontsize=8.5,
            title_fontsize=9.5,
            frameon=False,
        )

        ax.axis("equal")
        fig.tight_layout()

        st.pyplot(fig, clear_figure=True)

    with col_tabla:
        df_estado_global_tabla = df_estado_global.copy()

        df_estado_global_tabla["Participación"] = (
            df_estado_global_tabla["Participacion_%"]
            .map(lambda valor: f"{valor:.1f}%")
        )

        df_estado_global_tabla = (
            df_estado_global_tabla
            .rename(columns={"Recuento_Contratos": "Contratos"})
            [["Estado", "Contratos", "Participación"]]
        )

        st.markdown("##### Resumen por estado")

        st.dataframe(
            df_estado_global_tabla,
            use_container_width=True,
            hide_index=True,
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

    limpiar_estilo_grafico(ax)

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
        expanded=False,
    ):
        st.dataframe(
            df_pivot_estado.reset_index(),
            use_container_width=True,
            hide_index=True,
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
# Mapa de calor por gestor y estado
# ============================================================

section_title(
    "Mapa de calor de contratos por gestor y estado",
    (
        "Comparación visual para detectar concentraciones de contratos "
        "y estados críticos."
    ),
)

if df_recuento_estado.empty:
    st.info("No hay datos para construir el mapa de calor.")
else:
    df_heatmap_pivot = (
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
        if estado in df_heatmap_pivot.columns
    ]

    df_heatmap_pivot = df_heatmap_pivot[columnas_presentes]
    df_heatmap_pivot["Total"] = df_heatmap_pivot.sum(axis=1)

    df_heatmap_pivot = (
        df_heatmap_pivot
        .sort_values("Total", ascending=False)
    )

    df_heatmap_plot = df_heatmap_pivot.drop(columns="Total")

    if df_heatmap_plot.empty:
        st.info("No hay datos para construir el mapa de calor.")
    else:
        altura_figura = max(6, 0.38 * len(df_heatmap_plot) + 2)

        fig, ax = plt.subplots(figsize=(10.5, altura_figura))

        matriz = df_heatmap_plot.values

        im = ax.imshow(
            matriz,
            aspect="auto",
            cmap="YlGnBu",
        )

        ax.set_xticks(np.arange(len(df_heatmap_plot.columns)))
        ax.set_xticklabels(
            df_heatmap_plot.columns,
            rotation=35,
            ha="right",
        )

        ax.set_yticks(np.arange(len(df_heatmap_plot.index)))
        ax.set_yticklabels(df_heatmap_plot.index)

        ax.set_title(
            "Concentración de contratos por gestor y estado",
            fontsize=14,
            fontweight="bold",
            pad=14,
        )

        ax.set_xlabel("Estado")
        ax.set_ylabel("Gestor de contrato")

        valor_maximo = matriz.max() if matriz.size > 0 else 0

        for fila in range(matriz.shape[0]):
            for columna in range(matriz.shape[1]):
                valor = matriz[fila, columna]

                if valor > 0:
                    color_texto = (
                        "white"
                        if valor_maximo > 0 and valor >= valor_maximo * 0.65
                        else "#111827"
                    )

                    ax.text(
                        columna,
                        fila,
                        str(int(valor)),
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

        with st.expander(
            "Ver tabla del mapa de calor",
            expanded=False,
        ):
            st.dataframe(
                df_heatmap_plot.reset_index(),
                use_container_width=True,
                hide_index=True,
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
        color="#f59e0b",
        edgecolor="#d97706",
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

    limpiar_estilo_grafico(ax)

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
        expanded=False,
    ):
        st.dataframe(
            df_top_por_vencer
            .sort_values("Contratos_Por_Vencer", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander(
        "Ver detalle individual de contratos por vencer",
        expanded=False,
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
    expanded=False,
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
    expanded=False,
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
        f"{cobertura_me3n:.2%}"
    )

    st.write(
        "- Contratos filtrados sin información en ME3N: "
        f"{contratos_sin_me3n:,.0f}"
    )

    st.write(
        "- Participación sin información ME3N: "
        f"{sin_cobertura_me3n:.2%}"
    )

    st.write(
        "- Contratos filtrados por vencer: "
        f"{contratos_por_vencer:,.0f}"
    )

    st.write(
        "- Participación de contratos por vencer: "
        f"{porcentaje_por_vencer:.2%}"
    )

    st.write(
        "- Fecha usada como TODAY(): "
        f"{pd.Timestamp.today().normalize().date()}"
    )
