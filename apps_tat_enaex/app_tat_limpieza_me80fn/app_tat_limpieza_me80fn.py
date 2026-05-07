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
    page_title="Limpieza Transacción N°3 NME80FN",
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


def validar_columnas_requeridas(df: pd.DataFrame):
    columnas_requeridas = [
        "Documento compras",
        "Posición",
        "Fecha de documento",
        "Fecha contabiliz.",
        "Clase de operación"
    ]

    faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")


def limpiar_nme80fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Limpiar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()

    # Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how="all")

    # Eliminar columnas Unnamed vacías
    columnas_unnamed = [
        col for col in df.columns
        if str(col).startswith("Unnamed")
    ]

    for col in columnas_unnamed:
        if df[col].isna().all():
            df = df.drop(columns=[col])

    validar_columnas_requeridas(df)

    # Convertir fechas
    columnas_fecha = [
        "Fecha de entrada",
        "Fecha de documento",
        "Fecha contabiliz."
    ]

    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )

    # Convertir Clase de operación
    df["Clase de operación"] = pd.to_numeric(
        df["Clase de operación"],
        errors="coerce"
    )

    # Convertir numéricos frecuentes
    columnas_numericas = [
        "Documento compras",
        "Posición",
        "Cantidad",
        "Impte.mon.local",
        "Importe"
    ]

    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # Material puede venir como número o texto.
    # Se conserva mejor como texto para evitar perder códigos con formato.
    if "Material" in df.columns:
        df["Material"] = (
            df["Material"]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )

    # Limpiar textos
    cols_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in cols_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )

        df[col] = df[col].replace("", pd.NA)

    return df


def aplicar_logica_fechas_nme80fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    validar_columnas_requeridas(df)

    hoy = pd.Timestamp.today().normalize()

    keys = [
        "Documento compras",
        "Posición"
    ]

    # Primera fila de cada Documento compras + Posición
    final_df = (
        df
        .sort_index()
        .drop_duplicates(
            subset=keys,
            keep="first"
        )
        .copy()
    )

    # Filtrar Clase de operación = 2
    df_clase_2 = df[
        df["Clase de operación"].eq(2)
    ].copy()

    # Fecha de documento más cercana a hoy
    if not df_clase_2.empty and "Fecha de documento" in df_clase_2.columns:
        df_doc = df_clase_2.dropna(
            subset=["Fecha de documento"]
        ).copy()

        if not df_doc.empty:
            df_doc["_dist_fecha_documento"] = (
                df_doc["Fecha de documento"] - hoy
            ).abs()

            idx_fecha_documento = (
                df_doc
                .groupby(keys)["_dist_fecha_documento"]
                .idxmin()
            )

            fechas_documento = (
                df_doc
                .loc[idx_fecha_documento, keys + ["Fecha de documento"]]
                .rename(columns={
                    "Fecha de documento": "fecha_facturacion_proveedor"
                })
            )
        else:
            fechas_documento = pd.DataFrame(
                columns=keys + ["fecha_facturacion_proveedor"]
            )
    else:
        fechas_documento = pd.DataFrame(
            columns=keys + ["fecha_facturacion_proveedor"]
        )

    # Fecha contabiliz. más cercana a hoy
    if not df_clase_2.empty and "Fecha contabiliz." in df_clase_2.columns:
        df_cont = df_clase_2.dropna(
            subset=["Fecha contabiliz."]
        ).copy()

        if not df_cont.empty:
            df_cont["_dist_fecha_contabiliz"] = (
                df_cont["Fecha contabiliz."] - hoy
            ).abs()

            idx_fecha_contabiliz = (
                df_cont
                .groupby(keys)["_dist_fecha_contabiliz"]
                .idxmin()
            )

            fechas_contabiliz = (
                df_cont
                .loc[idx_fecha_contabiliz, keys + ["Fecha contabiliz."]]
                .rename(columns={
                    "Fecha contabiliz.": "fecha_entrada_mercancia_recepcion"
                })
            )
        else:
            fechas_contabiliz = pd.DataFrame(
                columns=keys + ["fecha_entrada_mercancia_recepcion"]
            )
    else:
        fechas_contabiliz = pd.DataFrame(
            columns=keys + ["fecha_entrada_mercancia_recepcion"]
        )

    # Unir fechas nuevas a la fila base
    final_df = final_df.merge(
        fechas_documento,
        on=keys,
        how="left"
    )

    final_df = final_df.merge(
        fechas_contabiliz,
        on=keys,
        how="left"
    )

    return final_df


# =========================================================
# Lectura con caché
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


@st.cache_data(show_spinner="Limpiando NME80FN...")
def limpiar_cache(df: pd.DataFrame) -> pd.DataFrame:
    return limpiar_nme80fn(df)


@st.cache_data(show_spinner="Aplicando lógica de fechas...")
def aplicar_logica_cache(df: pd.DataFrame) -> pd.DataFrame:
    return aplicar_logica_fechas_nme80fn(df)


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


@st.cache_data(show_spinner="Generando diagnóstico...")
def diagnostico_cache(df: pd.DataFrame):
    diagnostico_columnas = tabla_diagnostico_columnas(df)
    resumen_general = diagnostico_general(df)
    resumen_fechas = diagnostico_fechas(df)
    resumen_num = resumen_numerico(df)

    return diagnostico_columnas, resumen_general, resumen_fechas, resumen_num


# =========================================================
# Gráficos
# =========================================================

def chart_nulos_por_columna(diag_cols: pd.DataFrame):
    if diag_cols.empty:
        st.info("No hay columnas para graficar.")
        return

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
    if diag_cols.empty:
        st.info("No hay columnas para graficar.")
        return

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


def chart_clase_operacion(df: pd.DataFrame):
    if "Clase de operación" not in df.columns:
        st.info("No existe la columna Clase de operación.")
        return

    conteo = (
        df["Clase de operación"]
        .value_counts(dropna=False)
        .sort_index()
    )

    st.bar_chart(conteo)


# =========================================================
# Exportación
# =========================================================

def convertir_a_excel(
    df_limpio: pd.DataFrame,
    df_final: pd.DataFrame,
    diagnostico_columnas: pd.DataFrame | None = None,
    resumen_fechas: pd.DataFrame | None = None,
    resumen_num: pd.DataFrame | None = None
) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_limpio.to_excel(
            writer,
            index=False,
            sheet_name="NME80FN_Limpio"
        )

        df_final.to_excel(
            writer,
            index=False,
            sheet_name="NME80FN_Final"
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
    df_final: pd.DataFrame,
    diagnostico_columnas: pd.DataFrame,
    resumen_fechas: pd.DataFrame,
    resumen_num: pd.DataFrame
) -> bytes:
    return convertir_a_excel(
        df_limpio=df_limpio,
        df_final=df_final,
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
# Interfaz Streamlit
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Limpieza Transacción N°3 NME80FN
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube un archivo Parquet, Excel o CSV de <b>NME80FN</b>.
        La app agrupa por <b>Documento compras</b> y <b>Posición</b>,
        conserva una fila base y crea las columnas
        <b>fecha_facturacion_proveedor</b> y
        <b>fecha_entrada_mercancia_recepcion</b> usando las operaciones
        con <b>Clase de operación = 2</b>.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# Menú lateral
# =========================================================

with st.sidebar:
    pagina = st.radio(
        "Menú",
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
        "Para Parquet y Excel no se usa separador."
    )


uploaded_file = st.file_uploader(
    "Selecciona archivo NME80FN",
    type=["parquet", "xlsx", "csv"]
)


if uploaded_file is not None:
    try:
        bytes_archivo = uploaded_file.getvalue()

        df_original = leer_archivo_cache(
            bytes_archivo=bytes_archivo,
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv
        )

        df_limpio = limpiar_cache(df_original)
        df_final = aplicar_logica_cache(df_limpio)

        # =================================================
        # Vista Limpieza
        # =================================================

        if pagina == "Limpieza":
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
                "Filas finales",
                f"{len(df_final):,}"
            )

            reduccion = len(df_limpio) - len(df_final)

            col4.metric(
                "Filas agrupadas",
                f"{reduccion:,}"
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

            st.subheader("Vista previa final con columnas nuevas")

            columnas_preferidas = [
                "Documento compras",
                "Posición",
                "Centro",
                "Fecha de entrada",
                "Material",
                "Texto breve",
                "Cantidad",
                "Unidad medida pedido",
                "Impte.mon.local",
                "Moneda",
                "Importe",
                "Clase de operación",
                "Fecha de documento",
                "Fecha contabiliz.",
                "fecha_facturacion_proveedor",
                "fecha_entrada_mercancia_recepcion"
            ]

            columnas_preferidas = [
                col for col in columnas_preferidas
                if col in df_final.columns
            ]

            st.dataframe(
                df_final[columnas_preferidas].head(100),
                use_container_width=True
            )

            st.subheader("Conteo por Clase de operación")
            chart_clase_operacion(df_limpio)

            st.divider()

            st.subheader("Columnas nuevas creadas")

            st.dataframe(
                pd.DataFrame({
                    "Columna nueva": [
                        "fecha_facturacion_proveedor",
                        "fecha_entrada_mercancia_recepcion"
                    ],
                    "Origen": [
                        "Fecha de documento",
                        "Fecha contabiliz."
                    ],
                    "Regla": [
                        "Fecha más cercana a hoy dentro de Clase de operación = 2",
                        "Fecha más cercana a hoy dentro de Clase de operación = 2"
                    ]
                }),
                use_container_width=True
            )

            st.divider()

            st.subheader("Descargar resultado final")

            formato_descarga = st.radio(
                "Formato de descarga",
                options=[
                    "Excel",
                    "CSV",
                    "Parquet"
                ],
                horizontal=True
            )

            if formato_descarga == "Excel":
                diagnostico_columnas, resumen_general, resumen_fechas, resumen_num = diagnostico_cache(
                    df_final
                )

                excel_bytes = convertir_a_excel_cache(
                    df_limpio=df_limpio,
                    df_final=df_final,
                    diagnostico_columnas=diagnostico_columnas,
                    resumen_fechas=resumen_fechas,
                    resumen_num=resumen_num
                )

                st.download_button(
                    label="Descargar como Excel",
                    data=excel_bytes,
                    file_name="resultado_limpieza_transaccion_3_nme80fn.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif formato_descarga == "CSV":
                csv_bytes = convertir_a_csv_cache(df_final)

                st.download_button(
                    label="Descargar como CSV",
                    data=csv_bytes,
                    file_name="resultado_limpieza_transaccion_3_nme80fn.csv",
                    mime="text/csv"
                )

            elif formato_descarga == "Parquet":
                parquet_bytes = convertir_a_parquet_cache(df_final)

                st.download_button(
                    label="Descargar como Parquet",
                    data=parquet_bytes,
                    file_name="resultado_limpieza_transaccion_3_nme80fn.parquet",
                    mime="application/octet-stream"
                )

        # =================================================
        # Vista Diagnóstico
        # =================================================

        elif pagina == "Diagnóstico":
            diagnostico_columnas, resumen_general, resumen_fechas, resumen_num = diagnostico_cache(
                df_final
            )

            st.subheader("Diagnóstico general del resultado final")

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
            chart_tipos_dato(df_final)

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
                df_final.select_dtypes(include=["number"]).columns
            )

            if len(cols_num) == 0:
                st.info("No se encontraron columnas numéricas.")
            else:
                col_num = st.selectbox(
                    "Selecciona una columna numérica",
                    options=cols_num
                )

                chart_histograma_numerico(
                    df_final,
                    col_num
                )

                with st.expander("Ver resumen estadístico numérico"):
                    st.dataframe(
                        resumen_num,
                        use_container_width=True
                    )

            st.divider()

            st.subheader("Análisis de columnas de fecha")

            cols_fecha_detectadas = columnas_fecha(df_final)

            if len(cols_fecha_detectadas) == 0:
                st.info("No se encontraron columnas de fecha.")
            else:
                col_fecha = st.selectbox(
                    "Selecciona una columna de fecha",
                    options=cols_fecha_detectadas
                )

                chart_serie_fecha(
                    df_final,
                    col_fecha
                )

                with st.expander("Ver detalle de fechas"):
                    st.dataframe(
                        resumen_fechas,
                        use_container_width=True
                    )

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga un archivo para comenzar.")