import re
import unicodedata
from io import BytesIO
from urllib.parse import urljoin, unquote

import pandas as pd
import requests
import streamlit as st


# =========================
# Configuración
# =========================

URL_PAGINA_MOP = "https://planeamiento.mop.gob.cl/indices-y-precios-para-calculo-del-reajuste-polinomico/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12
}

CONCEPTOS_OBJETIVO = {
    "Índice de precios al consumidor (1)": "indice_precios_consumidor",
    "Índice de remuneraciones (2)": "indice_remuneraciones",
    "Petróleo Diesel (4)": "petroleo_diesel",
    "Dólar observado": "dolar_observado",
    "Petróleo Diesel de refinería CONCÓN": "petroleo_diesel_refineria_concon"
}


# =========================
# Funciones auxiliares
# =========================

def normalizar_texto(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)

    return texto


def extraer_mes_anio_desde_archivo(archivo):
    nombre = normalizar_texto(archivo)

    nombre_limpio = re.sub(r"[_\-.]+", " ", nombre)
    nombre_limpio = re.sub(r"\s+", " ", nombre_limpio).strip()

    partes = nombre_limpio.split()

    mes_detectado = None
    numero_mes = None

    for mes, numero in MESES.items():
        if mes in partes:
            mes_detectado = mes
            numero_mes = numero
            break

    anio_match = re.search(r"(20\d{2})", nombre_limpio)
    anio_detectado = int(anio_match.group(1)) if anio_match else None

    return mes_detectado, numero_mes, anio_detectado


def obtener_valor_concepto(df, concepto):
    concepto_norm = normalizar_texto(concepto)

    for _, fila in df.iterrows():
        detalle = normalizar_texto(fila[1]) if len(fila) > 1 else ""

        if concepto_norm in detalle:
            if len(fila) > 3:
                return fila[3]
            return pd.NA

    return pd.NA


@st.cache_data
def obtener_archivos_excel_mop():
    response = requests.get(
        URL_PAGINA_MOP,
        headers=HEADERS,
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
        url_completa = urljoin(URL_PAGINA_MOP, href)
        url_decodificada = unquote(url_completa)

        enlaces.append({
            "url": url_completa,
            "url_decodificada": url_decodificada
        })

    df_enlaces = pd.DataFrame(enlaces).drop_duplicates()

    df_excel = df_enlaces[
        df_enlaces["url_decodificada"]
        .str.lower()
        .str.contains(r"\.xls|\.xlsx", regex=True, na=False)
    ].copy()

    df_excel["archivo"] = df_excel["url_decodificada"].str.split("/").str[-1]

    df_excel[["mes", "numero_mes", "año"]] = df_excel["archivo"].apply(
        lambda x: pd.Series(extraer_mes_anio_desde_archivo(x))
    )

    df_excel = df_excel.dropna(subset=["año", "numero_mes"]).copy()

    df_excel["año"] = df_excel["año"].astype(int)
    df_excel["numero_mes"] = df_excel["numero_mes"].astype(int)

    df_excel = df_excel.sort_values(
        ["año", "numero_mes"],
        ascending=[True, True]
    ).reset_index(drop=True)

    return df_excel


@st.cache_data
def leer_archivo_excel_mop(url_archivo, archivo):
    response = requests.get(
        url_archivo,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    contenido = response.content

    excel = pd.ExcelFile(BytesIO(contenido))

    hoja = "planilla" if "planilla" in excel.sheet_names else excel.sheet_names[0]

    df = pd.read_excel(
        BytesIO(contenido),
        sheet_name=hoja,
        header=None
    )

    mes, numero_mes, anio = extraer_mes_anio_desde_archivo(archivo)

    registro = {
        "año": anio,
        "mes": mes,
        "numero_mes": numero_mes,
        "archivo": archivo,
        "url": url_archivo,
        "hoja": hoja
    }

    for concepto_original, nombre_columna in CONCEPTOS_OBJETIVO.items():
        registro[nombre_columna] = obtener_valor_concepto(
            df,
            concepto_original
        )

    return registro


def generar_resumen_mop(df_archivos_filtrado):
    registros = []
    errores = []

    total_archivos = len(df_archivos_filtrado)

    barra_progreso = st.progress(0)
    texto_estado = st.empty()

    if total_archivos == 0:
        texto_estado.write("No hay archivos para procesar.")
        return pd.DataFrame(), pd.DataFrame()

    for posicion, (_, row) in enumerate(df_archivos_filtrado.iterrows(), start=1):
        archivo = row["archivo"]
        url_archivo = row["url_decodificada"]

        texto_estado.write(
            f"Procesando archivo {posicion} de {total_archivos}: {archivo}"
        )

        try:
            registro = leer_archivo_excel_mop(
                url_archivo=url_archivo,
                archivo=archivo
            )

            registros.append(registro)

        except Exception as e:
            errores.append({
                "archivo": archivo,
                "url": url_archivo,
                "error": str(e)
            })

        avance = posicion / total_archivos
        barra_progreso.progress(avance)

    texto_estado.write("Procesamiento finalizado.")

    df_resultado = pd.DataFrame(registros)

    if not df_resultado.empty:
        df_resultado = df_resultado.sort_values(
            ["año", "numero_mes"],
            ascending=[True, True]
        ).reset_index(drop=True)

    df_errores = pd.DataFrame(errores)

    return df_resultado, df_errores


def crear_excel_salida(df_resultado, df_errores):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_resultado.to_excel(
            writer,
            sheet_name="Resumen",
            index=False
        )

        if not df_errores.empty:
            df_errores.to_excel(
                writer,
                sheet_name="Errores",
                index=False
            )

    return buffer.getvalue()


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="MOP - Reajuste Polinómico",
    layout="wide"
)

st.title("MOP - Índices y precios para reajuste polinómico")

st.write(
    "Esta aplicación obtiene los archivos Excel publicados por el MOP y extrae "
    "los valores principales para cada mes y año disponible."
)


# =========================
# Paso 1: Buscar archivos
# =========================

st.subheader("Paso 1: Buscar archivos Excel disponibles")

if st.button("Buscar archivos MOP"):
    try:
        df_archivos = obtener_archivos_excel_mop()

        st.session_state["df_archivos_mop"] = df_archivos

        if df_archivos.empty:
            st.warning("No se encontraron archivos Excel.")
        else:
            st.success(f"Se encontraron {len(df_archivos)} archivos Excel.")
            st.dataframe(
                df_archivos[["año", "mes", "numero_mes", "archivo", "url_decodificada"]],
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error al buscar archivos: {e}")


if "df_archivos_mop" in st.session_state:
    df_archivos = st.session_state["df_archivos_mop"]

    st.success("Archivos disponibles cargados en memoria.")

    with st.expander("Ver archivos Excel encontrados"):
        st.dataframe(
            df_archivos[["año", "mes", "numero_mes", "archivo", "url_decodificada"]],
            use_container_width=True
        )

    # =========================
    # Paso 2: Seleccionar años
    # =========================

    st.subheader("Paso 2: Selecciona los años a consultar")

    anios_disponibles = sorted(
        df_archivos["año"].dropna().unique().tolist(),
        reverse=True
    )

    ultimos_3_anios = anios_disponibles[:3]

    columnas_checkbox = st.columns(6)

    anios_seleccionados = []

    for posicion, anio in enumerate(anios_disponibles):
        columna_actual = columnas_checkbox[posicion % 6]

        with columna_actual:
            seleccionado = st.checkbox(
                str(anio),
                value=(anio in ultimos_3_anios),
                key=f"checkbox_anio_mop_{anio}"
            )

            if seleccionado:
                anios_seleccionados.append(anio)

    st.write("Años seleccionados:", anios_seleccionados)

    df_archivos_filtrado = df_archivos[
        df_archivos["año"].isin(anios_seleccionados)
    ].copy()

    df_archivos_filtrado = df_archivos_filtrado.sort_values(
        ["año", "numero_mes"],
        ascending=[True, True]
    )

    st.write("Archivos que serán procesados:")

    st.dataframe(
        df_archivos_filtrado[["año", "mes", "numero_mes", "archivo"]],
        use_container_width=True
    )

    # =========================
    # Paso 3: Generar resumen
    # =========================

    st.subheader("Paso 3: Generar resumen")

    if st.button("Generar resumen MOP"):
        if not anios_seleccionados:
            st.warning("Debes seleccionar al menos un año.")
        else:
            df_resultado, df_errores = generar_resumen_mop(
                df_archivos_filtrado
            )

            st.session_state["df_resultado_mop"] = df_resultado
            st.session_state["df_errores_mop"] = df_errores

            if not df_resultado.empty:
                st.success("Resumen generado correctamente.")
                st.dataframe(
                    df_resultado,
                    use_container_width=True
                )
            else:
                st.warning("No se generaron registros.")

            if not df_errores.empty:
                st.warning("Algunos archivos presentaron errores.")
                st.dataframe(
                    df_errores,
                    use_container_width=True
                )


# =========================
# Paso 4: Mostrar y descargar
# =========================

if "df_resultado_mop" in st.session_state:
    st.subheader("Paso 4: Descargar Excel")

    df_resultado = st.session_state["df_resultado_mop"]
    df_errores = st.session_state["df_errores_mop"]

    df_resultado = df_resultado.sort_values(
        ["año", "numero_mes"],
        ascending=[True, True]
    ).reset_index(drop=True)

    st.dataframe(
        df_resultado,
        use_container_width=True
    )

    excel_salida = crear_excel_salida(
        df_resultado,
        df_errores
    )

    st.download_button(
        label="Descargar Excel MOP",
        data=excel_salida,
        file_name="mop_indices_reajuste_polinomico.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )