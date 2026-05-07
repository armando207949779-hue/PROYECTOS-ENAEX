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

# app.py está dentro de apps_tat_enaex.
# Subimos un nivel hasta la raíz del repo: proyectos-enaex
ROOT_DIR = BASE_DIR.parent

# Ruta correcta:
# proyectos-enaex/assets/logo.svg
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================
# Configuración Streamlit
# =========================

st.set_page_config(
    page_title="Limpieza Transacción N°2 ARIBA",
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
    st.error(f"Logo no encontrado en ruta correcta: {LOGO_PATH}")


# =========================================================
# Lectura del archivo
# =========================================================

def leer_excel_data_desde_b14(uploaded_file) -> pd.DataFrame:
    """
    Lee hoja Data desde fila 14 como encabezado y elimina columna A.
    Equivale a empezar desde B14.
    """
    df = pd.read_excel(
        uploaded_file,
        sheet_name="Data",
        header=13
    )

    # Empezar desde columna B
    df = df.iloc[:, 1:].copy()

    return df


# =========================================================
# Limpieza y transformación
# =========================================================

def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Limpiar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()

    # Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how="all")

    # Eliminar columnas tipo Unnamed si están vacías o no aportan
    columnas_unnamed = [
        col for col in df.columns
        if col.startswith("Unnamed")
    ]

    for col in columnas_unnamed:
        if df[col].isna().all():
            df = df.drop(columns=[col])

    # Convertir fechas
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

    # Convertir numéricos
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

    # Tipo de Compra como entero nullable
    if "Tipo de Compra" in df.columns:
        df["Tipo de Compra"] = df["Tipo de Compra"].astype("Int64")

    # Número de línea como entero nullable
    if "Número de línea de la solicitud de compra" in df.columns:
        df["Número de línea de la solicitud de compra"] = (
            df["Número de línea de la solicitud de compra"]
            .astype("Int64")
        )

    # Limpiar textos
    cols_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in cols_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )

        # Convertir strings vacíos en nulos reales
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

    # Dejar solo CEN1
    df = df[
        df["ID de unidad de negocio"]
        .astype("string")
        .str.strip()
        .eq("CEN1")
    ].copy()

    # Crear columna categoría
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

    st.dataframe(
        conteo_categoria,
        use_container_width=True
    )

    st.bar_chart(
        conteo_categoria
        .set_index("Categoria Tipo de Compra")["Cantidad"]
    )


# =========================================================
# Exportación
# =========================================================

def convertir_a_excel(
    df_limpio: pd.DataFrame,
    df_filtrado: pd.DataFrame,
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

        df_filtrado.to_excel(
            writer,
            index=False,
            sheet_name="Final_Limpio_CEN1"
        )

        diagnostico_columnas.to_excel(
            writer,
            index=False,
            sheet_name="Diagnostico_Columnas"
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
# Interfaz Streamlit
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Limpieza Transacción N°2 ARIBA
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube el archivo Excel. La app leerá la hoja <b>Data</b> desde <b>B14</b>,
        estandarizará fechas y números, excluirá nulos en <b>Tipo de Compra</b>,
        dejará solo <b>ID de unidad de negocio = CEN1</b> y creará la columna
        <b>Categoria Tipo de Compra</b>.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


uploaded_file = st.file_uploader(
    "Selecciona archivo Excel",
    type=["xlsx"]
)


if uploaded_file is not None:
    try:
        df_original = leer_excel_data_desde_b14(uploaded_file)
        df_limpio = limpiar_fechas_y_numeros(df_original)
        df_final_limpio = aplicar_filtros_y_categoria(df_limpio)

        diagnostico_columnas = tabla_diagnostico_columnas(df_limpio)
        resumen_general = diagnostico_general(df_limpio)
        resumen_fechas = diagnostico_fechas(df_limpio)
        resumen_num = resumen_numerico(df_limpio)

        tab_limpieza, tab_diagnostico, tab_descarga = st.tabs([
            "Limpieza",
            "Diagnóstico",
            "Descarga"
        ])

        # =================================================
        # Tab limpieza
        # =================================================

        with tab_limpieza:
            st.success("Archivo procesado correctamente.")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Filas originales",
                f"{len(df_original):,}"
            )

            col2.metric(
                "Filas data limpia",
                f"{len(df_limpio):,}"
            )

            col3.metric(
                "Filas final limpio",
                f"{len(df_final_limpio):,}"
            )

            nulos_tipo_compra = (
                df_limpio["Tipo de Compra"].isna().sum()
                if "Tipo de Compra" in df_limpio.columns
                else 0
            )

            col4.metric(
                "Nulos Tipo de Compra",
                f"{nulos_tipo_compra:,}"
            )

            st.subheader("Vista previa original")
            st.dataframe(
                df_original.head(50),
                use_container_width=True
            )

            st.subheader("Vista previa final limpio")
            st.dataframe(
                df_final_limpio.head(100),
                use_container_width=True
            )

            st.subheader("Conteo por Categoria Tipo de Compra")
            chart_conteo_categoria(df_final_limpio)

        # =================================================
        # Tab diagnóstico
        # =================================================

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

            st.subheader("Detalle de columnas")
            st.dataframe(
                diagnostico_columnas,
                use_container_width=True
            )

            st.subheader("Porcentaje de nulos por columna")
            chart_nulos_por_columna(diagnostico_columnas)

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

        # =================================================
        # Tab descarga
        # =================================================

        with tab_descarga:
            st.subheader("Descargar resultado")

            excel_bytes = convertir_a_excel(
                df_limpio=df_limpio,
                df_filtrado=df_final_limpio,
                diagnostico_columnas=diagnostico_columnas,
                resumen_fechas=resumen_fechas,
                resumen_num=resumen_num
            )

            csv_bytes = convertir_a_csv(df_final_limpio)

            col_a, col_b = st.columns(2)

            with col_a:
                st.download_button(
                    label="Descargar Excel completo",
                    data=excel_bytes,
                    file_name="resultado_limpieza_transaccion_2_ariba.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col_b:
                st.download_button(
                    label="Descargar CSV final limpio",
                    data=csv_bytes,
                    file_name="resultado_limpieza_transaccion_2_ariba_final.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga un archivo Excel para comenzar.")
