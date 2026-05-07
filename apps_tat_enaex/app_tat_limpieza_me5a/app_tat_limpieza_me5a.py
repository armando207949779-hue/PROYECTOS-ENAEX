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
        df["Pedido"] = pd.to_numeric(df["Pedido"], errors="coerce").astype("Int64")

    cols_enteras = [
        "Solicitud de pedido",
        "Pos.solicitud pedido",
        "Posición de pedido"
    ]

    for col in cols_enteras:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    return df


def leer_archivo(uploaded_file) -> pd.DataFrame:
    nombre = uploaded_file.name.lower()

    if nombre.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)

    if nombre.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    raise ValueError("Formato no soportado. Usa .xlsx o .csv")


def convertir_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="limpio")

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


st.title("Limpieza archivo ME5A")
st.write("Sube un archivo Excel o CSV para aplicar limpieza de fechas y números.")

uploaded_file = st.file_uploader(
    "Selecciona archivo",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:
    try:
        df_original = leer_archivo(uploaded_file)

        st.subheader("Vista previa original")
        st.dataframe(df_original.head(), use_container_width=True)

        st.info(f"Archivo cargado con {df_original.shape[0]:,} filas y {df_original.shape[1]:,} columnas.")

        df_limpio = limpiar_fechas_y_numeros(df_original)

        st.subheader("Vista previa limpia")
        st.dataframe(df_limpio.head(), use_container_width=True)

        st.subheader("Tipos de datos después de limpieza")

        info_df = pd.DataFrame({
            "Columna": df_limpio.columns,
            "Tipo de dato": [str(dtype) for dtype in df_limpio.dtypes],
            "No nulos": df_limpio.notna().sum().values,
            "Nulos": df_limpio.isna().sum().values
        })

        st.dataframe(info_df, use_container_width=True)

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

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")

else:
    st.warning("Carga un archivo para comenzar.")