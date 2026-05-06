import pandas as pd
import requests
from io import StringIO, BytesIO
from pathlib import Path
import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo-vector-enaex.webp"


# =========================
# Detectar tabla dólar SII
# =========================

def encontrar_tabla_dolar(tablas):
    meses_abreviados = {
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    }

    for i, tabla in enumerate(tablas, start=1):
        columnas = [str(col).strip() for col in tabla.columns]

        tiene_columna_dia = "Día" in columnas or "Dia" in columnas
        meses_en_columnas = meses_abreviados.intersection(columnas)

        texto_tabla = tabla.astype(str).to_string()
        tiene_promedio = "Promedio" in texto_tabla

        if tiene_columna_dia and len(meses_en_columnas) >= 8 and tiene_promedio:
            return i, tabla

    return None, None


# =========================
# Cargar tabla dólar por año
# =========================

@st.cache_data
def cargar_tabla_dolar(anio):
    url = f"https://www.sii.cl/valores_y_fechas/dolar/dolar{anio}.htm"

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

    indice_tabla, tabla_dolar = encontrar_tabla_dolar(tablas)

    return url, indice_tabla, tabla_dolar, len(tablas)


# =========================
# Obtener promedio y último valor de un mes
# =========================

def obtener_resumen_mes(tabla, mes):
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


# =========================
# Generar resumen de varios años y todos los meses
# =========================

def generar_resumen_varios_anios_todos_los_meses(anios):
    meses = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    registros = []

    for anio in anios:
        try:
            url, indice_tabla, tabla_dolar, total_tablas = cargar_tabla_dolar(anio)

            if tabla_dolar is None:
                registros.append({
                    "Año": anio,
                    "Mes": "Todos",
                    "Valor dolar promedio": None,
                    "Valor ultimo observado": None,
                    "Último día observado": None,
                    "Estado": "No se encontró tabla"
                })
                continue

            for mes in meses:
                if mes not in tabla_dolar.columns:
                    registros.append({
                        "Año": anio,
                        "Mes": mes,
                        "Valor dolar promedio": None,
                        "Valor ultimo observado": None,
                        "Último día observado": None,
                        "Estado": "Mes no disponible"
                    })
                    continue

                ultimo_dia, ultimo_valor, valor_promedio = obtener_resumen_mes(
                    tabla_dolar,
                    mes
                )

                registros.append({
                    "Año": anio,
                    "Mes": mes,
                    "Valor dolar promedio": valor_promedio,
                    "Valor ultimo observado": ultimo_valor,
                    "Último día observado": ultimo_dia,
                    "Estado": "OK"
                })

        except Exception as e:
            registros.append({
                "Año": anio,
                "Mes": "Todos",
                "Valor dolar promedio": None,
                "Valor ultimo observado": None,
                "Último día observado": None,
                "Estado": f"Error: {e}"
            })

    return pd.DataFrame(registros)


# =========================
# Crear Excel en memoria
# =========================

def crear_excel_resumen(df):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            sheet_name="Resumen",
            index=False
        )

    return buffer.getvalue()


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="Resumen dólar SII",
    page_icon="🏢",
    layout="wide"
)


# =========================
# Encabezado con logo ENAEX
# =========================

col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=180)
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")

with col_titulo:
    st.title("Resumen dólar SII por años seleccionados")
    st.write(
        "Selecciona los años a consultar. El resumen incluirá automáticamente "
        "todos los meses desde Ene hasta Dic."
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
            key=f"checkbox_anio_{anio}"
        )

        if seleccionado:
            anios_seleccionados.append(anio)


st.write("Años seleccionados:", anios_seleccionados)


# =========================
# Generar resumen
# =========================

if st.button("Generar resumen"):
    if not anios_seleccionados:
        st.warning("Debes seleccionar al menos un año.")
    else:
        with st.spinner("Generando resumen..."):
            resumen = generar_resumen_varios_anios_todos_los_meses(
                anios_seleccionados
            )

        st.session_state["resumen_dolar"] = resumen

        st.success("Resumen generado correctamente.")
        st.dataframe(resumen, use_container_width=True)


# =========================
# Descargar Excel
# =========================

if "resumen_dolar" in st.session_state:
    resumen = st.session_state["resumen_dolar"]

    excel_resumen = crear_excel_resumen(resumen)

    st.download_button(
        label="Descargar Excel resumen",
        data=excel_resumen,
        file_name="resumen_dolar_sii.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
