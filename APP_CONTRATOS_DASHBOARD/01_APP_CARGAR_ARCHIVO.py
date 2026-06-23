# ============================================================
# APP_CARGAR_ARCHIVO_MEJORADO_SHAREPOINT.py
# 01_CARGA_ARCHIVOS
# Carga manual o desde SharePoint con clave
# Carga, validación y visualización compacta de archivos
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
import base64
import hashlib
import hmac
import re

import pandas as pd
import requests
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
# IMPORTANTE:
# El orden de este diccionario se usa para asociar las URLs
# de SharePoint configuradas en secrets.toml.
# ============================================================

ARCHIVOS_ESPERADOS: dict[str, str] = {
    "df_moneda_cambio": "01_BD_Moneda_Cambio.xlsx",
    "df_me2n_oc_ordenes": "02_ME2N_Ordenes.csv",
    "df_gasto_contratos": "03_Gasto_Contratos.csv",
    "df_centros": "04_Centros.csv",
    "df_bbdd_x_categoria": "05_BBDD_X_Categoria_BD.csv",
    "df_catalogo_categorias": "06_BD_Catalogo_Categorias.csv",
    "df_plan_ahorro_gestores": "07_BD_Plan_Ahorro_Gestores.csv",
    "df_registro_contratos": "08_BD_Registro_Contratos.csv",
    "df_hitos": "09_BD_Hitos.csv",
    "df_categorias": "10_BD_Categorias.csv",
    "df_me3n": "11_ME3N.csv",
}

EXTENSIONES_PERMITIDAS = ["csv", "xlsx", "xls", "parquet"]


@dataclass
class ResultadoCarga:
    dataframe: str
    archivo: str
    filas: int | None = None
    columnas: int | None = None
    peso_kb: float | None = None
    encoding: str | None = None
    separador: str | None = None
    origen: str | None = None
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
    "metodo_carga_activo": None,
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
    st.session_state["metodo_carga_activo"] = None

    # También elimina accesos directos tipo st.session_state["df_me3n"]
    for nombre_df in ARCHIVOS_ESPERADOS.keys():
        st.session_state.pop(nombre_df, None)


def guardar_dataframes_en_sesion(
    dataframes: dict[str, pd.DataFrame],
    config: dict[str, dict],
    df_validacion: pd.DataFrame,
    errores: list[dict],
    metodo: str,
) -> None:
    st.session_state["dataframes_cargados"] = dataframes
    st.session_state["config_carga"] = config
    st.session_state["df_validacion_archivos"] = df_validacion
    st.session_state["errores_carga"] = errores
    st.session_state["carga_completada"] = True
    st.session_state["metodo_carga_activo"] = metodo

    # Accesos directos para otros módulos:
    # st.session_state["df_moneda_cambio"], st.session_state["df_me3n"], etc.
    for nombre_df, df in dataframes.items():
        st.session_state[nombre_df] = df


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
            Carga manualmente los archivos requeridos o conéctate a SharePoint con clave.
        </p>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Seguridad SharePoint
# ============================================================

def calcular_sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def obtener_hash_clave_sharepoint() -> str:
    try:
        clave_hash = st.secrets["sharepoint_archivos"]["access_key_sha256"]
    except Exception:
        raise ValueError(
            "No se encontró sharepoint_archivos.access_key_sha256 en Secrets."
        )

    clave_hash = str(clave_hash).strip()

    if not clave_hash:
        raise ValueError("La clave hash de SharePoint está vacía en Secrets.")

    return clave_hash


def validar_clave_sharepoint(clave_ingresada: str) -> bool:
    if not clave_ingresada:
        return False

    hash_esperado = obtener_hash_clave_sharepoint()
    hash_ingresado = calcular_sha256(clave_ingresada.strip())

    return hmac.compare_digest(hash_ingresado, hash_esperado)


def obtener_urls_sharepoint() -> list[str]:
    try:
        urls = st.secrets["sharepoint_archivos"]["urls"]
    except Exception:
        raise ValueError("No se encontró sharepoint_archivos.urls en Secrets.")

    urls = [str(url).strip() for url in urls if str(url).strip()]

    if not urls:
        raise ValueError("La lista de URLs de SharePoint está vacía en Secrets.")

    esperados = len(ARCHIVOS_ESPERADOS)

    if len(urls) != esperados:
        raise ValueError(
            f"Se esperaban {esperados} URLs de SharePoint, pero hay {len(urls)}. "
            "Revisa el orden y la cantidad en Secrets."
        )

    return urls


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


def leer_csv_robusto_bytes(
    contenido: bytes,
    nombre_archivo: str,
) -> tuple[pd.DataFrame, dict[str, str]]:
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
        raise ValueError(f"No se pudo leer correctamente el CSV: {nombre_archivo}")

    return limpiar_columnas(mejor_df), mejor_config


def leer_excel_bytes(contenido: bytes) -> tuple[pd.DataFrame, dict[str, str]]:
    df = pd.read_excel(BytesIO(contenido))
    df = df.dropna(axis=1, how="all")

    return limpiar_columnas(df), {
        "encoding": "No aplica",
        "separador": "No aplica",
    }


def leer_parquet_bytes(contenido: bytes) -> tuple[pd.DataFrame, dict[str, str]]:
    df = pd.read_parquet(BytesIO(contenido))
    df = df.dropna(axis=1, how="all")

    return limpiar_columnas(df), {
        "encoding": "No aplica",
        "separador": "No aplica",
    }


def detectar_formato_archivo(
    contenido: bytes,
    nombre_archivo: str,
    content_type: str = "",
) -> str:
    extension = Path(nombre_archivo).suffix.lower()
    content_type = content_type.lower()

    # Parquet: magic bytes al inicio y final.
    if len(contenido) >= 8 and contenido[:4] == b"PAR1" and contenido[-4:] == b"PAR1":
        return "parquet"

    # XLSX normalmente es ZIP y comienza con PK.
    if contenido[:4] == b"PK\x03\x04":
        return "excel"

    if "spreadsheet" in content_type or "excel" in content_type:
        return "excel"

    if "parquet" in content_type:
        return "parquet"

    if "csv" in content_type or "text/plain" in content_type:
        return "csv"

    if extension in {".xlsx", ".xls"}:
        return "excel"

    if extension == ".parquet":
        return "parquet"

    if extension == ".csv":
        return "csv"

    # Último intento: tratarlo como CSV.
    return "csv"


def cargar_archivo_desde_bytes(
    contenido: bytes,
    nombre_archivo: str,
    content_type: str = "",
) -> tuple[pd.DataFrame, dict[str, str]]:
    formato = detectar_formato_archivo(
        contenido=contenido,
        nombre_archivo=nombre_archivo,
        content_type=content_type,
    )

    if formato == "csv":
        df, config = leer_csv_robusto_bytes(contenido, nombre_archivo)
    elif formato == "excel":
        df, config = leer_excel_bytes(contenido)
    elif formato == "parquet":
        df, config = leer_parquet_bytes(contenido)
    else:
        raise ValueError(f"Formato no soportado: {nombre_archivo}")

    config["formato_detectado"] = formato

    return df, config


def cargar_archivo_manual(uploaded_file) -> tuple[pd.DataFrame, dict[str, str]]:
    return cargar_archivo_desde_bytes(
        contenido=uploaded_file.getvalue(),
        nombre_archivo=uploaded_file.name,
        content_type=getattr(uploaded_file, "type", "") or "",
    )


# ============================================================
# SharePoint
# ============================================================

def preparar_url_descarga_sharepoint(url: str) -> str:
    url = url.strip()

    if not url:
        raise ValueError("La URL de SharePoint está vacía.")

    if "download=1" in url.lower():
        return url

    separador = "&" if "?" in url else "?"

    return f"{url}{separador}download=1"


def extraer_nombre_content_disposition(content_disposition: str) -> str | None:
    if not content_disposition:
        return None

    # filename*=UTF-8''archivo.xlsx
    match_utf = re.search(
        r"filename\*=UTF-8''([^;]+)",
        content_disposition,
        flags=re.IGNORECASE,
    )
    if match_utf:
        return match_utf.group(1).strip().strip('"')

    # filename="archivo.xlsx"
    match = re.search(
        r'filename="?([^";]+)"?',
        content_disposition,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip().strip('"')

    return None


def detectar_nombre_desde_url(url: str) -> str | None:
    try:
        path = urlparse(url).path
        nombre = Path(path).name
        if "." in nombre:
            return nombre
    except Exception:
        return None

    return None


@st.cache_data(show_spinner=False, ttl=300)
def descargar_archivo_sharepoint_cache(url: str) -> tuple[bytes, dict[str, str]]:
    url_descarga = preparar_url_descarga_sharepoint(url)

    response = requests.get(
        url_descarga,
        allow_redirects=True,
        timeout=90,
    )

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    contenido_inicio = response.content[:500].lower()

    if "text/html" in content_type or b"<html" in contenido_inicio:
        raise ValueError(
            "SharePoint devolvió HTML en vez del archivo. "
            "Verifica que el enlace permita descarga directa."
        )

    content_disposition = response.headers.get("Content-Disposition", "")

    metadata = {
        "url_final": response.url,
        "content_type": content_type,
        "content_disposition": content_disposition,
        "nombre_detectado": (
            extraer_nombre_content_disposition(content_disposition)
            or detectar_nombre_desde_url(response.url)
            or ""
        ),
    }

    return response.content, metadata


def construir_archivos_sharepoint() -> list[dict[str, str]]:
    urls = obtener_urls_sharepoint()

    archivos = []

    for indice, ((nombre_df, nombre_archivo_esperado), url) in enumerate(
        zip(ARCHIVOS_ESPERADOS.items(), urls),
        start=1,
    ):
        archivos.append(
            {
                "orden": indice,
                "dataframe": nombre_df,
                "archivo": nombre_archivo_esperado,
                "url": url,
            }
        )

    return archivos


# ============================================================
# Validación y carga manual
# ============================================================

def construir_mapa_archivos(archivos_seleccionados) -> dict[str, object]:
    """Convierte la lista de archivos subidos en un diccionario por nombre."""
    return {
        archivo.name: archivo
        for archivo in archivos_seleccionados or []
    }


def validar_archivos_manual(archivos_dict: dict[str, object]) -> pd.DataFrame:
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
                "origen": "Carga manual",
            }
        )

    return pd.DataFrame(registros)


def cargar_archivos_manual(
    archivos_dict: dict[str, object],
) -> tuple[dict[str, pd.DataFrame], dict[str, dict], pd.DataFrame, list[dict]]:
    dataframes_cargados: dict[str, pd.DataFrame] = {}
    config_carga: dict[str, dict] = {}
    errores_carga: list[dict] = []

    df_validacion = validar_archivos_manual(archivos_dict)
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
            df, config = cargar_archivo_manual(archivo)

            dataframes_cargados[nombre_df] = df

            config_carga[nombre_df] = {
                "archivo": nombre_archivo,
                "filas": df.shape[0],
                "columnas": df.shape[1],
                "peso_kb": round(archivo.size / 1024, 2),
                "encoding": config.get("encoding"),
                "separador": config.get("separador"),
                "formato_detectado": config.get("formato_detectado"),
                "origen": "Carga manual",
            }

        except Exception as exc:
            errores_carga.append(
                {
                    "dataframe": nombre_df,
                    "archivo": nombre_archivo,
                    "origen": "Carga manual",
                    "error": str(exc),
                }
            )

        progress_bar.progress(i / total)

    estado.empty()
    progress_bar.empty()

    return dataframes_cargados, config_carga, df_validacion, errores_carga


# ============================================================
# Validación y carga SharePoint
# ============================================================

def validar_archivos_sharepoint() -> pd.DataFrame:
    registros: list[dict[str, object]] = []

    for archivo in construir_archivos_sharepoint():
        registros.append(
            {
                "dataframe": archivo["dataframe"],
                "archivo": archivo["archivo"],
                "estado": "Configurado",
                "existe": True,
                "peso_kb": None,
                "origen": "SharePoint",
                "orden": archivo["orden"],
            }
        )

    return pd.DataFrame(registros)


def cargar_archivos_sharepoint() -> tuple[
    dict[str, pd.DataFrame],
    dict[str, dict],
    pd.DataFrame,
    list[dict],
]:
    dataframes_cargados: dict[str, pd.DataFrame] = {}
    config_carga: dict[str, dict] = {}
    errores_carga: list[dict] = []

    archivos_sharepoint = construir_archivos_sharepoint()
    df_validacion = validar_archivos_sharepoint()

    progress_bar = st.progress(0)
    estado = st.empty()
    total = len(archivos_sharepoint)

    for i, archivo in enumerate(archivos_sharepoint, start=1):
        nombre_df = archivo["dataframe"]
        nombre_archivo = archivo["archivo"]
        url = archivo["url"]

        estado.info(f"Descargando y cargando {nombre_archivo} ({i}/{total})...")

        try:
            contenido, metadata = descargar_archivo_sharepoint_cache(url)

            nombre_detectado = metadata.get("nombre_detectado") or nombre_archivo
            content_type = metadata.get("content_type") or ""

            df, config = cargar_archivo_desde_bytes(
                contenido=contenido,
                nombre_archivo=nombre_detectado or nombre_archivo,
                content_type=content_type,
            )

            dataframes_cargados[nombre_df] = df

            peso_kb = round(len(contenido) / 1024, 2)

            config_carga[nombre_df] = {
                "archivo": nombre_archivo,
                "archivo_detectado": nombre_detectado,
                "filas": df.shape[0],
                "columnas": df.shape[1],
                "peso_kb": peso_kb,
                "encoding": config.get("encoding"),
                "separador": config.get("separador"),
                "formato_detectado": config.get("formato_detectado"),
                "origen": "SharePoint",
                "orden": archivo["orden"],
            }

            df_validacion.loc[
                df_validacion["dataframe"] == nombre_df,
                ["estado", "peso_kb"],
            ] = ["Cargado", peso_kb]

        except Exception as exc:
            errores_carga.append(
                {
                    "dataframe": nombre_df,
                    "archivo": nombre_archivo,
                    "origen": "SharePoint",
                    "orden": archivo["orden"],
                    "error": str(exc),
                }
            )

            df_validacion.loc[
                df_validacion["dataframe"] == nombre_df,
                "estado",
            ] = "Error"

        progress_bar.progress(i / total)

    estado.empty()
    progress_bar.empty()

    if not dataframes_cargados:
        raise ValueError(
            "No se pudo cargar ningún archivo desde SharePoint. "
            "Revisa los enlaces, permisos y configuración en Secrets."
        )

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
        if not df_validacion.empty and "peso_kb" in df_validacion.columns
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Esperados", total)
    col2.metric("Disponibles", encontrados)
    col3.metric("Faltantes", faltantes)
    col4.metric("Peso cargado", f"{peso_total_mb:.2f} MB")

    if faltantes:
        st.warning(f"Hay {faltantes} archivo(s) faltante(s). Se cargaron solo los disponibles.")
    else:
        st.success("Todos los archivos esperados están disponibles.")


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
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)


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

            st.dataframe(df_tipos, use_container_width=True, hide_index=True)


def mostrar_errores(errores: list[dict]) -> None:
    if errores:
        with st.expander("Ver errores de carga", expanded=True):
            st.dataframe(
                pd.DataFrame(errores),
                use_container_width=True,
                hide_index=True,
            )


def mostrar_uso_modulos() -> None:
    with st.expander("Uso en otros módulos", expanded=False):
        st.code(
            'dataframes = st.session_state["dataframes_cargados"]\n'
            'df_me3n = dataframes["df_me3n"]\n'
            '\n'
            '# También quedan disponibles directamente:\n'
            'df_me3n = st.session_state["df_me3n"]\n'
            'df_moneda = st.session_state["df_moneda_cambio"]',
            language="python",
        )


# ============================================================
# App principal
# ============================================================

mostrar_encabezado()
st.divider()

metodo_carga = st.radio(
    "Método de carga",
    options=[
        "Cargar archivos",
        "Conexión SharePoint",
    ],
    horizontal=True,
)

with st.container(border=True):
    if metodo_carga == "Cargar archivos":
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
            boton_cargar_manual = st.button(
                "Validar y cargar archivos",
                type="primary",
                use_container_width=True,
                disabled=not archivos_seleccionados,
            )

        with col_limpiar:
            boton_limpiar_manual = st.button(
                "Limpiar",
                use_container_width=True,
                key="limpiar_manual",
            )

        if boton_limpiar_manual:
            limpiar_estado_carga()
            st.rerun()

        if boton_cargar_manual:
            limpiar_estado_carga()

            archivos_dict = construir_mapa_archivos(archivos_seleccionados)

            try:
                dataframes, config, df_validacion, errores = cargar_archivos_manual(
                    archivos_dict
                )

                guardar_dataframes_en_sesion(
                    dataframes=dataframes,
                    config=config,
                    df_validacion=df_validacion,
                    errores=errores,
                    metodo="Carga manual",
                )

                st.success(
                    f"Carga finalizada. Se cargaron {len(dataframes)} DataFrame(s)."
                )

            except Exception as exc:
                st.error(str(exc))

    if metodo_carga == "Conexión SharePoint":
        st.subheader("Conexión SharePoint")

        st.caption(
            "Carga los 11 archivos configurados en Secrets, respetando el orden de las URLs."
        )

        with st.form("form_sharepoint_archivos"):
            clave_sharepoint = st.text_input(
                "Clave de conexión",
                type="password",
                placeholder="Ingresa la clave autorizada",
            )

            conectar = st.form_submit_button(
                "Conectar y cargar archivos",
                type="primary",
                use_container_width=True,
            )

        col_limpiar_sp, _ = st.columns([1, 3])

        with col_limpiar_sp:
            boton_limpiar_sp = st.button(
                "Limpiar",
                use_container_width=True,
                key="limpiar_sharepoint",
            )

        if boton_limpiar_sp:
            limpiar_estado_carga()
            st.rerun()

        if conectar:
            limpiar_estado_carga()

            try:
                if not validar_clave_sharepoint(clave_sharepoint):
                    st.error("Clave incorrecta.")
                else:
                    dataframes, config, df_validacion, errores = cargar_archivos_sharepoint()

                    guardar_dataframes_en_sesion(
                        dataframes=dataframes,
                        config=config,
                        df_validacion=df_validacion,
                        errores=errores,
                        metodo="SharePoint",
                    )

                    st.success(
                        f"Conexión realizada correctamente. "
                        f"Se cargaron {len(dataframes)} DataFrame(s)."
                    )

            except Exception as exc:
                st.error(
                    "No se pudo completar la carga desde SharePoint. "
                    "Revisa la configuración en Secrets, permisos de enlaces y clave."
                )

                with st.expander("Detalle técnico", expanded=False):
                    st.write(str(exc))


if st.session_state["carga_completada"]:
    df_validacion = st.session_state["df_validacion_archivos"]
    dataframes_cargados = st.session_state["dataframes_cargados"]
    config_carga = st.session_state["config_carga"]
    errores_carga = st.session_state["errores_carga"]

    st.divider()
    st.subheader("Resultado de la carga")

    metodo_activo = st.session_state.get("metodo_carga_activo")
    if metodo_activo:
        st.caption(f"Método usado: **{metodo_activo}**")

    mostrar_metricas_validacion(df_validacion)
    mostrar_resumen_carga(config_carga, dataframes_cargados)

    with st.expander("Ver validación archivo por archivo", expanded=False):
        columnas_mostrar = [
            col for col in [
                "orden",
                "dataframe",
                "archivo",
                "estado",
                "peso_kb",
                "origen",
            ]
            if col in df_validacion.columns
        ]

        st.dataframe(
            df_validacion[columnas_mostrar],
            use_container_width=True,
            hide_index=True,
        )

    mostrar_errores(errores_carga)
    mostrar_vista_previa(dataframes_cargados)
    mostrar_uso_modulos()

else:
    st.info(
        "La vista de validación, resumen y previews aparecerá después de cargar los archivos."
    )
