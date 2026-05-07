import io
import os
import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype


# =========================================================
# Configuración general
# =========================================================

st.set_page_config(
    page_title="Transacción 2 Ariba",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# Logo
# =========================================================

# Usa aquí la misma ruta de la imagen que tenías en tu otro código
LOGO_PATH = r"C:\Users\Usuario\Downloads\logo.png"


def mostrar_logo_y_titulo():
    """
    Muestra el logo y el título principal.
    """
    if os.path.exists(LOGO_PATH):
        with st.sidebar:
            st.image(LOGO_PATH, use_container_width=True)

        col_logo, col_titulo = st.columns([1, 5])

        with col_logo:
            st.image(LOGO_PATH, width=120)

        with col_titulo:
            st.title("Transacción 2 Ariba")
    else:
        st.title("Transacción 2 Ariba")
        st.sidebar.warning("No se encontró el logo en la ruta indicada.")


# =========================================================
# Lectura del archivo
# =========================================================

def leer_excel_data_desde_b14(uploaded_file) -> pd.DataFrame:
    """
    Lee la hoja Data desde fila 14 como encabezado y elimina columna A.
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

    # Eliminar columnas tipo Unnamed si están vacías
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
            df[col] = pd.to_numeric(df[col], errors="coerce")

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

    df["Tipo de Compra Categoria"] = (
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

    return diagnostico.sort_values(
        by="% Nulos",
        ascending=False
    ).reset_index(drop=True)


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

    if not cols:
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

    return (
        df[cols_num]
        .describe()
        .T
        .reset_index()
        .rename(columns={"index": "Columna"})
    )


# =========================================================
# Gráficos Streamlit
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


def chart_conteo_categoria(df_filtrado: pd.DataFrame):
    if "Tipo de Compra Categoria" not in df_filtrado.columns:
        st.info("No existe la columna Tipo de Compra Categoria.")
        return

    conteo_categoria = (
        df_filtrado["Tipo de Compra Categoria"]
        .value_counts(dropna=False)
        .reset_index()
    )

    conteo_categoria.columns = [
        "Tipo de Compra Categoria",
        "Cantidad"
    ]

    st.dataframe(conteo_categoria, use_container_width=True)

    st.bar_chart(
        conteo_categoria
        .set_index("Tipo de Compra Categoria")["Cantidad"]
    )


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
# Exportación
# =========================================================

def convertir_a_excel(df_limpio: pd.DataFrame, df_filtrado: pd.DataFrame) -> bytes:
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
            sheet_name="CEN1_Filtrado"
        )

        if "Tipo de Compra Categoria" in df_filtrado.columns:
            conteo_categoria = (
                df_filtrado["Tipo de Compra Categoria"]
                .value_counts(dropna=False)
                .reset_index()
            )

            conteo_categoria.columns = [
                "Tipo de Compra Categoria",
                "Cantidad"
            ]

            conteo_categoria.to_excel(
                writer,
                index=False,
                sheet_name="Conteo_Categoria"
            )

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


# =========================================================
# Interfaz Streamlit
# =========================================================

mostrar_logo_y_titulo()

st.write(
    "Sube el archivo Excel. La app leerá la hoja **Data** desde **B14**, "
    "estandarizará fechas y números, excluirá nulos en **Tipo de Compra**, "
    "dejará solo **ID de unidad de negocio = CEN1** y creará la columna "
    "**Tipo de Compra Categoria**."
)

with st.sidebar:
    st.header("Configuración")

    st.caption(
        "El archivo debe ser Excel `.xlsx` y debe contener la hoja **Data**. "
        "La lectura inicia desde B14."
    )

    mostrar_vistas_originales = st.checkbox(
        "Mostrar vistas previas",
        value=True
    )

    top_n_unicos = st.slider(
        "Top columnas con más valores únicos",
        min_value=5,
        max_value=30,
        value=10,
        step=5
    )


uploaded_file = st.file_uploader(
    "Selecciona archivo Excel",
    type=["xlsx"]
)


if uploaded_file is not None:
    try:
        df_original = leer_excel_data_desde_b14(uploaded_file)
        df_limpio = limpiar_fechas_y_numeros(df_original)
        df_filtrado = aplicar_filtros_y_categoria(df_limpio)

        tab_limpieza, tab_diagnostico = st.tabs([
            "Limpieza y descarga",
            "Diagnóstico"
        ])

        with tab_limpieza:
            st.success("Archivo procesado correctamente.")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Filas originales", f"{len(df_original):,}")
            col2.metric("Filas limpias", f"{len(df_limpio):,}")
            col3.metric("Filas CEN1 filtradas", f"{len(df_filtrado):,}")

            nulos_tipo_compra = (
                df_limpio["Tipo de Compra"].isna().sum()
                if "Tipo de Compra" in df_limpio.columns
                else 0
            )

            col4.metric("Nulos Tipo de Compra", f"{nulos_tipo_compra:,}")

            if mostrar_vistas_originales:
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

                st.subheader("Vista previa filtrada CEN1")
                st.dataframe(
                    df_filtrado.head(100),
                    use_container_width=True
                )

            st.subheader("Conteo por Tipo de Compra Categoria")
            chart_conteo_categoria(df_filtrado)

            st.subheader("Descargar resultado")

            excel_bytes = convertir_a_excel(df_limpio, df_filtrado)
            csv_bytes = convertir_a_csv(df_filtrado)

            col_a, col_b = st.columns(2)

            with col_a:
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="resultado_limpio_filtrado_CEN1.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col_b:
                st.download_button(
                    label="Descargar CSV filtrado",
                    data=csv_bytes,
                    file_name="resultado_filtrado_CEN1.csv",
                    mime="text/csv"
                )

        with tab_diagnostico:
            st.subheader("Diagnóstico general data limpia")

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

            st.subheader("Detalle de columnas")
            st.dataframe(diag_cols, use_container_width=True)

            st.subheader("Porcentaje de nulos por columna")
            chart_nulos_por_columna(diag_cols)

            st.subheader("Distribución de tipos de dato")
            chart_tipos_dato(df_limpio)

            st.subheader("Top columnas con más valores únicos")
            chart_valores_unicos(diag_cols, top_n=top_n_unicos)

            columnas_50 = diag_cols[diag_cols["% Nulos"] >= 50]

            if columnas_50.empty:
                st.success("No hay columnas con 50% o más de nulos.")
            else:
                st.warning("Existen columnas con 50% o más de datos nulos.")
                chart_nulos_por_columna(columnas_50)

            st.divider()

            st.subheader("Resumen numérico")

            resumen_num = resumen_numerico(df_limpio)

            if resumen_num.empty:
                st.info("No se encontraron columnas numéricas.")
            else:
                st.dataframe(resumen_num, use_container_width=True)

                cols_num = list(df_limpio.select_dtypes(include=["number"]).columns)

                col_num = st.selectbox(
                    "Selecciona una columna numérica",
                    options=cols_num
                )

                chart_histograma_numerico(df_limpio, col_num)

            st.divider()

            st.subheader("Resumen de fechas")

            resumen_fechas = diagnostico_fechas(df_limpio)

            if resumen_fechas.empty:
                st.info("No se encontraron columnas de fecha.")
            else:
                st.dataframe(resumen_fechas, use_container_width=True)

                cols_fecha_detectadas = columnas_fecha(df_limpio)

                col_fecha = st.selectbox(
                    "Selecciona una columna de fecha",
                    options=cols_fecha_detectadas
                )

                chart_serie_fecha(df_limpio, col_fecha)

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga un archivo Excel para comenzar.")
