import io
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# =========================
# Configuración Streamlit
# =========================

st.set_page_config(
    page_title="Limpieza Transacción N°1 ME5A",
    page_icon="📊",
    layout="wide"
)


# =========================
# Encabezado con logo ENAEX centrado
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
    st.warning(f"Logo no encontrado: {LOGO_PATH}")


# =========================================================
# Limpieza: fechas, números y textos
# =========================================================

def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = df.columns.astype(str).str.strip()

    df = df.dropna(axis=1, how="all")

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
    data = (
        diag_cols
        .set_index("Columna")["% Nulos"]
        .sort_values(ascending=False)
    )

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

    hist = pd.cut(
        serie,
        bins=20
    ).value_counts().sort_index()

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
        Sube un archivo Excel o CSV para aplicar limpieza sobre columnas
        de fechas, números y textos de la transacción <b>ME5A</b>.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


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
        df_original = leer_archivo(
            uploaded_file,
            separador_csv
        )

        df_limpio = limpiar_fechas_y_numeros(df_original)

        diagnostico_columnas = tabla_diagnostico_columnas(df_limpio)
        resumen_general = diagnostico_general(df_limpio)
        resumen_fechas = diagnostico_fechas(df_limpio)
        resumen_num = resumen_numerico(df_limpio)

        tab_limpieza, tab_diagnostico, tab_descarga = st.tabs([
            "Limpieza",
            "Diagnóstico",
            "Descarga"
        ])

        with tab_limpieza:
            st.success("Archivo cargado correctamente.")

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

            st.subheader("Vista previa original")
            st.dataframe(
                df_original.head(50),
                use_container_width=True
            )

            st.subheader("Vista previa limpia")
            st.dataframe(
                df_limpio.head(50),
                use_container_width=True
            )

            st.subheader("Porcentaje de nulos por columna")
            chart_nulos_por_columna(diagnostico_columnas)

            with st.expander("Ver detalle de columnas"):
                st.dataframe(
                    diagnostico_columnas,
                    use_container_width=True
                )

        with tab_diagnostico:
            st.subheader("Diagnóstico general")

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
            chart_tipos_dato(df_limpio)

            st.subheader("Top columnas con mayor porcentaje de nulos")
            chart_nulos_por_columna(
                diagnostico_columnas.head(10)
            )

            columnas_50 = diagnostico_columnas[
                diagnostico_columnas["% Nulos"] >= 50
            ]

            if columnas_50.empty:
                st.success("No hay columnas con 50% o más de nulos.")
            else:
                st.warning("Existen columnas con 50% o más de datos nulos.")
                chart_nulos_por_columna(columnas_50)

            st.subheader("Top columnas con más valores únicos")
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

                chart_serie_fecha(
                    df_limpio,
                    col_fecha
                )

                with st.expander("Ver detalle de fechas"):
                    st.dataframe(
                        resumen_fechas,
                        use_container_width=True
                    )

        with tab_descarga:
            st.subheader("Descargar resultado")

            excel_bytes = convertir_a_excel(
                df_limpio=df_limpio,
                diagnostico_columnas=diagnostico_columnas,
                resumen_fechas=resumen_fechas,
                resumen_num=resumen_num
            )

            csv_bytes = convertir_a_csv(df_limpio)

            col_a, col_b = st.columns(2)

            with col_a:
                st.download_button(
                    label="Descargar Excel completo",
                    data=excel_bytes,
                    file_name="resultado_limpieza_transaccion_1_me5a.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col_b:
                st.download_button(
                    label="Descargar CSV limpio",
                    data=csv_bytes,
                    file_name="resultado_limpieza_transaccion_1_me5a.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga un archivo para comenzar.")
