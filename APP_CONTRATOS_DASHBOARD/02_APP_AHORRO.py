# 02_APP_AHORRO.py
# Dashboard de ahorro real, planificado, cumplimiento y proceso
# ============================================================

from pathlib import Path
import base64

import pandas as pd
import numpy as np
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
                line-height: 1.25;
            }

            .filter-card {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 18px 20px;
                margin-bottom: 18px;
            }

            .info-card {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 16px 18px;
                min-height: 128px;
                margin-bottom: 12px;
            }

            .info-title {
                font-size: 0.95rem;
                font-weight: 800;
                color: #111827;
                margin-bottom: 6px;
            }

            .info-text {
                font-size: 0.88rem;
                color: #4B5563;
                line-height: 1.38;
            }

            .formula-text {
                margin-top: 8px;
                font-size: 0.84rem;
                font-weight: 700;
                color: #111827;
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 8px 10px;
            }

            [data-testid="stDataFrame"] {
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                overflow: hidden;
                box-shadow: 0 1px 4px rgba(0,0,0,0.035);
            }

            [data-testid="stExpander"] {
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                background: #FFFFFF;
                overflow: hidden;
            }

            [data-testid="stExpander"] summary {
                font-weight: 700;
                color: #111827;
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


def info_card(titulo, texto, formula=None):
    formula_html = f"<div class='formula-text'>{formula}</div>" if formula else ""

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">{titulo}</div>
            <div class="info-text">{texto}</div>
            {formula_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def limpiar_estilo_grafico(ax) -> None:
    """
    Aplica formato visual limpio:
    - Sin grillas internas.
    - Sin bordes superior y derecho.
    - Bordes izquierdo/inferior suaves.
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


def preparar_tabla_visualizacion(df):
    """
    Devuelve una copia del DataFrame con las columnas de fecha visibles
    en formato DD-MM-YYYY, sin modificar los datos usados en cálculos.
    """
    df_visual = df.copy()

    for columna in df_visual.columns:
        if "fecha" in columna.lower():
            serie_fecha = pd.to_datetime(df_visual[columna], errors="coerce")
            if serie_fecha.notna().any():
                df_visual[columna] = serie_fecha.dt.strftime("%d-%m-%Y").fillna("")

    return df_visual


def construir_tabla_profesional(
    df,
    columnas,
    nombres=None,
    orden_por=None,
    ascendente=True
):
    """
    Prepara una tabla de presentación:
    - conserva únicamente columnas útiles;
    - elimina duplicidades visuales;
    - aplica nombres legibles;
    - ordena y reinicia el índice.
    """
    columnas_disponibles = [col for col in columnas if col in df.columns]
    tabla = df[columnas_disponibles].copy()

    if orden_por and orden_por in tabla.columns:
        tabla = tabla.sort_values(orden_por, ascending=ascendente)

    if nombres:
        tabla = tabla.rename(columns=nombres)

    return preparar_tabla_visualizacion(tabla.reset_index(drop=True))


def mostrar_tabla_profesional(
    df,
    columnas,
    nombres=None,
    orden_por=None,
    ascendente=True,
    column_config=None,
    altura=None
):
    """Renderiza una tabla uniforme, compacta y sin índice técnico."""
    tabla = construir_tabla_profesional(
        df=df,
        columnas=columnas,
        nombres=nombres,
        orden_por=orden_por,
        ascendente=ascendente
    )

    dataframe_kwargs = {
        "use_container_width": True,
        "hide_index": True,
        "column_config": column_config or {},
    }

    # Streamlit no acepta ``None`` como altura. Solo enviamos el
    # argumento cuando existe un valor válido. También se admiten
    # las opciones de altura reconocidas por versiones recientes.
    if isinstance(altura, int) and altura > 0:
        dataframe_kwargs["height"] = altura
    elif altura in {"auto", "content", "stretch"}:
        dataframe_kwargs["height"] = altura

    st.dataframe(tabla, **dataframe_kwargs)


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
df_me3n = obtener_dataframe("df_me3n")

if (
    df_plan_ahorro_gestores is None
    or df_catalogo_categorias is None
    or df_registro_contratos is None
    or df_me3n is None
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
            "N_Oferentes",
            "LineaBase_kUSD",
            "Ahorro_Real_kUSD"
        ],
        "df_registro_contratos"
    ),
    validar_columnas(
        df_me3n,
        [
            "Documento_compras",
            "In.período_validez",
            "Fin_período_validez",
            "Valor_previsto",
            "Valor_pendiente_total",
        ],
        "df_me3n"
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
df_real["N_Oferentes_num"] = pd.to_numeric(df_real["N_Oferentes"], errors="coerce")

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

# Preparación ME3N para Índice de Salud. El análisis se consolida por
# Documento_compras para evitar contar varias posiciones como contratos distintos.
df_salud_posiciones = df_me3n.copy()
df_salud_posiciones["Documento_compras"] = limpiar_texto_columna(
    df_salud_posiciones["Documento_compras"]
)
df_salud_posiciones["Fecha_Inicio"] = pd.to_datetime(
    df_salud_posiciones["In.período_validez"], errors="coerce"
)
df_salud_posiciones["Fecha_Fin"] = pd.to_datetime(
    df_salud_posiciones["Fin_período_validez"], errors="coerce"
)
df_salud_posiciones["Valor_Previsto_num"] = pd.to_numeric(
    df_salud_posiciones["Valor_previsto"], errors="coerce"
)
df_salud_posiciones["Valor_Pendiente_num"] = pd.to_numeric(
    df_salud_posiciones["Valor_pendiente_total"], errors="coerce"
)

columnas_agregacion_salud = {
    "Fecha_Inicio": "min",
    "Fecha_Fin": "max",
    # ME3N repite los valores de cabecera en cada posición del documento.
    # Se toma el primer valor para no multiplicar el contrato por su número de posiciones.
    "Valor_Previsto_num": "first",
    "Valor_Pendiente_num": "first",
}
for columna_opcional in ["Texto_breve", "Proveedor/Centro_suministrador", "Moneda"]:
    if columna_opcional in df_salud_posiciones.columns:
        columnas_agregacion_salud[columna_opcional] = "first"

df_salud = (
    df_salud_posiciones
    .dropna(subset=["Documento_compras"])
    .groupby("Documento_compras", as_index=False)
    .agg(columnas_agregacion_salud)
)

hoy = pd.Timestamp.today().normalize()
duracion_total_dias = (df_salud["Fecha_Fin"] - df_salud["Fecha_Inicio"]).dt.days
tiempo_restante_dias = (df_salud["Fecha_Fin"] - hoy).dt.days

df_salud["Tiempo_Restante_%"] = np.where(
    duracion_total_dias > 0,
    tiempo_restante_dias / duracion_total_dias,
    np.nan,
)
df_salud["Saldo_Restante_%"] = np.where(
    df_salud["Valor_Previsto_num"] > 0,
    df_salud["Valor_Pendiente_num"] / df_salud["Valor_Previsto_num"],
    np.nan,
)
df_salud["Indice_Salud"] = np.where(
    df_salud["Tiempo_Restante_%"] > 0,
    df_salud["Saldo_Restante_%"] / df_salud["Tiempo_Restante_%"],
    np.nan,
)

# Se conserva el valor matemático original y se crea una versión acotada
# solo para visualizaciones porcentuales.
df_salud["Tiempo_Restante_Visual_%"] = df_salud["Tiempo_Restante_%"].clip(0, 1)
df_salud["Saldo_Restante_Visual_%"] = df_salud["Saldo_Restante_%"].clip(lower=0)
df_salud["Tiempo_Restante_pct"] = df_salud["Tiempo_Restante_%"] * 100
df_salud["Saldo_Restante_pct"] = df_salud["Saldo_Restante_%"] * 100

condiciones_salud = [
    df_salud["Fecha_Fin"] < hoy,
    df_salud["Indice_Salud"] < 0.8,
    df_salud["Indice_Salud"].between(0.8, 1.2, inclusive="both"),
    df_salud["Indice_Salud"] > 1.2,
]
resultados_salud = ["Vencido", "Crítico", "En seguimiento", "Saludable"]
df_salud["Estado_Salud"] = np.select(
    condiciones_salud, resultados_salud, default="Sin cálculo"
)


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
    kpi_card(
        "% Cumplimiento",
        formato_porcentaje(cumplimiento),
        "Ahorro real dividido por ahorro planificado."
    )

kpi_col4, kpi_col5, kpi_col6 = st.columns(3)

with kpi_col4:
    kpi_card("N° Contratos", f"{n_contratos:,}")

with kpi_col5:
    kpi_card(
        "% Eficiencia",
        formato_porcentaje(eficiencia),
        "Ahorro real sobre la línea base válida."
    )

with kpi_col6:
    kpi_card("Base con línea base", formato_kusd(base), "Suma de LineaBase_kUSD válida")

st.markdown("#### Glosario de indicadores")

col_info1, col_info2 = st.columns(2)

with col_info1:
    info_card(
        "% Cumplimiento",
        "Mide qué porcentaje del ahorro planificado se ha logrado con el ahorro real registrado. "
        "Un valor igual o superior a 100% indica que la meta fue alcanzada o superada.",
        "Fórmula: (Ahorro Real / Ahorro Planificado) × 100"
    )

with col_info2:
    info_card(
        "% Eficiencia",
        "Mide la relación entre el ahorro real y la línea base de los contratos con línea base válida. "
        "Permite entender cuánto ahorro se obtuvo respecto del monto base negociado.",
        "Fórmula: (Ahorro Real con línea base válida / Línea Base válida) × 100"
    )

st.markdown("---")

st.caption(
    "Lectura sugerida: evolución global → desempeño por gestor → salud contractual → "
    "distribución por proceso → cumplimiento y detalle."
)


# ============================================================
# Tabla: Indicadores por gestor
# ============================================================

st.markdown("### Indicadores de gestión por gestor")
st.caption(
    "Ahorro, promedio de oferentes y composición de procesos calculada por cantidad de registros."
)

df_indicadores_gestor = (
    df_real_filtrado
    .groupby("Gestor", as_index=False)
    .agg(
        Ahorro_kUSD=("Ahorro_Real_kUSD_num", "sum"),
        Promedio_Oferentes=("N_Oferentes_num", "mean"),
        Total_Procesos=("Tipo_Proceso", "size"),
        Licitaciones=("Tipo_Proceso", lambda s: (s == "Licitación").sum()),
        Cost_Avoidance=(
            "Tipo_Proceso",
            lambda s: (s == "Negociación - Cost Avoidance").sum(),
        ),
        Asignaciones_Directas=(
            "Tipo_Proceso",
            lambda s: (s == "Asignación Directa").sum(),
        ),
    )
)

for columna_cantidad, columna_pct in [
    ("Licitaciones", "Licitación_%"),
    ("Cost_Avoidance", "Cost_Avoidance_%"),
    ("Asignaciones_Directas", "Asignación_Directa_%"),
]:
    df_indicadores_gestor[columna_pct] = np.where(
        df_indicadores_gestor["Total_Procesos"] > 0,
        df_indicadores_gestor[columna_cantidad]
        / df_indicadores_gestor["Total_Procesos"]
        * 100,
        0,
    )

df_indicadores_gestor = df_indicadores_gestor.sort_values(
    "Ahorro_kUSD", ascending=False
).reset_index(drop=True)

mostrar_tabla_profesional(
    df_indicadores_gestor,
    columnas=[
        "Gestor",
        "Ahorro_kUSD",
        "Promedio_Oferentes",
        "Total_Procesos",
        "Licitación_%",
        "Cost_Avoidance_%",
        "Asignación_Directa_%",
    ],
    nombres={
        "Ahorro_kUSD": "Ahorro",
        "Promedio_Oferentes": "Prom. oferentes",
        "Total_Procesos": "Procesos",
        "Licitación_%": "Licitación",
        "Cost_Avoidance_%": "Cost Avoidance",
        "Asignación_Directa_%": "Asig. directa",
    },
    orden_por="Ahorro_kUSD",
    ascendente=False,
    column_config={
        "Ahorro": st.column_config.NumberColumn(format="%.1f kUSD"),
        "Prom. oferentes": st.column_config.NumberColumn(format="%.1f"),
        "Licitación": st.column_config.NumberColumn(format="%.1f%%"),
        "Cost Avoidance": st.column_config.NumberColumn(format="%.1f%%"),
        "Asig. directa": st.column_config.NumberColumn(format="%.1f%%"),
    },
)

st.markdown("---")


# ============================================================
# Índice de Salud contractual ME3N
# ============================================================

st.markdown("### Índice de Salud contractual")
st.caption(
    "Consolidado por documento de compra. Índice = % saldo restante / % tiempo restante."
)

df_salud_valida = df_salud.dropna(subset=["Indice_Salud"]).copy()

if df_salud_valida.empty:
    st.info("No hay contratos con datos válidos para calcular el Índice de Salud.")
else:
    salud_promedio = df_salud_valida["Indice_Salud"].mean()
    contratos_criticos = int((df_salud_valida["Estado_Salud"] == "Crítico").sum())
    contratos_vencidos = int((df_salud["Estado_Salud"] == "Vencido").sum())
    documentos_con_calculo = len(df_salud_valida)

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        kpi_card("Índice de Salud promedio", f"{salud_promedio:.2f}")
    with col_s2:
        kpi_card("Contratos críticos", f"{contratos_criticos:,}", "Índice menor que 0,80")
    with col_s3:
        kpi_card("Contratos vencidos", f"{contratos_vencidos:,}")
    with col_s4:
        kpi_card("Documentos con cálculo", f"{documentos_con_calculo:,}")

    df_estado_salud = (
        df_salud
        .groupby("Estado_Salud", as_index=False)
        .size()
        .rename(columns={"size": "Contratos"})
        .sort_values("Contratos", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    bars = ax.barh(df_estado_salud["Estado_Salud"], df_estado_salud["Contratos"])
    ax.set_title("Distribución de contratos por estado de salud", loc="left", fontweight="bold")
    ax.set_xlabel("Documentos de compra")
    limpiar_estilo_grafico(ax)
    for bar in bars:
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{int(bar.get_width()):,}",
            va="center",
            fontweight="bold",
        )
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    columnas_salud = [
        "Documento_compras",
        "Texto_breve",
        "Proveedor/Centro_suministrador",
        "Fecha_Inicio",
        "Fecha_Fin",
        "Valor_Previsto_num",
        "Valor_Pendiente_num",
        "Tiempo_Restante_pct",
        "Saldo_Restante_pct",
        "Indice_Salud",
        "Estado_Salud",
    ]

    with st.expander("Ver detalle del Índice de Salud", expanded=True):
        mostrar_tabla_profesional(
            df_salud.sort_values(
                ["Estado_Salud", "Indice_Salud"], ascending=[True, True]
            ),
            columnas=columnas_salud,
            nombres={
                "Documento_compras": "Documento de compra",
                "Texto_breve": "Texto breve",
                "Proveedor/Centro_suministrador": "Proveedor",
                "Fecha_Inicio": "Inicio validez",
                "Fecha_Fin": "Fin validez",
                "Valor_Previsto_num": "Valor previsto",
                "Valor_Pendiente_num": "Valor pendiente",
                "Tiempo_Restante_pct": "% tiempo restante",
                "Saldo_Restante_pct": "% saldo restante",
                "Indice_Salud": "Índice de Salud",
                "Estado_Salud": "Estado",
            },
            column_config={
                "% tiempo restante": st.column_config.NumberColumn(format="%.1f%%"),
                "% saldo restante": st.column_config.NumberColumn(format="%.1f%%"),
                "Índice de Salud": st.column_config.NumberColumn(format="%.2f"),
                "Valor previsto": st.column_config.NumberColumn(format="%.2f"),
                "Valor pendiente": st.column_config.NumberColumn(format="%.2f"),
            },
            altura=520,
        )

    with st.expander("Definición de cálculo", expanded=False):
        st.markdown(
            "**% Tiempo restante** = (Fin validez − Hoy) / "
            "(Fin validez − Inicio validez)  \n\n"
            "**% Saldo restante** = Valor pendiente total / Valor previsto  \n\n"
            "**Índice de Salud** = % Saldo restante / % Tiempo restante"
        )
        st.caption(
            "Los valores monetarios conservan la moneda original de ME3N. "
            "No deben sumarse entre monedas sin aplicar previamente una tabla de conversión."
        )

st.markdown("---")


# ============================================================
# Gráfico: Evolución mensual y acumulada
# ============================================================

st.markdown("### Ahorro real mensual y acumulado")
st.caption(
    "Las barras muestran el ahorro logrado en cada mes y la línea muestra "
    "el avance acumulado durante el período filtrado."
)

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
    .reset_index(drop=True)
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

    ahorro_promedio_mensual = df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"].mean()
    mejor_mes_idx = df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"].idxmax()
    mejor_mes = df_ahorro_acumulado.loc[mejor_mes_idx, "AñoMes"]
    mejor_mes_valor = df_ahorro_acumulado.loc[
        mejor_mes_idx,
        "Ahorro_Real_Mensual_kUSD"
    ]
    ahorro_acumulado_final = df_ahorro_acumulado[
        "Ahorro_Real_Acumulado_kUSD"
    ].iloc[-1]

    resumen_col1, resumen_col2, resumen_col3 = st.columns(3)

    with resumen_col1:
        kpi_card(
            "Promedio mensual",
            formato_kusd(ahorro_promedio_mensual),
            "Promedio del ahorro real mensual en el período."
        )

    with resumen_col2:
        kpi_card(
            "Mejor mes",
            mejor_mes,
            f"{mejor_mes_valor:,.1f} kUSD de ahorro real."
        )

    with resumen_col3:
        kpi_card(
            "Acumulado del período",
            formato_kusd(ahorro_acumulado_final),
            "Ahorro real acumulado al último mes visible."
        )

    fig, ax1 = plt.subplots(figsize=(14, 6.4))
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#FFFFFF")

    posiciones = range(len(df_ahorro_acumulado))

    bars = ax1.bar(
        posiciones,
        df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"],
        width=0.64,
        color="#93C5FD",
        edgecolor="#2563EB",
        linewidth=1.0,
        label="Ahorro mensual",
        zorder=2
    )

    ax1.set_ylabel("Ahorro mensual [kUSD]", fontweight="bold")
    ax1.set_xlabel("Mes", fontweight="bold")
    ax1.set_xticks(list(posiciones))
    ax1.set_xticklabels(
        df_ahorro_acumulado["AñoMes"],
        rotation=45,
        ha="right"
    )
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

    ax2 = ax1.twinx()

    ax2.plot(
        posiciones,
        df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"],
        marker="o",
        markersize=6,
        markerfacecolor="#FFFFFF",
        markeredgewidth=2,
        linewidth=2.8,
        color="#1D4ED8",
        label="Ahorro acumulado",
        zorder=4
    )

    ax2.fill_between(
        posiciones,
        df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"],
        alpha=0.06,
        color="#1D4ED8",
        zorder=1
    )

    ax2.set_ylabel("Ahorro acumulado [kUSD]", fontweight="bold")
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

    max_mensual = max(
        float(df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"].max()),
        0
    )
    max_acumulado = max(
        float(df_ahorro_acumulado["Ahorro_Real_Acumulado_kUSD"].max()),
        0
    )

    margen_mensual = max(max_mensual * 0.25, 1)
    margen_acumulado = max(max_acumulado * 0.20, 1)

    ax1.set_ylim(0, max_mensual + margen_mensual)
    ax2.set_ylim(0, max_acumulado + margen_acumulado)

    # Etiquetas solo en los tres meses con mayor ahorro para evitar saturación.
    top_meses_indices = (
        df_ahorro_acumulado["Ahorro_Real_Mensual_kUSD"]
        .nlargest(min(3, len(df_ahorro_acumulado)))
        .index
    )

    for i in top_meses_indices:
        bar = bars[i]
        valor = df_ahorro_acumulado.loc[i, "Ahorro_Real_Mensual_kUSD"]

        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + margen_mensual * 0.06,
            f"{valor:,.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="#92400E"
        )

    ultimo_indice = len(df_ahorro_acumulado) - 1
    ultimo_valor = df_ahorro_acumulado[
        "Ahorro_Real_Acumulado_kUSD"
    ].iloc[-1]

    ax2.annotate(
        f"Acumulado: {ultimo_valor:,.1f} kUSD",
        xy=(ultimo_indice, ultimo_valor),
        xytext=(-18, 24),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold",
        color="#1D4ED8",
        ha="right",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "#FFFBEB",
            "edgecolor": "#60A5FA"
        },
        arrowprops={
            "arrowstyle": "->",
            "lw": 1.2,
            "color": "#1D4ED8"
        }
    )

    ax1.set_title(
        "Evolución del ahorro real",
        fontsize=15,
        fontweight="bold",
        pad=16,
        loc="left"
    )

    ax1.grid(
        axis="y",
        linestyle="--",
        linewidth=0.7,
        alpha=0.25,
        color="#9CA3AF"
    )

    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color("#D1D5DB")
    ax1.spines["bottom"].set_color("#D1D5DB")

    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_color("#D1D5DB")
    ax2.spines["bottom"].set_visible(False)

    ax1.tick_params(axis="x", colors="#374151")
    ax1.tick_params(axis="y", colors="#374151")
    ax2.tick_params(axis="y", colors="#374151")

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        handles1 + handles2,
        labels1 + labels2,
        loc="upper left",
        frameon=False,
        ncol=2,
        bbox_to_anchor=(0, 1.01)
    )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    with st.expander("Ver detalle mensual y acumulado", expanded=True):
        mostrar_tabla_profesional(
            df_ahorro_acumulado,
            columnas=[
                "Mes_Registro",
                "Ahorro_Real_Mensual_kUSD",
                "Ahorro_Real_Acumulado_kUSD"
            ],
            nombres={
                "Mes_Registro": "Mes",
                "Ahorro_Real_Mensual_kUSD": "Ahorro mensual",
                "Ahorro_Real_Acumulado_kUSD": "Ahorro acumulado"
            },
            orden_por="Mes_Registro",
            ascendente=True,
            column_config={
                "Ahorro mensual": st.column_config.NumberColumn(
                    format="%.1f kUSD"
                ),
                "Ahorro acumulado": st.column_config.NumberColumn(
                    format="%.1f kUSD"
                )
            }
        )

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

    col_donut, col_tabla_donut = st.columns([1.15, 0.85])

    with col_donut:
        fig, ax = plt.subplots(figsize=(7.8, 6.2))

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
                "fontsize": 8,
                "fontweight": "bold",
                "color": "#111827",
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

        leyenda_labels = [
            f"{row['Tipo_Proceso']} | {row['Ahorro_Real_Total_kUSD']:,.1f} kUSD | {row['Participacion_%']:.1f}%"
            for _, row in df_donut.iterrows()
        ]

        ax.legend(
            wedges,
            leyenda_labels,
            title="Tipo de proceso",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=8,
            title_fontsize=9,
            frameon=False,
        )

        plt.tight_layout(pad=1.0)
        st.pyplot(fig, clear_figure=True)

    with col_tabla_donut:
        st.markdown("#### Detalle por proceso")

        mostrar_tabla_profesional(
            df_donut,
            columnas=[
                "Tipo_Proceso",
                "Ahorro_Real_Total_kUSD",
                "Participacion_%"
            ],
            nombres={
                "Tipo_Proceso": "Tipo de proceso",
                "Ahorro_Real_Total_kUSD": "Ahorro real",
                "Participacion_%": "Participación"
            },
            orden_por="Ahorro_Real_Total_kUSD",
            ascendente=False,
            column_config={
                "Ahorro real": st.column_config.NumberColumn(
                    format="%.1f kUSD"
                ),
                "Participación": st.column_config.NumberColumn(
                    format="%.1f%%"
                )
            }
        )

st.markdown("---")


# ============================================================
# Gráfico: Barras proceso
# ============================================================

st.markdown("### Ahorro real por tipo de proceso")
st.caption(
    "Comparación del ahorro real y su participación dentro del total filtrado."
)

df_ahorro_proceso_bar = df_ahorro_proceso.sort_values(
    "Ahorro_Real_Total_kUSD",
    ascending=True
).reset_index(drop=True)

if df_ahorro_proceso_bar.empty:
    st.info("No hay datos para graficar ahorro por tipo de proceso.")
else:
    total_proceso_bar = df_ahorro_proceso_bar["Ahorro_Real_Total_kUSD"].sum()
    df_ahorro_proceso_bar["Participacion_%"] = (
        df_ahorro_proceso_bar["Ahorro_Real_Total_kUSD"] / total_proceso_bar * 100
        if total_proceso_bar > 0 else 0
    )

    fig, ax = plt.subplots(figsize=(13.5, 6.2))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    bars = ax.barh(
        df_ahorro_proceso_bar["Tipo_Proceso"],
        df_ahorro_proceso_bar["Ahorro_Real_Total_kUSD"],
        color="#2563EB",
        edgecolor="#1D4ED8",
        linewidth=0.8,
        height=0.62
    )

    ax.set_title(
        "Ahorro real por tipo de proceso",
        fontsize=15,
        fontweight="bold",
        pad=16,
        loc="left"
    )
    ax.set_xlabel("Ahorro real [kUSD]", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="x", linestyle="--", linewidth=0.7, alpha=0.22, color="#9CA3AF")
    limpiar_estilo_grafico(ax)

    max_valor = max(float(df_ahorro_proceso_bar["Ahorro_Real_Total_kUSD"].max()), 0)
    margen_derecho = max(max_valor * 0.30, 1)
    ax.set_xlim(0, max_valor + margen_derecho)

    for bar, (_, row) in zip(bars, df_ahorro_proceso_bar.iterrows()):
        valor = bar.get_width()
        y_pos = bar.get_y() + bar.get_height() / 2
        ax.text(
            valor + margen_derecho * 0.05,
            y_pos,
            f"{valor:,.1f} kUSD  ·  {row['Participacion_%']:.1f}%",
            va="center", ha="left", fontsize=9, fontweight="bold", color="#111827"
        )

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

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

df_progreso_gestor["Cumplimiento_Total_%"] = (
    df_progreso_gestor["Cumplimiento"] * 100
)

df_progreso_gestor["Cumplimiento_%"] = (
    df_progreso_gestor["Cumplimiento_Total_%"]
    .clip(lower=0, upper=100)
)

df_progreso_gestor["Sobrecumplimiento_%"] = (
    df_progreso_gestor["Cumplimiento_Total_%"] - 100
).clip(lower=0)

df_progreso_gestor["Cumplimiento_Grafico_%"] = (
    df_progreso_gestor["Cumplimiento_%"]
)

df_progreso_gestor = df_progreso_gestor.sort_values(
    "Cumplimiento_Total_%",
    ascending=True
).reset_index(drop=True)


# ============================================================
# Gráfico: Cumplimiento por gestor
# ============================================================

st.markdown("### Cumplimiento por gestor")
st.caption(
    "El tramo principal muestra el avance hasta 100%; el tramo verde muestra el sobrecumplimiento."
)

if df_progreso_gestor.empty:
    st.info("No hay datos para graficar.")
else:
    fig, ax = plt.subplots(figsize=(13.5, max(5.5, len(df_progreso_gestor) * 0.62)))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    ax.barh(
        df_progreso_gestor["Gestor"],
        [100] * len(df_progreso_gestor),
        color="#F3F4F6", edgecolor="#E5E7EB", linewidth=0.8, height=0.62
    )

    colores_base = [
        "#2563EB" if valor >= 100 else "#DC2626"
        for valor in df_progreso_gestor["Cumplimiento_Total_%"]
    ]

    ax.barh(
        df_progreso_gestor["Gestor"],
        df_progreso_gestor["Cumplimiento_%"],
        color=colores_base, edgecolor=colores_base, linewidth=0.8, height=0.62,
        label="Cumplimiento hasta 100%"
    )

    ax.barh(
        df_progreso_gestor["Gestor"],
        df_progreso_gestor["Sobrecumplimiento_%"],
        left=100,
        color="#4ADE80", edgecolor="#22C55E", linewidth=0.8, height=0.62,
        label="Sobrecumplimiento"
    )

    ax.axvline(100, linestyle="--", linewidth=1.2, color="#374151", alpha=0.85)

    max_total = max(float(df_progreso_gestor["Cumplimiento_Total_%"].max()), 100)
    limite_x = min(max(max_total + 28, 135), 260)
    ax.set_xlim(0, limite_x)
    ax.set_xlabel("Cumplimiento [%]", fontweight="bold")
    ax.set_title("Cumplimiento y sobrecumplimiento por gestor", fontsize=15, fontweight="bold", pad=16, loc="left")
    ax.grid(axis="x", linestyle="--", linewidth=0.7, alpha=0.22, color="#9CA3AF")
    limpiar_estilo_grafico(ax)

    for i, row in df_progreso_gestor.iterrows():
        total = row["Cumplimiento_Total_%"]
        posicion = min(max(total, 100) + 3, limite_x - 3)
        ax.text(
            posicion, i,
            f"{total:.1f}%  ·  {row['Ahorro_Real_Total_kUSD']:,.0f}/{row['Ahorro_Planificado_Total_kUSD']:,.0f} kUSD",
            va="center", ha="left", fontsize=9, fontweight="bold", color="#374151"
        )

    from matplotlib.patches import Patch
    ax.legend(
        handles=[
            Patch(facecolor="#2563EB", edgecolor="#2563EB", label="Meta alcanzada"),
            Patch(facecolor="#DC2626", edgecolor="#DC2626", label="Bajo la meta"),
            Patch(facecolor="#4ADE80", edgecolor="#22C55E", label="Sobrecumplimiento"),
            Patch(facecolor="#F3F4F6", edgecolor="#E5E7EB", label="Meta 100%"),
        ],
        loc="lower right", frameon=False, ncol=2
    )

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
    ax.grid(axis="x", linestyle="--", linewidth=0.7, alpha=0.22, color="#9CA3AF")

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

    st.markdown("#### Detalle de registros del Top contratos")

    contratos_top_labels = df_top_contratos_plot["Contrato_Label"].tolist()

    df_detalle_top_contratos = df_top_contratos[
        df_top_contratos["Contrato_Label"].isin(contratos_top_labels)
    ].copy()

    mostrar_tabla_profesional(
        df_detalle_top_contratos,
        columnas=[
            "Fecha_Registro",
            "Contratista",
            "Categoria",
            "Gestor",
            "Tipo_Proceso",
            "LineaBase_kUSD_num",
            "Ahorro_Real_kUSD_num"
        ],
        nombres={
            "Fecha_Registro": "Fecha",
            "Contratista": "Contratista",
            "Categoria": "Categoría",
            "Gestor": "Gestor",
            "Tipo_Proceso": "Tipo de proceso",
            "LineaBase_kUSD_num": "Línea base",
            "Ahorro_Real_kUSD_num": "Ahorro real"
        },
        orden_por="Ahorro_Real_kUSD_num",
        ascendente=False,
        column_config={
            "Línea base": st.column_config.NumberColumn(
                format="%.1f kUSD"
            ),
            "Ahorro real": st.column_config.NumberColumn(
                format="%.1f kUSD"
            )
        }
    )

st.markdown("---")


# ============================================================
# Tablas de apoyo
# ============================================================

st.markdown("### Tablas de apoyo")
st.caption(
    "Vistas depuradas para consulta. Se muestran únicamente columnas de negocio, "
    "sin campos técnicos ni métricas duplicadas."
)

with st.expander("Cumplimiento por gestor", expanded=True):
    tabla_cumplimiento = (
        df_progreso_gestor[
            [
                "Gestor",
                "Ahorro_Planificado_Total_kUSD",
                "Ahorro_Real_Total_kUSD",
                "Cumplimiento_%",
                "Sobrecumplimiento_%",
                "Cumplimiento_Total_%"
            ]
        ]
        .sort_values("Cumplimiento_Total_%", ascending=False)
        .drop(columns=["Cumplimiento_Total_%"])
        .rename(
            columns={
                "Ahorro_Planificado_Total_kUSD": "Planificado",
                "Ahorro_Real_Total_kUSD": "Ahorro real",
                "Cumplimiento_%": "Cumplimiento",
                "Sobrecumplimiento_%": "Sobrecumplimiento"
            }
        )
        .reset_index(drop=True)
    )

    max_sobrecumplimiento = max(
        10.0,
        float(tabla_cumplimiento["Sobrecumplimiento"].max())
        if not tabla_cumplimiento.empty else 10.0
    )

    tabla_cumplimiento_estilizada = (
        tabla_cumplimiento.style
        .format(
            {
                "Planificado": "{:,.1f} kUSD",
                "Ahorro real": "{:,.1f} kUSD",
                "Cumplimiento": "{:.1f}%",
                "Sobrecumplimiento": "{:.1f}%"
            },
            na_rep=""
        )
        .bar(
            subset=["Cumplimiento"],
            color="#2563EB",
            vmin=0,
            vmax=100
        )
        .bar(
            subset=["Sobrecumplimiento"],
            color="#4ADE80",
            vmin=0,
            vmax=max_sobrecumplimiento
        )
    )

    st.dataframe(
        tabla_cumplimiento_estilizada,
        use_container_width=True,
        hide_index=True
    )

with st.expander("Ahorro por tipo de proceso", expanded=True):
    tabla_proceso = df_ahorro_proceso.copy()
    total_proceso = tabla_proceso["Ahorro_Real_Total_kUSD"].sum()
    tabla_proceso["Participacion_%"] = (
        tabla_proceso["Ahorro_Real_Total_kUSD"] / total_proceso * 100
        if total_proceso > 0
        else 0
    )

    tabla_proceso_visual = (
        tabla_proceso[["Tipo_Proceso", "Ahorro_Real_Total_kUSD", "Participacion_%"]]
        .sort_values("Ahorro_Real_Total_kUSD", ascending=False)
        .rename(columns={
            "Tipo_Proceso": "Tipo de proceso",
            "Ahorro_Real_Total_kUSD": "Ahorro real",
            "Participacion_%": "Participación"
        })
        .reset_index(drop=True)
    )

    tabla_proceso_estilizada = (
        tabla_proceso_visual.style
        .format({"Ahorro real": "{:,.1f} kUSD", "Participación": "{:.1f}%"}, na_rep="")
        .bar(subset=["Participación"], color="#60A5FA", vmin=0, vmax=100)
    )

    st.dataframe(
        tabla_proceso_estilizada,
        use_container_width=True,
        hide_index=True
    )

with st.expander("Plan de ahorro por gestor", expanded=True):
    mostrar_tabla_profesional(
        df_plan,
        columnas=[
            "Gestor",
            "Ahorro_Planificado_kUSD_num"
        ],
        nombres={
            "Gestor": "Gestor",
            "Ahorro_Planificado_kUSD_num": "Ahorro planificado"
        },
        orden_por="Ahorro_Planificado_kUSD_num",
        ascendente=False,
        column_config={
            "Ahorro planificado": st.column_config.NumberColumn(
                format="%.1f kUSD"
            )
        }
    )
