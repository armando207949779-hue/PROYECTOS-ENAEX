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

URL_EXCEL_IPC_DIRECTA = (
    "https://www.ine.gob.cl/docs/default-source/"
    "%C3%ADndice-de-precios-al-consumidor/cuadros-estadisticos/"
    "base-anual-2023_100/series-de-tiempo/"
    "ipc-xls.xlsx?sfvrsn=5b901f39_70"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


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
# Descargar Excel IPC
# =========================

@st.cache_data
def descargar_excel_ipc():
    response = requests.get(
        URL_EXCEL_IPC_DIRECTA,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.content


# =========================
# Leer y limpiar Excel IPC
# =========================

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


# =========================
# Preparar IPC General
# =========================

def preparar_ipc_general(df_ipc):
    df_ipc_general = df_ipc[
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
        if columna in df_ipc_general.columns:
            df_ipc_general[columna] = pd.to_numeric(
                df_ipc_general[columna],
                errors="coerce"
            )

    df_ipc_general = df_ipc_general.dropna(
        subset=["Año", "Mes", "Índice"]
    )

    df_ipc_general["Año"] = df_ipc_general["Año"].astype(int)
    df_ipc_general["Mes"] = df_ipc_general["Mes"].astype(int)

    df_ipc_general["Fecha"] = pd.to_datetime(
        df_ipc_general["Año"].astype(str)
        + "-"
        + df_ipc_general["Mes"].astype(str)
        + "-01"
    )

    df_ipc_general = df_ipc_general.sort_values("Fecha")

    columnas_salida = [
        "Fecha",
        "Año",
        "Mes",
        "Glosa",
        "Índice",
        "Variación Mensual (%)",
        "Variación Acumulada (%)",
        "Variación 12 Meses (%)"
    ]

    columnas_salida = [
        col for col in columnas_salida
        if col in df_ipc_general.columns
    ]

    return df_ipc_general[columnas_salida]


# =========================
# Crear Excel salida
# =========================

def crear_excel_ipc(df_ipc_general):
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_ipc_general.to_excel(
            writer,
            sheet_name="IPC General",
            index=False
        )

    return buffer.getvalue()


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="INE IPC",
    page_icon="🏢",
    layout="wide"
)

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>Índice de Precios al Consumidor</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Consulta automática del IPC General publicado por el INE.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# =========================
# Botón principal
# =========================

if st.button("Generar resumen IPC"):
    with st.spinner("Descargando y procesando información del INE..."):
        try:
            contenido_excel = descargar_excel_ipc()

            df_ipc = leer_excel_ipc_limpio(contenido_excel)
            df_ipc_general = preparar_ipc_general(df_ipc)

            st.session_state["df_ipc_general"] = df_ipc_general
            st.session_state["df_ipc_completo"] = df_ipc

            if not df_ipc_general.empty:
                st.success("Resumen IPC generado correctamente.")
            else:
                st.warning("No se encontraron registros de IPC General.")

        except Exception as e:
            st.error(f"Error al generar el resumen IPC: {e}")


# =========================
# Mostrar resultados
# =========================

if "df_ipc_general" in st.session_state:
    df_ipc_general = st.session_state["df_ipc_general"]

    if not df_ipc_general.empty:
        st.markdown("---")
        st.subheader("Resumen IPC General")

        anios_disponibles = sorted(
            df_ipc_general["Año"]
            .dropna()
            .unique()
            .tolist(),
            reverse=True
        )

        anio_filtro = st.selectbox(
            "Filtrar por año",
            options=["Todos"] + anios_disponibles
        )

        df_filtrado = df_ipc_general.copy()

        if anio_filtro != "Todos":
            df_filtrado = df_filtrado[
                df_filtrado["Año"] == anio_filtro
            ]

        st.dataframe(
            df_filtrado,
            use_container_width=True
        )

        st.subheader("Gráfico temporal del IPC General")

        df_grafico = df_filtrado.copy()

        if not df_grafico.empty:
            datos_linea = df_grafico.set_index("Fecha")["Índice"]

            st.line_chart(datos_linea)
        else:
            st.info("No hay datos suficientes para generar el gráfico.")

        excel_ipc = crear_excel_ipc(df_filtrado)

        st.download_button(
            label="Descargar Excel IPC",
            data=excel_ipc,
            file_name="resumen_ipc_general_ine.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with st.expander("Ver datos completos del archivo IPC"):
            df_ipc_completo = st.session_state.get("df_ipc_completo")

            if df_ipc_completo is not None:
                st.dataframe(
                    df_ipc_completo,
                    use_container_width=True
                )