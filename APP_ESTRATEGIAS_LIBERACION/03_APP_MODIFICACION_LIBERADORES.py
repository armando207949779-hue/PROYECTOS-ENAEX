# ============================================================
# 03_APP_MODIFICACION_LIBERADORES
# APP_ESTRATEGIAS_LIBERACION
#
# Modos:
# 1. Editar un CECO en formato tabla
#    - Modificar celdas
#    - Agregar filas
#    - Eliminar filas
#    - Reordenar filas mediante la columna Orden
#
# 2. Reemplazar una persona en toda la base
#    - Indica en cuántos CECO participa
#    - Indica filas y posiciones afectadas
#    - Reemplaza todas sus apariciones
#
# Los cambios quedan disponibles en st.session_state y se puede
# descargar el Excel actualizado con fecha y hora en el nombre.
# ============================================================

from __future__ import annotations

import base64
import hashlib
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows


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

SESSION_WORKING_KEY = "mod_liberadores_working_df_v03"
SESSION_BACKUP_KEY = "mod_liberadores_backup_df_v03"
SESSION_SIGNATURE_KEY = "mod_liberadores_source_signature_v03"
SESSION_HISTORY_KEY = "mod_liberadores_history_v03"
SESSION_DOWNLOAD_KEY = "mod_liberadores_download_v03"
SESSION_DOWNLOAD_NAME_KEY = "mod_liberadores_download_name_v03"

LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]

FLOW_COLUMNS = [
    "CECO",
    "Planta",
    "Desde",
    "Hasta",
    "TipoDoc",
    "Lib1",
    "Lib2",
    "Lib3",
    "Lib4",
    "Lib5",
    "N_EO",
    "N_CD",
    "Match",
    "FuenteCD",
]

TABLE_COLUMNS = [
    "Orden",
    "CECO",
    "Planta",
    "Desde",
    "Hasta",
    "TipoDoc",
    "Lib1",
    "Lib2",
    "Lib3",
    "Lib4",
    "Lib5",
]

DOC_ORDER = {"AZNB": 0, "AZSR": 1}
DOC_LABEL = {
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
}

LS_LABEL = "Liberador Servicios"


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

            .question-card {
                border: 2px solid #93C5FD;
                border-radius: 16px;
                padding: 17px 19px;
                background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
                margin: .8rem 0 1rem;
            }

            .question-title {
                color: #17365D;
                font-size: 1.18rem;
                font-weight: 850;
            }

            .question-help {
                color: #64748B;
                font-size: .9rem;
                margin-top: 5px;
            }

            .mode-card {
                border: 1px solid #D0D5DD;
                border-radius: 14px;
                padding: 15px;
                background: #FFFFFF;
                min-height: 125px;
            }

            .metric-card {
                border: 1px solid #D0D5DD;
                border-radius: 13px;
                padding: 13px 15px;
                background: #FFFFFF;
                height: 100%;
            }

            .metric-label {
                color: #64748B;
                font-size: .78rem;
                font-weight: 750;
                text-transform: uppercase;
            }

            .metric-value {
                color: #17365D;
                font-size: 1.55rem;
                font-weight: 850;
                margin-top: 4px;
            }

            .material-legend {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 999px;
                background: #FFF1F0;
                color: #B42318;
                font-weight: 750;
                margin-right: 7px;
            }

            .service-legend {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 999px;
                background: #EFF8FF;
                color: #175CD3;
                font-weight: 750;
            }

            div[data-testid="stDataFrame"],
            div[data-testid="stDataEditor"] {
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
        '<div class="app-title">03 Modificación de Liberadores</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="app-subtitle">
            Edita un CECO en formato tabla o reemplaza una persona
            en todos los CECO donde participa.
        </div>
        """,
        unsafe_allow_html=True,
    )


def question(title: str, help_text: str) -> None:
    st.markdown(
        compact_html(
            f"""
            <div class="question-card">
                <div class="question-title">{title}</div>
                <div class="question-help">{help_text}</div>
            </div>
            """
        ),
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
    if text.lower() in {"", "nan", "none", "null", "—", "-"}:
        return ""
    return text


def strip_user(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text == LS_LABEL:
        return LS_LABEL

    # Quita un cargo visual agregado como correo (CARGO).
    match = re.match(r"^(.*?)(?:\s+\([^)]+\))?$", text)
    return match.group(1).strip() if match else text


def parse_number(value: Any, default: float = 0.0) -> float:
    text = clean_text(value)
    if not text:
        return default

    text = text.replace(" ", "")

    if re.fullmatch(r"[-+]?\d{1,3}(?:\.\d{3})+", text):
        text = text.replace(".", "")
    elif "," in text and "." not in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return default


def format_bound(value: Any) -> str:
    number = parse_number(value, default=0.0)
    if number >= 1e12:
        return "1E+12"
    return f"{int(number):,}".replace(",", ".")


def normalize_flow(df: pd.DataFrame) -> pd.DataFrame:
    flow = df.copy()
    flow.columns = [str(column).strip() for column in flow.columns]

    for column in FLOW_COLUMNS:
        if column not in flow.columns:
            flow[column] = ""

    flow = flow.loc[:, FLOW_COLUMNS].copy()

    for column in ["CECO", "Planta", "Match", "FuenteCD"]:
        flow[column] = flow[column].map(clean_text)

    flow["TipoDoc"] = flow["TipoDoc"].map(clean_text).str.upper()

    for column in LIB_COLS:
        flow[column] = flow[column].map(strip_user)

    for column in ["N_EO", "N_CD"]:
        flow[column] = (
            pd.to_numeric(flow[column], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    flow = flow[flow["CECO"].ne("")].reset_index(drop=True)
    flow.insert(0, "_ID_FILA", range(1, len(flow) + 1))
    return flow


def file_signature(file_name: str, file_bytes: bytes, rows: int) -> str:
    digest = hashlib.sha1(file_bytes[:100000]).hexdigest() if file_bytes else "no-bytes"
    return f"{file_name}|{len(file_bytes)}|{rows}|{digest}"


def cargo_dictionary(data: dict[str, pd.DataFrame]) -> dict[str, str]:
    users = data.get("dic_users", pd.DataFrame())
    if not isinstance(users, pd.DataFrame) or users.empty:
        return {}

    email_col = next(
        (
            column
            for column in users.columns
            if str(column).strip().lower() in {"correo", "email", "mail"}
        ),
        None,
    )
    cargo_col = next(
        (
            column
            for column in users.columns
            if str(column).strip().lower() in {"cargo", "rol", "role"}
        ),
        None,
    )

    if email_col is None:
        return {}

    result: dict[str, str] = {}
    for _, row in users.iterrows():
        email = strip_user(row.get(email_col, ""))
        cargo = clean_text(row.get(cargo_col, "")) if cargo_col else ""
        if email:
            result[email.lower()] = cargo

    return result


def display_user(value: Any, data: dict[str, pd.DataFrame]) -> str:
    email = strip_user(value)
    if not email:
        return ""
    if email == LS_LABEL:
        return LS_LABEL

    cargo = cargo_dictionary(data).get(email.lower(), "")
    return f"{email} ({cargo})" if cargo else email


def unique_users(flow: pd.DataFrame) -> list[str]:
    values = {
        strip_user(value)
        for column in LIB_COLS
        for value in flow[column].tolist()
        if strip_user(value)
    }
    return sorted(values, key=str.lower)


def row_contains_user(row: pd.Series, user: str) -> bool:
    target = strip_user(user).lower()
    return any(
        strip_user(row.get(column, "")).lower() == target
        for column in LIB_COLS
    )


def user_occurrences(flow: pd.DataFrame, user: str) -> pd.DataFrame:
    target = strip_user(user).lower()
    records: list[dict[str, Any]] = []

    for _, row in flow.iterrows():
        for column in LIB_COLS:
            current = strip_user(row.get(column, ""))
            if current.lower() != target:
                continue

            records.append(
                {
                    "_ID_FILA": row["_ID_FILA"],
                    "CECO": row["CECO"],
                    "Planta": row["Planta"],
                    "Desde": row["Desde"],
                    "Hasta": row["Hasta"],
                    "TipoDoc": row["TipoDoc"],
                    "Posición": column,
                    "Liberador": current,
                }
            )

    return pd.DataFrame(records)


def styled_preview(df: pd.DataFrame):
    visible = df.copy()

    def style_row(row: pd.Series) -> list[str]:
        doc = clean_text(row.get("TipoDoc")).upper()
        if doc == "AZNB":
            style = "background-color:#FFF1F0;color:#7A271A;"
        elif doc == "AZSR":
            style = "background-color:#EFF8FF;color:#1849A9;"
        else:
            style = ""
        return [style] * len(row)

    formatter = {
        "Desde": lambda value: format_bound(value),
        "Hasta": lambda value: format_bound(value),
    }

    return visible.style.apply(style_row, axis=1).format(formatter)


# ============================================================
# ESTADO
# ============================================================

def initialize_state(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
) -> None:
    normalized = normalize_flow(data["flujo"])
    signature = file_signature(file_name, file_bytes, len(normalized))

    if (
        SESSION_WORKING_KEY not in st.session_state
        or st.session_state.get(SESSION_SIGNATURE_KEY) != signature
    ):
        st.session_state[SESSION_WORKING_KEY] = normalized
        st.session_state[SESSION_BACKUP_KEY] = normalized.copy(deep=True)
        st.session_state[SESSION_SIGNATURE_KEY] = signature
        st.session_state[SESSION_HISTORY_KEY] = []
        st.session_state.pop(SESSION_DOWNLOAD_KEY, None)
        st.session_state.pop(SESSION_DOWNLOAD_NAME_KEY, None)


def get_working_flow() -> pd.DataFrame:
    value = st.session_state.get(SESSION_WORKING_KEY)
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=True)
    return pd.DataFrame(columns=["_ID_FILA", *FLOW_COLUMNS])


def set_working_flow(flow: pd.DataFrame) -> None:
    result = flow.copy(deep=True).reset_index(drop=True)

    if "_ID_FILA" not in result.columns:
        result.insert(0, "_ID_FILA", range(1, len(result) + 1))
    else:
        result["_ID_FILA"] = range(1, len(result) + 1)

    st.session_state[SESSION_WORKING_KEY] = result

    data = st.session_state.get(SESSION_DATA_KEY)
    if isinstance(data, dict):
        updated = dict(data)
        updated["flujo"] = (
            result.drop(columns=["_ID_FILA"], errors="ignore")
            .loc[:, FLOW_COLUMNS]
            .copy()
        )
        st.session_state[SESSION_DATA_KEY] = updated


def add_history(records: list[dict[str, Any]]) -> None:
    history = list(st.session_state.get(SESSION_HISTORY_KEY, []))
    history.extend(records)
    st.session_state[SESSION_HISTORY_KEY] = history


# ============================================================
# EXCEL
# ============================================================

def generate_download_name(original_name: str) -> str:
    stem = Path(original_name or "BBDD_FLUJO_LIBERACION.xlsx").stem
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{stem}_MODIFICADO_{timestamp}.xlsx"


def build_excel(
    original_bytes: bytes,
    flow: pd.DataFrame,
    history: list[dict[str, Any]],
) -> bytes:
    if not original_bytes:
        raise ValueError(
            "No se encontraron los bytes del Excel original. "
            "Vuelve a cargar el archivo desde 01 Cargar archivo."
        )

    try:
        workbook = load_workbook(BytesIO(original_bytes))
    except Exception as error:
        raise ValueError(
            "No fue posible abrir el archivo Excel original."
        ) from error

    if "Flujo" in workbook.sheetnames:
        sheet = workbook["Flujo"]
    else:
        sheet = workbook.create_sheet("Flujo")

    if sheet.max_row:
        sheet.delete_rows(1, sheet.max_row)

    export_flow = (
        flow.drop(columns=["_ID_FILA"], errors="ignore")
        .loc[:, FLOW_COLUMNS]
        .copy()
    )

    for row_index, values in enumerate(
        dataframe_to_rows(export_flow, index=False, header=True),
        start=1,
    ):
        for column_index, value in enumerate(values, start=1):
            sheet.cell(
                row=row_index,
                column=column_index,
                value=value,
            )

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    if "Cambios" in workbook.sheetnames:
        changes_sheet = workbook["Cambios"]
        if changes_sheet.max_row:
            changes_sheet.delete_rows(1, changes_sheet.max_row)
    else:
        changes_sheet = workbook.create_sheet("Cambios")

    history_df = pd.DataFrame(history)
    if history_df.empty:
        history_df = pd.DataFrame(
            columns=[
                "FechaHora",
                "Usuario",
                "Modo",
                "CECO",
                "TipoDoc",
                "Desde",
                "Hasta",
                "Campo",
                "ValorAntes",
                "ValorDespues",
                "Motivo",
            ]
        )

    for row_index, values in enumerate(
        dataframe_to_rows(history_df, index=False, header=True),
        start=1,
    ):
        for column_index, value in enumerate(values, start=1):
            changes_sheet.cell(
                row=row_index,
                column=column_index,
                value=value,
            )

    changes_sheet.freeze_panes = "A2"
    changes_sheet.auto_filter.ref = changes_sheet.dimensions

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def refresh_download(
    file_name: str,
    file_bytes: bytes,
) -> None:
    flow = get_working_flow()
    history = list(st.session_state.get(SESSION_HISTORY_KEY, []))

    generated = build_excel(
        original_bytes=file_bytes,
        flow=flow,
        history=history,
    )

    st.session_state[SESSION_DOWNLOAD_KEY] = generated
    st.session_state[SESSION_DOWNLOAD_NAME_KEY] = generate_download_name(
        file_name
    )


# ============================================================
# COMPARACIÓN DE TABLAS
# ============================================================

def row_key(row: pd.Series) -> tuple[str, str, float, float]:
    return (
        clean_text(row.get("CECO")),
        clean_text(row.get("TipoDoc")).upper(),
        parse_number(row.get("Desde")),
        parse_number(row.get("Hasta")),
    )


def compare_ceco_tables(
    before: pd.DataFrame,
    after: pd.DataFrame,
    actor: str,
    reason: str,
) -> list[dict[str, Any]]:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records: list[dict[str, Any]] = []

    before_map = {
        row_key(row): row
        for _, row in before.iterrows()
    }
    after_map = {
        row_key(row): row
        for _, row in after.iterrows()
    }

    all_keys = set(before_map) | set(after_map)

    for key in sorted(all_keys):
        old_row = before_map.get(key)
        new_row = after_map.get(key)

        if old_row is None and new_row is not None:
            records.append(
                {
                    "FechaHora": timestamp,
                    "Usuario": actor or "anonimo",
                    "Modo": "Edición puntual CECO",
                    "CECO": new_row["CECO"],
                    "TipoDoc": new_row["TipoDoc"],
                    "Desde": new_row["Desde"],
                    "Hasta": new_row["Hasta"],
                    "Campo": "Fila",
                    "ValorAntes": "No existía",
                    "ValorDespues": "Fila agregada",
                    "Motivo": reason or "Edición desde app 03",
                }
            )
            continue

        if old_row is not None and new_row is None:
            records.append(
                {
                    "FechaHora": timestamp,
                    "Usuario": actor or "anonimo",
                    "Modo": "Edición puntual CECO",
                    "CECO": old_row["CECO"],
                    "TipoDoc": old_row["TipoDoc"],
                    "Desde": old_row["Desde"],
                    "Hasta": old_row["Hasta"],
                    "Campo": "Fila",
                    "ValorAntes": "Fila existente",
                    "ValorDespues": "Fila eliminada",
                    "Motivo": reason or "Edición desde app 03",
                }
            )
            continue

        assert old_row is not None and new_row is not None

        for column in [
            "Planta",
            "Desde",
            "Hasta",
            "TipoDoc",
            *LIB_COLS,
            "N_EO",
            "N_CD",
            "Match",
            "FuenteCD",
        ]:
            old_value = clean_text(old_row.get(column, ""))
            new_value = clean_text(new_row.get(column, ""))

            if old_value == new_value:
                continue

            records.append(
                {
                    "FechaHora": timestamp,
                    "Usuario": actor or "anonimo",
                    "Modo": "Edición puntual CECO",
                    "CECO": new_row["CECO"],
                    "TipoDoc": new_row["TipoDoc"],
                    "Desde": new_row["Desde"],
                    "Hasta": new_row["Hasta"],
                    "Campo": column,
                    "ValorAntes": old_value or "—",
                    "ValorDespues": new_value or "—",
                    "Motivo": reason or "Edición desde app 03",
                }
            )

    return records


# ============================================================
# MODO 1: EDITAR CECO
# ============================================================

def prepare_ceco_editor(flow: pd.DataFrame, ceco: str) -> pd.DataFrame:
    subset = flow[flow["CECO"].eq(ceco)].copy()

    subset["_DOC_ORDER"] = (
        subset["TipoDoc"]
        .map(DOC_ORDER)
        .fillna(99)
    )
    subset["_DESDE_ORDER"] = subset["Desde"].map(parse_number)

    subset = subset.sort_values(
        ["_DOC_ORDER", "_DESDE_ORDER", "_ID_FILA"]
    ).reset_index(drop=True)

    subset.insert(0, "Orden", range(1, len(subset) + 1))
    return subset.loc[:, TABLE_COLUMNS]


def validate_edited_ceco(
    edited: pd.DataFrame,
    selected_ceco: str,
) -> tuple[pd.DataFrame | None, list[str]]:
    errors: list[str] = []
    result = edited.copy()

    for column in TABLE_COLUMNS:
        if column not in result.columns:
            result[column] = ""

    result = result.loc[:, TABLE_COLUMNS].copy()
    result = result.dropna(how="all").reset_index(drop=True)

    result["CECO"] = result["CECO"].map(clean_text)
    result["CECO"] = result["CECO"].replace("", selected_ceco)

    result["Planta"] = result["Planta"].map(clean_text)
    result["TipoDoc"] = result["TipoDoc"].map(clean_text).str.upper()

    for column in LIB_COLS:
        result[column] = result[column].map(strip_user)

    result["Orden"] = (
        pd.to_numeric(result["Orden"], errors="coerce")
        .fillna(999999)
    )

    result["Desde"] = result["Desde"].map(
        lambda value: parse_number(value, default=0.0)
    )
    result["Hasta"] = result["Hasta"].map(
        lambda value: parse_number(value, default=0.0)
    )

    invalid_ceco = result[~result["CECO"].eq(selected_ceco)]
    if not invalid_ceco.empty:
        errors.append(
            "Todas las filas deben mantener el CECO seleccionado."
        )

    invalid_doc = result[~result["TipoDoc"].isin(["AZNB", "AZSR"])]
    if not invalid_doc.empty:
        errors.append(
            "TipoDoc solo puede ser AZNB o AZSR."
        )

    invalid_range = result[result["Hasta"] < result["Desde"]]
    if not invalid_range.empty:
        errors.append(
            "Existen filas donde Hasta es menor que Desde."
        )

    duplicate_ranges = result.duplicated(
        subset=["CECO", "TipoDoc", "Desde", "Hasta"],
        keep=False,
    )
    if duplicate_ranges.any():
        errors.append(
            "Existen tramos duplicados para el mismo CECO y TipoDoc."
        )

    if errors:
        return None, errors

    result["_DOC_ORDER"] = result["TipoDoc"].map(DOC_ORDER).fillna(99)
    result = result.sort_values(
        ["_DOC_ORDER", "Orden", "Desde", "Hasta"]
    ).reset_index(drop=True)

    return result, []


def rebuild_ceco_rows(
    original_ceco_rows: pd.DataFrame,
    edited: pd.DataFrame,
) -> pd.DataFrame:
    metadata_map: dict[tuple[str, float, float], pd.Series] = {}

    for _, row in original_ceco_rows.iterrows():
        key = (
            clean_text(row["TipoDoc"]).upper(),
            parse_number(row["Desde"]),
            parse_number(row["Hasta"]),
        )
        metadata_map[key] = row

    rows: list[dict[str, Any]] = []

    for _, row in edited.iterrows():
        key = (
            clean_text(row["TipoDoc"]).upper(),
            parse_number(row["Desde"]),
            parse_number(row["Hasta"]),
        )
        original = metadata_map.get(key)

        libs = [strip_user(row[column]) for column in LIB_COLS]
        non_empty_count = sum(bool(value) for value in libs)

        if original is not None:
            n_eo = int(original.get("N_EO", 0) or 0)
            n_cd = int(original.get("N_CD", 0) or 0)
            match = clean_text(original.get("Match", ""))
            source_cd = clean_text(original.get("FuenteCD", ""))
        else:
            # Para filas nuevas se asume que los liberadores son CD,
            # salvo que el usuario ajuste luego los campos avanzados.
            n_eo = 0
            n_cd = non_empty_count
            match = "NO"
            source_cd = ""

        if n_eo + n_cd != non_empty_count:
            n_cd = max(0, non_empty_count - n_eo)

        rows.append(
            {
                "_ID_FILA": 0,
                "CECO": clean_text(row["CECO"]),
                "Planta": clean_text(row["Planta"]),
                "Desde": row["Desde"],
                "Hasta": row["Hasta"],
                "TipoDoc": clean_text(row["TipoDoc"]).upper(),
                **{
                    column: strip_user(row[column])
                    for column in LIB_COLS
                },
                "N_EO": n_eo,
                "N_CD": n_cd,
                "Match": match,
                "FuenteCD": source_cd,
            }
        )

    return pd.DataFrame(rows, columns=["_ID_FILA", *FLOW_COLUMNS])


def render_local_edit_mode(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
) -> None:
    flow = get_working_flow()

    question(
        "¿Qué CECO quieres modificar?",
        (
            "Al seleccionar el CECO aparecerán todas sus reglas de "
            "material y servicio en una tabla editable."
        ),
    )

    ceco_map = (
        flow[["CECO", "Planta"]]
        .drop_duplicates()
        .sort_values(["CECO", "Planta"])
        .groupby("CECO", as_index=False)
        .first()
    )
    plant_by_ceco = dict(zip(ceco_map["CECO"], ceco_map["Planta"]))

    selected_ceco = st.selectbox(
        "Buscar CECO",
        options=ceco_map["CECO"].tolist(),
        format_func=lambda value: (
            f"{value} | {plant_by_ceco.get(value, '')}"
            if plant_by_ceco.get(value, "")
            else value
        ),
        key="local_selected_ceco_v03",
    )

    current_rows = flow[flow["CECO"].eq(selected_ceco)].copy()
    editor_source = prepare_ceco_editor(flow, selected_ceco)

    st.markdown(
        """
        <span class="material-legend">Material · AZNB</span>
        <span class="service-legend">Servicio · AZSR</span>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Edita directamente las celdas. Usa `+` para agregar filas, "
        "el control de eliminación del editor para borrar y la columna "
        "`Orden` para cambiar el orden de las filas."
    )

    editor_key = (
        f"ceco_editor_{selected_ceco}_"
        f"{len(current_rows)}_"
        f"{int(current_rows['_ID_FILA'].sum())}"
    )

    edited = st.data_editor(
        editor_source,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        height=min(650, max(320, 38 * (len(editor_source) + 3))),
        column_config={
            "Orden": st.column_config.NumberColumn(
                "Orden",
                help="Número utilizado para ordenar las filas al guardar.",
                min_value=1,
                step=1,
                width="small",
            ),
            "CECO": st.column_config.TextColumn(
                "CECO",
                disabled=True,
                width="medium",
            ),
            "Planta": st.column_config.TextColumn(
                "Planta",
                width="medium",
            ),
            "Desde": st.column_config.NumberColumn(
                "Desde",
                min_value=0,
                step=1,
                format="%.0f",
                width="medium",
            ),
            "Hasta": st.column_config.NumberColumn(
                "Hasta",
                min_value=0,
                step=1,
                format="%.0f",
                width="medium",
            ),
            "TipoDoc": st.column_config.SelectboxColumn(
                "TipoDoc",
                options=["AZNB", "AZSR"],
                required=True,
                width="small",
            ),
            **{
                column: st.column_config.TextColumn(
                    column,
                    help="Correo del liberador.",
                    width="large",
                )
                for column in LIB_COLS
            },
        },
        key=editor_key,
    )

    validated, errors = validate_edited_ceco(
        edited=edited,
        selected_ceco=selected_ceco,
    )

    if errors:
        for error in errors:
            st.error(error)

    if validated is not None:
        st.markdown("#### Vista previa ordenada")
        preview = validated.drop(columns=["Orden"], errors="ignore")
        st.dataframe(
            styled_preview(preview),
            use_container_width=True,
            hide_index=True,
            height=min(520, max(230, 36 * (len(preview) + 2))),
        )

    question(
        "¿Quién modifica y cuál es el motivo?",
        "Los datos quedarán registrados en la hoja Cambios.",
    )

    col_actor, col_reason = st.columns(2)
    with col_actor:
        actor = st.text_input(
            "Usuario",
            placeholder="nombre.apellido",
            key="local_actor_v03",
        )
    with col_reason:
        reason = st.text_input(
            "Motivo",
            placeholder="Cambio de liberadores, ajuste de flujo...",
            key="local_reason_v03",
        )

    save_clicked = st.button(
        "💾 Guardar cambios del CECO",
        type="primary",
        use_container_width=True,
        disabled=validated is None,
        key="local_save_v03",
    )

    if save_clicked and validated is not None:
        rebuilt = rebuild_ceco_rows(current_rows, validated)

        remaining = flow[~flow["CECO"].eq(selected_ceco)].copy()
        updated = pd.concat(
            [remaining, rebuilt],
            ignore_index=True,
        )

        updated["_DOC_ORDER"] = (
            updated["TipoDoc"].map(DOC_ORDER).fillna(99)
        )
        updated["_DESDE_ORDER"] = updated["Desde"].map(parse_number)
        updated = (
            updated.sort_values(
                ["CECO", "_DOC_ORDER", "_DESDE_ORDER"]
            )
            .drop(columns=["_DOC_ORDER", "_DESDE_ORDER"])
            .reset_index(drop=True)
        )

        history = compare_ceco_tables(
            before=current_rows.drop(
                columns=["_ID_FILA"],
                errors="ignore",
            ),
            after=rebuilt.drop(
                columns=["_ID_FILA"],
                errors="ignore",
            ),
            actor=actor,
            reason=reason,
        )

        set_working_flow(updated)
        add_history(history)

        try:
            refresh_download(file_name, file_bytes)
            st.success(
                f"CECO {selected_ceco} actualizado. "
                f"Se registraron {len(history)} cambio(s)."
            )
            st.toast("Cambios guardados correctamente.", icon="✅")
        except ValueError as error:
            st.error(str(error))


# ============================================================
# MODO 2: REEMPLAZO GLOBAL
# ============================================================

def render_global_replace_mode(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
) -> None:
    flow = get_working_flow()
    users = unique_users(flow)

    question(
        "¿Qué persona quieres reemplazar en toda la base?",
        (
            "Este modo se utiliza, por ejemplo, cuando una persona deja "
            "la empresa y debe ser reemplazada en todos los CECO."
        ),
    )

    if not users:
        st.warning("No se encontraron liberadores en la base activa.")
        return

    old_user = st.selectbox(
        "Persona que sale",
        options=users,
        format_func=lambda value: display_user(value, data),
        key="global_old_user_v03",
    )

    occurrences = user_occurrences(flow, old_user)

    affected_cecos = (
        occurrences["CECO"].nunique()
        if not occurrences.empty
        else 0
    )
    affected_rows = (
        occurrences["_ID_FILA"].nunique()
        if not occurrences.empty
        else 0
    )
    affected_positions = len(occurrences)

    metric_cols = st.columns(3)
    metrics = [
        ("CECO afectados", affected_cecos),
        ("Filas afectadas", affected_rows),
        ("Apariciones", affected_positions),
    ]

    for column, (label, value) in zip(metric_cols, metrics):
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

    if occurrences.empty:
        st.warning("La persona seleccionada no aparece en la base.")
        return

    with st.expander(
        f"Ver dónde participa {display_user(old_user, data)}",
        expanded=True,
    ):
        display_occurrences = occurrences.drop(
            columns=["_ID_FILA"],
            errors="ignore",
        )
        st.dataframe(
            styled_preview(display_occurrences),
            use_container_width=True,
            hide_index=True,
            height=min(
                560,
                max(250, 36 * (len(display_occurrences) + 2)),
            ),
        )

    question(
        "¿Quién será la nueva persona?",
        (
            "Puedes seleccionar un liberador existente o escribir un "
            "correo nuevo."
        ),
    )

    replacement_mode = st.radio(
        "Origen del reemplazante",
        options=["existente", "nuevo"],
        format_func=lambda value: (
            "Seleccionar persona existente"
            if value == "existente"
            else "Escribir correo nuevo"
        ),
        horizontal=True,
        key="global_replacement_mode_v03",
    )

    new_user = ""

    if replacement_mode == "existente":
        candidates = [
            user
            for user in users
            if strip_user(user).lower() != strip_user(old_user).lower()
        ]

        if candidates:
            new_user = st.selectbox(
                "Nueva persona",
                options=candidates,
                format_func=lambda value: display_user(value, data),
                key="global_existing_new_user_v03",
            )
        else:
            st.warning(
                "No existen otras personas en la base. "
                "Selecciona Escribir correo nuevo."
            )
    else:
        new_user = strip_user(
            st.text_input(
                "Correo de la nueva persona",
                placeholder="nombre.apellido@enaex.com",
                key="global_new_email_v03",
            )
        )

    question(
        "Confirma el reemplazo global",
        (
            "La persona anterior será reemplazada en todas sus "
            "apariciones, sin modificar los demás liberadores."
        ),
    )

    col_actor, col_reason = st.columns(2)
    with col_actor:
        actor = st.text_input(
            "Usuario que realiza el cambio",
            placeholder="nombre.apellido",
            key="global_actor_v03",
        )
    with col_reason:
        reason = st.text_input(
            "Motivo",
            placeholder="Salida de la empresa, cambio de cargo...",
            key="global_reason_v03",
        )

    if new_user:
        st.info(
            f"Se reemplazará **{display_user(old_user, data)}** por "
            f"**{display_user(new_user, data)}** en "
            f"**{affected_cecos} CECO**, **{affected_rows} filas** "
            f"y **{affected_positions} posiciones**."
        )

    confirmation = st.checkbox(
        "Confirmo que deseo aplicar este reemplazo en toda la base.",
        value=False,
        key="global_confirm_v03",
    )

    apply_clicked = st.button(
        "🔁 Reemplazar en todos los CECO",
        type="primary",
        use_container_width=True,
        disabled=not (new_user and confirmation),
        key="global_apply_v03",
    )

    if apply_clicked:
        old_key = strip_user(old_user).lower()
        new_value = strip_user(new_user)

        if not new_value:
            st.error("Indica la nueva persona.")
            return

        updated = flow.copy(deep=True)
        history: list[dict[str, Any]] = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for row_index, row in updated.iterrows():
            for column in LIB_COLS:
                current = strip_user(row[column])
                if current.lower() != old_key:
                    continue

                updated.at[row_index, column] = new_value
                history.append(
                    {
                        "FechaHora": timestamp,
                        "Usuario": actor or "anonimo",
                        "Modo": "Reemplazo global",
                        "CECO": row["CECO"],
                        "TipoDoc": row["TipoDoc"],
                        "Desde": row["Desde"],
                        "Hasta": row["Hasta"],
                        "Campo": column,
                        "ValorAntes": current,
                        "ValorDespues": new_value,
                        "Motivo": reason or "Reemplazo global de persona",
                    }
                )

        set_working_flow(updated)
        add_history(history)

        try:
            refresh_download(file_name, file_bytes)
            st.success(
                f"Reemplazo completado: {len(history)} apariciones "
                f"actualizadas en {affected_cecos} CECO."
            )
            st.toast("Reemplazo global guardado.", icon="✅")
        except ValueError as error:
            st.error(str(error))


# ============================================================
# DESCARGA, HISTORIAL Y RESTAURACIÓN
# ============================================================

def render_download_and_admin(
    file_name: str,
    file_bytes: bytes,
) -> None:
    history = list(st.session_state.get(SESSION_HISTORY_KEY, []))

    st.markdown("---")
    st.subheader("Excel actualizado")

    generated = st.session_state.get(SESSION_DOWNLOAD_KEY)
    generated_name = st.session_state.get(SESSION_DOWNLOAD_NAME_KEY)

    col_generate, col_download = st.columns([1, 1.4])

    with col_generate:
        if st.button(
            "🔄 Preparar descarga actualizada",
            use_container_width=True,
            key="prepare_download_v03",
        ):
            try:
                refresh_download(file_name, file_bytes)
                st.rerun()
            except ValueError as error:
                st.error(str(error))

    with col_download:
        if generated and generated_name:
            st.download_button(
                "⬇️ Descargar Excel modificado",
                data=generated,
                file_name=generated_name,
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                type="primary",
                use_container_width=True,
                key="download_excel_v03",
            )
        else:
            st.button(
                "⬇️ Descargar Excel modificado",
                disabled=True,
                use_container_width=True,
                key="download_disabled_v03",
            )

    if generated_name:
        st.caption(f"Archivo preparado: `{generated_name}`")

    if history:
        with st.expander(
            f"Historial de modificaciones ({len(history)})",
            expanded=False,
        ):
            st.dataframe(
                pd.DataFrame(history),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Restaurar base originalmente cargada", expanded=False):
        st.warning(
            "Esta acción elimina todas las modificaciones realizadas "
            "durante la sesión actual."
        )

        restore_confirm = st.checkbox(
            "Confirmo que deseo restaurar la base original.",
            key="restore_confirm_v03",
        )

        if st.button(
            "Restaurar base original",
            disabled=not restore_confirm,
            use_container_width=True,
            key="restore_original_v03",
        ):
            backup = st.session_state.get(SESSION_BACKUP_KEY)
            if isinstance(backup, pd.DataFrame):
                set_working_flow(backup.copy(deep=True))
                st.session_state[SESSION_HISTORY_KEY] = []
                st.session_state.pop(SESSION_DOWNLOAD_KEY, None)
                st.session_state.pop(SESSION_DOWNLOAD_NAME_KEY, None)

                # Limpia los editores para evitar reutilizar datos anteriores.
                for key in list(st.session_state):
                    if (
                        str(key).startswith("ceco_editor_")
                        or str(key).startswith("local_")
                        or str(key).startswith("global_")
                    ):
                        st.session_state.pop(key, None)

                st.success("Se restauró la base originalmente cargada.")
                st.rerun()


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
        st.info("Selecciona **01 Cargar archivo** en la barra lateral.")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()

    data = st.session_state.get(SESSION_DATA_KEY)
    file_name = st.session_state.get(
        SESSION_FILE_KEY,
        "BBDD_FLUJO_LIBERACION.xlsx",
    )
    file_bytes = st.session_state.get(
        SESSION_FILE_BYTES_KEY,
        b"",
    )

    if (
        not isinstance(data, dict)
        or "flujo" not in data
        or not isinstance(data["flujo"], pd.DataFrame)
        or data["flujo"].empty
    ):
        render_no_file()
        return

    initialize_state(
        data=data,
        file_name=file_name,
        file_bytes=file_bytes,
    )

    flow = get_working_flow()

    st.success(
        (
            f"Archivo activo: **{file_name}** · "
            f"**{len(flow):,} filas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
        ).replace(",", ".")
    )

    question(
        "¿Qué quieres hacer?",
        (
            "Selecciona edición puntual para trabajar con la tabla de un "
            "CECO o reemplazo global para cambiar una persona en toda la base."
        ),
    )

    mode = st.radio(
        "Modo de modificación",
        options=["ceco", "global"],
        format_func=lambda value: (
            "📋 Editar un CECO en formato tabla"
            if value == "ceco"
            else "🌐 Reemplazar una persona en todos los CECO"
        ),
        horizontal=True,
        label_visibility="collapsed",
        key="modification_mode_v03",
    )

    if mode == "ceco":
        render_local_edit_mode(
            data=data,
            file_name=file_name,
            file_bytes=file_bytes,
        )
    else:
        render_global_replace_mode(
            data=data,
            file_name=file_name,
            file_bytes=file_bytes,
        )

    render_download_and_admin(
        file_name=file_name,
        file_bytes=file_bytes,
    )


if __name__ == "__main__":
    main()
