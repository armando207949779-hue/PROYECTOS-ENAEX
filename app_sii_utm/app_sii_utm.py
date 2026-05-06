import pandas as pd
import requests
import base64
from io import StringIO, BytesIO
from pathlib import Path
import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# =========================
# Cargar tabla UTM por año
# =========================

@st.cache_data
def cargar_tabla_utm(anio):
    url = f"https://www.sii.cl/valores_y_fechas/utm/utm{anio}.htm"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    tablas = pd.read_html(
        StringIO(response.text),
        decimal=",",
        thousands="."
    )

    # En las páginas UTM del SII, la tabla principal suele ser la primera
    tabla_utm = tablas[0].copy()

    tabla_utm.columns = [
        "Mes",
        "UTM",
        "UTA",
        "IPC valor puntos",
        "Variacion mensual",
        "Variacion acumulado",
        "Variacion 12 meses"
    ]

    tabla_utm.insert(0, "Año", anio)

    return url, tabla_utm, len(tablas)


# =========================
# Generar resumen varios años
# =========================

def generar_resumen_utm(anios):
    tablas_anuales = []
    errores = []

    for anio in anios:
        try:
            url, tabla_utm, total_tablas = cargar_tabla_utm(anio)
            tablas_anuales.append(tabla_utm)

        except Exception as e:
            errores.append({
                "Año": anio,
                "Error": str(e)
            })

    if tablas_anuales:
        resumen = pd.concat(tablas_anuales, ignore_index=True)
    else:
        resumen = pd.DataFrame()

    errores_df = pd.DataFrame(errores)

    return resumen, errores_df


# =========================
# Preparar datos para gráfico temporal
# =========================

def preparar_datos_grafico_utm(resumen_utm):
    orden_meses = {
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
        "Dic": 12
    }

    df_grafico = resumen_utm.copy()

    if df_grafico.empty:
        return df_grafico

    df_grafico["Mes_limpio"] = (
        df_grafico["Mes"]
        .astype(str)
        .str.strip()
    )

    df_grafico["Mes_numero"] = df_grafico["Mes_limpio"].map(orden_meses)

    df_grafico["UTM"] = pd.to_numeric(
        df_grafico["UTM"],
        errors="coerce"
    )

    df_grafico = df_grafico.dropna(
        subset=["Año", "Mes_numero", "UTM"]
    )

    df_grafico["Fecha"] = pd.to_datetime(
        df_grafico["Año"].astype(int).astype(str)
        + "-"
        + df_grafico["Mes_numero"].astype(int).astype(str)
        + "-01"
    )

    df_grafico = df_grafico.sort_values("Fecha")

    return df_grafico


# =========================
# Crear Excel
# =========================

def crear_excel_utm(resumen, errores_df):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        resumen.to_excel(
            writer,
            sheet_name="UTM",
            index=False
        )

        if not errores_df.empty:
            errores_df.to_excel(
                writer,
                sheet_name="Errores",
                index=False
            )

    return buffer.getvalue()


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="UTM SII Chile",
    page_icon="🏢",
    layout="wide"
)


# =========================
# Encabezado con logo ENAEX centrado
# =========================

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


st.markdown(
    "<h1 style='text-align: center;'>Consulta UTM SII por años</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Selecciona los años a consultar. La aplicación descargará la tabla UTM
        del SII para cada año seleccionado y generará un Excel consolidado.
    </p>
    """,
    unsafe_allow_html=True
)


# =========================
# Selección de años
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
            key=f"checkbox_anio_utm_{anio}"
        )

        if seleccionado:
            anios_seleccionados.append(anio)

st.write("Años seleccionados:", anios_seleccionados)


# =========================
# Generar resumen UTM
# =========================

if st.button("Generar resumen UTM"):
    if not anios_seleccionados:
        st.warning("Debes seleccionar al menos un año.")
    else:
        with st.spinner("Generando resumen UTM..."):
            resumen_utm, errores_utm = generar_resumen_utm(anios_seleccionados)

        st.session_state["resumen_utm"] = resumen_utm
        st.session_state["errores_utm"] = errores_utm

        if not resumen_utm.empty:
            st.success("Resumen UTM generado correctamente.")
        else:
            st.error("No se pudo generar el resumen UTM.")


# =========================
# Mostrar resultados, gráfico y descarga
# =========================

if "resumen_utm" in st.session_state:
    resumen_utm = st.session_state["resumen_utm"]
    errores_utm = st.session_state["errores_utm"]

    if not resumen_utm.empty:
        st.subheader("Tabla resumen UTM")
        st.dataframe(resumen_utm, use_container_width=True)

        df_grafico_utm = preparar_datos_grafico_utm(resumen_utm)

        if not df_grafico_utm.empty:
            st.subheader("Gráfico temporal de la UTM")

            datos_linea_utm = df_grafico_utm.set_index("Fecha")["UTM"]

            st.line_chart(datos_linea_utm)
        else:
            st.info("No hay datos suficientes para generar el gráfico temporal de la UTM.")

        excel_utm = crear_excel_utm(resumen_utm, errores_utm)

        st.download_button(
            label="Descargar Excel UTM",
            data=excel_utm,
            file_name="resumen_utm_sii.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if not errores_utm.empty:
        st.warning("Algunos años presentaron errores.")
        st.dataframe(errores_utm, use_container_width=True)
