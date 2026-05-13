import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


# =========================
# Ruta del logo ENAEX
# =========================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================
# Configuración Streamlit
# =========================

st.set_page_config(
    page_title="Fechas Finales Match Integrado",
    page_icon="📅",
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
    st.warning(f"Logo no encontrado en ruta correcta: {LOGO_PATH}")


# =========================================================
# Columnas esperadas - FORMATO NUEVO
# =========================================================

COL_SOLICITUD_ME5A = "Solicitud de pedido - ME5A"
COL_FECHA_SOLICITUD_ME5A = "Fecha de solicitud - ME5A"
COL_FECHA_LIBERACION_ME5A = "Fecha de liberación - ME5A"
COL_FECHA_PEDIDO_ME5A = "Fecha de pedido - ME5A"
COL_FECHA_APROBACION_ARIBA = "Fecha de aprobación - ARIBA"
COL_FECHA_FACTURACION_NME = "Fecha facturación proveedor - NME80FN"
COL_FECHA_RECEPCION_NME = "Fecha recepción mercancía - NME80FN"
COL_ESTADO_MATCH = "Estado del match"

COLUMNAS_REQUERIDAS = [
    COL_SOLICITUD_ME5A,
    COL_FECHA_SOLICITUD_ME5A,
    COL_FECHA_LIBERACION_ME5A,
    COL_FECHA_PEDIDO_ME5A,
    COL_FECHA_APROBACION_ARIBA,
    COL_FECHA_FACTURACION_NME,
    COL_FECHA_RECEPCION_NME,
]

COLUMNAS_FECHAS_ORIGEN = [
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
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner="Leyendo archivo...")
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


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def validar_columnas_requeridas(df: pd.DataFrame):
    faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]

    if faltantes:
        columnas_disponibles = df.columns.tolist()
        raise ValueError(
            "Faltan columnas requeridas del formato nuevo: "
            f"{faltantes}. Columnas disponibles en el archivo: {columnas_disponibles}"
        )


def convertir_fecha_serie(serie: pd.Series) -> pd.Series:
    """
    Convierte fechas desde el formato nuevo.
    Soporta fechas reales, texto de fecha y enteros tipo timestamp en milisegundos
    como 1704067200000.
    """
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_limpia = serie.copy()
    serie_num = pd.to_numeric(serie_limpia, errors="coerce")
    valores_validos = serie_num.dropna()

    if not valores_validos.empty:
        mediana = valores_validos.abs().median()

        if mediana > 10**11:
            return pd.to_datetime(serie_num, unit="ms", errors="coerce")

        if mediana > 10**9:
            return pd.to_datetime(serie_num, unit="s", errors="coerce")

        if mediana > 10**5:
            return pd.to_datetime(serie_num, unit="D", origin="1899-12-30", errors="coerce")

    return pd.to_datetime(serie_limpia, errors="coerce")


def normalizar_estado_match(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if COL_ESTADO_MATCH in df.columns:
        df[COL_ESTADO_MATCH] = (
            df[COL_ESTADO_MATCH]
            .astype("string")
            .str.strip()
            .replace({
                "Sin match": "No encontrado en ARIBA ni NME80FN",
                "Match en ARIBA y NME80FN": "Encontrado en ARIBA y NME80FN",
                "Match solo en ARIBA": "Encontrado solo en ARIBA",
                "Match solo en NME80FN": "Encontrado solo en NME80FN"
            })
        )

    return df


@st.cache_data(show_spinner="Aplicando lógica de fechas finales...")
def aplicar_logica_fechas_finales(df: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_columnas(df)
    validar_columnas_requeridas(df)
    df = normalizar_estado_match(df)

    for col in COLUMNAS_FECHAS_ORIGEN:
        df[col] = convertir_fecha_serie(df[col])

    solped_str = df[COL_SOLICITUD_ME5A].astype("string").str.strip()
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

    return df


def reordenar_columnas_fechas_al_final(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    columnas_finales_fecha = [col for col in COLUMNAS_FECHAS_FINALES if col in df.columns]

    columnas_fecha_originales = [
        col for col in df.columns
        if (
            "fecha" in col.lower()
            or "fe.liber" in col.lower()
        )
        and col not in columnas_finales_fecha
    ]

    columnas_no_fecha = [
        col for col in df.columns
        if col not in columnas_fecha_originales
        and col not in columnas_finales_fecha
    ]

    nuevo_orden = columnas_no_fecha + columnas_fecha_originales + columnas_finales_fecha

    return df[nuevo_orden].copy()


def resumen_fechas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [col for col in COLUMNAS_FECHAS_FINALES if col in df.columns]
    total = len(df)
    data = []

    nombres = {
        "fecha_solicitud_final": "fecha de solicitud final",
        "fecha_liberacion_final": "fecha de liberación final",
        "fecha_pedido_final": "fecha de pedido final",
        "fecha_facturacion_final": "fecha de facturación final",
        "fecha_recepcion_final": "fecha de recepción final",
    }

    for col in columnas:
        no_nulos = int(df[col].notna().sum())
        nulos = int(df[col].isna().sum())

        data.append({
            "Mensaje": f"{no_nulos:,} registros de {total:,} en ME5A tienen {nombres.get(col, col)} informada",
            "Columna": col,
            "No nulos": no_nulos,
            "Nulos": nulos,
            "% Nulos": round(df[col].isna().mean() * 100, 2),
            "Fecha mínima": df[col].min(),
            "Fecha máxima": df[col].max()
        })

    return pd.DataFrame(data)


def generar_resumen_cambios_fechas(df_original: pd.DataFrame, df_final: pd.DataFrame) -> dict:
    total = int(len(df_final))

    solped_str = df_final[COL_SOLICITUD_ME5A].astype("string").str.strip()
    mask_solped_6 = solped_str.str.startswith("6").fillna(False)

    total_usa_ariba = int(mask_solped_6.sum())
    total_usa_me5a = int((~mask_solped_6).sum())

    ejemplo = None
    if total > 0:
        candidatos = df_final[df_final["fecha_liberacion_final"].notna()].copy()
        if candidatos.empty:
            candidatos = df_final.copy()
        ejemplo = candidatos.iloc[0].to_dict()

    return {
        "total_registros": total,
        "columnas_originales": int(len(df_original.columns)),
        "columnas_finales": int(len(df_final.columns)),
        "columnas_nuevas": int(len([col for col in df_final.columns if col not in df_original.columns])),
        "total_usa_ariba": total_usa_ariba,
        "total_usa_me5a": total_usa_me5a,
        "ejemplo": ejemplo,
    }


def formatear_valor(valor):
    if pd.isna(valor):
        return ""
    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")
    return str(valor)


def construir_tabla_ejemplo_fechas(ejemplo: dict) -> pd.DataFrame:
    if not ejemplo:
        return pd.DataFrame()

    solicitud = ejemplo.get(COL_SOLICITUD_ME5A, "")
    solicitud_str = str(solicitud).strip()
    usa_ariba = solicitud_str.startswith("6")

    campo_liberacion_origen = (
        COL_FECHA_APROBACION_ARIBA
        if usa_ariba
        else COL_FECHA_LIBERACION_ME5A
    )

    return pd.DataFrame([
        {
            "Fecha final": "fecha_solicitud_final",
            "Campo origen usado": COL_FECHA_SOLICITUD_ME5A,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_ME5A)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_solicitud_final")),
            "Regla aplicada": "Se conserva la fecha de solicitud de ME5A"
        },
        {
            "Fecha final": "fecha_liberacion_final",
            "Campo origen usado": campo_liberacion_origen,
            "Valor origen": formatear_valor(ejemplo.get(campo_liberacion_origen)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_liberacion_final")),
            "Regla aplicada": (
                "Si Solicitud de pedido - ME5A empieza con 6, usa Fecha de aprobación - ARIBA; "
                "si no, usa Fecha de liberación - ME5A"
            )
        },
        {
            "Fecha final": "fecha_pedido_final",
            "Campo origen usado": COL_FECHA_PEDIDO_ME5A,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_PEDIDO_ME5A)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_pedido_final")),
            "Regla aplicada": "Se conserva la fecha de pedido de ME5A"
        },
        {
            "Fecha final": "fecha_facturacion_final",
            "Campo origen usado": COL_FECHA_FACTURACION_NME,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_FACTURACION_NME)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_facturacion_final")),
            "Regla aplicada": "Se usa la fecha de facturación proveedor de NME80FN"
        },
        {
            "Fecha final": "fecha_recepcion_final",
            "Campo origen usado": COL_FECHA_RECEPCION_NME,
            "Valor origen": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_NME)),
            "Resultado final": formatear_valor(ejemplo.get("fecha_recepcion_final")),
            "Regla aplicada": "Se usa la fecha de recepción de mercancía de NME80FN"
        },
    ])


def mostrar_resumen_cambios_fechas(resumen_cambios: dict):
    total = resumen_cambios["total_registros"]

    with st.expander("Cambios realizados y lógica de fechas finales", expanded=False):
        st.info(
            f"""
            **Archivos procesados**

            - Se procesaron **{total:,} registros** del match integrado.
            - El archivo original contenía **{resumen_cambios['columnas_originales']:,} columnas**.
            - El resultado final contiene **{resumen_cambios['columnas_finales']:,} columnas**.
            - Se agregaron **{resumen_cambios['columnas_nuevas']:,} columnas nuevas**.

            **Resultado de la lógica de fechas**

            - **{total:,} registros de {total:,} en ME5A fueron procesados para generar fechas finales**.
            - **{resumen_cambios['total_usa_ariba']:,} registros de {total:,} en ME5A usan Fecha de aprobación - ARIBA para la liberación**.
            - **{resumen_cambios['total_usa_me5a']:,} registros de {total:,} en ME5A usan Fecha de liberación - ME5A para la liberación**.

            **Regla principal de liberación**

            - Si **Solicitud de pedido - ME5A** empieza con **6**, la **fecha_liberacion_final** usa **Fecha de aprobación - ARIBA**.
            - Si **Solicitud de pedido - ME5A** no empieza con **6**, la **fecha_liberacion_final** usa **Fecha de liberación - ME5A**.
            """
        )

        st.subheader("Ejemplo de lógica de fechas finales")
        tabla_ejemplo = construir_tabla_ejemplo_fechas(resumen_cambios.get("ejemplo"))

        if tabla_ejemplo.empty:
            st.warning("No se encontró un registro disponible para mostrar como ejemplo.")
        else:
            st.table(tabla_ejemplo)


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


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


@st.cache_data(show_spinner="Preparando Parquet...")
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner="Preparando CSV...")
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner="Preparando Excel...")
def convertir_a_excel_cache(df: pd.DataFrame, resumen: pd.DataFrame) -> bytes:
    return convertir_a_excel(df, resumen)


# =========================================================
# Interfaz
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Fechas Finales Match Integrado
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube el archivo <b>match_integrado_me5a_ariba_nme80fn.parquet</b>.
        La app usa el formato nuevo exportado del match integrado y agrega fechas finales
        homologadas para solicitud, liberación, pedido, facturación y recepción.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.header("Configuración")

    pagina = st.radio(
        "Menú",
        options=[
            "Procesamiento",
            "Diagnóstico",
            "Descarga"
        ],
        index=0
    )

    st.divider()

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

    ordenar_fechas_final = st.checkbox(
        "Mover columnas de fecha al final",
        value=True
    )

    st.caption("El separador solo aplica si subes archivos CSV.")


uploaded_file = st.file_uploader(
    "Selecciona archivo match integrado",
    type=["parquet", "xlsx", "csv"]
)


if uploaded_file is not None:
    try:
        df_original = leer_archivo_cache(
            bytes_archivo=uploaded_file.getvalue(),
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv
        )

        df_original = limpiar_columnas(df_original)
        columnas_originales = list(df_original.columns)

        df_final = aplicar_logica_fechas_finales(df_original)

        columnas_nuevas = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        resumen_cambios = generar_resumen_cambios_fechas(
            df_original=df_original,
            df_final=df_final
        )

        if ordenar_fechas_final:
            df_final = reordenar_columnas_fechas_al_final(df_final)

        resumen = resumen_fechas(df_final)

        if pagina == "Procesamiento":
            st.success("Lógica de fechas finales aplicada correctamente.")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Filas originales", f"{len(df_original):,}")
            col2.metric("Filas finales", f"{len(df_final):,}")
            col3.metric("Columnas originales", f"{len(columnas_originales):,}")
            col4.metric("Columnas nuevas", f"{len(columnas_nuevas):,}")

            solped_6 = (
                df_original[COL_SOLICITUD_ME5A]
                .astype("string")
                .str.strip()
                .str.startswith("6")
                .fillna(False)
                .sum()
            )

            st.metric("SolPed que empiezan con 6", f"{int(solped_6):,}")

            mostrar_resumen_cambios_fechas(resumen_cambios)

            st.subheader("Vista previa original")
            st.dataframe(
                df_original.head(30),
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Columnas nuevas agregadas")
            st.write(columnas_nuevas)

            st.subheader("Vista previa con fechas finales")

            columnas_preferidas = [
                COL_SOLICITUD_ME5A,
                "Pedido - ME5A",
                "Posición solicitud de pedido - ME5A",
                "Posición de pedido - ME5A",
                "Material - ME5A",
                "Texto breve - ME5A",
                "Centro - ME5A",
                COL_ESTADO_MATCH,
                "criterio_fecha_liberacion",
                COL_FECHA_SOLICITUD_ME5A,
                COL_FECHA_LIBERACION_ME5A,
                COL_FECHA_APROBACION_ARIBA,
                COL_FECHA_PEDIDO_ME5A,
                COL_FECHA_FACTURACION_NME,
                COL_FECHA_RECEPCION_NME,
                "fecha_solicitud_final",
                "fecha_liberacion_final",
                "fecha_pedido_final",
                "fecha_facturacion_final",
                "fecha_recepcion_final"
            ]

            columnas_preferidas = [
                col for col in columnas_preferidas
                if col in df_final.columns
            ]

            st.dataframe(
                df_final[columnas_preferidas].head(100),
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Regla aplicada")

            st.dataframe(
                pd.DataFrame({
                    "Columna nueva": [
                        "fecha_solicitud_final",
                        "fecha_liberacion_final",
                        "fecha_pedido_final",
                        "fecha_facturacion_final",
                        "fecha_recepcion_final",
                        "criterio_fecha_liberacion"
                    ],
                    "Regla": [
                        "Usa Fecha de solicitud - ME5A",
                        "Si Solicitud de pedido - ME5A empieza con 6 usa Fecha de aprobación - ARIBA; si no, usa Fecha de liberación - ME5A",
                        "Usa Fecha de pedido - ME5A",
                        "Usa Fecha facturación proveedor - NME80FN",
                        "Usa Fecha recepción mercancía - NME80FN",
                        "Texto explicativo de la regla usada para fecha_liberacion_final"
                    ]
                }),
                use_container_width=True,
                hide_index=True
            )

        elif pagina == "Diagnóstico":
            st.subheader("Diagnóstico de fechas finales")

            st.dataframe(
                resumen,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Nulos por fecha final")

            if not resumen.empty:
                st.bar_chart(resumen.set_index("Columna")["Nulos"])

            st.divider()

            st.subheader("Distribución del criterio de liberación")

            if "criterio_fecha_liberacion" in df_final.columns:
                conteo_criterio = (
                    df_final["criterio_fecha_liberacion"]
                    .value_counts(dropna=False)
                    .reset_index()
                )

                conteo_criterio.columns = ["Criterio", "Cantidad"]

                st.dataframe(
                    conteo_criterio,
                    use_container_width=True,
                    hide_index=True
                )

                st.bar_chart(conteo_criterio.set_index("Criterio")["Cantidad"])

            st.divider()

            st.subheader("Filas con fecha_liberacion_final nula")

            if "fecha_liberacion_final" in df_final.columns:
                df_nulos_liberacion = df_final[
                    df_final["fecha_liberacion_final"].isna()
                ].copy()

                st.write(f"Cantidad: {len(df_nulos_liberacion):,}")

                columnas_nulos = [
                    COL_SOLICITUD_ME5A,
                    COL_FECHA_LIBERACION_ME5A,
                    COL_FECHA_APROBACION_ARIBA,
                    "criterio_fecha_liberacion",
                    "fecha_liberacion_final",
                    COL_ESTADO_MATCH
                ]

                columnas_nulos = [
                    col for col in columnas_nulos
                    if col in df_nulos_liberacion.columns
                ]

                st.dataframe(
                    df_nulos_liberacion[columnas_nulos].head(200),
                    use_container_width=True,
                    hide_index=True
                )

            st.divider()

            st.subheader("Control de columnas")

            st.write("Columnas originales conservadas:", len(columnas_originales))
            st.write("Columnas nuevas agregadas:", len(columnas_nuevas))
            st.write("Listado de columnas nuevas:")
            st.write(columnas_nuevas)

        elif pagina == "Descarga":
            st.subheader("Descargar resultado con fechas finales")

            st.info(
                "El archivo descargado conserva todas las columnas originales "
                "y agrega las columnas nuevas de fechas finales."
            )

            formato_descarga = st.radio(
                "Formato de descarga",
                options=["Parquet", "CSV", "Excel"],
                horizontal=True
            )

            if formato_descarga == "Parquet":
                parquet_bytes = convertir_a_parquet_cache(df_final)

                st.download_button(
                    label="Descargar Parquet",
                    data=parquet_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn_fechas_finales.parquet",
                    mime="application/octet-stream"
                )

            elif formato_descarga == "CSV":
                csv_bytes = convertir_a_csv_cache(df_final)

                st.download_button(
                    label="Descargar CSV",
                    data=csv_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn_fechas_finales.csv",
                    mime="text/csv"
                )

            elif formato_descarga == "Excel":
                limite_excel = 250_000

                if len(df_final) > limite_excel:
                    st.warning(
                        f"El resultado tiene {len(df_final):,} filas. "
                        f"Para evitar problemas de memoria, descarga en Parquet o CSV. "
                        f"Excel está limitado a {limite_excel:,} filas."
                    )
                else:
                    excel_bytes = convertir_a_excel_cache(df_final, resumen)

                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name="match_integrado_me5a_ariba_nme80fn_fechas_finales.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga el archivo match integrado para comenzar.")
