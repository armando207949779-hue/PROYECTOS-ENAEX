# App Streamlit: Limpieza minimalista ARIBA con entrada, salida, descarga Parquet y análisis opcional

import io
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
    page_title="Limpieza ARIBA",
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

@st.cache_data(show_spinner="Leyendo archivo...")
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
        df = pd.read_excel(
            buffer,
            sheet_name="Data",
            header=13
        )

        # En ARIBA el contenido útil comienza desde columna B.
        df = df.iloc[:, 1:].copy()

        return df

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
# Limpieza de datos ARIBA
# =========================================================

def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Limpieza de nombres de columnas
    df.columns = df.columns.astype(str).str.strip()

    # Eliminación de columnas completamente vacías
    df = df.dropna(axis=1, how="all")

    # Eliminación de columnas Unnamed vacías
    columnas_unnamed = [
        col for col in df.columns
        if str(col).startswith("Unnamed")
    ]

    for col in columnas_unnamed:
        if df[col].isna().all():
            df = df.drop(columns=[col])

    # Conversión de fechas
    cols_fecha = [
        "Fecha de la solicitud de compra",
        "Fecha de aprobación"
    ]

    for col in cols_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
                dayfirst=True
            )

    # Conversión de columnas numéricas
    cols_numericas = [
        "Tipo de Compra",
        "Número de línea de la solicitud de compra",
        "sum(Coste de variación de precio)"
    ]

    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # Conversión a enteros nullable
    if "Tipo de Compra" in df.columns:
        df["Tipo de Compra"] = df["Tipo de Compra"].astype("Int64")

    if "Número de línea de la solicitud de compra" in df.columns:
        df["Número de línea de la solicitud de compra"] = (
            df["Número de línea de la solicitud de compra"]
            .astype("Int64")
        )

    # Limpieza de textos
    cols_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in cols_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )

        df[col] = df[col].replace("", pd.NA)

    return df


def aplicar_filtros_y_categoria(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    columnas_requeridas = [
        "Tipo de Compra",
        "ID de unidad de negocio"
    ]

    faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    # Excluir nulos en Tipo de Compra
    df = df[df["Tipo de Compra"].notna()].copy()

    # Dejar solo unidad de negocio CEN1
    df = df[
        df["ID de unidad de negocio"]
        .astype("string")
        .str.strip()
        .eq("CEN1")
    ].copy()

    # Crear categoría de compra
    mapa_tipo_compra = {
        1: "CATALOGADA",
        2: "NO CATALOGADA",
        3: "COMPRA DIRECTA"
    }

    df["Categoria Tipo de Compra"] = (
        df["Tipo de Compra"]
        .map(mapa_tipo_compra)
        .astype("string")
    )

    return df


@st.cache_data(show_spinner="Limpiando archivo...")
def limpiar_cache(df: pd.DataFrame) -> pd.DataFrame:
    return limpiar_fechas_y_numeros(df)


@st.cache_data(show_spinner="Aplicando filtros...")
def filtrar_cache(df: pd.DataFrame) -> pd.DataFrame:
    return aplicar_filtros_y_categoria(df)


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


@st.cache_data(show_spinner="Generando diagnóstico...")
def diagnostico_cache(df: pd.DataFrame):
    diagnostico_columnas = tabla_diagnostico_columnas(df)
    resumen_general = diagnostico_general(df)
    resumen_fechas = diagnostico_fechas(df)
    resumen_num = resumen_numerico(df)

    return diagnostico_columnas, resumen_general, resumen_fechas, resumen_num


# =========================================================
# Exportación
# =========================================================

def generar_nombre_salida(extension: str) -> str:
    return f"ariba_limpio.{extension}"


def convertir_a_excel(
    df_limpio: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    diagnostico_columnas: pd.DataFrame | None = None,
    resumen_fechas: pd.DataFrame | None = None,
    resumen_num: pd.DataFrame | None = None
) -> bytes:

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_limpio.to_excel(
            writer,
            index=False,
            sheet_name="Data_Limpia"
        )

        df_filtrado.to_excel(
            writer,
            index=False,
            sheet_name="Final_Limpio_CEN1"
        )

        if "Categoria Tipo de Compra" in df_filtrado.columns:
            conteo_categoria = (
                df_filtrado["Categoria Tipo de Compra"]
                .value_counts(dropna=False)
                .reset_index()
            )

            conteo_categoria.columns = [
                "Categoria Tipo de Compra",
                "Cantidad"
            ]

            conteo_categoria.to_excel(
                writer,
                index=False,
                sheet_name="Conteo_Categoria"
            )

        if diagnostico_columnas is not None:
            diagnostico_columnas.to_excel(
                writer,
                index=False,
                sheet_name="Diagnostico_Columnas"
            )

        if resumen_fechas is not None and not resumen_fechas.empty:
            resumen_fechas.to_excel(
                writer,
                index=False,
                sheet_name="Resumen_Fechas"
            )

        if resumen_num is not None and not resumen_num.empty:
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


@st.cache_data(show_spinner="Preparando Excel...")
def convertir_a_excel_cache(
    df_limpio: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    diagnostico_columnas: pd.DataFrame,
    resumen_fechas: pd.DataFrame,
    resumen_num: pd.DataFrame
) -> bytes:
    return convertir_a_excel(
        df_limpio=df_limpio,
        df_filtrado=df_filtrado,
        diagnostico_columnas=diagnostico_columnas,
        resumen_fechas=resumen_fechas,
        resumen_num=resumen_num
    )


@st.cache_data(show_spinner="Preparando CSV...")
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner="Preparando Parquet...")
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


def chart_conteo_categoria(df_filtrado: pd.DataFrame):
    if "Categoria Tipo de Compra" not in df_filtrado.columns:
        st.info("No existe la columna Categoria Tipo de Compra.")
        return

    conteo_categoria = (
        df_filtrado["Categoria Tipo de Compra"]
        .value_counts(dropna=False)
        .reset_index()
    )

    conteo_categoria.columns = [
        "Categoria Tipo de Compra",
        "Cantidad"
    ]

    conteo_categoria = conteo_categoria.sort_values(
        by="Cantidad",
        ascending=False
    )

    st.dataframe(
        conteo_categoria,
        use_container_width=True
    )

    chart = (
        alt.Chart(conteo_categoria)
        .mark_bar()
        .encode(
            x=alt.X(
                "Categoria Tipo de Compra:N",
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
                alt.Tooltip("Categoria Tipo de Compra:N", title="Categoría"),
                alt.Tooltip("Cantidad:Q", title="Cantidad")
            ]
        )
        .properties(height=320)
    )

    st.altair_chart(chart, use_container_width=True)


# =========================================================
# Interfaz principal
# =========================================================

mostrar_logo()

st.markdown(
    """
    <h2 style='text-align:center; margin-bottom:0px;'>
        Limpieza ARIBA
    </h2>
    <p style='text-align:center; color:gray; margin-top:4px;'>
        Limpieza y filtrado de solicitudes de compra ARIBA
    </p>
    """,
    unsafe_allow_html=True
)

st.info(
    "La aplicación lee archivos ARIBA, limpia textos, fechas y números, "
    "filtra registros con Tipo de Compra válido, conserva solo la unidad de negocio CEN1 "
    "y crea la columna Categoria Tipo de Compra."
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

    with st.spinner("Procesando archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=bytes_archivo,
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv
        )

        df_limpio = limpiar_cache(df_original)
        df_final_limpio = filtrar_cache(df_limpio)

        diagnostico_columnas, resumen_general, resumen_fechas, resumen_num = diagnostico_cache(
            df_limpio
        )

        parquet_bytes = convertir_a_parquet_cache(df_final_limpio)
        csv_bytes = convertir_a_csv_cache(df_final_limpio)

        excel_bytes = convertir_a_excel_cache(
            df_limpio=df_limpio,
            df_filtrado=df_final_limpio,
            diagnostico_columnas=diagnostico_columnas,
            resumen_fechas=resumen_fechas,
            resumen_num=resumen_num
        )

        nombre_parquet = generar_nombre_salida("parquet")
        nombre_excel = generar_nombre_salida("xlsx")
        nombre_csv = generar_nombre_salida("csv")

    st.success("Archivo procesado correctamente.")

except Exception as e:
    st.error("No fue posible procesar el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# Métricas superiores
# =========================================================

nulos_tipo_compra = (
    df_limpio["Tipo de Compra"].isna().sum()
    if "Tipo de Compra" in df_limpio.columns
    else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Filas originales", f"{len(df_original):,}")
col2.metric("Filas limpias", f"{len(df_limpio):,}")
col3.metric("Filas CEN1", f"{len(df_final_limpio):,}")
col4.metric("Nulos Tipo Compra", f"{nulos_tipo_compra:,}")

st.divider()


# =========================================================
# Descarga rápida siempre visible
# =========================================================

st.markdown("### Descarga rápida")

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.download_button(
        label="Descargar Parquet",
        data=parquet_bytes,
        file_name=nombre_parquet,
        mime="application/octet-stream",
        use_container_width=True
    )

with col_d2:
    st.download_button(
        label="Descargar Excel",
        data=excel_bytes,
        file_name=nombre_excel,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_d3:
    st.download_button(
        label="Descargar CSV",
        data=csv_bytes,
        file_name=nombre_csv,
        mime="text/csv",
        use_container_width=True
    )

st.caption(
    "Parquet se deja como formato principal recomendado para conservar tipos de datos y trabajar con Python."
)

st.divider()


# =========================================================
# Vista Entrada
# =========================================================

if modulo == "Entrada":

    st.subheader("Entrada")

    tab1, tab2, tab3 = st.tabs([
        "Original",
        "Limpio",
        "Final CEN1"
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

    with tab3:
        st.dataframe(
            df_final_limpio.head(100),
            use_container_width=True
        )


# =========================================================
# Vista Salida
# =========================================================

elif modulo == "Salida":

    st.subheader("Salida")

    st.info(
        "Los archivos de descarga están disponibles en la sección superior. "
        "La salida principal corresponde a la base filtrada por CEN1 y Tipo de Compra válido."
    )

    st.dataframe(
        df_final_limpio.head(100),
        use_container_width=True
    )

    if "Categoria Tipo de Compra" in df_final_limpio.columns:
        st.markdown("### Resumen por categoría")
        chart_conteo_categoria(df_final_limpio)


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

    tab_a, tab_b, tab_c, tab_d, tab_e = st.tabs([
        "Nulos",
        "Tipos de dato",
        "Valores únicos",
        "Fechas",
        "Categoría"
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

    with tab_e:
        st.markdown("#### Conteo por Categoria Tipo de Compra")
        chart_conteo_categoria(df_final_limpio)
