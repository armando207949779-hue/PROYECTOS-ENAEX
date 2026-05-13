import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# Configuración general
# =========================================================

st.set_page_config(
    page_title="Fechas Finales Match Integrado",
    page_icon="📅",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================================================
# Columnas esperadas - formato nuevo
# =========================================================

COL_SOLICITUD_ME5A = "Solicitud de pedido - ME5A"
COL_FECHA_SOLICITUD_ME5A = "Fecha de solicitud - ME5A"
COL_FECHA_LIBERACION_ME5A = "Fecha de liberación - ME5A"
COL_FECHA_PEDIDO_ME5A = "Fecha de pedido - ME5A"
COL_FECHA_APROBACION_ARIBA = "Fecha de aprobación - ARIBA"
COL_FECHA_FACTURACION_NME = "Fecha facturación proveedor - NME80FN"
COL_FECHA_RECEPCION_NME = "Fecha recepción mercancía - NME80FN"
COL_ESTADO_MATCH = "Estado del match"

COLUMNAS_REQUERIDAS_FORMATO_NUEVO = [
    COL_SOLICITUD_ME5A,
    COL_FECHA_SOLICITUD_ME5A,
    COL_FECHA_LIBERACION_ME5A,
    COL_FECHA_PEDIDO_ME5A,
    COL_FECHA_APROBACION_ARIBA,
    COL_FECHA_FACTURACION_NME,
    COL_FECHA_RECEPCION_NME,
]

COLUMNAS_FECHAS_FINALES = [
    "fecha_solicitud_final",
    "fecha_liberacion_final",
    "fecha_pedido_final",
    "fecha_facturacion_final",
    "fecha_recepcion_final",
]


# =========================================================
# UI común
# =========================================================

def mostrar_logo(ancho: int = 180):
    if not LOGO_PATH.exists():
        return

    logo_svg = LOGO_PATH.read_text(encoding="utf-8")
    logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")

    st.markdown(
        f"""
        <div style="
            width: 100%;
            text-align: center;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                width="{ancho}"
            >
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# Funciones generales
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;):":
        return ";"
    if separador_csv == "Punto y coma (;)":
        return ";"
    if separador_csv == "Coma (,):":
        return ","
    if separador_csv == "Coma (,):":
        return ","
    if separador_csv == "Coma (, )":
        return ","
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    bytes_archivo: bytes,
    nombre_archivo: str,
    separador_csv: str
) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".xlsx"):
        return pd.read_excel(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip"
            )
        except Exception:
            buffer.seek(0)

            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def validar_columnas_requeridas(df: pd.DataFrame):
    faltantes = [
        col for col in COLUMNAS_REQUERIDAS_FORMATO_NUEVO
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas requeridas del formato nuevo: "
            f"{faltantes}"
        )


def normalizar_estado_match(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if COL_ESTADO_MATCH in df.columns:
        df[COL_ESTADO_MATCH] = (
            df[COL_ESTADO_MATCH]
            .astype("string")
            .replace({
                "Sin match": "No encontrado en ARIBA ni NME80FN",
                "Match en ARIBA y NME80FN": "Encontrado en ARIBA y NME80FN",
                "Match solo en ARIBA": "Encontrado solo en ARIBA",
                "Match solo en NME80FN": "Encontrado solo en NME80FN",
            })
        )

    return df


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    """
    Convierte fechas que pueden venir como:
    - datetime
    - texto de fecha
    - timestamp numérico en milisegundos, como 1704067200000
    - timestamp numérico en segundos
    """
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")

    mask_num = serie_num.notna()

    if mask_num.any():
        valores_abs = serie_num[mask_num].abs()

        mask_ms = mask_num & serie_num.abs().ge(10**11)
        mask_s = mask_num & serie_num.abs().lt(10**11)

        if mask_ms.any():
            resultado.loc[mask_ms] = pd.to_datetime(
                serie_num.loc[mask_ms],
                unit="ms",
                errors="coerce"
            )

        if mask_s.any():
            resultado.loc[mask_s] = pd.to_datetime(
                serie_num.loc[mask_s],
                unit="s",
                errors="coerce"
            )

    mask_no_num = ~mask_num

    if mask_no_num.any():
        resultado.loc[mask_no_num] = pd.to_datetime(
            serie.loc[mask_no_num],
            errors="coerce",
            dayfirst=True
        )

    return resultado


def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    return str(valor)


# =========================================================
# Lógica de fechas finales
# =========================================================

@st.cache_data(show_spinner=False)
def aplicar_logica_fechas_finales(df: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df)
    validar_columnas_requeridas(df)
    df = normalizar_estado_match(df)

    columnas_fecha_base = [
        COL_FECHA_SOLICITUD_ME5A,
        COL_FECHA_LIBERACION_ME5A,
        COL_FECHA_PEDIDO_ME5A,
        COL_FECHA_APROBACION_ARIBA,
        COL_FECHA_FACTURACION_NME,
        COL_FECHA_RECEPCION_NME,
    ]

    for col in columnas_fecha_base:
        df[col] = convertir_fecha_columna(df[col])

    solped_str = (
        df[COL_SOLICITUD_ME5A]
        .astype("string")
        .str.strip()
    )

    mask_solped_6 = solped_str.str.startswith("6").fillna(False)

    df["fecha_solicitud_final"] = df[COL_FECHA_SOLICITUD_ME5A]

    df["fecha_liberacion_final"] = np.where(
        mask_solped_6,
        df[COL_FECHA_APROBACION_ARIBA],
        df[COL_FECHA_LIBERACION_ME5A]
    )

    df["fecha_pedido_final"] = df[COL_FECHA_PEDIDO_ME5A]
    df["fecha_facturacion_final"] = df[COL_FECHA_FACTURACION_NME]
    df["fecha_recepcion_final"] = df[COL_FECHA_RECEPCION_NME]

    for col in COLUMNAS_FECHAS_FINALES:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["criterio_fecha_liberacion"] = np.where(
        mask_solped_6,
        "Solicitud de pedido - ME5A empieza con 6: usa Fecha de aprobación - ARIBA",
        "Solicitud de pedido - ME5A no empieza con 6: usa Fecha de liberación - ME5A"
    )

    df["fuente_fecha_liberacion_final"] = np.where(
        mask_solped_6,
        COL_FECHA_APROBACION_ARIBA,
        COL_FECHA_LIBERACION_ME5A
    )

    return df


def reordenar_columnas_fechas_al_final(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    columnas_finales = [
        "criterio_fecha_liberacion",
        "fuente_fecha_liberacion_final",
    ] + COLUMNAS_FECHAS_FINALES

    columnas_finales = [col for col in columnas_finales if col in df.columns]

    columnas_base = [
        col for col in df.columns
        if col not in columnas_finales
    ]

    return df[columnas_base + columnas_finales].copy()


# =========================================================
# Resúmenes y lógica explicativa
# =========================================================

def resumen_fechas(df: pd.DataFrame) -> pd.DataFrame:
    total = int(len(df))

    data = []

    for col in COLUMNAS_FECHAS_FINALES:
        if col not in df.columns:
            continue

        no_nulos = int(df[col].notna().sum())
        nulos = int(df[col].isna().sum())
        porcentaje_nulos = round(df[col].isna().mean() * 100, 2) if total else 0

        data.append({
            "Mensaje": f"{no_nulos:,} registros de {total:,} en ME5A tienen {col} informada",
            "Columna": col,
            "No nulos": no_nulos,
            "Nulos": nulos,
            "% Nulos": porcentaje_nulos,
            "Fecha mínima": df[col].min(),
            "Fecha máxima": df[col].max()
        })

    return pd.DataFrame(data)


def generar_resumen_cambios_fechas(
    df_original: pd.DataFrame,
    df_final: pd.DataFrame,
    columnas_originales: list,
    columnas_nuevas: list
) -> dict:
    total = int(len(df_final))

    solped_str = (
        df_final[COL_SOLICITUD_ME5A]
        .astype("string")
        .str.strip()
    )

    mask_solped_6 = solped_str.str.startswith("6").fillna(False)

    total_solped_6 = int(mask_solped_6.sum())
    total_solped_no_6 = int((~mask_solped_6).sum())

    ejemplo = None
    if not df_final.empty:
        # Prioriza un caso que use ARIBA; si no existe, usa el primer registro disponible.
        candidatos = df_final[mask_solped_6].copy()
        if candidatos.empty:
            candidatos = df_final.copy()
        ejemplo = candidatos.iloc[0].to_dict()

    return {
        "total_original": int(len(df_original)),
        "total_final": total,
        "columnas_originales": int(len(columnas_originales)),
        "columnas_finales": int(len(df_final.columns)),
        "columnas_nuevas": int(len(columnas_nuevas)),
        "duplicados_final": int(df_final.duplicated().sum()),
        "solped_6": total_solped_6,
        "solped_no_6": total_solped_no_6,
        "ejemplo": ejemplo,
    }


def generar_tabla_ejemplo_fechas(ejemplo: dict) -> pd.DataFrame:
    if not ejemplo:
        return pd.DataFrame(
            columns=[
                "Fecha final",
                "Campo origen usado",
                "Valor origen",
                "Resultado final",
                "Regla aplicada"
            ]
        )

    fuente_liberacion = ejemplo.get("fuente_fecha_liberacion_final", "")

    return pd.DataFrame([
        {
            "Fecha final": "fecha_solicitud_final",
            "Campo origen usado": COL_FECHA_SOLICITUD_ME5A,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_ME5A)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_solicitud_final")),
            "Regla aplicada": "Usa directamente la fecha de solicitud de ME5A."
        },
        {
            "Fecha final": "fecha_liberacion_final",
            "Campo origen usado": formatear_valor(fuente_liberacion),
            "Valor origen": formatear_valor(ejemplo.get(fuente_liberacion)) if fuente_liberacion else "",
            "Resultado final": formatear_valor(ejemplo.get("fecha_liberacion_final")),
            "Regla aplicada": formatear_valor(ejemplo.get("criterio_fecha_liberacion"))
        },
        {
            "Fecha final": "fecha_pedido_final",
            "Campo origen usado": COL_FECHA_PEDIDO_ME5A,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_PEDIDO_ME5A)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_pedido_final")),
            "Regla aplicada": "Usa directamente la fecha de pedido de ME5A."
        },
        {
            "Fecha final": "fecha_facturacion_final",
            "Campo origen usado": COL_FECHA_FACTURACION_NME,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_FACTURACION_NME)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_facturacion_final")),
            "Regla aplicada": "Usa la fecha de facturación proveedor desde NME80FN."
        },
        {
            "Fecha final": "fecha_recepcion_final",
            "Campo origen usado": COL_FECHA_RECEPCION_NME,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_NME)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_recepcion_final")),
            "Regla aplicada": "Usa la fecha de recepción de mercancía desde NME80FN."
        },
    ])


def mostrar_resumen_cambios_fechas(resumen_cambios: dict):
    with st.expander("Cambios realizados y lógica de fechas finales", expanded=False):
        st.info(
            f"""
            **Archivo cargado**

            - Se cargaron **{resumen_cambios['total_original']:,} registros** del match integrado.
            - El resultado final conserva **{resumen_cambios['total_final']:,} registros**.
            - Se conservaron las columnas originales y se agregaron **{resumen_cambios['columnas_nuevas']:,} columnas nuevas**.

            **Resultado de la lógica de fechas**

            - **{resumen_cambios['total_final']:,} registros de {resumen_cambios['total_original']:,} en ME5A fueron procesados para generar fechas finales**.
            - **{resumen_cambios['solped_6']:,} registros de {resumen_cambios['total_final']:,} en ME5A usan Fecha de aprobación - ARIBA para la fecha de liberación final**.
            - **{resumen_cambios['solped_no_6']:,} registros de {resumen_cambios['total_final']:,} en ME5A usan Fecha de liberación - ME5A para la fecha de liberación final**.

            **Regla principal de liberación**

            - Si **Solicitud de pedido - ME5A** empieza con **6**, entonces **fecha_liberacion_final** usa **Fecha de aprobación - ARIBA**.
            - Si **Solicitud de pedido - ME5A** no empieza con **6**, entonces **fecha_liberacion_final** usa **Fecha de liberación - ME5A**.

            **Salida generada**

            - Se generó una salida con **{resumen_cambios['total_final']:,} registros** y **{resumen_cambios['columnas_finales']:,} columnas**.
            - Filas duplicadas detectadas en la salida final: **{resumen_cambios['duplicados_final']:,}**.
            """
        )

        st.markdown("**Ejemplo de lógica de fechas finales**")
        tabla_ejemplo = generar_tabla_ejemplo_fechas(resumen_cambios.get("ejemplo"))

        if tabla_ejemplo.empty:
            st.warning("No se encontró un registro para mostrar como ejemplo.")
        else:
            st.table(tabla_ejemplo)


# =========================================================
# Exportación
# =========================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


def convertir_a_excel(df: pd.DataFrame, resumen: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Data_Fechas_Finales"
        )

        resumen.to_excel(
            writer,
            index=False,
            sheet_name="Resumen_Fechas"
        )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(df: pd.DataFrame, resumen: pd.DataFrame) -> bytes:
    return convertir_a_excel(df, resumen)


# =========================================================
# Interfaz
# =========================================================

mostrar_logo()

st.title("Fechas finales match integrado")
st.caption("ME5A · ARIBA · NME80FN")

with st.sidebar:
    st.header("Configuración")

    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación"
        ],
        index=0
    )

    limite_vista = st.number_input(
        "Filas en vista previa",
        min_value=50,
        max_value=1000,
        value=300,
        step=50
    )

    ordenar_fechas_final = st.checkbox(
        "Mover columnas de fecha al final",
        value=True
    )

    st.caption("El separador solo aplica a archivos CSV.")


st.subheader("Archivo")

uploaded_file = st.file_uploader(
    "Selecciona archivo match integrado",
    type=["parquet", "xlsx", "csv"]
)

if uploaded_file is None:
    st.info("Carga el archivo match integrado para generar las fechas finales.")
    st.stop()

try:
    with st.spinner("Leyendo archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=uploaded_file.getvalue(),
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv
        )

    columnas_originales = list(df_original.columns)

    with st.spinner("Aplicando lógica de fechas finales..."):
        df_final = aplicar_logica_fechas_finales(df_original)

        columnas_nuevas = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        if ordenar_fechas_final:
            df_final = reordenar_columnas_fechas_al_final(df_final)

        resumen = resumen_fechas(df_final)
        parquet_bytes = convertir_a_parquet_cache(df_final)

        resumen_cambios = generar_resumen_cambios_fechas(
            df_original=df_original,
            df_final=df_final,
            columnas_originales=columnas_originales,
            columnas_nuevas=columnas_nuevas
        )

    st.success("Fechas finales generadas correctamente.")

    mostrar_resumen_cambios_fechas(resumen_cambios)

    st.subheader("Indicadores")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Filas originales",
        f"{len(df_original):,}"
    )

    col2.metric(
        "Filas finales",
        f"{len(df_final):,}"
    )

    col3.metric(
        "Columnas originales",
        f"{len(columnas_originales):,}"
    )

    col4.metric(
        "Columnas nuevas",
        f"{len(columnas_nuevas):,}"
    )

    st.subheader("Resumen")

    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True
    )

    with st.expander("Vista previa original", expanded=False):
        st.caption(
            f"Mostrando hasta {int(limite_vista):,} registros de "
            f"{len(df_original):,} registros originales. "
            f"Columnas visibles: {len(df_original.columns):,}."
        )

        st.dataframe(
            df_original.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Vista previa final")

    st.caption(
        f"Mostrando hasta {int(limite_vista):,} registros de "
        f"{len(df_final):,} registros generados. "
        f"Columnas visibles: {len(df_final.columns):,}."
    )

    st.dataframe(
        df_final.head(int(limite_vista)),
        use_container_width=True,
        hide_index=True
    )

    with st.expander("Ver columnas disponibles", expanded=False):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Columnas originales**")
            st.write(columnas_originales)

        with c2:
            st.markdown("**Columnas finales**")
            st.write(df_final.columns.tolist())

    st.subheader("Descarga")

    st.download_button(
        label="Descargar resultado en Parquet",
        data=parquet_bytes,
        file_name="match_integrado_me5a_ariba_nme80fn_fechas_finales.parquet",
        mime="application/octet-stream",
        use_container_width=True
    )

    st.caption(
        "Parquet es el formato principal recomendado para conservar tipos de datos "
        "y trabajar con Python. CSV y Excel se preparan solo si los solicitas."
    )

    with st.expander("Opcional: descargar como CSV o Excel", expanded=False):
        col_csv, col_excel = st.columns(2)

        with col_csv:
            preparar_csv = st.button(
                "Preparar CSV",
                use_container_width=True
            )

            if preparar_csv:
                with st.spinner("Preparando CSV..."):
                    csv_bytes = convertir_a_csv_cache(df_final)

                st.download_button(
                    label="Descargar CSV",
                    data=csv_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn_fechas_finales.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with col_excel:
            limite_excel = 250_000

            if len(df_final) > limite_excel:
                st.button(
                    "Excel no disponible",
                    disabled=True,
                    use_container_width=True
                )

                st.warning(
                    f"Excel no está disponible porque la salida tiene más de {limite_excel:,} filas. "
                    "Usa Parquet o CSV."
                )
            else:
                preparar_excel = st.button(
                    "Preparar Excel",
                    use_container_width=True
                )

                if preparar_excel:
                    with st.spinner("Preparando Excel..."):
                        excel_bytes = convertir_a_excel_cache(
                            df_final,
                            resumen
                        )

                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name="match_integrado_me5a_ariba_nme80fn_fechas_finales.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

except Exception as e:
    st.error("No se pudo generar el archivo de fechas finales.")
    st.exception(e)
