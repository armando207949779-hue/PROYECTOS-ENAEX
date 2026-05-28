import base64
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

APP_DOLAR = PROJECT_DIR / "app_sii_dolar" / "app_sii_dolar.py"
APP_UTM = PROJECT_DIR / "app_sii_utm" / "app_sii_utm.py"
APP_IPC = PROJECT_DIR / "app_ine_ipc" / "app_ine_ipc.py"
APP_ICL = PROJECT_DIR / "app_ine_icl" / "app_ine_icl.py"
APP_MOP = PROJECT_DIR / "app_indice_polinomico_mop" / "app_indice_polinomico_mop.py"
APP_SIEVO = PROJECT_DIR / "app_sievo" / "app_sievo.py"
APP_CONSOLIDADO = PROJECT_DIR / "app_consolidado_temporal" / "app_consolidado_temporal.py"


# =========================
# Configuración general
# =========================

st.set_page_config(
    page_title="Proyectos ENAEX",
    page_icon="🏢",
    layout="wide"
)


# =========================
# Información de Fuentes de Datos
# =========================

FUENTES_DATOS = {
    "Dólar SII": {
        "descripcion": "Tipo de cambio del dólar observado",
        "fuente": "Servicio de Impuestos Internos (SII)",
        "url_fuente": "https://www.sii.cl/",
        "frecuencia": "Diaria",
        "actualizacion": "Cada día hábil",
        "variables": ["Dólar Observado"],
        "rango_datos": "Desde 1990"
    },
    "UTM SII": {
        "descripcion": "Unidad Tributaria Mensual, UTA e IPC valor puntos",
        "fuente": "Servicio de Impuestos Internos (SII)",
        "url_fuente": "https://www.sii.cl/",
        "frecuencia": "Mensual",
        "actualizacion": "Primer día de cada mes",
        "variables": ["UTM", "UTA", "IPC Valor Puntos"],
        "rango_datos": "Desde 1981"
    },
    "IPC INE": {
        "descripcion": "Índice de Precios al Consumidor General",
        "fuente": "Instituto Nacional de Estadísticas (INE)",
        "url_fuente": "https://www.ine.gob.cl/",
        "frecuencia": "Mensual",
        "actualizacion": "Últimos días del mes publicado",
        "variables": ["IPC General", "Variación Mensual", "Variación Anual"],
        "rango_datos": "Desde 1990"
    },
    "ICL INE": {
        "descripcion": "Índice de Costos Laborales y Remuneraciones",
        "fuente": "Instituto Nacional de Estadísticas (INE)",
        "url_fuente": "https://www.ine.gob.cl/",
        "frecuencia": "Trimestral",
        "actualizacion": "Mes posterior al trimestre",
        "variables": ["Índice Trimestral", "Variación Trimestral"],
        "rango_datos": "Desde 2009"
    },
    "MOP Reajuste Polinómico": {
        "descripcion": "Índices para cálculo de reajuste polinómico",
        "fuente": "Ministerio de Obras Públicas (MOP)",
        "url_fuente": "https://www.mop.gob.cl/",
        "frecuencia": "Mensual",
        "actualizacion": "Días posteriores a cierre de mes",
        "variables": ["Índice Polinómico General"],
        "rango_datos": "Desde 1990"
    },
    "Savings Bridge": {
        "descripcion": "Análisis de ahorro mediante gráficos Savings Bridge",
        "fuente": "Datos ingresados por el usuario",
        "url_fuente": "N/A",
        "frecuencia": "A demanda",
        "actualizacion": "Manual",
        "variables": ["Customizables"],
        "rango_datos": "Definido por usuario"
    },
    "Consolidado Temporal": {
        "descripcion": "Base consolidada de indicadores SII, INE y MOP",
        "fuente": "SII, INE, MOP",
        "url_fuente": "Ver indicadores individuales",
        "frecuencia": "Mensual",
        "actualizacion": "Cuando se actualizan los indicadores base",
        "variables": ["Dólar", "UTM", "IPC", "ICL", "Índices MOP"],
        "rango_datos": "Período disponible"
    }
}


# =========================
# Funciones auxiliares para mejoras
# =========================

def obtener_datos_temporales():
    """
    REEMPLAZAR esta función con tu lectura real de datos.
    Debe retornar un DataFrame con columnas: fecha, dolar, utm, ipc, icl
    """
    fechas = pd.date_range(start='2023-01-01', end=datetime.now(), freq='D')
    df = pd.DataFrame({
        'fecha': fechas,
        'dolar': 500 + (range(len(fechas)) % 100),
        'utm': 60000 + (range(len(fechas)) % 5000),
        'ipc': 120 + (range(len(fechas)) % 10),
        'icl': 110 + (range(len(fechas)) % 8),
    })
    return df


def detectar_datos_faltantes(df, ultimos_meses=3):
    """Detecta parámetros faltantes en los últimos meses"""
    if df.empty:
        return {"error": "No hay datos disponibles"}
    
    fecha_limite = datetime.now() - timedelta(days=30 * ultimos_meses)
    df_reciente = df[df['fecha'] >= fecha_limite].copy()
    
    if df_reciente.empty:
        return {"error": f"No hay datos en los últimos {ultimos_meses} meses"}
    
    faltantes = {}
    for col in df_reciente.columns:
        if col != 'fecha':
            valores_nulos = df_reciente[col].isna().sum()
            if valores_nulos > 0:
                porcentaje = (valores_nulos / len(df_reciente)) * 100
                faltantes[col] = {
                    "cantidad": valores_nulos,
                    "porcentaje": round(porcentaje, 2),
                    "total_registros": len(df_reciente)
                }
    
    return faltantes


# =========================
# Logo centrado
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
# Página principal
# =========================

def pagina_inicio():
    mostrar_logo_centrado()

    st.markdown(
        "<h1 style='text-align: center;'>Portal de Aplicaciones ENAEX</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Selecciona una aplicación desde el menú lateral para consultar indicadores,
            generar resúmenes, visualizar gráficos y descargar archivos Excel.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ===== SECCIÓN: Gráfico Temporal =====
    st.subheader("📊 Gráfico Temporal de Indicadores")
    
    try:
        df_datos = obtener_datos_temporales()
        
        if not df_datos.empty:
            col_grafico1, col_grafico2 = st.columns([3, 1])
            
            with col_grafico2:
                variables_disponibles = [col for col in df_datos.columns if col != 'fecha']
                variable_principal = st.selectbox(
                    "Variable principal",
                    variables_disponibles,
                    index=0,
                    key="var_principal"
                )
                
                variables_adicionales = st.multiselect(
                    "Variables adicionales",
                    [v for v in variables_disponibles if v != variable_principal],
                    key="vars_adicionales"
                )
            
            with col_grafico1:
                if variables_adicionales:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df_datos['fecha'],
                            y=df_datos[variable_principal],
                            name=variable_principal,
                            line=dict(color='#1f77b4', width=2),
                            mode='lines'
                        ),
                        secondary_y=False
                    )
                    
                    colores = ['#ff7f0e', '#2ca02c', '#d62728']
                    for i, var in enumerate(variables_adicionales):
                        fig.add_trace(
                            go.Scatter(
                                x=df_datos['fecha'],
                                y=df_datos[var],
                                name=var,
                                line=dict(color=colores[i % len(colores)], width=2),
                                mode='lines'
                            ),
                            secondary_y=True
                        )
                    
                    fig.update_layout(
                        title=f"Evolución: {variable_principal} y otras variables",
                        height=400,
                        hovermode='x unified',
                        template='plotly_white'
                    )
                else:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_datos['fecha'],
                        y=df_datos[variable_principal],
                        name=variable_principal,
                        line=dict(color='#1f77b4', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(31, 119, 180, 0.2)'
                    ))
                    
                    fig.update_layout(
                        title=f"Evolución del {variable_principal}",
                        xaxis_title="Fecha",
                        yaxis_title=variable_principal,
                        height=400,
                        hovermode='x',
                        template='plotly_white'
                    )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos disponibles para mostrar el gráfico temporal")
            
    except Exception as e:
        st.error(f"Error al cargar gráfico temporal: {e}")

    st.markdown("---")

    # ===== SECCIÓN: Alertas de Datos Faltantes =====
    st.subheader("⚠️ Estado de Datos en Últimos 3 Meses")
    
    try:
        df_datos = obtener_datos_temporales()
        faltantes = detectar_datos_faltantes(df_datos, ultimos_meses=3)
        
        if "error" in faltantes:
            st.info(faltantes["error"])
        elif faltantes:
            st.warning(f"Se detectaron {len(faltantes)} parámetro(s) con datos faltantes:")
            for variable, info in faltantes.items():
                st.error(
                    f"**{variable}**: {info['cantidad']} registros faltantes "
                    f"({info['porcentaje']}% de {info['total_registros']} registros)"
                )
        else:
            st.success("✅ Todos los parámetros están completos en los últimos 3 meses")
            
    except Exception as e:
        st.warning(f"No se pudo verificar estado de datos: {e}")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **Dólar SII**

            Consulta del dólar observado por año y mes.
            """
        )

    with col2:
        st.info(
            """
            **UTM SII**

            Consulta de UTM, UTA e IPC valor puntos.
            """
        )

    with col3:
        st.info(
            """
            **IPC INE**

            Consulta automática del IPC General publicado por el INE.
            """
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.info(
            """
            **ICL INE**

            Índice de Remuneraciones y Costos Laborales.
            """
        )

    with col5:
        st.info(
            """
            **MOP Reajuste Polinómico**

            Índices y precios para cálculo de reajuste polinómico.
            """
        )

    with col6:
        st.info(
            """
            **Savings Bridge**

            Generación de gráfico Savings Bridge desde tabla pegada.
            """
        )

    col7, col8, col9 = st.columns(3)

    with col7:
        st.info(
            """
            **Consolidado Temporal**

            Unifica indicadores SII, INE y MOP en una base mensual.
            """
        )


# =========================
# Página de Fuentes de Datos
# =========================

def pagina_fuentes_datos():
    mostrar_logo_centrado()
    
    st.markdown(
        "<h1 style='text-align: center;'>Fuentes de Datos de Indicadores</h1>",
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        Información detallada sobre las fuentes de datos,
        frecuencia de actualización y variables disponibles en cada indicador.
        """
    )
    
    st.markdown("---")
    
    tabs = st.tabs(list(FUENTES_DATOS.keys()))
    
    for tab, (nombre_indicador, info_fuente) in zip(tabs, FUENTES_DATOS.items()):
        with tab:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### {nombre_indicador}")
                st.markdown(f"**Descripción:** {info_fuente['descripcion']}")
                st.markdown("---")
                st.markdown("#### Información de la Fuente")
                
                info_col1, info_col2 = st.columns(2)
                
                with info_col1:
                    st.markdown(f"**Organismo:** {info_fuente['fuente']}")
                    st.markdown(f"**Frecuencia:** {info_fuente['frecuencia']}")
                    st.markdown(f"**Rango de datos:** {info_fuente['rango_datos']}")
                
                with info_col2:
                    st.markdown(f"**Actualización:** {info_fuente['actualizacion']}")
                    if info_fuente['url_fuente'] != 'N/A':
                        st.markdown(f"[Ir a página oficial]({info_fuente['url_fuente']})")
                
                st.markdown("---")
                st.markdown("#### Variables Disponibles")
                for i, variable in enumerate(info_fuente['variables'], 1):
                    st.markdown(f"{i}. {variable}")
            
            with col2:
                st.markdown("#### Resumen")
                st.metric("Estado", "Activo", delta=info_fuente['frecuencia'].lower())
                st.metric("Variables", len(info_fuente['variables']))


# =========================
# Validación rápida de archivos
# =========================

apps_requeridas = {
    "Dólar SII": APP_DOLAR,
    "UTM SII": APP_UTM,
    "IPC INE": APP_IPC,
    "ICL INE": APP_ICL,
    "MOP Reajuste": APP_MOP,
    "Savings Bridge": APP_SIEVO,
    "Consolidado Temporal": APP_CONSOLIDADO,
}

apps_faltantes = {
    nombre: ruta
    for nombre, ruta in apps_requeridas.items()
    if not ruta.exists()
}

if apps_faltantes:
    st.error("No se encontraron una o más apps. Revisa los nombres de carpetas y archivos.")

    for nombre, ruta in apps_faltantes.items():
        st.write(f"**{nombre}:** {ruta}")

    st.stop()


# =========================
# Navegación entre apps
# =========================

pagina = st.navigation(
    {
        "Inicio": [
            st.Page(
                pagina_inicio,
                title="Inicio",
                icon="🏠"
            )
        ],
        "Información": [
            st.Page(
                pagina_fuentes_datos,
                title="Fuentes de Datos",
                icon="📚"
            ),
        ],
        "Consolidado": [
            st.Page(
                APP_CONSOLIDADO,
                title="Consolidado Temporal",
                icon="🧩"
            ),
        ],
        "Indicadores SII": [
            st.Page(
                APP_DOLAR,
                title="Dólar SII",
                icon="💵"
            ),
            st.Page(
                APP_UTM,
                title="UTM SII",
                icon="📊"
            ),
        ],
        "Indicadores INE": [
            st.Page(
                APP_IPC,
                title="IPC INE",
                icon="📈"
            ),
            st.Page(
                APP_ICL,
                title="ICL INE",
                icon="📉"
            ),
        ],
        "MOP": [
            st.Page(
                APP_MOP,
                title="Reajuste Polinómico MOP",
                icon="🏗️"
            ),
        ],
        "Análisis": [
            st.Page(
                APP_SIEVO,
                title="Savings Bridge",
                icon="🌉"
            ),
        ],
    }
)

pagina.run()
