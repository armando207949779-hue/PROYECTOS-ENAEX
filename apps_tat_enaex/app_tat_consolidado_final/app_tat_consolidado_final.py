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

# Fechas finales usadas por el cálculo principal.
COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

# Columnas de origen reales del dataframe integrado.
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


# =========================================================
# Columnas nuevas ordenadas
# =========================================================

COLUMNAS_NUEVAS_ORDENADAS = [
    # Clasificación y datos base.
    "tipo_oc",
    "origen",
    "sistema",
    "nombre_tipo_compra",
    "monto",

    # Días calculados.
    "dias_liberacion_solped",
    "dias_comprador",
    "dias_liberacion_pedido",
    "dias_proveedor",
    "dias_logistica",
    "dias_tat_total",

    # Umbrales.
    "umbral_liberacion_solped",
    "umbral_comprador",
    "umbral_liberacion_pedido",
    "umbral_proveedor",
    "umbral_logistica",
    "umbral_tat_total",

    # Performance.
    "performance_liberacion_solped",
    "performance_comprador",
    "performance_liberacion_pedido",
    "performance_proveedor",
    "performance_logistica",
    "performance_tat_total",

    # Validación e incumplimiento.
    "tiene_fechas_inconsistentes",
    "dias_incumplimiento_tat",
    "incumplimiento_tat",
    "rango_incumplimiento_tat",
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
            "Faltan columnas requeridas para calcular performance TAT: "
            f"{faltantes}"
        )


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    """
    Convierte fechas que pueden venir como:
    - datetime
    - texto de fecha
    - timestamp numérico en milisegundos
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
    """
    Calcula días calendario entre dos fechas.
    Fórmula: fecha_fin - fecha_inicio.
    Si falta alguna fecha, el resultado queda vacío.
    """
    return (fecha_fin - fecha_inicio).dt.days


def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    return str(valor)


# =========================================================
# Evaluaciones de performance
# =========================================================

def evaluar_performance_basica(
    dias: pd.Series,
    umbral: pd.Series,
    texto_sin_dato: str = "No aplica",
    negativos_no_aplican: bool = False
) -> pd.Series:
    """
    Evalúa una métrica simple contra su umbral.

    Reglas:
    - Si no hay días o no hay umbral: texto_sin_dato.
    - Si hay días negativos y negativos_no_aplican=True: No aplica.
    - Si días <= umbral: Cumple.
    - Si días > umbral: No cumple.
    """
    resultado = pd.Series(texto_sin_dato, index=dias.index, dtype="object")

    mask_sin_dato = dias.isna() | umbral.isna()
    mask_negativo = dias.lt(0)

    if negativos_no_aplican:
        resultado.loc[mask_negativo] = "No aplica"

    mask_evaluable = ~mask_sin_dato

    if negativos_no_aplican:
        mask_evaluable = mask_evaluable & ~mask_negativo

    resultado.loc[mask_evaluable & dias.le(umbral)] = "Cumple"
    resultado.loc[mask_evaluable & dias.gt(umbral)] = "No cumple"

    return resultado


def evaluar_performance_tat(df: pd.DataFrame) -> pd.Series:
    """
    Evalúa el TAT total según tipo de OC.

    Reglas:
    - Si alguna etapa tiene días negativos: No aplica al análisis.
    - Si TAT total está vacío: En proceso.
    - OC 35 o 45 cumple si TAT <= 40.
    - OC 47 cumple si TAT <= 70.
    - Si es OC 35, 45 o 47 y supera el umbral: No cumple.
    - Otros tipos de OC: Sin datos.
    """
    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    mask_negativos = df["tiene_fechas_inconsistentes"].eq(True)
    mask_en_proceso = df["dias_tat_total"].isna()

    mask_tipo_nacional = df["tipo_oc"].isin(["35", "45"])
    mask_tipo_internacional = df["tipo_oc"].eq("47")
    mask_tipo_valido = df["tipo_oc"].isin(["35", "45", "47"])

    resultado.loc[mask_negativos] = "No aplica al análisis"
    resultado.loc[~mask_negativos & mask_en_proceso] = "En proceso"

    mask_evaluable = ~mask_negativos & ~mask_en_proceso

    resultado.loc[
        mask_evaluable & mask_tipo_nacional & df["dias_tat_total"].le(40)
    ] = "Cumple"

    resultado.loc[
        mask_evaluable & mask_tipo_internacional & df["dias_tat_total"].le(70)
    ] = "Cumple"

    resultado.loc[
        mask_evaluable
        & mask_tipo_valido
        & (
            (mask_tipo_nacional & df["dias_tat_total"].gt(40))
            | (mask_tipo_internacional & df["dias_tat_total"].gt(70))
        )
    ] = "No cumple"

    return resultado


def calcular_dias_incumplimiento_tat(
    dias_tat: pd.Series,
    umbral_tat: pd.Series
) -> pd.Series:
    """
    Calcula días de incumplimiento solo contra el TAT total.

    Reglas:
    - Si no hay TAT o no hay umbral, queda vacío.
    - Si TAT no supera el umbral, queda 0.
    - Si TAT supera el umbral, queda TAT - umbral.
    """
    diferencia = dias_tat - umbral_tat
    resultado = diferencia.where(diferencia > 0, 0)
    resultado = resultado.mask(dias_tat.isna() | umbral_tat.isna(), np.nan)
    return resultado


def calcular_rango_incumplimiento_tat(dias_incumplimiento: pd.Series) -> pd.Series:
    """
    Clasifica los días de incumplimiento TAT.
    """
    return pd.Series(
        np.select(
            [
                bool_array(dias_incumplimiento.isna()),
                bool_array(dias_incumplimiento.eq(0)),
                bool_array(dias_incumplimiento.between(1, 5, inclusive="both")),
                bool_array(dias_incumplimiento.between(6, 15, inclusive="both")),
                bool_array(dias_incumplimiento.between(16, 30, inclusive="both")),
                bool_array(dias_incumplimiento.gt(30)),
            ],
            [
                "Sin datos",
                "Sin incumplimiento",
                "0-5 días",
                "6-15 días",
                "16-30 días",
                "Mayor a un mes",
            ],
            default="Sin datos"
        ),
        index=dias_incumplimiento.index
    )


# =========================================================
# Tabla conceptual de fórmulas
# =========================================================

def tabla_inputs_formulas() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Métrica": "Liberación SolPed",
            "Nombre técnico": "dias_liberacion_solped",
            "Fecha inicio": COL_FECHA_SOLICITUD_FINAL,
            "Fecha fin": COL_FECHA_LIBERACION_FINAL,
            "Fórmula": "fecha_liberacion_final - fecha_solicitud_final",
            "Descripción": "Mide los días calendario entre la solicitud y la liberación de la SolPed.",
            "Umbral": "2 días",
            "Resultado esperado": "Cumple si los días son menores o iguales a 2.",
        },
        {
            "Métrica": "Comprador",
            "Nombre técnico": "dias_comprador",
            "Fecha inicio": COL_FECHA_LIBERACION_FINAL,
            "Fecha fin": COL_FECHA_PEDIDO_FINAL,
            "Fórmula": "fecha_pedido_final - fecha_liberacion_final",
            "Descripción": "Mide los días calendario entre la liberación de la SolPed y la creación/emisión del pedido.",
            "Umbral": "10 días",
            "Resultado esperado": "Cumple si los días son menores o iguales a 10.",
        },
        {
            "Métrica": "Liberación Pedido",
            "Nombre técnico": "dias_liberacion_pedido",
            "Fecha inicio": "Sin input disponible",
            "Fecha fin": "Sin input disponible",
            "Fórmula": "Sin cálculo",
            "Descripción": "No se calcula porque actualmente no existe la información necesaria.",
            "Umbral": "2 días",
            "Resultado esperado": "Sin datos.",
        },
        {
            "Métrica": "Proveedor",
            "Nombre técnico": "dias_proveedor",
            "Fecha inicio": COL_FECHA_PEDIDO_FINAL,
            "Fecha fin": COL_FECHA_FACTURACION_FINAL,
            "Fórmula": "fecha_facturacion_final - fecha_pedido_final",
            "Descripción": "Mide los días calendario entre la fecha de pedido y la fecha de facturación.",
            "Umbral": "OC 35/45 = 20 días; OC 47 = 60 días",
            "Resultado esperado": "Cumple si está dentro del umbral correspondiente al tipo de OC.",
        },
        {
            "Métrica": "Logística",
            "Nombre técnico": "dias_logistica",
            "Fecha inicio": COL_FECHA_FACTURACION_FINAL,
            "Fecha fin": COL_FECHA_RECEPCION_FINAL,
            "Fórmula": "fecha_recepcion_final - fecha_facturacion_final",
            "Descripción": "Mide los días calendario entre la facturación y la recepción de mercancía.",
            "Umbral": "11 días",
            "Resultado esperado": "Cumple si los días son menores o iguales a 11. Si el valor es negativo, no aplica.",
        },
        {
            "Métrica": "TAT Total",
            "Nombre técnico": "dias_tat_total",
            "Fecha inicio": COL_FECHA_SOLICITUD_FINAL,
            "Fecha fin": COL_FECHA_RECEPCION_FINAL,
            "Fórmula": "fecha_recepcion_final - fecha_solicitud_final",
            "Descripción": "Mide el ciclo completo punta a punta, desde la solicitud hasta la recepción.",
            "Umbral": "OC 35/45 = 40 días; OC 47 = 70 días",
            "Resultado esperado": "Cumple si está dentro del umbral correspondiente al tipo de OC.",
        },
    ])


# =========================================================
# Lógica principal de performance
# =========================================================

@st.cache_data(show_spinner=False)
def aplicar_logica_performance(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    validar_columnas_requeridas(df)

    # Convertir columnas de fecha.
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

    df["origen"] = np.select(
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

    df["sistema"] = np.select(
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

    # Tipo de compra ARIBA.
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

    # Monto.
    if COL_CANTIDAD_SOLICITADA in df.columns and COL_PRECIO_VALORACION in df.columns:
        df["monto"] = (
            pd.to_numeric(df[COL_CANTIDAD_SOLICITADA], errors="coerce")
            * pd.to_numeric(df[COL_PRECIO_VALORACION], errors="coerce")
        )
    else:
        df["monto"] = np.nan

    # =====================================================
    # Cálculos de días
    # =====================================================

    df["dias_liberacion_solped"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_LIBERACION_FINAL],
        fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL]
    )

    df["dias_comprador"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_PEDIDO_FINAL],
        fecha_inicio=df[COL_FECHA_LIBERACION_FINAL]
    )

    # No se calcula porque no hay inputs disponibles.
    df["dias_liberacion_pedido"] = np.nan

    df["dias_proveedor"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_FACTURACION_FINAL],
        fecha_inicio=df[COL_FECHA_PEDIDO_FINAL]
    )

    df["dias_logistica"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
        fecha_inicio=df[COL_FECHA_FACTURACION_FINAL]
    )

    df["dias_tat_total"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
        fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL]
    )

    # =====================================================
    # Umbrales
    # =====================================================

    df["umbral_liberacion_solped"] = 2
    df["umbral_comprador"] = 10
    df["umbral_liberacion_pedido"] = 2
    df["umbral_logistica"] = 11

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

    df["umbral_tat_total"] = np.select(
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

    df["umbral_proveedor"] = pd.to_numeric(
        df["umbral_proveedor"],
        errors="coerce"
    )

    df["umbral_tat_total"] = pd.to_numeric(
        df["umbral_tat_total"],
        errors="coerce"
    )

    # =====================================================
    # Validación de fechas inconsistentes
    # =====================================================

    columnas_dias_evaluables = [
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_liberacion_pedido",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
    ]

    df["tiene_fechas_inconsistentes"] = (
        df[columnas_dias_evaluables]
        .lt(0)
        .any(axis=1, skipna=True)
    )

    # =====================================================
    # Performance
    # =====================================================

    df["performance_liberacion_solped"] = evaluar_performance_basica(
        dias=df["dias_liberacion_solped"],
        umbral=pd.Series(df["umbral_liberacion_solped"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=False
    )

    df["performance_comprador"] = evaluar_performance_basica(
        dias=df["dias_comprador"],
        umbral=pd.Series(df["umbral_comprador"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=False
    )

    df["performance_liberacion_pedido"] = evaluar_performance_basica(
        dias=pd.Series(df["dias_liberacion_pedido"], index=df.index),
        umbral=pd.Series(df["umbral_liberacion_pedido"], index=df.index),
        texto_sin_dato="Sin datos",
        negativos_no_aplican=False
    )

    df["performance_proveedor"] = evaluar_performance_basica(
        dias=df["dias_proveedor"],
        umbral=df["umbral_proveedor"],
        texto_sin_dato="Sin datos",
        negativos_no_aplican=False
    )

    df["performance_logistica"] = evaluar_performance_basica(
        dias=df["dias_logistica"],
        umbral=pd.Series(df["umbral_logistica"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=True
    )

    df["performance_tat_total"] = evaluar_performance_tat(df)

    # =====================================================
    # Incumplimiento TAT
    # =====================================================

    df["dias_incumplimiento_tat"] = calcular_dias_incumplimiento_tat(
        dias_tat=df["dias_tat_total"],
        umbral_tat=df["umbral_tat_total"]
    )

    df["incumplimiento_tat"] = df["dias_incumplimiento_tat"].gt(0)

    df["rango_incumplimiento_tat"] = calcular_rango_incumplimiento_tat(
        df["dias_incumplimiento_tat"]
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
# Resúmenes
# =========================================================

def resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        {
            "columna": "performance_liberacion_solped",
            "metrica": "Liberación SolPed",
            "descripcion": "Tiempo entre solicitud y liberación de la SolPed.",
        },
        {
            "columna": "performance_comprador",
            "metrica": "Comprador",
            "descripcion": "Tiempo entre liberación de SolPed y creación/emisión del pedido.",
        },
        {
            "columna": "performance_liberacion_pedido",
            "metrica": "Liberación Pedido",
            "descripcion": "No se calcula actualmente porque no hay inputs disponibles.",
        },
        {
            "columna": "performance_proveedor",
            "metrica": "Proveedor",
            "descripcion": "Tiempo entre pedido y facturación.",
        },
        {
            "columna": "performance_logistica",
            "metrica": "Logística",
            "descripcion": "Tiempo entre facturación y recepción de mercancía.",
        },
        {
            "columna": "performance_tat_total",
            "metrica": "TAT Total",
            "descripcion": "Tiempo punta a punta desde solicitud hasta recepción.",
        },
    ]

    data = []

    for item in metricas:
        col = item["columna"]

        if col not in df.columns:
            continue

        serie = df[col].astype("object")

        cumple = int(serie.eq("Cumple").sum())
        no_cumple = int(serie.eq("No cumple").sum())
        no_aplica = int(serie.isin(["No aplica", "No aplica al análisis"]).sum())
        sin_datos = int(serie.isin(["Sin datos", "En proceso"]).sum())

        total_evaluable = cumple + no_cumple
        porcentaje_cumple = round((cumple / total_evaluable) * 100, 2) if total_evaluable else 0

        data.append({
            "Métrica": item["metrica"],
            "Descripción": item["descripcion"],
            "Cumple": cumple,
            "No cumple": no_cumple,
            "No aplica": no_aplica,
            "Sin datos / En proceso": sin_datos,
            "% Cumple sobre evaluables": porcentaje_cumple,
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

    incumplimientos_tat = (
        int(df_final["incumplimiento_tat"].eq(True).sum())
        if "incumplimiento_tat" in df_final.columns
        else 0
    )

    ejemplo = None
    if not df_final.empty:
        candidatos = df_final[df_final.get("incumplimiento_tat", False) == True].copy()
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
        "incumplimientos_tat": incumplimientos_tat,
        "sin_incumplimiento_tat": int(total - incumplimientos_tat),
        "ejemplo": ejemplo,
    }


def generar_tabla_ejemplo_performance(ejemplo: dict) -> pd.DataFrame:
    if not ejemplo:
        return pd.DataFrame(
            columns=[
                "Métrica",
                "Fecha inicio",
                "Fecha fin",
                "Días calculados",
                "Umbral",
                "Performance",
            ]
        )

    return pd.DataFrame([
        {
            "Métrica": "Liberación SolPed",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_LIBERACION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_liberacion_solped")),
            "Umbral": formatear_valor(ejemplo.get("umbral_liberacion_solped")),
            "Performance": formatear_valor(ejemplo.get("performance_liberacion_solped")),
        },
        {
            "Métrica": "Comprador",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_LIBERACION_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_PEDIDO_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_comprador")),
            "Umbral": formatear_valor(ejemplo.get("umbral_comprador")),
            "Performance": formatear_valor(ejemplo.get("performance_comprador")),
        },
        {
            "Métrica": "Liberación Pedido",
            "Fecha inicio": "Sin input",
            "Fecha fin": "Sin input",
            "Días calculados": formatear_valor(ejemplo.get("dias_liberacion_pedido")),
            "Umbral": formatear_valor(ejemplo.get("umbral_liberacion_pedido")),
            "Performance": formatear_valor(ejemplo.get("performance_liberacion_pedido")),
        },
        {
            "Métrica": "Proveedor",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_PEDIDO_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_FACTURACION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_proveedor")),
            "Umbral": formatear_valor(ejemplo.get("umbral_proveedor")),
            "Performance": formatear_valor(ejemplo.get("performance_proveedor")),
        },
        {
            "Métrica": "Logística",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_FACTURACION_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_logistica")),
            "Umbral": formatear_valor(ejemplo.get("umbral_logistica")),
            "Performance": formatear_valor(ejemplo.get("performance_logistica")),
        },
        {
            "Métrica": "TAT Total",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_tat_total")),
            "Umbral": formatear_valor(ejemplo.get("umbral_tat_total")),
            "Performance": formatear_valor(ejemplo.get("performance_tat_total")),
        },
    ])


def mostrar_resumen_cambios_performance(
    resumen_cambios: dict,
    resumen_cols: pd.DataFrame
):
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

        st.markdown("### 2. Inputs utilizados por cada métrica")

        st.caption(
            "Esta tabla permite auditar qué fechas usa cada indicador, cuál es su fórmula y cuál es el umbral aplicado."
        )

        st.dataframe(
            tabla_inputs_formulas(),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 3. Columnas agregadas")

        st.caption(
            "Esta tabla muestra las columnas nuevas creadas por la lógica de performance, "
            "incluyendo cantidad de nulos, porcentaje de nulos y tipo de dato."
        )

        st.dataframe(
            resumen_cols,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 4. Clasificación de OC")

        st.markdown(
            f"""
            La clasificación se realiza tomando los **dos primeros dígitos** del pedido/documento.

            Primero se intenta usar `{COL_PEDIDO}`.  
            Si esa columna no existe, se usa `{COL_DOCUMENTO_COMPRAS}`.

            | Columna | Lógica |
            |---|---|
            | `tipo_oc` | Dos primeros dígitos del pedido/documento |
            | `origen` | `35` y `45` = Nacional; `47` = Internacional; otros = Otro |
            | `sistema` | `35` = Ariba; `45` y `47` = ERP; otros = Otro |
            | `nombre_tipo_compra` | `1` = Catalogada; `2` = No catalogada; `3` = Directa; otros = Otro |
            | `monto` | Cantidad solicitada multiplicada por precio de valoración |
            """
        )

        st.markdown("### 5. Fórmulas de días calculados")

        st.markdown(
            f"""
            | Métrica | Columna generada | Fórmula aplicada |
            |---|---|---|
            | Liberación SolPed | `dias_liberacion_solped` | `{COL_FECHA_LIBERACION_FINAL} - {COL_FECHA_SOLICITUD_FINAL}` |
            | Comprador | `dias_comprador` | `{COL_FECHA_PEDIDO_FINAL} - {COL_FECHA_LIBERACION_FINAL}` |
            | Liberación Pedido | `dias_liberacion_pedido` | Sin cálculo porque no hay input disponible |
            | Proveedor | `dias_proveedor` | `{COL_FECHA_FACTURACION_FINAL} - {COL_FECHA_PEDIDO_FINAL}` |
            | Logística | `dias_logistica` | `{COL_FECHA_RECEPCION_FINAL} - {COL_FECHA_FACTURACION_FINAL}` |
            | TAT Total | `dias_tat_total` | `{COL_FECHA_RECEPCION_FINAL} - {COL_FECHA_SOLICITUD_FINAL}` |
            """
        )

        st.markdown("### 6. Umbrales aplicados")

        st.markdown(
            """
            | Métrica | Umbral |
            |---|---|
            | Liberación SolPed | 2 días |
            | Comprador | 10 días |
            | Liberación Pedido | 2 días, aunque queda sin datos por falta de input |
            | Proveedor | OC 35/45 = 20 días; OC 47 = 60 días |
            | Logística | 11 días |
            | TAT Total | OC 35/45 = 40 días; OC 47 = 70 días |
            """
        )

        st.markdown("### 7. Reglas de performance")

        st.markdown(
            """
            | Resultado | Significado |
            |---|---|
            | `Cumple` | La métrica tiene datos y está dentro del umbral |
            | `No cumple` | La métrica tiene datos y supera el umbral |
            | `No aplica` | No hay datos suficientes o el cálculo no es válido para esa métrica |
            | `Sin datos` | No existe input suficiente para calcular la métrica |
            | `En proceso` | El TAT Total aún no tiene fecha de recepción |
            | `No aplica al análisis` | Existe alguna fecha inconsistente que genera días negativos |
            """
        )

        st.markdown("### 8. Incumplimiento TAT")

        st.markdown(
            """
            El incumplimiento oficial se calcula usando únicamente el **TAT Total**.

            ```text
            dias_incumplimiento_tat = max(dias_tat_total - umbral_tat_total, 0)
            ```

            | Condición | Rango |
            |---|---|
            | Sin dato suficiente | Sin datos |
            | 0 días de exceso | Sin incumplimiento |
            | 1 a 5 días de exceso | 0-5 días |
            | 6 a 15 días de exceso | 6-15 días |
            | 16 a 30 días de exceso | 16-30 días |
            | Más de 30 días de exceso | Mayor a un mes |
            """
        )

        st.markdown("### 9. Resultado general de incumplimiento TAT")

        st.info(
            f"""
            - Registros con incumplimiento TAT: **{resumen_cambios['incumplimientos_tat']:,}**.
            - Registros sin incumplimiento TAT: **{resumen_cambios['sin_incumplimiento_tat']:,}**.

            **Distribución por tipo de OC**

            {texto_tipo_oc}
            """
        )

        st.markdown("### 10. Ejemplo de cálculo de performance")

        tabla_ejemplo = generar_tabla_ejemplo_performance(
            resumen_cambios.get("ejemplo")
        )

        if tabla_ejemplo.empty:
            st.warning("
