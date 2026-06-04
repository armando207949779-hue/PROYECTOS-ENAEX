# ============================================================
# APP_CARGAR_ARCHIVO.py
# 01_CARGA_ARCHIVOS
# Carga, validación y visualización de archivos seleccionados
# ============================================================

from pathlib import Path
import base64
import time
from io import BytesIO

import pandas as pd
import streamlit as st


# ============================================================
# Rutas del proyecto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="01_CARGA_ARCHIVOS",
    page_icon="📁",
    layout="wide"
)


# ============================================================
# Archivos esperados
# ============================================================

ARCHIVOS_ESPERADOS = {
    "df_moneda_cambio": "01_BD_Moneda_Cambio.xlsx",
    "df_ordenes": "02_Ordenes.csv",
    "df_gasto_contratos": "03_Gasto_Contratos.csv",
    "df_centros": "04_Centros.csv",
    "df_bbdd_x_categoria": "05_BBDD_X_Categoria_BD.csv",
    "df_catalogo_categorias": "06_BD_Catalogo_Categorias.csv",
    "df_plan_ahorro_gestores": "07_BD_Plan_Ahorro_Gestores.csv",
    "df_registro_contratos": "08_BD_Registro_Contratos.csv",
    "df_hitos": "09_BD_Hitos.csv",
    "df_categorias": "10_BD_Categorias.csv",
    "df_me5a": "11_ME5A.csv",
}


# ============================================================
# Logo
# ============================================================

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
                    style="width: 260px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# Funciones auxiliares
# ============================================================

def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace(" ", "_", regex=False)
        .str.replace("\ufeff", "", regex=False)
    )

    return df


def leer_csv_robusto(uploaded_file) -> tuple[pd.DataFrame, dict]:
    contenido = uploaded_file.getvalue()

    encodings = ["utf-8-sig", "latin1", "cp1252", "ISO-8859-1"]
    separadores = [",", ";", "\t", "|"]

    mejor_df = None
    mejor_config = None
    mejor_score = -1

    for encoding in encodings:
        for sep in separadores:
            try:
                temp = pd.read_csv(
                    BytesIO(contenido),
                    encoding=encoding,
                    sep=sep,
                    engine="python",
                    quotechar='"',
                    on_bad_lines="skip"
                )

                score = temp.shape[0] * temp.shape[1]

                if temp.shape[1] > 1 and score > mejor_score:
                    mejor_df = temp.copy()
                    mejor_config = {
                        "encoding": encoding,
                        "separador": sep
                    }
                    mejor_score = score

            except Exception:
                continue

    if mejor_df is None:
        raise ValueError(f"No se pudo leer correctamente el archivo CSV: {uploaded_file.name}")

    mejor_df = mejor_df.dropna(axis=1, how="all")
    mejor_df = limpiar_columnas(mejor_df)

    return mejor_df, mejor_config


def leer_excel(uploaded_file) -> tuple[pd.DataFrame, dict]:
    contenido = uploaded_file.getvalue()

    df = pd.read_excel(BytesIO(contenido))
    df = df.dropna(axis=1, how="all")
    df = limpiar_columnas(df)

    config = {
        "encoding": "No aplica",
        "separador": "No aplica"
    }

    return df, config


def cargar_archivo(uploaded_file) -> tuple[pd.DataFrame, dict]:
    nombre = uploaded_file.name
    extension = Path(nombre).suffix.lower()

    if extension == ".csv":
        return leer_csv_robusto(uploaded_file)

    if extension in [".xlsx", ".xls"]:
        return leer_excel(uploaded_file)

    raise ValueError(f"Formato no soportado: {nombre}")


def mostrar_resumen_dataframe(nombre_df: str, df: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Filas", f"{df.shape[0]:,}")

    with col2:
        st.metric("Columnas", f"{df.shape[1]:,}")

    with col3:
        memoria_mb = df.memory_usage(deep=True).sum() / 1024**2
        st.metric("Memoria estimada", f"{memoria_mb:.2f} MB")

    st.dataframe(df.head(30), use_container_width=True)

    with st.expander("Columnas y tipos de datos", expanded=False):
        df_tipos = pd.DataFrame({
            "Columna": df.columns,
            "Tipo": df.dtypes.astype(str).values,
            "Nulos": df.isna().sum().values,
            "Nulos_%": (df.isna().mean().values * 100).round(2),
        })

        st.dataframe(df_tipos, use_container_width=True)


def construir_validacion_archivos(archivos_dict: dict) -> pd.DataFrame:
    registros = []

    for nombre_df, nombre_archivo in ARCHIVOS_ESPERADOS.items():
        existe = nombre_archivo in archivos_dict

        peso_kb = None
        if existe:
            peso_kb = round(archivos_dict[nombre_archivo].size / 1024, 2)

        registros.append({
            "dataframe": nombre_df,
            "archivo": nombre_archivo,
            "estado": "Encontrado" if existe else "Faltante",
            "existe": existe,
            "peso_kb": peso_kb,
        })

    return pd.DataFrame(registros)


# ============================================================
# Estado de sesión
# ============================================================

if "archivos_subidos" not in st.session_state:
    st.session_state["archivos_subidos"] = {}

if "archivos_confirmados" not in st.session_state:
    st.session_state["archivos_confirmados"] = False

if "dataframes_cargados" not in st.session_state:
    st.session_state["dataframes_cargados"] = {}

if "config_carga" not in st.session_state:
    st.session_state["config_carga"] = {}

if "df_validacion_archivos" not in st.session_state:
    st.session_state["df_validacion_archivos"] = pd.DataFrame()

if "carga_completada" not in st.session_state:
    st.session_state["carga_completada"] = False


# ============================================================
# Interfaz principal
# ============================================================

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>01_CARGA_ARCHIVOS</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 17px;'>
        Carga, validación y visualización preliminar de las bases del dashboard de contratos.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# ============================================================
# 1. Selección de archivos
# ============================================================

st.subheader("1. Selección de archivos")

st.info(
    """
    Selecciona los archivos desde la carpeta local del dashboard.
    En la ventana de selección, entra a la carpeta y selecciona todos los archivos requeridos.
    """
)

archivos_seleccionados = st.file_uploader(
    "Seleccionar archivos",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True
)

col_confirmar, col_limpiar = st.columns([1, 1])

with col_confirmar:
    confirmar_archivos = st.button(
        "Confirmar archivos seleccionados",
        type="primary",
        use_container_width=True
    )

with col_limpiar:
    limpiar_sesion = st.button(
        "Limpiar carga",
        use_container_width=True
    )

if limpiar_sesion:
    st.session_state["archivos_subidos"] = {}
    st.session_state["archivos_confirmados"] = False
    st.session_state["dataframes_cargados"] = {}
    st.session_state["config_carga"] = {}
    st.session_state["df_validacion_archivos"] = pd.DataFrame()
    st.session_state["carga_completada"] = False
    st.success("Carga limpiada correctamente.")
    st.rerun()

if confirmar_archivos:
    if not archivos_seleccionados:
        st.error("No se seleccionaron archivos.")
    else:
        archivos_dict = {
            archivo.name: archivo
            for archivo in archivos_seleccionados
        }

        st.session_state["archivos_subidos"] = archivos_dict
        st.session_state["archivos_confirmados"] = True
        st.session_state["carga_completada"] = False

        df_validacion = construir_validacion_archivos(archivos_dict)
        st.session_state["df_validacion_archivos"] = df_validacion

        st.success("Archivos seleccionados confirmados correctamente.")


# ============================================================
# 2. Validación de archivos subidos
# ============================================================

st.subheader("2. Validación de archivos subidos")

if not st.session_state["archivos_confirmados"]:
    st.warning("Primero debes seleccionar y confirmar los archivos.")
    st.stop()

df_validacion = st.session_state["df_validacion_archivos"]

st.dataframe(
    df_validacion[
        [
            "dataframe",
            "archivo",
            "estado",
            "peso_kb",
        ]
    ],
    use_container_width=True
)

total_archivos = len(df_validacion)
archivos_encontrados = int(df_validacion["existe"].sum())
archivos_faltantes = total_archivos - archivos_encontrados
peso_total_kb = df_validacion["peso_kb"].fillna(0).sum()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Archivos esperados", total_archivos)

with col2:
    st.metric("Archivos encontrados", archivos_encontrados)

with col3:
    st.metric("Archivos faltantes", archivos_faltantes)

with col4:
    st.metric("Peso total", f"{peso_total_kb / 1024:.2f} MB")

if archivos_faltantes > 0:
    st.warning("Existen archivos faltantes. Puedes cargar los disponibles, pero algunos módulos podrían fallar.")
else:
    st.success("Todos los archivos esperados fueron encontrados.")


# ============================================================
# 3. Botón de carga de archivos
# ============================================================

st.subheader("3. Carga de archivos")

cargar_bases = st.button(
    "Cargar archivos",
    type="primary",
    use_container_width=True
)

if cargar_bases:
    archivos_subidos = st.session_state["archivos_subidos"]

    dataframes_cargados = {}
    config_carga = {}
    errores_carga = []

    archivos_disponibles = [
        (nombre_df, nombre_archivo)
        for nombre_df, nombre_archivo in ARCHIVOS_ESPERADOS.items()
        if nombre_archivo in archivos_subidos
    ]

    total_disponibles = len(archivos_disponibles)

    if total_disponibles == 0:
        st.error("No hay archivos disponibles para cargar.")
        st.stop()

    progress_bar = st.progress(0)
    estado_carga = st.empty()

    for i, (nombre_df, nombre_archivo) in enumerate(archivos_disponibles, start=1):
        archivo = archivos_subidos[nombre_archivo]

        estado_carga.info(f"Cargando {nombre_archivo} ({i}/{total_disponibles})...")

        try:
            df, config = cargar_archivo(archivo)

            dataframes_cargados[nombre_df] = df

            config_carga[nombre_df] = {
                "archivo": nombre_archivo,
                "filas": df.shape[0],
                "columnas": df.shape[1],
                "encoding": config.get("encoding"),
                "separador": config.get("separador"),
            }

        except Exception as e:
            errores_carga.append({
                "dataframe": nombre_df,
                "archivo": nombre_archivo,
                "error": str(e),
            })

        progress_bar.progress(i / total_disponibles)
        time.sleep(0.05)

    st.session_state["dataframes_cargados"] = dataframes_cargados
    st.session_state["config_carga"] = config_carga
    st.session_state["carga_completada"] = True

    estado_carga.empty()

    if dataframes_cargados:
        st.success(f"Archivos cargados correctamente. Se cargaron {len(dataframes_cargados)} DataFrames.")

    if errores_carga:
        st.error("Algunos archivos no pudieron cargarse.")
        st.dataframe(pd.DataFrame(errores_carga), use_container_width=True)


# ============================================================
# 4. Resumen general de carga
# ============================================================

st.subheader("4. Resumen general de DataFrames cargados")

dataframes_cargados = st.session_state["dataframes_cargados"]
config_carga = st.session_state["config_carga"]

if not dataframes_cargados:
    st.info("Presiona **Cargar archivos** para crear los DataFrames.")
else:
    df_resumen_carga = pd.DataFrame.from_dict(
        config_carga,
        orient="index"
    ).reset_index()

    df_resumen_carga = df_resumen_carga.rename(
        columns={"index": "dataframe"}
    )

    st.dataframe(df_resumen_carga, use_container_width=True)

    total_filas = sum(df.shape[0] for df in dataframes_cargados.values())
    total_columnas = sum(df.shape[1] for df in dataframes_cargados.values())
    total_memoria = sum(
        df.memory_usage(deep=True).sum() / 1024**2
        for df in dataframes_cargados.values()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total filas cargadas", f"{total_filas:,}")

    with col2:
        st.metric("Total columnas cargadas", f"{total_columnas:,}")

    with col3:
        st.metric("Memoria total estimada", f"{total_memoria:.2f} MB")


# ============================================================
# 5. Vista previa de DataFrames
# ============================================================

st.subheader("5. Vista previa de DataFrames")

if not dataframes_cargados:
    st.info("Los DataFrames aparecerán aquí después de cargarlos.")
else:
    st.success("Vista previa disponible para validar visualmente la carga de cada DataFrame.")

    mostrar_vistas = st.checkbox(
        "Mostrar vistas previas de todos los DataFrames",
        value=True
    )

    if mostrar_vistas:
        for nombre_df, df in dataframes_cargados.items():
            with st.expander(f"{nombre_df} | {df.shape[0]:,} filas x {df.shape[1]:,} columnas", expanded=True):
                mostrar_resumen_dataframe(nombre_df, df)


# ============================================================
# 6. Uso en otros módulos
# ============================================================

st.subheader("6. Uso de bases en otros módulos")

st.info(
    """
    Los DataFrames cargados quedan disponibles en memoria de sesión:

    `st.session_state["dataframes_cargados"]`

    Ejemplo:

    `df_ordenes = st.session_state["dataframes_cargados"]["df_ordenes"]`
    """
)
