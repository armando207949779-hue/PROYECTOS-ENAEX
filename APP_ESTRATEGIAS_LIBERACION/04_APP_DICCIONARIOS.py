# ============================================================
# 04_APP_DICCIONARIOS
# APP_ESTRATEGIAS_LIBERACION
#
# Consulta los diccionarios normalizados del archivo activo:
# - Dic_CECO: CECO | Planta | Centro
# - Dic_Usuarios: Correo | Cargo
# - Dic_Rangos: Orden | Desde | Hasta
#
# La aplicación prioriza los DataFrame disponibles en
# st.session_state y utiliza el Excel original como respaldo.
# ============================================================

from __future__ import annotations

import base64
import html
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
CHILE_TZ = ZoneInfo("America/Santiago")

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
        "titulo": "CECO",
        "icono": "🏭",
        "session_key": "dic_ceco",
        "columns": ["CECO", "Planta", "Centro"],
        "description": "Catálogo simplificado de centros de costo.",
        "aliases": [
            "DIC_CECO",
            "DIC_CECOS",
            "CECO",
            "CECOS",
            "DICCIONARIO_CECO",
            "DICCIONARIO_CECOS",
        ],
    },
    "usuarios": {
        "titulo": "USUARIOS",
        "icono": "👥",
        "session_key": "dic_users",
        "columns": ["Correo", "Cargo"],
        "description": "Catálogo de usuarios y cargos asociados.",
        "aliases": [
            "DIC_USUARIOS",
            "DIC_USUARIO",
            "USUARIOS",
            "USUARIO",
            "DICCIONARIO_USUARIOS",
            "DICCIONARIO_USUARIO",
        ],
    },
    "rangos": {
        "titulo": "RANGOS",
        "icono": "📏",
        "session_key": "dic_rangos",
        "columns": ["Orden", "Desde", "Hasta"],
        "description": "Catálogo de tramos de monto utilizados por el flujo.",
        "aliases": [
            "DIC_RANGOS",
            "DIC_RANGO",
            "RANGOS",
            "RANGO",
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
            }

            .app-logo img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 86px;
                object-fit: contain;
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

            .source-pill {
                display: inline-block;
                padding: 4px 9px;
                border-radius: 999px;
                background: #EFF6FF;
                color: #175CD3;
                border: 1px solid #BFDBFE;
                font-size: .78rem;
                font-weight: 750;
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


# ============================================================
# LOGO Y ENCABEZADO
# ============================================================

def buscar_logo() -> Path | None:
    return next(
        (
            path
            for path in LOGO_CANDIDATES
            if path.exists() and path.is_file()
        ),
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
            mime = (
                "image/png"
                if path.suffix.lower() == ".png"
                else "image/jpeg"
            )

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

    except (OSError, UnicodeError) as error:
        st.warning(f"No fue posible leer el logo: {error}")


def render_header() -> None:
    mostrar_logo()

    st.markdown(
        '<div class="app-title">04 Diccionarios</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="app-subtitle">
            Consulta, filtra y descarga los catálogos activos de CECO,
            usuarios y rangos.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# NORMALIZACIÓN
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

    if text.lower() in {
        "",
        "nan",
        "none",
        "null",
        "<na>",
        "n/a",
        "no usar",
        "—",
        "-",
    }:
        return ""

    return text


def normalize_sheet_name(value: str) -> str:
    normalized = clean_text(value).upper()
    replacements = str.maketrans(
        {
            "Á": "A",
            "É": "E",
            "Í": "I",
            "Ó": "O",
            "Ú": "U",
            "Ü": "U",
            "Ñ": "N",
        }
    )
    normalized = normalized.translate(replacements)
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

    return None


def normalize_dictionary(
    dataframe: pd.DataFrame | None,
    expected_columns: list[str],
) -> pd.DataFrame:
    if dataframe is None:
        return pd.DataFrame(columns=expected_columns)

    result = dataframe.copy()
    result.columns = [
        clean_text(column) or f"Columna_{index + 1}"
        for index, column in enumerate(result.columns)
    ]

    for column in expected_columns:
        if column not in result.columns:
            result[column] = ""

    result = result.loc[:, expected_columns].copy()

    for column in expected_columns:
        result[column] = result[column].map(
            lambda value: clean_text(value)
            if column not in {"Orden", "Desde", "Hasta"}
            else value
        )

    if "Orden" in result.columns:
        result["Orden"] = pd.to_numeric(
            result["Orden"],
            errors="coerce",
        )

    for column in ["Desde", "Hasta"]:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    result = result.dropna(axis=0, how="all")
    result = result[
        result.apply(
            lambda row: any(clean_text(value) for value in row),
            axis=1,
        )
    ]

    if "CECO" in result.columns:
        result = result[result["CECO"].map(clean_text).ne("")]
        result = result.drop_duplicates("CECO", keep="last")

    if "Correo" in result.columns:
        result = result[result["Correo"].map(clean_text).ne("")]
        result = result.drop_duplicates("Correo", keep="last")

    if "Orden" in result.columns:
        result = result.sort_values(
            ["Orden", "Desde", "Hasta"],
            na_position="last",
            kind="stable",
        )

    return result.reset_index(drop=True)


# ============================================================
# OBTENCIÓN DE DATOS
# ============================================================

@st.cache_data(show_spinner=False)
def read_excel_metadata(
    file_bytes: bytes,
) -> tuple[dict[str, pd.DataFrame], dict[str, str | None], list[str]]:
    if not file_bytes:
        return {}, {}, []

    try:
        excel = pd.ExcelFile(BytesIO(file_bytes))
    except Exception:
        return {}, {}, []

    sheet_names = list(excel.sheet_names)
    dictionaries: dict[str, pd.DataFrame] = {}
    resolved_names: dict[str, str | None] = {}

    for key, config in DICTIONARY_CONFIG.items():
        sheet_name = find_sheet_name(
            sheet_names,
            config["aliases"],
        )
        resolved_names[key] = sheet_name

        if sheet_name is None:
            dictionaries[key] = pd.DataFrame(
                columns=config["columns"]
            )
            continue

        try:
            raw = pd.read_excel(
                excel,
                sheet_name=sheet_name,
            )
        except Exception:
            raw = None

        dictionaries[key] = normalize_dictionary(
            raw,
            config["columns"],
        )

    return dictionaries, resolved_names, sheet_names


def get_active_dictionaries() -> tuple[
    dict[str, pd.DataFrame],
    dict[str, str],
    list[str],
]:
    data = st.session_state.get(SESSION_DATA_KEY)
    file_bytes = st.session_state.get(SESSION_FILE_BYTES_KEY, b"")

    fallback, resolved_names, sheet_names = read_excel_metadata(
        file_bytes
    )

    dictionaries: dict[str, pd.DataFrame] = {}
    sources: dict[str, str] = {}

    for key, config in DICTIONARY_CONFIG.items():
        session_df = (
            data.get(config["session_key"])
            if isinstance(data, dict)
            else None
        )

        normalized_session = normalize_dictionary(
            session_df
            if isinstance(session_df, pd.DataFrame)
            else None,
            config["columns"],
        )

        if not normalized_session.empty:
            dictionaries[key] = normalized_session
            sources[key] = "Base activa"
        else:
            dictionaries[key] = fallback.get(
                key,
                pd.DataFrame(columns=config["columns"]),
            )
            sources[key] = (
                f"Excel · {resolved_names.get(key)}"
                if resolved_names.get(key)
                else "No disponible"
            )

    return dictionaries, sources, sheet_names


# ============================================================
# BÚSQUEDA Y FILTROS
# ============================================================

def apply_global_search(
    dataframe: pd.DataFrame,
    search_text: str,
) -> pd.DataFrame:
    search = clean_text(search_text).casefold()

    if not search:
        return dataframe.copy()

    text_df = dataframe.fillna("").astype(str)

    mask = text_df.apply(
        lambda row: row.str.casefold().str.contains(
            re.escape(search),
            regex=True,
            na=False,
        ).any(),
        axis=1,
    )

    return dataframe.loc[mask].copy()


def suitable_filter_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    result: list[str] = []

    for column in dataframe.columns:
        unique_count = dataframe[column].nunique(dropna=True)

        if 1 < unique_count <= 150:
            result.append(column)

    return result


def apply_column_filters(
    dataframe: pd.DataFrame,
    dictionary_key: str,
) -> pd.DataFrame:
    result = dataframe.copy()
    columns = suitable_filter_columns(result)

    if not columns:
        st.caption(
            "No se detectaron columnas apropiadas para filtros rápidos."
        )
        return result

    selected_columns = st.multiselect(
        "Columnas para filtrar",
        options=columns,
        default=[],
        key=f"dict_{dictionary_key}_filter_columns_v02",
    )

    for column in selected_columns:
        values = sorted(
            {
                clean_text(value)
                for value in result[column].tolist()
                if clean_text(value)
            },
            key=str.casefold,
        )

        selected_values = st.multiselect(
            f"Valores de {column}",
            options=values,
            default=[],
            key=f"dict_{dictionary_key}_{column}_values_v02",
        )

        if selected_values:
            result = result[
                result[column]
                .map(clean_text)
                .isin(selected_values)
            ].copy()

    return result


# ============================================================
# EXPORTACIÓN
# ============================================================

def safe_file_part(value: str) -> str:
    return re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        clean_text(value),
    ).strip("_") or "DICCIONARIO"


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(
        index=False,
    ).encode("utf-8-sig")


def dataframe_to_excel_bytes(
    dataframe: pd.DataFrame,
    sheet_name: str,
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name[:31]

    headers = list(dataframe.columns)

    for column_index, header in enumerate(headers, start=1):
        sheet.cell(1, column_index, header)

    for row_index, row in enumerate(
        dataframe.itertuples(index=False, name=None),
        start=2,
    ):
        for column_index, value in enumerate(row, start=1):
            try:
                if pd.isna(value):
                    value = None
            except (TypeError, ValueError):
                pass

            sheet.cell(row_index, column_index, value)

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="17365D",
    )
    header_font = Font(
        name="Calibri",
        size=11,
        bold=True,
        color="FFFFFF",
    )
    thin = Side(style="thin", color="D0D5DD")
    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin,
    )

    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    sheet.row_dimensions[1].height = 28
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.sheet_view.showGridLines = False

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

    header_index = {
        clean_text(cell.value): cell.column
        for cell in sheet[1]
    }

    for column_name in ["Orden", "Desde", "Hasta"]:
        column_index = header_index.get(column_name)

        if column_index:
            for row_index in range(2, sheet.max_row + 1):
                sheet.cell(
                    row_index,
                    column_index,
                ).number_format = "#,##0"

    for column_index in range(1, sheet.max_column + 1):
        values = [
            clean_text(
                sheet.cell(row_index, column_index).value
            )
            for row_index in range(
                1,
                min(sheet.max_row, 250) + 1,
            )
        ]
        width = min(
            max(
                max((len(value) for value in values), default=8) + 2,
                12,
            ),
            42,
        )
        sheet.column_dimensions[
            get_column_letter(column_index)
        ].width = width

    if sheet.max_row >= 2 and sheet.max_column >= 1:
        table_name = (
            "Tabla"
            + safe_file_part(sheet_name).replace("-", "_")
        )[:250]
        reference = (
            f"A1:{get_column_letter(sheet.max_column)}{sheet.max_row}"
        )
        table = Table(
            displayName=table_name,
            ref=reference,
        )
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        sheet.add_table(table)

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


# ============================================================
# COMPONENTES DE INTERFAZ
# ============================================================

def escape_html(value: Any) -> str:
    return html.escape(clean_text(value))


def render_metrics(
    original: pd.DataFrame,
    filtered: pd.DataFrame,
) -> None:
    duplicate_rows = int(filtered.duplicated().sum())
    empty_cells = int(
        filtered.apply(
            lambda column: column.map(clean_text).eq("").sum()
        ).sum()
    )

    columns = st.columns(4)
    metrics = [
        ("Registros totales", len(original)),
        ("Registros visibles", len(filtered)),
        ("Columnas", len(filtered.columns)),
        ("Duplicados visibles", duplicate_rows),
    ]

    for column, (label, value) in zip(columns, metrics):
        with column:
            st.markdown(
                compact_html(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{escape_html(label)}</div>
                        <div class="metric-value">{value:,}</div>
                    </div>
                    """
                ).replace(",", "."),
                unsafe_allow_html=True,
            )

    if empty_cells:
        st.caption(
            f"La vista contiene {empty_cells:,} celdas vacías."
            .replace(",", ".")
        )


def render_dictionary(
    dictionary_key: str,
    dataframe: pd.DataFrame,
    source_label: str,
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
                    {escape_html(config["description"])}
                </div>
                <div style="margin-top:9px;">
                    <span class="source-pill">
                        Fuente: {escape_html(source_label)}
                    </span>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    if dataframe.empty:
        st.warning(
            f"No hay registros disponibles para {config['titulo']}."
        )
        return

    search_text = st.text_input(
        "Buscar en todas las columnas",
        placeholder=(
            "Escribe un CECO, planta, correo, cargo o monto..."
        ),
        key=f"dict_{dictionary_key}_search_v02",
    )

    searched = apply_global_search(
        dataframe,
        search_text,
    )

    with st.expander(
        "Filtros avanzados",
        expanded=False,
    ):
        filtered = apply_column_filters(
            searched,
            dictionary_key,
        )

    render_metrics(dataframe, filtered)

    st.markdown("#### Resultados")

    if filtered.empty:
        st.warning(
            "No hay registros que coincidan con la búsqueda y filtros."
        )
    else:
        display = filtered.copy()

        for column in ["Orden", "Desde", "Hasta"]:
            if column in display.columns:
                display[column] = display[column].map(
                    lambda value: (
                        f"{int(value):,}".replace(",", ".")
                        if pd.notna(value)
                        else ""
                    )
                )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            height=min(
                680,
                max(280, 35 * (len(display) + 2)),
            ),
        )

    base_name = Path(
        file_name or "BBDD_LIBERACION.xlsx"
    ).stem
    timestamp = datetime.now(CHILE_TZ).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    safe_title = safe_file_part(config["titulo"])

    excel_column, csv_column = st.columns(2)

    with excel_column:
        st.download_button(
            "⬇️ Descargar vista en Excel",
            data=dataframe_to_excel_bytes(
                filtered,
                config["titulo"],
            ),
            file_name=(
                f"{base_name}_{safe_title}_{timestamp}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key=f"dict_{dictionary_key}_excel_v02",
        )

    with csv_column:
        st.download_button(
            "⬇️ Descargar vista en CSV",
            data=dataframe_to_csv_bytes(filtered),
            file_name=(
                f"{base_name}_{safe_title}_{timestamp}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
            key=f"dict_{dictionary_key}_csv_v02",
        )

    with st.expander(
        "Calidad y estructura de columnas",
        expanded=False,
    ):
        info = pd.DataFrame(
            {
                "Columna": dataframe.columns,
                "Tipo detectado": [
                    str(dataframe[column].dtype)
                    for column in dataframe.columns
                ],
                "Valores no vacíos": [
                    int(
                        dataframe[column]
                        .map(clean_text)
                        .ne("")
                        .sum()
                    )
                    for column in dataframe.columns
                ],
                "Valores únicos": [
                    int(
                        dataframe[column]
                        .map(clean_text)
                        .replace("", pd.NA)
                        .nunique(dropna=True)
                    )
                    for column in dataframe.columns
                ],
            }
        )

        st.dataframe(
            info,
            use_container_width=True,
            hide_index=True,
        )


def render_no_file() -> None:
    st.warning(
        "No hay una base activa. Primero carga el Excel desde "
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
        st.info(
            "Selecciona **01 Cargar archivo** desde el menú lateral."
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()

    data = st.session_state.get(SESSION_DATA_KEY)
    file_bytes = st.session_state.get(
        SESSION_FILE_BYTES_KEY,
        b"",
    )

    if not isinstance(data, dict) and not file_bytes:
        render_no_file()
        return

    file_name = st.session_state.get(
        SESSION_FILE_KEY,
        "BBDD_LIBERACION.xlsx",
    )

    dictionaries, sources, sheet_names = get_active_dictionaries()

    st.success(
        (
            f"Archivo activo: **{file_name}** · "
            f"**{sum(len(df) for df in dictionaries.values()):,} "
            "registros de diccionarios**"
        ).replace(",", ".")
    )

    summary_columns = st.columns(3)

    for column, (key, config) in zip(
        summary_columns,
        DICTIONARY_CONFIG.items(),
    ):
        dataframe = dictionaries[key]

        with column:
            st.markdown(
                compact_html(
                    f"""
                    <div class="dictionary-card">
                        <div class="dictionary-title">
                            {config["icono"]} {config["titulo"]}
                        </div>
                        <div class="dictionary-caption">
                            {len(dataframe):,} registros ·
                            {len(dataframe.columns):,} columnas
                        </div>
                        <div class="dictionary-caption">
                            {escape_html(sources[key])}
                        </div>
                    </div>
                    """
                ).replace(",", "."),
                unsafe_allow_html=True,
            )

    tab_cecos, tab_users, tab_ranges, tab_sheets = st.tabs(
        [
            "🏭 CECO",
            "👥 USUARIOS",
            "📏 RANGOS",
            "📚 Hojas del Excel",
        ]
    )

    with tab_cecos:
        render_dictionary(
            "cecos",
            dictionaries["cecos"],
            sources["cecos"],
            file_name,
        )

    with tab_users:
        render_dictionary(
            "usuarios",
            dictionaries["usuarios"],
            sources["usuarios"],
            file_name,
        )

    with tab_ranges:
        render_dictionary(
            "rangos",
            dictionaries["rangos"],
            sources["rangos"],
            file_name,
        )

    with tab_sheets:
        st.subheader("Hojas disponibles en el Excel original")

        if not sheet_names:
            st.info(
                "No fue posible inspeccionar las hojas del archivo original. "
                "Los diccionarios activos continúan disponibles en memoria."
            )
        else:
            sheets_df = pd.DataFrame(
                {
                    "N.º": range(1, len(sheet_names) + 1),
                    "Nombre de hoja": sheet_names,
                    "Nombre normalizado": [
                        normalize_sheet_name(sheet)
                        for sheet in sheet_names
                    ],
                }
            )

            st.dataframe(
                sheets_df,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "Esta pestaña representa las hojas del archivo cargado. "
                "Los datos mostrados en las otras pestañas priorizan la "
                "base activa normalizada."
            )


if __name__ == "__main__":
    main()
