import io
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype


# =========================================================
# Rutas del proyecto
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# =========================================================
# Configuración Streamlit
# =========================================================

st.set_page_config(
    page_title="Limpieza Transacción N°2 Ariba",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# Encabezado con logo centrado
# =========================================================

def mostrar_logo():
    if LOGO_PATH.exists():
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")
        logo_base64 = base64.b64encode(
            logo_svg.encode("utf-8")
        ).decode("utf-8")

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
# Lectura del archivo
# =========================================================

def leer_excel_data_desde_b14(uploaded_file) -> pd.DataFrame:
    """
    Lee la hoja Data desde la fila 14 como encabezado.
    Luego elimina la columna A para comenzar desde B14.
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
# Limpieza de fechas, números y textos
# =========================================================

def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Limpiar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()

    # Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how="all")

    # Eliminar columnas Unnamed si están completamente vacías
    columnas_unnamed = [
        col for col in df.columns
        if col.startswith("Unnamed")
    ]

    for col in columnas_unnamed:
        if df[col].isna().all():
            df = df.drop(columns=[col])

    # Estandarizar textos
    cols_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in cols_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )

        # Convertir strings vacíos en nulos reales
        df[col] = df[col].replace("", pd.NA)

    # Estandarizar fechas
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

    # Estandarizar columnas numéricas
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

    # Convertir enteros a Int64 nullable
    if "Tipo de Compra" in df.columns:
        df["Tipo de Compra"] = df["Tipo de Compra"].astype("Int64")

    if "Número de línea de la solicitud de compra" in df.columns:
        df["Número de línea de la solicitud de compra"] = (
            df["Número de línea de la solicitud de compra"]
            .astype("Int64")
        )

    return df


# =========================================================
# Filtro CEN1 y categoría Tipo de Compra
# =========================================================

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

    # Dejar solo ID de unidad de negocio = CEN1
    df = df[
        df["ID de unidad de negocio"]
        .astype("string")
        .str.strip()
        .eq("CEN1")
    ].copy()

    # Crear categoría de Tipo de Compra
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
# Exportación
# =========================================================

def convertir_a_excel(
    df_limpio: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    conteo_categoria: pd.DataFrame,
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
            sheet_name="CEN1_Filtrado"
        )

        conteo_categoria.to_excel(
            writer,
            index=False,
            sheet_name="Conteo_Categoria"
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
# App Streamlit
# =========================================================

mostrar_logo()

st.markdown(
    """
    <h1 style='text-align: center;'>
        Limpieza Transacción N°2 Ariba
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube el archivo Excel. La app leerá la hoja <b>Data</b> desde <b>B14</b>,
        estandarizará fechas y números, excluirá nulos en <b>Tipo de Compra</b>,
        filtrará solo <b>CEN1</b> y creará la columna
        <b>Tipo de Compra Categoria</b>.
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
        df_filtrado = aplicar_filtros_y_categoria(df_limpio)

        conteo_categoria = (
            df_filtrado["Tipo de Compra Categoria"]
            .value_counts(dropna=False)
            .reset_index()
        )

        conteo_categoria.columns = [
            "Tipo de Compra Categoria",
            "Cantidad"
        ]

        diagnostico_columnas = tabla_diagnostico_columnas(df_limpio)
        resumen_general = diagnostico_general(df_limpio)
        resumen_fechas = diagnostico_fechas(df_limpio)
        resumen_num = resumen_numerico(df_limpio)

        tab_limpieza, tab_diagnostico, tab_descarga = st.tabs([
            "Limpieza y filtro",
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
                "Filas limpias",
                f"{len(df_limpio):,}"
            )

            col3.metric(
                "Filas CEN1 filtradas",
                f"{len(df_filtrado):,}"
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

            st.subheader("Conteo por Tipo de Compra Categoria")

            st.dataframe(
                conteo_categoria,
                use_container_width=True
            )

            if not conteo_categoria.empty:
                st.bar_chart(
                    conteo_categoria.set_index(
                        "Tipo de Compra Categoria"
                    )["Cantidad"]
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

            st.subheader("Vista previa filtrada CEN1")
            st.dataframe(
                df_filtrado.head(100),
                use_container_width=True
            )

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

            st.subheader("Porcentaje de nulos por columna")

            st.bar_chart(
                diagnostico_columnas
                .set_index("Columna")["% Nulos"]
                .sort_values(ascending=False)
            )

            with st.expander("Ver detalle de columnas"):
                st.dataframe(
                    diagnostico_columnas,
                    use_container_width=True
                )

            st.subheader("Distribución de tipos de datos")

            tipos = (
                pd.Series(
                    df_limpio.dtypes.astype(str),
                    name="Tipo de dato"
                )
                .value_counts()
                .sort_values(ascending=False)
            )

            st.bar_chart(tipos)

            st.subheader("Resumen numérico")

            if resumen_num.empty:
                st.info("No se encontraron columnas numéricas.")
            else:
                st.dataframe(
                    resumen_num,
                    use_container_width=True
                )

            st.subheader("Resumen de fechas")

            if resumen_fechas.empty:
                st.info("No se encontraron columnas de fecha.")
            else:
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
                df_filtrado=df_filtrado,
                conteo_categoria=conteo_categoria,
                diagnostico_columnas=diagnostico_columnas,
                resumen_fechas=resumen_fechas,
                resumen_num=resumen_num
            )

            csv_bytes = convertir_a_csv(df_filtrado)

            col_a, col_b = st.columns(2)

            with col_a:
                st.download_button(
                    label="Descargar Excel completo",
                    data=excel_bytes,
                    file_name="resultado_limpio_filtrado_CEN1.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col_b:
                st.download_button(
                    label="Descargar CSV filtrado CEN1",
                    data=csv_bytes,
                    file_name="resultado_filtrado_CEN1.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga un archivo Excel para comenzar.")
