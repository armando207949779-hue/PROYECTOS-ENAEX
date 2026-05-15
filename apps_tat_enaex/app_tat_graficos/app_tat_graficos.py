# app.py

import io

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Performance TAT",
    page_icon="📊",
    layout="wide"
)

COLOR_CUMPLE = "#5B5B5B"
COLOR_NO_CUMPLE = "#D94555"
COLOR_OBJETIVO = "#006B4F"

OBJETIVO_CUMPLIMIENTO = 65

ESTADOS_GRAFICO = ["Cumple", "No cumple"]

MESES_NOMBRE = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre"
}


# =========================================================
# FUNCIONES BASE
# =========================================================

@st.cache_data(show_spinner="Leyendo archivo parquet...")
def cargar_parquet(archivo_bytes: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(archivo_bytes)
    return pd.read_parquet(buffer)


def normalizar_performance(valor):
    if pd.isna(valor):
        return "Sin información"

    texto = (
        str(valor)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

    if texto in ["cumple", "true", "1", "si", "sí", "yes"]:
        return "Cumple"

    if texto in ["no cumple", "nocumple", "false", "0", "no"]:
        return "No cumple"

    return "Sin información"


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    col_fecha = "fecha_recepcion_final"
    col_performance = "performance_tat_total"

    faltantes = []

    if col_fecha not in df.columns:
        faltantes.append(col_fecha)

    if col_performance not in df.columns:
        faltantes.append(col_performance)

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    df[col_fecha] = pd.to_datetime(
        df[col_fecha],
        errors="coerce"
    )

    df["performance_tat_estado"] = df[col_performance].apply(
        normalizar_performance
    )

    df["anio"] = df[col_fecha].dt.year
    df["mes_num"] = df[col_fecha].dt.month

    df["periodo_fecha"] = (
        df[col_fecha]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)

    df["periodo_label"] = np.where(
        df["anio"].notna() & df["mes_nombre"].notna(),
        df["mes_nombre"].astype(str)
        + " "
        + df["anio"].astype("Int64").astype(str),
        pd.NA
    )

    return df


def detectar_columna_centro(df: pd.DataFrame):
    posibles = [
        "Centro - ME5A",
        "Centro",
        "Centro - NME80FN"
    ]

    for col in posibles:
        if col in df.columns:
            return col

    return None


def extraer_rango_fechas(rango_fechas):
    if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
    else:
        fecha_inicio = rango_fechas
        fecha_fin = rango_fechas

    if fecha_inicio is None or fecha_fin is None:
        return None, None

    fecha_inicio = pd.Timestamp(fecha_inicio)
    fecha_fin = (
        pd.Timestamp(fecha_fin)
        + pd.Timedelta(days=1)
        - pd.Timedelta(microseconds=1)
    )

    return fecha_inicio, fecha_fin


# =========================================================
# RESUMEN MENSUAL TAT
# =========================================================

def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df[
        df["fecha_recepcion_final"].notna()
        & df["performance_tat_estado"].isin(ESTADOS_GRAFICO)
    ].copy()

    if df.empty:
        return pd.DataFrame()

    resumen = (
        df
        .groupby(
            [
                "periodo_fecha",
                "periodo_label",
                "anio",
                "mes_num",
                "mes_nombre",
                "performance_tat_estado"
            ],
            dropna=False
        )
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=[
            "periodo_fecha",
            "periodo_label",
            "anio",
            "mes_num",
            "mes_nombre"
        ],
        columns="performance_tat_estado",
        values="cantidad",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    for estado in ESTADOS_GRAFICO:
        if estado not in tabla.columns:
            tabla[estado] = 0

    tabla["Total"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["Cumple"] / tabla["Total"] * 100,
        0
    )

    tabla["% No cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["No cumple"] / tabla["Total"] * 100,
        0
    )

    tabla = tabla.sort_values("periodo_fecha").reset_index(drop=True)

    return tabla


def completar_meses(
    tabla: pd.DataFrame,
    fecha_inicio,
    fecha_fin
) -> pd.DataFrame:
    if fecha_inicio is None or fecha_fin is None:
        return tabla

    fecha_inicio_mes = pd.Timestamp(fecha_inicio).normalize()
    fecha_fin_mes = pd.Timestamp(fecha_fin).normalize()

    periodos = pd.period_range(
        start=fecha_inicio_mes.to_period("M"),
        end=fecha_fin_mes.to_period("M"),
        freq="M"
    )

    base = pd.DataFrame({
        "periodo_fecha": periodos.to_timestamp()
    })

    base["anio"] = base["periodo_fecha"].dt.year
    base["mes_num"] = base["periodo_fecha"].dt.month
    base["mes_nombre"] = base["mes_num"].map(MESES_NOMBRE)
    base["periodo_label"] = (
        base["mes_nombre"].astype(str)
        + " "
        + base["anio"].astype(str)
    )

    if tabla.empty:
        base["Cumple"] = 0
        base["No cumple"] = 0
        base["Total"] = 0
        base["% Cumple"] = 0
        base["% No cumple"] = 0

        return base.sort_values("periodo_fecha").reset_index(drop=True)

    salida = base.merge(
        tabla,
        on=[
            "periodo_fecha",
            "periodo_label",
            "anio",
            "mes_num",
            "mes_nombre"
        ],
        how="left"
    )

    for col in ["Cumple", "No cumple", "Total", "% Cumple", "% No cumple"]:
        if col in salida.columns:
            salida[col] = salida[col].fillna(0)

    salida = salida.sort_values("periodo_fecha").reset_index(drop=True)

    return salida


def crear_data_plot(
    tabla: pd.DataFrame,
) -> pd.DataFrame:
    if tabla.empty:
        return pd.DataFrame()

    df_plot = tabla.copy()

    df_plot["Cumple"] = pd.to_numeric(
        df_plot["Cumple"],
        errors="coerce"
    ).fillna(0)

    df_plot["No cumple"] = pd.to_numeric(
        df_plot["No cumple"],
        errors="coerce"
    ).fillna(0)

    df_plot["Total"] = df_plot["Cumple"] + df_plot["No cumple"]

    df_plot["pct_cumple"] = np.where(
        df_plot["Total"] > 0,
        df_plot["Cumple"] / df_plot["Total"] * 100,
        0
    )

    df_plot["pct_no_cumple"] = np.where(
        df_plot["Total"] > 0,
        df_plot["No cumple"] / df_plot["Total"] * 100,
        0
    )

    df_plot["cumple_objetivo"] = np.where(
        df_plot["pct_cumple"] >= OBJETIVO_CUMPLIMIENTO,
        "Superó 65%",
        "No superó 65%"
    )

    df_plot["texto_pct"] = df_plot["pct_cumple"].map(
        lambda x: f"{x:.1f}%"
    )

    df_plot = df_plot.sort_values("periodo_fecha").reset_index(drop=True)

    return df_plot


def grafico_performance_tat(df_plot: pd.DataFrame):
    if df_plot.empty:
        st.warning("No hay datos evaluables para graficar.")
        return

    if df_plot["Total"].sum() == 0:
        st.warning("No hay registros Cumple / No cumple para graficar.")
        return

    orden_periodos = (
        df_plot[["periodo_label", "periodo_fecha"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")["periodo_label"]
        .tolist()
    )

    barras = (
        alt.Chart(df_plot)
        .mark_bar(
            size=34,
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5
        )
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos,
                title="Mes recepción",
                axis=alt.Axis(
                    labelAngle=-35,
                    labelOverlap=False,
                    labelFontSize=11,
                    titleFontSize=12
                )
            ),
            y=alt.Y(
                "pct_cumple:Q",
                title="% Cumplimiento",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(
                    labelFontSize=11,
                    titleFontSize=12,
                    format=".0f"
                )
            ),
            color=alt.Color(
                "cumple_objetivo:N",
                scale=alt.Scale(
                    domain=["Superó 65%", "No superó 65%"],
                    range=[COLOR_CUMPLE, COLOR_NO_CUMPLE]
                ),
                legend=alt.Legend(
                    title="Resultado objetivo",
                    orient="bottom",
                    labelFontSize=12
                )
            ),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("pct_cumple:Q", title="% Cumple", format=".2f"),
                alt.Tooltip("pct_no_cumple:Q", title="% No cumple", format=".2f"),
                alt.Tooltip("Cumple:Q", title="Cumple", format=",.0f"),
                alt.Tooltip("No cumple:Q", title="No cumple", format=",.0f"),
                alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f")
            ]
        )
    )

    etiquetas = (
        alt.Chart(df_plot)
        .mark_text(
            dy=-8,
            fontSize=11,
            fontWeight="bold",
            color="#222222"
        )
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos
            ),
            y=alt.Y("pct_cumple:Q"),
            text="texto_pct:N"
        )
    )

    linea_objetivo = (
        alt.Chart(pd.DataFrame({"objetivo": [OBJETIVO_CUMPLIMIENTO]}))
        .mark_rule(
            strokeDash=[10, 5],
            color=COLOR_OBJETIVO,
            size=4
        )
        .encode(
            y="objetivo:Q"
        )
    )

    texto_objetivo = (
        alt.Chart(pd.DataFrame({
            "periodo_label": [orden_periodos[0]],
            "objetivo": [OBJETIVO_CUMPLIMIENTO],
            "texto": [f"Objetivo {OBJETIVO_CUMPLIMIENTO}%"]
        }))
        .mark_text(
            align="left",
            baseline="bottom",
            dx=8,
            dy=-8,
            color=COLOR_OBJETIVO,
            fontWeight="bold",
            fontSize=14
        )
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos
            ),
            y="objetivo:Q",
            text="texto:N"
        )
    )

    chart = barras + etiquetas + linea_objetivo + texto_objetivo

    chart = (
        chart
        .properties(
            title=alt.TitleParams(
                text="% Cumplimiento TAT mensual",
                subtitle=(
                    "Se muestra solo el porcentaje de cumplimiento. "
                    "El color indica si el mes superó o no el objetivo."
                ),
                fontSize=18,
                subtitleFontSize=12,
                fontWeight="bold",
                anchor="start"
            ),
            height=430
        )
        .configure_axis(
            grid=True,
            gridOpacity=0.20
        )
        .configure_view(
            strokeWidth=0
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


# =========================================================
# TARJETAS POR ETAPA
# =========================================================

def detectar_columnas_etapas(df: pd.DataFrame):
    etapas = [
        {
            "titulo": "Lib Solped",
            "col_perf": "performance_liberacion_solped",
            "col_dias": "dias_liberacion_solped",
            "regla": "Nacional e Internacional < 2 días"
        },
        {
            "titulo": "Comprador",
            "col_perf": "performance_comprador",
            "col_dias": "dias_comprador",
            "regla": "Nacional e Internacional < 11 días"
        },
        {
            "titulo": "Proveedor",
            "col_perf": "performance_proveedor",
            "col_dias": "dias_proveedor",
            "regla": "Nacional < 20 días | Internacional < 60 días"
        },
        {
            "titulo": "Logística",
            "col_perf": "performance_logistica",
            "col_dias": "dias_logistica",
            "regla": "Nacional e Internacional < 10 días"
        }
    ]

    return etapas


def normalizar_estado_etapa(valor):
    if pd.isna(valor):
        return "Sin información"

    texto = (
        str(valor)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

    if texto == "cumple":
        return "Cumple"

    if texto == "no cumple":
        return "No cumple"

    if texto in ["no aplica", "no aplica al analisis"]:
        return "No aplica"

    if texto in ["sin datos", "en proceso"]:
        return "Sin datos"

    return "Sin información"


def calcular_resumen_etapa(
    df_base: pd.DataFrame,
    col_perf: str,
    col_dias: str
):
    temp = df_base.copy()

    temp["estado_etapa"] = temp[col_perf].apply(normalizar_estado_etapa)

    temp_eval = temp[
        temp["estado_etapa"].isin(["Cumple", "No cumple"])
    ].copy()

    conteo = (
        temp_eval["estado_etapa"]
        .value_counts()
        .reindex(["Cumple", "No cumple"], fill_value=0)
    )

    total = conteo.sum()

    porcentaje = conteo / total * 100 if total > 0 else conteo * 0

    dias = pd.to_numeric(
        temp[col_dias],
        errors="coerce"
    ).dropna()

    dias = dias[dias > 0]

    promedio = dias.mean() if not dias.empty else 0

    return conteo, porcentaje, promedio, total, len(dias)


def crear_tabla_diagnostico_etapas(df_base: pd.DataFrame) -> pd.DataFrame:
    etapas = detectar_columnas_etapas(df_base)

    data = []

    for etapa in etapas:
        col_perf = etapa["col_perf"]
        col_dias = etapa["col_dias"]

        if col_perf not in df_base.columns or col_dias not in df_base.columns:
            data.append({
                "Etapa": etapa["titulo"],
                "Estado": "Faltan columnas",
                "Columna performance": col_perf,
                "Columna días": col_dias,
            })
            continue

        conteo, porcentaje, promedio, total, n_promedio = calcular_resumen_etapa(
            df_base=df_base,
            col_perf=col_perf,
            col_dias=col_dias
        )

        data.append({
            "Etapa": etapa["titulo"],
            "Regla": etapa["regla"],
            "Cumple": int(conteo["Cumple"]),
            "No cumple": int(conteo["No cumple"]),
            "Total evaluable dona": int(total),
            "% Cumple": round(float(porcentaje["Cumple"]), 2),
            "% No cumple": round(float(porcentaje["No cumple"]), 2),
            "Promedio días Dx > 0": round(float(promedio), 2),
            "N usado promedio": int(n_promedio),
            "Columna performance": col_perf,
            "Columna días": col_dias,
        })

    return pd.DataFrame(data)


def render_tarjeta_etapa(
    titulo,
    regla,
    pct_cumple,
    cumple,
    no_cumple,
    total,
    promedio,
    objetivo=65
):
    color_estado = COLOR_OBJETIVO if pct_cumple >= objetivo else COLOR_NO_CUMPLE
    texto_estado = "Superó 65%" if pct_cumple >= objetivo else "No superó 65%"
    ancho_barra = max(0, min(float(pct_cumple), 100))

    html = f"""
    <div style="
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
        min-height: 360px;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        ">
            <div style="
                font-size: 20px;
                font-weight: 800;
                color: #222222;
            ">
                {titulo}
            </div>

            <div style="
                background: {color_estado};
                color: white;
                padding: 8px 12px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 800;
                white-space: nowrap;
            ">
                {texto_estado}
            </div>
        </div>

        <div style="
            margin-top: 10px;
            font-size: 13px;
            color: #666666;
            min-height: 38px;
        ">
            {regla}
        </div>

        <div style="
            margin-top: 18px;
            font-size: 42px;
            font-weight: 900;
            color: #222222;
            line-height: 1;
        ">
            {pct_cumple:.1f}%
        </div>

        <div style="
            margin-top: 7px;
            font-size: 12px;
            color: #666666;
        ">
            Cumplimiento de la etapa
        </div>

        <div style="
            margin-top: 16px;
            width: 100%;
            height: 12px;
            background: #F3F4F6;
            border-radius: 999px;
            overflow: hidden;
        ">
            <div style="
                width: {ancho_barra:.1f}%;
                height: 12px;
                background: {color_estado};
                border-radius: 999px;
            "></div>
        </div>

        <div style="
            margin-top: 8px;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #666666;
        ">
            <span>0%</span>
            <span style="font-weight: 700; color: {COLOR_OBJETIVO};">Objetivo {objetivo}%</span>
            <span>100%</span>
        </div>

        <div style="
            margin-top: 18px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 12px;
        ">
            <div style="
                background: #F3F4F6;
                border-radius: 12px;
                padding: 12px;
            ">
                <div style="color: #666666;">Cumple</div>
                <div style="
                    font-size: 20px;
                    font-weight: 800;
                    color: #222222;
                ">
                    {cumple:,}
                </div>
            </div>

            <div style="
                background: #F3F4F6;
                border-radius: 12px;
                padding: 12px;
            ">
                <div style="color: #666666;">No cumple</div>
                <div style="
                    font-size: 20px;
                    font-weight: 800;
                    color: #222222;
                ">
                    {no_cumple:,}
                </div>
            </div>
        </div>

        <div style="
            margin-top: 14px;
            font-size: 12px;
            color: #666666;
        ">
            Total evaluable: <b>{total:,}</b> · Promedio días: <b>{promedio:.1f}</b>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


# =========================================================
# APP
# =========================================================

st.title("Dashboard Performance TAT")

st.markdown(
    """
    Este dashboard carga un archivo `.parquet`, permite filtrar por centro
    y grafica el cumplimiento mensual y por etapa usando:

    - Fecha eje X: `fecha_recepcion_final`
    - Estado TAT: `performance_tat_total`
    - Centro: `Centro - ME5A`
    """
)

st.divider()

archivo = st.file_uploader(
    "Carga el archivo parquet",
    type=["parquet"]
)

if archivo is None:
    st.warning("Carga el archivo parquet para comenzar.")
    st.stop()


# =========================================================
# CARGA Y PREPARACIÓN
# =========================================================

try:
    df_original = cargar_parquet(archivo.getvalue())
    df = preparar_dataframe(df_original)

except Exception as e:
    st.error("Error al cargar o preparar el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filtros")

col_centro = detectar_columna_centro(df)

if col_centro is not None:
    centros = (
        df[col_centro]
        .dropna()
        .astype(str)
        .str.strip()
        .sort_values()
        .unique()
        .tolist()
    )

    default_centro = ["E002"] if "E002" in centros else []

    centros_sel = st.sidebar.multiselect(
        "Centro",
        options=centros,
        default=default_centro,
        help="Si no seleccionas centro, se muestran todos."
    )

else:
    centros_sel = []
    st.sidebar.warning("No se encontró columna de centro.")


fechas_validas = df["fecha_recepcion_final"].dropna()

if fechas_validas.empty:
    st.error("No hay fechas válidas en fecha_recepcion_final.")
    st.stop()

fecha_min = fechas_validas.min().date()
fecha_max = fechas_validas.max().date()

rango_fechas = st.sidebar.date_input(
    "Rango fecha recepción",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

mostrar_meses_sin_datos = st.sidebar.checkbox(
    "Mostrar meses sin datos",
    value=False
)

mostrar_df = st.sidebar.checkbox(
    "Mostrar dataframe filtrado",
    value=True
)

filtrar_tat_evaluable_etapas = st.sidebar.checkbox(
    "Etapas: filtrar Performance TAT Cumple / No cumple",
    value=True,
    help=(
        "Replica el filtro usado en Power BI para las tarjetas: "
        "performance_tat_total debe ser Cumple o No cumple."
    )
)

mostrar_diagnostico_tat = st.sidebar.checkbox(
    "Mostrar diagnóstico Performance TAT",
    value=False
)


# =========================================================
# APLICAR FILTROS GENERALES
# =========================================================

df_filtrado = df.copy()

if col_centro is not None and centros_sel:
    centros_sel_str = [
        str(x).strip()
        for x in centros_sel
    ]

    df_filtrado = df_filtrado[
        df_filtrado[col_centro]
        .astype(str)
        .str.strip()
        .isin(centros_sel_str)
    ].copy()


fecha_inicio, fecha_fin = extraer_rango_fechas(rango_fechas)

if fecha_inicio is None or fecha_fin is None:
    st.warning("Selecciona un rango de fechas válido.")
    st.stop()

if fecha_inicio > fecha_fin:
    st.error("La fecha de inicio no puede ser mayor que la fecha de fin.")
    st.stop()

df_filtrado["fecha_recepcion_final"] = pd.to_datetime(
    df_filtrado["fecha_recepcion_final"],
    errors="coerce"
)

df_filtrado = df_filtrado[
    df_filtrado["fecha_recepcion_final"].notna()
    & df_filtrado["fecha_recepcion_final"].between(
        fecha_inicio,
        fecha_fin
    )
].copy()


# =========================================================
# TABS
# =========================================================

tab_dashboard, tab_datos = st.tabs(
    [
        "Dashboard",
        "Datos filtrados"
    ]
)


# =========================================================
# TAB 1: DASHBOARD
# =========================================================

with tab_dashboard:

    total_filas = len(df_filtrado)

    cumple = df_filtrado["performance_tat_estado"].eq("Cumple").sum()
    no_cumple = df_filtrado["performance_tat_estado"].eq("No cumple").sum()

    total_evaluable = cumple + no_cumple
    no_evaluable = total_filas - total_evaluable

    pct_cumple = (
        cumple / total_evaluable * 100
        if total_evaluable > 0
        else 0
    )

    pct_no_cumple = (
        no_cumple / total_evaluable * 100
        if total_evaluable > 0
        else 0
    )

    st.subheader("Indicadores generales")

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    kpi1.metric("Filas filtradas", f"{total_filas:,}")
    kpi2.metric("Evaluables", f"{total_evaluable:,}")
    kpi3.metric("Cumple", f"{cumple:,}")
    kpi4.metric("No cumple", f"{no_cumple:,}")
    kpi5.metric("% Cumple", f"{pct_cumple:.2f}%")
    kpi6.metric("% No cumple", f"{pct_no_cumple:.2f}%")

    st.caption(
        f"Registros no evaluables excluidos del gráfico mensual: {no_evaluable:,}"
    )

    if mostrar_diagnostico_tat:
        with st.expander("Diagnóstico rápido Performance TAT", expanded=True):
            st.write("Distribución original de performance_tat_total filtrado:")

            if "performance_tat_total" in df_filtrado.columns:
                st.write(
                    df_filtrado["performance_tat_total"]
                    .astype(str)
                    .str.strip()
                    .value_counts(dropna=False)
                )

            st.write("Distribución normalizada:")
            st.write(
                df_filtrado["performance_tat_estado"]
                .value_counts(dropna=False)
            )

    st.divider()

    # =====================================================
    # GRÁFICO MENSUAL
    # =====================================================

    st.header("Cumplimiento mensual")

    tabla_resumen = crear_resumen_mensual(df_filtrado)

    if mostrar_meses_sin_datos:
        tabla_resumen = completar_meses(
            tabla=tabla_resumen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

    df_plot = crear_data_plot(
        tabla=tabla_resumen
    )

    grafico_performance_tat(df_plot=df_plot)

    with st.expander("Ver resumen mensual", expanded=False):
        if tabla_resumen.empty:
            st.info("No hay resumen mensual disponible.")
        else:
            columnas_resumen = [
                "periodo_fecha",
                "periodo_label",
                "Cumple",
                "No cumple",
                "Total",
                "% Cumple",
                "% No cumple"
            ]

            columnas_resumen = [
                col for col in columnas_resumen
                if col in tabla_resumen.columns
            ]

            st.dataframe(
                tabla_resumen[columnas_resumen],
                use_container_width=True
            )

    st.divider()

    # =====================================================
    # TARJETAS POR ETAPA
    # =====================================================

    st.header("Cumplimiento por etapa")

    df_etapas = df_filtrado.copy()

    if filtrar_tat_evaluable_etapas:
        df_etapas = df_etapas[
            df_etapas["performance_tat_estado"].isin(
                ["Cumple", "No cumple"]
            )
        ].copy()

    st.caption(
        "Las tarjetas y el ranking consideran solo Cumple / No cumple por etapa. "
        "Los promedios usan días > 0 sobre el dataframe filtrado."
    )

    tabla_diag = crear_tabla_diagnostico_etapas(df_etapas)

    if tabla_diag.empty:
        st.warning("No hay datos de etapas para mostrar.")
    else:
        cols = st.columns(4)

        for col, (_, row) in zip(cols, tabla_diag.iterrows()):
            with col:
                if "Estado" in row and row.get("Estado") == "Faltan columnas":
                    st.warning(f"Faltan columnas para {row['Etapa']}")
                    continue

                render_tarjeta_etapa(
                    titulo=row["Etapa"],
                    regla=row["Regla"],
                    pct_cumple=float(row["% Cumple"]),
                    cumple=int(row["Cumple"]),
                    no_cumple=int(row["No cumple"]),
                    total=int(row["Total evaluable dona"]),
                    promedio=float(row["Promedio días Dx > 0"]),
                    objetivo=OBJETIVO_CUMPLIMIENTO
                )

    with st.expander("Ver diagnóstico de etapas", expanded=False):
        st.dataframe(
            tabla_diag,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# TAB 2: DATOS FILTRADOS
# =========================================================

with tab_datos:

    if mostrar_df:
        st.subheader("Dataframe filtrado")

        st.caption(
            f"Mostrando primeras 500 filas de {len(df_filtrado):,} registros filtrados."
        )

        st.dataframe(
            df_filtrado.head(500),
            use_container_width=True
        )
    else:
        st.info("Activa 'Mostrar dataframe filtrado' en el panel lateral para ver la tabla.")

    st.subheader("Descarga")

    csv = df_filtrado.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")

    st.download_button(
        label="Descargar datos filtrados CSV",
        data=csv,
        file_name="performance_tat_filtrado.csv",
        mime="text/csv"
    )
