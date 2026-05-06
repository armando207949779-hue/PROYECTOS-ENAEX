import base64
from io import BytesIO
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

URL_ARCHIVO_IR_DIRECTO = (
    "https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/"
    "cuadros-estadisticos/ir-icl-base-anual-2023-100/"
    "series-base-2023/tabulado_ir.xlsx?sfvrsn=77d2fe83_52"
)

URL_ARCHIVO_IR_BASE = (
    "https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/"
    "cuadros-estadisticos/ir-icl-base-anual-2023-100/"
    "series-base-2023/tabulado_ir.xlsx"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


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
# Descargar Excel IR
# =========================

@st.cache_data
def descargar_excel_ir():
    errores = []

    for url in [URL_ARCHIVO_IR_DIRECTO, URL_ARCHIVO_IR_BASE]:
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )

            response.raise_for_status()

            return response.content

        except Exception as e:
            errores.append(f"{url}: {e}")

    raise ValueError(
        "No se pudo descargar el archivo IR del INE. "
        + " | ".join(errores)
    )


# =========================
# Leer Excel IR
# =========================

def leer_excel_ir(contenido_excel):
    excel = pd.ExcelFile(BytesIO(contenido_excel))

    hoja = "General"

    if hoja not in excel.sheet_names:
        hoja = excel.sheet_names[0]

    df = pd.read_excel(
        BytesIO(contenido_excel),
        sheet_name=hoja
    )

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df, excel.sheet_names, hoja


# =========================
# Preparar resumen IR
# =========================

def preparar_resumen_ir(df):
    df_resumen = df.copy()

    columnas_actuales = {
        str(col).strip().lower(): col
        for col in df_resumen.columns
    }

    columnas_necesarias = ["año", "mes", "índice"]

    for columna in columnas_necesarias:
        if columna not in columnas_actuales:
            raise ValueError(
                f"No se encontró la columna requerida: {columna}"
            )

    df_resumen = df_resumen.rename(
        columns={
            columnas_actuales["año"]: "Año",
            columnas_actuales["mes"]: "Mes",
            columnas_actuales["índice"]: "IR INE indice"
        }
    )

    df_resumen["Año"] = pd.to_numeric(
        df_resumen["Año"],
        errors="coerce"
    )

    df_resumen["Mes"] = pd.to_numeric(
        df_resumen["Mes"],
        errors="coerce"
    )

    df_resumen["IR INE indice"] = pd.to_numeric(
        df_resumen["IR INE indice"],
        errors="coerce"
    )

    df_resumen = df_resumen.dropna(
        subset=["Año", "Mes", "IR INE indice"]
    ).copy()

    df_resumen["Año"] = df_resumen["Año"].astype(int)
    df_resumen["Mes"] = df_resumen["Mes"].astype(int)

    df_resumen["Fecha"] = pd.to_datetime(
        df_resumen["Año"].astype(str)
        + "-"
        + df_resumen["Mes"].astype(str)
        + "-01"
    )

    columnas_extra = {}

    posibles_columnas_extra = {
        "var_mensual": "IR INE variacion mensual",
        "var_acum": "IR INE variacion acumulada",
        "var_12": "IR INE variacion 12 meses"
    }

    for original, nuevo in posibles_columnas_extra.items():
        if original in columnas_actuales:
            columna_real = columnas_actuales[original]

            df_resumen[nuevo] = pd.to_numeric(
                df_resumen[columna_real],
                errors="coerce"
            )

            columnas_extra[nuevo] = nuevo

    columnas_salida = [
        "Fecha",
        "Año",
        "Mes",
        "IR INE indice"
    ] + list(columnas_extra.keys())

    df_resumen = df_resumen[columnas_salida].sort_values("Fecha")

    return df_resumen


# =========================
# Crear Excel
# =========================

def crear_excel_ir(df_resumen, df_completo):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_resumen.to_excel(
            writer,
            sheet_name="IR resumen",
            index=False
        )

        df_completo.to_excel(
            writer,
            sheet_name="IR completo",
            index=False
        )

    return buffer.getvalue()


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="IR INE",
    page_icon="🏢",
    layout="wide"
)

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>Índice de Remuneraciones INE</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Consulta automática del Índice de Remuneraciones publicado por el INE.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# =========================
# Botón principal
# =========================

if st.button("Generar resumen IR"):
    with st.spinner("Descargando y procesando información del INE..."):
        try:
            contenido_excel = descargar_excel_ir()

            df_ir_completo, hojas, hoja_usada = leer_excel_ir(
                contenido_excel
            )

            df_ir_resumen = preparar_resumen_ir(
                df_ir_completo
            )

            st.session_state["df_ir_resumen"] = df_ir_resumen
            st.session_state["df_ir_completo"] = df_ir_completo
            st.session_state["hojas_ir"] = hojas
            st.session_state["hoja_usada_ir"] = hoja_usada

            if not df_ir_resumen.empty:
                st.success("Resumen IR generado correctamente.")
            else:
                st.warning("No se encontraron datos para generar el resumen IR.")

        except Exception as e:
            st.error(f"Error al generar el resumen IR: {e}")


# =========================
# Mostrar resultados
# =========================

if "df_ir_resumen" in st.session_state:
    df_ir_resumen = st.session_state["df_ir_resumen"]
    df_ir_completo = st.session_state["df_ir_completo"]
    hojas_ir = st.session_state["hojas_ir"]
    hoja_usada_ir = st.session_state["hoja_usada_ir"]

    if not df_ir_resumen.empty:
        st.markdown("---")

        st.subheader("Resumen IR")

        st.caption(f"Hoja utilizada: {hoja_usada_ir}")

        anios_disponibles = sorted(
            df_ir_resumen["Año"]
            .dropna()
            .unique()
            .tolist(),
            reverse=True
        )

        anio_filtro = st.selectbox(
            "Filtrar por año",
            options=["Todos"] + anios_disponibles
        )

        df_filtrado = df_ir_resumen.copy()

        if anio_filtro != "Todos":
            df_filtrado = df_filtrado[
                df_filtrado["Año"] == anio_filtro
            ]

        st.dataframe(
            df_filtrado,
            use_container_width=True
        )

        st.subheader("Gráfico temporal IR")

        if not df_filtrado.empty:
            datos_linea = df_filtrado.set_index("Fecha")["IR INE indice"]

            st.line_chart(datos_linea)
        else:
            st.info("No hay datos suficientes para generar el gráfico.")

        excel_ir = crear_excel_ir(
            df_filtrado,
            df_ir_completo
        )

        st.download_button(
            label="Descargar Excel IR",
            data=excel_ir,
            file_name="resumen_ir_ine.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with st.expander("Ver datos completos del archivo IR"):
            st.write("Hojas disponibles:")
            st.write(hojas_ir)

            st.dataframe(
                df_ir_completo,
                use_container_width=True
            )