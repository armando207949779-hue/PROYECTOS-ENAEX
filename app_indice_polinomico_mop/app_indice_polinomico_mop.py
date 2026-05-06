import re
import base64
import unicodedata
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
# Configuración
# =========================

URL_PAGINA_MOP = (
    "https://planeamiento.mop.gob.cl/"
    "indices-y-precios-para-calculo-del-reajuste-polinomico/"
)

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

ITEMS_OBJETIVO = {
    1: {
        "nombre": "Índice de precios al consumidor (1)",
        "columna": "indice_precios_consumidor"
    },
    2: {
        "nombre": "Índice de remuneraciones (2)",
        "columna": "indice_remuneraciones"
    },
    3: {
        "nombre": "Petróleo Diesel (4)",
        "columna": "petroleo_diesel"
    },
    22: {
        "nombre": "Dólar observado",
        "columna": "dolar_observado"
    },
    27: {
        "nombre": "Petróleo Diesel de refinería CONCÓN",
        "columna": "petroleo_diesel_refineria_concon"
    }
}


# =========================
# Funciones auxiliares
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


def convertir_item_a_entero(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    if texto.isdigit():
        return int(texto)

    return None


def obtener_valor_item(df, item_objetivo):
    for _, fila in df.iterrows():
        item = fila[0] if len(fila) > 0 else pd.NA
        detalle = fila[1] if len(fila) > 1 else pd.NA
        unidad = fila[2] if len(fila) > 2 else pd.NA
        valor = fila[3] if len(fila) > 3 else pd.NA

        item_numero = convertir_item_a_entero(item)

        if item_numero == item_objetivo:
            return {
                "item": item_numero,
                "detalle": detalle,
                "unidad": unidad,
                "valor": valor
            }

    return {
        "item": item_objetivo,
        "detalle": pd.NA,
        "unidad": pd.NA,
        "valor": pd.NA
    }


# =========================
# Obtener archivos Excel MOP
# =========================

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


# =========================
# Leer archivo Excel MOP
# =========================

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

    for item_objetivo, configuracion in ITEMS_OBJETIVO.items():
        columna = configuracion["columna"]
        nombre_base = configuracion["nombre"]

        resultado_item = obtener_valor_item(
            df=df,
            item_objetivo=item_objetivo
        )

        detalle = resultado_item["detalle"]
        unidad = resultado_item["unidad"]
        valor = resultado_item["valor"]

        if pd.isna(detalle):
            nombre_item = f"{item_objetivo} ({nombre_base})"
        else:
            nombre_item = f"{item_objetivo} ({detalle})"

        registro[f"{columna}_nombre"] = nombre_item
        registro[f"{columna}_unidad"] = unidad
        registro[columna] = valor

    return registro


# =========================
# Generar resumen MOP
# =========================

def generar_resumen_mop(df_archivos_filtrado):
    registros = []
    errores = []

    total_archivos = len(df_archivos_filtrado)

    if total_archivos == 0:
        return pd.DataFrame(), pd.DataFrame()

    barra_progreso = st.progress(0)
    texto_estado = st.empty()

    for posicion, (_, row) in enumerate(df_archivos_filtrado.iterrows(), start=1):
        archivo = row["archivo"]
        url_archivo = row["url_decodificada"]

        texto_estado.write(
            f"Procesando archivo {posicion} de {total_archivos}"
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

    texto_estado.empty()
    barra_progreso.empty()

    df_resultado = pd.DataFrame(registros)

    if not df_resultado.empty:
        df_resultado = df_resultado.sort_values(
            ["año", "numero_mes"],
            ascending=[True, True]
        ).reset_index(drop=True)

        df_resultado["fecha"] = pd.to_datetime(
            df_resultado["año"].astype(int).astype(str)
            + "-"
            + df_resultado["numero_mes"].astype(int).astype(str)
            + "-01"
        )

    df_errores = pd.DataFrame(errores)

    return df_resultado, df_errores


# =========================
# Crear Excel de salida
# =========================

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
    page_icon="🏢",
    layout="wide"
)

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>MOP - Índices y precios para reajuste polinómico</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Consulta automática de archivos publicados por el MOP y generación de resumen mensual.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# =========================
# Cargar archivos disponibles
# =========================

try:
    df_archivos = obtener_archivos_excel_mop()

    if df_archivos.empty:
        st.warning("No se encontraron archivos Excel disponibles.")
    else:
        anios_disponibles = sorted(
            df_archivos["año"].dropna().unique().tolist(),
            reverse=True
        )

        ultimos_3_anios = anios_disponibles[:3]

        st.subheader("Selecciona los años")

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

        if st.button("Generar resumen MOP"):
            if not anios_seleccionados:
                st.warning("Debes seleccionar al menos un año.")
            else:
                df_archivos_filtrado = df_archivos[
                    df_archivos["año"].isin(anios_seleccionados)
                ].copy()

                df_archivos_filtrado = df_archivos_filtrado.sort_values(
                    ["año", "numero_mes"],
                    ascending=[True, True]
                )

                with st.spinner("Generando resumen MOP..."):
                    df_resultado, df_errores = generar_resumen_mop(
                        df_archivos_filtrado
                    )

                st.session_state["df_resultado_mop"] = df_resultado
                st.session_state["df_errores_mop"] = df_errores
                st.session_state["df_archivos_mop"] = df_archivos_filtrado

                if not df_resultado.empty:
                    st.success("Resumen generado correctamente.")
                else:
                    st.warning("No se generaron registros.")

except Exception as e:
    st.error(f"Error al cargar información del MOP: {e}")


# =========================
# Mostrar resultados
# =========================

if "df_resultado_mop" in st.session_state:
    df_resultado = st.session_state["df_resultado_mop"]
    df_errores = st.session_state["df_errores_mop"]

    if not df_resultado.empty:
        st.markdown("---")
        st.subheader("Tabla resumen MOP")

        columnas_mostrar = [
            "año",
            "mes",
            "numero_mes",

            "indice_precios_consumidor_nombre",
            "indice_precios_consumidor_unidad",
            "indice_precios_consumidor",

            "indice_remuneraciones_nombre",
            "indice_remuneraciones_unidad",
            "indice_remuneraciones",

            "petroleo_diesel_nombre",
            "petroleo_diesel_unidad",
            "petroleo_diesel",

            "dolar_observado_nombre",
            "dolar_observado_unidad",
            "dolar_observado",

            "petroleo_diesel_refineria_concon_nombre",
            "petroleo_diesel_refineria_concon_unidad",
            "petroleo_diesel_refineria_concon"
        ]

        columnas_mostrar = [
            col for col in columnas_mostrar
            if col in df_resultado.columns
        ]

        st.dataframe(
            df_resultado[columnas_mostrar],
            use_container_width=True
        )

        st.subheader("Gráfico temporal")

        opciones_grafico = {
            "1 (Índice de precios al consumidor)": "indice_precios_consumidor",
            "2 (Índice de remuneraciones)": "indice_remuneraciones",
            "3 (Petróleo Diesel (4))": "petroleo_diesel",
            "22 (Dólar observado)": "dolar_observado",
            "27 (Petróleo Diesel de refinería CONCÓN)": "petroleo_diesel_refineria_concon"
        }

        opciones_disponibles = {
            nombre: columna
            for nombre, columna in opciones_grafico.items()
            if columna in df_resultado.columns
        }

        indicador_seleccionado = st.selectbox(
            "Selecciona indicador para graficar",
            options=list(opciones_disponibles.keys())
        )

        columna_grafico = opciones_disponibles[indicador_seleccionado]

        df_grafico = df_resultado.copy()

        df_grafico[columna_grafico] = pd.to_numeric(
            df_grafico[columna_grafico],
            errors="coerce"
        )

        df_grafico = df_grafico.dropna(
            subset=["fecha", columna_grafico]
        )

        if not df_grafico.empty:
            datos_linea = df_grafico.set_index("fecha")[columna_grafico]

            st.line_chart(datos_linea)
        else:
            st.info("No hay datos suficientes para generar el gráfico.")

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

    if not df_errores.empty:
        with st.expander("Ver errores de procesamiento"):
            st.dataframe(
                df_errores,
                use_container_width=True
            )

    if "df_archivos_mop" in st.session_state:
        with st.expander("Ver archivos procesados"):
            df_archivos_procesados = st.session_state["df_archivos_mop"]

            st.dataframe(
                df_archivos_procesados[
                    ["año", "mes", "numero_mes", "archivo", "url_decodificada"]
                ],
                use_container_width=True
            )
