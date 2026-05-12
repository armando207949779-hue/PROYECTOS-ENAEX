# App Streamlit: Limpieza minimalista ME5A con entrada, salida,
# descarga Parquet principal, CSV/Excel opcionales y análisis opcional

import io
import re
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt
from pandas.api.types import is_datetime64_any_dtype


# =========================================================
# Configuración general
# =========================================================

st.set_page_config(
    page_title="Limpieza ME5A",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# Logo
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


def mostrar_logo():
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
                margin-top: 5px;
                margin-bottom: 10px;
            ">
                <img 
                    src="data:image/svg+xml;base64,{logo_base64}" 
                    style="width: 220px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# Funciones base
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


# =========================================================
# Lectura de archivo
# =========================================================

@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    bytes_archivo: bytes,
    nombre_archivo: str,
    separador_csv: str
) -> pd.DataFrame:

    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".xlsx"):
        return pd.read_excel(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip"
            )

        except Exception:
            buffer.seek(0)

            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


# =========================================================
# Limpieza de datos ME5A
# =========================================================

def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = df.columns.astype(str).str.strip()

    df = df.dropna(axis=1, how="all")

    columnas_unnamed = [
        col for col in df.columns
        if str(col).startswith("Unnamed")
    ]

    for col in columnas_unnamed:
        if df[col].isna().all():
            df = df.drop(columns=[col])

    cols_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in cols_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )

        df[col] = df[col].replace("", pd.NA)

    cols_fecha = [
        "Fecha de solicitud",
        "Fecha modificación",
        "Fe.liber.Z",
        "Fecha de pedido",
        "Fecha de liberación"
    ]

    for col in cols_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
                dayfirst=True
            )

    if "Fecha de entrega" in df.columns:
        df["Fecha de entrega"] = pd.to_datetime(
            df["Fecha de entrega"].astype("string"),
            format="%Y%m%d",
            errors="coerce"
        )

    cols_numericas = [
        "Cantidad solicitada",
        "Precio de valoración"
    ]

    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    if "Pedido" in df.columns:
        df["Pedido"] = pd.to_numeric(
            df["Pedido"],
            errors="coerce"
        ).astype("Int64")

    cols_enteras = [
        "Solicitud de pedido",
        "Pos.solicitud pedido",
        "Posición de pedido"
    ]

    for col in cols_enteras:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).astype("Int64")

    return df


@st.cache_data(show_spinner=False)
def limpiar_cache(df: pd.DataFrame) -> pd.DataFrame:
    return limpiar_fechas_y_numeros(df)


# =========================================================
# Diagnóstico
# =========================================================

def tabla_diagnostico_columnas(df: pd.DataFrame) -> pd.DataFrame:
    total_filas = len(df)

    if total_filas == 0:
        return pd.DataFrame({
            "Columna": df.columns,
            "Tipo de dato": [str(dtype) for dtype in df.dtypes],
            "No nulos": 0,
            "Nulos": 0,
            "% Nulos": 0,
            "Valores únicos": 0
        })

    diagnostico = pd.DataFrame({
        "Columna": df.columns,
        "Tipo de dato": [str(dtype) for dtype in df.dtypes],
        "No nulos": df.notna().sum().values,
        "Nulos": df.isna().sum().values,
        "% Nulos": (df.isna().sum().values / total_filas * 100).round(2),
        "Valores únicos": df.nunique(dropna=True).values
    })

    diagnostico = diagnostico.sort_values(
        by="% Nulos",
        ascending=False
    ).reset_index(drop=True)

    return diagnostico


def diagnostico_general(df: pd.DataFrame) -> dict:
    total_filas = len(df)
    total_columnas = len(df.columns)
    total_celdas = total_filas * total_columnas

    total_nulos = int(df.isna().sum().sum())

    porcentaje_nulos = (
        round((total_nulos / total_celdas) * 100, 2)
        if total_celdas > 0
        else 0
    )

    duplicados = int(df.duplicated().sum())

    porcentaje_duplicados = (
        round((duplicados / total_filas) * 100, 2)
        if total_filas > 0
        else 0
    )

    return {
        "total_filas": total_filas,
        "total_columnas": total_columnas,
        "total_nulos": total_nulos,
        "porcentaje_nulos": porcentaje_nulos,
        "duplicados": duplicados,
        "porcentaje_duplicados": porcentaje_duplicados
    }


def columnas_fecha(df: pd.DataFrame) -> list:
    return [
        col for col in df.columns
        if is_datetime64_any_dtype(df[col])
    ]


def diagnostico_fechas(df: pd.DataFrame) -> pd.DataFrame:
    cols = columnas_fecha(df)

    if len(cols) == 0:
        return pd.DataFrame()

    data = []

    for col in cols:
        data.append({
            "Columna": col,
            "Fecha mínima": df[col].min(),
            "Fecha máxima": df[col].max(),
            "Nulos": df[col].isna().sum(),
            "% Nulos": round(df[col].isna().mean() * 100, 2)
        })

    return (
        pd.DataFrame(data)
        .sort_values("% Nulos", ascending=False)
        .reset_index(drop=True)
    )


def resumen_numerico(df: pd.DataFrame) -> pd.DataFrame:
    cols_num = df.select_dtypes(include=["number"]).columns

    if len(cols_num) == 0:
        return pd.DataFrame()

    resumen = df[cols_num].describe().T.reset_index()
    resumen = resumen.rename(columns={"index": "Columna"})

    return resumen


@st.cache_data(show_spinner=False)
def diagnostico_cache(df: pd.DataFrame):
    diagnostico_columnas = tabla_diagnostico_columnas(df)
    resumen_general = diagnostico_general(df)
    resumen_fechas = diagnostico_fechas(df)
    resumen_num = resumen_numerico(df)

    return diagnostico_columnas, resumen_general, resumen_fechas, resumen_num


# =========================================================
# Mensaje de cambios realizados
# =========================================================

def generar_resumen_cambios(
    df_original: pd.DataFrame,
    df_limpio: pd.DataFrame
) -> dict:

    columnas_originales = set(df_original.columns.astype(str))
    columnas_limpias = set(df_limpio.columns.astype(str))

    columnas_eliminadas = sorted(list(columnas_originales - columnas_limpias))
    columnas_agregadas = sorted(list(columnas_limpias - columnas_originales))

    columnas_convertidas_fecha = columnas_fecha(df_limpio)

    columnas_numericas_detectadas = [
        col for col in [
            "Cantidad solicitada",
            "Precio de valoración",
            "Pedido",
            "Solicitud de pedido",
            "Pos.solicitud pedido",
            "Posición de pedido"
        ]
        if col in df_limpio.columns
    ]

    duplicados = int(df_limpio.duplicated().sum())

    return {
        "filas_originales": int(len(df_original)),
        "columnas_originales": int(len(df_original.columns)),
        "filas_limpias": int(len(df_limpio)),
        "columnas_limpias": int(len(df_limpio.columns)),
        "columnas_eliminadas": columnas_eliminadas,
        "columnas_agregadas": columnas_agregadas,
        "columnas_fecha": columnas_convertidas_fecha,
        "columnas_numericas": columnas_numericas_detectadas,
        "duplicados": duplicados
    }


def mostrar_resumen_cambios(resumen: dict):
    columnas_eliminadas = resumen["columnas_eliminadas"]
    columnas_agregadas = resumen["columnas_agregadas"]
    columnas_fecha_convertidas = resumen["columnas_fecha"]
    columnas_numericas = resumen["columnas_numericas"]

    texto_columnas_eliminadas = (
        ", ".join(columnas_eliminadas)
        if columnas_eliminadas
        else "No se eliminaron columnas por nombre; solo se quitaron columnas completamente vacías si existían."
    )

    texto_columnas_agregadas = (
        ", ".join(columnas_agregadas)
        if columnas_agregadas
        else "No se agregaron columnas nuevas."
    )

    texto_fechas = (
        ", ".join(columnas_fecha_convertidas)
        if columnas_fecha_convertidas
        else "No se detectaron columnas de fecha convertidas."
    )

    texto_numericas = (
        ", ".join(columnas_numericas)
        if columnas_numericas
        else "No se detectaron columnas numéricas configuradas."
    )

    st.info(
        f"""
        **Cambios realizados al archivo cargado**

        - Se leyeron **{resumen['filas_originales']:,} filas** y **{resumen['columnas_originales']:,} columnas**.
        - Después de limpiar nombres de columnas, textos, fechas, números y columnas vacías, quedaron **{resumen['filas_limpias']:,} filas** y **{resumen['columnas_limpias']:,} columnas**.
        - Se quitaron columnas completamente vacías si existían.
        - Se limpiaron espacios en textos y valores vacíos.
        - Se convirtieron fechas detectadas: **{texto_fechas}**.
        - Se convirtieron columnas numéricas configuradas: **{texto_numericas}**.
        - Filas duplicadas detectadas: **{resumen['duplicados']:,}**.
        - Columnas eliminadas: **{texto_columnas_eliminadas}**
        - Columnas agregadas: **{texto_columnas_agregadas}**
        """
    )


# =========================================================
# Exportación
# =========================================================

def generar_nombre_salida(nombre_archivo: str, extension: str) -> str:
    nombre_base = Path(nombre_archivo).stem

    nombre_base = nombre_base.strip().lower()
    nombre_base = re.sub(r"\s+", "_", nombre_base)
    nombre_base = nombre_base.replace("-", "_")
    nombre_base = re.sub(r"[^a-zA-Z0-9_]", "", nombre_base)
    nombre_base = re.sub(r"_+", "_", nombre_base)
    nombre_base = nombre_base.strip("_")

    if nombre_base.startswith("me5a_"):
        return f"{nombre_base}_limpio.{extension}"

    if nombre_base == "me5a":
        return f"{nombre_base}_limpio.{extension}"

    return f"me5a_{nombre_base}_limpio.{extension}"


def convertir_a_excel(
    df_limpio: pd.DataFrame,
    diagnostico_columnas: pd.DataFrame,
    resumen_fechas: pd.DataFrame,
    resumen_num: pd.DataFrame
) -> bytes:

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_limpio.to_excel(
            writer,
            index=False,
            sheet_name="Data_Limpia"
        )

        diagnostico_columnas.to_excel(
            writer,
            index=False,
            sheet_name="Diagnostico_Columnas"
        )

        if not resumen_fechas.empty:
            resumen_fechas.to_excel(
                writer,
                index=False,
                sheet_name="Resumen_Fechas"
            )

        if not resumen_num.empty:
            resumen_num.to_excel(
                writer,
                index=False,
                sheet_name="Resumen_Numerico"
            )

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(
    df_limpio: pd.DataFrame,
    diagnostico_columnas: pd.DataFrame,
    resumen_fechas: pd.DataFrame,
    resumen_num: pd.DataFrame
) -> bytes:
    return convertir_a_excel(
        df_limpio=df_limpio,
        diagnostico_columnas=diagnostico_columnas,
        resumen_fechas=resumen_fechas,
        resumen_num=resumen_num
    )


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


# =========================================================
# Gráficos Altair
# =========================================================

def chart_nulos_por_columna(diag_cols: pd.DataFrame, top_n: int | None = None):
    if diag_cols.empty:
        st.info("No hay columnas para graficar.")
        return

    data = (
        diag_cols[["Columna", "% Nulos"]]
        .copy()
        .sort_values("% Nulos", ascending=False)
    )

    if top_n is not None:
        data = data.head(top_n)

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Columna:N",
                sort=alt.SortField(
                    field="% Nulos",
                    order="descending"
                ),
                title=None,
                axis=alt.Axis(labelAngle=-90)
            ),
            y=alt.Y(
                "% Nulos:Q",
                title="% nulos"
            ),
            tooltip=[
                alt.Tooltip("Columna:N", title="Columna"),
                alt.Tooltip("% Nulos:Q", title="% nulos", format=".2f")
            ]
        )
        .properties(height=380)
    )

    st.altair_chart(chart, use_container_width=True)


def chart_valores_unicos(diag_cols: pd.DataFrame, top_n: int = 10):
    if diag_cols.empty:
        st.info("No hay columnas para graficar.")
        return

    data = (
        diag_cols[["Columna", "Valores únicos"]]
        .copy()
        .sort_values("Valores únicos", ascending=False)
        .head(top_n)
    )

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Columna:N",
                sort=alt.SortField(
                    field="Valores únicos",
                    order="descending"
                ),
                title=None,
                axis=alt.Axis(labelAngle=-90)
            ),
            y=alt.Y(
                "Valores únicos:Q",
                title="Valores únicos"
            ),
            tooltip=[
                alt.Tooltip("Columna:N", title="Columna"),
                alt.Tooltip("Valores únicos:Q", title="Valores únicos")
            ]
        )
        .properties(height=380)
    )

    st.altair_chart(chart, use_container_width=True)


def chart_tipos_dato(df: pd.DataFrame):
    data = (
        pd.Series(df.dtypes.astype(str), name="Tipo de dato")
        .value_counts()
        .reset_index()
    )

    data.columns = ["Tipo de dato", "Cantidad"]

    data = data.sort_values(
        by="Cantidad",
        ascending=False
    )

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Tipo de dato:N",
                sort=alt.SortField(
                    field="Cantidad",
                    order="descending"
                ),
                title=None
            ),
            y=alt.Y(
                "Cantidad:Q",
                title="Cantidad"
            ),
            tooltip=[
                alt.Tooltip("Tipo de dato:N", title="Tipo de dato"),
                alt.Tooltip("Cantidad:Q", title="Cantidad")
            ]
        )
        .properties(height=320)
    )

    st.altair_chart(chart, use_container_width=True)


def chart_serie_fecha(df: pd.DataFrame, columna_fecha: str):
    data = (
        df[columna_fecha]
        .dropna()
        .dt.date
        .value_counts()
        .sort_index()
        .reset_index()
    )

    if data.empty:
        st.info("La columna seleccionada no tiene fechas válidas.")
        return

    data.columns = ["Fecha", "Cantidad"]
    data["Fecha"] = pd.to_datetime(data["Fecha"])

    chart = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X("Fecha:T", title="Fecha"),
            y=alt.Y("Cantidad:Q", title="Registros"),
            tooltip=[
                alt.Tooltip("Fecha:T", title="Fecha"),
                alt.Tooltip("Cantidad:Q", title="Registros")
            ]
        )
        .properties(height=360)
    )

    st.altair_chart(chart, use_container_width=True)


# =========================================================
# Interfaz principal
# =========================================================

mostrar_logo()

st.markdown(
    """
    <h2 style='text-align:center; margin-bottom:0px;'>
        Limpieza ME5A
    </h2>
    <p style='text-align:center; color:gray; margin-top:4px;'>
        Carga, limpieza y exportación de archivos ME5A
    </p>
    """,
    unsafe_allow_html=True
)

st.info(
    "La aplicación lee archivos ME5A, limpia textos, fechas y números, "
    "elimina columnas vacías y genera un archivo Parquet como salida principal."
)

st.divider()


# =========================================================
# Sidebar minimalista
# =========================================================

with st.sidebar:
    st.header("Menú")

    modulo = st.radio(
        "Selecciona una vista",
        options=[
            "Entrada",
            "Salida"
        ],
        index=0
    )

    st.divider()

    mostrar_analisis = st.checkbox(
        "Mostrar análisis",
        value=False
    )

    st.divider()

    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación"
        ],
        index=0
    )


# =========================================================
# Carga de archivo
# =========================================================

uploaded_file = st.file_uploader(
    "Cargar archivo",
    type=["parquet", "xlsx", "csv"],
    label_visibility="collapsed"
)


if uploaded_file is None:
    st.info("Carga un archivo Parquet, Excel o CSV para comenzar.")
    st.stop()


# =========================================================
# Procesamiento
# =========================================================

try:
    bytes_archivo = uploaded_file.getvalue()
    nombre_archivo = uploaded_file.name

    with st.spinner("Procesando archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=bytes_archivo,
            nombre_archivo=nombre_archivo,
            separador_csv=separador_csv
        )

        df_limpio = limpiar_cache(df_original)

        diagnostico_columnas, resumen_general, resumen_fechas, resumen_num = diagnostico_cache(
            df_limpio
        )

        parquet_bytes = convertir_a_parquet_cache(df_limpio)

        nombre_parquet = generar_nombre_salida(
            nombre_archivo,
            "parquet"
        )

        nombre_excel = generar_nombre_salida(
            nombre_archivo,
            "xlsx"
        )

        nombre_csv = generar_nombre_salida(
            nombre_archivo,
            "csv"
        )

        resumen_cambios = generar_resumen_cambios(
            df_original=df_original,
            df_limpio=df_limpio
        )

    st.success("Archivo procesado correctamente.")

except Exception as e:
    st.error("No fue posible procesar el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# Mensaje de cambios realizados
# =========================================================

mostrar_resumen_cambios(resumen_cambios)


# =========================================================
# Métricas superiores
# =========================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Filas originales", f"{len(df_original):,}")
col2.metric("Columnas originales", f"{df_original.shape[1]:,}")
col3.metric("Filas limpias", f"{len(df_limpio):,}")
col4.metric("Columnas limpias", f"{df_limpio.shape[1]:,}")

st.divider()


# =========================================================
# Descarga principal y descargas opcionales
# =========================================================

st.markdown("### Descarga")

st.download_button(
    label="Descargar Parquet",
    data=parquet_bytes,
    file_name=nombre_parquet,
    mime="application/octet-stream",
    use_container_width=True
)

st.caption(
    "Parquet es el formato principal recomendado para conservar tipos de datos "
    "y trabajar con Python. CSV y Excel se preparan solo si los solicitas."
)

with st.expander("Opcional: descargar como CSV o Excel"):
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                csv_bytes = convertir_a_csv_cache(df_limpio)

            st.download_button(
                label="Descargar CSV",
                data=csv_bytes,
                file_name=nombre_csv,
                mime="text/csv",
                use_container_width=True
            )

    with col_d2:
        preparar_excel = st.button(
            "Preparar Excel",
            use_container_width=True
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                excel_bytes = convertir_a_excel_cache(
                    df_limpio=df_limpio,
                    diagnostico_columnas=diagnostico_columnas,
                    resumen_fechas=resumen_fechas,
                    resumen_num=resumen_num
                )

            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name=nombre_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

st.divider()


# =========================================================
# Vista Entrada
# =========================================================

if modulo == "Entrada":

    st.subheader("Entrada")

    tab1, tab2 = st.tabs([
        "Archivo original",
        "Archivo limpio"
    ])

    with tab1:
        st.dataframe(
            df_original.head(100),
            use_container_width=True
        )

    with tab2:
        st.dataframe(
            df_limpio.head(100),
            use_container_width=True
        )


# =========================================================
# Vista Salida
# =========================================================

elif modulo == "Salida":

    st.subheader("Salida")

    st.info(
        "El archivo Parquet está disponible en la sección superior. "
        "CSV y Excel se preparan únicamente desde la sección opcional."
    )

    st.dataframe(
        df_limpio.head(100),
        use_container_width=True
    )


# =========================================================
# Análisis opcional
# =========================================================

if mostrar_analisis:

    st.divider()
    st.subheader("Análisis opcional")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "% nulos total",
        f"{resumen_general['porcentaje_nulos']}%"
    )

    col2.metric(
        "Celdas nulas",
        f"{resumen_general['total_nulos']:,}"
    )

    col3.metric(
        "% duplicados",
        f"{resumen_general['porcentaje_duplicados']}%"
    )

    col4.metric(
        "Filas duplicadas",
        f"{resumen_general['duplicados']:,}"
    )

    tab_a, tab_b, tab_c, tab_d = st.tabs([
        "Nulos",
        "Tipos de dato",
        "Valores únicos",
        "Fechas"
    ])

    with tab_a:
        st.markdown("#### Porcentaje de nulos por columna")
        chart_nulos_por_columna(
            diagnostico_columnas,
            top_n=20
        )

        with st.expander("Ver tabla de diagnóstico"):
            st.dataframe(
                diagnostico_columnas,
                use_container_width=True
            )

    with tab_b:
        st.markdown("#### Distribución de tipos de dato")
        chart_tipos_dato(df_limpio)

    with tab_c:
        st.markdown("#### Columnas con más valores únicos")
        chart_valores_unicos(
            diagnostico_columnas,
            top_n=20
        )

    with tab_d:
        cols_fecha_detectadas = columnas_fecha(df_limpio)

        if len(cols_fecha_detectadas) == 0:
            st.info("No se detectaron columnas de fecha.")
        else:
            col_fecha = st.selectbox(
                "Columna de fecha",
                options=cols_fecha_detectadas
            )

            chart_serie_fecha(
                df_limpio,
                col_fecha
            )

            with st.expander("Ver resumen de fechas"):
                st.dataframe(
                    resumen_fechas,
                    use_container_width=True
                )
