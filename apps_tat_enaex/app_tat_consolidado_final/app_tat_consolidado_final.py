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
    page_title="Performance TAT - Match Integrado",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================================================
# Columnas esperadas
# =========================================================

# Fechas finales: se mantienen con estos nombres porque el archivo procesado las trae así.
COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

# Columnas de origen reales del dataframe integrado.
# Nota: "Precio de valoración" no trae sufijo de origen en el dataframe recibido.
COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - NME80FN"
COL_TIPO_COMPRA_ARIBA = "Tipo de compra - ARIBA"
COL_CANTIDAD_SOLICITADA = "Cantidad solicitada - ME5A"
COL_PRECIO_VALORACION = "Precio de valoración"

COLUMNAS_REQUERIDAS_PERFORMANCE = [
    COL_FECHA_SOLICITUD_FINAL,
    COL_FECHA_LIBERACION_FINAL,
    COL_FECHA_PEDIDO_FINAL,
    COL_FECHA_FACTURACION_FINAL,
    COL_FECHA_RECEPCION_FINAL,
]

COLUMNAS_FECHA_PERFORMANCE = [
    # Fechas finales usadas por el cálculo de performance.
    COL_FECHA_SOLICITUD_FINAL,
    COL_FECHA_LIBERACION_FINAL,
    COL_FECHA_PEDIDO_FINAL,
    COL_FECHA_FACTURACION_FINAL,
    COL_FECHA_RECEPCION_FINAL,

    # Fechas de origen ME5A.
    "Fecha de solicitud - ME5A",
    "Fecha modificación",
    "Fecha de liberación - ME5A",
    "Fecha de pedido - ME5A",
    "Fecha de entrega - ME5A",
    "Fecha de liberación",

    # Fechas de origen ARIBA.
    "Fecha solicitud de compra - ARIBA",
    "Fecha de aprobación - ARIBA",

    # Fechas de origen NME80FN.
    "Fecha de entrada - NME80FN",
    "Fecha de documento - NME80FN",
    "Fecha contabilización - NME80FN",
    "Fecha facturación proveedor - NME80FN",
    "Fecha recepción mercancía - NME80FN",

    # Nombres antiguos, por compatibilidad con archivos anteriores.
    "Fecha de solicitud",
    "Fe.liber.Z",
    "Fecha de pedido",
    "Fecha de entrega",
    "ariba_fecha_solicitud_compra",
    "ariba_fecha_aprobacion",
    "nme_fecha_entrada",
    "nme_fecha_documento",
    "nme_fecha_contabiliz",
    "nme_fecha_facturacion_proveedor",
    "nme_fecha_entrada_mercancia_recepcion",
]

COLUMNAS_NUEVAS_ORDENADAS = [
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
    "rango_incumplimiento",
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
    if separador_csv in ["Punto y coma (;)", "Punto y coma (;):"]:
        return ";"
    if separador_csv in ["Coma (,)", "Coma (,):", "Coma (, )"]:
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
        col for col in COLUMNAS_REQUERIDAS_PERFORMANCE
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas requeridas para calcular performance: "
            f"{faltantes}"
        )


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


def bool_array(condicion) -> np.ndarray:
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


def diferencia_dias(fecha_fin: pd.Series, fecha_inicio: pd.Series) -> pd.Series:
    return (fecha_fin - fecha_inicio).dt.days


def evaluar_cumplimiento(valor: pd.Series, umbral: pd.Series) -> pd.Series:
    resultado = valor <= umbral
    resultado = resultado.mask(valor.isna() | umbral.isna(), pd.NA)
    return resultado


def dias_incumplimiento(valor: pd.Series, umbral: pd.Series) -> pd.Series:
    resultado = valor - umbral
    resultado = resultado.where(resultado > 0, 0)
    resultado = resultado.mask(valor.isna() | umbral.isna(), np.nan)
    return resultado


def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    return str(valor)


# =========================================================
# Lógica principal de performance
# =========================================================

@st.cache_data(show_spinner=False)
def aplicar_logica_performance(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    validar_columnas_requeridas(df)

    for col in COLUMNAS_FECHA_PERFORMANCE:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    # =====================================================
    # Tipo de OC
    # 35 = Ariba / Nacional
    # 45 = ERP / Nacional
    # 47 = ERP / Internacional
    # =====================================================

    if COL_PEDIDO in df.columns:
        df["tipo_oc"] = df[COL_PEDIDO].apply(extraer_tipo_oc)
    elif COL_DOCUMENTO_COMPRAS in df.columns:
        df["tipo_oc"] = df[COL_DOCUMENTO_COMPRAS].apply(extraer_tipo_oc)
    else:
        df["tipo_oc"] = pd.NA

    df["tipo_oc"] = df["tipo_oc"].astype("string")

    df["origen_oc"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47")),
        ],
        [
            "Nacional",
            "Internacional",
        ],
        default="Otro"
    )

    df["sistema_oc"] = np.select(
        [
            bool_array(df["tipo_oc"].eq("35")),
            bool_array(df["tipo_oc"].isin(["45", "47"])),
        ],
        [
            "Ariba",
            "ERP",
        ],
        default="Otro"
    )

    if COL_TIPO_COMPRA_ARIBA in df.columns:
        tipo_compra_num = pd.to_numeric(df[COL_TIPO_COMPRA_ARIBA], errors="coerce")
    else:
        tipo_compra_num = pd.Series(np.nan, index=df.index)

    df["nombre_tipo_compra"] = np.select(
        [
            bool_array(tipo_compra_num.eq(1)),
            bool_array(tipo_compra_num.eq(2)),
            bool_array(tipo_compra_num.eq(3)),
        ],
        [
            "Catalogada",
            "No catalogada",
            "Directa",
        ],
        default="Otro"
    )

    if COL_CANTIDAD_SOLICITADA in df.columns and COL_PRECIO_VALORACION in df.columns:
        df["monto_valoracion"] = (
            pd.to_numeric(df[COL_CANTIDAD_SOLICITADA], errors="coerce")
            * pd.to_numeric(df[COL_PRECIO_VALORACION], errors="coerce")
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
        COL_FECHA_PEDIDO_FINAL
    ]

    df.loc[mask_oc_45_47, "fecha_inicio_proveedor"] = (
        df.loc[mask_oc_45_47, COL_FECHA_PEDIDO_FINAL]
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
        df[COL_FECHA_LIBERACION_FINAL],
        df[COL_FECHA_SOLICITUD_FINAL]
    )

    df["dx_comprador_1"] = diferencia_dias(
        df[COL_FECHA_PEDIDO_FINAL],
        df[COL_FECHA_LIBERACION_FINAL]
    )

    df["dx_lib_pedido"] = np.nan

    df["dx_logistica"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df[COL_FECHA_FACTURACION_FINAL]
    )

    df["dx_proveedor"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df["fecha_inicio_proveedor"]
    )

    df["dx_tat"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df[COL_FECHA_SOLICITUD_FINAL]
    )

    # =====================================================
    # Umbrales
    # =====================================================

    df["umbral_lib_solped"] = 2
    df["umbral_comprador_1"] = 10
    df["umbral_lib_pedido"] = 2
    df["umbral_logistica"] = 11

    df["umbral_tat"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47")),
        ],
        [
            40,
            70,
        ],
        default=np.nan
    )

    df["umbral_proveedor"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47")),
        ],
        [
            20,
            60,
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

    columnas_incumplimiento = [
        "dias_incumplimiento_lib_solped",
        "dias_incumplimiento_comprador_1",
        "dias_incumplimiento_logistica",
        "dias_incumplimiento_tat",
        "dias_incumplimiento_proveedor",
    ]

    df["dias_incumplimiento_max"] = df[columnas_incumplimiento].max(
        axis=1,
        skipna=True
    )

    df["dias_incumplimiento_max"] = df["dias_incumplimiento_max"].fillna(0)
    df["incumplimiento"] = df["dias_incumplimiento_max"].gt(0)

    df["rango_incumplimiento"] = np.select(
        [
            bool_array(df["dias_incumplimiento_max"].eq(0)),
            bool_array(df["dias_incumplimiento_max"].between(1, 5, inclusive="both")),
            bool_array(df["dias_incumplimiento_max"].between(6, 15, inclusive="both")),
            bool_array(df["dias_incumplimiento_max"].between(16, 30, inclusive="both")),
            bool_array(df["dias_incumplimiento_max"].gt(30)),
        ],
        [
            "Sin incumplimiento",
            "0-5 días",
            "6-15 días",
            "16-30 días",
            "Mayor a un mes",
        ],
        default="Sin información"
    )

    return df


def reordenar_columnas_performance_al_final(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    columnas_finales = [
        col for col in COLUMNAS_NUEVAS_ORDENADAS
        if col in df.columns
    ]

    columnas_base = [
        col for col in df.columns
        if col not in columnas_finales
    ]

    return df[columnas_base + columnas_finales].copy()


# =========================================================
# Resúmenes y lógica explicativa
# =========================================================

def resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        "performance_lib_solped",
        "performance_comprador_1",
        "performance_lib_pedido",
        "performance_logistica",
        "performance_tat",
        "performance_proveedor",
    ]

    data = []

    for col in metricas:
        if col not in df.columns:
            continue

        serie = df[col]
        total_con_info = int(serie.notna().sum())
        cumple = int(serie.eq(True).sum())
        no_cumple = int(serie.eq(False).sum())
        sin_info = int(serie.isna().sum())
        porcentaje_cumple = round((cumple / total_con_info) * 100, 2) if total_con_info else 0

        data.append({
            "Métrica": col,
            "Cumple": cumple,
            "No cumple": no_cumple,
            "Sin información": sin_info,
            "% Cumple": porcentaje_cumple,
        })

    return pd.DataFrame(data)


def resumen_columnas_nuevas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        col for col in COLUMNAS_NUEVAS_ORDENADAS
        if col in df.columns
    ]

    return pd.DataFrame({
        "Columna nueva": columnas,
        "Nulos": [int(df[col].isna().sum()) for col in columnas],
        "% Nulos": [round(df[col].isna().mean() * 100, 2) for col in columnas],
        "Tipo dato": [str(df[col].dtype) for col in columnas],
    })


def generar_resumen_cambios_performance(
    df_original: pd.DataFrame,
    df_final: pd.DataFrame,
    columnas_originales: list,
    columnas_nuevas: list
) -> dict:
    total = int(len(df_final))

    conteo_tipo_oc = (
        df_final["tipo_oc"]
        .value_counts(dropna=False)
        .to_dict()
        if "tipo_oc" in df_final.columns
        else {}
    )

    incumplimientos = (
        int(df_final["incumplimiento"].eq(True).sum())
        if "incumplimiento" in df_final.columns
        else 0
    )

    ejemplo = None
    if not df_final.empty:
        candidatos = df_final[df_final.get("incumplimiento", False) == True].copy()
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
        "conteo_tipo_oc": conteo_tipo_oc,
        "incumplimientos": incumplimientos,
        "sin_incumplimiento": int(total - incumplimientos),
        "ejemplo": ejemplo,
    }


def generar_tabla_ejemplo_performance(ejemplo: dict) -> pd.DataFrame:
    if not ejemplo:
        return pd.DataFrame(
            columns=[
                "Cálculo",
                "Fecha / valor inicial",
                "Fecha / valor final",
                "Resultado",
                "Umbral",
                "Cumple",
            ]
        )

    return pd.DataFrame([
        {
            "Cálculo": "Liberación vs solicitud",
            "Fecha / valor inicial": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_FINAL)),
            "Fecha / valor final": formatear_valor(ejemplo.get(COL_FECHA_LIBERACION_FINAL)),
            "Resultado": formatear_valor(ejemplo.get("dx_lib_solped")),
            "Umbral": formatear_valor(ejemplo.get("umbral_lib_solped")),
            "Cumple": formatear_valor(ejemplo.get("performance_lib_solped")),
        },
        {
            "Cálculo": "Comprador 1",
            "Fecha / valor inicial": formatear_valor(ejemplo.get(COL_FECHA_LIBERACION_FINAL)),
            "Fecha / valor final": formatear_valor(ejemplo.get(COL_FECHA_PEDIDO_FINAL)),
            "Resultado": formatear_valor(ejemplo.get("dx_comprador_1")),
            "Umbral": formatear_valor(ejemplo.get("umbral_comprador_1")),
            "Cumple": formatear_valor(ejemplo.get("performance_comprador_1")),
        },
        {
            "Cálculo": "Logística",
            "Fecha / valor inicial": formatear_valor(ejemplo.get(COL_FECHA_FACTURACION_FINAL)),
            "Fecha / valor final": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_FINAL)),
            "Resultado": formatear_valor(ejemplo.get("dx_logistica")),
            "Umbral": formatear_valor(ejemplo.get("umbral_logistica")),
            "Cumple": formatear_valor(ejemplo.get("performance_logistica")),
        },
        {
            "Cálculo": "Proveedor",
            "Fecha / valor inicial": formatear_valor(ejemplo.get("fecha_inicio_proveedor")),
            "Fecha / valor final": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_FINAL)),
            "Resultado": formatear_valor(ejemplo.get("dx_proveedor")),
            "Umbral": formatear_valor(ejemplo.get("umbral_proveedor")),
            "Cumple": formatear_valor(ejemplo.get("performance_proveedor")),
        },
        {
            "Cálculo": "TAT total",
            "Fecha / valor inicial": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_FINAL)),
            "Fecha / valor final": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_FINAL)),
            "Resultado": formatear_valor(ejemplo.get("dx_tat")),
            "Umbral": formatear_valor(ejemplo.get("umbral_tat")),
            "Cumple": formatear_valor(ejemplo.get("performance_tat")),
        },
    ])


def mostrar_resumen_cambios_performance(resumen_cambios: dict, resumen_cols: pd.DataFrame):
    with st.expander("Cambios realizados y lógica de performance", expanded=True):
        conteo_tipo_oc = resumen_cambios.get("conteo_tipo_oc", {})
        texto_tipo_oc = "\n".join(
            [f"- **{tipo}**: {cantidad:,} registros" for tipo, cantidad in conteo_tipo_oc.items()]
        )

        if not texto_tipo_oc:
            texto_tipo_oc = "- No se pudo generar conteo por tipo de OC."

        st.markdown("### 1. Resumen del archivo procesado")

        st.info(
            f"""
            - Se cargaron **{resumen_cambios['total_original']:,} registros**.
            - El resultado final conserva **{resumen_cambios['total_final']:,} registros**.
            - Se conservaron las columnas originales.
            - Se agregaron **{resumen_cambios['columnas_nuevas']:,} columnas nuevas**.
            - Filas duplicadas detectadas en la salida final: **{resumen_cambios['duplicados_final']:,}**.
            """
        )

        st.markdown("### 2. Columnas agregadas")
        st.caption(
            "Esta tabla muestra todas las columnas nuevas creadas por la lógica de performance, "
            "junto con su cantidad de nulos, porcentaje de nulos y tipo de dato."
        )

        st.dataframe(
            resumen_cols,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 3. Lógica de clasificación de OC")

        st.markdown(
            f"""
            La clasificación se realiza tomando los **dos primeros dígitos** del pedido/documento.
            Primero se intenta usar `{COL_PEDIDO}`. Si esa columna no existe, se usa
            `{COL_DOCUMENTO_COMPRAS}`.

            | Columna agregada | Fórmula teórica | Lógica usada en el código |
            |---|---|---|
            | `tipo_oc` | Tipo de orden de compra según los 2 primeros dígitos del pedido/documento | `extraer_tipo_oc({COL_PEDIDO})`; si no existe `{COL_PEDIDO}`, usa `extraer_tipo_oc({COL_DOCUMENTO_COMPRAS})` |
            | `origen_oc` | Clasifica la OC como nacional o internacional | `35` y `45` = `Nacional`; `47` = `Internacional`; otros = `Otro` |
            | `sistema_oc` | Clasifica el sistema origen de la OC | `35` = `Ariba`; `45` y `47` = `ERP`; otros = `Otro` |
            | `nombre_tipo_compra` | Traduce el código de tipo de compra ARIBA a nombre de negocio | `{COL_TIPO_COMPRA_ARIBA}`: `1` = `Catalogada`; `2` = `No catalogada`; `3` = `Directa`; otros = `Otro` |
            | `monto_valoracion` | Valor estimado de la línea | `{COL_CANTIDAD_SOLICITADA} * {COL_PRECIO_VALORACION}` |
            """
        )

        st.markdown("### 4. Lógica de fecha inicio proveedor")

        st.markdown(
            """
            La fecha de inicio del proveedor se calcula según el tipo de OC.

            | Tipo OC | Fórmula teórica | Lógica usada en el código |
            |---|---|---|
            | `35` | El proveedor empieza desde la fecha de pedido | `fecha_inicio_proveedor = fecha_pedido_final` |
            | `45` / `47` | El proveedor empieza 3 días después de la fecha de pedido | `fecha_inicio_proveedor = fecha_pedido_final + 3 días` |
            | Otro / sin dato | No se puede determinar fecha de inicio proveedor | `fecha_inicio_proveedor = NaT` |
            """
        )

        st.markdown("### 5. Fórmulas de días calculados")

        st.markdown(
            """
            Las columnas `dx_*` calculan días calendario entre dos hitos. La operación usada es
            `fecha_final - fecha_inicial` y se toma el resultado en días.

            | Columna agregada | Fórmula teórica | Fórmula usada en el código |
            |---|---|---|
            | `dx_lib_solped` | Días entre liberación de SolPed y solicitud de SolPed | `fecha_liberacion_final - fecha_solicitud_final` |
            | `dx_comprador_1` | Días entre creación/emisión del pedido y liberación de SolPed | `fecha_pedido_final - fecha_liberacion_final` |
            | `dx_lib_pedido` | Días entre liberación del pedido y creación/emisión del pedido | Actualmente queda sin cálculo: `NaN` |
            | `dx_logistica` | Días entre recepción final y facturación final | `fecha_recepcion_final - fecha_facturacion_final` |
            | `dx_proveedor` | Días entre recepción final e inicio del proveedor | `fecha_recepcion_final - fecha_inicio_proveedor` |
            | `dx_tat` | Días totales entre recepción final y solicitud inicial | `fecha_recepcion_final - fecha_solicitud_final` |
            """
        )

        st.markdown("### 6. Umbrales usados")

        st.markdown(
            """
            Los umbrales son la cantidad máxima de días permitida para considerar que una etapa cumple.

            | Columna agregada | Fórmula teórica | Valor / lógica usada en el código |
            |---|---|---|
            | `umbral_lib_solped` | Máximo permitido para liberar SolPed | `2` días |
            | `umbral_comprador_1` | Máximo permitido entre liberación de SolPed y pedido | `10` días |
            | `umbral_lib_pedido` | Máximo permitido para liberar pedido | `2` días |
            | `umbral_logistica` | Máximo permitido entre facturación y recepción | `11` días |
            | `umbral_tat` | Máximo permitido para el ciclo total TAT | OC `35` / `45` = `40` días; OC `47` = `70` días |
            | `umbral_proveedor` | Máximo permitido para el tramo proveedor | OC `35` / `45` = `20` días; OC `47` = `60` días |
            """
        )

        st.markdown("### 7. Fórmulas de performance")

        st.markdown(
            """
            Cada columna de performance evalúa si los días calculados están dentro del umbral.
            Si falta el valor de días o el umbral, el resultado queda sin información.

            ```text
            performance = días_calculados <= umbral
            ```

            | Columna agregada | Fórmula teórica | Comparación usada en el código |
            |---|---|---|
            | `performance_lib_solped` | Cumple si liberación de SolPed está dentro del umbral | `dx_lib_solped <= umbral_lib_solped` |
            | `performance_comprador_1` | Cumple si comprador 1 está dentro del umbral | `dx_comprador_1 <= umbral_comprador_1` |
            | `performance_lib_pedido` | Cumple si liberación de pedido está dentro del umbral | `dx_lib_pedido <= umbral_lib_pedido` |
            | `performance_logistica` | Cumple si logística está dentro del umbral | `dx_logistica <= umbral_logistica` |
            | `performance_tat` | Cumple si TAT total está dentro del umbral | `dx_tat <= umbral_tat` |
            | `performance_proveedor` | Cumple si proveedor está dentro del umbral | `dx_proveedor <= umbral_proveedor` |
            """
        )

        st.markdown("### 8. Fórmulas de incumplimiento")

        st.markdown(
            """
            Para cada etapa se calcula el exceso de días contra el umbral. Si el resultado es menor
            o igual a 0, se considera 0 porque no hay incumplimiento.

            ```text
            días_incumplimiento = max(días_calculados - umbral, 0)
            ```

            | Columna agregada | Fórmula teórica | Fórmula usada en el código |
            |---|---|---|
            | `dias_incumplimiento_lib_solped` | Exceso de días en liberación de SolPed | `max(dx_lib_solped - umbral_lib_solped, 0)` |
            | `dias_incumplimiento_comprador_1` | Exceso de días en comprador 1 | `max(dx_comprador_1 - umbral_comprador_1, 0)` |
            | `dias_incumplimiento_logistica` | Exceso de días en logística | `max(dx_logistica - umbral_logistica, 0)` |
            | `dias_incumplimiento_tat` | Exceso de días en TAT total | `max(dx_tat - umbral_tat, 0)` |
            | `dias_incumplimiento_proveedor` | Exceso de días en proveedor | `max(dx_proveedor - umbral_proveedor, 0)` |
            | `dias_incumplimiento_max` | Mayor incumplimiento detectado entre todas las etapas | `max()` entre las columnas de incumplimiento anteriores |
            | `incumplimiento` | Indica si existe algún incumplimiento | `True` si `dias_incumplimiento_max > 0`; si no, `False` |
            """
        )

        st.markdown("### 9. Rangos de incumplimiento")

        st.markdown(
            """
            | Condición teórica | Lógica usada en el código | Rango asignado |
            |---|---|---|
            | Sin exceso de días | `dias_incumplimiento_max = 0` | `Sin incumplimiento` |
            | Incumplimiento menor | `dias_incumplimiento_max` entre `1` y `5` | `0-5 días` |
            | Incumplimiento medio | `dias_incumplimiento_max` entre `6` y `15` | `6-15 días` |
            | Incumplimiento alto | `dias_incumplimiento_max` entre `16` y `30` | `16-30 días` |
            | Incumplimiento crítico | `dias_incumplimiento_max > 30` | `Mayor a un mes` |
            """
        )

        st.markdown("### 10. Resultado general de incumplimiento")

        st.info(
            f"""
            - Registros con incumplimiento: **{resumen_cambios['incumplimientos']:,}**.
            - Registros sin incumplimiento: **{resumen_cambios['sin_incumplimiento']:,}**.

            **Distribución por tipo de OC**

            {texto_tipo_oc}
            """
        )

        st.markdown("### 11. Ejemplo de cálculo de performance")

        tabla_ejemplo = generar_tabla_ejemplo_performance(resumen_cambios.get("ejemplo"))

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


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(
    df: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame
) -> bytes:
    return convertir_a_excel(df, resumen_perf, resumen_cols)


# =========================================================
# Interfaz
# =========================================================

mostrar_logo()

st.title("Performance TAT - Match Integrado")
st.caption("ME5A · ARIBA · NME80FN · Fechas finales")

with st.sidebar:
    st.header("Configuración")

    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación",
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

    ordenar_performance_final = st.checkbox(
        "Mover columnas de performance al final",
        value=True
    )

    st.caption("El separador solo aplica a archivos CSV.")


st.subheader("Archivo")

uploaded_file = st.file_uploader(
    "Selecciona archivo con fechas finales",
    type=["parquet", "xlsx", "csv"]
)

if uploaded_file is None:
    st.info("Carga el archivo con fechas finales para calcular performance TAT.")
    st.stop()

try:
    with st.spinner("Leyendo archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=uploaded_file.getvalue(),
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv
        )

    columnas_originales = list(df_original.columns)

    with st.spinner("Aplicando lógica de performance..."):
        df_final = aplicar_logica_performance(df_original)

        columnas_nuevas = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        if ordenar_performance_final:
            df_final = reordenar_columnas_performance_al_final(df_final)

        resumen_perf = resumen_performance(df_final)
        resumen_cols = resumen_columnas_nuevas(df_final)
        parquet_bytes = convertir_a_parquet_cache(df_final)

        resumen_cambios = generar_resumen_cambios_performance(
            df_original=df_original,
            df_final=df_final,
            columnas_originales=columnas_originales,
            columnas_nuevas=columnas_nuevas
        )

    st.success("Performance TAT calculada correctamente.")

    mostrar_resumen_cambios_performance(resumen_cambios, resumen_cols)

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

    st.subheader("Resumen de performance")

    st.dataframe(
        resumen_perf,
        use_container_width=True,
        hide_index=True
    )


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

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "tipo_oc",
        "origen_oc",
        "sistema_oc",
        "nombre_tipo_compra",
        COL_CANTIDAD_SOLICITADA,
        COL_PRECIO_VALORACION,
        "monto_valoracion",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_LIBERACION_FINAL,
        COL_FECHA_PEDIDO_FINAL,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
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
        "rango_incumplimiento",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col in df_final.columns
    ]

    if columnas_preferidas:
        st.caption(
            f"Mostrando hasta {int(limite_vista):,} registros de "
            f"{len(df_final):,} registros generados. "
            f"Columnas visibles preferidas: {len(columnas_preferidas):,}."
        )

        st.dataframe(
            df_final[columnas_preferidas].head(int(limite_vista)),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.dataframe(
            df_final.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("Ver columnas nuevas agregadas", expanded=False):
        st.dataframe(
            resumen_cols,
            use_container_width=True,
            hide_index=True
        )

    with st.expander("Top filas con mayor incumplimiento", expanded=False):
        if "dias_incumplimiento_max" in df_final.columns:
            columnas_top = [
                "Solicitud de pedido - ME5A",
                COL_PEDIDO,
                COL_DOCUMENTO_COMPRAS,
                "tipo_oc",
                "origen_oc",
                "sistema_oc",
                "dx_tat",
                "dx_proveedor",
                "dx_logistica",
                "dias_incumplimiento_max",
                "rango_incumplimiento",
                COL_FECHA_SOLICITUD_FINAL,
                COL_FECHA_RECEPCION_FINAL,
            ]

            columnas_top = [
                col for col in columnas_top
                if col in df_final.columns
            ]

            st.dataframe(
                df_final
                .sort_values("dias_incumplimiento_max", ascending=False)
                [columnas_top]
                .head(int(limite_vista)),
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
        file_name="match_integrado_me5a_ariba_nme80fn_performance.parquet",
        mime="application/octet-stream",
        use_container_width=True
    )

    st.caption(
        "Parquet es el formato principal recomendado para conservar tipos de datos. "
        "CSV y Excel se preparan solo si los solicitas."
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
                    file_name="match_integrado_me5a_ariba_nme80fn_performance.csv",
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
                            resumen_perf,
                            resumen_cols
                        )

                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name="match_integrado_me5a_ariba_nme80fn_performance.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

except Exception as e:
    st.error("No se pudo calcular la performance TAT.")
    st.exception(e)
