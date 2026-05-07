import io
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Limpieza archivo ME5A",
    page_icon="📊",
    layout="wide"
)


def limpiar_fechas_y_numeros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica solo transformaciones de fechas y números.
    No modifica nombres de columnas ni textos.
    """

    df = df.copy()

    # =========================
    # 1. Transformar fechas
    # =========================

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

    # Fecha de entrega viene como entero tipo 20240101
    if "Fecha de entrega" in df.columns:
        df["Fecha de entrega"] = pd.to_datetime(
            df["Fecha de entrega"].astype("string"),
            format="%Y%m%d",
            errors="coerce"
        )

    # =========================
    # 2. Transformar números
    # =========================

    cols_numericas = [
        "Cantidad solicitada",
        "Precio de valoración"
    ]

    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Pedido como entero nullable para evitar notación científica
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


def leer_archivo(uploaded_file, separador_csv: str) -> pd.DataFrame:
    """
    Lee archivos Excel o CSV.
    Para CSV permite elegir separador y omitir líneas problemáticas.
    """

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


def convertir_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="limpio")

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def tabla_diagnostico_columnas(df: pd.DataFrame) -> pd.DataFrame:
    total_filas = len(df)

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


def diagnostico_numerico(df: pd.DataFrame) -> pd.DataFrame:
    cols_num = df.select_dtypes(include=["number"]).columns

    if len(cols_num) == 0:
        return pd.DataFrame()

    resumen = df[cols_num].describe().T.reset_index()
    resumen = resumen.rename(columns={"index": "Columna"})

    return resumen


def diagnostico_fechas(df: pd.DataFrame) -> pd.DataFrame:
    cols_fecha = df.select_dtypes(include=["datetime64[ns]", "datetime64[us]"]).columns

    if len(cols_fecha) == 0:
        return pd.DataFrame()

    data = []

    for col in cols_fecha:
        data.append({
            "Columna": col,
            "Fecha mínima": df[col].min(),
            "Fecha máxima": df[col].max(),
            "Nulos": df[col].isna().sum(),
            "% Nulos": round(df[col].isna().mean() * 100, 2)
        })

    return pd.DataFrame(data)


def columnas_con_muchos_nulos(df: pd.DataFrame, umbral: float = 50) -> pd.DataFrame:
    diag = tabla_diagnostico_columnas(df)
    return diag[diag["% Nulos"] >= umbral]


# =========================
# Interfaz Streamlit
# =========================

st.title("Limpieza archivo ME5A")
st.write(
    "Sube un archivo Excel o CSV para aplicar limpieza solo sobre "
    "columnas de fechas y números."
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

            st.subheader("Tipos de datos y nulos")

            info_df = tabla_diagnostico_columnas(df_limpio)

            st.dataframe(
                info_df,
                use_container_width=True
            )

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

            st.subheader("Columnas con mayor porcentaje de nulos")

            diag_cols = tabla_diagnostico_columnas(df_limpio)

            st.dataframe(
                diag_cols[["Columna", "Tipo de dato", "Nulos", "% Nulos", "Valores únicos"]],
                use_container_width=True
            )

            st.subheader("Columnas con más de 50% de nulos")

            cols_muchos_nulos = columnas_con_muchos_nulos(df_limpio, umbral=50)

            if cols_muchos_nulos.empty:
                st.success("No hay columnas con 50% o más de nulos.")
            else:
                st.warning("Estas columnas tienen 50% o más de datos nulos.")
                st.dataframe(cols_muchos_nulos, use_container_width=True)

            st.subheader("Diagnóstico de columnas numéricas")

            diag_num = diagnostico_numerico(df_limpio)

            if diag_num.empty:
                st.info("No se encontraron columnas numéricas.")
            else:
                st.dataframe(diag_num, use_container_width=True)

            st.subheader("Diagnóstico de columnas de fecha")

            diag_fecha = diagnostico_fechas(df_limpio)

            if diag_fecha.empty:
                st.info("No se encontraron columnas de fecha.")
            else:
                st.dataframe(diag_fecha, use_container_width=True)

            st.subheader("Distribución de tipos de datos")

            tipos_df = (
                pd.DataFrame(df_limpio.dtypes.astype(str), columns=["Tipo de dato"])
                .reset_index()
                .rename(columns={"index": "Columna"})
                .groupby("Tipo de dato")
                .size()
                .reset_index(name="Cantidad de columnas")
            )

            st.dataframe(tipos_df, use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")

else:
    st.warning("Carga un archivo para comenzar.")
