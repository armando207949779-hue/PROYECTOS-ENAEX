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
    st.error(f"Logo no encontrado en ruta correcta: {LOGO_PATH}")


# =========================================================
# Funciones generales
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;)":
        return ";"
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


def validar_columnas_requeridas(df: pd.DataFrame):
    columnas_requeridas = [
        "Solicitud de pedido",
        "Fecha de solicitud",
        "Fe.liber.Z",
        "Fecha de pedido",
        "ariba_fecha_aprobacion",
        "nme_fecha_facturacion_proveedor",
        "nme_fecha_entrada_mercancia_recepcion"
    ]

    faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")


@st.cache_data(show_spinner="Aplicando lógica de fechas finales...")
def aplicar_logica_fechas_finales(df: pd.DataFrame) -> pd.DataFrame:
    # Conserva TODAS las columnas originales
    df = df.copy()

    # Limpia nombres de columnas, pero no elimina ninguna
    df.columns = df.columns.astype(str).str.strip()

    validar_columnas_requeridas(df)

    columnas_fecha_base = [
        "Fecha de solicitud",
        "Fe.liber.Z",
        "Fecha de pedido",
        "ariba_fecha_aprobacion",
        "nme_fecha_facturacion_proveedor",
        "nme_fecha_entrada_mercancia_recepcion"
    ]

    for col in columnas_fecha_base:
        df[col] = pd.to_datetime(
            df[col],
            errors="coerce"
        )

    # Identificar SolPed que empiezan con 6
    solped_str = (
        df["Solicitud de pedido"]
        .astype("string")
        .str.strip()
    )

    mask_solped_6 = solped_str.str.startswith("6").fillna(False)

    # Crear columnas nuevas sin borrar ni reemplazar las originales
    df["fecha_solicitud_final"] = df["Fecha de solicitud"]

    df["fecha_liberacion_final"] = np.where(
        mask_solped_6,
        df["ariba_fecha_aprobacion"],
        df["Fe.liber.Z"]
    )

    df["fecha_pedido_final"] = df["Fecha de pedido"]

    df["fecha_facturacion_final"] = df["nme_fecha_facturacion_proveedor"]

    df["fecha_recepcion_final"] = df["nme_fecha_entrada_mercancia_recepcion"]

    columnas_nuevas_fecha = [
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final"
    ]

    for col in columnas_nuevas_fecha:
        df[col] = pd.to_datetime(
            df[col],
            errors="coerce"
        )

    df["criterio_fecha_liberacion"] = np.where(
        mask_solped_6,
        "Solicitud de pedido empieza con 6: usa ariba_fecha_aprobacion",
        "Solicitud de pedido no empieza con 6: usa Fe.liber.Z"
    )

    return df


def reordenar_columnas_fechas_al_final(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    columnas_finales_fecha = [
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final"
    ]

    columnas_finales_fecha = [
        col for col in columnas_finales_fecha
        if col in df.columns
    ]

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

    nuevo_orden = (
        columnas_no_fecha
        + columnas_fecha_originales
        + columnas_finales_fecha
    )

    return df[nuevo_orden].copy()


def resumen_fechas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final"
    ]

    columnas = [
        col for col in columnas
        if col in df.columns
    ]

    data = []

    for col in columnas:
        data.append({
            "Columna": col,
            "No nulos": df[col].notna().sum(),
            "Nulos": df[col].isna().sum(),
            "% Nulos": round(df[col].isna().mean() * 100, 2),
            "Fecha mínima": df[col].min(),
            "Fecha máxima": df[col].max()
        })

    return pd.DataFrame(data)


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
        La app conserva todas las columnas originales y agrega fechas finales
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

    st.caption(
        "El separador solo aplica si subes archivos CSV."
    )


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

        columnas_originales = list(df_original.columns)

        df_final = aplicar_logica_fechas_finales(df_original)

        columnas_nuevas = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        if ordenar_fechas_final:
            df_final = reordenar_columnas_fechas_al_final(df_final)

        resumen = resumen_fechas(df_final)

        if pagina == "Procesamiento":
            st.success("Lógica de fechas finales aplicada correctamente.")

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

            solped_6 = (
                df_original["Solicitud de pedido"]
                .astype("string")
                .str.strip()
                .str.startswith("6")
                .fillna(False)
                .sum()
            )

            st.metric(
                "SolPed que empiezan con 6",
                f"{solped_6:,}"
            )

            st.subheader("Vista previa original")
            st.dataframe(
                df_original.head(30),
                use_container_width=True
            )

            st.subheader("Columnas nuevas agregadas")
            st.write(columnas_nuevas)

            st.subheader("Vista previa con fechas finales")

            columnas_preferidas = [
                "Solicitud de pedido",
                "Pedido",
                "Pos.solicitud pedido",
                "Posición de pedido",
                "Material",
                "Texto breve",
                "Centro",
                "estado_match",
                "score_total_integrado",
                "criterio_fecha_liberacion",
                "Fecha de solicitud",
                "Fe.liber.Z",
                "ariba_fecha_aprobacion",
                "Fecha de pedido",
                "nme_fecha_facturacion_proveedor",
                "nme_fecha_entrada_mercancia_recepcion",
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
                use_container_width=True
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
                        "Fecha de solicitud",
                        "Si Solicitud de pedido empieza con 6 usa ariba_fecha_aprobacion; si no, usa Fe.liber.Z",
                        "Fecha de pedido",
                        "nme_fecha_facturacion_proveedor",
                        "nme_fecha_entrada_mercancia_recepcion",
                        "Texto explicativo de la regla usada para fecha_liberacion_final"
                    ]
                }),
                use_container_width=True
            )

        elif pagina == "Diagnóstico":
            st.subheader("Diagnóstico de fechas finales")

            st.dataframe(
                resumen,
                use_container_width=True
            )

            st.subheader("Nulos por fecha final")

            if not resumen.empty:
                st.bar_chart(
                    resumen.set_index("Columna")["Nulos"]
                )

            st.divider()

            st.subheader("Distribución del criterio de liberación")

            if "criterio_fecha_liberacion" in df_final.columns:
                conteo_criterio = (
                    df_final["criterio_fecha_liberacion"]
                    .value_counts(dropna=False)
                    .reset_index()
                )

                conteo_criterio.columns = [
                    "Criterio",
                    "Cantidad"
                ]

                st.dataframe(
                    conteo_criterio,
                    use_container_width=True
                )

                st.bar_chart(
                    conteo_criterio.set_index("Criterio")["Cantidad"]
                )

            st.divider()

            st.subheader("Filas con fecha_liberacion_final nula")

            if "fecha_liberacion_final" in df_final.columns:
                df_nulos_liberacion = df_final[
                    df_final["fecha_liberacion_final"].isna()
                ].copy()

                st.write(f"Cantidad: {len(df_nulos_liberacion):,}")

                columnas_nulos = [
                    "Solicitud de pedido",
                    "Fe.liber.Z",
                    "ariba_fecha_aprobacion",
                    "criterio_fecha_liberacion",
                    "fecha_liberacion_final",
                    "estado_match"
                ]

                columnas_nulos = [
                    col for col in columnas_nulos
                    if col in df_nulos_liberacion.columns
                ]

                st.dataframe(
                    df_nulos_liberacion[columnas_nulos].head(200),
                    use_container_width=True
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
                options=[
                    "Parquet",
                    "CSV",
                    "Excel"
                ],
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
                    excel_bytes = convertir_a_excel_cache(
                        df_final,
                        resumen
                    )

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