# App Streamlit: Limpieza minimalista NME80FN con entrada, salida, descarga Parquet y análisis opcional

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
    page_title="Limpieza NME80FN",
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
# Limpieza NME80FN
# =========================================================

def limpiar_nme80fn(df: pd.DataFrame) -> pd.DataFrame:
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

    validar_columnas_requeridas(df)

    # Conversión de fechas
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

    # Conversión de clase de operación
    df["Clase de operación"] = pd.to_numeric(
        df["Clase de operación"],
        errors="coerce"
    )

    # Conversión de columnas numéricas
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

    # Limpieza especial de material
    if "Material" in df.columns:
        df["Material"] = (
            df["Material"]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
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


def aplicar_logica_fechas_nme80fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    validar_columnas_requeridas(df)

    hoy = pd.Timestamp.today().normalize()
    keys = ["Documento compras", "Posición"]

    # Una fila base por Documento compras + Posición
    final_df = (
        df
        .sort_index()
        .drop_duplicates(
            subset=keys,
            keep="first"
        )
        .copy()
    )

    # Se trabaja solo con clase de operación 2
    df_clase_2 = df[
        df["Clase de operación"].eq(2)
    ].copy()

    if not df_clase_2.empty:

        # Fecha de facturación proveedor:
        # Fecha de documento más cercana a hoy dentro de clase 2
        df_doc = df_clase_2.dropna(
            subset=["Fecha de documento"]
        ).copy()

        if not df_doc.empty:
            df_doc["_dist_fecha_documento"] = (
                df_doc["Fecha de documento"] - hoy
            ).abs()

            idx_doc = (
                df_doc
                .groupby(keys)["_dist_fecha_documento"]
                .idxmin()
            )

            fechas_documento = (
                df_doc
                .loc[idx_doc, keys + ["Fecha de documento"]]
                .rename(columns={
                    "Fecha de documento": "fecha_facturacion_proveedor"
                })
            )
        else:
            fechas_documento = pd.DataFrame(
                columns=keys + ["fecha_facturacion_proveedor"]
            )

        # Fecha de recepción:
        # Fecha contabiliz. más cercana a hoy dentro de clase 2
        df_cont = df_clase_2.dropna(
            subset=["Fecha contabiliz."]
        ).copy()

        if not df_cont.empty:
            df_cont["_dist_fecha_contabiliz"] = (
                df_cont["Fecha contabiliz."] - hoy
            ).abs()

            idx_cont = (
                df_cont
                .groupby(keys)["_dist_fecha_contabiliz"]
                .idxmin()
            )

            fechas_contabiliz = (
                df_cont
                .loc[idx_cont, keys + ["Fecha contabiliz."]]
                .rename(columns={
                    "Fecha contabiliz.": "fecha_entrada_mercancia_recepcion"
                })
            )
        else:
            fechas_contabiliz = pd.DataFrame(
                columns=keys + ["fecha_entrada_mercancia_recepcion"]
            )

    else:
        fechas_documento = pd.DataFrame(
            columns=keys + ["fecha_facturacion_proveedor"]
        )

        fechas_contabiliz = pd.DataFrame(
            columns=keys + ["fecha_entrada_mercancia_recepcion"]
        )

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


@st.cache_data(show_spinner="Limpiando archivo...")
def limpiar_cache(df: pd.DataFrame) -> pd.DataFrame:
    return limpiar_nme80fn(df)


@st.cache_data(show_spinner="Aplicando lógica de fechas...")
def aplicar_logica_cache(df: pd.DataFrame) -> pd.DataFrame:
    return aplicar_logica_fechas_nme80fn(df)


# =========================================================
# Diagnóstico
# =========================================================

def diagnostico_general_liviano(df: pd.DataFrame) -> dict:
    total_filas = len(df)
    total_columnas = len(df.columns)
    total_celdas = total_filas * total_columnas

    total_nulos = int(df.isna().sum().sum())

    porcentaje_nulos = (
        round(total_nulos / total_celdas * 100, 2)
        if total_celdas > 0
        else 0
    )

    duplicados = int(df.duplicated().sum())

    porcentaje_duplicados = (
        round(duplicados / total_filas * 100, 2)
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


def tabla_diagnostico_columnas_liviana(df: pd.DataFrame) -> pd.DataFrame:
    total_filas = len(df)

    diag = pd.DataFrame({
        "Columna": df.columns,
        "Tipo de dato": [str(dtype) for dtype in df.dtypes],
        "No nulos": df.notna().sum().values,
        "Nulos": df.isna().sum().values,
    })

    if total_filas > 0:
        diag["% Nulos"] = (
            diag["Nulos"] / total_filas * 100
        ).round(2)
    else:
        diag["% Nulos"] = 0

    return (
        diag
        .sort_values("% Nulos", ascending=False)
        .reset_index(drop=True)
    )


def columnas_fecha_detectadas(df: pd.DataFrame) -> list:
    return [
        col for col in df.columns
        if is_datetime64_any_dtype(df[col])
    ]


@st.cache_data(show_spinner="Generando diagnóstico...")
def diagnostico_cache(df: pd.DataFrame):
    diag_general = diagnostico_general_liviano(df)
    diag_columnas = tabla_diagnostico_columnas_liviana(df)

    return diag_general, diag_columnas


# =========================================================
# Exportación
# =========================================================

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


def convertir_a_excel_seguro(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="NME80FN_Final"
        )

    return output.getvalue()


@st.cache_data(show_spinner="Preparando CSV...")
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner="Preparando Parquet...")
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner="Preparando Excel...")
def convertir_a_excel_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_excel_seguro(df)


# =========================================================
# Gráficos Altair
# =========================================================

def chart_nulos_por_columna(diag_columnas: pd.DataFrame, top_n: int | None = None):
    if diag_columnas.empty:
        st.info("No hay columnas para graficar.")
        return

    data = (
        diag_columnas[["Columna", "% Nulos"]]
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


def chart_conteo_clase_operacion(df: pd.DataFrame):
    if "Clase de operación" not in df.columns:
        st.info("No existe la columna Clase de operación.")
        return

    data = (
        df["Clase de operación"]
        .value_counts(dropna=False)
        .reset_index()
    )

    data.columns = ["Clase de operación", "Cantidad"]
    data["Clase de operación"] = data["Clase de operación"].astype("string")

    data = data.sort_values(
        by="Cantidad",
        ascending=False
    )

    st.dataframe(
        data,
        use_container_width=True
    )

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Clase de operación:N",
                sort=alt.SortField(
                    field="Cantidad",
                    order="descending"
                ),
                title="Clase de operación"
            ),
            y=alt.Y(
                "Cantidad:Q",
                title="Cantidad"
            ),
            tooltip=[
                alt.Tooltip("Clase de operación:N", title="Clase de operación"),
                alt.Tooltip("Cantidad:Q", title="Cantidad")
            ]
        )
        .properties(height=320)
    )

    st.altair_chart(chart, use_container_width=True)


def chart_fechas_generadas(df: pd.DataFrame):
    columnas = [
        "fecha_facturacion_proveedor",
        "fecha_entrada_mercancia_recepcion"
    ]

    data = []

    for col in columnas:
        if col in df.columns:
            data.append({
                "Columna": col,
                "Fechas generadas": int(df[col].notna().sum()),
                "Fechas faltantes": int(df[col].isna().sum())
            })

    if not data:
        st.info("No existen columnas de fechas generadas.")
        return

    resumen = pd.DataFrame(data)

    resumen_melt = resumen.melt(
        id_vars="Columna",
        value_vars=[
            "Fechas generadas",
            "Fechas faltantes"
        ],
        var_name="Estado",
        value_name="Cantidad"
    )

    st.dataframe(
        resumen,
        use_container_width=True
    )

    chart = (
        alt.Chart(resumen_melt)
        .mark_bar()
        .encode(
            x=alt.X(
                "Columna:N",
                title=None
            ),
            y=alt.Y(
                "Cantidad:Q",
                title="Cantidad"
            ),
            color=alt.Color(
                "Estado:N",
                title="Estado"
            ),
            tooltip=[
                alt.Tooltip("Columna:N", title="Columna"),
                alt.Tooltip("Estado:N", title="Estado"),
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
        Limpieza NME80FN
    </h2>
    <p style='text-align:center; color:gray; margin-top:4px;'>
        Limpieza y generación de fechas finales para historial de pedidos
    </p>
    """,
    unsafe_allow_html=True
)

st.info(
    "La aplicación limpia archivos NME80FN, valida columnas clave, agrupa por Documento compras y Posición, "
    "y genera las fechas finales de facturación proveedor y recepción usando registros con Clase de operación = 2."
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
    "Cargar archivo NME80FN",
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
        df_final = aplicar_logica_cache(df_limpio)

        diag_general, diag_columnas = diagnostico_cache(df_final)

        parquet_bytes = convertir_a_parquet_cache(df_final)
        csv_bytes = convertir_a_csv_cache(df_final)

        limite_excel = 250_000
        excel_disponible = len(df_final) <= limite_excel

        if excel_disponible:
            excel_bytes = convertir_a_excel_cache(df_final)
        else:
            excel_bytes = None

    st.success("Archivo procesado correctamente.")

except Exception as e:
    st.error("No fue posible procesar el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# Métricas superiores
# =========================================================

filas_agrupadas = len(df_limpio) - len(df_final)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Filas originales", f"{len(df_original):,}")
col2.metric("Filas limpias", f"{len(df_limpio):,}")
col3.metric("Filas finales", f"{len(df_final):,}")
col4.metric("Filas agrupadas", f"{filas_agrupadas:,}")

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
        file_name="nme80fn_final.parquet",
        mime="application/octet-stream",
        use_container_width=True
    )

with col_d2:
    st.download_button(
        label="Descargar CSV",
        data=csv_bytes,
        file_name="nme80fn_final.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_d3:
    if excel_disponible:
        st.download_button(
            label="Descargar Excel",
            data=excel_bytes,
            file_name="nme80fn_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.button(
            "Excel no disponible",
            disabled=True,
            use_container_width=True
        )

st.caption(
    "Parquet se deja como formato principal recomendado para conservar tipos de datos y trabajar con Python. "
    "Excel se limita a 250.000 filas para evitar problemas de rendimiento."
)

st.divider()


# =========================================================
# Columnas preferidas para visualización
# =========================================================

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


# =========================================================
# Vista Entrada
# =========================================================

if modulo == "Entrada":

    st.subheader("Entrada")

    tab1, tab2, tab3 = st.tabs([
        "Original",
        "Limpio",
        "Final"
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
            df_final[columnas_preferidas].head(100),
            use_container_width=True
        )


# =========================================================
# Vista Salida
# =========================================================

elif modulo == "Salida":

    st.subheader("Salida")

    st.info(
        "Los archivos de descarga están disponibles en la sección superior. "
        "La salida principal corresponde a una fila por Documento compras y Posición, "
        "con fechas finales de facturación proveedor y recepción."
    )

    st.dataframe(
        df_final[columnas_preferidas].head(100),
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
        f"{diag_general['porcentaje_nulos']}%"
    )

    col2.metric(
        "Celdas nulas",
        f"{diag_general['total_nulos']:,}"
    )

    col3.metric(
        "% duplicados",
        f"{diag_general['porcentaje_duplicados']}%"
    )

    col4.metric(
        "Filas duplicadas",
        f"{diag_general['duplicados']:,}"
    )

    tab_a, tab_b, tab_c, tab_d = st.tabs([
        "Nulos",
        "Tipos de dato",
        "Clase operación",
        "Fechas generadas"
    ])

    with tab_a:
        st.markdown("#### Porcentaje de nulos por columna")
        chart_nulos_por_columna(
            diag_columnas,
            top_n=20
        )

        with st.expander("Ver tabla de diagnóstico"):
            st.dataframe(
                diag_columnas,
                use_container_width=True
            )

    with tab_b:
        st.markdown("#### Distribución de tipos de dato")
        chart_tipos_dato(df_final)

    with tab_c:
        st.markdown("#### Conteo por Clase de operación")
        chart_conteo_clase_operacion(df_limpio)

    with tab_d:
        st.markdown("#### Cobertura de fechas generadas")
        chart_fechas_generadas(df_final)

        fechas = columnas_fecha_detectadas(df_final)

        with st.expander("Ver columnas de fecha detectadas"):
            if fechas:
                st.write(fechas)
            else:
                st.info("No se encontraron columnas de fecha.")
