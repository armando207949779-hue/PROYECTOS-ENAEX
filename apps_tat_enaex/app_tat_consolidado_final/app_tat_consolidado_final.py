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
    page_title="Performance TAT - Match Integrado",
    page_icon="📊",
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


def bool_array(condicion):
    return pd.Series(condicion).fillna(False).to_numpy(dtype=bool)


def extraer_tipo_oc(valor):
    if pd.isna(valor):
        return pd.NA

    texto = str(valor).strip()

    try:
        texto = str(int(float(texto)))
    except Exception:
        texto = texto.replace(".0", "")

    if len(texto) >= 2:
        return texto[:2]

    return pd.NA


def diferencia_dias(fecha_fin, fecha_inicio):
    return (fecha_fin - fecha_inicio).dt.days


def evaluar_cumplimiento(valor, umbral):
    resultado = valor <= umbral
    resultado = resultado.mask(valor.isna() | umbral.isna(), pd.NA)
    return resultado


def dias_incumplimiento(valor, umbral):
    resultado = valor - umbral
    resultado = resultado.where(resultado > 0, 0)
    resultado = resultado.mask(valor.isna() | umbral.isna(), np.nan)
    return resultado


def validar_columnas_requeridas(df: pd.DataFrame):
    columnas_requeridas = [
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final"
    ]

    faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")


# =========================================================
# Lógica principal de performance
# =========================================================

@st.cache_data(show_spinner="Aplicando lógica de performance...")
def aplicar_logica_performance(df_original: pd.DataFrame) -> pd.DataFrame:
    df = df_original.copy()

    df.columns = df.columns.astype(str).str.strip()

    validar_columnas_requeridas(df)

    # =====================================================
    # Asegurar fechas
    # =====================================================

    columnas_fecha = [
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final",
        "Fecha de solicitud",
        "Fe.liber.Z",
        "Fecha de pedido",
        "Fecha de entrega",
        "Fecha de liberación",
        "ariba_fecha_solicitud_compra",
        "ariba_fecha_aprobacion",
        "nme_fecha_entrada",
        "nme_fecha_documento",
        "nme_fecha_contabiliz",
        "nme_fecha_facturacion_proveedor",
        "nme_fecha_entrada_mercancia_recepcion"
    ]

    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # =====================================================
    # Tipo de OC
    # 35 = Ariba / Nacional
    # 45 = ERP / Nacional
    # 47 = ERP / Internacional
    # =====================================================

    if "Pedido" in df.columns:
        df["tipo_oc"] = df["Pedido"].apply(extraer_tipo_oc)
    elif "nme_documento_compras" in df.columns:
        df["tipo_oc"] = df["nme_documento_compras"].apply(extraer_tipo_oc)
    else:
        df["tipo_oc"] = pd.NA

    df["tipo_oc"] = df["tipo_oc"].astype("string")

    # =====================================================
    # Clasificaciones
    # =====================================================

    df["origen_oc"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47"))
        ],
        [
            "Nacional",
            "Internacional"
        ],
        default="Otro"
    )

    df["sistema_oc"] = np.select(
        [
            bool_array(df["tipo_oc"].eq("35")),
            bool_array(df["tipo_oc"].isin(["45", "47"]))
        ],
        [
            "Ariba",
            "ERP"
        ],
        default="Otro"
    )

    if "ariba_tipo_compra" in df.columns:
        tipo_compra_num = pd.to_numeric(df["ariba_tipo_compra"], errors="coerce")
    else:
        tipo_compra_num = pd.Series(np.nan, index=df.index)

    df["nombre_tipo_compra"] = np.select(
        [
            bool_array(tipo_compra_num.eq(1)),
            bool_array(tipo_compra_num.eq(2)),
            bool_array(tipo_compra_num.eq(3))
        ],
        [
            "Catalogada",
            "No catalogada",
            "Directa"
        ],
        default="Otro"
    )

    # =====================================================
    # Cálculo económico
    # Monto = Cantidad solicitada * Precio de valoración
    # =====================================================

    if "Cantidad solicitada" in df.columns and "Precio de valoración" in df.columns:
        df["monto_valoracion"] = (
            pd.to_numeric(df["Cantidad solicitada"], errors="coerce")
            * pd.to_numeric(df["Precio de valoración"], errors="coerce")
        )
    else:
        df["monto_valoracion"] = np.nan

    # =====================================================
    # Fecha inicio proveedor
    # OC 35      -> fecha_pedido_final
    # OC 45 / 47 -> fecha_pedido_final + 3 días
    # =====================================================

    df["fecha_inicio_proveedor"] = pd.NaT

    mask_oc_35 = bool_array(df["tipo_oc"].eq("35"))
    mask_oc_45_47 = bool_array(df["tipo_oc"].isin(["45", "47"]))

    df.loc[mask_oc_35, "fecha_inicio_proveedor"] = df.loc[
        mask_oc_35,
        "fecha_pedido_final"
    ]

    df.loc[mask_oc_45_47, "fecha_inicio_proveedor"] = (
        df.loc[mask_oc_45_47, "fecha_pedido_final"]
        + pd.Timedelta(days=3)
    )

    df["fecha_inicio_proveedor"] = pd.to_datetime(
        df["fecha_inicio_proveedor"],
        errors="coerce"
    )

    # =====================================================
    # Cálculos de días
    # =====================================================

    df["dx_lib_solped"] = diferencia_dias(
        df["fecha_liberacion_final"],
        df["fecha_solicitud_final"]
    )

    df["dx_comprador_1"] = diferencia_dias(
        df["fecha_pedido_final"],
        df["fecha_liberacion_final"]
    )

    df["dx_lib_pedido"] = np.nan

    df["dx_logistica"] = diferencia_dias(
        df["fecha_recepcion_final"],
        df["fecha_facturacion_final"]
    )

    df["dx_proveedor"] = diferencia_dias(
        df["fecha_recepcion_final"],
        df["fecha_inicio_proveedor"]
    )

    df["dx_tat"] = diferencia_dias(
        df["fecha_recepcion_final"],
        df["fecha_solicitud_final"]
    )

    # =====================================================
    # Umbrales de cumplimiento
    # =====================================================

    df["umbral_lib_solped"] = 2
    df["umbral_comprador_1"] = 10
    df["umbral_lib_pedido"] = 2
    df["umbral_logistica"] = 11

    df["umbral_tat"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47"))
        ],
        [
            40,
            70
        ],
        default=np.nan
    )

    df["umbral_proveedor"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47"))
        ],
        [
            20,
            60
        ],
        default=np.nan
    )

    df["umbral_tat"] = pd.to_numeric(df["umbral_tat"], errors="coerce")
    df["umbral_proveedor"] = pd.to_numeric(df["umbral_proveedor"], errors="coerce")

    # =====================================================
    # Evaluación de performance
    # =====================================================

    df["performance_lib_solped"] = evaluar_cumplimiento(
        df["dx_lib_solped"],
        pd.Series(df["umbral_lib_solped"], index=df.index)
    )

    df["performance_comprador_1"] = evaluar_cumplimiento(
        df["dx_comprador_1"],
        pd.Series(df["umbral_comprador_1"], index=df.index)
    )

    df["performance_lib_pedido"] = evaluar_cumplimiento(
        pd.Series(df["dx_lib_pedido"], index=df.index),
        pd.Series(df["umbral_lib_pedido"], index=df.index)
    )

    df["performance_logistica"] = evaluar_cumplimiento(
        df["dx_logistica"],
        pd.Series(df["umbral_logistica"], index=df.index)
    )

    df["performance_tat"] = evaluar_cumplimiento(
        df["dx_tat"],
        df["umbral_tat"]
    )

    df["performance_proveedor"] = evaluar_cumplimiento(
        df["dx_proveedor"],
        df["umbral_proveedor"]
    )

    # =====================================================
    # Días de incumplimiento
    # =====================================================

    df["dias_incumplimiento_lib_solped"] = dias_incumplimiento(
        df["dx_lib_solped"],
        pd.Series(df["umbral_lib_solped"], index=df.index)
    )

    df["dias_incumplimiento_comprador_1"] = dias_incumplimiento(
        df["dx_comprador_1"],
        pd.Series(df["umbral_comprador_1"], index=df.index)
    )

    df["dias_incumplimiento_logistica"] = dias_incumplimiento(
        df["dx_logistica"],
        pd.Series(df["umbral_logistica"], index=df.index)
    )

    df["dias_incumplimiento_tat"] = dias_incumplimiento(
        df["dx_tat"],
        df["umbral_tat"]
    )

    df["dias_incumplimiento_proveedor"] = dias_incumplimiento(
        df["dx_proveedor"],
        df["umbral_proveedor"]
    )

    # =====================================================
    # Incumplimiento general
    # =====================================================

    columnas_incumplimiento = [
        "dias_incumplimiento_lib_solped",
        "dias_incumplimiento_comprador_1",
        "dias_incumplimiento_logistica",
        "dias_incumplimiento_tat",
        "dias_incumplimiento_proveedor"
    ]

    df["dias_incumplimiento_max"] = df[columnas_incumplimiento].max(
        axis=1,
        skipna=True
    )

    df["dias_incumplimiento_max"] = df["dias_incumplimiento_max"].fillna(0)
    df["incumplimiento"] = df["dias_incumplimiento_max"].gt(0)

    # =====================================================
    # Rango de incumplimiento
    # =====================================================

    df["rango_incumplimiento"] = np.select(
        [
            bool_array(df["dias_incumplimiento_max"].eq(0)),
            bool_array(df["dias_incumplimiento_max"].between(1, 5, inclusive="both")),
            bool_array(df["dias_incumplimiento_max"].between(6, 15, inclusive="both")),
            bool_array(df["dias_incumplimiento_max"].between(16, 30, inclusive="both")),
            bool_array(df["dias_incumplimiento_max"].gt(30))
        ],
        [
            "Sin incumplimiento",
            "0-5 días",
            "6-15 días",
            "16-30 días",
            "Mayor a un mes"
        ],
        default="Sin información"
    )

    return df


# =========================================================
# Diagnósticos
# =========================================================

def resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        "performance_lib_solped",
        "performance_comprador_1",
        "performance_lib_pedido",
        "performance_logistica",
        "performance_tat",
        "performance_proveedor"
    ]

    data = []

    for col in metricas:
        if col in df.columns:
            serie = df[col]

            data.append({
                "Métrica": col,
                "Cumple": int(serie.eq(True).sum()),
                "No cumple": int(serie.eq(False).sum()),
                "Sin información": int(serie.isna().sum()),
                "% Cumple": round(serie.eq(True).mean() * 100, 2)
            })

    return pd.DataFrame(data)


def resumen_columnas_nuevas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "tipo_oc",
        "origen_oc",
        "sistema_oc",
        "nombre_tipo_compra",
        "monto_valoracion",
        "fecha_inicio_proveedor",
        "dx_lib_solped",
        "dx_comprador_1",
        "dx_lib_pedido",
        "dx_logistica",
        "dx_proveedor",
        "dx_tat",
        "umbral_lib_solped",
        "umbral_comprador_1",
        "umbral_lib_pedido",
        "umbral_logistica",
        "umbral_tat",
        "umbral_proveedor",
        "performance_lib_solped",
        "performance_comprador_1",
        "performance_lib_pedido",
        "performance_logistica",
        "performance_tat",
        "performance_proveedor",
        "dias_incumplimiento_lib_solped",
        "dias_incumplimiento_comprador_1",
        "dias_incumplimiento_logistica",
        "dias_incumplimiento_tat",
        "dias_incumplimiento_proveedor",
        "dias_incumplimiento_max",
        "incumplimiento",
        "rango_incumplimiento"
    ]

    columnas = [col for col in columnas if col in df.columns]

    return pd.DataFrame({
        "Columna nueva": columnas,
        "Nulos": [df[col].isna().sum() for col in columnas],
        "% Nulos": [round(df[col].isna().mean() * 100, 2) for col in columnas],
        "Tipo dato": [str(df[col].dtype) for col in columnas]
    })


# =========================================================
# Exportación
# =========================================================

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


def convertir_a_excel(
    df: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame
) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Performance_TAT"
        )

        resumen_perf.to_excel(
            writer,
            index=False,
            sheet_name="Resumen_Performance"
        )

        resumen_cols.to_excel(
            writer,
            index=False,
            sheet_name="Columnas_Nuevas"
        )

    return output.getvalue()


@st.cache_data(show_spinner="Preparando Parquet...")
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner="Preparando CSV...")
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner="Preparando Excel...")
def convertir_a_excel_cache(
    df: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame
) -> bytes:
    return convertir_a_excel(df, resumen_perf, resumen_cols)


# =========================================================
# Interfaz
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Performance TAT - Match Integrado
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube el archivo <b>match_integrado_me5a_ariba_nme80fn_fechas_finales.parquet</b>.
        La app conserva todas las columnas originales y agrega clasificación,
        cálculos de días, performance, umbrales e incumplimientos.
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
            "Resumen",
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

    st.caption(
        "El separador solo aplica si subes archivos CSV."
    )


uploaded_file = st.file_uploader(
    "Selecciona archivo con fechas finales",
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

        df_final = aplicar_logica_performance(df_original)

        columnas_agregadas = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        resumen_perf = resumen_performance(df_final)
        resumen_cols = resumen_columnas_nuevas(df_final)

        if pagina == "Procesamiento":
            st.success("Lógica de performance aplicada correctamente.")

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
                f"{len(columnas_agregadas):,}"
            )

            st.subheader("Vista previa original")
            st.dataframe(
                df_original.head(30),
                use_container_width=True
            )

            st.subheader("Vista previa con performance")

            columnas_preferidas = [
                "Solicitud de pedido",
                "Pedido",
                "tipo_oc",
                "origen_oc",
                "sistema_oc",
                "nombre_tipo_compra",
                "Cantidad solicitada",
                "Precio de valoración",
                "monto_valoracion",
                "fecha_solicitud_final",
                "fecha_liberacion_final",
                "fecha_pedido_final",
                "fecha_facturacion_final",
                "fecha_recepcion_final",
                "fecha_inicio_proveedor",
                "dx_lib_solped",
                "dx_comprador_1",
                "dx_lib_pedido",
                "dx_logistica",
                "dx_proveedor",
                "dx_tat",
                "umbral_tat",
                "umbral_proveedor",
                "performance_lib_solped",
                "performance_comprador_1",
                "performance_lib_pedido",
                "performance_logistica",
                "performance_tat",
                "performance_proveedor",
                "dias_incumplimiento_max",
                "incumplimiento",
                "rango_incumplimiento"
            ]

            columnas_preferidas = [
                col for col in columnas_preferidas
                if col in df_final.columns
            ]

            st.dataframe(
                df_final[columnas_preferidas].head(200),
                use_container_width=True
            )

            st.subheader("Columnas nuevas agregadas")
            st.dataframe(
                resumen_cols,
                use_container_width=True
            )

        elif pagina == "Resumen":
            st.subheader("Resumen de performance")

            st.dataframe(
                resumen_perf,
                use_container_width=True
            )

            if not resumen_perf.empty:
                st.bar_chart(
                    resumen_perf.set_index("Métrica")["% Cumple"]
                )

            st.divider()

            st.subheader("Rango de incumplimiento")

            if "rango_incumplimiento" in df_final.columns:
                conteo_rango = (
                    df_final["rango_incumplimiento"]
                    .value_counts(dropna=False)
                    .reset_index()
                )

                conteo_rango.columns = [
                    "Rango incumplimiento",
                    "Cantidad"
                ]

                st.dataframe(
                    conteo_rango,
                    use_container_width=True
                )

                st.bar_chart(
                    conteo_rango.set_index("Rango incumplimiento")["Cantidad"]
                )

            st.divider()

            st.subheader("Distribución por tipo de OC")

            if "tipo_oc" in df_final.columns:
                conteo_tipo_oc = (
                    df_final["tipo_oc"]
                    .value_counts(dropna=False)
                    .reset_index()
                )

                conteo_tipo_oc.columns = [
                    "Tipo OC",
                    "Cantidad"
                ]

                st.dataframe(
                    conteo_tipo_oc,
                    use_container_width=True
                )

                st.bar_chart(
                    conteo_tipo_oc.set_index("Tipo OC")["Cantidad"]
                )

            st.divider()

            st.subheader("Incumplimientos")

            if "incumplimiento" in df_final.columns:
                conteo_inc = (
                    df_final["incumplimiento"]
                    .value_counts(dropna=False)
                    .reset_index()
                )

                conteo_inc.columns = [
                    "Incumplimiento",
                    "Cantidad"
                ]

                st.dataframe(
                    conteo_inc,
                    use_container_width=True
                )

            st.divider()

            st.subheader("Top filas con mayor incumplimiento")

            if "dias_incumplimiento_max" in df_final.columns:
                columnas_top = [
                    "Solicitud de pedido",
                    "Pedido",
                    "tipo_oc",
                    "origen_oc",
                    "sistema_oc",
                    "dx_tat",
                    "dx_proveedor",
                    "dx_logistica",
                    "dias_incumplimiento_max",
                    "rango_incumplimiento",
                    "fecha_solicitud_final",
                    "fecha_recepcion_final"
                ]

                columnas_top = [
                    col for col in columnas_top
                    if col in df_final.columns
                ]

                st.dataframe(
                    df_final
                    .sort_values("dias_incumplimiento_max", ascending=False)
                    [columnas_top]
                    .head(200),
                    use_container_width=True
                )

        elif pagina == "Descarga":
            st.subheader("Descargar resultado con performance")

            st.info(
                "El resultado conserva todas las columnas originales y agrega "
                "las columnas nuevas de clasificación, días, performance e incumplimiento."
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
                    file_name="match_integrado_me5a_ariba_nme80fn_performance.parquet",
                    mime="application/octet-stream"
                )

            elif formato_descarga == "CSV":
                csv_bytes = convertir_a_csv_cache(df_final)

                st.download_button(
                    label="Descargar CSV",
                    data=csv_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn_performance.csv",
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
                        resumen_perf,
                        resumen_cols
                    )

                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name="match_integrado_me5a_ariba_nme80fn_performance.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga el archivo con fechas finales para comenzar.")