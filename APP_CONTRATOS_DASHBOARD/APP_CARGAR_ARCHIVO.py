# ============================================================
# 01_CARGA_ARCHIVOS
# App Streamlit para cargar, validar y visualizar bases locales
# ============================================================

from pathlib import Path

import pandas as pd
import streamlit as st


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


def leer_csv_robusto(ruta: Path) -> tuple[pd.DataFrame, dict]:
    encodings = ["utf-8-sig", "latin1", "cp1252", "ISO-8859-1"]
    separadores = [",", ";", "\t", "|"]

    mejor_df = None
    mejor_config = None
    mejor_score = -1

    for encoding in encodings:
        for sep in separadores:
            try:
                temp = pd.read_csv(
                    ruta,
                    encoding=encoding,
                    sep=sep,
                    engine="python",
                    quotechar='"',
                    on_bad_lines="skip"
                )

                score = temp.shape[0] * temp.shape[1]

                if score > mejor_score and temp.shape[1] > 1:
                    mejor_df = temp.copy()
                    mejor_config = {
                        "encoding": encoding,
                        "separador": sep,
                    }
                    mejor_score = score

            except Exception:
                continue

    if mejor_df is None:
        raise ValueError(f"No se pudo leer correctamente el archivo CSV: {ruta.name}")

    mejor_df = mejor_df.dropna(axis=1, how="all")
    mejor_df = limpiar_columnas(mejor_df)

    return mejor_df, mejor_config


def leer_excel(ruta: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_excel(ruta)
    df = df.dropna(axis=1, how="all")
    df = limpiar_columnas(df)

    config = {
        "encoding": "No aplica",
        "separador": "No aplica",
    }

    return df, config


@st.cache_data(show_spinner=False)
def cargar_archivo(ruta_str: str) -> tuple[pd.DataFrame, dict]:
    ruta = Path(ruta_str)
    extension = ruta.suffix.lower()

    if extension == ".csv":
        return leer_csv_robusto(ruta)

    if extension in [".xlsx", ".xls"]:
        return leer_excel(ruta)

    raise ValueError(f"Formato no soportado: {ruta.name}")


def obtener_info_archivo(ruta: Path) -> dict:
    if not ruta.exists():
        return {
            "archivo": ruta.name,
            "existe": False,
            "peso_kb": None,
            "ruta": str(ruta),
        }

    return {
        "archivo": ruta.name,
        "existe": True,
        "peso_kb": round(ruta.stat().st_size / 1024, 2),
        "ruta": str(ruta),
    }


def mostrar_resumen_dataframe(nombre_df: str, df: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Filas", f"{df.shape[0]:,}")

    with col2:
        st.metric("Columnas", f"{df.shape[1]:,}")

    with col3:
        memoria_mb = df.memory_usage(deep=True).sum() / 1024**2
        st.metric("Memoria estimada", f"{memoria_mb:.2f} MB")

    with st.expander(f"Columnas de {nombre_df}", expanded=False):
        st.write(df.columns.tolist())

    with st.expander(f"Vista previa de {nombre_df}", expanded=True):
        st.dataframe(df.head(50), use_container_width=True)

    with st.expander(f"Tipos de datos de {nombre_df}", expanded=False):
        df_tipos = pd.DataFrame({
            "Columna": df.columns,
            "Tipo": df.dtypes.astype(str).values,
            "Nulos": df.isna().sum().values,
            "Nulos_%": (df.isna().mean().values * 100).round(2),
        })

        st.dataframe(df_tipos, use_container_width=True)


# ============================================================
# Interfaz principal
# ============================================================

st.markdown(
    "<h1 style='text-align: center;'>01_CARGA_ARCHIVOS</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 17px;'>
        Carga, validación y visualización preliminar de las bases del dashboard.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# ============================================================
# 1. Selección de carpeta
# ============================================================

st.subheader("1. Selección de carpeta")

ruta_default = r"C:\Users\enrique.brun.aep\Downloads\BBDD_DASHBOARD_MONITOREO_CONTRATOS"

ruta_carpeta_input = st.text_input(
    "Ruta de la carpeta que contiene las bases",
    value=ruta_default
)

ruta_carpeta = Path(ruta_carpeta_input)

if not ruta_carpeta.exists():
    st.error(f"La carpeta no existe: {ruta_carpeta}")
    st.stop()

if not ruta_carpeta.is_dir():
    st.error(f"La ruta ingresada no corresponde a una carpeta: {ruta_carpeta}")
    st.stop()

st.success(f"Carpeta encontrada: {ruta_carpeta}")


# ============================================================
# 2. Validación de archivos
# ============================================================

st.subheader("2. Validación de archivos esperados")

registros_archivos = []

for nombre_df, archivo in ARCHIVOS_ESPERADOS.items():
    ruta_archivo = ruta_carpeta / archivo
    info = obtener_info_archivo(ruta_archivo)
    info["dataframe"] = nombre_df
    registros_archivos.append(info)

df_validacion = pd.DataFrame(registros_archivos)

df_validacion["estado"] = df_validacion["existe"].map({
    True: "Encontrado",
    False: "Faltante",
})

st.dataframe(
    df_validacion[
        [
            "dataframe",
            "archivo",
            "estado",
            "peso_kb",
            "ruta",
        ]
    ],
    use_container_width=True
)

total_archivos = len(df_validacion)
archivos_encontrados = int(df_validacion["existe"].sum())
archivos_faltantes = total_archivos - archivos_encontrados

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Archivos esperados", total_archivos)

with col2:
    st.metric("Archivos encontrados", archivos_encontrados)

with col3:
    st.metric("Archivos faltantes", archivos_faltantes)

if archivos_faltantes > 0:
    st.warning("Existen archivos faltantes. Puedes cargar los disponibles, pero algunos módulos podrían fallar.")


# ============================================================
# 3. Carga de archivos
# ============================================================

st.subheader("3. Carga de bases")

if "dataframes_cargados" not in st.session_state:
    st.session_state["dataframes_cargados"] = {}

if "config_carga" not in st.session_state:
    st.session_state["config_carga"] = {}

if st.button("Cargar bases disponibles", type="primary"):
    dataframes_cargados = {}
    config_carga = {}
    errores_carga = []

    with st.spinner("Cargando archivos..."):
        for nombre_df, archivo in ARCHIVOS_ESPERADOS.items():
            ruta_archivo = ruta_carpeta / archivo

            if not ruta_archivo.exists():
                continue

            try:
                df, config = cargar_archivo(str(ruta_archivo))

                dataframes_cargados[nombre_df] = df
                config_carga[nombre_df] = {
                    "archivo": archivo,
                    "filas": df.shape[0],
                    "columnas": df.shape[1],
                    "encoding": config.get("encoding"),
                    "separador": config.get("separador"),
                }

            except Exception as e:
                errores_carga.append({
                    "dataframe": nombre_df,
                    "archivo": archivo,
                    "error": str(e),
                })

    st.session_state["dataframes_cargados"] = dataframes_cargados
    st.session_state["config_carga"] = config_carga

    if dataframes_cargados:
        st.success(f"Se cargaron {len(dataframes_cargados)} bases correctamente.")

    if errores_carga:
        st.error("Algunos archivos no pudieron cargarse.")
        st.dataframe(pd.DataFrame(errores_carga), use_container_width=True)


# ============================================================
# 4. Resumen general de carga
# ============================================================

st.subheader("4. Resumen de bases cargadas")

dataframes_cargados = st.session_state.get("dataframes_cargados", {})
config_carga = st.session_state.get("config_carga", {})

if not dataframes_cargados:
    st.info("Todavía no hay bases cargadas.")
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
# 5. Visualización opcional
# ============================================================

st.subheader("5. Visualización opcional de contenido")

if not dataframes_cargados:
    st.info("Carga las bases para visualizar su contenido.")
else:
    nombre_seleccionado = st.selectbox(
        "Selecciona un DataFrame",
        options=list(dataframes_cargados.keys())
    )

    df_seleccionado = dataframes_cargados[nombre_seleccionado]

    st.markdown(f"### `{nombre_seleccionado}`")

    mostrar_resumen_dataframe(nombre_seleccionado, df_seleccionado)


# ============================================================
# 6. Acceso desde otras pestañas
# ============================================================

st.subheader("6. Uso en otros módulos")

st.info(
    """
    Los DataFrames cargados quedan disponibles en:

    `st.session_state["dataframes_cargados"]`

    Ejemplo:

    `df_ordenes = st.session_state["dataframes_cargados"]["df_ordenes"]`
    """
)
