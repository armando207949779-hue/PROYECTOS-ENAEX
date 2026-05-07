import io
import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype


st.set_page_config(
    page_title="Limpieza archivo ME5A",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# Limpieza: solo fechas y números
# =========================================================

def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    cols_fecha = [
        "Fecha de solicitud",
        "Fecha modificación",
        "Fe.liber.Z",
        "Fecha de pedido",
        "Fecha de liberación"
    ]

    for col in cols_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

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
            df[col] = pd.to_numeric(df[col], errors="coerce")

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


# =========================================================
# Lectura de archivos
# =========================================================

def leer_archivo(uploaded_file, separador_csv: str) -> pd.DataFrame:
    nombre = uploaded_file.name.lower()

    if nombre.endswith(".xlsx"):
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

    raise ValueError("Formato no soportado. Usa .xlsx o .csv")


# =========================================================
# Exportación
# =========================================================

def convertir_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="limpio")

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


# =========================================================
# Diagnósticos
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
    porcentaje_nulos = round((total_nulos / total_celdas) * 100, 2) if total_celdas > 0 else 0

    duplicados = int(df.duplicated().sum())
    porcentaje_duplicados = round((duplicados / total_filas) * 100, 2) if total_filas > 0 else 0

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

    return pd.DataFrame(data)


def resumen_numerico(df: pd.DataFrame) -> pd.DataFrame:
    cols_num = df.select_dtypes(include=["number"]).columns

    if len(cols_num) == 0:
        return pd.DataFrame()

    resumen = df[cols_num].describe().T.reset_index()
    resumen = resumen.rename(columns={"index": "Columna"})

    return resumen


# =========================================================
# Gráficos nativos Streamlit
# =========================================================

def chart_nulos_por_columna(diag_cols: pd.DataFrame):
    data = diag_cols.set_index("Columna")["% Nulos"].sort_values(ascending=False)
    st.bar_chart(data)


def chart_tipos_dato(df: pd.DataFrame):
    tipos = (
        pd.Series(df.dtypes.astype(str), name="Tipo de dato")
        .value_counts()
        .sort_values(ascending=False)
    )

    st.bar_chart(tipos)


def chart_valores_unicos(diag_cols: pd.DataFrame, top_n: int = 10):
    data = (
        diag_cols
        .sort_values("Valores únicos", ascending=False)
        .head(top_n)
        .set_index("Columna")["Valores únicos"]
    )

    st.bar_chart(data)


def chart_histograma_numerico(df: pd.DataFrame, columna: str):
    serie = df[columna].dropna()

    if serie.empty:
        st.info("La columna seleccionada no tiene datos numéricos válidos.")
        return

    hist = pd.cut(serie, bins=20).value_counts().sort_index()
    hist.index = hist.index.astype(str)

    st.bar_chart(hist)


def chart_serie_fecha(df: pd.DataFrame, columna_fecha: str):
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

st.title("Limpieza archivo ME5A")
st.write(
    "Sube un archivo Excel o CSV para aplicar limpieza solo sobre columnas de fechas y números."
)

with st.sidebar:
    st.header("Configuración")

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
        "Si el CSV falla, prueba con 'Punto y coma (;)', "
        "que suele ser común en archivos exportados desde Excel/SAP."
    )


uploaded_file = st.file_uploader(
    "Selecciona archivo",
    type=["xlsx", "csv"]
)


if uploaded_file is not None:
    try:
        df_original = leer_archivo(uploaded_file, separador_csv)
        df_limpio = limpiar_fechas_y_numeros(df_original)

        tab_limpieza, tab_diagnostico = st.tabs([
            "Limpieza y descarga",
            "Diagnóstico data limpia"
        ])

        with tab_limpieza:
            st.success("Archivo cargado correctamente.")

            st.info(
                f"Archivo original: {df_original.shape[0]:,} filas "
                f"y {df_original.shape[1]:,} columnas."
            )

            st.subheader("Vista previa original")
            st.dataframe(df_original.head(), use_container_width=True)

            st.subheader("Vista previa limpia")
            st.dataframe(df_limpio.head(), use_container_width=True)

            st.subheader("Porcentaje de nulos por columna")

            diag_cols = tabla_diagnostico_columnas(df_limpio)
            chart_nulos_por_columna(diag_cols)

            with st.expander("Ver detalle de columnas"):
                st.dataframe(diag_cols, use_container_width=True)

            st.subheader("Descargar archivo limpio")

            excel_bytes = convertir_a_excel(df_limpio)
            csv_bytes = convertir_a_csv(df_limpio)

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="Descargar como Excel",
                    data=excel_bytes,
                    file_name="archivo_limpio.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col2:
                st.download_button(
                    label="Descargar como CSV",
                    data=csv_bytes,
                    file_name="archivo_limpio.csv",
                    mime="text/csv"
                )

        with tab_diagnostico:
            st.subheader("Diagnóstico general")

            resumen = diagnostico_general(df_limpio)

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Filas", f"{resumen['total_filas']:,}")
            col2.metric("Columnas", f"{resumen['total_columnas']:,}")
            col3.metric("% nulos total", f"{resumen['porcentaje_nulos']}%")
            col4.metric("% duplicados", f"{resumen['porcentaje_duplicados']}%")

            col5, col6 = st.columns(2)

            col5.metric("Celdas nulas", f"{resumen['total_nulos']:,}")
            col6.metric("Filas duplicadas", f"{resumen['duplicados']:,}")

            diag_cols = tabla_diagnostico_columnas(df_limpio)

            st.divider()

            st.subheader("Distribución de tipos de datos")
            chart_tipos_dato(df_limpio)

            st.subheader("Top columnas con mayor porcentaje de nulos")
            chart_nulos_por_columna(diag_cols.head(10))

            columnas_50 = diag_cols[diag_cols["% Nulos"] >= 50]

            if columnas_50.empty:
                st.success("No hay columnas con 50% o más de nulos.")
            else:
                st.warning("Existen columnas con 50% o más de datos nulos.")
                chart_nulos_por_columna(columnas_50)

            st.subheader("Top columnas con más valores únicos")
            chart_valores_unicos(diag_cols, top_n=10)

            st.divider()

            st.subheader("Análisis de columnas numéricas")

            cols_num = list(df_limpio.select_dtypes(include=["number"]).columns)

            if len(cols_num) == 0:
                st.info("No se encontraron columnas numéricas.")
            else:
                col_num = st.selectbox(
                    "Selecciona una columna numérica",
                    options=cols_num
                )

                chart_histograma_numerico(df_limpio, col_num)

                with st.expander("Ver resumen estadístico numérico"):
                    st.dataframe(resumen_numerico(df_limpio), use_container_width=True)

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

                chart_serie_fecha(df_limpio, col_fecha)

                with st.expander("Ver detalle de fechas"):
                    st.dataframe(diagnostico_fechas(df_limpio), use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")

else:
    st.warning("Carga un archivo para comenzar.")
