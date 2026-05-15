from pathlib import Path

import pandas as pd
import streamlit as st


# =========================
# Configuración
# =========================

st.title("Cargar archivo base TAT")

st.markdown(
    """
    Sube el archivo base una sola vez.  
    Luego podrás cambiar entre pestañas de visualización sin volver a cargarlo.
    """
)


# =========================
# Funciones
# =========================

@st.cache_data(show_spinner="Leyendo archivo...")
def leer_archivo(uploaded_file, nombre_archivo):
    extension = Path(nombre_archivo).suffix.lower()

    if extension == ".csv":
        return pd.read_csv(uploaded_file)

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(uploaded_file)

    raise ValueError("Formato no soportado. Usa CSV, XLSX o XLS.")


def guardar_dataframe_en_sesion(df, nombre_archivo):
    st.session_state["df_tat"] = df
    st.session_state["nombre_archivo_tat"] = nombre_archivo


def eliminar_dataframe_de_sesion():
    st.session_state.pop("df_tat", None)
    st.session_state.pop("nombre_archivo_tat", None)


# =========================
# Carga de archivo
# =========================

archivo = st.file_uploader(
    "Selecciona el archivo base TAT",
    type=["xlsx", "xls", "csv"],
    key="archivo_base_tat_uploader"
)

if archivo is not None:
    try:
        df = leer_archivo(archivo, archivo.name)
        guardar_dataframe_en_sesion(df, archivo.name)

        st.success(f"Archivo cargado correctamente: {archivo.name}")

    except Exception as error:
        st.error("No se pudo cargar el archivo.")
        st.exception(error)


# =========================
# Estado actual
# =========================

st.markdown("---")

if "df_tat" not in st.session_state:
    st.warning("Todavía no hay un archivo cargado.")
    st.stop()

df_tat = st.session_state["df_tat"]
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo sin nombre")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Archivo", nombre_archivo)

with col2:
    st.metric("Filas", f"{df_tat.shape[0]:,}")

with col3:
    st.metric("Columnas", f"{df_tat.shape[1]:,}")


st.subheader("Vista previa del archivo cargado")
st.dataframe(df_tat.head(50), use_container_width=True)


st.subheader("Columnas disponibles")
st.write(list(df_tat.columns))


if st.button("Eliminar archivo cargado"):
    eliminar_dataframe_de_sesion()
    st.success("Archivo eliminado de la sesión.")
    st.rerun()
