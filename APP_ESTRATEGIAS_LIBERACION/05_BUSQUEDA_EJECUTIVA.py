# ============================================================
# 05_BUSQUEDA_EJECUTIVA
# APP_ESTRATEGIAS_LIBERACION
#
# Consulta rápida de flujos de liberación.
#
# Modos disponibles:
# 1. Buscar por CECO + tipo + monto.
# 2. Buscar por usuario y mostrar todos los CECO donde aparece.
#
# Formato esperado:
# CECO | Planta | Desde | Hasta | TipoDoc |
# Lib1 | Lib2 | Lib3 | Lib4 | Lib5
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

SESSION_MODE_KEY = "busqueda_ejecutiva_mode_v02"
SESSION_RESULT_KEY = "busqueda_ejecutiva_result_v02"
SESSION_CECO_KEY = "busqueda_ejecutiva_ceco_v02"
SESSION_DOC_KEY = "busqueda_ejecutiva_doc_v02"
SESSION_AMOUNT_KEY = "busqueda_ejecutiva_amount_v02"
SESSION_USER_KEY = "busqueda_ejecutiva_user_v02"
SESSION_USER_TEXT_KEY = "busqueda_ejecutiva_user_text_v02"

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
]

DOC_LABEL = {
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
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

MODE_LABEL = {
    "FLOW": "🔎 Buscar por CECO + tipo + monto",
    "USER": "👤 Buscar por usuario",
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


def strip_user_email(value: Any) -> str:
    text = clean_text(value)

    if not text or text == LS_LABEL:
        return text

    match = re.match(r"^(.*?)(?:\s+\([^)]+\))?$", text)
    return match.group(1).strip() if match else text


def email_key(value: Any) -> str:
    return strip_user_email(value).casefold()


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
        raise ValueError(
            f"Monto o rango no válido: {value!r}"
        ) from error


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
            }

            .executive-logo img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 88px;
                object-fit: contain;
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
                background: #F8FAFC;
                border: 2px solid #CBD5E1;
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

    except (OSError, UnicodeError) as error:
        st.warning(f"No fue posible leer el logo: {error}")


def render_header() -> None:
    mostrar_logo()

    st.markdown(
        '<div class="executive-title">05 Búsqueda Ejecutiva</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="executive-subtitle">
            Consulta un flujo por CECO o revisa todos los CECO
            donde participa un usuario.
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
    flow = raw_data.get("flujo")

    if not isinstance(flow, pd.DataFrame):
        raise ValueError(
            "No se encontró la hoja Flujo en la sesión."
        )

    flow = flow.copy()
    flow.columns = [
        str(column).strip()
        for column in flow.columns
    ]

    missing = [
        column
        for column in FLOW_COLUMNS
        if column not in flow.columns
    ]

    if missing:
        raise ValueError(
            "La base activa no tiene el formato vigente. "
            f"Faltan: {', '.join(missing)}."
        )

    flow = flow.loc[:, FLOW_COLUMNS].copy()
    flow["CECO"] = flow["CECO"].map(clean_text)
    flow["Planta"] = flow["Planta"].map(clean_text)
    flow["TipoDoc"] = (
        flow["TipoDoc"]
        .map(clean_text)
        .str.upper()
    )

    for column in LIB_COLS:
        flow[column] = flow[column].map(
            strip_user_email
        )

    flow = flow[
        flow["CECO"].ne("")
        & flow["TipoDoc"].isin(DOC_LABEL)
    ].reset_index(drop=True)

    users = raw_data.get(
        "dic_users",
        pd.DataFrame(),
    )

    if not isinstance(users, pd.DataFrame):
        users = pd.DataFrame()

    return {
        **raw_data,
        "flujo": flow,
        "dic_users": users.copy(),
    }


def cargo_map(
    data: dict[str, pd.DataFrame],
) -> dict[str, str]:
    users = data.get(
        "dic_users",
        pd.DataFrame(),
    )

    if not isinstance(users, pd.DataFrame) or users.empty:
        return {}

    email_column = next(
        (
            column
            for column in users.columns
            if str(column).strip().lower()
            in {"correo", "email", "mail"}
        ),
        None,
    )

    cargo_column = next(
        (
            column
            for column in users.columns
            if str(column).strip().lower()
            in {"cargo", "rol", "role"}
        ),
        None,
    )

    if email_column is None:
        return {}

    result: dict[str, str] = {}

    for _, row in users.iterrows():
        email = strip_user_email(
            row.get(email_column, "")
        )
        cargo = (
            clean_text(row.get(cargo_column, ""))
            if cargo_column is not None
            else ""
        )

        if email:
            result[email.casefold()] = cargo

    return result


def display_with_cargo(
    user: Any,
    data: dict[str, pd.DataFrame],
) -> str:
    email = strip_user_email(user)

    if not email or email == LS_LABEL:
        return email

    cargo = cargo_map(data).get(
        email.casefold(),
        "",
    )

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
        .loc[
            data["flujo"]["CECO"].eq(ceco),
            "Planta",
        ]
        .map(clean_text)
    )

    plants = (
        plants[plants.ne("")]
        .unique()
        .tolist()
    )

    return (
        f"{ceco} | {plants[0]}"
        if plants
        else ceco
    )


def docs_for_ceco(
    data: dict[str, pd.DataFrame],
    ceco: str,
) -> list[str]:
    docs = (
        data["flujo"]
        .loc[
            data["flujo"]["CECO"].eq(ceco),
            "TipoDoc",
        ]
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
        low = parse_bound(
            row["Desde"],
            low=True,
        )
        high = parse_bound(
            row["Hasta"],
            low=False,
        )

        if low <= amount <= high:
            return row

    return None


def libs_from_row(row: pd.Series) -> list[str]:
    return [
        strip_user_email(
            row.get(column, "")
        )
        for column in LIB_COLS
        if strip_user_email(
            row.get(column, "")
        )
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
        "planta": clean_text(
            selected_row.get("Planta", "")
        ),
        "doc": doc_type,
        "monto": amount,
        "desde": selected_row["Desde"],
        "hasta": selected_row["Hasta"],
        "libs": libs_from_row(selected_row),
    }


def unique_users(
    data: dict[str, pd.DataFrame],
) -> list[str]:
    flow = data["flujo"]

    return sorted(
        {
            strip_user_email(value)
            for column in LIB_COLS
            for value in flow[column].tolist()
            if strip_user_email(value)
        },
        key=str.casefold,
    )


def user_occurrences(
    data: dict[str, pd.DataFrame],
    user: str,
) -> pd.DataFrame:
    target = email_key(user)
    records: list[dict[str, Any]] = []

    if not target:
        return pd.DataFrame()

    flow = data["flujo"]

    for _, row in flow.iterrows():
        for position, column in enumerate(
            LIB_COLS,
            start=1,
        ):
            current = strip_user_email(
                row.get(column, "")
            )

            if email_key(current) != target:
                continue

            records.append(
                {
                    "CECO": row["CECO"],
                    "Planta": row["Planta"],
                    "TipoDoc": row["TipoDoc"],
                    "Desde": row["Desde"],
                    "Hasta": row["Hasta"],
                    "Posición": f"Liberador {position}",
                    "Usuario": current,
                }
            )

    if not records:
        return pd.DataFrame(
            columns=[
                "CECO",
                "Planta",
                "TipoDoc",
                "Desde",
                "Hasta",
                "Posición",
                "Usuario",
            ]
        )

    result = pd.DataFrame(records)
    result["_DesdeOrden"] = result["Desde"].map(
        lambda value: parse_bound(
            value,
            low=True,
        )
    )
    result["_TipoOrden"] = result["TipoDoc"].map(
        {"AZNB": 0, "AZSR": 1}
    ).fillna(99)

    return (
        result.sort_values(
            [
                "Planta",
                "CECO",
                "_TipoOrden",
                "_DesdeOrden",
                "Posición",
            ],
            kind="stable",
        )
        .drop(
            columns=[
                "_DesdeOrden",
                "_TipoOrden",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# RESULTADO DE FLUJO
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

    for index, user in enumerate(
        users,
        start=1,
    ):
        parts.append(
            compact_html(
                f"""
                <div class="flow-card">
                    <div style="
                        font-size:11px;
                        color:#64748B;
                        font-weight:700;
                    ">
                        Liberador {index}
                    </div>

                    <div style="
                        font-weight:700;
                        color:#17365D;
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
    metrics = [
        ("CECO", case["ceco"]),
        ("Planta", case["planta"] or "—"),
        (
            "Tipo",
            DOC_LABEL.get(
                case["doc"],
                case["doc"],
            ),
        ),
        ("Monto", fmt_money(case["monto"])),
        (
            "Tramo",
            f"{fmt_bound(case['desde'])} – "
            f"{fmt_bound(case['hasta'])}",
        ),
        ("Liberadores", str(len(case["libs"]))),
    ]

    doc_color = DOC_COLOR.get(
        case["doc"],
        "#17365D",
    )
    doc_background = DOC_BG.get(
        case["doc"],
        "#FFFFFF",
    )
    doc_border = DOC_BORDER.get(
        case["doc"],
        "#E2E8F0",
    )

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
                color:#17365D;
                font-size:18px;
                font-weight:850;
            ">
                Resultado de la consulta
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
# TABLAS
# ============================================================

def format_ceco_table(
    flow: pd.DataFrame,
    ceco: str,
) -> pd.DataFrame:
    table = flow[
        flow["CECO"].eq(ceco)
    ].copy()

    table["_DesdeOrden"] = table["Desde"].map(
        lambda value: parse_bound(
            value,
            low=True,
        )
    )
    table["_TipoOrden"] = table["TipoDoc"].map(
        {"AZNB": 0, "AZSR": 1}
    ).fillna(99)

    table = table.sort_values(
        [
            "_TipoOrden",
            "_DesdeOrden",
        ]
    )

    table = table[FLOW_COLUMNS].copy()
    table["Desde"] = table["Desde"].map(
        fmt_bound
    )
    table["Hasta"] = table["Hasta"].map(
        fmt_bound
    )

    for column in LIB_COLS:
        table[column] = table[column].map(
            strip_user_email
        )

    return table.reset_index(drop=True)


def style_flow_table(
    table: pd.DataFrame,
) -> pd.io.formats.style.Styler:
    def style_row(
        row: pd.Series,
    ) -> list[str]:
        doc = clean_text(
            row.get("TipoDoc", "")
        )

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
        .apply(
            style_row,
            axis=1,
        )
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

    table = format_ceco_table(
        data["flujo"],
        ceco,
    )

    if table.empty:
        st.info(
            "No existen reglas para el CECO seleccionado."
        )
        return

    st.caption(
        (
            f"{len(table):,} reglas encontradas para {ceco}. "
            "La tabla incluye todos los tramos de Material y Servicio."
        ).replace(",", ".")
    )

    st.dataframe(
        style_flow_table(table),
        use_container_width=True,
        hide_index=True,
        height=min(
            650,
            85 + len(table) * 35,
        ),
    )


def style_user_table(
    table: pd.DataFrame,
) -> pd.io.formats.style.Styler:
    def style_row(
        row: pd.Series,
    ) -> list[str]:
        doc = clean_text(
            row.get("TipoDoc", "")
        )

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
        .apply(
            style_row,
            axis=1,
        )
        .set_properties(
            **{
                "border-color": "#D0D5DD",
                "font-size": "12px",
            }
        )
    )


# ============================================================
# NODO INICIAL
# ============================================================

def render_initial_mode() -> str:
    question_node(
        1,
        "¿Cómo quieres realizar la búsqueda?",
        (
            "Busca un flujo por CECO, tipo y monto, "
            "o revisa todos los CECO donde aparece un usuario."
        ),
    )

    return st.selectbox(
        "Tipo de búsqueda",
        options=list(MODE_LABEL),
        format_func=lambda value: MODE_LABEL[value],
        key=SESSION_MODE_KEY,
        help=(
            "Selecciona el criterio que deseas utilizar "
            "para consultar la base activa."
        ),
    )


# ============================================================
# BÚSQUEDA POR CECO + TIPO + MONTO
# ============================================================

def render_flow_search(
    data: dict[str, pd.DataFrame],
) -> None:
    question_node(
        2,
        "¿Qué flujo quieres consultar?",
        (
            "Selecciona el CECO, indica si corresponde "
            "a Material o Servicio e ingresa el monto."
        ),
    )

    all_cecos = ceco_values(data)

    if not all_cecos:
        st.warning(
            "No existen CECO disponibles en la base activa."
        )
        return

    current_ceco = st.session_state.get(
        SESSION_CECO_KEY
    )

    if current_ceco not in all_cecos:
        st.session_state[SESSION_CECO_KEY] = (
            all_cecos[0]
        )

    ceco_column, doc_column, amount_column = (
        st.columns(
            [1.55, 1.15, 1.1],
            gap="medium",
        )
    )

    with ceco_column:
        selected_ceco = st.selectbox(
            "CECO",
            options=all_cecos,
            format_func=lambda value: ceco_label(
                data,
                value,
            ),
            key=SESSION_CECO_KEY,
        )

    available_docs = docs_for_ceco(
        data,
        selected_ceco,
    )

    if not available_docs:
        st.warning(
            "El CECO seleccionado no tiene registros "
            "de Material ni Servicio."
        )
        return

    current_doc = st.session_state.get(
        SESSION_DOC_KEY
    )

    if current_doc not in available_docs:
        st.session_state[SESSION_DOC_KEY] = (
            available_docs[0]
        )

    with doc_column:
        selected_doc = st.selectbox(
            "Tipo",
            options=available_docs,
            format_func=lambda value: DOC_LABEL[value],
            key=SESSION_DOC_KEY,
        )

    with amount_column:
        amount_text = st.text_input(
            "Monto",
            placeholder="Ejemplo: 5.000.000",
            key=SESSION_AMOUNT_KEY,
        )

    search_clicked = st.button(
        "🔎 Consultar flujo",
        type="primary",
        use_container_width=True,
        key="executive_flow_search_button_v02",
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

            st.session_state[SESSION_RESULT_KEY] = {
                "mode": "FLOW",
                "case": case,
            }

        except ValueError as error:
            st.session_state.pop(
                SESSION_RESULT_KEY,
                None,
            )
            st.error(str(error))

    result = st.session_state.get(
        SESSION_RESULT_KEY
    )

    if (
        isinstance(result, dict)
        and result.get("mode") == "FLOW"
    ):
        case = result.get("case", {})

        same_selection = (
            case.get("ceco") == selected_ceco
            and case.get("doc") == selected_doc
        )

        if same_selection:
            st.markdown("---")
            st.markdown(
                html_result(
                    case,
                    data,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "Presiona **Consultar flujo** para actualizar "
                "el resultado con la nueva selección."
            )

    with st.expander(
        f"Ver tramos disponibles para {selected_ceco}",
        expanded=False,
    ):
        table = format_ceco_table(
            data["flujo"],
            selected_ceco,
        )

        st.dataframe(
            style_flow_table(table),
            use_container_width=True,
            hide_index=True,
            height=min(
                650,
                85 + len(table) * 35,
            ),
        )

    if (
        isinstance(result, dict)
        and result.get("mode") == "FLOW"
        and result.get("case", {}).get("ceco")
        == selected_ceco
    ):
        render_ceco_table(
            data,
            selected_ceco,
        )


# ============================================================
# BÚSQUEDA POR USUARIO
# ============================================================

def render_user_search(
    data: dict[str, pd.DataFrame],
) -> None:
    question_node(
        2,
        "¿Qué usuario quieres consultar?",
        (
            "Selecciona un usuario existente o escribe un correo. "
            "La aplicación mostrará todos los CECO, tipos, tramos "
            "y posiciones donde participa."
        ),
    )

    users = unique_users(data)

    if not users:
        st.warning(
            "No se encontraron usuarios en los flujos activos."
        )
        return

    input_mode = st.radio(
        "Origen del usuario",
        options=["LIST", "TEXT"],
        format_func=lambda value: (
            "Seleccionar usuario existente"
            if value == "LIST"
            else "Escribir correo"
        ),
        horizontal=True,
        key="executive_user_input_mode_v02",
    )

    selected_user = ""

    if input_mode == "LIST":
        selected_user = st.selectbox(
            "Usuario",
            options=users,
            format_func=lambda value: display_with_cargo(
                value,
                data,
            ),
            key=SESSION_USER_KEY,
        )
    else:
        selected_user = strip_user_email(
            st.text_input(
                "Correo del usuario",
                placeholder="nombre.apellido@enaex.com",
                key=SESSION_USER_TEXT_KEY,
            )
        )

    search_clicked = st.button(
        "👤 Buscar apariciones del usuario",
        type="primary",
        use_container_width=True,
        key="executive_user_search_button_v02",
    )

    if search_clicked:
        if not selected_user:
            st.error(
                "Selecciona o escribe un usuario."
            )
        else:
            occurrences = user_occurrences(
                data,
                selected_user,
            )

            st.session_state[SESSION_RESULT_KEY] = {
                "mode": "USER",
                "user": selected_user,
                "occurrences": occurrences,
            }

    result = st.session_state.get(
        SESSION_RESULT_KEY
    )

    if not (
        isinstance(result, dict)
        and result.get("mode") == "USER"
    ):
        return

    result_user = clean_text(
        result.get("user", "")
    )

    if email_key(result_user) != email_key(selected_user):
        st.info(
            "Presiona **Buscar apariciones del usuario** "
            "para actualizar el resultado."
        )
        return

    occurrences = result.get(
        "occurrences",
        pd.DataFrame(),
    )

    if not isinstance(
        occurrences,
        pd.DataFrame,
    ):
        occurrences = pd.DataFrame()

    st.markdown("---")
    st.subheader("Resultado por usuario")

    if occurrences.empty:
        st.warning(
            f"No se encontraron apariciones para "
            f"**{display_with_cargo(result_user, data)}**."
        )
        return

    unique_cecos = int(
        occurrences["CECO"].nunique()
    )
    unique_plants = int(
        occurrences["Planta"].nunique()
    )
    unique_rows = int(
        occurrences[
            [
                "CECO",
                "TipoDoc",
                "Desde",
                "Hasta",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )
    total_positions = len(occurrences)

    metric_columns = st.columns(4)
    metrics = [
        ("CECO", unique_cecos),
        ("Plantas", unique_plants),
        ("Tramos", unique_rows),
        ("Apariciones", total_positions),
    ]

    for column, (label, value) in zip(
        metric_columns,
        metrics,
    ):
        column.metric(
            label,
            f"{value:,}".replace(",", "."),
        )

    st.success(
        f"Usuario consultado: "
        f"**{display_with_cargo(result_user, data)}**"
    )

    display = occurrences.copy()
    display["Tipo"] = display["TipoDoc"].map(
        DOC_LABEL
    )
    display["Desde"] = display["Desde"].map(
        fmt_bound
    )
    display["Hasta"] = display["Hasta"].map(
        fmt_bound
    )

    display = display[
        [
            "CECO",
            "Planta",
            "Tipo",
            "Desde",
            "Hasta",
            "Posición",
            "Usuario",
        ]
    ]

    st.dataframe(
        style_user_table(
            display.rename(
                columns={"Tipo": "TipoDoc"}
            )
        ).set_properties(
            subset=["TipoDoc"],
        ),
        use_container_width=True,
        hide_index=True,
        height=min(
            700,
            max(
                280,
                36 * (len(display) + 2),
            ),
        ),
    )

    st.markdown("#### Resumen por CECO")

    summary = (
        occurrences.groupby(
            [
                "CECO",
                "Planta",
                "TipoDoc",
            ],
            as_index=False,
        )
        .agg(
            Tramos=(
                "Desde",
                "count",
            ),
            Posiciones=(
                "Posición",
                lambda values: ", ".join(
                    sorted(set(values))
                ),
            ),
        )
    )

    summary["Tipo"] = summary["TipoDoc"].map(
        DOC_LABEL
    )

    summary = summary[
        [
            "CECO",
            "Planta",
            "Tipo",
            "Tramos",
            "Posiciones",
        ]
    ]

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
    )


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
            st.switch_page(
                "01_CARGAR_ARCHIVO_FLUJO.py"
            )
    except Exception:
        st.info(
            "Selecciona **01 Cargar archivo** "
            "desde la barra lateral."
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()

    raw_data = st.session_state.get(
        SESSION_DATA_KEY
    )

    if not isinstance(raw_data, dict):
        render_no_file()
        return

    try:
        data = prepare_data(raw_data)
    except ValueError as error:
        st.error(str(error))
        return

    flow = data["flujo"]
    file_name = st.session_state.get(
        SESSION_FILE_KEY,
        "Archivo cargado",
    )

    st.success(
        (
            f"Usando archivo activo: **{file_name}** · "
            f"**{len(flow):,} reglas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
        ).replace(",", ".")
    )

    mode = render_initial_mode()

    if mode == "FLOW":
        render_flow_search(data)
    else:
        render_user_search(data)


if __name__ == "__main__":
    main()
