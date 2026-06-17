# ============================================================
# 06_CARGAR_ARCHIVO
# Carga múltiple de archivos base TAT
# Guarda archivo activo en sesión como df_tat
# ============================================================

import base64
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# ESTILOS
# No se modifica .block-container para no afectar el logo.
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #fafafa;
            padding: 12px;
            border-radius: 12px;
            border: 1px solid #eeeeee;
        }

        div[data-testid="stFileUploader"] {
            padding: 6px;
            border-radius: 12px;
        }

        .page-title {
            text-align: center;
            font-size: 30px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 2px;
        }

        .page-subtitle {
            text-align: center;
            color: #6B7280;
            font-size: 15px;
            margin-bottom: 18px;
        }

        .section-caption {
            color: #6B7280;
            font-size: 14px;
            margin-top: -6px;
            margin-bottom: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOGO
# ============================================================

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
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

def inicializar_estado():
    if "archivos_tat" not in st.session_state:
        st.session_state["archivos_tat"] = {}

    if "archivo_tat_activo" not in st.session_state:
        st.session_state["archivo_tat_activo"] = None

    if "df_tat" not in st.session_state:
        st.session_state["df_tat"] = None

    if "nombre_archivo_tat" not in st.session_state:
        st.session_state["nombre_archivo_tat"] = None


# ============================================================
# FUNCIONES BASE
# ============================================================

def obtener_separador(separador_csv: str):
    separadores = {
        "Automático": None,
        "Punto y coma (;)": ";",
        "Coma (,)": ",",
        "Tabulación": "\t",
    }

    return separadores.get(separador_csv, None)


@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    archivo_bytes: bytes,
    nombre_archivo: str,
    separador_csv: str,
) -> pd.DataFrame:

    extension = Path(nombre_archivo).suffix.lower()
    buffer = BytesIO(archivo_bytes)

    if extension == ".parquet":
        return pd.read_parquet(buffer)

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(buffer)

    if extension == ".csv":
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip",
            )

        except Exception:
            buffer.seek(0)

            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip",
            )

    raise ValueError("Formato no soportado. Usa CSV, XLSX, XLS o PARQUET.")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def guardar_archivo_en_sesion(df: pd.DataFrame, nombre_archivo: str):
    df = limpiar_nombres_columnas(df)

    st.session_state["archivos_tat"][nombre_archivo] = df
    st.session_state["archivo_tat_activo"] = nombre_archivo

    st.session_state["df_tat"] = df
    st.session_state["nombre_archivo_tat"] = nombre_archivo


def activar_archivo(nombre_archivo: str):
    df = st.session_state["archivos_tat"][nombre_archivo]

    st.session_state["archivo_tat_activo"] = nombre_archivo
    st.session_state["df_tat"] = df
    st.session_state["nombre_archivo_tat"] = nombre_archivo


def eliminar_archivo_de_sesion(nombre_archivo: str):
    if nombre_archivo in st.session_state["archivos_tat"]:
        st.session_state["archivos_tat"].pop(nombre_archivo)

    archivos_restantes = list(st.session_state["archivos_tat"].keys())

    if archivos_restantes:
        activar_archivo(archivos_restantes[0])
    else:
        st.session_state["archivo_tat_activo"] = None
        st.session_state["df_tat"] = None
        st.session_state["nombre_archivo_tat"] = None


def eliminar_todos_los_archivos():
    st.session_state["archivos_tat"] = {}
    st.session_state["archivo_tat_activo"] = None
    st.session_state["df_tat"] = None
    st.session_state["nombre_archivo_tat"] = None


def obtener_resumen_archivos() -> pd.DataFrame:
    resumen = []

    for nombre, df in st.session_state["archivos_tat"].items():
        resumen.append(
            {
                "Archivo": nombre,
                "Filas": df.shape[0],
                "Columnas": df.shape[1],
                "Memoria aproximada MB": round(
                    df.memory_usage(deep=True).sum() / 1024 / 1024,
                    2,
                ),
                "Activo": nombre == st.session_state.get("archivo_tat_activo"),
            }
        )

    return pd.DataFrame(resumen)


def construir_tabla_columnas(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "N°": range(1, len(df.columns) + 1),
            "Columna": list(df.columns),
            "Tipo de dato": [str(df[col].dtype) for col in df.columns],
            "Valores no nulos": [int(df[col].notna().sum()) for col in df.columns],
            "Valores nulos": [int(df[col].isna().sum()) for col in df.columns],
        }
    )


# ============================================================
# APP
# ============================================================

inicializar_estado()
mostrar_logo()

st.markdown(
    """
    <div class="page-title">06_CARGAR_ARCHIVO</div>
    <div class="page-subtitle">
        Carga archivos base TAT y define el archivo activo para las demás apps.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIGURACIÓN DE LECTURA
# ============================================================

with st.expander("Configuración CSV", expanded=False):
    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación",
        ],
        index=0,
    )

    st.caption("Esta configuración solo aplica a archivos CSV.")


# ============================================================
# CARGA DE ARCHIVOS
# ============================================================

st.markdown("### Cargar archivos")
st.caption("Formatos permitidos: CSV, XLSX, XLS y PARQUET. Puedes cargar uno o varios archivos.")

archivos = st.file_uploader(
    "Selecciona uno o varios archivos base TAT",
    type=["xlsx", "xls", "csv", "parquet"],
    accept_multiple_files=True,
    key="archivos_base_tat_uploader",
    label_visibility="collapsed",
)

if archivos:
    archivos_cargados = []
    archivos_con_error = []

    with st.spinner("Leyendo archivos..."):
        for archivo in archivos:
            try:
                archivo_bytes = archivo.getvalue()

                df = leer_archivo_cache(
                    archivo_bytes=archivo_bytes,
                    nombre_archivo=archivo.name,
                    separador_csv=separador_csv,
                )

                guardar_archivo_en_sesion(
                    df=df,
                    nombre_archivo=archivo.name,
                )

                archivos_cargados.append(archivo.name)

            except Exception as error:
                archivos_con_error.append(
                    {
                        "archivo": archivo.name,
                        "error": str(error),
                    }
                )

    if archivos_cargados:
        st.success(
            f"{len(archivos_cargados)} archivo(s) cargado(s). "
            f"Activo: {st.session_state['nombre_archivo_tat']}"
        )

    if archivos_con_error:
        st.error(
            f"No se pudieron cargar {len(archivos_con_error)} archivo(s)."
        )

        with st.expander("Ver errores de carga", expanded=False):
            for item in archivos_con_error:
                st.write(f"**{item['archivo']}**")
                st.code(item["error"])


# ============================================================
# SIN ARCHIVOS
# ============================================================

if not st.session_state["archivos_tat"]:
    st.info("Todavía no hay archivos cargados.")
    st.stop()


# ============================================================
# ARCHIVO ACTIVO
# ============================================================

st.divider()

st.markdown("### Archivo activo")
st.caption("Este archivo queda disponible para las demás apps como df_tat.")

archivos_disponibles = list(st.session_state["archivos_tat"].keys())

archivo_activo_actual = st.session_state.get("archivo_tat_activo")

if archivo_activo_actual not in archivos_disponibles:
    archivo_activo_actual = archivos_disponibles[0]
    activar_archivo(archivo_activo_actual)

archivo_seleccionado = st.selectbox(
    "Seleccionar archivo activo",
    options=archivos_disponibles,
    index=archivos_disponibles.index(st.session_state["archivo_tat_activo"]),
    key="selector_archivo_tat",
)

activar_archivo(archivo_seleccionado)

df_tat = st.session_state["df_tat"]
nombre_archivo = st.session_state["nombre_archivo_tat"]

col1, col2, col3 = st.columns(3)

col1.metric("Archivo activo", nombre_archivo)
col2.metric("Filas", f"{df_tat.shape[0]:,}")
col3.metric("Columnas", f"{df_tat.shape[1]:,}")

st.success(
    f"Archivo activo guardado correctamente: **{nombre_archivo}**"
)


# ============================================================
# ARCHIVOS CARGADOS
# ============================================================

with st.expander("Archivos cargados en sesión", expanded=False):
    resumen_df = obtener_resumen_archivos()

    st.dataframe(
        resumen_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# VISTA PREVIA
# ============================================================

with st.expander("Vista previa del archivo activo", expanded=False):
    max_filas = min(200, max(5, df_tat.shape[0]))

    filas_preview = st.slider(
        "Cantidad de filas a mostrar",
        min_value=5,
        max_value=max_filas,
        value=min(50, max_filas),
        step=5,
    )

    st.dataframe(
        df_tat.head(filas_preview),
        use_container_width=True,
    )


# ============================================================
# COLUMNAS
# ============================================================

with st.expander("Columnas disponibles del archivo activo", expanded=False):
    columnas_df = construir_tabla_columnas(df_tat)

    st.dataframe(
        columnas_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ACCIONES
# ============================================================

with st.expander("Acciones", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        eliminar_activo = st.button(
            "Eliminar archivo activo",
            use_container_width=True,
        )

        if eliminar_activo:
            eliminar_archivo_de_sesion(archivo_seleccionado)
            st.success("Archivo activo eliminado de la sesión.")
            st.rerun()

    with col2:
        eliminar_todos = st.button(
            "Eliminar todos los archivos",
            use_container_width=True,
        )

        if eliminar_todos:
            eliminar_todos_los_archivos()
            st.success("Todos los archivos fueron eliminados de la sesión.")
            st.rerun()
