# ============================================================
# APP_CARGAR_ARCHIVO_MEJORADO_SHAREPOINT.py
# 01_CARGA_ARCHIVOS
# Carga manual o desde SharePoint con clave
# Admite nombres con fecha final: _YYYYMMDD
# Ejemplo: 01_BD_Moneda_Cambio_20260728.xlsx
# ============================================================

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
from urllib.parse import urlparse, unquote
import base64
import csv
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
#
# Los archivos reales pueden incorporar una fecha al final:
#   01_BD_Moneda_Cambio_20260728.xlsx
#   02_ME2N_Ordenes_20260728.csv
#
# También se acepta el nombre sin fecha.
#
# IMPORTANTE:
# El orden del diccionario se utiliza para asociar las URLs de
# SharePoint configuradas en secrets.toml.
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
PATRON_FECHA_ARCHIVO = re.compile(r"_(\d{8})$", flags=re.IGNORECASE)


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
    """Limpia únicamente la información generada por la carga."""
    st.session_state["dataframes_cargados"] = {}
    st.session_state["config_carga"] = {}
    st.session_state["df_validacion_archivos"] = pd.DataFrame()
    st.session_state["errores_carga"] = []
    st.session_state["carga_completada"] = False
    st.session_state["metodo_carga_activo"] = None

    for nombre_df in ARCHIVOS_ESPERADOS:
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

    for nombre_df, df in dataframes.items():
        st.session_state[nombre_df] = df


# ============================================================
# Nombres y fechas de archivos
# ============================================================

def analizar_nombre_archivo(nombre_archivo: str) -> dict[str, object]:
    """
    Separa nombre base, extensión y fecha final YYYYMMDD.

    Ejemplo:
        01_BD_Moneda_Cambio_20260728.xlsx

    Devuelve:
        nombre_base: 01_BD_Moneda_Cambio
        extension: .xlsx
        fecha_archivo: Timestamp('2026-07-28')
        fecha_archivo_iso: 2026-07-28
        fecha_archivo_texto: 28/07/2026
    """
    nombre_limpio = unquote(Path(str(nombre_archivo)).name).strip()
    ruta = Path(nombre_limpio)
    extension = ruta.suffix.lower()
    stem = ruta.stem.strip()

    coincidencia = PATRON_FECHA_ARCHIVO.search(stem)
    fecha = pd.NaT
    nombre_base = stem

    if coincidencia:
        texto_fecha = coincidencia.group(1)
        fecha_convertida = pd.to_datetime(
            texto_fecha,
            format="%Y%m%d",
            errors="coerce",
        )

        if not pd.isna(fecha_convertida):
            fecha = fecha_convertida
            nombre_base = stem[:coincidencia.start()].rstrip("_- ")

    return {
        "nombre_original": nombre_limpio,
        "nombre_base": nombre_base,
        "nombre_base_normalizado": nombre_base.casefold(),
        "extension": extension,
        "fecha_archivo": fecha,
        "fecha_archivo_iso": (
            fecha.strftime("%Y-%m-%d") if not pd.isna(fecha) else None
        ),
        "fecha_archivo_texto": (
            fecha.strftime("%d/%m/%Y") if not pd.isna(fecha) else "Sin fecha"
        ),
    }


def nombre_corresponde(
    nombre_real: str,
    nombre_esperado: str,
) -> bool:
    """
    Compara nombres ignorando una fecha final _YYYYMMDD.

    La extensión debe coincidir, excepto que ambos formatos pertenezcan
    al grupo Excel (.xlsx/.xls).
    """
    real = analizar_nombre_archivo(nombre_real)
    esperado = analizar_nombre_archivo(nombre_esperado)

    if real["nombre_base_normalizado"] != esperado["nombre_base_normalizado"]:
        return False

    ext_real = str(real["extension"])
    ext_esperada = str(esperado["extension"])

    grupo_excel = {".xlsx", ".xls"}

    if ext_real == ext_esperada:
        return True

    if ext_real in grupo_excel and ext_esperada in grupo_excel:
        return True

    return False


def seleccionar_version_mas_reciente(archivos: list[object]) -> object:
    """
    Si se suben varias versiones del mismo archivo, selecciona:
    1. La de fecha YYYYMMDD más reciente.
    2. Si ninguna tiene fecha, la última de la lista.
    """
    if not archivos:
        raise ValueError("No hay archivos para seleccionar.")

    def clave(archivo: object) -> tuple[int, pd.Timestamp]:
        info = analizar_nombre_archivo(getattr(archivo, "name", ""))
        fecha = info["fecha_archivo"]

        if pd.isna(fecha):
            return (0, pd.Timestamp.min)

        return (1, pd.Timestamp(fecha))

    return max(archivos, key=clave)


def construir_mapa_archivos(
    archivos_seleccionados,
) -> dict[str, object]:
    """
    Asocia cada nombre esperado con el archivo real correspondiente.

    Acepta:
        01_BD_Moneda_Cambio.xlsx
        01_BD_Moneda_Cambio_20260728.xlsx

    Si hay varias fechas del mismo archivo, conserva la más reciente.
    """
    archivos = list(archivos_seleccionados or [])
    mapa: dict[str, object] = {}

    for nombre_esperado in ARCHIVOS_ESPERADOS.values():
        candidatos = [
            archivo
            for archivo in archivos
            if nombre_corresponde(archivo.name, nombre_esperado)
        ]

        if candidatos:
            mapa[nombre_esperado] = seleccionar_version_mas_reciente(candidatos)

    return mapa


# ============================================================
# Logo e interfaz
# ============================================================

def mostrar_logo_centrado() -> None:
    if not LOGO_PATH.exists():
        return

    logo_svg = LOGO_PATH.read_text(encoding="utf-8")
    logo_base64 = base64.b64encode(
        logo_svg.encode("utf-8")
    ).decode("utf-8")

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
    except Exception as exc:
        raise ValueError(
            "No se encontró sharepoint_archivos.access_key_sha256 en Secrets."
        ) from exc

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
    except Exception as exc:
        raise ValueError(
            "No se encontró sharepoint_archivos.urls en Secrets."
        ) from exc

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


def limpiar_valor_csv(valor: object) -> object:
    if not isinstance(valor, str):
        return valor

    texto = valor.strip()

    if len(texto) >= 2 and texto[0] == "'" and texto[-1] == "'":
        texto = texto[1:-1].strip()

    return texto


def construir_df_desde_texto_csv(
    texto: str,
    nombre_archivo: str,
    encoding: str,
) -> tuple[pd.DataFrame, dict[str, str]]:
    texto = texto.replace("\ufeff", "").replace("\x00", "")

    lineas = [linea for linea in texto.splitlines() if linea.strip()]

    if not lineas:
        raise ValueError("El archivo no contiene líneas legibles.")

    candidatos_sep = [";", ",", "\t", "|"]
    muestra = lineas[:50]
    puntajes = {
        sep: sum(linea.count(sep) for linea in muestra)
        for sep in candidatos_sep
    }

    mejor_sep = max(puntajes, key=puntajes.get)

    if puntajes[mejor_sep] <= 0:
        raise ValueError(
            "No se detectó separador CSV válido en las primeras líneas."
        )

    filas: list[list[object]] = []

    lector = csv.reader(
        StringIO("\n".join(lineas)),
        delimiter=mejor_sep,
        quotechar='"',
        escapechar="\\",
        doublequote=True,
        skipinitialspace=True,
    )

    for fila in lector:
        fila_limpia = [limpiar_valor_csv(celda) for celda in fila]

        if any(str(celda).strip() for celda in fila_limpia):
            filas.append(fila_limpia)

    if not filas:
        raise ValueError("No se pudieron construir filas desde el CSV.")

    max_columnas = max(len(fila) for fila in filas)

    if max_columnas <= 1:
        raise ValueError(
            "El archivo se leyó como una sola columna. "
            "No se pudo separar correctamente."
        )

    filas_normalizadas = [
        fila + [""] * (max_columnas - len(fila))
        for fila in filas
    ]

    encabezados = [
        str(col).strip().replace("\ufeff", "")
        for col in filas_normalizadas[0]
    ]

    encabezados_limpios: list[str] = []
    usados: dict[str, int] = {}

    for i, col in enumerate(encabezados, start=1):
        nombre_col = col if col else f"columna_{i}"

        if nombre_col in usados:
            usados[nombre_col] += 1
            nombre_col = f"{nombre_col}_{usados[nombre_col]}"
        else:
            usados[nombre_col] = 1

        encabezados_limpios.append(nombre_col)

    datos = filas_normalizadas[1:]
    df = pd.DataFrame(datos, columns=encabezados_limpios)
    df = df.dropna(axis=1, how="all")

    if df.empty and len(filas_normalizadas) > 1:
        raise ValueError("El CSV fue separado, pero no contiene datos.")

    return limpiar_columnas(df), {
        "encoding": encoding,
        "separador": mejor_sep,
        "lector": "csv.reader",
    }


def leer_csv_robusto_bytes(
    contenido: bytes,
    nombre_archivo: str,
) -> tuple[pd.DataFrame, dict[str, str]]:
    encodings = [
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "latin1",
        "cp1252",
        "ISO-8859-1",
    ]

    separadores = [";", ",", "\t", "|", None]
    errores: list[str] = []

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
                        "separador": "Automático" if sep is None else sep,
                        "lector": "pandas",
                    }
                    mejor_score = score

            except Exception as exc:
                errores.append(
                    f"pandas encoding={encoding} sep={sep}: {exc}"
                )

    if mejor_df is not None and mejor_config is not None:
        return limpiar_columnas(mejor_df), mejor_config

    for encoding in encodings:
        try:
            texto = contenido.decode(encoding, errors="replace")
            return construir_df_desde_texto_csv(
                texto=texto,
                nombre_archivo=nombre_archivo,
                encoding=encoding,
            )
        except Exception as exc:
            errores.append(f"csv.reader encoding={encoding}: {exc}")

    inicio_hex = contenido[:40].hex(" ")
    inicio_texto = ""

    for encoding in encodings:
        try:
            inicio_texto = contenido[:300].decode(
                encoding,
                errors="replace",
            )
            break
        except Exception:
            continue

    raise ValueError(
        f"No se pudo leer correctamente el CSV: {nombre_archivo}. "
        f"Primeros bytes HEX: {inicio_hex}. "
        f"Inicio texto detectado: {inicio_texto[:200]}"
    )


def leer_excel_bytes(
    contenido: bytes,
) -> tuple[pd.DataFrame, dict[str, str]]:
    df = pd.read_excel(BytesIO(contenido))
    df = df.dropna(axis=1, how="all")

    return limpiar_columnas(df), {
        "encoding": "No aplica",
        "separador": "No aplica",
    }


def leer_parquet_bytes(
    contenido: bytes,
) -> tuple[pd.DataFrame, dict[str, str]]:
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

    if (
        len(contenido) >= 8
        and contenido[:4] == b"PAR1"
        and contenido[-4:] == b"PAR1"
    ):
        return "parquet"

    if contenido[:4] == b"PK\x03\x04":
        return "excel"

    if contenido[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
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

    return "csv"


def cargar_archivo_desde_bytes(
    contenido: bytes,
    nombre_archivo: str,
    content_type: str = "",
) -> tuple[pd.DataFrame, dict[str, str]]:
    nombre_archivo = unquote(str(nombre_archivo))

    formato = detectar_formato_archivo(
        contenido=contenido,
        nombre_archivo=nombre_archivo,
        content_type=content_type,
    )

    errores_intentos: list[str] = []
    orden_intentos = [formato]

    for candidato in ["excel", "csv", "parquet"]:
        if candidato not in orden_intentos:
            orden_intentos.append(candidato)

    for intento in orden_intentos:
        try:
            if intento == "csv":
                df, config = leer_csv_robusto_bytes(
                    contenido,
                    nombre_archivo,
                )
            elif intento == "excel":
                df, config = leer_excel_bytes(contenido)
            elif intento == "parquet":
                df, config = leer_parquet_bytes(contenido)
            else:
                continue

            config["formato_detectado"] = intento
            config["formato_sugerido"] = formato

            return df, config

        except Exception as exc:
            errores_intentos.append(f"{intento}: {exc}")

    raise ValueError(
        f"No se pudo leer correctamente el archivo: {nombre_archivo}. "
        f"Intentos realizados -> {' | '.join(errores_intentos)}"
    )


def cargar_archivo_manual(
    uploaded_file,
) -> tuple[pd.DataFrame, dict[str, str]]:
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


def extraer_nombre_content_disposition(
    content_disposition: str,
) -> str | None:
    if not content_disposition:
        return None

    match_utf = re.search(
        r"filename\*=UTF-8''([^;]+)",
        content_disposition,
        flags=re.IGNORECASE,
    )
    if match_utf:
        return unquote(match_utf.group(1).strip().strip('"'))

    match = re.search(
        r'filename="?([^";]+)"?',
        content_disposition,
        flags=re.IGNORECASE,
    )
    if match:
        return unquote(match.group(1).strip().strip('"'))

    return None


def detectar_nombre_desde_url(url: str) -> str | None:
    try:
        path = urlparse(url).path
        nombre = unquote(Path(path).name)

        if "." in nombre:
            return nombre
    except Exception:
        return None

    return None


@st.cache_data(show_spinner=False, ttl=300)
def descargar_archivo_sharepoint_cache(
    url: str,
) -> tuple[bytes, dict[str, str]]:
    url_descarga = preparar_url_descarga_sharepoint(url)

    response = requests.get(
        url_descarga,
        allow_redirects=True,
        timeout=90,
    )
    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        "",
    ).lower()

    contenido_inicio = response.content[:500].lower()

    if "text/html" in content_type or b"<html" in contenido_inicio:
        raise ValueError(
            "SharePoint devolvió HTML en vez del archivo. "
            "Verifica que el enlace permita descarga directa."
        )

    content_disposition = response.headers.get(
        "Content-Disposition",
        "",
    )

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
    archivos: list[dict[str, str]] = []

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

def validar_archivos_manual(
    archivos_dict: dict[str, object],
) -> pd.DataFrame:
    registros: list[dict[str, object]] = []

    for nombre_df, nombre_esperado in ARCHIVOS_ESPERADOS.items():
        archivo = archivos_dict.get(nombre_esperado)
        existe = archivo is not None

        info = (
            analizar_nombre_archivo(archivo.name)
            if existe
            else {}
        )

        registros.append(
            {
                "dataframe": nombre_df,
                "archivo_esperado": nombre_esperado,
                "archivo": archivo.name if existe else None,
                "fecha_archivo": info.get("fecha_archivo_texto"),
                "fecha_archivo_iso": info.get("fecha_archivo_iso"),
                "estado": "Encontrado" if existe else "Faltante",
                "existe": existe,
                "peso_kb": (
                    round(archivo.size / 1024, 2)
                    if existe
                    else None
                ),
                "origen": "Carga manual",
            }
        )

    return pd.DataFrame(registros)


def cargar_archivos_manual(
    archivos_dict: dict[str, object],
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, dict],
    pd.DataFrame,
    list[dict],
]:
    dataframes_cargados: dict[str, pd.DataFrame] = {}
    config_carga: dict[str, dict] = {}
    errores_carga: list[dict] = []

    df_validacion = validar_archivos_manual(archivos_dict)
    disponibles = df_validacion[df_validacion["existe"]]

    if disponibles.empty:
        raise ValueError(
            "No hay archivos esperados disponibles para cargar. "
            "Se acepta el nombre normal o con fecha final _YYYYMMDD."
        )

    progress_bar = st.progress(0)
    estado = st.empty()
    total = len(disponibles)

    for i, row in enumerate(disponibles.itertuples(index=False), start=1):
        nombre_df = row.dataframe
        nombre_esperado = row.archivo_esperado
        archivo = archivos_dict[nombre_esperado]
        nombre_real = archivo.name
        info_nombre = analizar_nombre_archivo(nombre_real)

        estado.info(f"Cargando {nombre_real} ({i}/{total})...")

        try:
            df, config = cargar_archivo_manual(archivo)

            dataframes_cargados[nombre_df] = df
            config_carga[nombre_df] = {
                "archivo_esperado": nombre_esperado,
                "archivo": nombre_real,
                "fecha_archivo": info_nombre["fecha_archivo_texto"],
                "fecha_archivo_iso": info_nombre["fecha_archivo_iso"],
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
                    "archivo": nombre_real,
                    "fecha_archivo": info_nombre["fecha_archivo_texto"],
                    "origen": "Carga manual",
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

    return (
        dataframes_cargados,
        config_carga,
        df_validacion,
        errores_carga,
    )


# ============================================================
# Validación y carga SharePoint
# ============================================================

def validar_archivos_sharepoint() -> pd.DataFrame:
    registros: list[dict[str, object]] = []

    for archivo in construir_archivos_sharepoint():
        registros.append(
            {
                "dataframe": archivo["dataframe"],
                "archivo_esperado": archivo["archivo"],
                "archivo": None,
                "fecha_archivo": None,
                "fecha_archivo_iso": None,
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
        nombre_esperado = archivo["archivo"]
        url = archivo["url"]

        estado.info(
            f"Descargando y cargando {nombre_esperado} ({i}/{total})..."
        )

        try:
            contenido, metadata = descargar_archivo_sharepoint_cache(url)

            nombre_detectado = (
                metadata.get("nombre_detectado")
                or nombre_esperado
            )
            content_type = metadata.get("content_type") or ""
            info_nombre = analizar_nombre_archivo(nombre_detectado)

            df, config = cargar_archivo_desde_bytes(
                contenido=contenido,
                nombre_archivo=nombre_detectado,
                content_type=content_type,
            )

            dataframes_cargados[nombre_df] = df
            peso_kb = round(len(contenido) / 1024, 2)

            config_carga[nombre_df] = {
                "archivo_esperado": nombre_esperado,
                "archivo": nombre_detectado,
                "fecha_archivo": info_nombre["fecha_archivo_texto"],
                "fecha_archivo_iso": info_nombre["fecha_archivo_iso"],
                "filas": df.shape[0],
                "columnas": df.shape[1],
                "peso_kb": peso_kb,
                "encoding": config.get("encoding"),
                "separador": config.get("separador"),
                "formato_detectado": config.get("formato_detectado"),
                "origen": "SharePoint",
                "orden": archivo["orden"],
            }

            mascara = df_validacion["dataframe"] == nombre_df

            df_validacion.loc[
                mascara,
                [
                    "archivo",
                    "fecha_archivo",
                    "fecha_archivo_iso",
                    "estado",
                    "peso_kb",
                ],
            ] = [
                nombre_detectado,
                info_nombre["fecha_archivo_texto"],
                info_nombre["fecha_archivo_iso"],
                "Cargado",
                peso_kb,
            ]

        except Exception as exc:
            errores_carga.append(
                {
                    "dataframe": nombre_df,
                    "archivo": nombre_esperado,
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

    return (
        dataframes_cargados,
        config_carga,
        df_validacion,
        errores_carga,
    )


# ============================================================
# Visualizaciones compactas
# ============================================================

def obtener_ultima_fecha(
    df_validacion: pd.DataFrame,
) -> pd.Timestamp | None:
    if (
        df_validacion.empty
        or "fecha_archivo_iso" not in df_validacion.columns
    ):
        return None

    fechas = pd.to_datetime(
        df_validacion["fecha_archivo_iso"],
        errors="coerce",
    ).dropna()

    if fechas.empty:
        return None

    return fechas.max()


def mostrar_metricas_validacion(
    df_validacion: pd.DataFrame,
) -> None:
    total = len(df_validacion)
    encontrados = (
        int(df_validacion["existe"].sum())
        if not df_validacion.empty
        else 0
    )
    faltantes = total - encontrados

    peso_total_mb = (
        df_validacion["peso_kb"].fillna(0).sum() / 1024
        if (
            not df_validacion.empty
            and "peso_kb" in df_validacion.columns
        )
        else 0
    )

    ultima_fecha = obtener_ultima_fecha(df_validacion)
    ultima_fecha_texto = (
        ultima_fecha.strftime("%d/%m/%Y")
        if ultima_fecha is not None
        else "Sin fecha"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Esperados", total)
    col2.metric("Disponibles", encontrados)
    col3.metric("Faltantes", faltantes)
    col4.metric("Peso cargado", f"{peso_total_mb:.2f} MB")
    col5.metric("Última fecha archivos", ultima_fecha_texto)

    if faltantes:
        st.warning(
            f"Hay {faltantes} archivo(s) faltante(s). "
            "Se cargaron solo los disponibles."
        )
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

    df_resumen = df_resumen.rename(
        columns={"index": "dataframe"}
    )

    columnas_prioritarias = [
        "dataframe",
        "orden",
        "archivo",
        "fecha_archivo",
        "archivo_esperado",
        "filas",
        "columnas",
        "peso_kb",
        "formato_detectado",
        "encoding",
        "separador",
        "origen",
    ]

    columnas_existentes = [
        columna
        for columna in columnas_prioritarias
        if columna in df_resumen.columns
    ]

    otras_columnas = [
        columna
        for columna in df_resumen.columns
        if columna not in columnas_existentes
        and columna != "fecha_archivo_iso"
    ]

    df_resumen = df_resumen[
        columnas_existentes + otras_columnas
    ]

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

    with st.expander(
        "Ver resumen técnico de carga",
        expanded=False,
    ):
        st.dataframe(
            df_resumen,
            use_container_width=True,
            hide_index=True,
        )


def mostrar_vista_previa(
    dataframes: dict[str, pd.DataFrame],
) -> None:
    if not dataframes:
        return

    with st.expander(
        "Ver vista previa de DataFrames",
        expanded=False,
    ):
        nombre_df = st.selectbox(
            "Selecciona un DataFrame",
            options=list(dataframes.keys()),
        )

        df = dataframes[nombre_df]

        st.caption(
            f"{nombre_df}: "
            f"{df.shape[0]:,} filas x {df.shape[1]:,} columnas"
        )

        st.dataframe(
            df.head(30),
            use_container_width=True,
        )

        with st.expander(
            "Columnas, tipos y nulos",
            expanded=False,
        ):
            df_tipos = pd.DataFrame(
                {
                    "columna": df.columns,
                    "tipo": df.dtypes.astype(str).values,
                    "nulos": df.isna().sum().values,
                    "nulos_%": (
                        df.isna().mean().values * 100
                    ).round(2),
                }
            )

            st.dataframe(
                df_tipos,
                use_container_width=True,
                hide_index=True,
            )


def mostrar_errores(errores: list[dict]) -> None:
    if errores:
        with st.expander(
            "Ver errores de carga",
            expanded=True,
        ):
            st.dataframe(
                pd.DataFrame(errores),
                use_container_width=True,
                hide_index=True,
            )


def mostrar_uso_modulos() -> None:
    with st.expander(
        "Uso en otros módulos",
        expanded=False,
    ):
        st.code(
            'dataframes = st.session_state["dataframes_cargados"]\n'
            'df_me3n = dataframes["df_me3n"]\n'
            '\n'
            '# También quedan disponibles directamente:\n'
            'df_me3n = st.session_state["df_me3n"]\n'
            'df_moneda = st.session_state["df_moneda_cambio"]\n'
            '\n'
            '# Metadatos de carga y fecha del archivo:\n'
            'config = st.session_state["config_carga"]\n'
            'fecha_me3n = config["df_me3n"]["fecha_archivo"]',
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
            "Selecciona los CSV/XLSX requeridos. "
            "Los nombres pueden terminar en _YYYYMMDD, por ejemplo: "
            "01_BD_Moneda_Cambio_20260728.xlsx. "
            "Si subes varias versiones del mismo archivo, se utilizará la más reciente."
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
            archivos_dict = construir_mapa_archivos(
                archivos_seleccionados
            )

            try:
                (
                    dataframes,
                    config,
                    df_validacion,
                    errores,
                ) = cargar_archivos_manual(archivos_dict)

                guardar_dataframes_en_sesion(
                    dataframes=dataframes,
                    config=config,
                    df_validacion=df_validacion,
                    errores=errores,
                    metodo="Carga manual",
                )

                st.success(
                    f"Carga finalizada. "
                    f"Se cargaron {len(dataframes)} DataFrame(s)."
                )

            except Exception as exc:
                st.error(str(exc))

    if metodo_carga == "Conexión SharePoint":
        st.subheader("Conexión SharePoint")

        st.caption(
            "Carga los 11 archivos configurados en Secrets, "
            "respetando el orden de las URLs. "
            "La fecha _YYYYMMDD se obtiene del nombre descargado."
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
                    (
                        dataframes,
                        config,
                        df_validacion,
                        errores,
                    ) = cargar_archivos_sharepoint()

                    guardar_dataframes_en_sesion(
                        dataframes=dataframes,
                        config=config,
                        df_validacion=df_validacion,
                        errores=errores,
                        metodo="SharePoint",
                    )

                    st.success(
                        "Conexión realizada correctamente. "
                        f"Se cargaron {len(dataframes)} DataFrame(s)."
                    )

            except Exception as exc:
                st.error(
                    "No se pudo completar la carga desde SharePoint. "
                    "Revisa la configuración en Secrets, "
                    "permisos de enlaces y clave."
                )

                with st.expander(
                    "Detalle técnico",
                    expanded=False,
                ):
                    st.write(str(exc))


if st.session_state["carga_completada"]:
    df_validacion = st.session_state["df_validacion_archivos"]
    dataframes_cargados = st.session_state["dataframes_cargados"]
    config_carga = st.session_state["config_carga"]
    errores_carga = st.session_state["errores_carga"]

    st.divider()
    st.subheader("Resultado de la carga")

    metodo_activo = st.session_state.get(
        "metodo_carga_activo"
    )

    if metodo_activo:
        st.caption(f"Método usado: **{metodo_activo}**")

    mostrar_metricas_validacion(df_validacion)
    mostrar_resumen_carga(
        config_carga,
        dataframes_cargados,
    )

    with st.expander(
        "Ver validación archivo por archivo",
        expanded=False,
    ):
        columnas_mostrar = [
            col
            for col in [
                "orden",
                "dataframe",
                "archivo",
                "fecha_archivo",
                "archivo_esperado",
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
        "La vista de validación, resumen y previews aparecerá "
        "después de cargar los archivos."
    )
