import pandas as pd
import requests
from io import StringIO, BytesIO
import streamlit as st


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
    layout="wide"
)

st.title("Consulta UTM SII por años")

st.write(
    "Selecciona los años a consultar. La aplicación descargará la tabla UTM "
    "del SII para cada año seleccionado y generará un Excel consolidado."
)

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
            st.dataframe(resumen_utm, use_container_width=True)
        else:
            st.error("No se pudo generar el resumen UTM.")

        if not errores_utm.empty:
            st.warning("Algunos años presentaron errores.")
            st.dataframe(errores_utm, use_container_width=True)


if "resumen_utm" in st.session_state:
    resumen_utm = st.session_state["resumen_utm"]
    errores_utm = st.session_state["errores_utm"]

    if not resumen_utm.empty:
        excel_utm = crear_excel_utm(resumen_utm, errores_utm)

        st.download_button(
            label="Descargar Excel UTM",
            data=excel_utm,
            file_name="resumen_utm_sii.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )