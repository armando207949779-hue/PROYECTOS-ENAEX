# ============================================================
# 07_FILTRO
# Filtro, búsqueda y seguimiento de solicitudes de compra
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import base64
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st


# ============================================================
# Configuración de página
# ============================================================

st.set_page_config(
    page_title="07_FILTRO",
    page_icon="🔎",
    layout="wide",
)


# ============================================================
# Rutas
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilos
# IMPORTANTE:
# No se modifica .block-container para no afectar el logo.
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 14px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }

        div[data-testid="stFileUploader"] {
            padding: 10px;
            border-radius: 12px;
        }

        .app-header {
            text-align: center;
            margin-bottom: 1rem;
        }

        .app-title {
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 0;
        }

        .app-subtitle {
            color: #6c757d;
            font-size: 16px;
            margin-top: 4px;
        }

        .step-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
        }

        .small-muted {
            color: #6c757d;
            font-size: 14px;
        }

        .field-label {
            font-weight: 700;
            color: #495057;
            font-size: 13px;
            margin-bottom: 2px;
        }

        .field-value {
            color: #212529;
            font-size: 15px;
            margin-bottom: 10px;
            word-break: break-word;
        }

        .status-card {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 12px;
        }

        .timeline-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .timeline-item-done {
            flex: 1;
            min-width: 150px;
            background-color: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-radius: 14px;
            padding: 12px;
            text-align: center;
        }

        .timeline-item-pending {
            flex: 1;
            min-width: 150px;
            background-color: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 14px;
            padding: 12px;
            text-align: center;
        }

        .timeline-icon {
            font-size: 24px;
            margin-bottom: 4px;
        }

        .timeline-title {
            font-size: 14px;
            font-weight: 700;
            color: #212529;
            margin-bottom: 4px;
        }

        .timeline-date {
            font-size: 13px;
            color: #495057;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Logo
# ============================================================

def mostrar_logo():
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
                margin-top: 5px;
                margin-bottom: 10px;
            ">
                <img 
                    src="data:image/svg+xml;base64,{logo_base64}" 
                    style="width: 220px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# Funciones generales
# ============================================================

def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    return str(valor)


def formatear_fecha(valor) -> str:
    if pd.isna(valor):
        return "Sin fecha"

    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "Sin fecha"

    return fecha.strftime("%Y-%m-%d")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def normalizar_columnas_me80fn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compatibilidad con archivos antiguos que aún tengan NME80FN.
    """
    df = df.copy()

    renombrar = {
        col: col.replace("NME80FN", "ME80FN")
        for col in df.columns
        if "NME80FN" in col
    }

    df = df.rename(columns=renombrar)

    if "Estado del match" in df.columns:
        df["Estado del match"] = (
            df["Estado del match"]
            .astype("string")
            .str.replace("NME80FN", "ME80FN", regex=False)
        )

    return df


def buscar_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    for col in candidatos:
        if col in df.columns:
            return col

    return None


def normalizar_texto_serie(serie: pd.Series) -> pd.Series:
    return (
        serie
        .astype("string")
        .str.strip()
        .str.lower()
    )


def aplicar_filtro_texto(
    df: pd.DataFrame,
    columna: str | None,
    texto: str,
    modo: str = "Contiene",
) -> pd.DataFrame:

    if columna is None or columna not in df.columns:
        return df

    texto = str(texto).strip()

    if not texto:
        return df

    serie = normalizar_texto_serie(df[columna])
    texto_norm = texto.lower().strip()

    if modo == "Exacta":
        return df[serie.eq(texto_norm)].copy()

    return df[serie.str.contains(texto_norm, na=False, regex=False)].copy()


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


# ============================================================
# Detección de columnas
# ============================================================

def detectar_columnas_clave(df: pd.DataFrame) -> dict:
    return {
        "solped": buscar_columna(
            df,
            [
                "Solicitud de pedido - ME5A",
                "Solicitud de pedido",
                "Solicitud de compra ERP - ARIBA",
                "ariba_solicitud_compra_erp",
            ],
        ),
        "pedido": buscar_columna(
            df,
            [
                "Pedido - ME5A",
                "Pedido",
                "ID pedido - ARIBA",
                "ariba_id_pedido",
            ],
        ),
        "posicion": buscar_columna(
            df,
            [
                "Posición solicitud de pedido - ME5A",
                "Pos.solicitud pedido",
                "Posición de pedido - ME5A",
                "Posición de pedido",
                "Línea solicitud de compra - ARIBA",
            ],
        ),
        "material": buscar_columna(
            df,
            [
                "Material - ME5A",
                "Material",
                "Material - ME80FN",
            ],
        ),
        "texto_breve": buscar_columna(
            df,
            [
                "Texto breve - ME5A",
                "Texto breve",
                "Descripción - ARIBA",
                "Texto breve - ME80FN",
            ],
        ),
        "centro": buscar_columna(
            df,
            [
                "Centro - ME5A",
                "Centro",
                "Centro - ME80FN",
            ],
        ),
        "tipo_oc": buscar_columna(
            df,
            [
                "tipo_oc",
            ],
        ),
        "sistema": buscar_columna(
            df,
            [
                "sistema",
            ],
        ),
        "estado_match": buscar_columna(
            df,
            [
                "Estado del match",
                "estado_match",
            ],
        ),
        "fecha_solicitud": buscar_columna(
            df,
            [
                "fecha_solicitud_final",
                "Fecha de solicitud - ME5A",
                "Fecha de solicitud",
            ],
        ),
        "fecha_liberacion": buscar_columna(
            df,
            [
                "fecha_liberacion_final",
                "Fecha de liberación - ME5A",
                "Fecha de liberación",
            ],
        ),
        "fecha_pedido": buscar_columna(
            df,
            [
                "fecha_pedido_final",
                "Fecha de pedido - ME5A",
                "Fecha de pedido",
            ],
        ),
        "fecha_facturacion": buscar_columna(
            df,
            [
                "fecha_facturacion_final",
                "Fecha facturación proveedor - ME80FN",
            ],
        ),
        "fecha_recepcion": buscar_columna(
            df,
            [
                "fecha_recepcion_final",
                "Fecha recepción mercancía - ME80FN",
            ],
        ),
        "dias_tat_total": buscar_columna(
            df,
            [
                "dias_tat_total",
            ],
        ),
        "umbral_tat_total": buscar_columna(
            df,
            [
                "umbral_tat_total",
            ],
        ),
        "performance_tat_total": buscar_columna(
            df,
            [
                "performance_tat_total",
            ],
        ),
        "dias_incumplimiento": buscar_columna(
            df,
            [
                "dias_incumplimiento_tat",
            ],
        ),
        "rango_incumplimiento": buscar_columna(
            df,
            [
                "rango_incumplimiento_tat",
            ],
        ),
    }


def construir_columnas_vista(df: pd.DataFrame, columnas_clave: dict) -> list[str]:
    columnas = [
        columnas_clave["solped"],
        columnas_clave["pedido"],
        columnas_clave["posicion"],
        columnas_clave["material"],
        columnas_clave["texto_breve"],
        columnas_clave["centro"],
        columnas_clave["tipo_oc"],
        columnas_clave["sistema"],
        columnas_clave["estado_match"],
        columnas_clave["fecha_solicitud"],
        columnas_clave["fecha_liberacion"],
        columnas_clave["fecha_pedido"],
        columnas_clave["fecha_facturacion"],
        columnas_clave["fecha_recepcion"],
        columnas_clave["dias_tat_total"],
        columnas_clave["umbral_tat_total"],
        columnas_clave["performance_tat_total"],
        columnas_clave["dias_incumplimiento"],
        columnas_clave["rango_incumplimiento"],
    ]

    columnas = [
        col for col in columnas
        if col is not None and col in df.columns
    ]

    return list(dict.fromkeys(columnas))


# ============================================================
# Visualización de observación
# ============================================================

def mostrar_campo(label: str, valor):
    st.markdown(
        f"""
        <div class="field-label">{label}</div>
        <div class="field-value">{formatear_valor(valor)}</div>
        """,
        unsafe_allow_html=True,
    )


def obtener_valor(registro: pd.Series, columna: str | None):
    if columna is None:
        return ""

    if columna not in registro.index:
        return ""

    return registro.get(columna)


def mostrar_figura_estado_solped(registro: pd.Series, columnas_clave: dict):
    etapas = [
        {
            "etapa": "Solicitud",
            "fecha": obtener_valor(registro, columnas_clave["fecha_solicitud"]),
        },
        {
            "etapa": "Liberación",
            "fecha": obtener_valor(registro, columnas_clave["fecha_liberacion"]),
        },
        {
            "etapa": "Pedido",
            "fecha": obtener_valor(registro, columnas_clave["fecha_pedido"]),
        },
        {
            "etapa": "Facturación",
            "fecha": obtener_valor(registro, columnas_clave["fecha_facturacion"]),
        },
        {
            "etapa": "Recepción",
            "fecha": obtener_valor(registro, columnas_clave["fecha_recepcion"]),
        },
    ]

    html_items = ""

    for item in etapas:
        fecha = pd.to_datetime(item["fecha"], errors="coerce")
        realizado = pd.notna(fecha)

        clase = "timeline-item-done" if realizado else "timeline-item-pending"
        icono = "✅" if realizado else "❌"
        fecha_texto = formatear_fecha(item["fecha"])

        html_items += f"""
        <div class="{clase}">
            <div class="timeline-icon">{icono}</div>
            <div class="timeline-title">{item['etapa']}</div>
            <div class="timeline-date">{fecha_texto}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="status-card">
            <div style="font-weight:700; font-size:17px; margin-bottom:8px;">
                Estado de la SOLPED
            </div>
            <div class="timeline-wrap">
                {html_items}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def construir_tabla_etapas_tat(registro: pd.Series, columnas_clave: dict) -> pd.DataFrame:
    etapas = [
        {
            "Etapa": "Solicitud",
            "Fecha": obtener_valor(registro, columnas_clave["fecha_solicitud"]),
        },
        {
            "Etapa": "Liberación",
            "Fecha": obtener_valor(registro, columnas_clave["fecha_liberacion"]),
        },
        {
            "Etapa": "Pedido",
            "Fecha": obtener_valor(registro, columnas_clave["fecha_pedido"]),
        },
        {
            "Etapa": "Facturación",
            "Fecha": obtener_valor(registro, columnas_clave["fecha_facturacion"]),
        },
        {
            "Etapa": "Recepción",
            "Fecha": obtener_valor(registro, columnas_clave["fecha_recepcion"]),
        },
    ]

    registros = []

    for item in etapas:
        fecha = pd.to_datetime(item["Fecha"], errors="coerce")
        realizado = pd.notna(fecha)

        registros.append(
            {
                "Etapa": item["Etapa"],
                "Fecha TAT": formatear_fecha(item["Fecha"]),
                "Estado": "Realizado" if realizado else "Pendiente",
                "Marca": "✅" if realizado else "❌",
            }
        )

    return pd.DataFrame(registros)


def mostrar_detalle_observacion(registro: pd.Series, columnas_clave: dict):
    mostrar_figura_estado_solped(registro, columnas_clave)

    st.markdown("#### Datos principales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mostrar_campo("SOLPED", obtener_valor(registro, columnas_clave["solped"]))
        mostrar_campo("Pedido", obtener_valor(registro, columnas_clave["pedido"]))

    with col2:
        mostrar_campo("Posición", obtener_valor(registro, columnas_clave["posicion"]))
        mostrar_campo("Material", obtener_valor(registro, columnas_clave["material"]))

    with col3:
        mostrar_campo("Texto breve", obtener_valor(registro, columnas_clave["texto_breve"]))
        mostrar_campo("Centro", obtener_valor(registro, columnas_clave["centro"]))

    with col4:
        mostrar_campo("Tipo de OC", obtener_valor(registro, columnas_clave["tipo_oc"]))
        mostrar_campo("Sistema", obtener_valor(registro, columnas_clave["sistema"]))

    st.markdown("#### Fechas TAT")

    fechas_df = pd.DataFrame(
        [
            {
                "Fecha": "Fecha solicitud",
                "Valor": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_solicitud"])),
            },
            {
                "Fecha": "Fecha liberación",
                "Valor": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_liberacion"])),
            },
            {
                "Fecha": "Fecha pedido",
                "Valor": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_pedido"])),
            },
            {
                "Fecha": "Fecha facturación",
                "Valor": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_facturacion"])),
            },
            {
                "Fecha": "Fecha recepción",
                "Valor": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_recepcion"])),
            },
        ]
    )

    st.dataframe(
        fechas_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Indicadores TAT")

    col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)

    col_t1.metric(
        "Días TAT total",
        formatear_valor(obtener_valor(registro, columnas_clave["dias_tat_total"])),
    )

    col_t2.metric(
        "Umbral TAT total",
        formatear_valor(obtener_valor(registro, columnas_clave["umbral_tat_total"])),
    )

    col_t3.metric(
        "Performance TAT",
        formatear_valor(obtener_valor(registro, columnas_clave["performance_tat_total"])),
    )

    col_t4.metric(
        "Días incumplimiento",
        formatear_valor(obtener_valor(registro, columnas_clave["dias_incumplimiento"])),
    )

    col_t5.metric(
        "Rango incumplimiento",
        formatear_valor(obtener_valor(registro, columnas_clave["rango_incumplimiento"])),
    )

    st.markdown("#### Etapas del TAT")

    st.dataframe(
        construir_tabla_etapas_tat(registro, columnas_clave),
        use_container_width=True,
        hide_index=True,
    )

    if columnas_clave["estado_match"]:
        st.markdown("#### Estado del match")
        st.info(formatear_valor(obtener_valor(registro, columnas_clave["estado_match"])))


# ============================================================
# Encabezado
# ============================================================

mostrar_logo()

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">07_FILTRO</div>
        <div class="app-subtitle">
            Busca una SOLPED, filtra registros y visualiza el seguimiento TAT de la solicitud
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Obtener dataframe activo
# ============================================================

df_tat = st.session_state.get("df_tat")
nombre_archivo_tat = st.session_state.get("nombre_archivo_tat")

if df_tat is None:
    st.info("No hay archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_tat = limpiar_nombres_columnas(df_tat)
df_tat = normalizar_columnas_me80fn(df_tat)

df_base = df_tat.copy()
df_base["_id_observacion"] = range(len(df_base))

columnas_clave = detectar_columnas_clave(df_base)

if columnas_clave["solped"] is None:
    st.error(
        "No se encontró columna SOLPED. Se esperaba una columna como "
        "'Solicitud de pedido - ME5A' o 'Solicitud de pedido'."
    )
    st.stop()


# ============================================================
# Filtros en encabezado
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">Filtros</h4>
        <p class="small-muted">
            Filtra por SOLPED, pedido, posición o material. Por defecto se selecciona la primera observación disponible.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1.4, 1.4, 1.1, 1.4, 1])

with col_f1:
    filtro_solped = st.text_input(
        "SOLPED",
        placeholder="Ej: 6000123456",
        key="filtro_solped",
    )

with col_f2:
    filtro_pedido = st.text_input(
        "Pedido",
        placeholder="Ej: 4500123456",
        key="filtro_pedido",
    )

with col_f3:
    filtro_posicion = st.text_input(
        "Posición",
        placeholder="Ej: 10",
        key="filtro_posicion",
    )

with col_f4:
    filtro_material = st.text_input(
        "Material",
        placeholder="Ej: 123456",
        key="filtro_material",
    )

with col_f5:
    modo_busqueda = st.selectbox(
        "Modo",
        options=[
            "Contiene",
            "Exacta",
        ],
        index=0,
        key="filtro_modo",
    )


limpiar_filtros = st.button(
    "Limpiar filtros",
    use_container_width=True,
)

if limpiar_filtros:
    claves_filtros = [
        "filtro_solped",
        "filtro_pedido",
        "filtro_posicion",
        "filtro_material",
        "filtro_modo",
        "selector_observacion",
        "filtro_parquet_bytes",
        "filtro_parquet_firma",
        "filtro_csv_bytes",
        "filtro_csv_firma",
    ]

    for clave in claves_filtros:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


# ============================================================
# Aplicar filtros
# ============================================================

df_filtrado = df_base.copy()

df_filtrado = aplicar_filtro_texto(
    df=df_filtrado,
    columna=columnas_clave["solped"],
    texto=filtro_solped,
    modo=modo_busqueda,
)

df_filtrado = aplicar_filtro_texto(
    df=df_filtrado,
    columna=columnas_clave["pedido"],
    texto=filtro_pedido,
    modo=modo_busqueda,
)

df_filtrado = aplicar_filtro_texto(
    df=df_filtrado,
    columna=columnas_clave["posicion"],
    texto=filtro_posicion,
    modo=modo_busqueda,
)

df_filtrado = aplicar_filtro_texto(
    df=df_filtrado,
    columna=columnas_clave["material"],
    texto=filtro_material,
    modo=modo_busqueda,
)


# ============================================================
# Indicadores
# ============================================================

total_original = len(df_base)
total_filtrado = len(df_filtrado)

total_solped_original = int(df_base[columnas_clave["solped"]].nunique(dropna=True))
total_solped_filtrado = (
    int(df_filtrado[columnas_clave["solped"]].nunique(dropna=True))
    if not df_filtrado.empty
    else 0
)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

col_m1.metric("Filas totales", f"{total_original:,}")
col_m2.metric("Filas filtradas", f"{total_filtrado:,}")
col_m3.metric("SOLPED únicas", f"{total_solped_original:,}")
col_m4.metric("SOLPED filtradas", f"{total_solped_filtrado:,}")


# ============================================================
# Selección de observación optimizada
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">Observación seleccionada</h4>
        <p class="small-muted">
            Selecciona una observación para visualizar el seguimiento de la SOLPED.
            Por defecto se toma la primera observación filtrada.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_filtrado.empty:
    st.warning("No hay observaciones para mostrar con los filtros actuales.")
    st.stop()

limite_selector = 500

df_selector = df_filtrado.head(limite_selector).copy()

if len(df_filtrado) > limite_selector:
    st.info(
        f"Hay {len(df_filtrado):,} observaciones filtradas. "
        f"Para mantener buen rendimiento, el selector muestra las primeras {limite_selector:,}. "
        "Usa los filtros para reducir el resultado."
    )

df_selector["_etiqueta_observacion"] = (
    "SOLPED "
    + df_selector[columnas_clave["solped"]].astype("string").fillna("")
)

if columnas_clave["pedido"] is not None and columnas_clave["pedido"] in df_selector.columns:
    df_selector["_etiqueta_observacion"] += (
        " | Pedido "
        + df_selector[columnas_clave["pedido"]].astype("string").fillna("")
    )

if columnas_clave["posicion"] is not None and columnas_clave["posicion"] in df_selector.columns:
    df_selector["_etiqueta_observacion"] += (
        " | Pos "
        + df_selector[columnas_clave["posicion"]].astype("string").fillna("")
    )

if columnas_clave["material"] is not None and columnas_clave["material"] in df_selector.columns:
    df_selector["_etiqueta_observacion"] += (
        " | Material "
        + df_selector[columnas_clave["material"]].astype("string").fillna("")
    )

opciones_selector = dict(
    zip(
        df_selector["_etiqueta_observacion"],
        df_selector["_id_observacion"],
    )
)

etiqueta_seleccionada = st.selectbox(
    "Observación",
    options=list(opciones_selector.keys()),
    index=0,
    key="selector_observacion",
)

id_observacion_seleccionada = opciones_selector[etiqueta_seleccionada]

registro_seleccionado = (
    df_filtrado[df_filtrado["_id_observacion"].eq(id_observacion_seleccionada)]
    .iloc[0]
)

mostrar_detalle_observacion(
    registro=registro_seleccionado,
    columnas_clave=columnas_clave,
)


# ============================================================
# Resultado filtrado
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">Resultado filtrado</h4>
        <p class="small-muted">
            Tabla resumida de las observaciones disponibles con los filtros aplicados.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

columnas_vista = construir_columnas_vista(df_filtrado, columnas_clave)

limite_vista = st.number_input(
    "Filas a mostrar",
    min_value=20,
    max_value=1000,
    value=200,
    step=20,
)

df_vista = df_filtrado.drop(columns=["_id_observacion"], errors="ignore")

columnas_vista = [
    col for col in columnas_vista
    if col in df_vista.columns
]

if columnas_vista:
    st.dataframe(
        df_vista[columnas_vista].head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.dataframe(
        df_vista.head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Descarga opcional optimizada
# ============================================================

with st.expander("Descargar resultado filtrado", expanded=False):
    st.caption(
        "Parquet es el formato recomendado. Los archivos se preparan solo cuando los solicitas."
    )

    df_export = df_filtrado.drop(columns=["_id_observacion"], errors="ignore")

    firma_export = (
        f"{len(df_export)}_"
        f"{filtro_solped}_"
        f"{filtro_pedido}_"
        f"{filtro_posicion}_"
        f"{filtro_material}_"
        f"{modo_busqueda}"
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        preparar_parquet = st.button(
            "Preparar Parquet filtrado",
            use_container_width=True,
            key="preparar_parquet_filtrado",
        )

        if preparar_parquet:
            with st.spinner("Preparando Parquet..."):
                st.session_state["filtro_parquet_bytes"] = convertir_a_parquet_cache(df_export)
                st.session_state["filtro_parquet_firma"] = firma_export

        if (
            st.session_state.get("filtro_parquet_bytes") is not None
            and st.session_state.get("filtro_parquet_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Parquet filtrado",
                data=st.session_state["filtro_parquet_bytes"],
                file_name="resultado_filtrado_solped.parquet",
                mime="application/octet-stream",
                type="primary",
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV filtrado",
            use_container_width=True,
            key="preparar_csv_filtrado",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["filtro_csv_bytes"] = convertir_a_csv_cache(df_export)
                st.session_state["filtro_csv_firma"] = firma_export

        if (
            st.session_state.get("filtro_csv_bytes") is not None
            and st.session_state.get("filtro_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV filtrado",
                data=st.session_state["filtro_csv_bytes"],
                file_name="resultado_filtrado_solped.csv",
                mime="text/csv",
                use_container_width=True,
            )
