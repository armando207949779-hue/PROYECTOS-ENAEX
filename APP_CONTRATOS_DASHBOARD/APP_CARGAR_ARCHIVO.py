# ============================================================
# APP_CARGAR_ARCHIVO.py
# 01_CARGA_ARCHIVOS
# Carga, validación y visualización preliminar de bases locales
# ============================================================

from pathlib import Path
import base64
import time

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
        "separador": "No aplica"
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
            "ruta": str(ruta)
        }

    return {
        "archivo": ruta.name,
        "existe": True,
        "peso_kb": round(ruta.stat().st_size / 1024, 2),
        "ruta": str(ruta)
    }


def construir_validacion_archivos(ruta_carpeta: Path) -> pd.DataFrame:
    registros = []

    for nombre_df, archivo in ARCHIVOS_ESPERADOS.items():
        ruta_archivo = ruta_carpeta / archivo
        info = obtener_info_archivo(ruta_archivo)
        info["dataframe"] = nombre_df
        registros.append(info)

    df_validacion = pd.DataFrame(registros)

    df_validacion["estado"] = df_validacion["existe"].map({
        True: "Encontrado",
        False: "Faltante"
    })

    return df_validacion


def mostrar_resumen_dataframe(nombre_df: str, df: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Filas", f"{df.shape[0]:,}")

    with col2:
        st.metric("Columnas", f"{df.shape[1]:,}")

    with col3:
        memoria_mb = df.memory_usage(deep=True).sum() / 1024**2
        st.metric("Memoria estimada", f"{memoria_mb:.2f} MB")

    with st.expander("Columnas", expanded=False):
        st.write(df.columns.tolist())

    with st.expander("Tipos de datos", expanded=False):
        df_tipos = pd.DataFrame({
            "Columna": df.columns,
            "Tipo": df.dtypes.astype(str).values,
            "Nulos": df.isna().sum().values,
            "Nulos_%": (df.isna().mean().values * 100).round(2),
        })

        st.dataframe(df_tipos, use_container_width=True)

    with st.expander("Vista previa", expanded=True):
        st.dataframe(df.head(50), use_container_width=True)


# ============================================================
# Estado de sesión
# ============================================================

if "ruta_carpeta_confirmada" not in st.session_state:
    st.session_state["ruta_carpeta_confirmada"] = None

if "dataframes_cargados" not in st.session_state:
    st.session_state["dataframes_cargados"] = {}

if "config_carga" not in st.session_state:
    st.session_state["config_carga"] = {}

if "df_validacion_archivos" not in st.session_state:
    st.session_state["df_validacion_archivos"] = pd.DataFrame()


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
# 1. Selección de carpeta
# ============================================================

st.subheader("1. Selección de carpeta")

st.info(
    """
    Ingresa la ruta local de la carpeta que contiene las bases.
    Luego presiona **Confirmar carpeta** para validar los archivos esperados.
    """
)

ruta_default = r"C:\Users\enrique.brun.aep\Downloads\BBDD_DASHBOARD_MONITOREO_CONTRATOS"

ruta_carpeta_input = st.text_input(
    "Ruta de carpeta",
    value=ruta_default,
    placeholder=r"C:\Users\usuario\Downloads\BBDD_DASHBOARD_MONITOREO_CONTRATOS"
)

col_confirmar, col_limpiar = st.columns([1, 1])

with col_confirmar:
    confirmar_carpeta = st.button(
        "Confirmar carpeta",
        type="primary",
        use_container_width=True
    )

with col_limpiar:
    limpiar_sesion = st.button(
        "Limpiar carga",
        use_container_width=True
    )

if limpiar_sesion:
    st.session_state["ruta_carpeta_confirmada"] = None
    st.session_state["dataframes_cargados"] = {}
    st.session_state["config_carga"] = {}
    st.session_state["df_validacion_archivos"] = pd.DataFrame()
    st.success("Carga limpiada correctamente.")
    st.rerun()

if confirmar_carpeta:
    ruta_carpeta = Path(ruta_carpeta_input)

    if not ruta_carpeta.exists():
        st.error(f"La carpeta no existe: {ruta_carpeta}")

    elif not ruta_carpeta.is_dir():
        st.error(f"La ruta ingresada no corresponde a una carpeta: {ruta_carpeta}")

    else:
        st.session_state["ruta_carpeta_confirmada"] = str(ruta_carpeta)

        df_validacion = construir_validacion_archivos(ruta_carpeta)
        st.session_state["df_validacion_archivos"] = df_validacion

        st.success(f"Carpeta confirmada correctamente: {ruta_carpeta}")


# ============================================================
# 2. Validación de archivos
# ============================================================

st.subheader("2. Validación de archivos esperados")

ruta_confirmada = st.session_state["ruta_carpeta_confirmada"]

if ruta_confirmada is None:
    st.warning("Primero debes confirmar una carpeta.")
    st.stop()

ruta_carpeta = Path(ruta_confirmada)

df_validacion = st.session_state["df_validacion_archivos"]

if df_validacion.empty:
    df_validacion = construir_validacion_archivos(ruta_carpeta)
    st.session_state["df_validacion_archivos"] = df_validacion

st.dataframe(
    df_validacion[
        [
            "dataframe",
            "archivo",
            "estado",
            "peso_kb",
            "ruta"
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
# 3. Carga de bases
# ============================================================

st.subheader("3. Carga de bases")

cargar_bases = st.button(
    "Cargar bases disponibles",
    type="primary",
    use_container_width=True
)

if cargar_bases:
    dataframes_cargados = {}
    config_carga = {}
    errores_carga = []

    archivos_disponibles = [
        (nombre_df, archivo)
        for nombre_df, archivo in ARCHIVOS_ESPERADOS.items()
        if (ruta_carpeta / archivo).exists()
    ]

    total_disponibles = len(archivos_disponibles)

    progress_bar = st.progress(0)
    estado_carga = st.empty()

    for i, (nombre_df, archivo) in enumerate(archivos_disponibles, start=1):
        ruta_archivo = ruta_carpeta / archivo

        estado_carga.info(f"Cargando {archivo} ({i}/{total_disponibles})...")

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

        progress_bar.progress(i / total_disponibles)
        time.sleep(0.05)

    st.session_state["dataframes_cargados"] = dataframes_cargados
    st.session_state["config_carga"] = config_carga

    estado_carga.empty()

    if dataframes_cargados:
        st.success(f"Carga completada. Se cargaron {len(dataframes_cargados)} bases correctamente.")

    if errores_carga:
        st.error("Algunos archivos no pudieron cargarse.")
        st.dataframe(pd.DataFrame(errores_carga), use_container_width=True)


# ============================================================
# 4. Resumen general de carga
# ============================================================

st.subheader("4. Resumen general de bases cargadas")

dataframes_cargados = st.session_state["dataframes_cargados"]
config_carga = st.session_state["config_carga"]

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
# 5. Visualización opcional de DataFrames
# ============================================================

st.subheader("5. Visualización opcional de DataFrames")

if not dataframes_cargados:
    st.info("Carga las bases para visualizar su contenido.")
else:
    mostrar_dataframes = st.checkbox(
        "Mostrar visor de DataFrames",
        value=False
    )

    if mostrar_dataframes:
        nombre_seleccionado = st.selectbox(
            "Selecciona un DataFrame",
            options=list(dataframes_cargados.keys())
        )

        df_seleccionado = dataframes_cargados[nombre_seleccionado]

        st.markdown(f"### `{nombre_seleccionado}`")

        mostrar_resumen_dataframe(nombre_seleccionado, df_seleccionado)


# ============================================================
# 6. Uso en otros módulos
# ============================================================

st.subheader("6. Uso de bases en otros módulos")

st.info(
    """
    Las bases cargadas quedan disponibles en memoria de sesión:

    `st.session_state["dataframes_cargados"]`

    Ejemplo:

    `df_ordenes = st.session_state["dataframes_cargados"]["df_ordenes"]`
    """
)
