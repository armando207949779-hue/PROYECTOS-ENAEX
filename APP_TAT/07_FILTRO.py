# ============================================================
# 07_FILTRO
# Filtro, búsqueda y seguimiento de solicitudes de compra
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import base64
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# Rutas
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilos mínimos
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

        .result-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 16px 18px;
            margin-top: 12px;
            margin-bottom: 12px;
        }

        .section-title {
            font-size: 1.08rem;
            font-weight: 800;
            color: #1f2937;
            margin-top: 20px;
            margin-bottom: 4px;
        }

        .section-subtitle {
            font-size: 0.88rem;
            color: #6b7280;
            margin-bottom: 12px;
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
        return "—"

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    texto = str(valor).strip()

    if texto == "":
        return "—"

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


def formatear_entero(valor) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return formatear_valor(valor)

    return f"{int(round(numero)):,}".replace(",", ".")


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


def obtener_valor(registro: pd.Series, columna: str | None):
    if columna is None:
        return pd.NA

    if columna not in registro.index:
        return pd.NA

    return registro.get(columna)


def normalizar_valor_busqueda(valor) -> str:
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().lower()

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


def normalizar_serie_busqueda(serie: pd.Series) -> pd.Series:
    return serie.apply(normalizar_valor_busqueda)


def aplicar_filtro_texto(
    df: pd.DataFrame,
    columna: str | None,
    texto: str,
    modo: str = "Exacta",
) -> pd.DataFrame:

    if columna is None or columna not in df.columns:
        return df

    texto = str(texto).strip()

    if not texto:
        return df

    serie = normalizar_serie_busqueda(df[columna])
    texto_norm = normalizar_valor_busqueda(texto)

    if modo == "Exacta":
        return df[serie.eq(texto_norm)].copy()

    return df[serie.str.contains(texto_norm, na=False, regex=False)].copy()


def hay_criterio_busqueda(
    filtro_solped: str,
    filtro_pedido: str,
    filtro_posicion: str,
    filtro_material: str,
    filtro_texto_breve: str,
) -> bool:
    valores = [
        filtro_solped,
        filtro_pedido,
        filtro_posicion,
        filtro_material,
        filtro_texto_breve,
    ]

    return any(str(valor).strip() for valor in valores)


def aplicar_filtros_con_progreso(
    df_base: pd.DataFrame,
    columnas_clave: dict,
    filtro_solped: str,
    filtro_pedido: str,
    filtro_posicion: str,
    filtro_material: str,
    filtro_texto_breve: str,
    modo_busqueda: str,
) -> pd.DataFrame:

    barra = st.progress(0, text="Preparando búsqueda...")

    df_filtrado = df_base.copy()

    barra.progress(15, text="Cargando base activa...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["solped"],
        texto=filtro_solped,
        modo=modo_busqueda,
    )

    barra.progress(35, text="Buscando SOLPED...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["pedido"],
        texto=filtro_pedido,
        modo=modo_busqueda,
    )

    barra.progress(50, text="Buscando pedido...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["posicion"],
        texto=filtro_posicion,
        modo=modo_busqueda,
    )

    barra.progress(65, text="Buscando posición...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["material"],
        texto=filtro_material,
        modo=modo_busqueda,
    )

    barra.progress(80, text="Buscando material...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["texto_breve"],
        texto=filtro_texto_breve,
        modo="Contiene",
    )

    barra.progress(100, text="Búsqueda finalizada.")

    return df_filtrado


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
                "Documento de compras - ME80FN",
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
        "grupo_compras": buscar_columna(
            df,
            [
                "Grupo de compras",
                "Grupo compras",
                "Grupo de compras - ME5A",
            ],
        ),
        "tipo_oc": buscar_columna(
            df,
            [
                "tipo_oc",
                "Tipo OC",
                "Clase de documento",
            ],
        ),
        "sistema": buscar_columna(
            df,
            [
                "sistema",
                "Sistema",
            ],
        ),
        "origen": buscar_columna(
            df,
            [
                "origen",
                "Origen",
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
                "Fecha facturación",
            ],
        ),
        "fecha_recepcion": buscar_columna(
            df,
            [
                "fecha_recepcion_final",
                "Fecha recepción mercancía - ME80FN",
                "Fecha recepción",
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


# ============================================================
# Construcción de etiquetas y tablas
# ============================================================

def construir_etiqueta_observacion(row: pd.Series, columnas_clave: dict) -> str:
    solped = formatear_valor(obtener_valor(row, columnas_clave["solped"]))
    pedido = formatear_valor(obtener_valor(row, columnas_clave["pedido"]))
    posicion = formatear_valor(obtener_valor(row, columnas_clave["posicion"]))
    material = formatear_valor(obtener_valor(row, columnas_clave["material"]))
    texto = formatear_valor(obtener_valor(row, columnas_clave["texto_breve"]))
    fila = formatear_valor(row.get("_id_observacion", ""))

    etiqueta = f"SOLPED {solped}"

    if pedido != "—":
        etiqueta += f" | Pedido {pedido}"

    if posicion != "—":
        etiqueta += f" | Pos {posicion}"

    if material != "—":
        etiqueta += f" | Material {material}"

    if texto != "—":
        texto_corto = texto[:45] + "..." if len(texto) > 45 else texto
        etiqueta += f" | {texto_corto}"

    etiqueta += f" | Fila {fila}"

    return etiqueta


def construir_tabla_general(registro: pd.Series, columnas_clave: dict) -> pd.DataFrame:
    datos = [
        {
            "Campo": "SOLPED",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["solped"])),
        },
        {
            "Campo": "Pedido",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["pedido"])),
        },
        {
            "Campo": "Posición",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["posicion"])),
        },
        {
            "Campo": "Material",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["material"])),
        },
        {
            "Campo": "Texto breve",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["texto_breve"])),
        },
        {
            "Campo": "Centro",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["centro"])),
        },
        {
            "Campo": "Grupo de compras",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["grupo_compras"])),
        },
        {
            "Campo": "Tipo OC",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["tipo_oc"])),
        },
        {
            "Campo": "Sistema",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["sistema"])),
        },
        {
            "Campo": "Origen",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["origen"])),
        },
        {
            "Campo": "Estado del match",
            "Valor": formatear_valor(obtener_valor(registro, columnas_clave["estado_match"])),
        },
    ]

    return pd.DataFrame(datos)


def construir_tabla_fechas(registro: pd.Series, columnas_clave: dict) -> pd.DataFrame:
    datos = [
        {
            "Etapa": "Solicitud",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_solicitud"])),
        },
        {
            "Etapa": "Liberación",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_liberacion"])),
        },
        {
            "Etapa": "Pedido",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_pedido"])),
        },
        {
            "Etapa": "Facturación",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_facturacion"])),
        },
        {
            "Etapa": "Recepción",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_recepcion"])),
        },
    ]

    return pd.DataFrame(datos)


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


def construir_validacion_temporal_tat(
    registro: pd.Series,
    columnas_clave: dict,
) -> pd.DataFrame:

    etapas = {
        "Solicitud": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_solicitud"]),
            errors="coerce",
        ),
        "Liberación": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_liberacion"]),
            errors="coerce",
        ),
        "Pedido": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_pedido"]),
            errors="coerce",
        ),
        "Facturación": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_facturacion"]),
            errors="coerce",
        ),
        "Recepción": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_recepcion"]),
            errors="coerce",
        ),
    }

    comparaciones = [
        ("Solicitud", "Liberación"),
        ("Liberación", "Pedido"),
        ("Pedido", "Facturación"),
        ("Facturación", "Recepción"),
        ("Solicitud", "Facturación"),
        ("Solicitud", "Recepción"),
    ]

    validaciones = []

    for inicio, fin in comparaciones:
        fecha_inicio = etapas[inicio]
        fecha_fin = etapas[fin]

        if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
            estado = "Sin datos"
            detalle = "No evaluable por fecha faltante"
            dias = pd.NA

        else:
            dias = int((fecha_fin - fecha_inicio).days)

            if fecha_fin >= fecha_inicio:
                estado = "Correcto"
                detalle = "Orden temporal válido"
            else:
                estado = "Revisar"
                detalle = "La fecha final ocurre antes que la fecha inicial"

        validaciones.append(
            {
                "Validación": f"{inicio} → {fin}",
                "Fecha inicial": formatear_fecha(fecha_inicio),
                "Fecha final": formatear_fecha(fecha_fin),
                "Días entre fechas": dias,
                "Estado": estado,
                "Detalle": detalle,
            }
        )

    return pd.DataFrame(validaciones)


# ============================================================
# Visualización de resultado confirmado
# ============================================================

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

    st.markdown("#### Flujo de la SOLPED")

    cols = st.columns(len(etapas))

    for col, item in zip(cols, etapas):
        fecha = pd.to_datetime(item["fecha"], errors="coerce")
        realizado = pd.notna(fecha)
        fecha_texto = formatear_fecha(item["fecha"])

        with col:
            if realizado:
                st.success(
                    f"✅ **{item['etapa']}**\n\n{fecha_texto}"
                )
            else:
                st.error(
                    f"❌ **{item['etapa']}**\n\nSin fecha"
                )


def mostrar_validacion_temporal_tat(
    registro: pd.Series,
    columnas_clave: dict,
):
    st.markdown("#### Validación temporal")

    validacion_df = construir_validacion_temporal_tat(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    total_revisar = int(validacion_df["Estado"].eq("Revisar").sum())
    total_sin_datos = int(validacion_df["Estado"].eq("Sin datos").sum())

    if total_revisar > 0:
        st.error(
            "Se detectaron fechas fuera de orden temporal. "
            "Revisa los casos marcados como 'Revisar'."
        )

    elif total_sin_datos > 0:
        st.warning(
            "Las fechas disponibles están ordenadas, pero existen etapas sin fecha. "
            "El flujo no se puede validar completamente."
        )

    else:
        st.success(
            "Las fechas TAT están ordenadas temporalmente."
        )

    st.dataframe(
        validacion_df,
        use_container_width=True,
        hide_index=True,
    )


def mostrar_detalle_observacion(registro: pd.Series, columnas_clave: dict):
    st.markdown("### Resultado confirmado")
    st.caption("Detalle ordenado desde información general hasta validaciones específicas.")

    st.markdown("#### 1. Información general")

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)

    col_g1.metric(
        "SOLPED",
        formatear_valor(obtener_valor(registro, columnas_clave["solped"])),
    )

    col_g2.metric(
        "Pedido",
        formatear_valor(obtener_valor(registro, columnas_clave["pedido"])),
    )

    col_g3.metric(
        "Posición",
        formatear_valor(obtener_valor(registro, columnas_clave["posicion"])),
    )

    col_g4.metric(
        "Centro",
        formatear_valor(obtener_valor(registro, columnas_clave["centro"])),
    )

    st.dataframe(
        construir_tabla_general(registro, columnas_clave),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### 2. Seguimiento del flujo TAT")

    mostrar_figura_estado_solped(registro, columnas_clave)

    st.markdown("#### 3. Fechas principales")

    st.dataframe(
        construir_tabla_fechas(registro, columnas_clave),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### 4. Indicadores TAT")

    col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)

    col_t1.metric(
        "Días TAT total",
        formatear_entero(obtener_valor(registro, columnas_clave["dias_tat_total"])),
    )

    col_t2.metric(
        "Umbral TAT total",
        formatear_entero(obtener_valor(registro, columnas_clave["umbral_tat_total"])),
    )

    col_t3.metric(
        "Performance TAT",
        formatear_valor(obtener_valor(registro, columnas_clave["performance_tat_total"])),
    )

    col_t4.metric(
        "Días incumplimiento",
        formatear_entero(obtener_valor(registro, columnas_clave["dias_incumplimiento"])),
    )

    col_t5.metric(
        "Rango incumplimiento",
        formatear_valor(obtener_valor(registro, columnas_clave["rango_incumplimiento"])),
    )

    st.markdown("#### 5. Estado de etapas")

    st.dataframe(
        construir_tabla_etapas_tat(registro, columnas_clave),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### 6. Validación temporal")

    mostrar_validacion_temporal_tat(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    with st.expander("Ver registro completo", expanded=False):
        registro_df = (
            registro
            .drop(labels=["_id_observacion"], errors="ignore")
            .to_frame(name="Valor")
            .reset_index()
            .rename(columns={"index": "Campo"})
        )

        st.dataframe(
            registro_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Encabezado
# ============================================================

mostrar_logo()

st.title("07_FILTRO")
st.caption(
    "Ingresa un criterio de búsqueda, ejecuta la consulta y confirma qué registro quieres revisar."
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
# Filtros iniciales
# ============================================================

st.markdown("### Búsqueda")
st.caption(
    "Completa al menos un campo. Luego presiona **Buscar** para cargar los resultados."
)

with st.form("form_busqueda_solped"):
    col_f1, col_f2, col_f3 = st.columns(3)

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

    col_f4, col_f5, col_f6 = st.columns([1.2, 1.6, 1])

    with col_f4:
        filtro_material = st.text_input(
            "Material",
            placeholder="Ej: 123456",
            key="filtro_material",
        )

    with col_f5:
        filtro_texto_breve = st.text_input(
            "Texto breve",
            placeholder="Buscar por descripción",
            key="filtro_texto_breve",
        )

    with col_f6:
        modo_busqueda = st.selectbox(
            "Modo",
            options=[
                "Exacta",
                "Contiene",
            ],
            index=0,
            key="filtro_modo",
        )

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        buscar = st.form_submit_button(
            "Buscar",
            use_container_width=True,
            type="primary",
        )

    with col_b2:
        limpiar = st.form_submit_button(
            "Limpiar",
            use_container_width=True,
        )


if limpiar:
    claves_filtros = [
        "filtro_solped",
        "filtro_pedido",
        "filtro_posicion",
        "filtro_material",
        "filtro_texto_breve",
        "filtro_modo",
        "selector_observacion",
        "df_filtrado_solped",
        "firma_filtros_solped",
        "filtro_id_confirmado",
        "filtro_detalle_confirmado",
    ]

    for clave in claves_filtros:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


firma_filtros_actual = (
    f"{filtro_solped}_"
    f"{filtro_pedido}_"
    f"{filtro_posicion}_"
    f"{filtro_material}_"
    f"{filtro_texto_breve}_"
    f"{modo_busqueda}_"
    f"{len(df_base)}"
)


if buscar:
    if not hay_criterio_busqueda(
        filtro_solped=filtro_solped,
        filtro_pedido=filtro_pedido,
        filtro_posicion=filtro_posicion,
        filtro_material=filtro_material,
        filtro_texto_breve=filtro_texto_breve,
    ):
        st.warning("Ingresa al menos un criterio de búsqueda antes de continuar.")
        st.stop()

    with st.spinner("Buscando coincidencias..."):
        df_filtrado = aplicar_filtros_con_progreso(
            df_base=df_base,
            columnas_clave=columnas_clave,
            filtro_solped=filtro_solped,
            filtro_pedido=filtro_pedido,
            filtro_posicion=filtro_posicion,
            filtro_material=filtro_material,
            filtro_texto_breve=filtro_texto_breve,
            modo_busqueda=modo_busqueda,
        )

        st.session_state["df_filtrado_solped"] = df_filtrado
        st.session_state["firma_filtros_solped"] = firma_filtros_actual

        if "filtro_id_confirmado" in st.session_state:
            del st.session_state["filtro_id_confirmado"]

        if "filtro_detalle_confirmado" in st.session_state:
            del st.session_state["filtro_detalle_confirmado"]

    st.success("Búsqueda finalizada.")

else:
    if (
        st.session_state.get("df_filtrado_solped") is not None
        and st.session_state.get("firma_filtros_solped") == firma_filtros_actual
    ):
        df_filtrado = st.session_state["df_filtrado_solped"].copy()
    else:
        st.stop()


# ============================================================
# Validación de resultados
# ============================================================

if df_filtrado.empty:
    st.warning("No se encontraron coincidencias con los criterios ingresados.")
    st.stop()


# ============================================================
# Selección y confirmación de coincidencia
# ============================================================

total_resultados = len(df_filtrado)

if total_resultados == 1:
    registro_seleccionado = df_filtrado.iloc[0]
    st.success("Se encontró una única coincidencia. Se muestra el detalle del registro.")

else:
    st.markdown("### Coincidencias encontradas")
    st.caption(
        "Se encontró más de una coincidencia. Selecciona cuál registro quieres revisar y confirma."
    )

    st.info(
        f"Se encontraron **{total_resultados:,} coincidencias**. "
        "Selecciona una observación para continuar."
    )

    limite_selector = 500
    df_selector = df_filtrado.head(limite_selector).copy()

    if len(df_filtrado) > limite_selector:
        st.warning(
            f"Se muestran las primeras {limite_selector:,} coincidencias en el selector. "
            "Refina la búsqueda para reducir resultados."
        )

    df_selector["_etiqueta_observacion"] = df_selector.apply(
        lambda row: construir_etiqueta_observacion(row, columnas_clave),
        axis=1,
    )

    opciones_selector = dict(
        zip(
            df_selector["_etiqueta_observacion"],
            df_selector["_id_observacion"],
        )
    )

    etiqueta_seleccionada = st.selectbox(
        "Coincidencia",
        options=list(opciones_selector.keys()),
        index=0,
        key="selector_observacion",
    )

    id_observacion_seleccionada = opciones_selector[etiqueta_seleccionada]

    confirmar = st.button(
        "Confirmar y ver detalle",
        type="primary",
        use_container_width=True,
    )

    if confirmar:
        st.session_state["filtro_id_confirmado"] = id_observacion_seleccionada
        st.session_state["filtro_detalle_confirmado"] = True

    id_confirmado = st.session_state.get("filtro_id_confirmado")

    if id_confirmado != id_observacion_seleccionada:
        st.stop()

    registro_seleccionado = (
        df_filtrado[df_filtrado["_id_observacion"].eq(id_observacion_seleccionada)]
        .iloc[0]
    )

    st.success("Registro confirmado. Se muestra el detalle seleccionado.")


# ============================================================
# Resultado confirmado
# ============================================================

mostrar_detalle_observacion(
    registro=registro_seleccionado,
    columnas_clave=columnas_clave,
)
