import base64
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st


# =========================
# Configuración de página
# =========================

st.set_page_config(
    page_title="Cargar archivos TAT",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# Rutas
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# =========================
# Estilos
# =========================

def aplicar_estilos():
    st.markdown(
        """
        <style>
            .main {
                background-color: #f7f9fc;
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1200px;
            }

            .header-card {
                background: linear-gradient(135deg, #ffffff 0%, #eef4ff 100%);
                border: 1px solid #dce6f5;
                border-radius: 22px;
                padding: 28px 32px;
                margin-bottom: 25px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            }

            .title {
                text-align: center;
                color: #0f172a;
                font-size: 38px;
                font-weight: 800;
                margin-bottom: 10px;
            }

            .subtitle {
                text-align: center;
                color: #475569;
                font-size: 17px;
                line-height: 1.6;
                margin-bottom: 0;
            }

            .section-card {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 18px;
                padding: 24px;
                margin-bottom: 22px;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
            }

            .success-box {
                background-color: #ecfdf5;
                color: #065f46;
                border: 1px solid #a7f3d0;
                border-radius: 14px;
                padding: 14px 18px;
                font-weight: 600;
                margin-top: 12px;
            }

            .warning-box {
                background-color: #fffbeb;
                color: #92400e;
                border: 1px solid #fde68a;
                border-radius: 14px;
                padding: 14px 18px;
                font-weight: 600;
                margin-top: 12px;
            }

            .error-box {
                background-color: #fef2f2;
                color: #991b1b;
                border: 1px solid #fecaca;
                border-radius: 14px;
                padding: 14px 18px;
                font-weight: 600;
                margin-top: 12px;
            }

            div[data-testid="stMetric"] {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                padding: 18px;
                border-radius: 16px;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
            }

            div[data-testid="stMetricLabel"] {
                color: #475569;
                font-weight: 700;
            }

            div[data-testid="stMetricValue"] {
                color: #0f172a;
                font-weight: 800;
            }

            .stButton > button {
                border-radius: 12px;
                border: 1px solid #cbd5e1;
                padding: 0.55rem 1rem;
                font-weight: 700;
                transition: all 0.2s ease-in-out;
            }

            .stButton > button:hover {
                border-color: #2563eb;
                color: #2563eb;
                transform: translateY(-1px);
            }

            .small-text {
                color: #64748b;
                font-size: 14px;
            }

            hr {
                margin-top: 1rem;
                margin-bottom: 1.5rem;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


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
                margin-top: 5px;
                margin-bottom: 18px;
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
        st.markdown(
            f"""
            <div class="warning-box">
                Logo no encontrado: {LOGO_PATH}
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================
# Estado de sesión
# =========================

def inicializar_estado():
    if "archivos_tat" not in st.session_state:
        st.session_state["archivos_tat"] = {}

    if "archivo_tat_activo" not in st.session_state:
        st.session_state["archivo_tat_activo"] = None


# =========================
# Lectura de archivo
# =========================

@st.cache_data(show_spinner="Leyendo archivo...")
def leer_archivo(archivo_bytes, nombre_archivo):
    extension = Path(nombre_archivo).suffix.lower()
    buffer = BytesIO(archivo_bytes)

    if extension == ".csv":
        return pd.read_csv(buffer)

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(buffer)

    if extension == ".parquet":
        return pd.read_parquet(buffer)

    raise ValueError("Formato no soportado. Usa CSV, XLSX, XLS o PARQUET.")


def guardar_archivo_en_sesion(df, nombre_archivo):
    st.session_state["archivos_tat"][nombre_archivo] = df
    st.session_state["archivo_tat_activo"] = nombre_archivo


def eliminar_archivo_de_sesion(nombre_archivo):
    if nombre_archivo in st.session_state["archivos_tat"]:
        st.session_state["archivos_tat"].pop(nombre_archivo)

    archivos_restantes = list(st.session_state["archivos_tat"].keys())

    if archivos_restantes:
        st.session_state["archivo_tat_activo"] = archivos_restantes[0]
    else:
        st.session_state["archivo_tat_activo"] = None


def eliminar_todos_los_archivos():
    st.session_state["archivos_tat"] = {}
    st.session_state["archivo_tat_activo"] = None


# =========================
# Utilidades
# =========================

def obtener_resumen_archivos():
    resumen = []

    for nombre, df in st.session_state["archivos_tat"].items():
        resumen.append(
            {
                "Archivo": nombre,
                "Filas": df.shape[0],
                "Columnas": df.shape[1],
                "Memoria aproximada MB": round(
                    df.memory_usage(deep=True).sum() / 1024 / 1024,
                    2
                )
            }
        )

    return pd.DataFrame(resumen)


def mostrar_mensaje_html(tipo, texto):
    clases = {
        "success": "success-box",
        "warning": "warning-box",
        "error": "error-box"
    }

    clase = clases.get(tipo, "warning-box")

    st.markdown(
        f"""
        <div class="{clase}">
            {texto}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# Interfaz
# =========================

aplicar_estilos()
inicializar_estado()

mostrar_logo_centrado()

st.markdown(
    """
    <div class="header-card">
        <div class="title">Cargar archivos base TAT</div>
        <p class="subtitle">
            Sube uno o varios archivos en una sola carga para reutilizarlos en
            Filtro TAT, Gráficos TAT y Performance de Plantas.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# Carga de archivos
# =========================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

st.subheader("Carga múltiple de archivos")

st.markdown(
    """
    <p class="small-text">
        Formatos permitidos: CSV, XLSX, XLS y PARQUET.
        Puedes seleccionar varios archivos al mismo tiempo.
    </p>
    """,
    unsafe_allow_html=True
)

archivos = st.file_uploader(
    "Selecciona uno o varios archivos base TAT",
    type=["xlsx", "xls", "csv", "parquet"],
    accept_multiple_files=True,
    key="archivos_base_tat_uploader"
)

if archivos:
    archivos_cargados = []
    archivos_con_error = []

    for archivo in archivos:
        try:
            archivo_bytes = archivo.getvalue()
            df = leer_archivo(archivo_bytes, archivo.name)
            guardar_archivo_en_sesion(df, archivo.name)
            archivos_cargados.append(archivo.name)

        except Exception as error:
            archivos_con_error.append(
                {
                    "archivo": archivo.name,
                    "error": str(error)
                }
            )

    if archivos_cargados:
        mostrar_mensaje_html(
            "success",
            f"Archivos cargados correctamente: {len(archivos_cargados)}"
        )

        with st.expander("Ver archivos cargados"):
            for nombre in archivos_cargados:
                st.write(f"✅ {nombre}")

    if archivos_con_error:
        mostrar_mensaje_html(
            "error",
            f"No se pudieron cargar {len(archivos_con_error)} archivo(s)."
        )

        with st.expander("Ver errores"):
            for item in archivos_con_error:
                st.write(f"❌ {item['archivo']}")
                st.code(item["error"])

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Validación inicial
# =========================

if not st.session_state["archivos_tat"]:
    mostrar_mensaje_html(
        "warning",
        "Todavía no hay archivos cargados. Sube uno o varios archivos para continuar."
    )
    st.stop()


# =========================
# Resumen general
# =========================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

st.subheader("Resumen general")

archivos_disponibles = list(st.session_state["archivos_tat"].keys())

total_archivos = len(archivos_disponibles)
total_filas = sum(
    df.shape[0]
    for df in st.session_state["archivos_tat"].values()
)
total_columnas_distintas = len(
    set(
        columna
        for df in st.session_state["archivos_tat"].values()
        for columna in df.columns
    )
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Archivos cargados", f"{total_archivos:,}")

with col2:
    st.metric("Filas totales", f"{total_filas:,}")

with col3:
    st.metric("Columnas distintas", f"{total_columnas_distintas:,}")

resumen_df = obtener_resumen_archivos()

st.dataframe(
    resumen_df,
    use_container_width=True,
    hide_index=True
)

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Selector de archivo activo
# =========================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

st.subheader("Archivo activo")

archivo_activo_actual = st.session_state.get("archivo_tat_activo")

if archivo_activo_actual not in archivos_disponibles:
    archivo_activo_actual = archivos_disponibles[0]
    st.session_state["archivo_tat_activo"] = archivo_activo_actual

archivo_seleccionado = st.selectbox(
    "Selecciona el archivo que quieres visualizar",
    options=archivos_disponibles,
    index=archivos_disponibles.index(archivo_activo_actual),
    key="selector_archivo_tat"
)

st.session_state["archivo_tat_activo"] = archivo_seleccionado

df_tat = st.session_state["archivos_tat"][archivo_seleccionado]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Archivo seleccionado", archivo_seleccionado)

with col2:
    st.metric("Filas", f"{df_tat.shape[0]:,}")

with col3:
    st.metric("Columnas", f"{df_tat.shape[1]:,}")

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Vista previa
# =========================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

st.subheader("Vista previa del archivo seleccionado")

filas_preview = st.slider(
    "Cantidad de filas a mostrar",
    min_value=5,
    max_value=min(200, max(5, df_tat.shape[0])),
    value=min(50, max(5, df_tat.shape[0])),
    step=5
)

st.dataframe(
    df_tat.head(filas_preview),
    use_container_width=True
)

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Columnas disponibles
# =========================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

st.subheader("Columnas disponibles")

columnas_df = pd.DataFrame(
    {
        "N°": range(1, len(df_tat.columns) + 1),
        "Columna": list(df_tat.columns),
        "Tipo de dato": [str(df_tat[col].dtype) for col in df_tat.columns],
        "Valores no nulos": [df_tat[col].notna().sum() for col in df_tat.columns],
        "Valores nulos": [df_tat[col].isna().sum() for col in df_tat.columns],
    }
)

st.dataframe(
    columnas_df,
    use_container_width=True,
    hide_index=True
)

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Acciones
# =========================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

st.subheader("Acciones")

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "Eliminar archivo seleccionado",
        use_container_width=True
    ):
        eliminar_archivo_de_sesion(archivo_seleccionado)
        st.success("Archivo seleccionado eliminado de la sesión.")
        st.rerun()

with col2:
    if st.button(
        "Eliminar todos los archivos",
        use_container_width=True
    ):
        eliminar_todos_los_archivos()
        st.success("Todos los archivos fueron eliminados de la sesión.")
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
