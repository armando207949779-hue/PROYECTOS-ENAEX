# ============================================================
# 03_APP_MODIFICACION_LIBERADORES
# APP_ESTRATEGIAS_LIBERACION
#
# Asistente paso a paso para modificar liberadores:
# 1) ¿Qué quieres hacer?
# 2) Seleccionar CECO
# 3) Seleccionar tipo
# 4) Seleccionar tramo
# 5) Seleccionar pieza / completar acción
# 6) Revisar antes y después
# 7) Guardar en sesión y descargar Excel actualizado
# ============================================================

from __future__ import annotations

import base64
import re
from copy import deepcopy
from datetime import datetime
from html import escape
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

SESSION_WORKING_KEY = "mod_liberadores_working_df_v02"
SESSION_BACKUP_KEY = "mod_liberadores_backup_df_v02"
SESSION_SIGNATURE_KEY = "mod_liberadores_source_signature_v02"
SESSION_DRAFT_KEY = "mod_liberadores_draft_v02"
SESSION_HISTORY_KEY = "mod_liberadores_history_v02"
SESSION_DOWNLOAD_KEY = "mod_liberadores_download_v02"
SESSION_DOWNLOAD_NAME_KEY = "mod_liberadores_download_name_v02"

LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]
FLOW_COLUMNS = [
    "CECO", "Planta", "Desde", "Hasta", "TipoDoc",
    "Lib1", "Lib2", "Lib3", "Lib4", "Lib5",
    "N_EO", "N_CD", "Match", "FuenteCD",
]

DOC_LABEL = {
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
}

DOC_COLOR = {
    "AZNB": "#C62828",
    "AZSR": "#1565C0",
}

ACTION_LABEL = {
    "mover": "Mover un liberador",
    "reemplazar": "Reemplazar un liberador",
    "eliminar": "Eliminar un liberador",
    "agregar": "Agregar un liberador",
}

ACTION_ICON = {
    "mover": "↔️",
    "reemplazar": "🔁",
    "eliminar": "🗑️",
    "agregar": "➕",
}

LS_LABEL = "Liberador Servicios"


# ============================================================
# ESTILOS Y LOGO
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

            .fl-logo-wrap {
                width: 100%;
                min-height: 90px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: .7rem 0 .7rem;
                overflow: visible;
            }

            .fl-logo-wrap img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 88px;
                object-fit: contain;
                display: block;
            }

            .fl-title {
                text-align: center;
                color: #17365D;
                font-size: 2rem;
                font-weight: 850;
                margin: .1rem 0;
            }

            .fl-subtitle {
                text-align: center;
                color: #64748B;
                font-size: 1rem;
                margin-bottom: 1.2rem;
            }

            .question-node {
                padding: 18px 20px;
                border-radius: 16px;
                border: 2px solid #93C5FD;
                background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
                margin: .7rem 0 1rem;
            }

            .question-node .q-number {
                display: inline-flex;
                width: 30px;
                height: 30px;
                align-items: center;
                justify-content: center;
                border-radius: 999px;
                background: #17365D;
                color: #FFFFFF;
                font-weight: 800;
                margin-right: 8px;
            }

            .question-node .q-title {
                color: #17365D;
                font-size: 1.2rem;
                font-weight: 850;
            }

            .question-node .q-help {
                color: #64748B;
                font-size: .9rem;
                margin-top: 7px;
            }

            .step-card {
                padding: 14px 16px;
                border: 1px solid #D0D5DD;
                border-radius: 14px;
                background: #FFFFFF;
                margin: .5rem 0 .8rem;
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
                <div class="fl-logo-wrap">
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
        '<div class="fl-title">03 Modificación de Liberadores</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-subtitle">
            Responde las preguntas del asistente, revisa el resultado
            y descarga el Excel actualizado.
        </div>
        """,
        unsafe_allow_html=True,
    )


def question_node(number: int, title: str, help_text: str) -> None:
    st.markdown(
        compact_html(
            f"""
            <div class="question-node">
                <div>
                    <span class="q-number">{number}</span>
                    <span class="q-title">{escape(title)}</span>
                </div>
                <div class="q-help">{escape(help_text)}</div>
            </div>
            """
        ),
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
    return "" if text.lower() in {"", "nan", "none", "—", "-"} else text


def parse_bound(value: Any, low: bool = True) -> float:
    text = clean_text(value)
    if not text or text == "*":
        return 0.0 if low else 1e18

    text = text.replace(" ", "")
    if re.fullmatch(r"[-+]?\d{1,3}(?:\.\d{3})+", text):
        text = text.replace(".", "")
    else:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return 0.0 if low else 1e18


def fmt_bound(value: Any) -> str:
    try:
        number = parse_bound(value, low=False)
        if number >= 1e12:
            return "999.999.999.999"
        return f"{int(number):,}".replace(",", ".")
    except (TypeError, ValueError):
        return clean_text(value)


def strip_user_email(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text == LS_LABEL:
        return LS_LABEL

    match = re.match(r"^(.*?)(?:\s*\(([^)]+)\))?$", text)
    return match.group(1).strip() if match else text


def preparar_flujo(df: pd.DataFrame) -> pd.DataFrame:
    flow = df.copy()
    flow.columns = [str(column).strip() for column in flow.columns]

    for column in FLOW_COLUMNS:
        if column not in flow.columns:
            flow[column] = ""

    flow = flow[FLOW_COLUMNS].copy()
    flow["CECO"] = flow["CECO"].map(clean_text)
    flow["Planta"] = flow["Planta"].map(clean_text)
    flow["TipoDoc"] = flow["TipoDoc"].map(clean_text).str.upper()
    flow["Match"] = flow["Match"].map(clean_text).str.upper()
    flow["FuenteCD"] = flow["FuenteCD"].map(clean_text)

    for column in LIB_COLS:
        flow[column] = flow[column].map(strip_user_email)

    for column in ["N_EO", "N_CD"]:
        flow[column] = (
            pd.to_numeric(flow[column], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    flow = flow[flow["CECO"].ne("")].reset_index(drop=True)
    flow.insert(0, "_ID_FILA", range(1, len(flow) + 1))
    return flow


def libs_from_row(row: pd.Series) -> list[str]:
    return [
        strip_user_email(row.get(column, ""))
        for column in LIB_COLS
        if strip_user_email(row.get(column, ""))
    ]


def libs_padded(libs: list[str]) -> list[str]:
    values = [strip_user_email(value) for value in libs if strip_user_email(value)]
    return (values + [""] * 5)[:5]


def cargo_map(data: dict[str, pd.DataFrame]) -> dict[str, str]:
    users = data.get("dic_users", pd.DataFrame())
    if not isinstance(users, pd.DataFrame) or users.empty:
        return {}

    correo_col = next(
        (column for column in users.columns if str(column).strip().lower() == "correo"),
        None,
    )
    cargo_col = next(
        (column for column in users.columns if str(column).strip().lower() == "cargo"),
        None,
    )

    if correo_col is None:
        return {}

    result: dict[str, str] = {}
    for _, row in users.iterrows():
        email = strip_user_email(row.get(correo_col, ""))
        cargo = clean_text(row.get(cargo_col, "")) if cargo_col else ""
        if email:
            result[email.lower()] = cargo
    return result


def display_user(value: Any, data: dict[str, pd.DataFrame]) -> str:
    email = strip_user_email(value)
    if not email:
        return ""
    if email == LS_LABEL:
        return LS_LABEL

    cargo = cargo_map(data).get(email.lower(), "")
    return f"{email} ({cargo})" if cargo else email


# ============================================================
# ESTADO
# ============================================================

def source_signature(file_name: str, file_bytes: bytes, rows: int) -> str:
    return f"{file_name}|{len(file_bytes)}|{rows}"


def default_draft() -> dict[str, Any]:
    return {
        "action": "",
        "ceco": "",
        "doc": "",
        "row_id": None,
        "before": [],
        "after": [],
        "n_eo": 0,
        "selected_piece": None,
        "replacement_from": "",
        "changes": [],
    }


def initialize_state(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
) -> None:
    flow = preparar_flujo(data["flujo"])
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


def working_df() -> pd.DataFrame:
    value = st.session_state.get(SESSION_WORKING_KEY)
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=True)
    return pd.DataFrame(columns=["_ID_FILA", *FLOW_COLUMNS])


def get_draft() -> dict[str, Any]:
    draft = st.session_state.get(SESSION_DRAFT_KEY)
    if not isinstance(draft, dict):
        draft = default_draft()
        st.session_state[SESSION_DRAFT_KEY] = draft
    return deepcopy(draft)


def save_draft(draft: dict[str, Any]) -> None:
    st.session_state[SESSION_DRAFT_KEY] = deepcopy(draft)


def reset_draft(keep_action: bool = False) -> None:
    current = get_draft()
    new_draft = default_draft()
    if keep_action:
        new_draft["action"] = current.get("action", "")
    st.session_state[SESSION_DRAFT_KEY] = new_draft


def update_session_data(flow: pd.DataFrame) -> None:
    st.session_state[SESSION_WORKING_KEY] = flow.reset_index(drop=True)

    data = st.session_state.get(SESSION_DATA_KEY)
    if isinstance(data, dict):
        updated = dict(data)
        updated["flujo"] = (
            flow.drop(columns=["_ID_FILA"], errors="ignore")
            .loc[:, FLOW_COLUMNS]
            .copy()
        )
        st.session_state[SESSION_DATA_KEY] = updated


# ============================================================
# VISUALIZACIÓN
# ============================================================

def flow_html(
    libs: list[str],
    n_eo: int,
    data: dict[str, pd.DataFrame],
    title: str,
) -> str:
    if not libs:
        return (
            f"<div style='font-family:Arial,sans-serif;'>"
            f"<b>{escape(title)}</b>"
            f"<p style='color:#64748B;'>Sin liberadores.</p></div>"
        )

    parts: list[str] = []
    for index, user in enumerate(libs):
        is_eo = index < n_eo
        background = "#EAF7EE" if is_eo else "#EEF2FF"
        border = "#7BC596" if is_eo else "#A5B4FC"
        text_color = "#166534" if is_eo else "#1E3A8A"
        role = "EO" if is_eo else "CD"

        parts.append(
            f"""
            <div class="flow-card"
                 style="background:{background};border:2px solid {border};">
                <div style="font-size:11px;color:#64748B;font-weight:700;">
                    Liberador {index + 1} · {role}
                </div>
                <div style="
                    font-size:12px;
                    font-weight:750;
                    color:{text_color};
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
    n_eo: int,
    data: dict[str, pd.DataFrame],
) -> None:
    st.markdown(
        compact_html(
            f"""
            <div class="comparison-grid">
                <div class="comparison-before">
                    {flow_html(before, n_eo, data, "ANTES")}
                </div>
                <div class="comparison-after">
                    {flow_html(after, n_eo, data, "DESPUÉS")}
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def style_ceco_table(df: pd.DataFrame):
    visible = df.drop(columns=["_ID_FILA"], errors="ignore").copy()

    def row_style(row: pd.Series) -> list[str]:
        doc = clean_text(row.get("TipoDoc")).upper()
        if doc == "AZNB":
            style = "background-color:#FFF1F0;color:#7A271A;"
        elif doc == "AZSR":
            style = "background-color:#EFF8FF;color:#1849A9;"
        else:
            style = ""
        return [style] * len(row)

    return visible.style.apply(row_style, axis=1).format(
        {
            "Desde": lambda value: fmt_bound(value),
            "Hasta": lambda value: fmt_bound(value),
        }
    )


# ============================================================
# EXCEL
# ============================================================

def build_excel(
    original_bytes: bytes,
    flow: pd.DataFrame,
    changes: list[dict[str, Any]],
) -> bytes:
    if not original_bytes:
        raise ValueError("No se encontraron los bytes del Excel cargado.")

    try:
        workbook = load_workbook(BytesIO(original_bytes))
    except Exception as exc:
        raise ValueError("No fue posible abrir el Excel original.") from exc

    if "Flujo" in workbook.sheetnames:
        sheet = workbook["Flujo"]
    else:
        sheet = workbook.create_sheet("Flujo")

    for row in sheet.iter_rows():
        for cell in row:
            cell.value = None

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

    if changes:
        change_sheet_name = "Cambios"
        if change_sheet_name in workbook.sheetnames:
            change_sheet = workbook[change_sheet_name]
            first_empty = change_sheet.max_row + 1
            if change_sheet.max_row == 1 and all(
                cell.value is None for cell in change_sheet[1]
            ):
                first_empty = 1
        else:
            change_sheet = workbook.create_sheet(change_sheet_name)
            first_empty = 1

        changes_df = pd.DataFrame(changes)
        write_header = first_empty == 1

        for row_index, values in enumerate(
            dataframe_to_rows(
                changes_df,
                index=False,
                header=write_header,
            ),
            start=first_empty,
        ):
            for column_index, value in enumerate(values, start=1):
                change_sheet.cell(
                    row=row_index,
                    column=column_index,
                    value=value,
                )

        change_sheet.freeze_panes = "A2"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def download_name(original_name: str) -> str:
    stem = Path(original_name or "BBDD_FLUJO_LIBERACION.xlsx").stem
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{stem}_MODIFICADO_{timestamp}.xlsx"


# ============================================================
# ACCIONES DEL ASISTENTE
# ============================================================

def apply_action(
    action: str,
    before: list[str],
    selected_index: int | None,
    destination_index: int | None,
    new_user: str,
) -> tuple[list[str], str]:
    after = list(before)

    if action == "mover":
        if selected_index is None:
            raise ValueError("Selecciona el liberador que deseas mover.")
        if destination_index is None:
            raise ValueError("Selecciona la posición de destino.")
        if selected_index == destination_index:
            raise ValueError("El liberador ya se encuentra en esa posición.")

        value = after.pop(selected_index)
        after.insert(destination_index, value)
        return after, (
            f"{value} se moverá desde Liberador {selected_index + 1} "
            f"a Liberador {destination_index + 1}."
        )

    if action == "reemplazar":
        if selected_index is None:
            raise ValueError("Selecciona el liberador que deseas reemplazar.")
        if not new_user:
            raise ValueError("Indica el nuevo correo o Liberador Servicios.")

        old_user = after[selected_index]

        existing_index = next(
            (
                index
                for index, value in enumerate(after)
                if strip_user_email(value).lower() == new_user.lower()
                and index != selected_index
            ),
            None,
        )

        if existing_index is not None:
            after[selected_index], after[existing_index] = (
                after[existing_index],
                after[selected_index],
            )
            return after, (
                "El nuevo liberador ya estaba en el flujo. "
                f"Se intercambiarán Liberador {selected_index + 1} "
                f"y Liberador {existing_index + 1}."
            )

        after[selected_index] = new_user
        return after, (
            f"{old_user} será reemplazado por {new_user} "
            f"en Liberador {selected_index + 1}."
        )

    if action == "eliminar":
        if selected_index is None:
            raise ValueError("Selecciona el liberador que deseas eliminar.")

        removed = after.pop(selected_index)
        return after, f"{removed} será eliminado del flujo."

    if action == "agregar":
        if len(after) >= 5:
            raise ValueError("El flujo ya tiene el máximo de 5 liberadores.")
        if not new_user:
            raise ValueError("Indica el correo que deseas agregar.")

        if any(
            strip_user_email(value).lower() == new_user.lower()
            for value in after
        ):
            raise ValueError("Ese liberador ya existe en el flujo.")

        after.append(new_user)
        return after, (
            f"{new_user} se agregará como Liberador {len(after)}."
        )

    raise ValueError("Selecciona una acción válida.")


def build_change_rows(
    row: pd.Series,
    before: list[str],
    after: list[str],
    actor: str,
    reason: str,
    action: str,
) -> list[dict[str, Any]]:
    before_padded = libs_padded(before)
    after_padded = libs_padded(after)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows: list[dict[str, Any]] = []
    for column, old, new in zip(LIB_COLS, before_padded, after_padded):
        if old == new:
            continue

        rows.append(
            {
                "FechaHora": timestamp,
                "Usuario": actor or "anonimo",
                "TipoCambio": ACTION_LABEL.get(action, action),
                "CECO": clean_text(row.get("CECO")),
                "Planta": clean_text(row.get("Planta")),
                "Desde": row.get("Desde", ""),
                "Hasta": row.get("Hasta", ""),
                "TipoDoc": clean_text(row.get("TipoDoc")),
                "Campo": column,
                "ValorAntes": old or "—",
                "ValorDespues": new or "—",
                "Nota": reason or "Modificación desde app 03",
            }
        )
    return rows


# ============================================================
# INTERFAZ PRINCIPAL
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


def render_wizard(
    data: dict[str, pd.DataFrame],
    file_name: str,
    file_bytes: bytes,
) -> None:
    flow = working_df()
    draft = get_draft()

    st.success(
        (
            f"Archivo activo: **{file_name}** · "
            f"**{len(flow):,} filas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
        ).replace(",", ".")
    )

    # --------------------------------------------------------
    # 1. Pregunta inicial
    # --------------------------------------------------------
    question_node(
        1,
        "¿Qué quieres hacer?",
        "Selecciona una acción. El asistente mostrará únicamente las preguntas necesarias.",
    )

    action = st.radio(
        "Acción",
        options=list(ACTION_LABEL),
        format_func=lambda value: (
            f"{ACTION_ICON[value]} {ACTION_LABEL[value]}"
        ),
        horizontal=True,
        index=(
            list(ACTION_LABEL).index(draft["action"])
            if draft.get("action") in ACTION_LABEL
            else 0
        ),
        label_visibility="collapsed",
        key="mod_action_v02",
    )

    if action != draft.get("action"):
        reset_draft()
        draft = get_draft()
        draft["action"] = action
        save_draft(draft)

    st.info(
        {
            "mover": (
                "Seleccionarás una pieza del flujo y la moverás a otra posición."
            ),
            "reemplazar": (
                "Seleccionarás una pieza y definirás quién ocupará su lugar."
            ),
            "eliminar": (
                "Seleccionarás una pieza para retirarla del flujo."
            ),
            "agregar": (
                "Agregarás un nuevo liberador al final del flujo seleccionado."
            ),
        }[action]
    )

    # --------------------------------------------------------
    # 2. CECO
    # --------------------------------------------------------
    question_node(
        2,
        "¿En qué CECO quieres trabajar?",
        "Selecciona un CECO para ver sus reglas de material y servicio.",
    )

    ceco_rows = (
        flow[["CECO", "Planta"]]
        .drop_duplicates()
        .sort_values(["CECO", "Planta"])
    )

    ceco_options = ceco_rows["CECO"].tolist()
    plant_map = (
        ceco_rows.groupby("CECO")["Planta"]
        .first()
        .to_dict()
    )

    selected_ceco = st.selectbox(
        "CECO",
        options=ceco_options,
        format_func=lambda value: (
            f"{value} | {plant_map.get(value, '')}"
            if plant_map.get(value, "")
            else value
        ),
        key="mod_ceco_v02",
    )

    ceco_table = flow[flow["CECO"].eq(selected_ceco)].copy()
    with st.expander(
        f"Ver tabla completa del CECO {selected_ceco}",
        expanded=False,
    ):
        st.dataframe(
            style_ceco_table(ceco_table),
            use_container_width=True,
            hide_index=True,
            height=min(520, max(230, 35 * (len(ceco_table) + 2))),
        )

    # --------------------------------------------------------
    # 3. Tipo
    # --------------------------------------------------------
    question_node(
        3,
        "¿Es material o servicio?",
        "Solo se muestran los tipos disponibles para el CECO seleccionado.",
    )

    available_docs = [
        doc
        for doc in ["AZNB", "AZSR"]
        if not ceco_table[ceco_table["TipoDoc"].eq(doc)].empty
    ]

    if not available_docs:
        st.error("El CECO seleccionado no posee reglas AZNB ni AZSR.")
        return

    selected_doc = st.radio(
        "Tipo de documento",
        options=available_docs,
        format_func=lambda value: DOC_LABEL[value],
        horizontal=True,
        key="mod_doc_v02",
    )

    doc_table = ceco_table[ceco_table["TipoDoc"].eq(selected_doc)].copy()
    doc_table["_LO"] = doc_table["Desde"].map(
        lambda value: parse_bound(value, low=True)
    )
    doc_table = doc_table.sort_values("_LO").drop(columns="_LO")

    # --------------------------------------------------------
    # 4. Rango
    # --------------------------------------------------------
    question_node(
        4,
        "¿Qué tramo quieres modificar?",
        "Cada tramo tiene su propio flujo de liberadores.",
    )

    row_options = doc_table["_ID_FILA"].tolist()
    row_by_id = doc_table.set_index("_ID_FILA")

    selected_row_id = st.selectbox(
        "Tramo",
        options=row_options,
        format_func=lambda row_id: (
            f"{fmt_bound(row_by_id.loc[row_id, 'Desde'])} – "
            f"{fmt_bound(row_by_id.loc[row_id, 'Hasta'])}"
        ),
        key="mod_range_v02",
    )

    selected_row = row_by_id.loc[selected_row_id]
    before = libs_from_row(selected_row)
    n_eo = int(selected_row.get("N_EO", 0) or 0)

    st.markdown(
        flow_html(
            before,
            n_eo,
            data,
            (
                f"Flujo actual · {selected_ceco} · "
                f"{DOC_LABEL[selected_doc]} · "
                f"{fmt_bound(selected_row['Desde'])} – "
                f"{fmt_bound(selected_row['Hasta'])}"
            ),
        ),
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # 5. Pregunta de acción
    # --------------------------------------------------------
    question_node(
        5,
        (
            "¿Qué pieza quieres modificar?"
            if action != "agregar"
            else "¿Quién quieres agregar?"
        ),
        (
            "Selecciona el liberador y completa la pregunta adicional."
            if action != "agregar"
            else "Ingresa el correo del nuevo liberador o selecciona Liberador Servicios."
        ),
    )

    selected_index: int | None = None
    destination_index: int | None = None
    new_user = ""

    if action != "agregar":
        if not before:
            st.error(
                "El tramo no tiene liberadores. Selecciona la acción Agregar."
            )
            return

        piece_options = list(range(len(before)))
        selected_index = st.selectbox(
            "Pieza",
            options=piece_options,
            format_func=lambda index: (
                f"Liberador {index + 1}: "
                f"{display_user(before[index], data)}"
            ),
            key="mod_piece_v02",
        )

    if action == "mover":
        destination_options = list(range(len(before)))
        destination_index = st.selectbox(
            "¿A qué posición?",
            options=destination_options,
            format_func=lambda index: f"Liberador {index + 1}",
            key="mod_destination_v02",
        )

    elif action in {"reemplazar", "agregar"}:
        input_mode = st.radio(
            (
                "¿Quién entra?"
                if action == "reemplazar"
                else "¿Qué quieres agregar?"
            ),
            options=["correo", "servicios"],
            format_func=lambda value: (
                "Correo de usuario"
                if value == "correo"
                else "Liberador Servicios"
            ),
            horizontal=True,
            key="mod_input_mode_v02",
        )

        if input_mode == "servicios":
            new_user = LS_LABEL
        else:
            existing_users = sorted(
                {
                    strip_user_email(value)
                    for column in LIB_COLS
                    for value in flow[column].tolist()
                    if strip_user_email(value)
                    and strip_user_email(value) != LS_LABEL
                }
            )

            new_user = strip_user_email(
                st.selectbox(
                    "Correo",
                    options=["__NUEVO__", *existing_users],
                    format_func=lambda value: (
                        "Escribir un correo nuevo"
                        if value == "__NUEVO__"
                        else display_user(value, data)
                    ),
                    key="mod_user_select_v02",
                )
            )

            if new_user == "__NUEVO__":
                new_user = strip_user_email(
                    st.text_input(
                        "Nuevo correo",
                        placeholder="nombre.apellido@enaex.com",
                        key="mod_new_email_v02",
                    )
                )

    # --------------------------------------------------------
    # 6. Vista previa
    # --------------------------------------------------------
    question_node(
        6,
        "¿Así debe quedar?",
        "Revisa la comparación antes de guardar el cambio.",
    )

    try:
        after, action_summary = apply_action(
            action=action,
            before=before,
            selected_index=selected_index,
            destination_index=destination_index,
            new_user=new_user,
        )
        preview_valid = True
        st.info(action_summary)
        render_comparison(before, after, n_eo, data)
    except ValueError as error:
        after = list(before)
        preview_valid = False
        st.warning(str(error))
        render_comparison(before, after, n_eo, data)

    # --------------------------------------------------------
    # 7. Identificación y guardado
    # --------------------------------------------------------
    question_node(
        7,
        "¿Quién realiza el cambio y por qué?",
        "Estos datos quedarán registrados en la hoja Cambios del Excel descargado.",
    )

    col_actor, col_reason = st.columns(2)

    with col_actor:
        actor = st.text_input(
            "Usuario que modifica",
            placeholder="nombre.apellido",
            key="mod_actor_v02",
        )

    with col_reason:
        reason = st.text_input(
            "Motivo",
            placeholder="vacaciones, reemplazo, reordenamiento...",
            key="mod_reason_v02",
        )

    propagate = False
    replaced_user = ""
    if action == "reemplazar" and selected_index is not None:
        replaced_user = before[selected_index]
        propagate = st.checkbox(
            (
                "Aplicar el mismo reemplazo en todas las apariciones de "
                f"{display_user(replaced_user, data)}"
            ),
            value=False,
            key="mod_propagate_v02",
        )

    col_save, col_reset = st.columns([1.4, 1])

    with col_save:
        save_clicked = st.button(
            "💾 Guardar modificación",
            type="primary",
            use_container_width=True,
            disabled=not preview_valid,
            key="mod_save_v02",
        )

    with col_reset:
        reset_clicked = st.button(
            "↩️ Reiniciar preguntas",
            use_container_width=True,
            key="mod_reset_v02",
        )

    if reset_clicked:
        reset_draft()
        for key in [
            "mod_action_v02",
            "mod_ceco_v02",
            "mod_doc_v02",
            "mod_range_v02",
            "mod_piece_v02",
            "mod_destination_v02",
            "mod_input_mode_v02",
            "mod_user_select_v02",
            "mod_new_email_v02",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    if save_clicked:
        updated_flow = flow.copy(deep=True)
        history = list(st.session_state.get(SESSION_HISTORY_KEY, []))

        selected_mask = updated_flow["_ID_FILA"].eq(selected_row_id)
        if not selected_mask.any():
            st.error("La fila seleccionada ya no existe.")
            return

        change_rows = build_change_rows(
            selected_row,
            before,
            after,
            actor,
            reason,
            action,
        )

        after_padded = libs_padded(after)
        for column, value in zip(LIB_COLS, after_padded):
            updated_flow.loc[selected_mask, column] = value

        # Propagación global opcional para reemplazos.
        if (
            propagate
            and action == "reemplazar"
            and selected_index is not None
            and new_user
            and replaced_user
        ):
            old_key = strip_user_email(replaced_user).lower()

            for row_index, row in updated_flow.iterrows():
                if int(row["_ID_FILA"]) == int(selected_row_id):
                    continue

                for column in LIB_COLS:
                    current = strip_user_email(row[column])
                    if current.lower() != old_key:
                        continue

                    propagated_before = current
                    updated_flow.at[row_index, column] = new_user
                    change_rows.append(
                        {
                            "FechaHora": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "Usuario": actor or "anonimo",
                            "TipoCambio": (
                                "Reemplazo propagado a otros CECO"
                            ),
                            "CECO": clean_text(row["CECO"]),
                            "Planta": clean_text(row["Planta"]),
                            "Desde": row["Desde"],
                            "Hasta": row["Hasta"],
                            "TipoDoc": clean_text(row["TipoDoc"]),
                            "Campo": column,
                            "ValorAntes": propagated_before,
                            "ValorDespues": new_user,
                            "Nota": reason or "Reemplazo global",
                        }
                    )

        history.extend(change_rows)
        st.session_state[SESSION_HISTORY_KEY] = history
        update_session_data(updated_flow)

        try:
            generated_excel = build_excel(
                original_bytes=file_bytes,
                flow=updated_flow,
                changes=history,
            )
            generated_name = download_name(file_name)
            st.session_state[SESSION_DOWNLOAD_KEY] = generated_excel
            st.session_state[SESSION_DOWNLOAD_NAME_KEY] = generated_name

            st.success(
                f"Modificación guardada. Se registraron "
                f"{len(change_rows)} cambio(s)."
            )
            st.toast("Base actualizada correctamente.", icon="✅")
        except ValueError as error:
            st.error(str(error))

    # --------------------------------------------------------
    # Descarga y resumen
    # --------------------------------------------------------
    generated_excel = st.session_state.get(SESSION_DOWNLOAD_KEY)
    generated_name = st.session_state.get(SESSION_DOWNLOAD_NAME_KEY)

    if generated_excel and generated_name:
        st.markdown("---")
        st.subheader("Descargar Excel actualizado")
        st.download_button(
            "⬇️ Descargar archivo modificado",
            data=generated_excel,
            file_name=generated_name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True,
            key="mod_download_v02",
        )
        st.caption(
            f"Nombre del archivo: `{generated_name}`"
        )

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
            "Esta acción elimina todas las modificaciones realizadas "
            "durante la sesión actual."
        )
        if st.button(
            "Restaurar archivo originalmente cargado",
            use_container_width=True,
            key="mod_restore_original_v02",
        ):
            backup = st.session_state.get(SESSION_BACKUP_KEY)
            if isinstance(backup, pd.DataFrame):
                update_session_data(backup.copy(deep=True))
                st.session_state[SESSION_HISTORY_KEY] = []
                st.session_state.pop(SESSION_DOWNLOAD_KEY, None)
                st.session_state.pop(SESSION_DOWNLOAD_NAME_KEY, None)
                reset_draft()
                st.success("Se restauró la base originalmente cargada.")
                st.rerun()


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
    file_bytes = st.session_state.get(SESSION_FILE_BYTES_KEY, b"")

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
