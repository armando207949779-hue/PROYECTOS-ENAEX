# ============================================================
# 04_APP_DICCIONARIOS
# APP_ESTRATEGIAS_LIBERACION
#
# Permite consultar las hojas de diccionarios del Excel activo:
# - CECOS
# - USUARIOS
# - RANGOS
#
# Funciones:
# - Detección flexible del nombre de las hojas
# - Pestañas independientes
# - Búsqueda en todas las columnas
# - Filtros por columnas
# - Métricas
# - Descarga individual en Excel y CSV
# - Vista de todas las hojas disponibles
# ============================================================

from __future__ import annotations

import base64
import re
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_CANDIDATES = [
    PROJECT_DIR / "assets" / "logo.svg",
    BASE_DIR / "assets" / "logo.svg",
    PROJECT_DIR / "assets" / "logo.png",
    BASE_DIR / "assets" / "logo.png",
    PROJECT_DIR / "assets" / "logo.jpg",
    BASE_DIR / "assets" / "logo.jpg",
    PROJECT_DIR / "assets" / "logo.jpeg",
    BASE_DIR / "assets" / "logo.jpeg",
]

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_FILE_BYTES_KEY = "flujo_liberacion_file_bytes"

DICTIONARY_CONFIG = {
    "cecos": {
        "titulo": "CECOS",
        "icono": "🏭",
        "descripcion": (
            "Catálogo de centros de costo, plantas y atributos asociados."
        ),
        "aliases": [
            "CECOS",
            "CECO",
            "DIC_CECOS",
            "DIC_CECO",
            "DICCIONARIO_CECOS",
            "DICCIONARIO_CECO",
        ],
    },
    "usuarios": {
        "titulo": "USUARIOS",
        "icono": "👥",
        "descripcion": (
            "Catálogo de usuarios, correos, cargos y datos relacionados."
        ),
        "aliases": [
            "USUARIOS",
            "USUARIO",
            "DIC_USUARIOS",
            "DIC_USUARIO",
            "DICCIONARIO_USUARIOS",
            "DICCIONARIO_USUARIO",
        ],
    },
    "rangos": {
        "titulo": "RANGOS",
        "icono": "📏",
        "descripcion": (
            "Catálogo de rangos de monto y reglas asociadas."
        ),
        "aliases": [
            "RANGOS",
            "RANGO",
            "DIC_RANGOS",
            "DIC_RANGO",
            "DICCIONARIO_RANGOS",
            "DICCIONARIO_RANGO",
        ],
    },
}


# ============================================================
# ESTILOS
# ============================================================

def compact_html(value: str) -> str:
    return re.sub(r">\s+<", "><", dedent(value).strip())


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer,
            .block-container {
                padding-top: 6.5rem !important;
                padding-bottom: 3rem !important;
            }

            .app-logo {
                width: 100%;
                min-height: 88px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: .6rem 0 .6rem;
                overflow: visible;
            }

            .app-logo img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 86px;
                object-fit: contain;
                display: block;
            }

            .app-title {
                text-align: center;
                color: #17365D;
                font-size: 2rem;
                font-weight: 850;
                margin: .1rem 0;
            }

            .app-subtitle {
                text-align: center;
                color: #64748B;
                font-size: 1rem;
                margin-bottom: 1.2rem;
            }

            .dictionary-card {
                border: 1px solid #D0D5DD;
                border-radius: 14px;
                padding: 14px 16px;
                background: #FFFFFF;
                height: 100%;
            }

            .dictionary-title {
                color: #17365D;
                font-size: 1rem;
                font-weight: 850;
            }

            .dictionary-caption {
                color: #64748B;
                font-size: .85rem;
                margin-top: 4px;
            }

            .metric-card {
                border: 1px solid #D0D5DD;
                border-radius: 13px;
                padding: 12px 14px;
                background: #FFFFFF;
                height: 100%;
            }

            .metric-label {
                color: #64748B;
                font-size: .76rem;
                font-weight: 750;
                text-transform: uppercase;
            }

            .metric-value {
                color: #17365D;
                font-size: 1.45rem;
                font-weight: 850;
                margin-top: 3px;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def buscar_logo() -> Path | None:
    return next(
        (path for path in LOGO_CANDIDATES if path.exists() and path.is_file()),
        None,
    )


def mostrar_logo() -> None:
    path = buscar_logo()
    if path is None:
        return

    try:
        if path.suffix.lower() == ".svg":
            raw = path.read_text(encoding="utf-8").encode("utf-8")
            mime = "image/svg+xml"
        else:
            raw = path.read_bytes()
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"

        encoded = base64.b64encode(raw).decode("utf-8")
        st.markdown(
            compact_html(
                f"""
                <div class="app-logo">
                    <img src="data:{mime};base64,{encoded}" alt="Logo ENAEX">
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
    except (OSError, UnicodeError):
        st.warning(f"No fue posible leer el logo: {path.name}")


def render_header() -> None:
    mostrar_logo()
    st.markdown(
        '<div class="app-title">04 Diccionarios</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="app-subtitle">
            Consulta los diccionarios de CECOS, USUARIOS y RANGOS
            contenidos en el Excel activo.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UTILIDADES
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "null"} else text


def normalize_sheet_name(value: str) -> str:
    """Normaliza un nombre de hoja para compararlo con sus alias."""
    normalized = str(value).strip().upper()
    normalized = (
        normalized.replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ü", "U")
        .replace("Ñ", "N")
    )
    return re.sub(r"[^A-Z0-9]+", "_", normalized).strip("_")


def find_sheet_name(
    sheet_names: list[str],
    aliases: list[str],
) -> str | None:
    normalized_sheets = {
        normalize_sheet_name(sheet): sheet
        for sheet in sheet_names
    }

    for alias in aliases:
        normalized_alias = normalize_sheet_name(alias)
        if normalized_alias in normalized_sheets:
            return normalized_sheets[normalized_alias]

    # Segunda búsqueda: contiene el término principal.
    normalized_aliases = [normalize_sheet_name(alias) for alias in aliases]
    for normalized_sheet, original_sheet in normalized_sheets.items():
        if any(
            normalized_alias in normalized_sheet
            or normalized_sheet in normalized_alias
            for normalized_alias in normalized_aliases
        ):
            return original_sheet

    return None


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result.columns = [
        clean_text(column) or f"Columna_{index + 1}"
        for index, column in enumerate(result.columns)
    ]

    # Elimina columnas totalmente vacías.
    result = result.dropna(axis=1, how="all")

    # Elimina filas totalmente vacías.
    result = result.dropna(axis=0, how="all").reset_index(drop=True)

    return result


@st.cache_data(show_spinner=False)
def read_dictionaries(
    file_bytes: bytes,
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, str | None],
    list[str],
]:
    if not file_bytes:
        raise ValueError("El archivo activo no contiene datos binarios.")

    try:
        excel = pd.ExcelFile(BytesIO(file_bytes))
    except Exception as error:
        raise ValueError(
            "No fue posible abrir el Excel activo."
        ) from error

    sheets = list(excel.sheet_names)
    dictionaries: dict[str, pd.DataFrame] = {}
    resolved_names: dict[str, str | None] = {}

    for key, config in DICTIONARY_CONFIG.items():
        sheet_name = find_sheet_name(
            sheet_names=sheets,
            aliases=config["aliases"],
        )
        resolved_names[key] = sheet_name

        if sheet_name is None:
            dictionaries[key] = pd.DataFrame()
            continue

        try:
            raw = pd.read_excel(excel, sheet_name=sheet_name)
            dictionaries[key] = normalize_dataframe(raw)
        except Exception:
            dictionaries[key] = pd.DataFrame()

    return dictionaries, resolved_names, sheets


def dataframe_to_excel_bytes(
    df: pd.DataFrame,
    sheet_name: str,
) -> bytes:
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            sheet_name=sheet_name[:31],
            index=False,
        )

    return output.getvalue()


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    # utf-8-sig permite abrir correctamente acentos en Excel.
    return df.to_csv(index=False).encode("utf-8-sig")


def apply_global_search(
    df: pd.DataFrame,
    search_text: str,
) -> pd.DataFrame:
    search = clean_text(search_text).lower()
    if not search:
        return df.copy()

    text_df = df.fillna("").astype(str)
    mask = text_df.apply(
        lambda row: row.str.lower().str.contains(
            re.escape(search),
            regex=True,
            na=False,
        ).any(),
        axis=1,
    )

    return df.loc[mask].copy()


def suitable_filter_columns(df: pd.DataFrame) -> list[str]:
    columns: list[str] = []

    for column in df.columns:
        unique_count = df[column].nunique(dropna=True)

        # Solo ofrece filtros manejables.
        if 1 < unique_count <= 100:
            columns.append(column)

    return columns


def apply_column_filters(
    df: pd.DataFrame,
    dictionary_key: str,
) -> pd.DataFrame:
    result = df.copy()
    filter_columns = suitable_filter_columns(result)

    if not filter_columns:
        st.caption("No se detectaron columnas adecuadas para filtros rápidos.")
        return result

    selected_filter_columns = st.multiselect(
        "Columnas para filtrar",
        options=filter_columns,
        default=[],
        key=f"{dictionary_key}_filter_columns",
    )

    for column in selected_filter_columns:
        values = sorted(
            {
                clean_text(value)
                for value in result[column].tolist()
                if clean_text(value)
            },
            key=str.lower,
        )

        selected_values = st.multiselect(
            f"Filtrar {column}",
            options=values,
            default=[],
            key=f"{dictionary_key}_filter_{column}",
        )

        if selected_values:
            result = result[
                result[column]
                .map(clean_text)
                .isin(selected_values)
            ].copy()

    return result


def render_metrics(
    original_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
) -> None:
    empty_cells = int(filtered_df.isna().sum().sum())
    duplicate_rows = int(filtered_df.duplicated().sum())

    columns = st.columns(4)
    metrics = [
        ("Filas totales", len(original_df)),
        ("Filas visibles", len(filtered_df)),
        ("Columnas", len(filtered_df.columns)),
        ("Duplicados visibles", duplicate_rows),
    ]

    for column, (label, value) in zip(columns, metrics):
        with column:
            st.markdown(
                compact_html(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value:,}</div>
                    </div>
                    """
                ).replace(",", "."),
                unsafe_allow_html=True,
            )

    if empty_cells:
        st.caption(
            f"La vista filtrada contiene {empty_cells:,} celdas vacías."
            .replace(",", ".")
        )


# ============================================================
# VISTA DE UN DICCIONARIO
# ============================================================

def render_dictionary(
    dictionary_key: str,
    df: pd.DataFrame,
    real_sheet_name: str | None,
    file_name: str,
) -> None:
    config = DICTIONARY_CONFIG[dictionary_key]

    st.markdown(
        compact_html(
            f"""
            <div class="dictionary-card">
                <div class="dictionary-title">
                    {config["icono"]} {config["titulo"]}
                </div>
                <div class="dictionary-caption">
                    {config["descripcion"]}
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    if real_sheet_name is None:
        st.warning(
            f"No se encontró una hoja compatible con **{config['titulo']}**."
        )
        st.caption(
            "Nombres reconocidos: "
            + ", ".join(f"`{alias}`" for alias in config["aliases"])
        )
        return

    if df.empty:
        st.warning(
            f"La hoja **{real_sheet_name}** existe, pero está vacía "
            "o no pudo ser interpretada."
        )
        return

    st.success(
        (
            f"Hoja detectada: **{real_sheet_name}** · "
            f"**{len(df):,} filas** · **{len(df.columns):,} columnas**"
        ).replace(",", ".")
    )

    search_text = st.text_input(
        "Buscar en todas las columnas",
        placeholder="Escribe un CECO, correo, cargo, rango...",
        key=f"{dictionary_key}_search",
    )

    searched = apply_global_search(df, search_text)

    with st.expander("Filtros avanzados", expanded=False):
        filtered = apply_column_filters(
            searched,
            dictionary_key,
        )

    render_metrics(
        original_df=df,
        filtered_df=filtered,
    )

    st.markdown("#### Resultados")

    if filtered.empty:
        st.warning("No hay registros que coincidan con la búsqueda y filtros.")
    else:
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            height=min(680, max(280, 35 * (len(filtered) + 2))),
        )

    base_name = Path(file_name or "BBDD_FLUJO_LIBERACION.xlsx").stem
    safe_sheet = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        config["titulo"],
    )

    col_excel, col_csv = st.columns(2)

    with col_excel:
        st.download_button(
            "⬇️ Descargar vista en Excel",
            data=dataframe_to_excel_bytes(
                filtered,
                config["titulo"],
            ),
            file_name=f"{base_name}_{safe_sheet}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key=f"{dictionary_key}_download_excel",
        )

    with col_csv:
        st.download_button(
            "⬇️ Descargar vista en CSV",
            data=dataframe_to_csv_bytes(filtered),
            file_name=f"{base_name}_{safe_sheet}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{dictionary_key}_download_csv",
        )

    with st.expander("Información de columnas", expanded=False):
        info = pd.DataFrame(
            {
                "Columna": df.columns,
                "Tipo detectado": [
                    str(df[column].dtype)
                    for column in df.columns
                ],
                "Valores no vacíos": [
                    int(df[column].notna().sum())
                    for column in df.columns
                ],
                "Valores únicos": [
                    int(df[column].nunique(dropna=True))
                    for column in df.columns
                ],
            }
        )
        st.dataframe(
            info,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# SIN ARCHIVO
# ============================================================

def render_no_file() -> None:
    st.warning(
        "No hay un archivo activo. Primero carga el Excel desde "
        "**01 Cargar archivo**."
    )

    try:
        if st.button(
            "📤 Ir a 01 Cargar archivo",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page("01_CARGAR_ARCHIVO_FLUJO.py")
    except Exception:
        st.info("Selecciona **01 Cargar archivo** desde la barra lateral.")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()

    file_name = st.session_state.get(
        SESSION_FILE_KEY,
        "BBDD_FLUJO_LIBERACION.xlsx",
    )
    file_bytes = st.session_state.get(
        SESSION_FILE_BYTES_KEY,
        b"",
    )

    if not file_bytes:
        render_no_file()
        return

    try:
        dictionaries, resolved_names, all_sheets = read_dictionaries(
            file_bytes
        )
    except ValueError as error:
        st.error(str(error))
        return

    st.success(
        f"Archivo activo: **{file_name}** · "
        f"**{len(all_sheets)} hojas detectadas**"
    )

    detected_count = sum(
        sheet_name is not None
        for sheet_name in resolved_names.values()
    )

    summary_columns = st.columns(3)

    for column, (key, config) in zip(
        summary_columns,
        DICTIONARY_CONFIG.items(),
    ):
        with column:
            sheet_name = resolved_names[key]
            status = (
                f"Hoja: {sheet_name}"
                if sheet_name
                else "No encontrada"
            )
            st.markdown(
                compact_html(
                    f"""
                    <div class="dictionary-card">
                        <div class="dictionary-title">
                            {config["icono"]} {config["titulo"]}
                        </div>
                        <div class="dictionary-caption">{escape_html(status)}</div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    if detected_count < len(DICTIONARY_CONFIG):
        missing = [
            DICTIONARY_CONFIG[key]["titulo"]
            for key, sheet_name in resolved_names.items()
            if sheet_name is None
        ]
        st.info(
            "No se detectaron todos los diccionarios. Faltan: "
            f"**{', '.join(missing)}**."
        )

    tab_cecos, tab_users, tab_ranges, tab_sheets = st.tabs(
        [
            "🏭 CECOS",
            "👥 USUARIOS",
            "📏 RANGOS",
            "📚 Hojas disponibles",
        ]
    )

    with tab_cecos:
        render_dictionary(
            dictionary_key="cecos",
            df=dictionaries["cecos"],
            real_sheet_name=resolved_names["cecos"],
            file_name=file_name,
        )

    with tab_users:
        render_dictionary(
            dictionary_key="usuarios",
            df=dictionaries["usuarios"],
            real_sheet_name=resolved_names["usuarios"],
            file_name=file_name,
        )

    with tab_ranges:
        render_dictionary(
            dictionary_key="rangos",
            df=dictionaries["rangos"],
            real_sheet_name=resolved_names["rangos"],
            file_name=file_name,
        )

    with tab_sheets:
        st.subheader("Hojas disponibles en el Excel")
        sheets_df = pd.DataFrame(
            {
                "N.º": range(1, len(all_sheets) + 1),
                "Nombre de hoja": all_sheets,
                "Normalización": [
                    normalize_sheet_name(sheet)
                    for sheet in all_sheets
                ],
            }
        )
        st.dataframe(
            sheets_df,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Esta vista ayuda a identificar el nombre exacto cuando "
            "un diccionario no fue detectado automáticamente."
        )


def escape_html(value: Any) -> str:
    """Escapa texto para insertarlo de forma segura en HTML."""
    import html
    return html.escape(clean_text(value))


if __name__ == "__main__":
    main()
