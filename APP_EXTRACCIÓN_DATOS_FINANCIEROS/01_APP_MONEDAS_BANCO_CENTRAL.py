# ============================================================
# 01_APP_MONEDAS_BANCO_CENTRAL
# Consulta monedas e indicadores Banco Central de Chile
# Conversión a CLP y USD por unidad
# ============================================================

import base64
from pathlib import Path
from datetime import date, timedelta
from io import BytesIO
from typing import Callable

import pandas as pd
import requests
import streamlit as st


# ============================================================
# Rutas del proyecto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="Monedas Banco Central ENAEX",
    page_icon="💱",
    layout="wide",
)


# ============================================================
# Constantes Banco Central
# ============================================================

URL_BDE = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"

SERIES_MONEDAS = {
    "ARS": "F072.ARS.USD.N.O.D",
    "AUD": "F072.AUD.USD.N.O.D",
    "BOB": "F072.BOL.USD.N.O.D",
    "BRL": "F072.BRL.USD.N.O.D",
    "CAD": "F072.CAD.USD.N.O.D",
    "CHF": "F072.CHF.USD.N.O.D",
    "CLP": "F073.TCO.PRE.Z.D",
    "COP": "F072.COP.USD.N.O.D",
    "EUR": "F072.EUR.USD.N.O.D",
    "GBP": "F072.GBP.USD.N.O.D",
    "MXN": "F072.MXN.USD.N.O.D",
    "PEN": "F072.PEN.USD.N.O.D",
    "UF": "F073.UFF.PRE.Z.D",
    "USD": "F073.TCO.PRE.Z.D",
    "UTM": "F073.UTR.PRE.Z.M",
}

# Estas series vienen publicadas como:
# moneda por dólar de EEUU
# Ejemplo BRL:
# valor_bde = 5.1740 significa 1 USD = 5.1740 BRL
MONEDAS_POR_USD = [
    "ARS",
    "AUD",
    "BOB",
    "BRL",
    "CAD",
    "CHF",
    "COP",
    "EUR",
    "GBP",
    "MXN",
    "PEN",
]


# ============================================================
# Logo centrado
# ============================================================

def mostrar_logo_centrado() -> None:
    """Muestra el logo corporativo centrado."""
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
                    alt="ENAEX"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# Credenciales
# ============================================================

def obtener_credenciales() -> tuple[str, str]:
    """
    Obtiene credenciales desde Streamlit Secrets.

    En .streamlit/secrets.toml local o en Streamlit Cloud → Settings → Secrets:

    [bde]
    user = "TU_USUARIO"
    password = "TU_CLAVE"
    """
    try:
        user = st.secrets["bde"]["user"]
        password = st.secrets["bde"]["password"]

        if not user or not password:
            st.error("Credenciales BDE vacías en secrets.")
            st.stop()

        return user, password

    except Exception:
        st.error(
            """
            No se encontraron credenciales BDE en Streamlit Secrets.

            Debes configurar:

            [bde]  
            user = "TU_USUARIO"  
            password = "TU_CLAVE"
            """
        )
        st.stop()


# ============================================================
# Consulta API BDE
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def consultar_serie_bde(
    user: str,
    password: str,
    codigo: str,
    series_id: str,
    fecha_consulta: date,
    dias_retroceso: int = 400,
) -> dict:
    """
    Consulta una serie BDE y devuelve el último valor disponible
    menor o igual a la fecha seleccionada.
    """

    fecha_desde = fecha_consulta - timedelta(days=dias_retroceso)

    params = {
        "user": user,
        "pass": password,
        "function": "GetSeries",
        "timeseries": series_id,
        "firstdate": fecha_desde.strftime("%Y-%m-%d"),
        "lastdate": fecha_consulta.strftime("%Y-%m-%d"),
    }

    try:
        response = requests.get(URL_BDE, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()

        if data.get("Codigo") != 0:
            return {
                "codigo": codigo,
                "fecha": None,
                "valor_bde": None,
                "descripcion": data.get("Descripcion"),
                "seriesId": series_id,
                "estado": "ERROR_BDE",
            }

        obs = data.get("Series", {}).get("Obs", [])

        if not obs:
            return {
                "codigo": codigo,
                "fecha": None,
                "valor_bde": None,
                "descripcion": "Sin observaciones para el rango consultado",
                "seriesId": series_id,
                "estado": "SIN_DATOS",
            }

        df = pd.DataFrame(obs)

        df["fecha"] = pd.to_datetime(
            df["indexDateString"],
            format="%d-%m-%Y",
            errors="coerce",
        )

        df["valor_bde"] = pd.to_numeric(
            df["value"],
            errors="coerce",
        )

        df = df.dropna(subset=["fecha", "valor_bde"])
        df = df[df["fecha"].dt.date <= fecha_consulta]

        if df.empty:
            return {
                "codigo": codigo,
                "fecha": None,
                "valor_bde": None,
                "descripcion": "Sin observaciones válidas hasta la fecha consultada",
                "seriesId": series_id,
                "estado": "SIN_DATOS",
            }

        ultimo = df.sort_values("fecha").tail(1)

        return {
            "codigo": codigo,
            "fecha": ultimo["fecha"].iloc[0].date(),
            "valor_bde": float(ultimo["valor_bde"].iloc[0]),
            "descripcion": data["Series"].get("descripEsp"),
            "seriesId": data["Series"].get("seriesId", series_id),
            "estado": "OK",
        }

    except Exception as e:
        return {
            "codigo": codigo,
            "fecha": None,
            "valor_bde": None,
            "descripcion": f"Error de consulta: {e}",
            "seriesId": series_id,
            "estado": "ERROR_CONSULTA",
        }


def consultar_monedas_bde(
    user: str,
    password: str,
    fecha_consulta: date,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> pd.DataFrame:
    """
    Consulta todas las monedas definidas.

    progress_callback recibe:
    - índice actual
    - total de series
    - código de moneda/indicador
    """

    resultados = []
    total = len(SERIES_MONEDAS)

    for i, (codigo, series_id) in enumerate(SERIES_MONEDAS.items(), start=1):
        if progress_callback is not None:
            progress_callback(i, total, codigo)

        resultado = consultar_serie_bde(
            user=user,
            password=password,
            codigo=codigo,
            series_id=series_id,
            fecha_consulta=fecha_consulta,
        )

        resultados.append(resultado)

    df = pd.DataFrame(resultados)
    df = df.sort_values("codigo").reset_index(drop=True)

    return df


# ============================================================
# Cálculos de conversión
# ============================================================

def calcular_equivalencias(df_monedas: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega:
    - equivalencia_usd: USD por 1 unidad de moneda/indicador
    - valor_clp_por_unidad: CLP por 1 unidad de moneda/indicador
    - lectura_bde
    - lectura_usd
    """

    df = df_monedas.copy()

    df["valor_bde"] = pd.to_numeric(df["valor_bde"], errors="coerce")

    if df.loc[df["codigo"] == "CLP", "valor_bde"].dropna().empty:
        st.error("No se pudo obtener el dólar observado CLP/USD.")
        st.stop()

    # Dólar observado: CLP por 1 USD
    dolar_clp = float(
        df.loc[df["codigo"] == "CLP", "valor_bde"].dropna().iloc[0]
    )

    df["equivalencia_usd"] = pd.NA
    df["valor_clp_por_unidad"] = pd.NA
    df["lectura_bde"] = pd.NA
    df["lectura_usd"] = pd.NA
    df["tipo_conversion"] = pd.NA

    # --------------------------------------------------------
    # 1) Monedas publicadas como moneda por USD
    # --------------------------------------------------------

    mask_monedas = df["codigo"].isin(MONEDAS_POR_USD)

    df.loc[mask_monedas, "equivalencia_usd"] = (
        1 / df.loc[mask_monedas, "valor_bde"]
    )

    df.loc[mask_monedas, "valor_clp_por_unidad"] = (
        df.loc[mask_monedas, "equivalencia_usd"].astype(float) * dolar_clp
    )

    df.loc[mask_monedas, "lectura_bde"] = (
        "1 USD = "
        + df.loc[mask_monedas, "valor_bde"].round(6).astype(str)
        + " "
        + df.loc[mask_monedas, "codigo"]
    )

    df.loc[mask_monedas, "lectura_usd"] = (
        "1 "
        + df.loc[mask_monedas, "codigo"]
        + " = "
        + df.loc[mask_monedas, "equivalencia_usd"].astype(float).round(9).astype(str)
        + " USD"
    )

    df.loc[mask_monedas, "tipo_conversion"] = (
        "Se invierte porque BDE entrega moneda por USD"
    )

    # --------------------------------------------------------
    # 2) CLP
    # --------------------------------------------------------

    mask_clp = df["codigo"].eq("CLP")

    df.loc[mask_clp, "equivalencia_usd"] = 1 / dolar_clp
    df.loc[mask_clp, "valor_clp_por_unidad"] = 1.0

    df.loc[mask_clp, "lectura_bde"] = (
        "1 USD = "
        + df.loc[mask_clp, "valor_bde"].round(6).astype(str)
        + " CLP"
    )

    df.loc[mask_clp, "lectura_usd"] = (
        "1 CLP = "
        + df.loc[mask_clp, "equivalencia_usd"].astype(float).round(9).astype(str)
        + " USD"
    )

    df.loc[mask_clp, "tipo_conversion"] = (
        "Se invierte porque BDE entrega CLP por USD"
    )

    # --------------------------------------------------------
    # 3) UF y UTM
    # --------------------------------------------------------

    mask_clp_unidad = df["codigo"].isin(["UF", "UTM"])

    df.loc[mask_clp_unidad, "equivalencia_usd"] = (
        df.loc[mask_clp_unidad, "valor_bde"] / dolar_clp
    )

    df.loc[mask_clp_unidad, "valor_clp_por_unidad"] = (
        df.loc[mask_clp_unidad, "valor_bde"]
    )

    df.loc[mask_clp_unidad, "lectura_bde"] = (
        "1 "
        + df.loc[mask_clp_unidad, "codigo"]
        + " = "
        + df.loc[mask_clp_unidad, "valor_bde"].round(6).astype(str)
        + " CLP"
    )

    df.loc[mask_clp_unidad, "lectura_usd"] = (
        "1 "
        + df.loc[mask_clp_unidad, "codigo"]
        + " = "
        + df.loc[mask_clp_unidad, "equivalencia_usd"].astype(float).round(9).astype(str)
        + " USD"
    )

    df.loc[mask_clp_unidad, "tipo_conversion"] = (
        "Se divide por dólar observado porque BDE entrega CLP por unidad"
    )

    # --------------------------------------------------------
    # 4) USD
    # --------------------------------------------------------

    mask_usd = df["codigo"].eq("USD")

    df.loc[mask_usd, "equivalencia_usd"] = 1.0
    df.loc[mask_usd, "valor_clp_por_unidad"] = dolar_clp
    df.loc[mask_usd, "lectura_bde"] = f"1 USD = {round(dolar_clp, 6)} CLP"
    df.loc[mask_usd, "lectura_usd"] = "1 USD = 1 USD"
    df.loc[mask_usd, "tipo_conversion"] = "USD base"

    # --------------------------------------------------------
    # Tipos finales
    # --------------------------------------------------------

    df["equivalencia_usd"] = pd.to_numeric(
        df["equivalencia_usd"],
        errors="coerce",
    )

    df["valor_clp_por_unidad"] = pd.to_numeric(
        df["valor_clp_por_unidad"],
        errors="coerce",
    )

    return df


def crear_tabla_conversion(df_monedas: pd.DataFrame) -> pd.DataFrame:
    """
    Crea tabla final solicitada:

    Moneda
    Valor_CLP_por_Unidad
    Factor_USD_por_Unidad
    Fecha_Conversion
    """

    df_conversion = df_monedas.rename(
        columns={
            "codigo": "Moneda",
            "valor_clp_por_unidad": "Valor_CLP_por_Unidad",
            "equivalencia_usd": "Factor_USD_por_Unidad",
            "fecha": "Fecha_Conversion",
        }
    )[
        [
            "Moneda",
            "Valor_CLP_por_Unidad",
            "Factor_USD_por_Unidad",
            "Fecha_Conversion",
        ]
    ].copy()

    df_conversion["Valor_CLP_por_Unidad"] = pd.to_numeric(
        df_conversion["Valor_CLP_por_Unidad"],
        errors="coerce",
    )

    df_conversion["Factor_USD_por_Unidad"] = pd.to_numeric(
        df_conversion["Factor_USD_por_Unidad"],
        errors="coerce",
    )

    df_conversion = df_conversion.sort_values("Moneda").reset_index(drop=True)

    return df_conversion


# ============================================================
# Exportación Excel
# ============================================================

def dataframe_a_excel(
    df_detalle: pd.DataFrame,
    df_conversion: pd.DataFrame,
) -> bytes:
    """Genera un archivo Excel en memoria con ambas tablas."""

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_conversion.to_excel(
            writer,
            index=False,
            sheet_name="Conversion_USD_CLP",
        )

        df_detalle.to_excel(
            writer,
            index=False,
            sheet_name="Detalle_BDE",
        )

    return output.getvalue()


# ============================================================
# Formateadores
# ============================================================

def formato_entero_clp(valor: float) -> str:
    """Formatea valores CLP como entero."""
    return f"{valor:,.0f} CLP"


def formato_entero_usd(valor: float) -> str:
    """Formatea valores USD como entero."""
    return f"{valor:,.0f} USD"


def formato_usd_observado(valor: float) -> str:
    """Formatea USD observado con 2 decimales."""
    return f"{valor:,.2f} CLP"


# ============================================================
# Página principal
# ============================================================

def main() -> None:
    mostrar_logo_centrado()

    st.markdown(
        "<h1 style='text-align: center;'>Monedas Banco Central</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Consulta de monedas, UF, UTM y dólar observado desde la BDE del Banco Central de Chile,
            con equivalencia en CLP y USD por unidad.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    user, password = obtener_credenciales()

    # --------------------------------------------------------
    # Panel de consulta
    # --------------------------------------------------------

    col_fecha, col_info = st.columns([1, 2])

    with col_fecha:
        fecha_consulta = st.date_input(
            "Fecha de consulta",
            value=date.today(),
            max_value=date.today(),
            help=(
                "La app usará el último dato disponible menor o igual "
                "a la fecha seleccionada."
            ),
        )

    with col_info:
        st.info(
            """
            La consulta obtiene el último valor disponible hasta la fecha seleccionada.
            Esto es importante porque algunas series no publican datos todos los días,
            por ejemplo UTM es mensual y algunas monedas no tienen valores en fines de semana o feriados.
            """
        )

    consultar = st.button(
        "Consultar Banco Central",
        type="primary",
        use_container_width=True,
    )

    st.markdown("---")

    if not consultar:
        st.success(
            """
            Selecciona una fecha y presiona **Consultar Banco Central**.
            Por defecto se usa la fecha de hoy.
            """
        )
        return

    # --------------------------------------------------------
    # Barra de progreso de consulta
    # --------------------------------------------------------

    st.subheader("Progreso de consulta")

    progress_bar = st.progress(0)
    progress_text = st.empty()

    def actualizar_progreso(actual: int, total: int, codigo: str) -> None:
        porcentaje = int((actual / total) * 100)
        progress_bar.progress(porcentaje)
        progress_text.info(
            f"Consultando {codigo}... {actual} de {total} series procesadas ({porcentaje}%)."
        )

    with st.spinner("Consultando datos en Banco Central..."):
        df_base = consultar_monedas_bde(
            user=user,
            password=password,
            fecha_consulta=fecha_consulta,
            progress_callback=actualizar_progreso,
        )

        progress_text.info("Calculando equivalencias en CLP y USD...")
        progress_bar.progress(90)

        df_monedas = calcular_equivalencias(df_base)
        df_conversion = crear_tabla_conversion(df_monedas)

        progress_bar.progress(100)
        progress_text.success("Consulta finalizada correctamente.")

    # --------------------------------------------------------
    # KPIs principales
    # --------------------------------------------------------

    dolar_clp = df_conversion.loc[
        df_conversion["Moneda"] == "USD",
        "Valor_CLP_por_Unidad",
    ].iloc[0]

    uf_clp = df_conversion.loc[
        df_conversion["Moneda"] == "UF",
        "Valor_CLP_por_Unidad",
    ].iloc[0]

    uf_usd = df_conversion.loc[
        df_conversion["Moneda"] == "UF",
        "Factor_USD_por_Unidad",
    ].iloc[0]

    utm_clp = df_conversion.loc[
        df_conversion["Moneda"] == "UTM",
        "Valor_CLP_por_Unidad",
    ].iloc[0]

    utm_usd = df_conversion.loc[
        df_conversion["Moneda"] == "UTM",
        "Factor_USD_por_Unidad",
    ].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    # USD observado queda con decimales
    col1.metric(
        "USD observado",
        formato_usd_observado(dolar_clp),
    )

    # Indicadores restantes como enteros
    col2.metric(
        "UF",
        formato_entero_clp(uf_clp),
        formato_entero_usd(uf_usd),
    )

    col3.metric(
        "UTM",
        formato_entero_clp(utm_clp),
        formato_entero_usd(utm_usd),
    )

    col4.metric(
        "Fecha consulta",
        fecha_consulta.strftime("%Y-%m-%d"),
    )

    st.markdown("---")

    # --------------------------------------------------------
    # Tabla solicitada
    # --------------------------------------------------------

    st.subheader("Tabla de conversión solicitada")

    st.caption(
        """
        Esta tabla muestra cuánto vale 1 unidad de cada moneda o indicador
        expresado en CLP y en USD.
        """
    )

    df_conversion_mostrar = df_conversion.copy()

    df_conversion_mostrar["Valor_CLP_por_Unidad"] = (
        df_conversion_mostrar["Valor_CLP_por_Unidad"].round(6)
    )

    df_conversion_mostrar["Factor_USD_por_Unidad"] = (
        df_conversion_mostrar["Factor_USD_por_Unidad"].round(9)
    )

    st.dataframe(
        df_conversion_mostrar,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Tabla detalle BDE
    # --------------------------------------------------------

    st.markdown("---")
    st.subheader("Detalle de datos Banco Central")

    st.caption(
        """
        Esta tabla conserva el valor original publicado por la BDE,
        la interpretación del dato y el tipo de conversión aplicado.
        """
    )

    df_detalle = df_monedas[
        [
            "codigo",
            "fecha",
            "valor_bde",
            "lectura_bde",
            "valor_clp_por_unidad",
            "equivalencia_usd",
            "lectura_usd",
            "tipo_conversion",
            "descripcion",
            "seriesId",
            "estado",
        ]
    ].copy()

    df_detalle["valor_bde"] = df_detalle["valor_bde"].round(9)
    df_detalle["valor_clp_por_unidad"] = df_detalle["valor_clp_por_unidad"].round(9)
    df_detalle["equivalencia_usd"] = df_detalle["equivalencia_usd"].round(9)

    st.dataframe(
        df_detalle,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Descargas
    # --------------------------------------------------------

    st.markdown("---")
    st.subheader("Descargar resultados")

    col_csv, col_excel = st.columns(2)

    csv_conversion = df_conversion.to_csv(index=False).encode("utf-8-sig")

    with col_csv:
        st.download_button(
            label="Descargar tabla conversión CSV",
            data=csv_conversion,
            file_name=f"conversion_monedas_bde_{fecha_consulta}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    excel_data = dataframe_a_excel(
        df_detalle=df_detalle,
        df_conversion=df_conversion,
    )

    with col_excel:
        st.download_button(
            label="Descargar Excel completo",
            data=excel_data,
            file_name=f"monedas_banco_central_{fecha_consulta}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    # --------------------------------------------------------
    # Notas finales
    # --------------------------------------------------------

    st.markdown("---")

    st.info(
        """
        **Notas de interpretación**

        - Para ARS, AUD, BOB, BRL, CAD, CHF, COP, EUR, GBP, MXN y PEN,
          Banco Central publica la serie como **moneda por dólar de EEUU**.
          Por eso se invierte para obtener USD por unidad.

        - Para UF y UTM, Banco Central publica valores en CLP por unidad.
          Por eso se divide por el dólar observado para obtener USD por unidad.

        - Para USD, el valor CLP por unidad corresponde al dólar observado.
        """
    )


# ============================================================
# Ejecutar app
# ============================================================

if __name__ == "__main__":
    main()
