# ============================================================
# APP_CARGAR_ARCHIVO_MEJORADO.py
# 01_CARGA_ARCHIVOS
# Carga, validación y visualización compacta de archivos
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import base64

import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="01_CARGA_ARCHIVOS",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Archivos esperados
# ============================================================

ARCHIVOS_ESPERADOS: dict[str, str] = {
    "df_moneda_cambio": "01_BD_Moneda_Cambio.xlsx",
    "df_ordenes": "02_ME2N_Ordenes.csv",
    "df_gasto_contratos": "03_Gasto_Contratos.csv",
    "df_centros": "04_Centros.csv",
    "df_bbdd_x_categoria": "05_BBDD_X_Categoria_BD.csv",
    "df_catalogo_categorias": "06_BD_Catalogo_Categorias.csv",
    "df_plan_ahorro_gestores": "07_BD_Plan_Ahorro_Gestores.csv",
    "df_registro_contratos": "08_BD_Registro_Contratos.csv",
    "df_hitos": "09_BD_Hitos.csv",
    "df_categorias": "10_BD_Categorias.csv",
    "df_me5a": "11_ME3N.csv",
}

EXTENSIONES_PERMITIDAS = ["csv", "xlsx", "xls"]


@dataclass
class ResultadoCarga:
    dataframe: str
    archivo: str
    filas: int | None = None
    columnas: int | None = None
    peso_kb: float | None = None
    encoding: str | None = None
    separador: str | None = None
    estado: str = "Pendiente"
    error: str | None = None


# ============================================================
# Estado de sesión
# ============================================================

DEFAULT_SESSION_STATE = {
    "dataframes_cargados": {},
    "config_carga": {},
    "df_validacion_archivos": pd.DataFrame(),
    "errores_carga": [],
    "carga_completada": False,
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def limpiar_estado_carga() -> None:
    """Limpia solo la información generada por la carga."""
    st.session_state["dataframes_cargados"] = {}
    st.session_state["config_carga"] = {}
    st.session_state["df_validacion_archivos"] = pd.DataFrame()
    st.session_state["errores_carga"] = []
    st.session_state["carga_completada"] = False


# ============================================================
# Logo e interfaz
# ============================================================

def mostrar_logo_centrado() -> None:
    if not LOGO_PATH.exists():
        return

    logo_svg = LOGO_PATH.read_text(encoding="utf-8")
    logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")

    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;margin:8px 0 12px 0;">
            <img src="data:image/svg+xml;base64,{logo_base64}" style="width:230px;">
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_encabezado() -> None:
    mostrar_logo_centrado()

    st.markdown(
        """
        <h1 style='text-align:center;margin-bottom:0;'>Carga de archivos</h1>
        <p style='text-align:center;font-size:16px;margin-top:6px;'>
            Sube los archivos requeridos y presiona un solo botón para validarlos y cargarlos.
        </p>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Lectura y normalización
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


def leer_csv_robusto(uploaded_file) -> tuple[pd.DataFrame, dict[str, str]]:
    contenido = uploaded_file.getvalue()

    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252", "ISO-8859-1"]
    separadores = [",", ";", "\t", "|"]

    mejor_df: pd.DataFrame | None = None
    mejor_config: dict[str, str] | None = None
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
                    on_bad_lines="skip",
                )

                temp = temp.dropna(axis=1, how="all")
                score = temp.shape[0] * temp.shape[1]

                if temp.shape[1] > 1 and score > mejor_score:
                    mejor_df = temp.copy()
                    mejor_config = {
                        "encoding": encoding,
                        "separador": sep,
                    }
                    mejor_score = score

            except Exception:
                continue

    if mejor_df is None or mejor_config is None:
        raise ValueError(f"No se pudo leer correctamente el CSV: {uploaded_file.name}")

    return limpiar_columnas(mejor_df), mejor_config


def leer_excel(uploaded_file) -> tuple[pd.DataFrame, dict[str, str]]:
    df = pd.read_excel(BytesIO(uploaded_file.getvalue()))
    df = df.dropna(axis=1, how="all")

    return limpiar_columnas(df), {
        "encoding": "No aplica",
        "separador": "No aplica",
    }


def cargar_archivo(uploaded_file) -> tuple[pd.DataFrame, dict[str, str]]:
    extension = Path(uploaded_file.name).suffix.lower()

    if extension == ".csv":
        return leer_csv_robusto(uploaded_file)

    if extension in {".xlsx", ".xls"}:
        return leer_excel(uploaded_file)

    raise ValueError(f"Formato no soportado: {uploaded_file.name}")


# ============================================================
# Validación y carga
# ============================================================

def construir_mapa_archivos(archivos_seleccionados) -> dict[str, object]:
    """Convierte la lista de archivos subidos en un diccionario por nombre."""
    return {
        archivo.name: archivo
        for archivo in archivos_seleccionados or []
    }


def validar_archivos(archivos_dict: dict[str, object]) -> pd.DataFrame:
    registros: list[dict[str, object]] = []

    for nombre_df, nombre_archivo in ARCHIVOS_ESPERADOS.items():
        archivo = archivos_dict.get(nombre_archivo)
        existe = archivo is not None

        registros.append(
            {
                "dataframe": nombre_df,
                "archivo": nombre_archivo,
                "estado": "Encontrado" if existe else "Faltante",
                "existe": existe,
                "peso_kb": round(archivo.size / 1024, 2) if existe else None,
            }
        )

    return pd.DataFrame(registros)


def cargar_archivos(
    archivos_dict: dict[str, object],
) -> tuple[dict[str, pd.DataFrame], dict[str, dict], pd.DataFrame, list[dict]]:
    dataframes_cargados: dict[str, pd.DataFrame] = {}
    config_carga: dict[str, dict] = {}
    errores_carga: list[dict] = []

    df_validacion = validar_archivos(archivos_dict)
    disponibles = df_validacion[df_validacion["existe"]]

    if disponibles.empty:
        raise ValueError("No hay archivos esperados disponibles para cargar.")

    progress_bar = st.progress(0)
    estado = st.empty()
    total = len(disponibles)

    for i, row in enumerate(disponibles.itertuples(index=False), start=1):
        nombre_df = row.dataframe
        nombre_archivo = row.archivo
        archivo = archivos_dict[nombre_archivo]

        estado.info(f"Cargando {nombre_archivo} ({i}/{total})...")

        try:
            df, config = cargar_archivo(archivo)

            dataframes_cargados[nombre_df] = df

            config_carga[nombre_df] = {
                "archivo": nombre_archivo,
                "filas": df.shape[0],
                "columnas": df.shape[1],
                "peso_kb": round(archivo.size / 1024, 2),
                "encoding": config.get("encoding"),
                "separador": config.get("separador"),
            }

        except Exception as exc:
            errores_carga.append(
                {
                    "dataframe": nombre_df,
                    "archivo": nombre_archivo,
                    "error": str(exc),
                }
            )

        progress_bar.progress(i / total)

    estado.empty()
    progress_bar.empty()

    return dataframes_cargados, config_carga, df_validacion, errores_carga


# ============================================================
# Visualizaciones compactas
# ============================================================

def mostrar_metricas_validacion(df_validacion: pd.DataFrame) -> None:
    total = len(df_validacion)
    encontrados = int(df_validacion["existe"].sum()) if not df_validacion.empty else 0
    faltantes = total - encontrados

    peso_total_mb = (
        df_validacion["peso_kb"].fillna(0).sum() / 1024
        if not df_validacion.empty
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Esperados", total)
    col2.metric("Encontrados", encontrados)
    col3.metric("Faltantes", faltantes)
    col4.metric("Peso total", f"{peso_total_mb:.2f} MB")

    if faltantes:
        st.warning(f"Hay {faltantes} archivo(s) faltante(s). Se cargaron solo los disponibles.")
    else:
        st.success("Todos los archivos esperados fueron encontrados.")


def mostrar_resumen_carga(
    config_carga: dict[str, dict],
    dataframes: dict[str, pd.DataFrame],
) -> None:
    if not dataframes:
        return

    df_resumen = pd.DataFrame.from_dict(
        config_carga,
        orient="index",
    ).reset_index()

    df_resumen = df_resumen.rename(columns={"index": "dataframe"})

    total_filas = sum(df.shape[0] for df in dataframes.values())
    total_columnas = sum(df.shape[1] for df in dataframes.values())

    total_memoria = sum(
        df.memory_usage(deep=True).sum() / 1024**2
        for df in dataframes.values()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total filas", f"{total_filas:,}")
    col2.metric("Total columnas", f"{total_columnas:,}")
    col3.metric("Memoria estimada", f"{total_memoria:.2f} MB")

    with st.expander("Ver resumen técnico de carga", expanded=False):
        st.dataframe(df_resumen, use_container_width=True)


def mostrar_vista_previa(dataframes: dict[str, pd.DataFrame]) -> None:
    if not dataframes:
        return

    with st.expander("Ver vista previa de DataFrames", expanded=False):
        nombre_df = st.selectbox(
            "Selecciona un DataFrame",
            options=list(dataframes.keys()),
        )

        df = dataframes[nombre_df]

        st.caption(
            f"{nombre_df}: {df.shape[0]:,} filas x {df.shape[1]:,} columnas"
        )

        st.dataframe(
            df.head(30),
            use_container_width=True,
        )

        with st.expander("Columnas, tipos y nulos", expanded=False):
            df_tipos = pd.DataFrame(
                {
                    "columna": df.columns,
                    "tipo": df.dtypes.astype(str).values,
                    "nulos": df.isna().sum().values,
                    "nulos_%": (df.isna().mean().values * 100).round(2),
                }
            )

            st.dataframe(df_tipos, use_container_width=True)


def mostrar_errores(errores: list[dict]) -> None:
    if errores:
        with st.expander("Ver errores de carga", expanded=True):
            st.dataframe(
                pd.DataFrame(errores),
                use_container_width=True,
            )


# ============================================================
# App principal
# ============================================================

mostrar_encabezado()
st.divider()

with st.container(border=True):
    st.subheader("Subir y cargar archivos")

    st.caption(
        "Selecciona todos los CSV/XLSX requeridos. Luego presiona el botón de carga una sola vez."
    )

    archivos_seleccionados = st.file_uploader(
        "Archivos del dashboard",
        type=EXTENSIONES_PERMITIDAS,
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    col_cargar, col_limpiar = st.columns([3, 1])

    with col_cargar:
        boton_cargar = st.button(
            "Validar y cargar archivos",
            type="primary",
            use_container_width=True,
            disabled=not archivos_seleccionados,
        )

    with col_limpiar:
        boton_limpiar = st.button(
            "Limpiar",
            use_container_width=True,
        )


if boton_limpiar:
    limpiar_estado_carga()
    st.rerun()


if boton_cargar:
    limpiar_estado_carga()

    archivos_dict = construir_mapa_archivos(archivos_seleccionados)

    try:
        dataframes, config, df_validacion, errores = cargar_archivos(archivos_dict)

        st.session_state["dataframes_cargados"] = dataframes
        st.session_state["config_carga"] = config
        st.session_state["df_validacion_archivos"] = df_validacion
        st.session_state["errores_carga"] = errores
        st.session_state["carga_completada"] = True

        st.success(
            f"Carga finalizada. Se cargaron {len(dataframes)} DataFrame(s)."
        )

    except Exception as exc:
        st.error(str(exc))


if st.session_state["carga_completada"]:
    df_validacion = st.session_state["df_validacion_archivos"]
    dataframes_cargados = st.session_state["dataframes_cargados"]
    config_carga = st.session_state["config_carga"]
    errores_carga = st.session_state["errores_carga"]

    st.divider()
    st.subheader("Resultado de la carga")

    mostrar_metricas_validacion(df_validacion)
    mostrar_resumen_carga(config_carga, dataframes_cargados)

    with st.expander("Ver validación archivo por archivo", expanded=False):
        st.dataframe(
            df_validacion[
                [
                    "dataframe",
                    "archivo",
                    "estado",
                    "peso_kb",
                ]
            ],
            use_container_width=True,
        )

    mostrar_errores(errores_carga)
    mostrar_vista_previa(dataframes_cargados)

    with st.expander("Uso en otros módulos", expanded=False):
        st.code(
            'dataframes = st.session_state["dataframes_cargados"]\n'
            'df_ordenes = dataframes["df_ordenes"]',
            language="python",
        )

else:
    st.info(
        "La vista de validación, resumen y previews aparecerá después de cargar los archivos."
    )
