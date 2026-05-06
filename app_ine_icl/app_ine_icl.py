import re
import base64
from io import BytesIO
from urllib.parse import urljoin, unquote
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# =========================
# URLs INE
# =========================

URL_PAGINA_INE = (
    "https://www.ine.gob.cl/estadisticas-por-tema/"
    "mercado-laboral/remuneraciones-y-costos-laborales"
)

URL_ARCHIVO_BASE = (
    "https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/"
    "cuadros-estadisticos/ir-icl-base-anual-2023-100/"
    "series-base-2023/tabulado_icl.xlsx"
)

URL_ARCHIVO_DIRECTO_CONOCIDO = (
    "https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/"
    "cuadros-estadisticos/ir-icl-base-anual-2023-100/"
    "series-base-2023/tabulado_icl.xlsx?sfvrsn=43d76e7c_50"
)


# =========================
# Columnas requeridas
# =========================

COLUMNAS_REQUERIDAS = [
    "año",
    "mes",
    "estado",
    "índice",
    "var_mensual",
    "var_acum",
    "var_12"
]


# =========================
# Descargar Excel desde URL
# =========================

def descargar_url_excel(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    es_excel = (
        "spreadsheet" in content_type
        or "excel" in content_type
        or ".xlsx" in url.lower()
    )

    if not es_excel:
        raise ValueError(f"La URL no parece ser un Excel. Content-Type: {content_type}")

    return response.content, response.headers


# =========================
# Buscar URL del archivo tabulado_icl.xlsx
# =========================

def buscar_url_tabulado_icl():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        URL_PAGINA_INE,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    html = response.text

    hrefs = re.findall(
        r'href=["\'](.*?)["\']',
        html,
        flags=re.IGNORECASE
    )

    enlaces = []

    for href in hrefs:
        url_completa = urljoin(URL_PAGINA_INE, href)
        url_decodificada = unquote(url_completa)

        enlaces.append({
            "url": url_completa,
            "url_decodificada": url_decodificada
        })

    df_enlaces = pd.DataFrame(enlaces).drop_duplicates()

    if df_enlaces.empty:
        return None, df_enlaces

    df_tabulado = df_enlaces[
        df_enlaces["url_decodificada"]
        .str.lower()
        .str.contains("tabulado_icl.xlsx", na=False)
    ].copy()

    if df_tabulado.empty:
        return None, df_enlaces

    url_encontrada = df_tabulado.iloc[0]["url"]

    return url_encontrada, df_enlaces


# =========================
# Obtener Excel ICL
# =========================

@st.cache_data
def obtener_excel_icl():
    # 1. Intentar URL directa conocida completa
    try:
        contenido, headers = descargar_url_excel(URL_ARCHIVO_DIRECTO_CONOCIDO)

        return {
            "contenido": contenido,
            "url_usada": URL_ARCHIVO_DIRECTO_CONOCIDO,
            "metodo": "URL directa conocida completa",
            "headers": headers,
            "df_enlaces": None
        }

    except Exception:
        pass

    # 2. Intentar URL base sin sfvrsn
    try:
        contenido, headers = descargar_url_excel(URL_ARCHIVO_BASE)

        return {
            "contenido": contenido,
            "url_usada": URL_ARCHIVO_BASE,
            "metodo": "URL base hasta tabulado_icl.xlsx",
            "headers": headers,
            "df_enlaces": None
        }

    except Exception:
        pass

    # 3. Buscar automáticamente en la página INE
    try:
        url_encontrada, df_enlaces = buscar_url_tabulado_icl()

        if url_encontrada is not None:
            contenido, headers = descargar_url_excel(url_encontrada)

            return {
                "contenido": contenido,
                "url_usada": url_encontrada,
                "metodo": "Búsqueda automática por tabulado_icl.xlsx",
                "headers": headers,
                "df_enlaces": df_enlaces
            }

        return {
            "contenido": None,
            "url_usada": None,
            "metodo": "No encontrado automáticamente",
            "headers": None,
            "df_enlaces": df_enlaces
        }

    except Exception:
        return {
            "contenido": None,
            "url_usada": None,
            "metodo": "No encontrado automáticamente",
            "headers": None,
            "df_enlaces": None
        }


# =========================
# Leer hoja General
# =========================

def leer_hoja_general(archivo_excel):
    excel = pd.ExcelFile(archivo_excel)

    hojas = excel.sheet_names

    if "General" not in hojas:
        return None, hojas, "No se encontró la hoja 'General'."

    df_general = pd.read_excel(
        archivo_excel,
        sheet_name="General"
    )

    return df_general, hojas, None


# =========================
# Validar columnas
# =========================

def validar_columnas(df):
    columnas_actuales = [
        str(col).strip()
        for col in df.columns
    ]

    faltantes = [
        col for col in COLUMNAS_REQUERIDAS
        if col not in columnas_actuales
    ]

    return faltantes


# =========================
# Preparar datos ICL
# =========================

def preparar_datos_icl(archivo_bytes):
    archivo_para_leer = BytesIO(archivo_bytes)

    df_general, hojas, error_hoja = leer_hoja_general(archivo_para_leer)

    if error_hoja is not None:
        return None, error_hoja

    faltantes = validar_columnas(df_general)

    if faltantes:
        mensaje = (
            "La hoja General no tiene todas las columnas requeridas. "
            f"Columnas faltantes: {faltantes}"
        )
        return None, mensaje

    df_general = df_general.copy()

    df_general["año"] = pd.to_numeric(
        df_general["año"],
        errors="coerce"
    )

    df_general["mes"] = pd.to_numeric(
        df_general["mes"],
        errors="coerce"
    )

    df_general["índice"] = pd.to_numeric(
        df_general["índice"],
        errors="coerce"
    )

    df_general = df_general.dropna(
        subset=["año", "mes", "índice"]
    )

    df_general["año"] = df_general["año"].astype(int)
    df_general["mes"] = df_general["mes"].astype(int)

    df_general["fecha"] = pd.to_datetime(
        df_general["año"].astype(str)
        + "-"
        + df_general["mes"].astype(str)
        + "-01"
    )

    df_general = df_general.sort_values("fecha")

    return df_general, None


# =========================
# Crear Excel de salida
# =========================

def crear_excel_salida(df):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            sheet_name="General",
            index=False
        )

    return buffer.getvalue()


# =========================
# Mostrar logo centrado
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
                    style="width: 260px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="INE ICL",
    page_icon="🏢",
    layout="wide"
)

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>Índice de Remuneraciones y Costos Laborales</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Consulta automática del archivo ICL del INE y descarga de la hoja General.
    </p>
    """,
    unsafe_allow_html=True
)


# =========================
# Botón principal
# =========================

st.markdown("---")

if st.button("Generar resumen ICL"):
    with st.spinner("Buscando y procesando información del INE..."):
        resultado = obtener_excel_icl()

        if resultado["contenido"] is not None:
            df_general, error = preparar_datos_icl(resultado["contenido"])

            if error is None:
                st.session_state["df_general_icl"] = df_general
                st.session_state["url_usada_icl"] = resultado["url_usada"]
                st.session_state["metodo_descarga_icl"] = resultado["metodo"]

                st.success("Resumen ICL generado correctamente.")
            else:
                st.error(error)

        else:
            st.warning(
                "No se encontró automáticamente el archivo del INE. "
                "Puedes usar la carga manual disponible más abajo."
            )


# =========================
# Opción secundaria: carga manual
# =========================

with st.expander("Carga manual de archivo Excel"):
    archivo_subido = st.file_uploader(
        "Sube el archivo Excel del INE si la búsqueda automática no funciona",
        type=["xlsx", "xls"]
    )

    if archivo_subido is not None:
        archivo_bytes = archivo_subido.read()

        df_general, error = preparar_datos_icl(archivo_bytes)

        if error is None:
            st.session_state["df_general_icl"] = df_general
            st.session_state["url_usada_icl"] = "Archivo subido manualmente"
            st.session_state["metodo_descarga_icl"] = "Carga manual"

            st.success("Archivo procesado correctamente.")
        else:
            st.error(error)


# =========================
# Mostrar resultados
# =========================

if "df_general_icl" in st.session_state:
    df_general = st.session_state["df_general_icl"]

    st.markdown("---")
    st.subheader("Resumen ICL")

    anios = sorted(
        df_general["año"]
        .dropna()
        .unique()
        .tolist()
    )

    anio_filtro = st.selectbox(
        "Filtrar por año",
        options=["Todos"] + anios
    )

    df_filtrado = df_general.copy()

    if anio_filtro != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["año"] == anio_filtro
        ]

    st.dataframe(
        df_filtrado,
        use_container_width=True
    )

    st.subheader("Gráfico temporal del índice")

    df_grafico = df_filtrado.copy()

    if not df_grafico.empty:
        datos_linea = df_grafico.set_index("fecha")["índice"]

        st.line_chart(datos_linea)
    else:
        st.info("No hay datos suficientes para generar el gráfico.")

    excel_salida = crear_excel_salida(df_filtrado)

    st.download_button(
        label="Descargar Excel",
        data=excel_salida,
        file_name="ine_icl_general.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    with st.expander("Información técnica"):
        st.write("Método de descarga:")
        st.write(st.session_state.get("metodo_descarga_icl", "No disponible"))

        st.write("Fuente:")
        st.write(st.session_state.get("url_usada_icl", "No disponible"))
