import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Performance de Plantas",
    page_icon="📊",
    layout="wide",
)

COLOR_CUMPLE = "#666666"      # Gris
COLOR_NO_CUMPLE = "#E84A5F"   # Rojo
COLOR_META = "#008060"        # Verde
META = 65

# Columnas del NUEVO dataframe
COL_FECHA_RECEPCION = "fecha_recepcion_final"
COL_FECHA_FACTURA = "fecha_facturacion_final"
COL_PERF = "performance_tat_total"
COL_CENTRO = "Centro - ME5A"

# Si no existe Centro - ME5A, se intenta usar esta columna
COL_CENTRO_FALLBACK = "Centro - NME80FN"

# Filtro igual al de Power BI:
# fecha_facturacion_final posterior a 01-02-2024 12:00 a. m.
FECHA_FILTRO_POWERBI = pd.Timestamp("2024-02-01")

CENTROS_EXCLUIR_SERVICIOS = ["E001", "E002", "E009", "E024", "E021"]

# =========================================================
# FUNCIONES
# =========================================================

def leer_archivo(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame:
    nombre = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if nombre.endswith(".csv") or nombre.endswith(".txt"):
        # Intenta separador automático; si falla, prueba ; y tab
        for sep in [None, ";", "\t", ","]:
            try:
                return pd.read_csv(
                    io.BytesIO(data),
                    sep=sep,
                    engine="python",
                    encoding="utf-8-sig",
                    on_bad_lines="skip",
                )
            except Exception:
                continue
        return pd.read_csv(io.BytesIO(data), engine="python", encoding="latin1", on_bad_lines="skip")

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(io.BytesIO(data))

    if nombre.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(data))

    if nombre.endswith(".json") or nombre.endswith(".jsonl"):
        # Soporta JSON normal o JSON Lines
        try:
            return pd.read_json(io.BytesIO(data), lines=True)
        except ValueError:
            return pd.read_json(io.BytesIO(data))

    raise ValueError("Formato no soportado. Usa CSV, TXT, Excel, Parquet, JSON o JSONL.")


def convertir_fecha(serie: pd.Series) -> pd.Series:
    """Convierte fechas en epoch ms, epoch s o texto a datetime."""
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")

    mask_num = serie_num.notna()
    if mask_num.any():
        # En tu nuevo dataframe las fechas vienen como 1704067200000, o sea epoch en milisegundos
        mask_ms = mask_num & serie_num.abs().ge(10**11)
        mask_s = mask_num & serie_num.abs().lt(10**11)

        resultado.loc[mask_ms] = pd.to_datetime(serie_num.loc[mask_ms], unit="ms", errors="coerce")
        resultado.loc[mask_s] = pd.to_datetime(serie_num.loc[mask_s], unit="s", errors="coerce")

    mask_texto = ~mask_num
    if mask_texto.any():
        resultado.loc[mask_texto] = pd.to_datetime(serie.loc[mask_texto], dayfirst=True, errors="coerce")

    return resultado


def normalizar_performance(serie: pd.Series) -> pd.Series:
    serie = serie.astype(str).str.strip()
    serie = serie.replace({
        "No Cumple": "No cumple",
        "NO CUMPLE": "No cumple",
        "CUMPLE": "Cumple",
        "cumple": "Cumple",
        "no cumple": "No cumple",
        "No aplica al análisis": "No aplica al analisis",
    })
    return serie


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    col_centro = COL_CENTRO
    if col_centro not in df.columns and COL_CENTRO_FALLBACK in df.columns:
        col_centro = COL_CENTRO_FALLBACK

    columnas_requeridas = [COL_FECHA_RECEPCION, COL_FECHA_FACTURA, COL_PERF, col_centro]
    faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    df[COL_FECHA_RECEPCION] = convertir_fecha(df[COL_FECHA_RECEPCION])
    df[COL_FECHA_FACTURA] = convertir_fecha(df[COL_FECHA_FACTURA])
    df[COL_PERF] = normalizar_performance(df[COL_PERF])
    df[col_centro] = df[col_centro].astype(str).str.strip()

    # Columna estándar para graficar
    df["centro_grafico"] = df[col_centro]

    # Filtro Power BI: fecha_facturacion_final posterior a 01-02-2024
    df = df[
        (df[COL_FECHA_FACTURA] > FECHA_FILTRO_POWERBI) &
        (df[COL_FECHA_RECEPCION].notna()) &
        (df[COL_PERF].isin(["Cumple", "No cumple"]))
    ].copy()

    df["Mes"] = df[COL_FECHA_RECEPCION].dt.to_period("M").dt.to_timestamp()

    return df


def crear_resumen(data: pd.DataFrame) -> pd.DataFrame:
    resumen = (
        data
        .groupby(["Mes", COL_PERF])
        .size()
        .reset_index(name="Cantidad")
    )

    resumen["Total Mes"] = resumen.groupby("Mes")["Cantidad"].transform("sum")
    resumen["Porcentaje"] = resumen["Cantidad"] / resumen["Total Mes"] * 100
    resumen = resumen.sort_values("Mes")
    return resumen


def agregar_grafico(fig, data: pd.DataFrame, fila: int, mostrar_leyenda: bool):
    resumen = crear_resumen(data)

    for estado, color in [("Cumple", COLOR_CUMPLE), ("No cumple", COLOR_NO_CUMPLE)]:
        estado_data = resumen[resumen[COL_PERF] == estado].copy()

        fig.add_trace(
            go.Bar(
                x=estado_data["Mes"],
                y=estado_data["Porcentaje"],
                name=estado,
                marker_color=color,
                text=estado_data["Porcentaje"].round(1).astype(str) + "%",
                textposition="inside",
                textfont=dict(color="white", size=11),
                hovertemplate=(
                    "Mes: %{x|%b %Y}<br>"
                    f"Estado: {estado}<br>"
                    "Porcentaje: %{y:.1f}%<br>"
                    "<extra></extra>"
                ),
                showlegend=mostrar_leyenda,
            ),
            row=fila,
            col=1,
        )

    fig.add_hline(
        y=META,
        line_dash="dash",
        line_color=COLOR_META,
        annotation_text=f"Meta {META}%",
        annotation_position="top left",
        row=fila,
        col=1,
    )


def grafico_performance_plantas(df: pd.DataFrame):
    grupos = {
        "Performance TAT Prillex": df[df["centro_grafico"] == "E002"].copy(),
        "Performance TAT Rio Loa": df[df["centro_grafico"] == "E024"].copy(),
        "Performance TAT Plantas de servicios": df[~df["centro_grafico"].isin(CENTROS_EXCLUIR_SERVICIOS)].copy(),
    }

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=list(grupos.keys()),
    )

    for fila, (titulo, data) in enumerate(grupos.items(), start=1):
        if data.empty:
            fig.add_annotation(
                text="Sin datos",
                x=0.5,
                y=0.5,
                xref=f"x{fila if fila > 1 else ''} domain",
                yref=f"y{fila if fila > 1 else ''} domain",
                showarrow=False,
                row=fila,
                col=1,
            )
            continue

        agregar_grafico(fig, data, fila=fila, mostrar_leyenda=(fila == 1))

    fig.update_layout(
        title={
            "text": "<b>PERFORMANCE DE PLANTAS</b>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 28},
        },
        barmode="stack",
        height=850,
        margin=dict(l=40, r=40, t=100, b=40),
        legend=dict(
            title="Performance TAT",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        plot_bgcolor="#F2F2F2",
        paper_bgcolor="#FFFFFF",
    )

    for fila in range(1, 4):
        fig.update_yaxes(
            range=[0, 100],
            ticksuffix="%",
            tickvals=[0, 50, 100],
            title_text="",
            row=fila,
            col=1,
        )
        fig.update_xaxes(
            tickformat="%b\n%Y",
            row=fila,
            col=1,
        )

    fig.update_xaxes(title_text="Fecha recepción mercancía", row=3, col=1)

    st.plotly_chart(fig, use_container_width=True)


def mostrar_diagnostico(df: pd.DataFrame):
    with st.expander("Ver diagnóstico de datos"):
        st.write("Filas usadas después de filtros:", len(df))
        st.write("Rango fecha recepción:", df[COL_FECHA_RECEPCION].min(), "→", df[COL_FECHA_RECEPCION].max())
        st.write("Centros principales:")
        st.dataframe(df["centro_grafico"].value_counts().reset_index().rename(columns={"centro_grafico": "Centro", "count": "Filas"}))
        st.write("Performance TAT:")
        st.dataframe(df[COL_PERF].value_counts().reset_index().rename(columns={COL_PERF: "Estado", "count": "Filas"}))

# =========================================================
# APP
# =========================================================

st.title("Performance de Plantas")
st.caption("Prillex = E002 · Rio Loa = E024 · Plantas de servicios = todos excepto E001, E002, E009, E024 y E021")

archivo = st.file_uploader(
    "Carga el nuevo dataframe",
    type=["csv", "txt", "xlsx", "xls", "parquet", "json", "jsonl"],
)

if archivo is None:
    st.info("Carga un archivo para ver el gráfico.")
    st.stop()

try:
    df_original = leer_archivo(archivo)
    df_base = preparar_dataframe(df_original)

    if df_base.empty:
        st.warning("No hay datos después de aplicar el filtro de fecha y Performance TAT.")
        st.stop()

    grafico_performance_plantas(df_base)
    mostrar_diagnostico(df_base)

except Exception as e:
    st.error("No se pudo generar el gráfico.")
    st.exception(e)
