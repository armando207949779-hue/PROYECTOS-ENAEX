# ============================================================
# 05_BUSQUEDA_EJECUTIVA
# APP_ESTRATEGIAS_LIBERACION
#
# Consulta rápida de flujos de liberación.
# No incluye simulación aleatoria ni modificación de datos.
#
# Flujo:
# 1. Seleccionar CECO
# 2. Seleccionar Material o Servicio
# 3. Ingresar monto
# 4. Consultar flujo
# ============================================================

from __future__ import annotations

import base64
import re
from html import escape
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

SESSION_RESULT_KEY = "busqueda_ejecutiva_result_v01"
SESSION_CECO_KEY = "busqueda_ejecutiva_ceco_v01"
SESSION_DOC_KEY = "busqueda_ejecutiva_doc_v01"
SESSION_AMOUNT_KEY = "busqueda_ejecutiva_amount_v01"

LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]

TABLE_COLS = [
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

DOC_LABEL = {
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
}

DOC_SHORT_LABEL = {
    "AZNB": "Material",
    "AZSR": "Servicio",
}

DOC_COLOR = {
    "AZNB": "#B42318",
    "AZSR": "#175CD3",
}

DOC_BG = {
    "AZNB": "#FFF1F0",
    "AZSR": "#EFF8FF",
}

DOC_BORDER = {
    "AZNB": "#FDA29B",
    "AZSR": "#84CAFF",
}

LS_LABEL = "Liberador Servicios"


# ============================================================
# UTILIDADES
# ============================================================

def compact_html(value: str) -> str:
    return re.sub(r">\s+<", "><", dedent(value).strip())


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


def strip_user_email(value: Any) -> str:
    text = clean_text(value)
    if not text or text == LS_LABEL:
        return text

    match = re.match(r"^(.*?)(?:\s*\(([^)]+)\))?$", text)
    return match.group(1).strip() if match else text


def parse_bound(value: Any, low: bool = True) -> float:
    text = clean_text(value)

    if text in {"", "*"}:
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
    except ValueError as error:
        raise ValueError(f"Monto o rango no válido: {value!r}") from error


def parse_amount(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None

    amount = parse_bound(text, low=True)

    if amount < 0:
        raise ValueError("El monto no puede ser negativo.")

    return int(round(amount))


def fmt_bound(value: Any) -> str:
    text = clean_text(value)

    if text == "*":
        return "*"

    try:
        number = parse_bound(value, low=False)

        if number >= 1e15:
            return "*"

        if number >= 1e12:
            return "1E+12"

        return f"{int(number):,}".replace(",", ".")
    except (TypeError, ValueError):
        return text


def fmt_money(value: int | float) -> str:
    return f"$ {int(value):,}".replace(",", ".")


def normalize_int(value: Any) -> int:
    try:
        if value is None or pd.isna(value):
            return 0
        return int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError):
        return 0


def normalize_yes(value: Any) -> bool:
    return clean_text(value).upper() in {
        "SI",
        "SÍ",
        "YES",
        "TRUE",
        "1",
    }


# ============================================================
# ESTILOS Y LOGO
# ============================================================

def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer,
            .block-container {
                padding-top: 6.5rem !important;
                padding-bottom: 2.5rem !important;
            }

            .executive-logo {
                width: 100%;
                min-height: 90px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: .6rem 0 12px;
                overflow: visible;
            }

            .executive-logo img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 88px;
                object-fit: contain;
                display: block;
            }

            .executive-title {
                text-align: center;
                color: #17365D;
                font-size: 2rem;
                font-weight: 850;
                margin: .2rem 0;
            }

            .executive-subtitle {
                text-align: center;
                color: #64748B;
                font-size: 1rem;
                margin-bottom: 1.2rem;
            }

            .question-node {
                padding: 17px 19px;
                border-radius: 16px;
                border: 2px solid #93C5FD;
                background: linear-gradient(
                    135deg,
                    #EFF6FF 0%,
                    #F8FAFC 100%
                );
                margin: .7rem 0 1rem;
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
                font-size: 1.18rem;
                font-weight: 850;
            }

            .question-help {
                color: #64748B;
                font-size: .9rem;
                margin-top: 7px;
            }

            .result-card {
                font-family: Arial, sans-serif;
                padding: 17px;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 15px;
                box-shadow: 0 1px 3px rgba(15, 23, 42, .06);
            }

            .metric-card {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 11px 13px;
                background: #FFFFFF;
                min-height: 78px;
            }

            .metric-label {
                color: #64748B;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: .03em;
            }

            .metric-value {
                color: #17365D;
                font-size: 17px;
                font-weight: 850;
                margin-top: 5px;
                word-break: break-word;
            }

            .flow-card {
                min-width: 170px;
                max-width: 225px;
                border-radius: 12px;
                padding: 11px;
                font-family: Arial, sans-serif;
            }

            .legend {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin: 6px 0 10px;
            }

            .legend-pill {
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 700;
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


def mostrar_logo() -> None:
    path = next(
        (
            candidate
            for candidate in LOGO_CANDIDATES
            if candidate.exists() and candidate.is_file()
        ),
        None,
    )

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
            (
                f'<div class="executive-logo">'
                f'<img src="data:{mime};base64,{encoded}" '
                f'alt="Logo ENAEX"></div>'
            ),
            unsafe_allow_html=True,
        )
    except (OSError, UnicodeError):
        st.warning(f"No fue posible leer el logo: {path.name}")


def render_header() -> None:
    mostrar_logo()

    st.markdown(
        '<div class="executive-title">05 Búsqueda Ejecutiva</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="executive-subtitle">
            Consulta rápida del flujo de liberación por CECO,
            tipo de documento y monto.
        </div>
        """,
        unsafe_allow_html=True,
    )


def question_node(
    number: int,
    title: str,
    help_text: str,
) -> None:
    st.markdown(
        compact_html(
            f"""
            <div class="question-node">
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
# DATOS
# ============================================================

def prepare_data(
    raw_data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    if "flujo" not in raw_data:
        raise ValueError("No se encontró la hoja Flujo en la sesión.")

    flow = raw_data["flujo"].copy()
    flow.columns = [str(column).strip() for column in flow.columns]

    for column in TABLE_COLS:
        if column not in flow.columns:
            flow[column] = ""

    flow["CECO"] = flow["CECO"].map(clean_text)
    flow["Planta"] = flow["Planta"].map(clean_text)
    flow["TipoDoc"] = flow["TipoDoc"].map(clean_text).str.upper()

    for column in LIB_COLS:
        flow[column] = flow[column].map(strip_user_email)

    flow = flow[
        flow["CECO"].ne("")
        & flow["TipoDoc"].isin(DOC_LABEL)
    ].reset_index(drop=True)

    users = raw_data.get("dic_users", pd.DataFrame()).copy()

    return {
        **raw_data,
        "flujo": flow,
        "dic_users": users,
    }


def cargo_map(
    data: dict[str, pd.DataFrame],
) -> dict[str, str]:
    users = data.get("dic_users", pd.DataFrame())

    if not isinstance(users, pd.DataFrame) or users.empty:
        return {}

    email_column = next(
        (
            column
            for column in users.columns
            if str(column).strip().lower() in {
                "correo",
                "email",
                "mail",
            }
        ),
        None,
    )

    cargo_column = next(
        (
            column
            for column in users.columns
            if str(column).strip().lower() in {
                "cargo",
                "rol",
                "role",
            }
        ),
        None,
    )

    if email_column is None:
        return {}

    result: dict[str, str] = {}

    for _, row in users.iterrows():
        email = strip_user_email(row.get(email_column, ""))
        cargo = (
            clean_text(row.get(cargo_column, ""))
            if cargo_column is not None
            else ""
        )

        if email:
            result[email.lower()] = cargo

    return result


def display_with_cargo(
    user: Any,
    data: dict[str, pd.DataFrame],
) -> str:
    email = strip_user_email(user)

    if not email or email == LS_LABEL:
        return email

    cargo = cargo_map(data).get(email.lower(), "")

    return (
        email
        if not cargo or cargo == LS_LABEL
        else f"{email} ({cargo})"
    )


def ceco_values(
    data: dict[str, pd.DataFrame],
) -> list[str]:
    return sorted(
        data["flujo"]["CECO"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def ceco_label(
    data: dict[str, pd.DataFrame],
    ceco: str,
) -> str:
    plants = (
        data["flujo"]
        .loc[data["flujo"]["CECO"].eq(ceco), "Planta"]
        .map(clean_text)
    )

    plants = plants[plants.ne("")].unique().tolist()

    return f"{ceco} | {plants[0]}" if plants else ceco


def docs_for_ceco(
    data: dict[str, pd.DataFrame],
    ceco: str,
) -> list[str]:
    docs = (
        data["flujo"]
        .loc[data["flujo"]["CECO"].eq(ceco), "TipoDoc"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    return [
        doc
        for doc in ["AZNB", "AZSR"]
        if doc in docs
    ]


def pick_row(
    flow: pd.DataFrame,
    ceco: str,
    doc_type: str,
    amount: int | float,
) -> pd.Series | None:
    subset = flow[
        flow["CECO"].eq(ceco)
        & flow["TipoDoc"].eq(doc_type)
    ]

    for _, row in subset.iterrows():
        low = parse_bound(row["Desde"], low=True)
        high = parse_bound(row["Hasta"], low=False)

        if low <= amount <= high:
            return row

    return None


def libs_from_row(row: pd.Series) -> list[str]:
    return [
        strip_user_email(row.get(column, ""))
        for column in LIB_COLS
        if strip_user_email(row.get(column, ""))
    ]


def build_case(
    data: dict[str, pd.DataFrame],
    ceco: str,
    doc_type: str,
    amount: int,
) -> dict[str, Any]:
    selected_row = pick_row(
        data["flujo"],
        ceco,
        doc_type,
        amount,
    )

    if selected_row is None:
        raise ValueError(
            "No se encontró un tramo para el CECO, tipo y monto "
            "seleccionados. Revisa la tabla de reglas."
        )

    return {
        "ceco": ceco,
        "planta": clean_text(selected_row.get("Planta", "")),
        "doc": doc_type,
        "monto": amount,
        "desde": selected_row["Desde"],
        "hasta": selected_row["Hasta"],
        "match": normalize_yes(selected_row.get("Match", "")),
        "n_eo": normalize_int(selected_row.get("N_EO", 0)),
        "n_cd": normalize_int(selected_row.get("N_CD", 0)),
        "fuente_cd": clean_text(selected_row.get("FuenteCD", "")),
        "libs": libs_from_row(selected_row),
    }


# ============================================================
# RESULTADO
# ============================================================

def html_flow(
    case: dict[str, Any],
    data: dict[str, pd.DataFrame],
) -> str:
    users = [
        user
        for user in case["libs"]
        if clean_text(user)
    ]

    if not users:
        return (
            "<p style='font-family:Arial;color:#64748B;'>"
            "El tramo no tiene liberadores registrados.</p>"
        )

    range_text = (
        f"{fmt_bound(case['desde'])} – "
        f"{fmt_bound(case['hasta'])}"
    )

    parts: list[str] = []

    for index, user in enumerate(users, start=1):
        is_eo = index <= case["n_eo"]

        if is_eo:
            background = "#EAF7EE"
            border = "#7BC596"
            text_color = "#166534"
            group = "EO"
        else:
            background = "#F8FAFC"
            border = "#CBD5E1"
            text_color = "#1E3A8A"
            group = "CD"

        parts.append(
            compact_html(
                f"""
                <div class="flow-card"
                     style="background:{background};
                            border:2px solid {border};">
                    <div style="
                        font-size:11px;
                        color:#64748B;
                        font-weight:700;
                    ">
                        Liberador {index} · {group}
                    </div>

                    <div style="
                        font-weight:700;
                        color:{text_color};
                        margin:6px 0;
                        overflow-wrap:anywhere;
                        font-size:12px;
                    ">
                        {escape(display_with_cargo(user, data))}
                    </div>

                    <div style="
                        font-size:10px;
                        color:#64748B;
                    ">
                        {escape(range_text)}
                    </div>
                </div>
                """
            )
        )

        if index < len(users):
            parts.append(
                "<div style='font-size:21px;color:#94A3B8;"
                "font-weight:700;'>→</div>"
            )

    return compact_html(
        """
        <div style="font-family:Arial;margin-top:14px;">
            <div style="
                font-weight:850;
                color:#17365D;
                margin-bottom:8px;
            ">
                Flujo de liberación
            </div>

            <div style="
                display:flex;
                flex-wrap:wrap;
                align-items:center;
                gap:7px;
            ">
        """
        + "".join(parts)
        + "</div></div>"
    )


def html_result(
    case: dict[str, Any],
    data: dict[str, pd.DataFrame],
) -> str:
    if case["match"]:
        badge = (
            "<span style='background:#166534;color:#FFF;"
            "padding:3px 9px;border-radius:999px;"
            "font-size:11px;font-weight:700;'>MATCH</span>"
        )
    else:
        badge = (
            "<span style='background:#C2410C;color:#FFF;"
            "padding:3px 9px;border-radius:999px;"
            "font-size:11px;font-weight:700;'>SIN MATCH</span>"
        )

    metrics = [
        ("CECO", case["ceco"]),
        ("Planta", case["planta"] or "—"),
        ("Tipo", DOC_LABEL.get(case["doc"], case["doc"])),
        ("Monto", fmt_money(case["monto"])),
        (
            "Tramo",
            f"{fmt_bound(case['desde'])} – "
            f"{fmt_bound(case['hasta'])}",
        ),
        ("Liberadores", str(len(case["libs"]))),
    ]

    doc_color = DOC_COLOR.get(case["doc"], "#17365D")
    doc_background = DOC_BG.get(case["doc"], "#FFFFFF")
    doc_border = DOC_BORDER.get(case["doc"], "#E2E8F0")

    metric_html = "".join(
        compact_html(
            f"""
            <div class="metric-card"
                 style="{
                    'background:' + doc_background
                    + ';border-color:' + doc_border + ';'
                    if label == 'Tipo'
                    else ''
                 }">
                <div class="metric-label">
                    {escape(label)}
                </div>

                <div class="metric-value"
                     style="{
                        'color:' + doc_color + ';'
                        if label == 'Tipo'
                        else ''
                     }">
                    {escape(value)}
                </div>
            </div>
            """
        )
        for label, value in metrics
    )

    return compact_html(
        f"""
        <div class="result-card"
             style="border-top:4px solid {doc_color};">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:12px;
            ">
                <div style="
                    color:#17365D;
                    font-size:18px;
                    font-weight:850;
                ">
                    Resultado de la consulta
                </div>
                {badge}
            </div>

            <div style="
                display:grid;
                grid-template-columns:
                    repeat(auto-fit,minmax(150px,1fr));
                gap:9px;
                margin-top:13px;
            ">
                {metric_html}
            </div>

            {html_flow(case, data)}
        </div>
        """
    )


# ============================================================
# TABLA DEL CECO
# ============================================================

def format_ceco_table(
    flow: pd.DataFrame,
    ceco: str,
) -> pd.DataFrame:
    table = flow[flow["CECO"].eq(ceco)].copy()

    table["_DesdeOrden"] = table["Desde"].map(
        lambda value: parse_bound(value, low=True)
    )

    table["_TipoOrden"] = table["TipoDoc"].map(
        {"AZNB": 0, "AZSR": 1}
    ).fillna(99)

    table = table.sort_values(
        ["_TipoOrden", "_DesdeOrden"]
    )

    available_columns = [
        column
        for column in TABLE_COLS
        if column in table.columns
    ]

    table = table[available_columns].copy()

    table["Desde"] = table["Desde"].map(fmt_bound)
    table["Hasta"] = table["Hasta"].map(fmt_bound)

    for column in LIB_COLS:
        if column in table.columns:
            table[column] = table[column].map(strip_user_email)

    if "N_EO" in table.columns:
        table["N_EO"] = table["N_EO"].map(normalize_int)

    if "N_CD" in table.columns:
        table["N_CD"] = table["N_CD"].map(normalize_int)

    return table.reset_index(drop=True)


def style_ceco_table(
    table: pd.DataFrame,
) -> pd.io.formats.style.Styler:
    def style_row(row: pd.Series) -> list[str]:
        doc = clean_text(row.get("TipoDoc", ""))

        if doc == "AZNB":
            style = (
                "background-color:#FFF1F0;"
                "color:#7A271A;"
            )
        elif doc == "AZSR":
            style = (
                "background-color:#EFF8FF;"
                "color:#1849A9;"
            )
        else:
            style = ""

        return [style] * len(row)

    return (
        table.style
        .apply(style_row, axis=1)
        .set_properties(
            **{
                "border-color": "#D0D5DD",
                "font-size": "12px",
            }
        )
    )


def render_ceco_table(
    data: dict[str, pd.DataFrame],
    ceco: str,
) -> None:
    st.markdown("---")
    st.subheader("Reglas del CECO")

    st.markdown(
        compact_html(
            f"""
            <div class="legend">
                <span class="legend-pill"
                      style="
                        background:{DOC_BG['AZNB']};
                        color:{DOC_COLOR['AZNB']};
                        border:1px solid {DOC_BORDER['AZNB']};
                      ">
                    Material · AZNB
                </span>

                <span class="legend-pill"
                      style="
                        background:{DOC_BG['AZSR']};
                        color:{DOC_COLOR['AZSR']};
                        border:1px solid {DOC_BORDER['AZSR']};
                      ">
                    Servicio · AZSR
                </span>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    table = format_ceco_table(data["flujo"], ceco)

    if table.empty:
        st.info("No existen reglas para el CECO seleccionado.")
        return

    st.caption(
        (
            f"{len(table):,} reglas encontradas para {ceco}. "
            "La tabla incluye todos los tramos de Material y Servicio."
        ).replace(",", ".")
    )

    st.dataframe(
        style_ceco_table(table),
        use_container_width=True,
        hide_index=True,
        height=min(650, 85 + len(table) * 35),
    )


# ============================================================
# BÚSQUEDA
# ============================================================

def render_search(
    data: dict[str, pd.DataFrame],
) -> None:
    flow = data["flujo"]
    file_name = st.session_state.get(
        SESSION_FILE_KEY,
        "Archivo cargado",
    )

    st.success(
        (
            f"Usando archivo activo: **{file_name}** · "
            f"**{len(flow):,} filas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
        ).replace(",", ".")
    )

    question_node(
        1,
        "¿Qué flujo quieres consultar?",
        (
            "Selecciona el CECO, indica si corresponde a Material "
            "o Servicio e ingresa el monto."
        ),
    )

    all_cecos = ceco_values(data)

    if not all_cecos:
        st.warning("No existen CECO disponibles en la base activa.")
        return

    current_ceco = st.session_state.get(SESSION_CECO_KEY)

    if current_ceco not in all_cecos:
        st.session_state[SESSION_CECO_KEY] = all_cecos[0]

    ceco_col, doc_col, amount_col = st.columns(
        [1.55, 1.15, 1.1],
        gap="medium",
    )

    with ceco_col:
        selected_ceco = st.selectbox(
            "CECO",
            options=all_cecos,
            format_func=lambda value: ceco_label(data, value),
            key=SESSION_CECO_KEY,
        )

    available_docs = docs_for_ceco(data, selected_ceco)

    if not available_docs:
        st.warning(
            "El CECO seleccionado no tiene registros de "
            "Material ni Servicio."
        )
        return

    current_doc = st.session_state.get(SESSION_DOC_KEY)

    if current_doc not in available_docs:
        st.session_state[SESSION_DOC_KEY] = available_docs[0]

    with doc_col:
        selected_doc = st.selectbox(
            "Tipo",
            options=available_docs,
            format_func=lambda value: DOC_LABEL[value],
            key=SESSION_DOC_KEY,
        )

    with amount_col:
        amount_text = st.text_input(
            "Monto",
            placeholder="Ejemplo: 5.000.000",
            key=SESSION_AMOUNT_KEY,
        )

    search_clicked = st.button(
        "🔎 Consultar flujo",
        type="primary",
        use_container_width=True,
        key="executive_search_button_v01",
    )

    if search_clicked:
        try:
            amount = parse_amount(amount_text)

            if amount is None:
                raise ValueError(
                    "Ingresa un monto para realizar la consulta."
                )

            case = build_case(
                data=data,
                ceco=selected_ceco,
                doc_type=selected_doc,
                amount=amount,
            )

            st.session_state[SESSION_RESULT_KEY] = case

        except ValueError as error:
            st.session_state.pop(SESSION_RESULT_KEY, None)
            st.error(str(error))

    result = st.session_state.get(SESSION_RESULT_KEY)

    if result:
        # Si se cambia manualmente el CECO o tipo, no muestra un
        # resultado antiguo correspondiente a otra selección.
        same_selection = (
            result["ceco"] == selected_ceco
            and result["doc"] == selected_doc
        )

        if same_selection:
            st.markdown("---")
            st.markdown(
                html_result(result, data),
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "Presiona **Consultar flujo** para actualizar el resultado "
                "con la nueva selección."
            )

    with st.expander(
        f"Ver tramos disponibles para {selected_ceco}",
        expanded=False,
    ):
        table = format_ceco_table(data["flujo"], selected_ceco)

        st.dataframe(
            style_ceco_table(table),
            use_container_width=True,
            hide_index=True,
            height=min(650, 85 + len(table) * 35),
        )

    if result and result["ceco"] == selected_ceco:
        render_ceco_table(data, selected_ceco)


# ============================================================
# SIN ARCHIVO
# ============================================================

def render_no_file() -> None:
    st.warning(
        "No hay un archivo activo. Primero carga la base en "
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
            "Selecciona **01 Cargar archivo** desde la barra lateral."
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()

    raw_data = st.session_state.get(SESSION_DATA_KEY)

    if not isinstance(raw_data, dict):
        render_no_file()
        return

    try:
        data = prepare_data(raw_data)
    except ValueError as error:
        st.error(str(error))
        return

    render_search(data)


if __name__ == "__main__":
    main()
