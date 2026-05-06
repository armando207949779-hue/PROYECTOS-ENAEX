import re
import base64
import unicodedata
from io import StringIO, BytesIO
from pathlib import Path
from urllib.parse import urljoin, unquote

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
# Configuración general
# =========================

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MESES_NUM = {
    "Ene": 1,
    "Feb": 2,
    "Mar": 3,
    "Abr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Ago": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dic": 12,
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Setiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
}

MESES_ABREV = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
]


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
# Utilidades
# =========================

def crear_fecha(anio, mes_numero):
    return pd.to_datetime(
        pd.Series(anio).astype(int).astype(str)
        + "-"
        + pd.Series(mes_numero).astype(int).astype(str)
        + "-01"
    )


def normalizar_texto(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)

    return texto


def convertir_numerico(serie):
    return pd.to_numeric(
        serie,
        errors="coerce"
    )


# =========================
# DÓLAR SII
# =========================

def encontrar_tabla_dolar(tablas):
    meses_abreviados = set(MESES_ABREV)

    for tabla in tablas:
        columnas = [str(col).strip() for col in tabla.columns]

        tiene_columna_dia = "Día" in columnas or "Dia" in columnas
        meses_en_columnas = meses_abreviados.intersection(columnas)
        texto_tabla = tabla.astype(str).to_string()
        tiene_promedio = "Promedio" in texto_tabla

        if tiene_columna_dia and len(meses_en_columnas) >= 8 and tiene_promedio:
            return tabla

    return None


@st.cache_data
def cargar_tabla_dolar(anio):
    url = f"https://www.sii.cl/valores_y_fechas/dolar/dolar{anio}.htm"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    tablas = pd.read_html(
        StringIO(response.text),
        decimal=",",
        thousands="."
    )

    return encontrar_tabla_dolar(tablas)


def obtener_resumen_mes_dolar(tabla, mes):
    tabla_temp = tabla.copy()

    columna_dia = "Día" if "Día" in tabla_temp.columns else "Dia"

    fila_promedio = tabla_temp[
        tabla_temp[columna_dia].astype(str).str.strip().str.lower() == "promedio"
    ]

    if not fila_promedio.empty:
        valor_promedio = fila_promedio[mes].iloc[0]
    else:
        valor_promedio = tabla_temp[mes].mean(skipna=True)

    tabla_dias = tabla_temp[
        pd.to_numeric(tabla_temp[columna_dia], errors="coerce").notna()
    ].copy()

    valores_mes = tabla_dias[[columna_dia, mes]].dropna(subset=[mes])

    if valores_mes.empty:
        ultimo_dia = None
        ultimo_valor = None
    else:
        ultimo_dia = valores_mes[columna_dia].iloc[-1]
        ultimo_valor = valores_mes[mes].iloc[-1]

    return ultimo_dia, ultimo_valor, valor_promedio


def generar_df_dolar(anios):
    registros = []

    for anio in anios:
        try:
            tabla_dolar = cargar_tabla_dolar(anio)

            if tabla_dolar is None:
                continue

            for mes in MESES_ABREV:
                if mes not in tabla_dolar.columns:
                    continue

                ultimo_dia, ultimo_valor, valor_promedio = obtener_resumen_mes_dolar(
                    tabla_dolar,
                    mes
                )

                mes_numero = MESES_NUM[mes]

                registros.append({
                    "Año": anio,
                    "Mes": mes_numero,
                    "Fecha": pd.Timestamp(year=anio, month=mes_numero, day=1),
                    "Dolar promedio SII": valor_promedio,
                    "Dolar ultimo observado SII": ultimo_valor,
                    "Dolar ultimo dia observado": ultimo_dia
                })

        except Exception as e:
            st.warning(f"Dólar SII {anio}: {e}")

    df = pd.DataFrame(registros)

    if not df.empty:
        df["Dolar promedio SII"] = convertir_numerico(df["Dolar promedio SII"])
        df["Dolar ultimo observado SII"] = convertir_numerico(df["Dolar ultimo observado SII"])

    return df


# =========================
# UTM SII
# =========================

@st.cache_data
def cargar_tabla_utm(anio):
    url = f"https://www.sii.cl/valores_y_fechas/utm/utm{anio}.htm"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    tablas = pd.read_html(
        StringIO(response.text),
        decimal=",",
        thousands="."
    )

    tabla_utm = tablas[0].copy()

    tabla_utm.columns = [
        "Mes texto",
        "UTM",
        "UTA",
        "IPC valor puntos SII",
        "UTM variacion mensual",
        "UTM variacion acumulado",
        "UTM variacion 12 meses"
    ]

    tabla_utm.insert(0, "Año", anio)

    return tabla_utm


def generar_df_utm(anios):
    tablas = []

    for anio in anios:
        try:
            tabla = cargar_tabla_utm(anio)
            tablas.append(tabla)

        except Exception as e:
            st.warning(f"UTM SII {anio}: {e}")

    if not tablas:
        return pd.DataFrame()

    df = pd.concat(tablas, ignore_index=True)

    df["Mes"] = df["Mes texto"].astype(str).str.strip().map(MESES_NUM)

    df = df.dropna(subset=["Año", "Mes"]).copy()

    df["Año"] = df["Año"].astype(int)
    df["Mes"] = df["Mes"].astype(int)

    df["Fecha"] = pd.to_datetime(
        df["Año"].astype(str)
        + "-"
        + df["Mes"].astype(str)
        + "-01"
    )

    columnas_numericas = [
        "UTM",
        "UTA",
        "IPC valor puntos SII",
        "UTM variacion mensual",
        "UTM variacion acumulado",
        "UTM variacion 12 meses"
    ]

    for columna in columnas_numericas:
        if columna in df.columns:
            df[columna] = convertir_numerico(df[columna])

    columnas_salida = [
        "Fecha",
        "Año",
        "Mes",
        "UTM",
        "UTA",
        "IPC valor puntos SII",
        "UTM variacion mensual",
        "UTM variacion acumulado",
        "UTM variacion 12 meses"
    ]

    return df[columnas_salida]


# =========================
# IPC INE
# =========================

URL_EXCEL_IPC_DIRECTA = (
    "https://www.ine.gob.cl/docs/default-source/"
    "%C3%ADndice-de-precios-al-consumidor/cuadros-estadisticos/"
    "base-anual-2023_100/series-de-tiempo/"
    "ipc-xls.xlsx?sfvrsn=5b901f39_70"
)


@st.cache_data
def descargar_excel_ipc_ine():
    response = requests.get(
        URL_EXCEL_IPC_DIRECTA,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    return response.content


def leer_excel_ipc_limpio(contenido_excel):
    df_raw = pd.read_excel(
        BytesIO(contenido_excel),
        sheet_name="IPC 2023=100",
        header=None
    )

    fila_header = df_raw[
        df_raw.apply(
            lambda fila: (
                fila.astype(str).str.strip().eq("Año").any()
                and fila.astype(str).str.strip().eq("Mes").any()
                and fila.astype(str).str.strip().eq("Glosa").any()
            ),
            axis=1
        )
    ].index[0]

    columnas = df_raw.iloc[fila_header].tolist()

    df_ipc = df_raw.iloc[fila_header + 1:].copy()
    df_ipc.columns = columnas
    df_ipc = df_ipc.dropna(how="all").reset_index(drop=True)

    df_ipc.columns = [
        str(col).strip()
        for col in df_ipc.columns
    ]

    return df_ipc


def generar_df_ipc_ine():
    try:
        contenido = descargar_excel_ipc_ine()
        df_ipc = leer_excel_ipc_limpio(contenido)

        df = df_ipc[
            df_ipc["Glosa"].astype(str).str.strip().eq("IPC General")
        ].copy()

        columnas_numericas = [
            "Año",
            "Mes",
            "Índice",
            "Variación Mensual (%)",
            "Variación Acumulada (%)",
            "Variación 12 Meses (%)"
        ]

        for columna in columnas_numericas:
            if columna in df.columns:
                df[columna] = convertir_numerico(df[columna])

        df = df.dropna(subset=["Año", "Mes", "Índice"]).copy()

        df["Año"] = df["Año"].astype(int)
        df["Mes"] = df["Mes"].astype(int)

        df["Fecha"] = pd.to_datetime(
            df["Año"].astype(str)
            + "-"
            + df["Mes"].astype(str)
            + "-01"
        )

        df = df.rename(
            columns={
                "Índice": "IPC INE indice",
                "Variación Mensual (%)": "IPC INE variacion mensual",
                "Variación Acumulada (%)": "IPC INE variacion acumulada",
                "Variación 12 Meses (%)": "IPC INE variacion 12 meses"
            }
        )

        columnas_salida = [
            "Fecha",
            "Año",
            "Mes",
            "IPC INE indice",
            "IPC INE variacion mensual",
            "IPC INE variacion acumulada",
            "IPC INE variacion 12 meses"
        ]

        return df[columnas_salida].sort_values("Fecha")

    except Exception as e:
        st.warning(f"IPC INE: {e}")
        return pd.DataFrame()


# =========================
# ICL INE
# =========================

URL_ARCHIVO_ICL = (
    "https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/"
    "cuadros-estadisticos/ir-icl-base-anual-2023-100/"
    "series-base-2023/tabulado_icl.xlsx?sfvrsn=43d76e7c_50"
)


@st.cache_data
def descargar_excel_icl():
    response = requests.get(
        URL_ARCHIVO_ICL,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    return response.content


def generar_df_icl():
    try:
        contenido = descargar_excel_icl()

        df = pd.read_excel(
            BytesIO(contenido),
            sheet_name="General"
        )

        columnas_actuales = {
            str(col).strip(): col
            for col in df.columns
        }

        columnas_necesarias = ["año", "mes", "índice"]

        for columna in columnas_necesarias:
            if columna not in columnas_actuales:
                return pd.DataFrame()

        df = df.rename(
            columns={
                columnas_actuales["año"]: "Año",
                columnas_actuales["mes"]: "Mes",
                columnas_actuales["índice"]: "ICL INE indice"
            }
        )

        df["Año"] = convertir_numerico(df["Año"])
        df["Mes"] = convertir_numerico(df["Mes"])
        df["ICL INE indice"] = convertir_numerico(df["ICL INE indice"])

        df = df.dropna(subset=["Año", "Mes", "ICL INE indice"]).copy()

        df["Año"] = df["Año"].astype(int)
        df["Mes"] = df["Mes"].astype(int)

        df["Fecha"] = pd.to_datetime(
            df["Año"].astype(str)
            + "-"
            + df["Mes"].astype(str)
            + "-01"
        )

        columnas_extra = {}

        for original, nuevo in {
            "var_mensual": "ICL INE variacion mensual",
            "var_acum": "ICL INE variacion acumulada",
            "var_12": "ICL INE variacion 12 meses"
        }.items():
            if original in columnas_actuales:
                df[nuevo] = convertir_numerico(df[columnas_actuales[original]])
                columnas_extra[nuevo] = nuevo

        columnas_salida = [
            "Fecha",
            "Año",
            "Mes",
            "ICL INE indice"
        ] + list(columnas_extra.keys())

        return df[columnas_salida].sort_values("Fecha")

    except Exception as e:
        st.warning(f"ICL INE: {e}")
        return pd.DataFrame()


# =========================
# MOP
# =========================

URL_PAGINA_MOP = (
    "https://planeamiento.mop.gob.cl/"
    "indices-y-precios-para-calculo-del-reajuste-polinomico/"
)

MESES_MOP = {
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

CONCEPTOS_OBJETIVO_MOP = {
    "Índice de precios al consumidor (1)": "MOP indice precios consumidor",
    "Índice de remuneraciones (2)": "MOP indice remuneraciones",
    "Petróleo Diesel (4)": "MOP petroleo diesel",
    "Dólar observado": "MOP dolar observado",
    "Petróleo Diesel de refinería CONCÓN": "MOP petroleo diesel refineria concon"
}


def extraer_mes_anio_desde_archivo_mop(archivo):
    nombre = normalizar_texto(archivo)

    nombre_limpio = re.sub(r"[_\-.]+", " ", nombre)
    nombre_limpio = re.sub(r"\s+", " ", nombre_limpio).strip()

    partes = nombre_limpio.split()

    mes_detectado = None
    numero_mes = None

    for mes, numero in MESES_MOP.items():
        if mes in partes:
            mes_detectado = mes
            numero_mes = numero
            break

    anio_match = re.search(r"(20\d{2})", nombre_limpio)
    anio_detectado = int(anio_match.group(1)) if anio_match else None

    return mes_detectado, numero_mes, anio_detectado


def obtener_valor_concepto_mop(df, concepto):
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

    if df_excel.empty:
        return df_excel

    df_excel["archivo"] = df_excel["url_decodificada"].str.split("/").str[-1]

    df_excel[["mes_texto", "Mes", "Año"]] = df_excel["archivo"].apply(
        lambda x: pd.Series(extraer_mes_anio_desde_archivo_mop(x))
    )

    df_excel = df_excel.dropna(subset=["Año", "Mes"]).copy()

    df_excel["Año"] = df_excel["Año"].astype(int)
    df_excel["Mes"] = df_excel["Mes"].astype(int)

    df_excel = df_excel.sort_values(["Año", "Mes"]).reset_index(drop=True)

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

    mes_texto, mes_numero, anio = extraer_mes_anio_desde_archivo_mop(archivo)

    registro = {
        "Año": anio,
        "Mes": mes_numero,
        "Fecha": pd.Timestamp(year=anio, month=mes_numero, day=1)
    }

    for concepto_original, nombre_columna in CONCEPTOS_OBJETIVO_MOP.items():
        registro[nombre_columna] = obtener_valor_concepto_mop(
            df,
            concepto_original
        )

    return registro


def generar_df_mop(anios):
    try:
        df_archivos = obtener_archivos_excel_mop()

        if df_archivos.empty:
            return pd.DataFrame()

        df_archivos = df_archivos[
            df_archivos["Año"].isin(anios)
        ].copy()

        if df_archivos.empty:
            return pd.DataFrame()

        registros = []

        barra = st.progress(0)
        estado = st.empty()

        total = len(df_archivos)

        for posicion, (_, row) in enumerate(df_archivos.iterrows(), start=1):
            estado.write(f"Procesando MOP {posicion} de {total}")

            try:
                registro = leer_archivo_excel_mop(
                    row["url_decodificada"],
                    row["archivo"]
                )
                registros.append(registro)
            except Exception as e:
                st.warning(f"MOP {row['archivo']}: {e}")

            barra.progress(posicion / total)

        barra.empty()
        estado.empty()

        df = pd.DataFrame(registros)

        if df.empty:
            return df

        for columna in df.columns:
            if columna not in ["Fecha", "Año", "Mes"]:
                df[columna] = convertir_numerico(df[columna])

        return df.sort_values("Fecha")

    except Exception as e:
        st.warning(f"MOP: {e}")
        return pd.DataFrame()


# =========================
# Consolidado
# =========================

def unir_dataframes_temporales(dataframes):
    dataframes_validos = [
        df for df in dataframes
        if df is not None and not df.empty
    ]

    if not dataframes_validos:
        return pd.DataFrame()

    df_final = dataframes_validos[0].copy()

    for df in dataframes_validos[1:]:
        df_final = pd.merge(
            df_final,
            df,
            on=["Fecha", "Año", "Mes"],
            how="outer"
        )

    df_final = df_final.sort_values(["Fecha"]).reset_index(drop=True)

    return df_final


def crear_excel_consolidado(df_consolidado):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_consolidado.to_excel(
            writer,
            sheet_name="Consolidado",
            index=False
        )

    return buffer.getvalue()


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="Consolidado Temporal ENAEX",
    page_icon="🏢",
    layout="wide"
)

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>Consolidado Temporal de Indicadores</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Genera una base unificada mensual con indicadores SII, INE y MOP.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# =========================
# Parámetros
# =========================

anios_disponibles = list(range(2009, 2027))
ultimos_3_anios = anios_disponibles[-3:]

st.subheader("Selecciona los años")

columnas_checkbox = st.columns(6)

anios_seleccionados = []

for posicion, anio in enumerate(anios_disponibles):
    columna_actual = columnas_checkbox[posicion % 6]

    with columna_actual:
        seleccionado = st.checkbox(
            str(anio),
            value=(anio in ultimos_3_anios),
            key=f"checkbox_anio_consolidado_{anio}"
        )

        if seleccionado:
            anios_seleccionados.append(anio)

st.write("Años seleccionados:", anios_seleccionados)

with st.expander("Fuentes a incluir"):
    incluir_dolar = st.checkbox("Dólar SII", value=True)
    incluir_utm = st.checkbox("UTM SII / IPC valor puntos SII", value=True)
    incluir_ipc_ine = st.checkbox("IPC INE", value=True)
    incluir_icl = st.checkbox("ICL INE", value=True)
    incluir_mop = st.checkbox("MOP reajuste polinómico", value=False)


# =========================
# Botón generar
# =========================

if st.button("Generar consolidado temporal"):
    if not anios_seleccionados:
        st.warning("Debes seleccionar al menos un año.")
    else:
        dataframes = []

        with st.spinner("Generando consolidado temporal..."):
            if incluir_dolar:
                st.write("Consultando Dólar SII...")
                df_dolar = generar_df_dolar(anios_seleccionados)
                dataframes.append(df_dolar)

            if incluir_utm:
                st.write("Consultando UTM SII...")
                df_utm = generar_df_utm(anios_seleccionados)
                dataframes.append(df_utm)

            if incluir_ipc_ine:
                st.write("Consultando IPC INE...")
                df_ipc_ine = generar_df_ipc_ine()

                if not df_ipc_ine.empty:
                    df_ipc_ine = df_ipc_ine[
                        df_ipc_ine["Año"].isin(anios_seleccionados)
                    ].copy()

                dataframes.append(df_ipc_ine)

            if incluir_icl:
                st.write("Consultando ICL INE...")
                df_icl = generar_df_icl()

                if not df_icl.empty:
                    df_icl = df_icl[
                        df_icl["Año"].isin(anios_seleccionados)
                    ].copy()

                dataframes.append(df_icl)

            if incluir_mop:
                st.write("Consultando MOP...")
                df_mop = generar_df_mop(anios_seleccionados)
                dataframes.append(df_mop)

            df_consolidado = unir_dataframes_temporales(dataframes)

        st.session_state["df_consolidado_temporal"] = df_consolidado

        if df_consolidado.empty:
            st.warning("No se generaron datos para el consolidado.")
        else:
            st.success("Consolidado temporal generado correctamente.")


# =========================
# Mostrar resultados
# =========================

if "df_consolidado_temporal" in st.session_state:
    df_consolidado = st.session_state["df_consolidado_temporal"]

    if not df_consolidado.empty:
        st.markdown("---")
        st.subheader("Tabla consolidada")

        st.dataframe(
            df_consolidado,
            use_container_width=True
        )

        columnas_graficables = [
            col for col in df_consolidado.columns
            if col not in ["Fecha", "Año", "Mes", "Dolar ultimo dia observado"]
            and pd.api.types.is_numeric_dtype(df_consolidado[col])
        ]

        if columnas_graficables:
            st.subheader("Gráfico temporal")

            columnas_seleccionadas = st.multiselect(
                "Selecciona indicadores para graficar",
                options=columnas_graficables,
                default=columnas_graficables[:1]
            )

            if columnas_seleccionadas:
                df_grafico = df_consolidado.set_index("Fecha")[columnas_seleccionadas]

                st.line_chart(df_grafico)
            else:
                st.info("Selecciona al menos un indicador para graficar.")

        excel_consolidado = crear_excel_consolidado(df_consolidado)

        st.download_button(
            label="Descargar Excel consolidado",
            data=excel_consolidado,
            file_name="consolidado_temporal_indicadores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )