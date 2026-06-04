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
# Logo centrado
# ============================================================

def mostrar_logo_centrado():
    if LOGO_PATH.exists():
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")

        logo_base64 = base64.b64encode(
            logo_svg.encode("utf-8")
        ).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 10px;
                margin-bottom: 20px;
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
    """
    Conversión ajustada al formato usado en tus bases:
    - 7,27      -> 7.27
    - 145,00    -> 145
    - 81.036,00 -> 81.036
    """
    if pd.isna(valor):
        return pd.NA

    s = str(valor).strip()

    if s == "" or s.lower() in ["nan", "none"]:
        return pd.NA

    if "." in s and "," in s:
        s = s.split(",")[0]
        return pd.to_numeric(s, errors="coerce")

    if "," in s:
        s = s.replace(",", ".")
        return pd.to_numeric(s, errors="coerce")

    return pd.to_numeric(s, errors="coerce")


def convertir_planificado(valor):
    """
    Para BD_Plan_Ahorro_Gestores:
    - 191,00 -> 191
    - 53,20  -> 53.20
    """
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


def formato_eje_kusd(x, pos=None):
    if abs(x) >= 1_000:
        return f"{x/1_000:.1f}M"
    return f"{x:,.0f}"


def validar_columnas(df, columnas, nombre_df):
    faltantes = [col for col in columnas if col not in df.columns]

    if faltantes:
        st.error(
            f"El DataFrame `{nombre_df}` no contiene las columnas requeridas: {faltantes}"
        )
        return False

    return True


def obtener_dataframe(nombre_df):
    dataframes = st.session_state.get("dataframes_cargados", {})

    if nombre_df not in dataframes:
        st.error(f"No se encontró `{nombre_df}` en `st.session_state['dataframes_cargados']`.")
        return None

    return dataframes[nombre_df].copy()


# ============================================================
# Carga desde session_state
# ============================================================

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>02_AHORRO</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 17px;'>
        Seguimiento de ahorro planificado, ahorro real, cumplimiento, eficiencia,
        acumulados y distribución por gestor, contrato y tipo de proceso.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

if "dataframes_cargados" not in st.session_state or not st.session_state["dataframes_cargados"]:
    st.warning(
        """
        Primero debes cargar las bases desde la pestaña **01_CARGA_ARCHIVOS**.
        """
    )
    st.stop()


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
# Validación mínima de columnas
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
# Preparación de dimensiones
# ============================================================

df_dim_proceso = pd.DataFrame({
    "Tipo_Proceso": [
        "Licitación",
        "Cotización",
        "Asignación Directa",
        "Negociación - Cost Avoidance"
    ]
})

df_plan_ahorro_gestores["Gestor"] = limpiar_texto_columna(
    df_plan_ahorro_gestores["Gestor"]
)

df_catalogo_categorias["Gestor"] = limpiar_texto_columna(
    df_catalogo_categorias["Gestor"]
)

df_catalogo_categorias["Categoria"] = limpiar_texto_columna(
    df_catalogo_categorias["Categoria"]
)

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
# Preparación de tablas base
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

df_real["Ahorro_Real_kUSD_num"] = (
    df_real["Ahorro_Real_kUSD"]
    .apply(convertir_kusd)
)

df_real["LineaBase_kUSD_num"] = (
    df_real["LineaBase_kUSD"]
    .apply(convertir_kusd)
)

# Si Gestor viene vacío en registro de contratos, se trae desde catálogo por Categoría
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
# Filtros
# ============================================================

st.sidebar.header("Filtros")

gestores_disponibles = sorted(df_real["Gestor"].dropna().unique().tolist())
procesos_disponibles = sorted(df_real["Tipo_Proceso"].dropna().unique().tolist())

fechas_validas = df_real["Fecha_Registro"].dropna()

if not fechas_validas.empty:
    fecha_min = fechas_validas.min().date()
    fecha_max = fechas_validas.max().date()
else:
    fecha_min = None
    fecha_max = None

gestores_filtro = st.sidebar.multiselect(
    "Gestor",
    options=gestores_disponibles,
    default=gestores_disponibles
)

procesos_filtro = st.sidebar.multiselect(
    "Tipo de proceso",
    options=procesos_disponibles,
    default=procesos_disponibles
)

if fecha_min and fecha_max:
    rango_fechas = st.sidebar.date_input(
        "Rango Fecha Registro",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )
else:
    rango_fechas = None

df_real_filtrado = df_real.copy()

if gestores_filtro:
    df_real_filtrado = df_real_filtrado[
        df_real_filtrado["Gestor"].isin(gestores_filtro)
    ]

if procesos_filtro:
    df_real_filtrado = df_real_filtrado[
        df_real_filtrado["Tipo_Proceso"].isin(procesos_filtro)
    ]

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

eficiencia = (
    ahorro_con_base / base
    if base != 0
    else 0
)


# ============================================================
# Tarjetas KPI
# ============================================================

st.subheader("1. Indicadores principales")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Ahorro Planificado", formato_kusd(ahorro_planificado_total))

with col2:
    st.metric("Ahorro Real", formato_kusd(ahorro_real_total))

with col3:
    st.metric("% Cumplimiento", formato_porcentaje(cumplimiento))

with col4:
    st.metric("N° Contratos", f"{n_contratos:,}")

with col5:
    st.metric("% Eficiencia", formato_porcentaje(eficiencia))

st.markdown("---")


# ============================================================
# Cálculo por gestor
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
df_progreso_gestor["Cumplimiento_Grafico_%"] = (
    df_progreso_gestor["Cumplimiento_%"]
    .clip(upper=100)
)

df_progreso_gestor = df_progreso_gestor.sort_values(
    "Cumplimiento_%",
    ascending=True
).reset_index(drop=True)


# ============================================================
# Visualizaciones
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Cumplimiento por gestor",
        "Evolución mensual",
        "Top contratos",
        "Tipo de proceso",
        "Tablas"
    ]
)


# ============================================================
# TAB 1: Cumplimiento por gestor
# ============================================================

with tab1:
    st.subheader("2. Cumplimiento de ahorro por gestor")

    if df_progreso_gestor.empty:
        st.info("No hay datos para graficar.")
    else:
        fig, ax = plt.subplots(figsize=(12, max(5, len(df_progreso_gestor) * 0.55)))

        ax.barh(
            df_progreso_gestor["Gestor"],
            [100] * len(df_progreso_gestor),
            color="#E0E0E0",
            label="Meta 100%"
        )

        ax.barh(
            df_progreso_gestor["Gestor"],
            df_progreso_gestor["Cumplimiento_Grafico_%"],
            color="#1976D2",
            label="Cumplimiento"
        )

        ax.axvline(
            100,
            linestyle="--",
            linewidth=1.2,
            color="black",
            label="Meta"
        )

        for i, row in df_progreso_gestor.iterrows():
            texto = (
                f"{row['Cumplimiento_%']:.1f}% | "
                f"{row['Ahorro_Real_Total_kUSD']:,.0f} / "
                f"{row['Ahorro_Planificado_Total_kUSD']:,.0f} kUSD"
            )

            ax.text(
                102,
                i,
                texto,
                va="center",
                fontsize=9
            )

        ax.set_xlabel("Cumplimiento [%]")
        ax.set_ylabel("Gestor")
        ax.set_title("Cumplimiento de Ahorro Real vs Planificado por Gestor")
        ax.set_xlim(0, 150)
        ax.grid(axis="x", alpha=0.25)
        ax.legend(loc="lower right")

        st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla de cumplimiento por gestor", expanded=False):
        st.dataframe(df_progreso_gestor, use_container_width=True)


# ============================================================
# TAB 2: Evolución mensual
# ============================================================

with tab2:
    st.subheader("3. Evolución mensual del ahorro real")

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

        fig, ax1 = plt.subplots(figsize=(12, 6))

        ax1.bar(
            df_ahorro_acumulado["Mes_Registro"],
            df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"],
            width=18,
            alpha=0.30,
            label="Ahorro Real Mensual"
        )

        ax1.set_ylabel("Ahorro mensual [kUSD]")
        ax1.grid(axis="y", alpha=0.25)

        ax2 = ax1.twinx()

        ax2.plot(
            df_ahorro_acumulado["Mes_Registro"],
            df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"],
            marker="o",
            linewidth=2.8,
            label="Ahorro Real Acumulado"
        )

        ax2.set_ylabel("Ahorro acumulado [kUSD]")

        ultimo_mes = df_ahorro_acumulado["Mes_Registro"].iloc[-1]
        ultimo_valor = df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"].iloc[-1]

        ax2.scatter(ultimo_mes, ultimo_valor, s=120, zorder=5)

        ax2.annotate(
            f"Total acumulado: {ultimo_valor:,.1f} kUSD",
            xy=(ultimo_mes, ultimo_valor),
            xytext=(20, 20),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", lw=1.2)
        )

        ax1.set_xlabel("Mes de registro")
        ax1.set_xticks(df_ahorro_acumulado["Mes_Registro"])
        ax1.set_xticklabels(
            df_ahorro_acumulado["AñoMes"],
            rotation=45,
            ha="right"
        )

        ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
        ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

        plt.title(
            "Evolución del Ahorro Real Mensual y Acumulado",
            fontsize=14,
            fontweight="bold"
        )

        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()

        ax1.legend(
            handles1 + handles2,
            labels1 + labels2,
            loc="upper left",
            frameon=True
        )

        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

        with st.expander("Ver tabla mensual", expanded=False):
            st.dataframe(df_ahorro_acumulado, use_container_width=True)


# ============================================================
# TAB 3: Top contratos
# ============================================================

with tab3:
    st.subheader("4. Top contratos por ahorro real")

    top_n = st.slider(
        "Cantidad de contratos a mostrar",
        min_value=5,
        max_value=20,
        value=10
    )

    df_top_contratos = df_real_filtrado.copy()

    df_top_contratos["Categoria"] = (
        df_top_contratos["Categoria"]
        .fillna("Sin categoría")
    )

    df_top_contratos["Contratista"] = (
        df_top_contratos["Contratista"]
        .fillna("Sin contratista")
    )

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
        fig, ax = plt.subplots(figsize=(12, max(5, top_n * 0.45)))

        ax.barh(
            df_top_contratos_plot["Contrato_Label"],
            df_top_contratos_plot["Ahorro_Real_kUSD_num"],
            color="#1976D2"
        )

        ax.set_xlabel("Ahorro Real [kUSD]")
        ax.set_ylabel("Contrato")
        ax.set_title(f"Top {top_n} contratos por ahorro real")
        ax.grid(axis="x", alpha=0.3)

        max_valor = df_top_contratos_plot["Ahorro_Real_kUSD_num"].max()

        for i, valor in enumerate(df_top_contratos_plot["Ahorro_Real_kUSD_num"]):
            ax.text(
                valor + max_valor * 0.01,
                i,
                f"{valor:,.1f}",
                va="center",
                fontsize=9
            )

        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

        with st.expander("Ver tabla Top contratos", expanded=False):
            st.dataframe(
                df_top_contratos_plot[
                    [
                        "Contratista",
                        "Categoria",
                        "Tipo_Proceso",
                        "Ahorro_Real_kUSD",
                        "Ahorro_Real_kUSD_num"
                    ]
                ],
                use_container_width=True
            )


# ============================================================
# TAB 4: Tipo de proceso
# ============================================================

with tab4:
    st.subheader("5. Ahorro por tipo de proceso")

    df_proc = df_real_filtrado.copy()

    df_dim_proceso["Tipo_Proceso"] = limpiar_texto_columna(
        df_dim_proceso["Tipo_Proceso"]
    )

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

    df_ahorro_proceso = df_ahorro_proceso.sort_values(
        "Ahorro_Real_Total_kUSD",
        ascending=True
    ).reset_index(drop=True)

    col_graf1, col_graf2 = st.columns([1.2, 1])

    with col_graf1:
        fig, ax = plt.subplots(figsize=(9, 5))

        ax.barh(
            df_ahorro_proceso["Tipo_Proceso"],
            df_ahorro_proceso["Ahorro_Real_Total_kUSD"],
            color="#1976D2"
        )

        ax.set_xlabel("Ahorro Real Total [kUSD]")
        ax.set_ylabel("Tipo de Proceso")
        ax.set_title("Ahorro Real Total por Tipo de Proceso")
        ax.grid(axis="x", alpha=0.25)
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

        max_valor = df_ahorro_proceso["Ahorro_Real_Total_kUSD"].max()

        if max_valor > 0:
            for i, valor in enumerate(df_ahorro_proceso["Ahorro_Real_Total_kUSD"]):
                ax.text(
                    valor + max_valor * 0.02,
                    i,
                    f"{valor:,.1f} kUSD",
                    va="center",
                    fontsize=9
                )

        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

    with col_graf2:
        df_donut = df_ahorro_proceso[
            df_ahorro_proceso["Ahorro_Real_Total_kUSD"] > 0
        ].copy()

        if df_donut.empty:
            st.info("No hay datos positivos para el gráfico donut.")
        else:
            total_ahorro = df_donut["Ahorro_Real_Total_kUSD"].sum()

            fig, ax = plt.subplots(figsize=(6, 6))

            wedges, texts, autotexts = ax.pie(
                df_donut["Ahorro_Real_Total_kUSD"],
                labels=df_donut["Tipo_Proceso"],
                autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={
                    "width": 0.38,
                    "edgecolor": "white"
                }
            )

            ax.text(
                0,
                0.05,
                f"{total_ahorro:,.0f}",
                ha="center",
                va="center",
                fontsize=18,
                fontweight="bold"
            )

            ax.text(
                0,
                -0.12,
                "kUSD total",
                ha="center",
                va="center",
                fontsize=10
            )

            ax.set_title("Participación del Ahorro Real")
            plt.tight_layout()
            st.pyplot(fig, clear_figure=True)

    with st.expander("Ver tabla por tipo de proceso", expanded=False):
        st.dataframe(df_ahorro_proceso, use_container_width=True)


# ============================================================
# TAB 5: Tablas
# ============================================================

with tab5:
    st.subheader("6. Tablas de apoyo")

    with st.expander("DimProceso", expanded=False):
        st.dataframe(df_dim_proceso, use_container_width=True)

    with st.expander("DimGestor", expanded=False):
        st.dataframe(df_dim_gestor, use_container_width=True)

    with st.expander("Registro contratos filtrado", expanded=False):
        st.dataframe(df_real_filtrado, use_container_width=True)

    with st.expander("Plan ahorro gestores", expanded=False):
        st.dataframe(df_plan, use_container_width=True)
