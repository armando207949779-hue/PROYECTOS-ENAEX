import io
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURACIÓN
# =========================================================

COLOR_CUMPLE = "#606060"
COLOR_NO_CUMPLE = "#EF3E52"
COLOR_META = "#008060"
COLOR_BG = "#F3F4F6"
COLOR_CARD = "#FFFFFF"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"

META = 65

COL_FECHA_RECEPCION = "fecha_recepcion_final"
COL_FECHA_FACTURA = "fecha_facturacion_final"
COL_PERF = "performance_tat_total"

COL_CENTRO_PRIORIDAD = "Centro - ME5A"
COL_CENTRO_FALLBACK = "Centro - NME80FN"

FECHA_FILTRO_POWERBI = pd.Timestamp("2024-02-01")

CENTROS_EXCLUIR_SERVICIOS = ["E001", "E002", "E009", "E024", "E021"]

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
    12: "diciembre",
}


# =========================================================
# ESTILO
# =========================================================

def aplicar_css():
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {COLOR_BG};
            }}
            .block-container {{
                padding-top: 1.5rem;
                padding-bottom: 2rem;
                max-width: 1500px;
            }}
            .main-title {{
                text-align: center;
                font-size: 34px;
                font-weight: 850;
                color: {COLOR_TEXTO};
                margin-bottom: 4px;
            }}
            .main-caption {{
                text-align: center;
                font-size: 13px;
                color: {COLOR_MUTED};
                margin-bottom: 18px;
            }}
            .chart-card {{
                background: {COLOR_CARD};
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 14px 16px 8px 16px;
                box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
                margin-bottom: 14px;
            }}
            .chart-title {{
                font-size: 17px;
                font-weight: 750;
                color: {COLOR_TEXTO};
                margin-bottom: 4px;
            }}
            .chart-caption {{
                font-size: 12px;
                color: {COLOR_MUTED};
                margin-bottom: 8px;
            }}
            .metric-box {{
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                padding: 10px 12px;
            }}
            .metric-label {{
                font-size: 11px;
                color: {COLOR_MUTED};
                font-weight: 650;
            }}
            .metric-value {{
                font-size: 22px;
                font-weight: 850;
                color: {COLOR_TEXTO};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# LECTURA
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;)":
        return ";"
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo_cache(bytes_archivo: bytes, nombre_archivo: str, separador_csv: str) -> pd.DataFrame:
    nombre = nombre_archivo.lower()
    buffer = io.BytesIO(bytes_archivo)

    if nombre.endswith(".csv") or nombre.endswith(".txt"):
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip",
            )
        except Exception:
            buffer.seek(0)
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip",
            )

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(buffer)

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".json") or nombre.endswith(".jsonl"):
        try:
            return pd.read_json(buffer, lines=True)
        except ValueError:
            buffer.seek(0)
            return pd.read_json(buffer)

    raise ValueError("Formato no soportado. Usa CSV, TXT, Excel, Parquet, JSON o JSONL.")


# =========================================================
# PREPARACIÓN
# =========================================================

def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")

    resultado = pd.Series(
        pd.NaT,
        index=serie.index,
        dtype="datetime64[ns]",
    )

    mask_num = serie_num.notna()

    if mask_num.any():
        mask_ms = mask_num & serie_num.abs().ge(10**11)
        mask_s = mask_num & serie_num.abs().lt(10**11)

        if mask_ms.any():
            resultado.loc[mask_ms] = pd.to_datetime(
                serie_num.loc[mask_ms],
                unit="ms",
                errors="coerce",
            )

        if mask_s.any():
            resultado.loc[mask_s] = pd.to_datetime(
                serie_num.loc[mask_s],
                unit="s",
                errors="coerce",
            )

    mask_texto = ~mask_num

    if mask_texto.any():
        resultado.loc[mask_texto] = pd.to_datetime(
            serie.loc[mask_texto],
            dayfirst=True,
            errors="coerce",
        )

    return resultado


def normalizar_performance(serie: pd.Series) -> pd.Series:
    salida = serie.astype(str).str.strip()

    salida = salida.replace(
        {
            "Cumple": "Cumple",
            "CUMPLE": "Cumple",
            "cumple": "Cumple",
            "No cumple": "No cumple",
            "No Cumple": "No cumple",
            "NO CUMPLE": "No cumple",
            "no cumple": "No cumple",
            "No aplica al análisis": "No aplica al analisis",
            "No aplica al analisis": "No aplica al analisis",
            "Sin datos": "Sin datos",
            "Sin Datos": "Sin datos",
            "En proceso": "En proceso",
        }
    )

    return salida


def obtener_columna_centro(df: pd.DataFrame) -> str:
    if COL_CENTRO_PRIORIDAD in df.columns:
        return COL_CENTRO_PRIORIDAD

    if COL_CENTRO_FALLBACK in df.columns:
        return COL_CENTRO_FALLBACK

    if "Centro" in df.columns:
        return "Centro"

    raise ValueError(
        "No se encontró columna de centro. Se esperaba 'Centro - ME5A', "
        "'Centro - NME80FN' o 'Centro'."
    )


def validar_columnas(df: pd.DataFrame, col_centro: str):
    requeridas = [
        COL_FECHA_RECEPCION,
        COL_FECHA_FACTURA,
        COL_PERF,
        col_centro,
    ]

    faltantes = [col for col in requeridas if col not in df.columns]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")


@st.cache_data(show_spinner=False)
def preparar_dataframe(df_original: pd.DataFrame) -> pd.DataFrame:
    df = df_original.copy()
    df.columns = df.columns.astype(str).str.strip()

    col_centro = obtener_columna_centro(df)
    validar_columnas(df, col_centro)

    df[COL_FECHA_RECEPCION] = convertir_fecha_columna(df[COL_FECHA_RECEPCION])
    df[COL_FECHA_FACTURA] = convertir_fecha_columna(df[COL_FECHA_FACTURA])
    df[COL_PERF] = normalizar_performance(df[COL_PERF])
    df["centro_grafico"] = df[col_centro].astype(str).str.strip()

    df = df[
        (df[COL_FECHA_FACTURA] > FECHA_FILTRO_POWERBI)
        & df[COL_FECHA_RECEPCION].notna()
        & df[COL_PERF].isin(["Cumple", "No cumple"])
    ].copy()

    df["periodo_fecha"] = df[COL_FECHA_RECEPCION].dt.to_period("M").dt.to_timestamp()
    df["anio"] = df[COL_FECHA_RECEPCION].dt.year
    df["mes_num"] = df[COL_FECHA_RECEPCION].dt.month
    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)
    df["periodo_label"] = (
        df["mes_nombre"].astype(str)
        + " "
        + df["anio"].astype("Int64").astype(str)
    )

    df["grupo_planta"] = "Plantas de servicios"

    df.loc[df["centro_grafico"].eq("E002"), "grupo_planta"] = "Prillex"
    df.loc[df["centro_grafico"].eq("E024"), "grupo_planta"] = "Rio Loa"

    df.loc[
        df["centro_grafico"].isin(CENTROS_EXCLUIR_SERVICIOS)
        & ~df["centro_grafico"].isin(["E002", "E024"]),
        "grupo_planta",
    ] = "Excluir"

    df = df[df["grupo_planta"].ne("Excluir")].copy()

    return df


# =========================================================
# RESÚMENES
# =========================================================

def crear_resumen_grupo(df: pd.DataFrame, grupo: str) -> pd.DataFrame:
    data = df[df["grupo_planta"].eq(grupo)].copy()

    if data.empty:
        return pd.DataFrame()

    resumen = (
        data
        .groupby(["periodo_fecha", "periodo_label", COL_PERF])
        .size()
        .reset_index(name="cantidad")
    )

    resumen["total_mes"] = resumen.groupby("periodo_fecha")["cantidad"].transform("sum")
    resumen["porcentaje"] = resumen["cantidad"] / resumen["total_mes"] * 100

    resumen["estado"] = resumen[COL_PERF].replace(
        {
            "Cumple": "Cumple",
            "No cumple": "No Cumple",
        }
    )

    resumen["orden_estado"] = resumen["estado"].map(
        {
            "Cumple": 1,
            "No Cumple": 2,
        }
    )

    resumen = resumen.sort_values(["periodo_fecha", "orden_estado"])

    return resumen


def resumen_kpis(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    tabla = (
        df
        .groupby(["grupo_planta", COL_PERF])
        .size()
        .reset_index(name="cantidad")
    )

    pivot = tabla.pivot_table(
        index="grupo_planta",
        columns=COL_PERF,
        values="cantidad",
        fill_value=0,
        aggfunc="sum",
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["Total evaluable"] = pivot["Cumple"] + pivot["No cumple"]
    pivot["% Cumple"] = pivot["Cumple"] / pivot["Total evaluable"] * 100
    pivot["% Cumple"] = pivot["% Cumple"].fillna(0)

    return pivot


# =========================================================
# GRÁFICOS ALTAIR
# =========================================================

def grafico_grupo(df: pd.DataFrame, grupo: str, titulo: str):
    resumen = crear_resumen_grupo(df, grupo)

    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-title'>{titulo}</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='chart-caption'>Base: Performance TAT Cumple / No cumple. "
        "Filtro aplicado: fecha_facturacion_final posterior a 01-02-2024.</div>",
        unsafe_allow_html=True,
    )

    if resumen.empty:
        st.info("Sin datos para este grupo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    orden_periodos = (
        resumen
        .drop_duplicates("periodo_fecha")
        .sort_values("periodo_fecha")["periodo_label"]
        .tolist()
    )

    barras = (
        alt.Chart(resumen)
        .mark_bar(size=28)
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos,
                title=None,
                axis=alt.Axis(labelAngle=-90, labelFontSize=10),
            ),
            y=alt.Y(
                "porcentaje:Q",
                stack="zero",
                title="% Performance TAT",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(
                    values=[0, 50, 100],
                    labelExpr="datum.value + '%'",
                    grid=True,
                ),
            ),
            color=alt.Color(
                "estado:N",
                scale=alt.Scale(
                    domain=["Cumple", "No Cumple"],
                    range=[COLOR_CUMPLE, COLOR_NO_CUMPLE],
                ),
                legend=alt.Legend(
                    title="Performance TAT",
                    orient="top",
                    direction="horizontal",
                ),
            ),
            order=alt.Order("orden_estado:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("estado:N", title="Estado"),
                alt.Tooltip("cantidad:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("porcentaje:Q", title="Porcentaje", format=".1f"),
                alt.Tooltip("total_mes:Q", title="Total mes", format=",.0f"),
            ],
        )
    )

    etiquetas = (
        alt.Chart(resumen)
        .mark_text(
            color="white",
            fontSize=10,
            dy=0,
            angle=270,
            fontWeight="bold",
        )
        .encode(
            x=alt.X("periodo_label:N", sort=orden_periodos),
            y=alt.Y("porcentaje:Q", stack="center"),
            text=alt.Text("porcentaje:Q", format=".1f"),
            order=alt.Order("orden_estado:Q", sort="ascending"),
        )
    )

    linea_meta = (
        alt.Chart(pd.DataFrame({"meta": [META]}))
        .mark_rule(
            color=COLOR_META,
            strokeDash=[6, 4],
            strokeWidth=2,
        )
        .encode(
            y="meta:Q",
        )
    )

    texto_meta = (
        alt.Chart(pd.DataFrame({"meta": [META], "x": [orden_periodos[0]]}))
        .mark_text(
            align="left",
            baseline="bottom",
            dx=4,
            dy=-4,
            color=COLOR_META,
            fontSize=11,
            fontWeight="bold",
        )
        .encode(
            x=alt.X("x:N", sort=orden_periodos),
            y="meta:Q",
            text=alt.value(f"Meta {META}%"),
        )
    )

    chart = (
        (barras + etiquetas + linea_meta + texto_meta)
        .properties(height=185)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def mostrar_kpis(df: pd.DataFrame):
    kpis = resumen_kpis(df)

    if kpis.empty:
        return

    orden = ["Prillex", "Rio Loa", "Plantas de servicios"]

    cols = st.columns(3)

    for i, grupo in enumerate(orden):
        data = kpis[kpis["grupo_planta"].eq(grupo)]

        if data.empty:
            cumple = 0
            no_cumple = 0
            total = 0
            pct = 0
        else:
            fila = data.iloc[0]
            cumple = int(fila["Cumple"])
            no_cumple = int(fila["No cumple"])
            total = int(fila["Total evaluable"])
            pct = float(fila["% Cumple"])

        with cols[i]:
            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">{grupo}</div>
                    <div class="metric-value">{pct:.1f}%</div>
                    <div style="font-size:11px;color:{COLOR_MUTED};">
                        Cumple: {cumple:,} · No cumple: {no_cumple:,} · Total: {total:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def mostrar_diagnostico(df: pd.DataFrame):
    with st.expander("Ver diagnóstico de datos", expanded=False):
        st.write("Filas usadas después de filtros:", len(df))

        st.write(
            "Rango fecha recepción:",
            df[COL_FECHA_RECEPCION].min(),
            "→",
            df[COL_FECHA_RECEPCION].max(),
        )

        st.write("Centros principales:")
        centros = (
            df["centro_grafico"]
            .value_counts()
            .reset_index()
        )
        centros.columns = ["Centro", "Filas"]
        st.dataframe(centros, use_container_width=True, hide_index=True)

        st.write("Performance TAT:")
        perf = (
            df[COL_PERF]
            .value_counts()
            .reset_index()
        )
        perf.columns = ["Estado", "Filas"]
        st.dataframe(perf, use_container_width=True, hide_index=True)

        st.write("Grupos:")
        grupos = (
            df["grupo_planta"]
            .value_counts()
            .reset_index()
        )
        grupos.columns = ["Grupo", "Filas"]
        st.dataframe(grupos, use_container_width=True, hide_index=True)


# =========================================================
# APP
# =========================================================

aplicar_css()

st.markdown(
    """
    <div class="main-title">PERFORMANCE DE PLANTAS</div>
    <div class="main-caption">
        Prillex = E002 · Rio Loa = E024 · Plantas de servicios = todos excepto E001, E002, E009, E024 y E021
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Performance de Plantas")

    separador_csv = st.selectbox(
        "Separador CSV",
        options=["Automático", "Punto y coma (;)", "Coma (,)", "Tabulación"],
        index=0,
    )

    mostrar_diagnostico_check = st.checkbox(
        "Mostrar diagnóstico",
        value=False,
    )

    st.caption(
        "El gráfico usa fecha_recepcion_final como eje X y filtra "
        "fecha_facturacion_final > 01-02-2024."
    )

archivo = st.file_uploader(
    "Carga el dataframe con fechas finales",
    type=["csv", "txt", "xlsx", "xls", "parquet", "json", "jsonl"],
)

if archivo is None:
    st.info("Carga un archivo para visualizar el gráfico de Performance de Plantas.")
    st.stop()

try:
    with st.spinner("Leyendo archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=archivo.getvalue(),
            nombre_archivo=archivo.name,
            separador_csv=separador_csv,
        )

    with st.spinner("Preparando gráfico..."):
        df_base = preparar_dataframe(df_original)

    if df_base.empty:
        st.warning(
            "No hay datos después de aplicar los filtros: "
            "fecha_facturacion_final > 01-02-2024, fecha_recepcion_final válida "
            "y Performance TAT en Cumple / No cumple."
        )
        st.stop()

    mostrar_kpis(df_base)

    st.divider()

    grafico_grupo(
        df=df_base,
        grupo="Prillex",
        titulo="Performance TAT Prillex",
    )

    grafico_grupo(
        df=df_base,
        grupo="Rio Loa",
        titulo="Performance TAT Rio Loa",
    )

    grafico_grupo(
        df=df_base,
        grupo="Plantas de servicios",
        titulo="Performance TAT Plantas de servicios",
    )

    if mostrar_diagnostico_check:
        mostrar_diagnostico(df_base)

except Exception as e:
    st.error("No se pudo generar el gráfico de Performance de Plantas.")
    st.exception(e)
