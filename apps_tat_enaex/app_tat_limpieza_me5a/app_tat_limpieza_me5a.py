# App Streamlit: Limpieza y diagnóstico de archivo ME5A con mensajes explicativos y gráficos ordenados

import io
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype


# =========================
# Ruta del logo ENAEX
# =========================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================
# Configuración Streamlit
# =========================

st.set_page_config(
    page_title="Limpieza Transacción N°1 ME5A",
    page_icon="📊",
    layout="wide"
)


# =========================
# Encabezado con logo ENAEX
# =========================

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
            margin-top: 10px;
            margin-bottom: 20px;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                style="width: 260px; display: block;"
            >
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.warning(f"Logo no encontrado en la ruta esperada: {LOGO_PATH}")


# =========================================================
# Funciones auxiliares de mensajes
# =========================================================

def mostrar_mensaje_proceso(titulo: str, descripcion: str, tipo: str = "info"):
    """
    Muestra mensajes explicativos durante el flujo de carga, limpieza,
    diagnóstico y exportación.
    """

    if tipo == "success":
        st.success(f"✅ {titulo}\n\n{descripcion}")
    elif tipo == "warning":
        st.warning(f"⚠️ {titulo}\n\n{descripcion}")
    elif tipo == "error":
        st.error(f"❌ {titulo}\n\n{descripcion}")
    else:
        st.info(f"ℹ️ {titulo}\n\n{descripcion}")


# =========================================================
# Limpieza: fechas, números y textos
# =========================================================

def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia el archivo ME5A:
    - Estandariza nombres de columnas.
    - Elimina columnas completamente vacías.
    - Limpia espacios en textos.
    - Convierte columnas de fecha.
    - Convierte columnas numéricas y enteras.
    """

    df = df.copy()

    # Limpiar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()

    # Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how="all")

    # Limpiar columnas de texto
    cols_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in cols_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )

        df[col] = df[col].replace("", pd.NA)

    # Convertir fechas estándar
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

    # Convertir fecha de entrega formato YYYYMMDD
    if "Fecha de entrega" in df.columns:
        df["Fecha de entrega"] = pd.to_datetime(
            df["Fecha de entrega"].astype("string"),
            format="%Y%m%d",
            errors="coerce"
        )

    # Convertir columnas numéricas decimales
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

    # Convertir Pedido a entero nullable
    if "Pedido" in df.columns:
        df["Pedido"] = pd.to_numeric(
            df["Pedido"],
            errors="coerce"
        ).astype("Int64")

    # Convertir columnas enteras
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


# =========================================================
# Lectura de archivos
# =========================================================

def leer_archivo(uploaded_file, separador_csv: str) -> pd.DataFrame:
    """
    Lee archivos Parquet, Excel o CSV.
    Para CSV permite separador automático, punto y coma, coma o tabulación.
    """

    nombre = uploaded_file.name.lower()

    if nombre.endswith(".parquet"):
        uploaded_file.seek(0)
        return pd.read_parquet(uploaded_file)

    if nombre.endswith(".xlsx"):
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file)

    if nombre.endswith(".csv"):
        uploaded_file.seek(0)

        if separador_csv == "Automático":
            sep = None
        elif separador_csv == "Punto y coma (;)":
            sep = ";"
        elif separador_csv == "Coma (,)":
            sep = ","
        elif separador_csv == "Tabulación":
            sep = "\t"
        else:
            sep = None

        try:
            return pd.read_csv(
                uploaded_file,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip"
            )

        except Exception:
            uploaded_file.seek(0)

            return pd.read_csv(
                uploaded_file,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


# =========================================================
# Exportación
# =========================================================

def convertir_a_excel(
    df_limpio: pd.DataFrame,
    diagnostico_columnas: pd.DataFrame,
    resumen_fechas: pd.DataFrame,
    resumen_num: pd.DataFrame
) -> bytes:
    """
    Exporta el resultado limpio y sus diagnósticos a Excel.
    """

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
    """
    Exporta el resultado limpio a CSV con codificación UTF-8.
    """

    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    """
    Exporta el resultado limpio a Parquet.
    """

    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


# =========================================================
# Diagnósticos
# =========================================================

def tabla_diagnostico_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera diagnóstico por columna:
    - Tipo de dato.
    - Cantidad de no nulos.
    - Cantidad de nulos.
    - Porcentaje de nulos.
    - Valores únicos.
    """

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
    """
    Genera métricas globales del archivo limpio.
    """

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
        "total_celdas": total_celdas,
        "total_nulos": total_nulos,
        "porcentaje_nulos": porcentaje_nulos,
        "duplicados": duplicados,
        "porcentaje_duplicados": porcentaje_duplicados
    }


def columnas_fecha(df: pd.DataFrame) -> list:
    """
    Detecta columnas con tipo fecha.
    """

    return [
        col for col in df.columns
        if is_datetime64_any_dtype(df[col])
    ]


def diagnostico_fechas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resume columnas de fecha:
    - Fecha mínima.
    - Fecha máxima.
    - Nulos.
    - Porcentaje de nulos.
    """

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

    resumen = pd.DataFrame(data)

    resumen = resumen.sort_values(
        by="% Nulos",
        ascending=False
    ).reset_index(drop=True)

    return resumen


def resumen_numerico(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera resumen estadístico de columnas numéricas.
    """

    cols_num = df.select_dtypes(include=["number"]).columns

    if len(cols_num) == 0:
        return pd.DataFrame()

    resumen = df[cols_num].describe().T.reset_index()
    resumen = resumen.rename(columns={"index": "Columna"})

    return resumen


# =========================================================
# Gráficos Streamlit ordenados de mayor a menor
# =========================================================

def chart_nulos_por_columna(diag_cols: pd.DataFrame):
    """
    Grafica porcentaje de nulos por columna.
    El gráfico se ordena de mayor a menor.
    """

    data = (
        diag_cols
        .sort_values("% Nulos", ascending=False)
        .set_index("Columna")["% Nulos"]
    )

    st.bar_chart(data)


def chart_tipos_dato(df: pd.DataFrame):
    """
    Grafica cantidad de columnas por tipo de dato.
    El gráfico se ordena de mayor a menor.
    """

    tipos = (
        pd.Series(df.dtypes.astype(str), name="Tipo de dato")
        .value_counts()
        .sort_values(ascending=False)
    )

    st.bar_chart(tipos)


def chart_valores_unicos(diag_cols: pd.DataFrame, top_n: int = 10):
    """
    Grafica las columnas con más valores únicos.
    El gráfico se ordena de mayor a menor.
    """

    data = (
        diag_cols
        .sort_values("Valores únicos", ascending=False)
        .head(top_n)
        .set_index("Columna")["Valores únicos"]
    )

    st.bar_chart(data)


def chart_histograma_numerico(df: pd.DataFrame, columna: str):
    """
    Grafica distribución de una columna numérica.
    Los intervalos se muestran en orden natural.
    """

    serie = df[columna].dropna()

    if serie.empty:
        st.info("La columna seleccionada no tiene datos numéricos válidos.")
        return

    hist = pd.cut(
        serie,
        bins=20
    ).value_counts().sort_index()

    hist.index = hist.index.astype(str)

    st.bar_chart(hist)


def chart_serie_fecha(df: pd.DataFrame, columna_fecha: str):
    """
    Grafica cantidad de registros por fecha.
    La serie se ordena cronológicamente.
    """

    data = (
        df[columna_fecha]
        .dropna()
        .dt.date
        .value_counts()
        .sort_index()
    )

    if data.empty:
        st.info("La columna seleccionada no tiene fechas válidas.")
        return

    st.line_chart(data)


# =========================================================
# Interfaz Streamlit
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Limpieza Transacción N°1 ME5A
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Esta aplicación permite cargar un archivo de la transacción <b>ME5A</b>,
        limpiar columnas de texto, fechas y números, diagnosticar la calidad de datos
        y descargar el resultado procesado.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.header("Configuración")

    vista_sidebar = st.radio(
        "Vista",
        options=[
            "Limpieza",
            "Diagnóstico"
        ],
        index=0
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

    st.caption(
        "Esta opción solo aplica para archivos CSV. "
        "Para archivos Parquet y Excel no se utiliza separador."
    )


uploaded_file = st.file_uploader(
    "Selecciona archivo",
    type=["parquet", "xlsx", "csv"]
)


if uploaded_file is not None:
    try:
        mostrar_mensaje_proceso(
            titulo="Archivo recibido",
            descripcion=(
                f"Se cargó el archivo `{uploaded_file.name}`. "
                "Ahora se realizará la lectura según su formato."
            ),
            tipo="info"
        )

        with st.spinner("Leyendo archivo..."):
            df_original = leer_archivo(
                uploaded_file,
                separador_csv
            )

        mostrar_mensaje_proceso(
            titulo="Lectura completada",
            descripcion=(
                f"El archivo fue leído correctamente. "
                f"Contiene {len(df_original):,} filas y {df_original.shape[1]:,} columnas antes de la limpieza."
            ),
            tipo="success"
        )

        mostrar_mensaje_proceso(
            titulo="Proceso de limpieza iniciado",
            descripcion=(
                "Se limpiarán nombres de columnas, textos vacíos, columnas completamente nulas, "
                "fechas, números y campos enteros relevantes para ME5A."
            ),
            tipo="info"
        )

        with st.spinner("Limpiando datos..."):
            df_limpio = limpiar_fechas_y_numeros(df_original)

        columnas_eliminadas = df_original.shape[1] - df_limpio.shape[1]

        mostrar_mensaje_proceso(
            titulo="Limpieza completada",
            descripcion=(
                f"El archivo limpio contiene {len(df_limpio):,} filas y {df_limpio.shape[1]:,} columnas. "
                f"Se eliminaron {columnas_eliminadas:,} columnas completamente vacías."
            ),
            tipo="success"
        )

        mostrar_mensaje_proceso(
            titulo="Diagnóstico de calidad de datos",
            descripcion=(
                "Se calcularán métricas generales, porcentaje de nulos por columna, "
                "tipos de datos, valores únicos, fechas y resumen numérico."
            ),
            tipo="info"
        )

        with st.spinner("Generando diagnósticos..."):
            diagnostico_columnas = tabla_diagnostico_columnas(df_limpio)
            resumen_general = diagnostico_general(df_limpio)
            resumen_fechas = diagnostico_fechas(df_limpio)
            resumen_num = resumen_numerico(df_limpio)

        mostrar_mensaje_proceso(
            titulo="Diagnóstico completado",
            descripcion=(
                f"El archivo limpio tiene {resumen_general['porcentaje_nulos']}% de celdas nulas "
                f"y {resumen_general['porcentaje_duplicados']}% de filas duplicadas."
            ),
            tipo="success"
        )

        # =================================================
        # Vista Limpieza
        # =================================================

        if vista_sidebar == "Limpieza":

            tab_limpieza, = st.tabs([
                "Limpieza"
            ])

            with tab_limpieza:
                st.subheader("Resumen del proceso de limpieza")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Filas originales",
                    f"{len(df_original):,}"
                )

                col2.metric(
                    "Columnas originales",
                    f"{df_original.shape[1]:,}"
                )

                col3.metric(
                    "Filas limpias",
                    f"{len(df_limpio):,}"
                )

                col4.metric(
                    "Columnas limpias",
                    f"{df_limpio.shape[1]:,}"
                )

                st.info(
                    "En esta sección se compara la base original con la base limpia. "
                    "La limpieza no elimina filas, pero sí puede eliminar columnas completamente vacías "
                    "y corregir formatos de texto, fecha y número."
                )

                st.subheader("Vista previa original")
                st.caption(
                    "Primeras 50 filas del archivo tal como fue cargado, antes de aplicar limpieza."
                )
                st.dataframe(
                    df_original.head(50),
                    use_container_width=True
                )

                st.subheader("Vista previa limpia")
                st.caption(
                    "Primeras 50 filas después de limpiar columnas, textos, fechas y números."
                )
                st.dataframe(
                    df_limpio.head(50),
                    use_container_width=True
                )

                st.subheader("Porcentaje de nulos por columna")
                st.caption(
                    "El gráfico está ordenado de mayor a menor porcentaje de nulos."
                )
                chart_nulos_por_columna(diagnostico_columnas)

                with st.expander("Ver detalle de columnas"):
                    st.dataframe(
                        diagnostico_columnas,
                        use_container_width=True
                    )

                st.divider()

                st.subheader("Descargar resultado limpio")

                st.info(
                    "El archivo puede descargarse en Excel, CSV o Parquet. "
                    "El Excel incluye la data limpia y hojas adicionales de diagnóstico."
                )

                with st.spinner("Preparando archivos de descarga..."):
                    excel_bytes = convertir_a_excel(
                        df_limpio=df_limpio,
                        diagnostico_columnas=diagnostico_columnas,
                        resumen_fechas=resumen_fechas,
                        resumen_num=resumen_num
                    )

                    csv_bytes = convertir_a_csv(df_limpio)
                    parquet_bytes = convertir_a_parquet(df_limpio)

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.download_button(
                        label="Descargar como Excel",
                        data=excel_bytes,
                        file_name="resultado_limpieza_transaccion_1_me5a.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col_b:
                    st.download_button(
                        label="Descargar como CSV",
                        data=csv_bytes,
                        file_name="resultado_limpieza_transaccion_1_me5a.csv",
                        mime="text/csv"
                    )

                with col_c:
                    st.download_button(
                        label="Descargar como Parquet",
                        data=parquet_bytes,
                        file_name="resultado_limpieza_transaccion_1_me5a.parquet",
                        mime="application/octet-stream"
                    )

        # =================================================
        # Vista Diagnóstico
        # =================================================

        elif vista_sidebar == "Diagnóstico":
            st.subheader("Diagnóstico general")

            st.info(
                "Esta vista resume la calidad general del archivo limpio. "
                "Permite identificar nulos, duplicados, tipos de datos, columnas críticas "
                "y comportamiento de variables numéricas o de fecha."
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Filas",
                f"{resumen_general['total_filas']:,}"
            )

            col2.metric(
                "Columnas",
                f"{resumen_general['total_columnas']:,}"
            )

            col3.metric(
                "% nulos total",
                f"{resumen_general['porcentaje_nulos']}%"
            )

            col4.metric(
                "% duplicados",
                f"{resumen_general['porcentaje_duplicados']}%"
            )

            col5, col6 = st.columns(2)

            col5.metric(
                "Celdas nulas",
                f"{resumen_general['total_nulos']:,}"
            )

            col6.metric(
                "Filas duplicadas",
                f"{resumen_general['duplicados']:,}"
            )

            st.divider()

            st.subheader("Distribución de tipos de datos")
            st.caption(
                "Cantidad de columnas por tipo de dato, ordenadas de mayor a menor."
            )
            chart_tipos_dato(df_limpio)

            st.subheader("Top columnas con mayor porcentaje de nulos")
            st.caption(
                "Se muestran las columnas con mayor proporción de datos faltantes."
            )
            chart_nulos_por_columna(
                diagnostico_columnas.head(10)
            )

            columnas_50 = diagnostico_columnas[
                diagnostico_columnas["% Nulos"] >= 50
            ]

            if columnas_50.empty:
                st.success("No hay columnas con 50% o más de datos nulos.")
            else:
                st.warning(
                    "Existen columnas con 50% o más de datos nulos. "
                    "Se recomienda revisar si estas columnas deben mantenerse, eliminarse o completarse."
                )

                st.caption(
                    "Columnas críticas ordenadas de mayor a menor porcentaje de nulos."
                )
                chart_nulos_por_columna(columnas_50)

            st.subheader("Top columnas con más valores únicos")
            st.caption(
                "Este gráfico ayuda a identificar columnas con alta cardinalidad, "
                "como códigos, documentos, materiales o textos descriptivos."
            )
            chart_valores_unicos(
                diagnostico_columnas,
                top_n=10
            )

            st.divider()

            st.subheader("Análisis de columnas numéricas")

            cols_num = list(
                df_limpio.select_dtypes(include=["number"]).columns
            )

            if len(cols_num) == 0:
                st.info("No se encontraron columnas numéricas.")
            else:
                col_num = st.selectbox(
                    "Selecciona una columna numérica",
                    options=cols_num
                )

                st.caption(
                    f"Distribución de la columna numérica `{col_num}` mediante intervalos."
                )

                chart_histograma_numerico(
                    df_limpio,
                    col_num
                )

                with st.expander("Ver resumen estadístico numérico"):
                    st.dataframe(
                        resumen_num,
                        use_container_width=True
                    )

            st.divider()

            st.subheader("Análisis de columnas de fecha")

            cols_fecha_detectadas = columnas_fecha(df_limpio)

            if len(cols_fecha_detectadas) == 0:
                st.info("No se encontraron columnas de fecha.")
            else:
                col_fecha = st.selectbox(
                    "Selecciona una columna de fecha",
                    options=cols_fecha_detectadas
                )

                st.caption(
                    f"Cantidad de registros por día para la columna `{col_fecha}`."
                )

                chart_serie_fecha(
                    df_limpio,
                    col_fecha
                )

                with st.expander("Ver detalle de fechas"):
                    st.dataframe(
                        resumen_fechas,
                        use_container_width=True
                    )

    except Exception as e:
        mostrar_mensaje_proceso(
            titulo="Error en el procesamiento",
            descripcion=(
                "Ocurrió un problema al leer, limpiar o diagnosticar el archivo. "
                "Revisa el formato del archivo, el separador CSV o los nombres de columnas."
            ),
            tipo="error"
        )
        st.exception(e)

else:
    st.warning("Carga un archivo para comenzar.")
