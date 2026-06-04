# ============================================================
# 02_APP_AHORRO.py
# Dashboard de ahorro real, planificado, cumplimiento y proceso
# ============================================================

from pathlib import Path
import base64

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st


# ============================================================
# Rutas del proyecto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilo visual
# ============================================================

def aplicar_estilo():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2.8rem;
                padding-bottom: 2.5rem;
                max-width: 1550px;
            }

            .kpi-card {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 20px 18px;
                min-height: 118px;
                box-shadow: 0px 2px 8px rgba(0,0,0,0.045);
                display: flex;
                flex-direction: column;
                justify-content: center;
                margin-bottom: 10px;
            }

            .kpi-title {
                font-size: 0.90rem;
                color: #4B5563;
                font-weight: 600;
                margin-bottom: 8px;
                white-space: normal;
                line-height: 1.25;
            }

            .kpi-value {
                font-size: 1.50rem;
                color: #111827;
                font-weight: 800;
                line-height: 1.15;
                white-space: normal;
                word-break: break-word;
            }

            .kpi-subtitle {
                margin-top: 8px;
                font-size: 0.78rem;
                color: #6B7280;
            }

            .filter-card {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 18px 20px;
                margin-bottom: 18px;
            }

            h1, h2, h3 {
                letter-spacing: -0.02em;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


def mostrar_logo_centrado():
    if LOGO_PATH.exists():
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")
        logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 26px;
                margin-bottom: 18px;
                padding-top: 8px;
            ">
                <img
                    src="data:image/svg+xml;base64,{logo_base64}"
                    style="width: 240px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


def kpi_card(titulo, valor, subtitulo=None):
    subtitulo_html = f"<div class='kpi-subtitle'>{subtitulo}</div>" if subtitulo else ""

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            {subtitulo_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def limpiar_estilo_grafico(ax) -> None:
    """
    Aplica formato visual limpio a los gráficos:
    - Sin grillas internas.
    - Sin bordes superior y derecho.
    - Bordes izquierdo/inferior suaves.
    - Ticks en gris oscuro.
    """
    ax.grid(False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")

    ax.tick_params(axis="x", colors="#374151")
    ax.tick_params(axis="y", colors="#374151")


def limpiar_estilo_grafico_doble_eje(ax1, ax2) -> None:
    """
    Aplica estilo limpio para gráficos con doble eje.
    """
    ax1.grid(False)
    ax2.grid(False)

    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color("#D1D5DB")
    ax1.spines["bottom"].set_color("#D1D5DB")

    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_color("#D1D5DB")
    ax2.spines["bottom"].set_color("#D1D5DB")

    ax1.tick_params(axis="x", colors="#374151")
    ax1.tick_params(axis="y", colors="#374151")
    ax2.tick_params(axis="y", colors="#374151")


# ============================================================
# Funciones auxiliares
# ============================================================

def formato_kusd(valor):
    if pd.isna(valor):
        return "--"
    return f"{valor:,.0f} kUSD"


def formato_porcentaje(valor):
    if pd.isna(valor):
        return "--"
    return f"{valor:.2%}".replace(".", ",")


def convertir_kusd(valor):
    if pd.isna(valor):
        return pd.NA

    s = str(valor).strip()

    if s == "" or s.lower() in ["nan", "none"]:
        return pd.NA

    # Formato usado en la base: 81.036,00 -> 81.036
    if "." in s and "," in s:
        s = s.split(",")[0]
        return pd.to_numeric(s, errors="coerce")

    # Formato: 7,27 -> 7.27
    if "," in s:
        s = s.replace(",", ".")
        return pd.to_numeric(s, errors="coerce")

    return pd.to_numeric(s, errors="coerce")


def convertir_planificado(valor):
    if pd.isna(valor):
        return pd.NA

    s = str(valor).strip()

    if s == "" or s.lower() in ["nan", "none"]:
        return pd.NA

    s = s.replace(",", ".")
    return pd.to_numeric(s, errors="coerce")


def limpiar_texto_columna(serie):
    return (
        serie
        .astype(str)
        .str.strip()
        .replace(["", "nan", "NaN", "None"], pd.NA)
    )


def validar_columnas(df, columnas, nombre_df):
    faltantes = [col for col in columnas if col not in df.columns]

    if faltantes:
        st.error(f"El DataFrame `{nombre_df}` no contiene las columnas requeridas: {faltantes}")
        return False

    return True


def obtener_dataframe(nombre_df):
    dataframes = st.session_state.get("dataframes_cargados", {})

    if nombre_df not in dataframes:
        st.error(f"No se encontró `{nombre_df}` en `st.session_state['dataframes_cargados']`.")
        return None

    return dataframes[nombre_df].copy()


# ============================================================
# Inicio app
# ============================================================

aplicar_estilo()
mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>02_AHORRO</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 16px; color: #4B5563;'>
        Seguimiento de ahorro planificado, ahorro real, cumplimiento, eficiencia,
        acumulados y distribución por gestor, contrato y tipo de proceso.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

if "dataframes_cargados" not in st.session_state or not st.session_state["dataframes_cargados"]:
    st.warning("Primero debes cargar las bases desde la pestaña **01_CARGA_ARCHIVOS**.")
    st.stop()


# ============================================================
# Cargar DataFrames desde session_state
# ============================================================

df_plan_ahorro_gestores = obtener_dataframe("df_plan_ahorro_gestores")
df_catalogo_categorias = obtener_dataframe("df_catalogo_categorias")
df_registro_contratos = obtener_dataframe("df_registro_contratos")

if (
    df_plan_ahorro_gestores is None
    or df_catalogo_categorias is None
    or df_registro_contratos is None
):
    st.stop()


# ============================================================
# Validación columnas
# ============================================================

validaciones = [
    validar_columnas(
        df_plan_ahorro_gestores,
        ["Gestor", "Ahorro_Planificado_kUSD"],
        "df_plan_ahorro_gestores"
    ),
    validar_columnas(
        df_catalogo_categorias,
        ["Categoria", "Gestor"],
        "df_catalogo_categorias"
    ),
    validar_columnas(
        df_registro_contratos,
        [
            "Fecha_Registro",
            "Categoria",
            "Contratista",
            "Tipo_Proceso",
            "LineaBase_kUSD",
            "Ahorro_Real_kUSD"
        ],
        "df_registro_contratos"
    ),
]

if not all(validaciones):
    st.stop()


# ============================================================
# Dimensiones
# ============================================================

df_dim_proceso = pd.DataFrame({
    "Tipo_Proceso": [
        "Licitación",
        "Cotización",
        "Asignación Directa",
        "Negociación - Cost Avoidance"
    ]
})

df_plan_ahorro_gestores["Gestor"] = limpiar_texto_columna(df_plan_ahorro_gestores["Gestor"])
df_catalogo_categorias["Gestor"] = limpiar_texto_columna(df_catalogo_categorias["Gestor"])
df_catalogo_categorias["Categoria"] = limpiar_texto_columna(df_catalogo_categorias["Categoria"])

df_dim_gestor = pd.concat(
    [
        df_plan_ahorro_gestores[["Gestor"]],
        df_catalogo_categorias[["Gestor"]]
    ],
    ignore_index=True
)

df_dim_gestor = (
    df_dim_gestor
    .dropna(subset=["Gestor"])
    .drop_duplicates(subset=["Gestor"])
    .sort_values("Gestor")
    .reset_index(drop=True)
)


# ============================================================
# Preparación de tablas
# ============================================================

df_plan = df_plan_ahorro_gestores.copy()

df_plan["Ahorro_Planificado_kUSD_num"] = (
    df_plan["Ahorro_Planificado_kUSD"]
    .apply(convertir_planificado)
)

df_real = df_registro_contratos.copy()

df_real["Fecha_Registro"] = pd.to_datetime(
    df_real["Fecha_Registro"],
    dayfirst=True,
    errors="coerce"
)

df_real["Categoria"] = limpiar_texto_columna(df_real["Categoria"])
df_real["Contratista"] = limpiar_texto_columna(df_real["Contratista"])
df_real["Tipo_Proceso"] = limpiar_texto_columna(df_real["Tipo_Proceso"])

df_real["Ahorro_Real_kUSD_num"] = df_real["Ahorro_Real_kUSD"].apply(convertir_kusd)
df_real["LineaBase_kUSD_num"] = df_real["LineaBase_kUSD"].apply(convertir_kusd)

if "Gestor" not in df_real.columns or df_real["Gestor"].isna().all():
    df_catalogo_aux = (
        df_catalogo_categorias[["Categoria", "Gestor"]]
        .dropna(subset=["Categoria", "Gestor"])
        .drop_duplicates(subset=["Categoria"])
    )

    df_real = df_real.drop(columns=["Gestor"], errors="ignore")

    df_real = df_real.merge(
        df_catalogo_aux,
        on="Categoria",
        how="left"
    )
else:
    df_real["Gestor"] = limpiar_texto_columna(df_real["Gestor"])

df_real["Gestor"] = df_real["Gestor"].fillna("Sin gestor")


# ============================================================
# Filtros en encabezado
# ============================================================

st.markdown("### Filtros")

with st.container():
    st.markdown("<div class='filter-card'>", unsafe_allow_html=True)

    gestores_disponibles = sorted(df_real["Gestor"].dropna().unique().tolist())
    procesos_disponibles = sorted(df_real["Tipo_Proceso"].dropna().unique().tolist())

    fechas_validas = df_real["Fecha_Registro"].dropna()

    if not fechas_validas.empty:
        fecha_min = fechas_validas.min().date()
        fecha_max = fechas_validas.max().date()
    else:
        fecha_min = None
        fecha_max = None

    col_f1, col_f2, col_f3 = st.columns([1.15, 1.15, 0.9])

    with col_f1:
        gestores_filtro = st.multiselect(
            "Gestor",
            options=gestores_disponibles,
            default=gestores_disponibles
        )

    with col_f2:
        procesos_filtro = st.multiselect(
            "Tipo de proceso",
            options=procesos_disponibles,
            default=procesos_disponibles
        )

    with col_f3:
        if fecha_min and fecha_max:
            rango_fechas = st.date_input(
                "Rango Fecha Registro",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max
            )
        else:
            rango_fechas = None

    st.markdown("</div>", unsafe_allow_html=True)


df_real_filtrado = df_real.copy()

if gestores_filtro:
    df_real_filtrado = df_real_filtrado[df_real_filtrado["Gestor"].isin(gestores_filtro)]

if procesos_filtro:
    df_real_filtrado = df_real_filtrado[df_real_filtrado["Tipo_Proceso"].isin(procesos_filtro)]

if rango_fechas and isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas

    df_real_filtrado = df_real_filtrado[
        (df_real_filtrado["Fecha_Registro"].dt.date >= fecha_inicio)
        & (df_real_filtrado["Fecha_Registro"].dt.date <= fecha_fin)
    ]


# ============================================================
# Métricas principales
# ============================================================

ahorro_planificado_total = df_plan["Ahorro_Planificado_kUSD_num"].sum()
ahorro_planificado_total = 0 if pd.isna(ahorro_planificado_total) else ahorro_planificado_total

ahorro_real_total = df_real_filtrado["Ahorro_Real_kUSD_num"].sum()
ahorro_real_total = 0 if pd.isna(ahorro_real_total) else ahorro_real_total

cumplimiento = (
    ahorro_real_total / ahorro_planificado_total
    if ahorro_planificado_total != 0
    else 0
)

n_contratos = len(df_real_filtrado)

filtro_base = (
    df_real_filtrado["LineaBase_kUSD_num"].notna()
    & (df_real_filtrado["LineaBase_kUSD_num"] > 0)
)

base = df_real_filtrado.loc[filtro_base, "LineaBase_kUSD_num"].sum()
ahorro_con_base = df_real_filtrado.loc[filtro_base, "Ahorro_Real_kUSD_num"].sum()

eficiencia = ahorro_con_base / base if base != 0 else 0


# ============================================================
# KPIs
# ============================================================

st.markdown("### Indicadores principales")

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    kpi_card("Ahorro Planificado", formato_kusd(ahorro_planificado_total))

with kpi_col2:
    kpi_card("Ahorro Real", formato_kusd(ahorro_real_total))

with kpi_col3:
    kpi_card("% Cumplimiento", formato_porcentaje(cumplimiento))

kpi_col4, kpi_col5, kpi_col6 = st.columns(3)

with kpi_col4:
    kpi_card("N° Contratos", f"{n_contratos:,}")

with kpi_col5:
    kpi_card("% Eficiencia", formato_porcentaje(eficiencia))

with kpi_col6:
    kpi_card("Base con línea base", formato_kusd(base), "Suma de LineaBase_kUSD válida")

st.markdown("---")


# ============================================================
# Tablas agregadas
# ============================================================

df_plan_gestor = (
    df_plan
    .groupby("Gestor", as_index=False)["Ahorro_Planificado_kUSD_num"]
    .sum()
    .rename(columns={"Ahorro_Planificado_kUSD_num": "Ahorro_Planificado_Total_kUSD"})
)

df_real_gestor = (
    df_real_filtrado
    .groupby("Gestor", as_index=False)["Ahorro_Real_kUSD_num"]
    .sum()
    .rename(columns={"Ahorro_Real_kUSD_num": "Ahorro_Real_Total_kUSD"})
)

df_progreso_gestor = (
    df_dim_gestor
    .merge(df_plan_gestor, on="Gestor", how="left")
    .merge(df_real_gestor, on="Gestor", how="left")
)

df_progreso_gestor[
    ["Ahorro_Planificado_Total_kUSD", "Ahorro_Real_Total_kUSD"]
] = (
    df_progreso_gestor[
        ["Ahorro_Planificado_Total_kUSD", "Ahorro_Real_Total_kUSD"]
    ]
    .fillna(0)
)

df_progreso_gestor["Cumplimiento"] = df_progreso_gestor.apply(
    lambda row: row["Ahorro_Real_Total_kUSD"] / row["Ahorro_Planificado_Total_kUSD"]
    if row["Ahorro_Planificado_Total_kUSD"] > 0 else 0,
    axis=1
)

df_progreso_gestor["Cumplimiento_%"] = df_progreso_gestor["Cumplimiento"] * 100
df_progreso_gestor["Cumplimiento_Grafico_%"] = df_progreso_gestor["Cumplimiento_%"].clip(upper=100)

df_progreso_gestor = df_progreso_gestor.sort_values(
    "Cumplimiento_%",
    ascending=True
).reset_index(drop=True)


# ============================================================
# Gráfico: Cumplimiento por gestor
# ============================================================

st.markdown("### Cumplimiento por gestor")

if df_progreso_gestor.empty:
    st.info("No hay datos para graficar.")
else:
    fig, ax = plt.subplots(figsize=(13, max(5, len(df_progreso_gestor) * 0.55)))

    ax.barh(
        df_progreso_gestor["Gestor"],
        [100] * len(df_progreso_gestor),
        color="#E5E7EB",
        edgecolor="#D1D5DB",
        linewidth=0.8,
        label="Meta 100%"
    )

    ax.barh(
        df_progreso_gestor["Gestor"],
        df_progreso_gestor["Cumplimiento_Grafico_%"],
        color="#2563EB",
        edgecolor="#1D4ED8",
        linewidth=0.8,
        label="Cumplimiento"
    )

    ax.axvline(
        100,
        linestyle="--",
        linewidth=1.1,
        color="#111827",
        alpha=0.8
    )

    max_cumplimiento = df_progreso_gestor["Cumplimiento_%"].max()
    limite_x = max(150, min(max_cumplimiento + 35, 220))

    ax.set_xlim(0, limite_x)
    ax.set_xlabel("Cumplimiento [%]")
    ax.set_title("Cumplimiento por gestor", fontsize=14, fontweight="bold", pad=14)

    limpiar_estilo_grafico(ax)

    for i, row in df_progreso_gestor.iterrows():
        texto = (
            f"{row['Cumplimiento_%']:.1f}% | "
            f"{row['Ahorro_Real_Total_kUSD']:,.0f} / "
            f"{row['Ahorro_Planificado_Total_kUSD']:,.0f} kUSD"
        )

        posicion_texto = min(
            max(row["Cumplimiento_Grafico_%"], 100) + 3,
            limite_x - 5
        )

        ax.text(
            posicion_texto,
            i,
            texto,
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#111827"
        )

    ax.legend(loc="lower right", frameon=False)

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

st.markdown("---")


# ============================================================
# Gráfico: Evolución mensual y acumulada
# ============================================================

st.markdown("### Ahorro real mensual y acumulado")

df_acum = df_real_filtrado.copy()

df_acum["Mes_Registro"] = (
    df_acum["Fecha_Registro"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

df_ahorro_acumulado = (
    df_acum
    .dropna(subset=["Mes_Registro"])
    .groupby("Mes_Registro", as_index=False)["Ahorro_Real_kUSD_num"]
    .sum()
    .rename(columns={"Ahorro_Real_kUSD_num": "Ahorro_Real_Mensual_kUSD"})
    .sort_values("Mes_Registro")
)

if df_ahorro_acumulado.empty:
    st.info("No hay datos mensuales para visualizar.")
else:
    df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"] = (
        df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"].cumsum()
    )

    df_ahorro_acumulado["AñoMes"] = (
        df_ahorro_acumulado["Mes_Registro"].dt.strftime("%Y-%m")
    )

    fig, ax1 = plt.subplots(figsize=(13, 5.8))

    bars = ax1.bar(
        df_ahorro_acumulado["Mes_Registro"],
        df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"],
        width=18,
        alpha=0.35,
        color="#93C5FD",
        edgecolor="#60A5FA",
        linewidth=0.8,
        label="Mensual"
    )

    ax1.set_ylabel("Mensual [kUSD]")

    ax2 = ax1.twinx()

    ax2.plot(
        df_ahorro_acumulado["Mes_Registro"],
        df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"],
        marker="o",
        linewidth=2.5,
        color="#1D4ED8",
        label="Acumulado"
    )

    ax2.set_ylabel("Acumulado [kUSD]")

    ultimo_mes = df_ahorro_acumulado["Mes_Registro"].iloc[-1]
    ultimo_valor = df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"].iloc[-1]

    max_mensual = df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"].max()
    max_acumulado = df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"].max()

    margen_mensual = max_mensual * 0.20 if max_mensual > 0 else 1
    margen_acumulado = max_acumulado * 0.22 if max_acumulado > 0 else 1

    ax1.set_ylim(0, max_mensual + margen_mensual)
    ax2.set_ylim(0, max_acumulado + margen_acumulado)

    ax2.annotate(
        f"{ultimo_valor:,.1f} kUSD",
        xy=(ultimo_mes, ultimo_valor),
        xytext=(-10, 22),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold",
        color="#111827",
        ha="right",
        arrowprops=dict(arrowstyle="->", lw=1.0, color="#111827")
    )

    ax1.set_title("Ahorro real mensual y acumulado", fontsize=14, fontweight="bold", pad=14)
    ax1.set_xlabel("Mes")
    ax1.set_xticks(df_ahorro_acumulado["Mes_Registro"])
    ax1.set_xticklabels(df_ahorro_acumulado["AñoMes"], rotation=45, ha="right")

    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

    limpiar_estilo_grafico_doble_eje(ax1, ax2)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left", frameon=False)

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

st.markdown("---")


# ============================================================
# Gráfico: Top contratos
# ============================================================

st.markdown("### Top contratos por ahorro real")

top_n = st.slider(
    "Cantidad de contratos a mostrar",
    min_value=5,
    max_value=20,
    value=10,
    key="top_contratos_slider"
)

df_top_contratos = df_real_filtrado.copy()

df_top_contratos["Categoria"] = df_top_contratos["Categoria"].fillna("Sin categoría")
df_top_contratos["Contratista"] = df_top_contratos["Contratista"].fillna("Sin contratista")

df_top_contratos["Contrato_Label"] = (
    df_top_contratos["Contratista"].astype(str).str.strip()
    + " | "
    + df_top_contratos["Categoria"].astype(str).str.strip()
)

df_top_contratos_plot = (
    df_top_contratos
    .dropna(subset=["Ahorro_Real_kUSD_num"])
    .sort_values("Ahorro_Real_kUSD_num", ascending=False)
    .head(top_n)
    .sort_values("Ahorro_Real_kUSD_num", ascending=True)
    .reset_index(drop=True)
)

if df_top_contratos_plot.empty:
    st.info("No hay contratos para visualizar.")
else:
    fig, ax = plt.subplots(figsize=(13, max(5, top_n * 0.48)))

    bars = ax.barh(
        df_top_contratos_plot["Contrato_Label"],
        df_top_contratos_plot["Ahorro_Real_kUSD_num"],
        color="#2563EB",
        edgecolor="#1D4ED8",
        linewidth=0.8
    )

    ax.set_title("Top contratos por ahorro real", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Ahorro Real [kUSD]")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

    limpiar_estilo_grafico(ax)

    max_valor = df_top_contratos_plot["Ahorro_Real_kUSD_num"].max()
    margen_derecho = max(max_valor * 0.22, 1)

    ax.set_xlim(0, max_valor + margen_derecho)

    for bar in bars:
        valor = bar.get_width()
        y_pos = bar.get_y() + bar.get_height() / 2

        ax.text(
            valor + margen_derecho * 0.08,
            y_pos,
            f"{valor:,.1f} kUSD",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color="#111827"
        )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

st.markdown("---")


# ============================================================
# Tipo de proceso
# ============================================================

df_proc = df_real_filtrado.copy()

df_dim_proceso["Tipo_Proceso"] = limpiar_texto_columna(df_dim_proceso["Tipo_Proceso"])

df_ahorro_proceso = (
    df_proc
    .groupby("Tipo_Proceso", as_index=False)["Ahorro_Real_kUSD_num"]
    .sum()
    .rename(columns={"Ahorro_Real_kUSD_num": "Ahorro_Real_Total_kUSD"})
)

df_ahorro_proceso = (
    df_dim_proceso
    .merge(df_ahorro_proceso, on="Tipo_Proceso", how="left")
)

df_ahorro_proceso["Ahorro_Real_Total_kUSD"] = (
    df_ahorro_proceso["Ahorro_Real_Total_kUSD"]
    .fillna(0)
)


# ============================================================
# Gráfico: Donut proceso compacto
# ============================================================

st.markdown("### Participación del ahorro por tipo de proceso")

df_donut = df_ahorro_proceso[
    df_ahorro_proceso["Ahorro_Real_Total_kUSD"] > 0
].copy()

if df_donut.empty:
    st.info("No hay datos positivos para el gráfico.")
else:
    total_ahorro = df_donut["Ahorro_Real_Total_kUSD"].sum()

    df_donut["Participacion_%"] = (
        df_donut["Ahorro_Real_Total_kUSD"] / total_ahorro * 100
    )

    df_donut = df_donut.sort_values(
        "Ahorro_Real_Total_kUSD",
        ascending=False
    ).reset_index(drop=True)

    col_donut, col_tabla_donut = st.columns([0.85, 1.15])

    with col_donut:
        fig, ax = plt.subplots(figsize=(4.6, 4.2))

        wedges, texts, autotexts = ax.pie(
            df_donut["Ahorro_Real_Total_kUSD"],
            labels=None,
            autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
            startangle=90,
            pctdistance=0.78,
            wedgeprops={
                "width": 0.36,
                "edgecolor": "white"
            },
            textprops={
                "fontsize": 8
            }
        )

        ax.text(
            0,
            0.05,
            f"{total_ahorro:,.0f}",
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold"
        )

        ax.text(
            0,
            -0.12,
            "kUSD total",
            ha="center",
            va="center",
            fontsize=8
        )

        ax.set_aspect("equal")

        plt.tight_layout(pad=0.5)
        st.pyplot(fig, clear_figure=True)

    with col_tabla_donut:
        st.markdown("#### Detalle por proceso")

        df_donut_resumen = df_donut[
            [
                "Tipo_Proceso",
                "Ahorro_Real_Total_kUSD",
                "Participacion_%"
            ]
        ].copy()

        df_donut_resumen["Ahorro_Real_Total_kUSD"] = (
            df_donut_resumen["Ahorro_Real_Total_kUSD"]
            .map(lambda x: f"{x:,.1f} kUSD")
        )

        df_donut_resumen["Participacion_%"] = (
            df_donut_resumen["Participacion_%"]
            .map(lambda x: f"{x:.1f}%")
        )

        st.dataframe(
            df_donut_resumen,
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")


# ============================================================
# Gráfico: Barras proceso
# ============================================================

st.markdown("### Ahorro real por tipo de proceso")

df_ahorro_proceso_bar = df_ahorro_proceso.sort_values(
    "Ahorro_Real_Total_kUSD",
    ascending=True
).reset_index(drop=True)

if df_ahorro_proceso_bar.empty:
    st.info("No hay datos para graficar ahorro por tipo de proceso.")
else:
    fig, ax = plt.subplots(figsize=(13, 5.5))

    bars = ax.barh(
        df_ahorro_proceso_bar["Tipo_Proceso"],
        df_ahorro_proceso_bar["Ahorro_Real_Total_kUSD"],
        color="#2563EB",
        edgecolor="#1D4ED8",
        linewidth=0.8
    )

    ax.set_title("Ahorro real por tipo de proceso", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Ahorro Real Total [kUSD]")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

    limpiar_estilo_grafico(ax)

    max_valor = df_ahorro_proceso_bar["Ahorro_Real_Total_kUSD"].max()
    margen_derecho = max(max_valor * 0.22, 1)

    ax.set_xlim(0, max_valor + margen_derecho)

    if max_valor > 0:
        for bar in bars:
            valor = bar.get_width()
            y_pos = bar.get_y() + bar.get_height() / 2

            ax.text(
                valor + margen_derecho * 0.08,
                y_pos,
                f"{valor:,.1f} kUSD",
                va="center",
                ha="left",
                fontsize=9,
                fontweight="bold",
                color="#111827"
            )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

st.markdown("---")


# ============================================================
# Tablas de apoyo
# ============================================================

st.markdown("### Tablas de apoyo")

with st.expander("Ver tabla de cumplimiento por gestor", expanded=False):
    st.dataframe(df_progreso_gestor, use_container_width=True)

with st.expander("Ver tabla de ahorro por tipo de proceso", expanded=False):
    st.dataframe(df_ahorro_proceso_bar, use_container_width=True)

with st.expander("Ver registro de contratos filtrado", expanded=False):
    st.dataframe(df_real_filtrado, use_container_width=True)

with st.expander("Ver plan ahorro gestores", expanded=False):
    st.dataframe(df_plan, use_container_width=True)
