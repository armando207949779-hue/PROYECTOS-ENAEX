import re
from io import BytesIO
from urllib.parse import urljoin, unquote

import pandas as pd
import requests
import streamlit as st


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

COLUMNAS_REQUERIDAS = [
    "año",
    "mes",
    "estado",
    "índice",
    "var_mensual",
    "var_acum",
    "var_12"
]


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

    # 2. Intentar URL base hasta tabulado_icl.xlsx, sin sfvrsn
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

    # 3. Buscar en la página cualquier link que contenga tabulado_icl.xlsx
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


def crear_excel_salida(df):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            sheet_name="General",
            index=False
        )

    return buffer.getvalue()


st.set_page_config(
    page_title="INE ICL - Hoja General",
    layout="wide"
)

st.title("INE - Índice de Remuneraciones y Costos Laborales")

st.write(
    "La aplicación busca el archivo `tabulado_icl.xlsx`. "
    "La parte posterior de la URL, como `?sfvrsn=...`, puede cambiar."
)


st.subheader("Paso 1: Buscar / descargar archivo INE")

if st.button("Buscar / descargar archivo"):
    resultado = obtener_excel_icl()

    if resultado["contenido"] is not None:
        st.session_state["archivo_bytes"] = resultado["contenido"]
        st.session_state["url_usada"] = resultado["url_usada"]
        st.session_state["metodo_descarga"] = resultado["metodo"]

        st.success("Archivo descargado correctamente.")

        st.write("Método usado:")
        st.write(resultado["metodo"])

        st.write("URL usada:")
        st.write(resultado["url_usada"])

        st.write("Tamaño bytes:")
        st.write(len(resultado["contenido"]))

        if resultado["headers"] is not None:
            st.write("Content-Type:")
            st.write(resultado["headers"].get("Content-Type"))

    else:
        st.warning("No se encontró automáticamente el archivo.")
        st.info("Puedes subir el Excel manualmente en el Paso 2.")

    if resultado["df_enlaces"] is not None:
        st.session_state["df_enlaces"] = resultado["df_enlaces"]


if "url_usada" in st.session_state:
    st.success("Archivo disponible en memoria.")
    st.write("Método:")
    st.write(st.session_state["metodo_descarga"])
    st.write("URL:")
    st.write(st.session_state["url_usada"])


if "df_enlaces" in st.session_state:
    with st.expander("Ver enlaces encontrados en la página"):
        st.dataframe(
            st.session_state["df_enlaces"],
            use_container_width=True
        )


st.subheader("Paso 2: Opción secundaria - subir archivo Excel")

archivo_subido = st.file_uploader(
    "Sube el archivo Excel si no fue posible descargarlo automáticamente",
    type=["xlsx", "xls"]
)

if archivo_subido is not None:
    st.session_state["archivo_bytes"] = archivo_subido.read()
    st.session_state["metodo_descarga"] = "Archivo subido manualmente"
    st.session_state["url_usada"] = "No aplica"

    st.success("Archivo subido correctamente.")


st.subheader("Paso 3: Leer hoja General")

if "archivo_bytes" not in st.session_state:
    st.info("Primero busca el archivo automáticamente o sube un Excel.")
else:
    try:
        archivo_para_leer = BytesIO(st.session_state["archivo_bytes"])

        df_general, hojas, error_hoja = leer_hoja_general(archivo_para_leer)

        st.write("Hojas disponibles:")
        st.write(hojas)

        if error_hoja is not None:
            st.error(error_hoja)

        else:
            faltantes = validar_columnas(df_general)

            if faltantes:
                st.error("La hoja General no tiene todas las columnas requeridas.")

                st.write("Columnas faltantes:")
                st.write(faltantes)

                st.write("Columnas encontradas:")
                st.write(list(df_general.columns))

            else:
                st.success("Hoja General leída correctamente.")

                st.dataframe(
                    df_general,
                    use_container_width=True
                )

                st.subheader("Paso 4: Filtro por año")

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

                st.subheader("Paso 5: Descargar Excel limpio")

                excel_salida = crear_excel_salida(df_filtrado)

                st.download_button(
                    label="Descargar Excel",
                    data=excel_salida,
                    file_name="ine_icl_general.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")