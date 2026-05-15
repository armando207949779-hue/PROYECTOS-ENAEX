import base64
from pathlib import Path

import pandas as pd
import streamlit as st


# =========================
# Rutas
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# =========================
# Logo
# =========================

def mostrar_logo_centrado():
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
                    style="width: 220px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# =========================
# Lectura de archivo
# =========================

@st.cache_data(show_spinner="Leyendo archivo...")
def leer_archivo(archivo_bytes, nombre_archivo):
    extension = Path(nombre_archivo).suffix.lower()

    if extension == ".csv":
        return pd.read_csv(archivo_bytes)

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(archivo_bytes)

    if extension == ".parquet":
        return pd.read_parquet(archivo_bytes)

    raise ValueError("Formato no soportado. Usa CSV, XLSX, XLS o PARQUET.")


def guardar_dataframe_en_sesion(df, nombre_archivo):
    st.session_state["df_tat"] = df
    st.session_state["nombre_archivo_tat"] = nombre_archivo


def eliminar_dataframe_de_sesion():
    st.session_state.pop("df_tat", None)
    st.session_state.pop("nombre_archivo_tat", None)


# =========================
# Interfaz
# =========================

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>Cargar archivo base TAT</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 17px;'>
        Sube el archivo base una sola vez para reutilizarlo en Filtro TAT,
        Gráficos TAT y Performance de Plantas.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

archivo = st.file_uploader(
    "Selecciona el archivo base TAT",
    type=["xlsx", "xls", "csv", "parquet"],
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
