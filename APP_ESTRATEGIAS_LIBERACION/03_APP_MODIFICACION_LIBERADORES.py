# ============================================================
# 03_APP_MODIFICACION_LIBERADORES
# APP_ESTRATEGIAS_LIBERACION
#
# Asistente de modificación basado en escenarios:
# situación → alcance → CECO/tipo/rango → pieza/acción
# → validación → vista previa → impacto global opcional
# → auditoría → Excel profesional.
#
# Formato vigente:
# CECO | Planta | Desde | Hasta | TipoDoc |
# Lib1 | Lib2 | Lib3 | Lib4 | Lib5
# ============================================================

from __future__ import annotations

import base64
import hashlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter
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

SESSION_WORKING_KEY = "mod_liberadores_working_df_v04"
SESSION_BACKUP_KEY = "mod_liberadores_backup_df_v04"
SESSION_SIGNATURE_KEY = "mod_liberadores_signature_v04"
SESSION_DRAFT_KEY = "mod_liberadores_draft_v04"
SESSION_HISTORY_KEY = "mod_liberadores_history_v04"
SESSION_DOWNLOAD_KEY = "mod_liberadores_download_v04"
SESSION_DOWNLOAD_NAME_KEY = "mod_liberadores_download_name_v04"

LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]
FLOW_COLUMNS = [
    "CECO", "Planta", "Desde", "Hasta", "TipoDoc",
    "Lib1", "Lib2", "Lib3", "Lib4", "Lib5",
]

DOC_LABEL = {
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
}

ACTION_LABEL = {
    "mover": "Mover a otra posición",
    "reemplazar": "Reemplazar esta pieza",
    "eliminar": "Eliminar esta pieza",
    "agregar": "Agregar una pieza nueva",
}

SCENARIO_LABEL = {
    "ajuste": "🛠️ Ajustar un flujo específico",
    "salida": "🚪 Reemplazar a alguien que salió de la empresa",
    "temporal": "🗓️ Cubrir una ausencia temporal",
    "orden": "↕️ Reordenar aprobadores de un tramo",
    "dotacion": "➕➖ Agregar o retirar un liberador",
}

SCENARIO_HELP = {
    "ajuste": (
        "Permite mover, reemplazar, agregar o eliminar una pieza "
        "en un CECO, tipo y rango específicos."
    ),
    "salida": (
        "Busca todas las apariciones de una persona y la reemplaza "
        "en todos los CECO de la base."
    ),
    "temporal": (
        "Reemplaza una persona solo en el tramo seleccionado, "
        "sin afectar sus demás participaciones."
    ),
    "orden": (
        "Cambia el orden de aprobación dentro de un tramo, "
        "sin modificar las personas."
    ),
    "dotacion": (
        "Agrega un nuevo liberador o retira uno existente "
        "en un tramo específico."
    ),
}

LS_LABEL = "Liberador Servicios"

# Zona horaria oficial de Santiago de Chile. ZoneInfo aplica
# automáticamente los cambios de horario de verano/invierno.
CHILE_TZ = ZoneInfo("America/Santiago")


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
                padding: 16px 18px;
                background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
                margin: .8rem 0 1rem;
            }

            .question-number {
                display: inline-flex;
                width: 30px;
                height: 30px;
                align-items: center;
                justify-content: center;
                border-radius: 999px;
                background: #17365D;
                color: #FFFFFF;
                font-weight: 850;
                margin-right: 8px;
            }

            .question-title {
                color: #17365D;
                font-size: 1.15rem;
                font-weight: 850;
            }

            .question-help {
                color: #64748B;
                font-size: .9rem;
                margin-top: 6px;
            }

            .flow-card {
                min-width: 175px;
                max-width: 230px;
                border-radius: 13px;
                padding: 12px;
                font-family: Arial, sans-serif;
            }

            .comparison-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
                gap: 14px;
                margin-top: 10px;
            }

            .comparison-before {
                padding: 14px;
                border-radius: 14px;
                border: 1px solid #FECACA;
                background: #FEF2F2;
            }

            .comparison-after {
                padding: 14px;
                border-radius: 14px;
                border: 1px solid #BBF7D0;
                background: #F0FDF4;
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
                font-size: 1.5rem;
                font-weight: 850;
                margin-top: 4px;
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
        '<div class="app-title">03 Modificación de Liberadores</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="app-subtitle">
            Asistente robusto para modificar flujos sin distinción EO/CD y exportar una versión profesional.
        </div>
        """,
        unsafe_allow_html=True,
    )


def question(number: int, title: str, help_text: str) -> None:
    st.markdown(
        compact_html(
            f"""
            <div class="question-card">
                <div>
                    <span class="question-number">{number}</span>
                    <span class="question-title">{escape(title)}</span>
                </div>
                <div class="question-help">{escape(help_text)}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# NORMALIZACIÓN
# ============================================================

def validate_flow_schema(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Valida el formato simplificado antes de permitir modificaciones."""
    flow = data.get("flujo")

    if not isinstance(flow, pd.DataFrame) or flow.empty:
        raise ValueError("La base activa no contiene registros de flujo.")

    missing = [
        column
        for column in FLOW_COLUMNS
        if column not in flow.columns
    ]

    if missing:
        raise ValueError(
            "La base activa no tiene el formato vigente. "
            f"Faltan: {', '.join(missing)}. "
            "Vuelve a cargar el Excel desde 01 Cargar Archivo."
        )

    return flow



def clean_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "null", "<na>", "n/a", "no usar", "—", "-"} else text


def strip_user(value: Any) -> str:
    text = clean_text(value)
    if not text or text == LS_LABEL:
        return text

    match = re.match(r"^(.*?)(?:\s+\([^)]+\))?$", text)
    return match.group(1).strip() if match else text


def email_key(value: Any) -> str:
    return strip_user(value).lower()


def parse_bound(value: Any, low: bool = True) -> float:
    text = clean_text(value)
    if not text or text == "*":
        return 0.0 if low else 1e18

    normalized = text.replace(" ", "")

    if "." in normalized and "," in normalized:
        if normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
    elif normalized.count(".") > 1:
        normalized = normalized.replace(".", "")
    elif normalized.count(",") > 1:
        normalized = normalized.replace(",", "")
    elif "," in normalized:
        left, right = normalized.rsplit(",", 1)
        normalized = left + right if len(right) == 3 else left + "." + right
    elif "." in normalized:
        left, right = normalized.rsplit(".", 1)
        if len(right) == 3 and left.replace("-", "").isdigit():
            normalized = left + right

    try:
        return float(normalized)
    except ValueError:
        return 0.0 if low else 1e18


def fmt_bound(value: Any) -> str:
    number = parse_bound(value, low=False)
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

    for column in ["CECO", "Planta"]:
        flow[column] = flow[column].map(clean_text)

    flow["TipoDoc"] = flow["TipoDoc"].map(clean_text).str.upper()

    for column in LIB_COLS:
        flow[column] = flow[column].map(strip_user)


    flow = flow[
        flow["CECO"].ne("")
        & flow["TipoDoc"].isin(["AZNB", "AZSR"])
    ].reset_index(drop=True)

    flow.insert(0, "_ID_FILA", range(1, len(flow) + 1))
    return flow


def libs_from_row(row: pd.Series) -> list[str]:
    return [
        strip_user(row.get(column, ""))
        for column in LIB_COLS
        if strip_user(row.get(column, ""))
    ]


def libs_padded(values: list[str]) -> list[str]:
    cleaned = [
        strip_user(value)
        for value in values
        if strip_user(value)
    ]
    return (cleaned + [""] * 5)[:5]


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
    return sorted(
        {
            strip_user(value)
            for column in LIB_COLS
            for value in flow[column].tolist()
            if strip_user(value) and strip_user(value) != LS_LABEL
        },
        key=str.lower,
    )



def is_valid_email(value: Any) -> bool:
    """Valida correos simples; Liberador Servicios es una excepción válida."""
    text = strip_user(value)
    if text == LS_LABEL:
        return True
    if not text:
        return False
    return bool(
        re.fullmatch(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text,
        )
    )


def validate_flow_result(
    libs: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    """Valida el flujo borrador antes de permitir su guardado."""
    errors: list[str] = []
    cleaned = [strip_user(value) for value in libs if strip_user(value)]

    if not cleaned and not allow_empty:
        errors.append(
            "El tramo no puede quedar sin liberadores. "
            "Agrega al menos una persona antes de guardar."
        )

    if len(cleaned) > 5:
        errors.append("El flujo no puede superar 5 liberadores.")

    normalized = [email_key(value) for value in cleaned]
    if len(normalized) != len(set(normalized)):
        errors.append("El flujo contiene liberadores duplicados.")

    invalid = [
        value
        for value in cleaned
        if value != LS_LABEL and not is_valid_email(value)
    ]
    if invalid:
        errors.append(
            "Existen correos con formato no válido: "
            + ", ".join(invalid)
        )

    return errors



# ============================================================
# ESTADO
# ============================================================

def source_signature(
    file_name: str,
    file_bytes: bytes,
    rows: int,
) -> str:
    digest = (
        hashlib.sha1(file_bytes[:100000]).hexdigest()
        if file_bytes
        else "no-bytes"
    )
    return f"{file_name}|{len(file_bytes)}|{rows}|{digest}"


def default_draft() -> dict[str, Any]:
    return {
        "ceco": "",
        "doc": "",
        "row_id": None,
        "libs_before": [],
        "libs_after": [],
        "replaced_from": "",
        "replaced_to": "",
        "last_message": "",
    }


def initialize_state(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
) -> None:
    flow = normalize_flow(validate_flow_schema(data))
    signature = source_signature(file_name, file_bytes, len(flow))

    if (
        SESSION_WORKING_KEY not in st.session_state
        or st.session_state.get(SESSION_SIGNATURE_KEY) != signature
    ):
        st.session_state[SESSION_WORKING_KEY] = flow
        st.session_state[SESSION_BACKUP_KEY] = flow.copy(deep=True)
        st.session_state[SESSION_SIGNATURE_KEY] = signature
        st.session_state[SESSION_DRAFT_KEY] = default_draft()
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


def get_draft() -> dict[str, Any]:
    value = st.session_state.get(SESSION_DRAFT_KEY)
    if not isinstance(value, dict):
        value = default_draft()
        st.session_state[SESSION_DRAFT_KEY] = value
    return dict(value)


def set_draft(draft: dict[str, Any]) -> None:
    st.session_state[SESSION_DRAFT_KEY] = dict(draft)


def reset_draft() -> None:
    st.session_state[SESSION_DRAFT_KEY] = default_draft()


# ============================================================
# TABLAS Y FLUJOS
# ============================================================

def style_flow_table(df: pd.DataFrame):
    visible_columns = [
        "CECO", "Planta", "Desde", "Hasta", "TipoDoc",
        "Lib1", "Lib2", "Lib3", "Lib4", "Lib5",
    ]
    visible = df.loc[:, visible_columns].copy()

    def style_row(row: pd.Series) -> list[str]:
        if row["TipoDoc"] == "AZNB":
            style = "background-color:#FFF1F0;color:#7A271A;"
        elif row["TipoDoc"] == "AZSR":
            style = "background-color:#EFF8FF;color:#1849A9;"
        else:
            style = ""
        return [style] * len(row)

    return visible.style.apply(style_row, axis=1).format(
        {
            "Desde": lambda value: fmt_bound(value),
            "Hasta": lambda value: fmt_bound(value),
        }
    )


def flow_html(
    libs: list[str],
    data: dict[str, pd.DataFrame],
    title: str,
) -> str:
    if not libs:
        return (
            f"<div style='font-family:Arial,sans-serif;'>"
            f"<b>{escape(title)}</b>"
            f"<p style='color:#B42318;'>Sin liberadores.</p></div>"
        )

    parts: list[str] = []

    for index, user in enumerate(libs):
        parts.append(
            f"""
            <div class="flow-card"
                 style="background:#F8FAFC;border:2px dashed #94A3B8;">
                <div style="font-size:11px;color:#64748B;font-weight:750;">
                    Liberador {index + 1}
                </div>
                <div style="
                    font-size:12px;
                    font-weight:750;
                    color:#17365D;
                    margin-top:7px;
                    overflow-wrap:anywhere;
                ">
                    {escape(display_user(user, data))}
                </div>
            </div>
            """
        )

        if index < len(libs) - 1:
            parts.append(
                "<div style='font-size:21px;color:#94A3B8;font-weight:700;'>→</div>"
            )

    return compact_html(
        f"""
        <div style="font-family:Arial,sans-serif;">
            <div style="font-weight:850;color:#17365D;margin-bottom:9px;">
                {escape(title)}
            </div>
            <div style="display:flex;flex-wrap:wrap;align-items:center;gap:7px;">
                {''.join(parts)}
            </div>
        </div>
        """
    )


def render_comparison(
    before: list[str],
    after: list[str],
    data: dict[str, pd.DataFrame],
) -> None:
    st.markdown(
        compact_html(
            f"""
            <div class="comparison-grid">
                <div class="comparison-before">
                    {flow_html(before, data, "ANTES")}
                </div>
                <div class="comparison-after">
                    {flow_html(after, data, "DESPUÉS · BORRADOR")}
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# ACCIONES
# ============================================================

def apply_action(
    action: str,
    libs: list[str],
    selected_index: int | None,
    destination_index: int | None,
    new_value: str,
) -> tuple[list[str], str, str, str]:
    result = list(libs)
    replaced_from = ""
    replaced_to = ""

    if action == "agregar":
        if len(result) >= 5:
            raise ValueError("El flujo ya tiene el máximo de 5 liberadores.")
        if not new_value:
            raise ValueError("Indica quién deseas agregar.")
        if email_key(new_value) in [email_key(value) for value in result]:
            raise ValueError("La persona ya existe en el flujo.")

        result.append(new_value)
        return (
            result,
            f"Agregado como Liberador {len(result)}: {new_value}.",
            "",
            "",
        )

    if selected_index is None:
        raise ValueError("Selecciona una pieza.")

    if selected_index < 0 or selected_index >= len(result):
        raise ValueError("La pieza seleccionada no es válida.")

    if action == "eliminar":
        removed = result.pop(selected_index)
        return result, f"Eliminado: {removed}.", "", ""

    if action == "mover":
        if destination_index is None:
            raise ValueError("Indica a qué posición deseas mover la pieza.")
        if destination_index == selected_index:
            raise ValueError("La pieza ya está en esa posición.")

        piece = result.pop(selected_index)
        result.insert(destination_index, piece)
        return (
            result,
            f"Movido {piece} a Liberador {destination_index + 1}.",
            "",
            "",
        )

    if action == "reemplazar":
        if not new_value:
            raise ValueError("Indica quién entra.")

        old_value = result[selected_index]
        keys = [email_key(value) for value in result]

        if (
            email_key(new_value) in keys
            and email_key(new_value) != email_key(old_value)
        ):
            other_index = keys.index(email_key(new_value))
            result[selected_index], result[other_index] = (
                result[other_index],
                result[selected_index],
            )
            return (
                result,
                (
                    "La persona ya estaba en el flujo. "
                    f"Se intercambiaron Liberador {selected_index + 1} "
                    f"y Liberador {other_index + 1}."
                ),
                "",
                "",
            )

        result[selected_index] = new_value
        replaced_from = old_value
        replaced_to = new_value

        return (
            result,
            (
                f"Reemplazo en Liberador {selected_index + 1}: "
                f"{old_value} → {new_value}."
            ),
            replaced_from,
            replaced_to,
        )

    raise ValueError("Selecciona una acción válida.")


def occurrences_of_person(
    flow: pd.DataFrame,
    person: str,
) -> pd.DataFrame:
    target = email_key(person)
    records: list[dict[str, Any]] = []

    if not target:
        return pd.DataFrame()

    for _, row in flow.iterrows():
        for column in LIB_COLS:
            current = strip_user(row[column])
            if email_key(current) != target:
                continue

            records.append(
                {
                    "_ID_FILA": int(row["_ID_FILA"]),
                    "CECO": row["CECO"],
                    "Planta": row["Planta"],
                    "Desde": row["Desde"],
                    "Hasta": row["Hasta"],
                    "TipoDoc": row["TipoDoc"],
                    "Campo": column,
                    "ValorAntes": current,
                }
            )

    return pd.DataFrame(records)


# ============================================================
# EXCEL
# ============================================================

def download_name(original_name: str) -> str:
    """
    Nombre estable, corto e intuitivo usando hora oficial de Santiago.
    Ejemplo: BBDD_LIBERACION_2026-07-29_12-23-45.xlsx
    """
    timestamp = datetime.now(CHILE_TZ).strftime("%Y-%m-%d_%H-%M-%S")
    return f"BBDD_LIBERACION_{timestamp}.xlsx"


def sanitize_excel_value(value: Any) -> Any:
    """Evita que NaN/NaT sean escritos como valores inválidos."""
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def remove_existing_tables(sheet) -> None:
    """Elimina tablas antiguas antes de reescribir una hoja."""
    for table_name in list(sheet.tables.keys()):
        del sheet.tables[table_name]


def professional_sheet_format(
    sheet,
    *,
    table_name: str,
    header_fill: str = "17365D",
    tab_color: str | None = None,
) -> None:
    """Aplica formato corporativo y legible a una hoja."""
    if sheet.max_row < 1 or sheet.max_column < 1:
        return

    if tab_color:
        sheet.sheet_properties.tabColor = tab_color

    header_font = Font(
        name="Calibri",
        size=11,
        bold=True,
        color="FFFFFF",
    )
    header_pattern = PatternFill(
        fill_type="solid",
        fgColor=header_fill,
    )
    thin_gray = Side(style="thin", color="D0D5DD")
    body_border = Border(
        left=thin_gray,
        right=thin_gray,
        top=thin_gray,
        bottom=thin_gray,
    )

    for cell in sheet[1]:
        cell.font = header_font
        cell.fill = header_pattern
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )
        cell.border = body_border

    sheet.row_dimensions[1].height = 30
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.sheet_view.showGridLines = False

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Calibri", size=10)
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )
            cell.border = body_border

    # Formatos numéricos de montos.
    header_index = {
        str(cell.value).strip(): cell.column
        for cell in sheet[1]
        if cell.value is not None
    }
    for column_name in ["Desde", "Hasta"]:
        column_index = header_index.get(column_name)
        if column_index:
            for row_index in range(2, sheet.max_row + 1):
                sheet.cell(row_index, column_index).number_format = '#,##0'

    # Anchos calculados con límites para evitar hojas excesivamente anchas.
    for column_index in range(1, sheet.max_column + 1):
        letter = get_column_letter(column_index)
        values = [
            str(sheet.cell(row_index, column_index).value or "")
            for row_index in range(1, min(sheet.max_row, 250) + 1)
        ]
        width = min(max(max(map(len, values), default=8) + 2, 10), 42)

        header = str(sheet.cell(1, column_index).value or "")
        if header in LIB_COLS:
            width = max(width, 30)
        elif header in {"Nota", "ValorAntes", "ValorDespues"}:
            width = max(width, 24)
        elif header in {"CECO", "Planta", "TipoDoc", "Campo"}:
            width = max(width, 14)

        sheet.column_dimensions[letter].width = width

    remove_existing_tables(sheet)

    if sheet.max_row >= 2:
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", table_name)
        reference = (
            f"A1:{get_column_letter(sheet.max_column)}{sheet.max_row}"
        )
        table = Table(
            displayName=safe_name[:250],
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


def write_dataframe_to_sheet(
    sheet,
    dataframe: pd.DataFrame,
) -> None:
    """Reescribe una hoja conservando el libro y otras pestañas."""
    if sheet.max_row:
        sheet.delete_rows(1, sheet.max_row)

    for row_index, values in enumerate(
        dataframe_to_rows(dataframe, index=False, header=True),
        start=1,
    ):
        for column_index, value in enumerate(values, start=1):
            sheet.cell(
                row=row_index,
                column=column_index,
                value=sanitize_excel_value(value),
            )


def build_excel(
    original_bytes: bytes,
    flow: pd.DataFrame,
    history: list[dict[str, Any]],
) -> bytes:
    if not original_bytes:
        raise ValueError(
            "No se encontraron los bytes del Excel. "
            "Vuelve a cargarlo desde 01 Cargar archivo."
        )

    try:
        workbook = load_workbook(BytesIO(original_bytes))
    except Exception as error:
        raise ValueError("No fue posible abrir el Excel original.") from error

    if "Flujo" in workbook.sheetnames:
        flow_sheet = workbook["Flujo"]
    else:
        flow_sheet = workbook.create_sheet("Flujo")

    export_flow = (
        flow.drop(columns=["_ID_FILA"], errors="ignore")
        .loc[:, FLOW_COLUMNS]
        .copy()
    )
    write_dataframe_to_sheet(flow_sheet, export_flow)
    professional_sheet_format(
        flow_sheet,
        table_name="TablaFlujoLiberacion",
        header_fill="17365D",
        tab_color="175CD3",
    )

    if "Cambios" in workbook.sheetnames:
        change_sheet = workbook["Cambios"]
    else:
        change_sheet = workbook.create_sheet("Cambios")

    history_df = pd.DataFrame(history)
    history_columns = [
        "FechaHora",
        "Usuario",
        "CECO",
        "Desde",
        "Hasta",
        "TipoDoc",
        "Campo",
        "ValorAntes",
        "ValorDespues",
        "Nota",
    ]
    if history_df.empty:
        history_df = pd.DataFrame(columns=history_columns)
    else:
        for column in history_columns:
            if column not in history_df.columns:
                history_df[column] = ""
        history_df = history_df.loc[:, history_columns]

    write_dataframe_to_sheet(change_sheet, history_df)
    professional_sheet_format(
        change_sheet,
        table_name="TablaHistorialCambios",
        header_fill="7F1D1D",
        tab_color="B42318",
    )

    # Hoja ejecutiva con información de la versión generada.
    if "Resumen_Version" in workbook.sheetnames:
        summary_sheet = workbook["Resumen_Version"]
    else:
        summary_sheet = workbook.create_sheet("Resumen_Version", 0)

    summary_df = pd.DataFrame(
        [
            {
                "Fecha generación": datetime.now(CHILE_TZ).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Zona horaria": "America/Santiago",
                "Filas de flujo": len(export_flow),
                "CECO únicos": export_flow["CECO"].nunique(),
                "Cambios registrados": len(history_df),
                "Estado": "Versión modificada",
            }
        ]
    )
    write_dataframe_to_sheet(summary_sheet, summary_df)
    professional_sheet_format(
        summary_sheet,
        table_name="TablaResumenVersion",
        header_fill="166534",
        tab_color="16A34A",
    )

    # Alinea los diccionarios con el formato simplificado.
    if "Dic_CECO" in workbook.sheetnames:
        ceco_sheet = workbook["Dic_CECO"]
        headers = [clean_text(cell.value) for cell in ceco_sheet[1]]
        keep = [name for name in ["CECO", "Planta", "Centro"] if name in headers]
        if keep:
            values = list(ceco_sheet.iter_rows(values_only=True))
            source = pd.DataFrame(values[1:], columns=headers)
            write_dataframe_to_sheet(ceco_sheet, source.loc[:, keep])
            professional_sheet_format(
                ceco_sheet,
                table_name="TablaDicCECO",
                header_fill="475467",
                tab_color="64748B",
            )

    if "Dic_Rangos" in workbook.sheetnames:
        range_sheet = workbook["Dic_Rangos"]
        headers = [clean_text(cell.value) for cell in range_sheet[1]]
        keep = [name for name in ["Orden", "Desde", "Hasta"] if name in headers]
        if keep:
            values = list(range_sheet.iter_rows(values_only=True))
            source = pd.DataFrame(values[1:], columns=headers)
            write_dataframe_to_sheet(range_sheet, source.loc[:, keep])
            professional_sheet_format(
                range_sheet,
                table_name="TablaDicRangos",
                header_fill="475467",
                tab_color="64748B",
            )

    if "Formato_Flujo" in workbook.sheetnames:
        del workbook["Formato_Flujo"]

    # Las demás hojas se preservan. Se estilizan solo sus encabezados
    # cuando contienen una tabla reconocible, sin alterar sus datos.
    protected = {"Resumen_Version", "Flujo", "Cambios"}
    for sheet in workbook.worksheets:
        if sheet.title in protected:
            continue
        if sheet.max_row >= 1 and sheet.max_column >= 1:
            for cell in sheet[1]:
                if cell.value is not None:
                    cell.font = Font(
                        name="Calibri",
                        size=11,
                        bold=True,
                        color="FFFFFF",
                    )
                    cell.fill = PatternFill(
                        fill_type="solid",
                        fgColor="475467",
                    )
                    cell.alignment = Alignment(
                        horizontal="center",
                        vertical="center",
                        wrap_text=True,
                    )
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            sheet.sheet_view.showGridLines = False

    workbook.active = workbook.sheetnames.index("Resumen_Version")

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def refresh_download(
    file_name: str,
    file_bytes: bytes,
) -> None:
    generated = build_excel(
        original_bytes=file_bytes,
        flow=get_working_flow(),
        history=list(st.session_state.get(SESSION_HISTORY_KEY, [])),
    )
    st.session_state[SESSION_DOWNLOAD_KEY] = generated
    st.session_state[SESSION_DOWNLOAD_NAME_KEY] = download_name(file_name)


# ============================================================
# REEMPLAZO GLOBAL DE PERSONA
# ============================================================

def render_global_replacement(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
    actor: str,
    reason: str,
) -> None:
    """Reemplaza una persona en todas sus apariciones de la base."""
    flow = get_working_flow()
    users = unique_users(flow)

    question(
        2,
        "¿Qué persona se va de la empresa?",
        (
            "Selecciona la persona que debe ser reemplazada. "
            "Antes de guardar podrás revisar todos los CECO afectados."
        ),
    )

    if not users:
        st.warning("No se encontraron correos de liberadores en la base activa.")
        return

    old_user = st.selectbox(
        "Persona que sale",
        options=users,
        format_func=lambda value: display_user(value, data),
        key="global_old_user_v05",
    )

    occurrences = occurrences_of_person(flow, old_user)

    if occurrences.empty:
        st.warning("La persona seleccionada no tiene apariciones en la base.")
        return

    affected_cecos = int(occurrences["CECO"].nunique())
    affected_rows = int(occurrences["_ID_FILA"].nunique())
    affected_positions = int(len(occurrences))

    metric_cols = st.columns(3)
    metrics = [
        ("CECO donde participa", affected_cecos),
        ("Filas afectadas", affected_rows),
        ("Apariciones", affected_positions),
    ]

    for column, (label, value) in zip(metric_cols, metrics):
        with column:
            st.markdown(
                compact_html(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{escape(label)}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    question(
        3,
        "¿Dónde participa actualmente?",
        (
            "Revisa todos los CECO, tramos, tipos y posiciones "
            "antes de seleccionar a la nueva persona."
        ),
    )

    occurrence_view = occurrences[
        [
            "CECO",
            "Planta",
            "Desde",
            "Hasta",
            "TipoDoc",
            "Campo",
            "ValorAntes",
        ]
    ].rename(
        columns={
            "Campo": "Posición",
            "ValorAntes": "Persona actual",
        }
    )

    def style_occurrence_row(row: pd.Series) -> list[str]:
        doc = clean_text(row.get("TipoDoc")).upper()
        if doc == "AZNB":
            style = "background-color:#FFF1F0;color:#7A271A;"
        elif doc == "AZSR":
            style = "background-color:#EFF8FF;color:#1849A9;"
        else:
            style = ""
        return [style] * len(row)

    styled_occurrences = (
        occurrence_view.style
        .apply(style_occurrence_row, axis=1)
        .format(
            {
                "Desde": lambda value: fmt_bound(value),
                "Hasta": lambda value: fmt_bound(value),
            }
        )
    )

    st.dataframe(
        styled_occurrences,
        use_container_width=True,
        hide_index=True,
        height=min(600, max(260, 36 * (len(occurrence_view) + 2))),
    )

    question(
        4,
        "¿Quién será la nueva persona?",
        (
            "Selecciona un usuario existente o escribe un correo nuevo. "
            "El reemplazo se aplicará en todas las apariciones mostradas."
        ),
    )

    replacement_source = st.radio(
        "Origen de la nueva persona",
        options=["existing", "new"],
        format_func=lambda value: (
            "Seleccionar usuario existente"
            if value == "existing"
            else "Escribir correo nuevo"
        ),
        horizontal=True,
        key="global_replacement_source_v05",
    )

    new_user = ""

    if replacement_source == "existing":
        candidates = [
            user
            for user in users
            if email_key(user) != email_key(old_user)
        ]

        if candidates:
            new_user = st.selectbox(
                "Nueva persona",
                options=candidates,
                format_func=lambda value: display_user(value, data),
                key="global_new_existing_user_v05",
            )
        else:
            st.warning(
                "No hay otra persona disponible. "
                "Selecciona Escribir correo nuevo."
            )
    else:
        new_user = strip_user(
            st.text_input(
                "Correo de la nueva persona",
                placeholder="nombre.apellido@enaex.com",
                key="global_new_email_v05",
            )
        )

    question(
        5,
        "¿Confirmas el reemplazo global?",
        (
            "Se reemplazará únicamente a la persona seleccionada; "
            "los demás liberadores y el orden del flujo permanecerán sin cambios."
        ),
    )

    if new_user:
        st.info(
            f"Se reemplazará **{display_user(old_user, data)}** por "
            f"**{display_user(new_user, data)}** en "
            f"**{affected_cecos} CECO**, **{affected_rows} filas** "
            f"y **{affected_positions} posiciones**."
        )

    confirmation = st.checkbox(
        (
            "Confirmo que la persona seleccionada debe ser reemplazada "
            "en toda la base."
        ),
        value=False,
        key="global_confirm_v05",
    )

    global_ready = bool(
        new_user
        and confirmation
        and clean_text(actor)
        and clean_text(reason)
        and is_valid_email(new_user)
    )

    if new_user and not is_valid_email(new_user):
        st.error("El correo de la nueva persona no tiene un formato válido.")

    if not clean_text(actor) or not clean_text(reason):
        st.warning(
            "Para realizar un reemplazo global debes indicar "
            "quién modifica y el motivo."
        )

    apply_clicked = st.button(
        "🔁 Aplicar reemplazo global y preparar Excel",
        type="primary",
        use_container_width=True,
        disabled=not global_ready,
        key="global_apply_v06",
    )

    if apply_clicked:
        old_key = email_key(old_user)
        replacement = strip_user(new_user)

        if not replacement:
            st.error("Indica la nueva persona.")
            return

        if email_key(replacement) == old_key:
            st.error("La nueva persona debe ser distinta de la persona que sale.")
            return

        updated = flow.copy(deep=True)
        timestamp = datetime.now(CHILE_TZ).strftime("%Y-%m-%d %H:%M:%S")
        changes: list[dict[str, Any]] = []

        for row_index, row in updated.iterrows():
            for column in LIB_COLS:
                current = strip_user(row[column])

                if email_key(current) != old_key:
                    continue

                updated.at[row_index, column] = replacement

                changes.append(
                    {
                        "FechaHora": timestamp,
                        "Usuario": actor or "anonimo",
                        "CECO": row["CECO"],
                        "Desde": row["Desde"],
                        "Hasta": row["Hasta"],
                        "TipoDoc": row["TipoDoc"],
                        "Campo": column,
                        "ValorAntes": current,
                        "ValorDespues": replacement,
                        "Nota": (
                            reason
                            or "Reemplazo global por salida de la empresa"
                        ),
                    }
                )

        set_working_flow(updated)

        history = list(st.session_state.get(SESSION_HISTORY_KEY, []))
        history.extend(changes)
        st.session_state[SESSION_HISTORY_KEY] = history

        try:
            refresh_download(file_name, file_bytes)
            st.success(
                f"Reemplazo global completado: "
                f"**{len(changes)} apariciones** actualizadas "
                f"en **{affected_cecos} CECO**."
            )
            st.toast("Reemplazo global guardado.", icon="✅")
        except ValueError as error:
            st.error(str(error))

    generated = st.session_state.get(SESSION_DOWNLOAD_KEY)
    generated_name = st.session_state.get(SESSION_DOWNLOAD_NAME_KEY)

    if generated and generated_name:
        st.markdown("---")
        st.subheader("Descargar versión profesional del Excel")
        st.download_button(
            "⬇️ Descargar archivo modificado",
            data=generated,
            file_name=generated_name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True,
            key="global_download_v05",
        )
        st.caption(f"Archivo preparado: `{generated_name}`")

    history = st.session_state.get(SESSION_HISTORY_KEY, [])
    if history:
        with st.expander(
            f"Historial de esta sesión ({len(history)} cambios)",
            expanded=False,
        ):
            st.dataframe(
                pd.DataFrame(history),
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# INTERFAZ PASO A PASO
# ============================================================

def render_wizard(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
) -> None:
    flow = get_working_flow()
    draft = get_draft()

    st.success(
        (
            f"Archivo activo: **{file_name}** · "
            f"**{len(flow):,} filas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
        ).replace(",", ".")
    )

    # --------------------------------------------------------
    # Datos del cambio
    # --------------------------------------------------------
    with st.expander("Identificación del cambio", expanded=True):
        actor_col, reason_col = st.columns(2)

        with actor_col:
            actor = st.text_input(
                "¿Quién modifica?",
                placeholder="nombre.apellido",
                key="mod_actor_v04",
            )

        with reason_col:
            reason = st.text_input(
                "¿Por qué?",
                placeholder="vacaciones, reorden, reemplazo...",
                key="mod_reason_v04",
            )

    # --------------------------------------------------------
    # 1. Escenario de negocio
    # --------------------------------------------------------
    question(
        1,
        "¿Qué situación necesitas resolver?",
        (
            "Selecciona el escenario más parecido a tu necesidad. "
            "La aplicación limitará las opciones para evitar errores."
        ),
    )

    scenario = st.radio(
        "Escenario",
        options=list(SCENARIO_LABEL),
        format_func=lambda value: SCENARIO_LABEL[value],
        label_visibility="collapsed",
        key="mod_scenario_v06",
    )
    st.info(SCENARIO_HELP[scenario])

    if scenario == "salida":
        if not clean_text(actor) or not clean_text(reason):
            st.warning(
                "Completa ¿Quién modifica? y ¿Por qué? antes de "
                "aplicar un reemplazo global."
            )
        render_global_replacement(
            data=data,
            file_name=file_name,
            file_bytes=file_bytes,
            actor=actor,
            reason=reason,
        )
        return

    # --------------------------------------------------------
    # 2. CECO
    # --------------------------------------------------------
    question(
        2,
        "¿Qué CECO quieres modificar?",
        "Selecciona el CECO y revisa su tabla completa.",
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
        "CECO",
        options=ceco_map["CECO"].tolist(),
        format_func=lambda value: (
            f"{value} | {plant_by_ceco.get(value, '')}"
            if plant_by_ceco.get(value, "")
            else value
        ),
        key="mod_ceco_v04",
    )

    ceco_rows = flow[flow["CECO"].eq(selected_ceco)].copy()

    st.dataframe(
        style_flow_table(ceco_rows),
        use_container_width=True,
        hide_index=True,
        height=min(520, max(250, 36 * (len(ceco_rows) + 2))),
    )

    # --------------------------------------------------------
    # 2. Tipo
    # --------------------------------------------------------
    question(
        3,
        "¿Qué tipo quieres modificar?",
        "Selecciona Material o Servicio.",
    )

    available_docs = [
        doc
        for doc in ["AZNB", "AZSR"]
        if not ceco_rows[ceco_rows["TipoDoc"].eq(doc)].empty
    ]

    if not available_docs:
        st.error("El CECO no contiene reglas AZNB ni AZSR.")
        return

    selected_doc = st.radio(
        "Tipo de documento",
        options=available_docs,
        format_func=lambda value: DOC_LABEL[value],
        horizontal=True,
        key="mod_doc_v04",
    )

    doc_rows = ceco_rows[
        ceco_rows["TipoDoc"].eq(selected_doc)
    ].copy()

    doc_rows["_DESDE"] = doc_rows["Desde"].map(
        lambda value: parse_bound(value, low=True)
    )
    doc_rows = (
        doc_rows.sort_values(["_DESDE", "_ID_FILA"])
        .drop(columns=["_DESDE"])
    )

    # --------------------------------------------------------
    # 3. Rango
    # --------------------------------------------------------
    question(
        4,
        "¿Qué rango quieres abrir?",
        "Selecciona el tramo cuyo flujo deseas modificar.",
    )

    row_lookup = doc_rows.set_index("_ID_FILA")

    selected_row_id = st.selectbox(
        "Rango",
        options=doc_rows["_ID_FILA"].tolist(),
        format_func=lambda row_id: (
            f"{fmt_bound(row_lookup.loc[row_id, 'Desde'])} – "
            f"{fmt_bound(row_lookup.loc[row_id, 'Hasta'])}"
        ),
        key="mod_range_v04",
    )

    selected_row = row_lookup.loc[selected_row_id]
    current_identity = (
        selected_ceco,
        selected_doc,
        int(selected_row_id),
    )
    draft_identity = (
        draft.get("ceco"),
        draft.get("doc"),
        draft.get("row_id"),
    )

    if current_identity != draft_identity:
        libs = libs_from_row(selected_row)
        draft = default_draft()
        draft.update(
            {
                "ceco": selected_ceco,
                "doc": selected_doc,
                "row_id": int(selected_row_id),
                "libs_before": list(libs),
                "libs_after": list(libs),
            }
        )
        set_draft(draft)

    libs_before = list(draft["libs_before"])
    libs_after = list(draft["libs_after"])

    st.info(
        f"Tramo activo: **{fmt_bound(selected_row['Desde'])} – "
        f"{fmt_bound(selected_row['Hasta'])}**."
    )

    st.markdown(
        flow_html(
            libs_after,
            data,
            "Flujo actual del tramo",
        ),
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # 4. Pieza
    # --------------------------------------------------------
    question(
        5,
        "¿Qué pieza quieres modificar?",
        "Para Agregar no es necesario seleccionar una pieza.",
    )

    piece_options = list(range(len(libs_after)))
    selected_piece = None

    if piece_options:
        selected_piece = st.selectbox(
            "Pieza",
            options=piece_options,
            format_func=lambda index: (
                f"Liberador {index + 1}: "
                f"{display_user(libs_after[index], data)}"
            ),
            key="mod_piece_v04",
        )
    else:
        st.warning(
            "El flujo no tiene liberadores. Utiliza la acción Agregar."
        )

    # --------------------------------------------------------
    # 5. Acción
    # --------------------------------------------------------
    question(
        6,
        "¿Qué quieres hacer?",
        "La subpregunta cambia según la acción seleccionada.",
    )

    scenario_actions = {
        "ajuste": ["mover", "reemplazar", "eliminar", "agregar"],
        "temporal": ["reemplazar"],
        "orden": ["mover"],
        "dotacion": ["agregar", "eliminar"],
    }
    allowed_actions = scenario_actions.get(
        scenario,
        list(ACTION_LABEL),
    )

    action = st.selectbox(
        "Acción",
        options=allowed_actions,
        format_func=lambda value: ACTION_LABEL[value],
        key="mod_action_v06",
    )

    destination_index = None
    new_value = ""

    if action == "mover":
        if not piece_options:
            st.warning("No existen piezas para mover.")
        else:
            destination_index = st.selectbox(
                "¿A qué posición?",
                options=piece_options,
                format_func=lambda index: f"Liberador {index + 1}",
                key="mod_destination_v04",
            )

    elif action in {"reemplazar", "agregar"}:
        prompt = (
            "¿Qué entra?"
            if action == "reemplazar"
            else "¿Qué agregas?"
        )

        entry_mode = st.radio(
            prompt,
            options=["mail", "ls"],
            format_func=lambda value: (
                "Correo"
                if value == "mail"
                else "Liberador Servicios"
            ),
            horizontal=True,
            key="mod_entry_mode_v04",
        )

        if entry_mode == "ls":
            new_value = LS_LABEL
        else:
            users = unique_users(flow)
            selection_mode = st.radio(
                "Origen del correo",
                options=["existing", "new"],
                format_func=lambda value: (
                    "Seleccionar usuario existente"
                    if value == "existing"
                    else "Escribir correo nuevo"
                ),
                horizontal=True,
                key="mod_user_mode_v04",
            )

            if selection_mode == "existing" and users:
                new_value = st.selectbox(
                    "Correo",
                    options=users,
                    format_func=lambda value: display_user(value, data),
                    key="mod_existing_user_v04",
                )
            else:
                new_value = strip_user(
                    st.text_input(
                        "Correo",
                        placeholder="nombre.apellido@enaex.com",
                        key="mod_new_user_v04",
                    )
                )

    apply_clicked = st.button(
        "Aplicar respuesta",
        type="primary",
        use_container_width=True,
        key="mod_apply_answer_v04",
    )

    if apply_clicked:
        try:
            if (
                action in {"reemplazar", "agregar"}
                and new_value
                and not is_valid_email(new_value)
            ):
                raise ValueError(
                    "El correo ingresado no tiene un formato válido."
                )

            result, message, replaced_from, replaced_to = apply_action(
                action=action,
                libs=libs_after,
                selected_index=(
                    selected_piece
                    if action != "agregar"
                    else None
                ),
                destination_index=destination_index,
                new_value=strip_user(new_value),
            )

            draft["libs_after"] = result
            draft["last_message"] = message
            draft["replaced_from"] = replaced_from
            draft["replaced_to"] = replaced_to
            set_draft(draft)
            st.rerun()

        except ValueError as error:
            st.error(str(error))

    if draft.get("last_message"):
        st.success(draft["last_message"])

    # --------------------------------------------------------
    # Vista previa
    # --------------------------------------------------------
    st.markdown("### Vista previa")
    render_comparison(
        before=libs_before,
        after=libs_after,
        data=data,
    )

    col_undo, col_restart = st.columns(2)

    with col_undo:
        if st.button(
            "↩️ Retroceder último borrador",
            use_container_width=True,
            disabled=libs_after == libs_before,
            key="mod_undo_v04",
        ):
            draft["libs_after"] = list(libs_before)
            draft["replaced_from"] = ""
            draft["replaced_to"] = ""
            draft["last_message"] = "Se restauró el flujo original del tramo."
            set_draft(draft)
            st.rerun()

    with col_restart:
        if st.button(
            "🔄 Reiniciar selección",
            use_container_width=True,
            key="mod_restart_v04",
        ):
            reset_draft()
            for key in [
                "mod_piece_v04",
                "mod_action_v04",
                "mod_destination_v04",
                "mod_entry_mode_v04",
                "mod_user_mode_v04",
                "mod_existing_user_v04",
                "mod_new_user_v04",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

    # --------------------------------------------------------
    # Propagación global
    # --------------------------------------------------------
    propagate = False
    occurrences = pd.DataFrame()

    if draft.get("replaced_from") and draft.get("replaced_to"):
        question(
            7,
            "¿Quieres reemplazar también en otros CECO?",
            (
                "Utiliza esta opción si la persona salió de la empresa "
                "y debe ser reemplazada en todas sus apariciones."
            ),
        )

        occurrences = occurrences_of_person(
            flow,
            draft["replaced_from"],
        )

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
            ("CECO donde participa", affected_cecos),
            ("Filas afectadas", affected_rows),
            ("Apariciones", affected_positions),
        ]

        for column, (label, value) in zip(metric_cols, metrics):
            with column:
                st.markdown(
                    compact_html(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">{escape(label)}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )

        with st.expander(
            (
                "Ver todas las apariciones de "
                f"{display_user(draft['replaced_from'], data)}"
            ),
            expanded=False,
        ):
            visible_occurrences = occurrences.drop(
                columns=["_ID_FILA"],
                errors="ignore",
            )
            st.dataframe(
                style_flow_table(
                    visible_occurrences.rename(
                        columns={
                            "Campo": "Lib1",
                            "ValorAntes": "Lib2",
                        }
                    ).assign(
                        Lib3="",
                        Lib4="",
                        Lib5="",
                    )
                )
                if not visible_occurrences.empty
                else visible_occurrences,
                use_container_width=True,
                hide_index=True,
            )

        propagate = st.radio(
            "¿Otros CECO?",
            options=["no", "yes"],
            format_func=lambda value: (
                "NO — guardar solo este tramo"
                if value == "no"
                else (
                    "SÍ — reemplazar en todos los CECO donde aparecía "
                    "la persona que salió"
                )
            ),
            key="mod_propagate_v04",
        ) == "yes"

    # --------------------------------------------------------
    # Guardado
    # --------------------------------------------------------
    question(
        8,
        "¿Guardar los cambios?",
        (
            "Los cambios se aplicarán a la base activa y quedarán "
            "registrados en la hoja Cambios."
        ),
    )

    no_changes = libs_padded(libs_before) == libs_padded(libs_after)
    validation_errors = validate_flow_result(libs_after)
    missing_identification = (
        not clean_text(actor)
        or not clean_text(reason)
    )

    if validation_errors:
        for validation_error in validation_errors:
            st.error(validation_error)

    if missing_identification:
        st.warning(
            "Para guardar debes indicar quién realiza el cambio "
            "y el motivo."
        )

    save_clicked = st.button(
        "💾 Guardar cambios y preparar Excel",
        type="primary",
        use_container_width=True,
        disabled=(
            no_changes
            or bool(validation_errors)
            or missing_identification
        ),
        key="mod_save_v06",
    )

    if no_changes:
        st.caption("Todavía no hay cambios para guardar.")

    if save_clicked:
        updated = flow.copy(deep=True)
        selected_mask = updated["_ID_FILA"].eq(int(selected_row_id))

        if not selected_mask.any():
            st.error("La fila seleccionada ya no existe.")
            return

        before_padded = libs_padded(libs_before)
        after_padded = libs_padded(libs_after)
        timestamp = datetime.now(CHILE_TZ).strftime("%Y-%m-%d %H:%M:%S")
        changes: list[dict[str, Any]] = []

        for column, old_value, new_value in zip(
            LIB_COLS,
            before_padded,
            after_padded,
        ):
            if strip_user(old_value) == strip_user(new_value):
                continue

            updated.loc[selected_mask, column] = strip_user(new_value)
            changes.append(
                {
                    "FechaHora": timestamp,
                    "Usuario": actor or "anonimo",
                    "CECO": selected_ceco,
                    "Desde": selected_row["Desde"],
                    "Hasta": selected_row["Hasta"],
                    "TipoDoc": selected_doc,
                    "Campo": column,
                    "ValorAntes": strip_user(old_value) or "—",
                    "ValorDespues": strip_user(new_value) or "—",
                    "Nota": reason or "Edición guiada de liberadores",
                }
            )


        if (
            propagate
            and draft.get("replaced_from")
            and draft.get("replaced_to")
        ):
            old_key = email_key(draft["replaced_from"])
            new_person = strip_user(draft["replaced_to"])

            for row_index, row in updated.iterrows():
                for column in LIB_COLS:
                    current = strip_user(row[column])

                    if email_key(current) != old_key:
                        continue

                    # Evita duplicar el registro ya modificado del tramo actual.
                    if (
                        int(row["_ID_FILA"]) == int(selected_row_id)
                        and column in [
                            change["Campo"]
                            for change in changes
                        ]
                    ):
                        continue

                    updated.at[row_index, column] = new_person
                    changes.append(
                        {
                            "FechaHora": timestamp,
                            "Usuario": actor or "anonimo",
                            "CECO": row["CECO"],
                            "Desde": row["Desde"],
                            "Hasta": row["Hasta"],
                            "TipoDoc": row["TipoDoc"],
                            "Campo": column,
                            "ValorAntes": current,
                            "ValorDespues": new_person,
                            "Nota": (
                                (reason or "Reemplazo global")
                                + " | propagado a otros CECO"
                            ),
                        }
                    )

        set_working_flow(updated)

        history = list(st.session_state.get(SESSION_HISTORY_KEY, []))
        history.extend(changes)
        st.session_state[SESSION_HISTORY_KEY] = history

        try:
            refresh_download(file_name, file_bytes)
            draft["libs_before"] = list(libs_after)
            draft["replaced_from"] = ""
            draft["replaced_to"] = ""
            draft["last_message"] = (
                f"Guardado correctamente: {len(changes)} cambio(s)."
            )
            set_draft(draft)

            st.success(
                f"Guardado correctamente: **{len(changes)} cambio(s)**."
            )
            st.toast("Base activa actualizada.", icon="✅")
        except ValueError as error:
            st.error(str(error))

    # --------------------------------------------------------
    # Descarga
    # --------------------------------------------------------
    generated = st.session_state.get(SESSION_DOWNLOAD_KEY)
    generated_name = st.session_state.get(SESSION_DOWNLOAD_NAME_KEY)

    if generated and generated_name:
        st.markdown("---")
        st.subheader("Descargar versión profesional del Excel")

        st.download_button(
            "⬇️ Descargar archivo modificado",
            data=generated,
            file_name=generated_name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True,
            key="mod_download_v04",
        )

        st.caption(f"Archivo preparado: `{generated_name}`")

    history = st.session_state.get(SESSION_HISTORY_KEY, [])
    if history:
        with st.expander(
            f"Historial de esta sesión ({len(history)} cambios)",
            expanded=False,
        ):
            st.dataframe(
                pd.DataFrame(history),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Restaurar base original", expanded=False):
        st.warning(
            "Esta acción elimina las modificaciones realizadas "
            "durante la sesión."
        )

        confirm_restore = st.checkbox(
            "Confirmo que deseo restaurar el archivo originalmente cargado.",
            key="mod_confirm_restore_v04",
        )

        if st.button(
            "Restaurar base original",
            disabled=not confirm_restore,
            use_container_width=True,
            key="mod_restore_v04",
        ):
            backup = st.session_state.get(SESSION_BACKUP_KEY)
            if isinstance(backup, pd.DataFrame):
                set_working_flow(backup.copy(deep=True))
                reset_draft()
                st.session_state[SESSION_HISTORY_KEY] = []
                st.session_state.pop(SESSION_DOWNLOAD_KEY, None)
                st.session_state.pop(SESSION_DOWNLOAD_NAME_KEY, None)
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
        st.info("Selecciona **01 Cargar archivo** desde la barra lateral.")


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

    render_wizard(
        data=data,
        file_name=file_name,
        file_bytes=file_bytes,
    )


if __name__ == "__main__":
    main()
