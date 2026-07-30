# ============================================================
# 02_APP_SIMULADOR_ALEATORIO
# APP_ESTRATEGIAS_LIBERACION
#
# Lee los siete archivos cargados por 01_CARGAR_ARCHIVO_FLUJO:
# Liberador 1–5, Diccionario CECO-Plantas y
# Diccionario Usuarios-Cargos.
#
# Flujo interno esperado:
# CECO | Planta | Desde | Hasta | TipoDoc |
# Lib1 | Lib2 | Lib3 | Lib4 | Lib5
# ============================================================

from __future__ import annotations

import base64
import random
import re
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN Y CONSTANTES
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
]

LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]
TABLE_COLS = [
    "CECO", "Planta", "Desde", "Hasta", "TipoDoc",
    "Lib1", "Lib2", "Lib3", "Lib4", "Lib5",
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

LEVELS = (1, 2, 3, 4, 5)
FILE_ROLE_CECO = "dic_ceco"
FILE_ROLE_USERS = "dic_users"
FILE_ROLE_LIBERATORS = {
    level: f"liberador_{level}"
    for level in LEVELS
}

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_CASE_KEY = "flujo_liberacion_last_case"
SESSION_SOURCE_FILES_KEY = "flujo_liberacion_source_files_v05"
SESSION_EDITOR_CECO = "sim_editor_ceco_v03"
SESSION_EDITOR_DOC = "sim_editor_doc_v03"
SESSION_EDITOR_AMOUNT = "sim_editor_amount_v03"
SESSION_PENDING_EDITOR = "sim_pending_editor_v03"
SESSION_HISTORY_KEY = "sim_case_history_v04"



# ============================================================
# UTILIDADES GENERALES
# ============================================================

def compact_html(value: str) -> str:
    value = dedent(value).strip()
    return re.sub(r">\s+<", "><", value)


def clean_user(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "null", "<na>", "n/a", "no usar", "—", "-"} else text


def strip_user_email(value: Any) -> str:
    text = clean_user(value)
    if not text or text == LS_LABEL:
        return text

    match = re.match(r"^(.*?)(?:\s*\(([^)]+)\))?$", text)
    return match.group(1).strip() if match else text


def parse_bound(value: Any, low: bool = True) -> float:
    text = clean_user(value)
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
    except ValueError as exc:
        raise ValueError(f"Valor de rango no válido: {value!r}") from exc


def parse_amount(value: Any) -> int | None:
    text = clean_user(value)
    if not text:
        return None

    amount = parse_bound(text, low=True)
    if amount < 0:
        raise ValueError("El monto no puede ser negativo.")

    return int(round(amount))


def fmt_bound(value: Any) -> str:
    text = clean_user(value)
    if text == "*":
        return "*"

    try:
        number = parse_bound(value, low=False)
        if number >= 1e15:
            return "*"
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
            .stMainBlockContainer, .block-container {
                padding-top: 6.5rem !important;
                padding-bottom: 2.5rem;
            }

            .fl-logo-wrap {
                width: 100%;
                min-height: 90px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: .6rem 0 12px;
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
                font-weight: 800;
                margin: .2rem 0;
            }

            .fl-subtitle {
                text-align: center;
                color: #64748B;
                font-size: 1rem;
                margin-bottom: 1.2rem;
            }

            .fl-section-title {
                color: #17365D;
                font-size: 1.1rem;
                font-weight: 800;
                margin: .4rem 0 .6rem;
            }

            .fl-card {
                font-family: Arial, sans-serif;
                padding: 16px;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                box-shadow: 0 1px 2px rgba(15, 23, 42, .05);
            }

            .fl-metric {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 11px 13px;
                background: #FFFFFF;
                min-height: 78px;
            }

            .fl-metric-label {
                color: #64748B;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: .03em;
            }

            .fl-metric-value {
                color: #17365D;
                font-size: 17px;
                font-weight: 800;
                margin-top: 5px;
                word-break: break-word;
            }

            .fl-help-box {
                padding: 12px 14px;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #175CD3;
                border-radius: 10px;
                color: #475467;
                font-size: 13px;
                margin-bottom: 12px;
            }

            .fl-doc-legend {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin: 6px 0 10px;
            }

            .fl-doc-pill {
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 700;
            }

            .fl-question-node {
                padding: 17px 19px;
                border-radius: 16px;
                border: 2px solid #93C5FD;
                background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
                margin: .7rem 0 1rem;
            }

            .fl-question-number {
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

            .fl-question-title {
                color: #17365D;
                font-size: 1.18rem;
                font-weight: 800;
            }

            .fl-question-help {
                color: #64748B;
                font-size: .9rem;
                margin-top: 7px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_logo() -> None:
    path = next((p for p in LOGO_CANDIDATES if p.exists() and p.is_file()), None)
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
            f'<div class="fl-logo-wrap"><img src="data:{mime};base64,{encoded}" alt="Logo"></div>',
            unsafe_allow_html=True,
        )
    except (OSError, UnicodeError):
        st.warning(f"No fue posible leer el logo: {path.name}")


# ============================================================
# DATOS Y REGLAS DEL FLUJO
# ============================================================

def validate_flow_schema(data: dict[str, Any]) -> pd.DataFrame:
    """Valida la versión reconstruida desde los siete archivos."""
    if not isinstance(data, dict):
        raise ValueError(
            "No existe una versión activa. Carga los siete archivos "
            "desde 01 Cargar Versión."
        )

    flow = data.get("flujo")
    if not isinstance(flow, pd.DataFrame) or flow.empty:
        raise ValueError(
            "La versión activa no contiene un flujo reconstruido válido."
        )

    required = [
        "CECO", "Planta", "Desde", "Hasta", "TipoDoc",
        "Lib1", "Lib2", "Lib3", "Lib4", "Lib5",
    ]
    missing = [column for column in required if column not in flow.columns]

    if missing:
        raise ValueError(
            "El flujo reconstruido no tiene la estructura requerida. "
            f"Faltan: {', '.join(missing)}."
        )

    liberadores = data.get("liberadores")
    if not isinstance(liberadores, dict):
        raise ValueError(
            "La versión activa no conserva los cinco liberadores."
        )

    missing_levels = [
        level
        for level in LEVELS
        if not isinstance(liberadores.get(level), pd.DataFrame)
    ]
    if missing_levels:
        raise ValueError(
            "Faltan niveles: "
            + ", ".join(
                f"Liberador {level}"
                for level in missing_levels
            )
            + "."
        )

    ceco_dictionary = data.get("dic_ceco")
    if not isinstance(ceco_dictionary, pd.DataFrame):
        raise ValueError(
            "No se encontró el Diccionario CECO-Plantas."
        )

    ceco_missing_columns = [
        column
        for column in ["CECO", "Planta"]
        if column not in ceco_dictionary.columns
    ]
    if ceco_missing_columns:
        raise ValueError(
            "El Diccionario CECO-Plantas no tiene las columnas: "
            + ", ".join(ceco_missing_columns)
            + "."
        )

    users_dictionary = data.get("dic_users")
    if not isinstance(users_dictionary, pd.DataFrame):
        raise ValueError(
            "No se encontró el Diccionario Usuarios-Cargos."
        )

    users_missing_columns = [
        column
        for column in ["Correo", "Cargo"]
        if column not in users_dictionary.columns
    ]
    if users_missing_columns:
        raise ValueError(
            "El Diccionario Usuarios-Cargos no tiene las columnas: "
            + ", ".join(users_missing_columns)
            + "."
        )

    return flow



def cargo_map(data: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    users = data.get("dic_users", pd.DataFrame())

    if not isinstance(users, pd.DataFrame) or users.empty:
        return mapping

    for _, row in users.iterrows():
        email = strip_user_email(row.get("Correo", ""))
        cargo = clean_user(row.get("Cargo", ""))
        if email:
            mapping[email.lower()] = cargo

    return mapping


def display_with_cargo(user: Any, data: dict[str, pd.DataFrame]) -> str:
    email = strip_user_email(user)
    if not email or email == LS_LABEL:
        return email

    cargo = cargo_map(data).get(email.lower(), "")
    return email if not cargo or cargo == LS_LABEL else f"{email} ({cargo})"

def ceco_dictionary_map(
    data: dict[str, Any],
) -> dict[str, dict[str, str]]:
    dictionary = data.get("dic_ceco", pd.DataFrame())
    if not isinstance(dictionary, pd.DataFrame) or dictionary.empty:
        return {}

    mapping: dict[str, dict[str, str]] = {}

    for _, row in dictionary.iterrows():
        ceco = clean_user(row.get("CECO", ""))
        if not ceco:
            continue

        mapping[ceco] = {
            "planta": clean_user(row.get("Planta", "")),
            "centro": clean_user(row.get("Centro", "")),
        }

    return mapping


def ceco_metadata(
    data: dict[str, Any],
    ceco: str,
) -> dict[str, str]:
    return ceco_dictionary_map(data).get(
        clean_user(ceco),
        {"planta": "", "centro": ""},
    )


def users_not_in_dictionary(
    data: dict[str, Any],
) -> list[str]:
    flow = validate_flow_schema(data)
    known = set(cargo_map(data))

    users = {
        strip_user_email(value).lower()
        for column in LIB_COLS
        for value in flow[column].tolist()
        if strip_user_email(value)
        and strip_user_email(value) != LS_LABEL
    }

    return sorted(user for user in users if user not in known)



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
        desde = parse_bound(row["Desde"], low=True)
        hasta = parse_bound(row["Hasta"], low=False)
        if desde <= amount <= hasta:
            return row

    return None


def libs_from_row(row: pd.Series) -> list[str]:
    return [
        strip_user_email(row[column])
        for column in LIB_COLS
        if strip_user_email(row[column])
    ]


def random_amount_for_row(row: pd.Series) -> int:
    low = max(0, int(parse_bound(row["Desde"], low=True)))
    high_value = parse_bound(row["Hasta"], low=False)

    # Evita generar montos excesivamente alejados cuando el último tramo
    # termina en 1E+12 o en un límite abierto.
    high = min(int(high_value), low + 250_000_000)
    if high_value >= 1e17:
        high = low + 250_000_000

    if high < low:
        raise ValueError("El rango seleccionado tiene límites inconsistentes.")

    return random.randint(low, high)


def build_case(
    data: dict[str, pd.DataFrame],
    ceco: str,
    doc_type: str | None = None,
    amount: int | None = None,
) -> dict[str, Any]:
    flow = validate_flow_schema(data)
    ceco = clean_user(ceco)

    docs = sorted(
        flow.loc[flow["CECO"].eq(ceco), "TipoDoc"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    docs = [doc for doc in docs if doc in DOC_LABEL]

    if not docs:
        raise ValueError(f"No existen datos válidos para el CECO {ceco}.")

    if doc_type is None:
        doc_type = random.choice(docs)

    if doc_type not in docs:
        raise ValueError(
            f"El CECO {ceco} no tiene registros para "
            f"{DOC_LABEL.get(doc_type, doc_type)}."
        )

    rows = flow[
        flow["CECO"].eq(ceco)
        & flow["TipoDoc"].eq(doc_type)
    ]

    if amount is None:
        selected_row = rows.sample(n=1).iloc[0]
        amount = random_amount_for_row(selected_row)
    else:
        selected_row = pick_row(flow, ceco, doc_type, amount)

    if selected_row is None:
        raise ValueError(
            "No se encontró un tramo para la combinación de CECO, tipo y monto indicada. "
            "Revisa la tabla de reglas del CECO."
        )

    metadata = ceco_metadata(data, ceco)

    return {
        "ceco": ceco,
        "planta": metadata.get("planta", "")
        or clean_user(selected_row.get("Planta", "")),
        "centro": metadata.get("centro", ""),
        "doc": doc_type,
        "monto": int(amount),
        "desde": selected_row["Desde"],
        "hasta": selected_row["Hasta"],
        "libs": libs_from_row(selected_row),
    }


def available_pairs(
    data: dict[str, pd.DataFrame],
    doc_filter: str,
) -> list[tuple[str, str]]:
    flow = validate_flow_schema(data)

    if doc_filter in DOC_LABEL:
        flow = flow[flow["TipoDoc"].eq(doc_filter)]

    return [
        (str(ceco), str(doc))
        for ceco, doc in flow[["CECO", "TipoDoc"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
        if doc in DOC_LABEL
    ]


def ceco_values(data: dict[str, Any]) -> list[str]:
    flow = validate_flow_schema(data)
    return sorted(
        flow["CECO"].dropna().astype(str).unique().tolist()
    )


def ceco_label(data: dict[str, Any], ceco: str) -> str:
    metadata = ceco_metadata(data, ceco)
    details = [
        value
        for value in [
            metadata.get("planta", ""),
            metadata.get("centro", ""),
        ]
        if value
    ]

    return (
        f"{ceco} | {' | '.join(details)}"
        if details
        else ceco
    )



def docs_for_ceco(data: dict[str, pd.DataFrame], ceco: str) -> list[str]:
    flow = validate_flow_schema(data)
    docs = (
        flow.loc[flow["CECO"].eq(ceco), "TipoDoc"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    return [doc for doc in ["AZNB", "AZSR"] if doc in docs]


# ============================================================
# COMPONENTES VISUALES DEL RESULTADO
# ============================================================

def html_flow(case: dict[str, Any], data: dict[str, pd.DataFrame]) -> str:
    users = [user for user in case["libs"] if clean_user(user)]

    if not users:
        return (
            "<p style='font-family:Arial;color:#64748B;'>"
            "El tramo no tiene liberadores registrados.</p>"
        )

    range_text = f"{fmt_bound(case['desde'])} – {fmt_bound(case['hasta'])}"
    parts: list[str] = []

    for index, user in enumerate(users, start=1):
        parts.append(
            compact_html(
                f"""
                <div style="min-width:170px;max-width:225px;background:#F8FAFC;
                    border:2px solid #CBD5E1;border-radius:12px;padding:11px;
                    font-family:Arial,sans-serif;">
                    <div style="font-size:11px;color:#64748B;font-weight:700;">
                        Liberador {index}
                    </div>
                    <div style="font-weight:700;color:#17365D;margin:6px 0;
                        overflow-wrap:anywhere;font-size:12px;">
                        {escape(display_with_cargo(user, data))}
                    </div>
                    <div style="font-size:10px;color:#64748B;">
                        {escape(range_text)}
                    </div>
                </div>
                """
            )
        )

        if index < len(users):
            parts.append(
                "<div style='font-size:21px;color:#94A3B8;font-weight:700;'>→</div>"
            )

    return compact_html(
        "<div style='font-family:Arial;margin-top:14px;'>"
        "<div style='font-weight:800;color:#17365D;margin-bottom:8px;'>Flujo final</div>"
        "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:7px;'>"
        + "".join(parts)
        + "</div></div>"
    )


def html_case(
    case: dict[str, Any],
    data: dict[str, pd.DataFrame],
    title: str,
) -> str:
    metrics = [
        ("CECO", case["ceco"]),
        ("Planta", case["planta"] or "—"),
        ("Centro", case.get("centro", "") or "—"),
        ("Tipo", DOC_LABEL.get(case["doc"], case["doc"])),
        ("Monto", fmt_money(case["monto"])),
        ("Tramo", f"{fmt_bound(case['desde'])} – {fmt_bound(case['hasta'])}"),
        ("Liberadores", str(len(case["libs"]))),
    ]

    doc_color = DOC_COLOR.get(case["doc"], "#17365D")
    doc_background = DOC_BG.get(case["doc"], "#FFFFFF")
    doc_border = DOC_BORDER.get(case["doc"], "#E2E8F0")

    metric_html = "".join(
        compact_html(
            f"""
            <div class="fl-metric" style="{
                'background:' + doc_background + ';border-color:' + doc_border + ';'
                if label == 'Tipo' else ''
            }">
                <div class="fl-metric-label">{escape(label)}</div>
                <div class="fl-metric-value" style="{
                    'color:' + doc_color + ';' if label == 'Tipo' else ''
                }">{escape(value)}</div>
            </div>
            """
        )
        for label, value in metrics
    )

    return compact_html(
        f"""
        <div class="fl-card" style="border-top:4px solid {doc_color};">
            <div style="color:#17365D;font-size:17px;font-weight:800;">
                {escape(title)}
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
                gap:9px;margin-top:13px;">
                {metric_html}
            </div>
            {html_flow(case, data)}
        </div>
        """
    )


# ============================================================
# TABLA DEL CECO
# ============================================================

def format_table_dataframe(flow: pd.DataFrame, ceco: str) -> pd.DataFrame:
    table = flow[flow["CECO"].eq(ceco)].copy()

    available_columns = [column for column in TABLE_COLS if column in table.columns]
    table = table[available_columns]

    if "Desde" in table.columns:
        table["Desde"] = table["Desde"].map(fmt_bound)
    if "Hasta" in table.columns:
        table["Hasta"] = table["Hasta"].map(fmt_bound)

    for column in LIB_COLS:
        if column in table.columns:
            table[column] = table[column].map(strip_user_email)


    sort_columns = [column for column in ["TipoDoc", "Desde"] if column in table.columns]
    if sort_columns:
        # Se conserva una columna auxiliar numérica para ordenar correctamente los tramos.
        original_subset = flow[flow["CECO"].eq(ceco)].copy()
        original_subset["_DesdeOrden"] = original_subset["Desde"].map(
            lambda value: parse_bound(value, low=True)
        )
        original_subset = original_subset.sort_values(["TipoDoc", "_DesdeOrden"])
        table = table.loc[original_subset.index]

    return table.reset_index(drop=True)


def style_ceco_table(table: pd.DataFrame) -> pd.io.formats.style.Styler:
    def style_row(row: pd.Series) -> list[str]:
        doc = clean_user(row.get("TipoDoc", ""))

        if doc == "AZNB":
            style = "background-color: #FFF1F0; color: #7A271A;"
        elif doc == "AZSR":
            style = "background-color: #EFF8FF; color: #1849A9;"
        else:
            style = ""

        return [style] * len(row)

    return (
        table.style
        .apply(style_row, axis=1)
        .set_properties(**{
            "border-color": "#D0D5DD",
            "font-size": "12px",
        })
    )


def render_ceco_table(data: dict[str, pd.DataFrame], ceco: str) -> None:
    st.markdown(
        '<div class="fl-section-title">3. Tabla de reglas del CECO</div>',
        unsafe_allow_html=True,
    )

    legend = compact_html(
        f"""
        <div class="fl-doc-legend">
            <span class="fl-doc-pill" style="background:{DOC_BG['AZNB']};
                color:{DOC_COLOR['AZNB']};border:1px solid {DOC_BORDER['AZNB']};">
                Material · AZNB
            </span>
            <span class="fl-doc-pill" style="background:{DOC_BG['AZSR']};
                color:{DOC_COLOR['AZSR']};border:1px solid {DOC_BORDER['AZSR']};">
                Servicio · AZSR
            </span>
        </div>
        """
    )
    st.markdown(legend, unsafe_allow_html=True)

    table = format_table_dataframe(data["flujo"], ceco)

    if table.empty:
        st.info("No existen reglas para el CECO seleccionado.")
        return

    st.caption(
        f"{len(table):,} reglas encontradas para {ceco}. "
        "La tabla muestra todos los tramos de material y servicio.".replace(",", ".")
    )

    st.dataframe(
        style_ceco_table(table),
        use_container_width=True,
        hide_index=True,
        height=min(650, 85 + (len(table) * 35)),
    )


# ============================================================
# ESTADO EDITABLE DEL CASO
# ============================================================

def set_editor_from_case(case: dict[str, Any]) -> None:
    """Actualiza los campos antes de que sus widgets sean creados."""
    st.session_state[SESSION_EDITOR_CECO] = case["ceco"]
    st.session_state[SESSION_EDITOR_DOC] = case["doc"]
    st.session_state[SESSION_EDITOR_AMOUNT] = str(case["monto"])


def queue_editor_from_case(case: dict[str, Any]) -> None:
    """Deja una actualización pendiente para aplicarla en el siguiente rerun."""
    st.session_state[SESSION_PENDING_EDITOR] = {
        "ceco": case["ceco"],
        "doc": case["doc"],
        "monto": str(case["monto"]),
    }


def apply_pending_editor() -> None:
    """Aplica cambios pendientes antes de instanciar selectbox/text_input."""
    pending = st.session_state.pop(SESSION_PENDING_EDITOR, None)
    if not pending:
        return

    st.session_state[SESSION_EDITOR_CECO] = pending["ceco"]
    st.session_state[SESSION_EDITOR_DOC] = pending["doc"]
    st.session_state[SESSION_EDITOR_AMOUNT] = pending["monto"]


def save_case(
    case: dict[str, Any],
    title: str,
    *,
    update_editor_next_run: bool = False,
) -> None:
    st.session_state[SESSION_CASE_KEY] = {
        "case": case,
        "title": title,
    }

    if update_editor_next_run:
        queue_editor_from_case(case)


def remember_current_case() -> None:
    """Guarda el resultado actual para permitir retroceder."""
    current = st.session_state.get(SESSION_CASE_KEY)
    if not current:
        return

    history = st.session_state.setdefault(SESSION_HISTORY_KEY, [])
    if not history or history[-1] != current:
        history.append(current)
        del history[:-20]


def restore_previous_case() -> bool:
    """Restaura el último caso guardado y sincroniza los editores."""
    history = st.session_state.get(SESSION_HISTORY_KEY, [])
    if not history:
        return False

    previous = history.pop()
    st.session_state[SESSION_HISTORY_KEY] = history
    st.session_state[SESSION_CASE_KEY] = previous
    queue_editor_from_case(previous["case"])
    return True


def clear_case() -> None:
    st.session_state.pop(SESSION_CASE_KEY, None)
    st.session_state.pop(SESSION_EDITOR_CECO, None)
    st.session_state.pop(SESSION_EDITOR_DOC, None)
    st.session_state.pop(SESSION_EDITOR_AMOUNT, None)
    st.session_state.pop(SESSION_PENDING_EDITOR, None)


# ============================================================
# ENCABEZADO Y SIMULADOR ALEATORIO
# ============================================================

def render_header() -> None:
    mostrar_logo()
    st.markdown(
        '<div class="fl-title">02 Simulador Aleatorio</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="fl-subtitle">Simula usando cinco liberadores y los diccionarios de CECO y usuarios.</div>',
        unsafe_allow_html=True,
    )


def render_random_generator(data: dict[str, pd.DataFrame]) -> None:
    st.markdown(
        '<div class="fl-section-title">1. Generar caso aleatorio</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        compact_html(
            """
            <div class="fl-help-box">
                Selecciona el tipo inicial y genera una combinación aleatoria.
                Después podrás cambiar el CECO, el tipo de documento o el monto
                para recalcular el flujo.
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    col_doc, col_button = st.columns([1.7, 1.2], gap="medium")

    with col_doc:
        doc_filter = st.selectbox(
            "Tipo inicial",
            ["RAND", "AZNB", "AZSR"],
            format_func=lambda value: {
                "RAND": "Material o Servicio",
                "AZNB": "Material (AZNB)",
                "AZSR": "Servicio (AZSR)",
            }[value],
            key="sim_doc_filter_v03",
        )

    with col_button:
        st.write("")
        st.write("")
        random_button = st.button(
            "🎲 Generar caso aleatorio",
            type="primary",
            use_container_width=True,
            key="sim_random_button_v03",
        )

    if random_button:
        try:
            pairs = available_pairs(data, doc_filter)
            if not pairs:
                raise ValueError(
                    "No existen combinaciones CECO/tipo para los filtros seleccionados."
                )

            ceco, doc_type = random.choice(pairs)
            case = build_case(data, ceco, doc_type, amount=None)
            remember_current_case()
            save_case(
                case,
                f"Caso aleatorio · {DOC_LABEL[doc_type]}",
                update_editor_next_run=True,
            )
            st.rerun()

        except ValueError as exc:
            st.error(str(exc))


def render_editable_case(data: dict[str, pd.DataFrame]) -> None:
    # Los cambios pendientes deben aplicarse antes de crear los widgets.
    apply_pending_editor()

    result = st.session_state.get(SESSION_CASE_KEY)

    st.markdown("---")
    st.markdown(
        '<div class="fl-section-title">2. Ajustar caso generado</div>',
        unsafe_allow_html=True,
    )

    if not result:
        st.info("Genera un caso aleatorio para habilitar los campos editables.")
        return

    current_case = result["case"]

    if SESSION_EDITOR_CECO not in st.session_state:
        set_editor_from_case(current_case)

    all_cecos = ceco_values(data)
    current_ceco = st.session_state.get(SESSION_EDITOR_CECO, current_case["ceco"])
    if current_ceco not in all_cecos:
        current_ceco = current_case["ceco"]
        st.session_state[SESSION_EDITOR_CECO] = current_ceco

    ceco_col, doc_col, amount_col = st.columns([1.5, 1.1, 1.1], gap="medium")

    with ceco_col:
        selected_ceco = st.selectbox(
            "CECO",
            all_cecos,
            index=all_cecos.index(current_ceco),
            format_func=lambda value: ceco_label(data, value),
            key=SESSION_EDITOR_CECO,
            help="Al cambiar el CECO, el resultado se recalcula automáticamente.",
        )

    available_docs = docs_for_ceco(data, selected_ceco)
    if not available_docs:
        available_docs = ["AZNB", "AZSR"]

    current_doc = st.session_state.get(SESSION_EDITOR_DOC, current_case["doc"])
    if current_doc not in available_docs:
        current_doc = available_docs[0]
        st.session_state[SESSION_EDITOR_DOC] = current_doc

    with doc_col:
        selected_doc = st.selectbox(
            "Tipo de documento",
            available_docs,
            index=available_docs.index(current_doc),
            format_func=lambda value: DOC_LABEL[value],
            key=SESSION_EDITOR_DOC,
            help="Material usa AZNB y Servicio usa AZSR.",
        )

    with amount_col:
        selected_amount_text = st.text_input(
            "Monto",
            key=SESSION_EDITOR_AMOUNT,
            help="Presiona Enter o sal del campo para recalcular.",
        )

    # Recalcula automáticamente cuando cambian CECO, tipo o monto.
    try:
        selected_amount = parse_amount(selected_amount_text)
        editor_changed = (
            selected_ceco != current_case["ceco"]
            or selected_doc != current_case["doc"]
            or (selected_amount is not None and float(selected_amount) != float(current_case["monto"]))
        )

        if editor_changed and selected_amount is not None:
            updated_case = build_case(data, selected_ceco, selected_doc, selected_amount)
            remember_current_case()
            save_case(updated_case, "Caso modificado por el usuario")
            result = st.session_state[SESSION_CASE_KEY]
            current_case = result["case"]
    except ValueError as exc:
        st.warning(str(exc))

    button_amount, button_back = st.columns([1.25, 1.0])

    with button_amount:
        random_amount_button = st.button(
            "🎯 Nuevo monto del tramo",
            use_container_width=True,
            key="sim_random_amount_v04",
        )

    with button_back:
        back_button = st.button(
            "↩️ Retroceder",
            use_container_width=True,
            key="sim_back_v04",
            disabled=not bool(st.session_state.get(SESSION_HISTORY_KEY)),
            help="Vuelve al caso anterior.",
        )

    if random_amount_button:
        try:
            flow = validate_flow_schema(data)
            rows = flow[
                flow["CECO"].eq(selected_ceco)
                & flow["TipoDoc"].eq(selected_doc)
            ]

            if rows.empty:
                raise ValueError("No existen tramos para la selección actual.")

            selected_row = rows.sample(n=1).iloc[0]
            new_amount = random_amount_for_row(selected_row)
            case = build_case(data, selected_ceco, selected_doc, new_amount)
            remember_current_case()
            save_case(
                case,
                "Caso modificado · monto aleatorio",
                update_editor_next_run=True,
            )
            st.rerun()

        except ValueError as exc:
            st.error(str(exc))

    if back_button:
        if restore_previous_case():
            st.rerun()
        else:
            st.info("No hay un caso anterior disponible.")

    result = st.session_state.get(SESSION_CASE_KEY)
    if result:
        case = result["case"]
        st.markdown(
            html_case(case, data, result["title"]),
            unsafe_allow_html=True,
        )
        render_ceco_table(data, st.session_state.get(SESSION_EDITOR_CECO, case["ceco"]))


def render_simulator(data: dict[str, Any]) -> None:
    flow = validate_flow_schema(data)
    file_names = st.session_state.get(SESSION_FILE_KEY, {})
    liberadores = data.get("liberadores", {})
    dic_ceco = data.get("dic_ceco", pd.DataFrame())
    dic_users = data.get("dic_users", pd.DataFrame())

    loaded_levels = sum(
        isinstance(liberadores.get(level), pd.DataFrame)
        for level in LEVELS
    )
    dictionaries_loaded = int(
        isinstance(dic_ceco, pd.DataFrame)
    ) + int(
        isinstance(dic_users, pd.DataFrame)
    )

    st.success(
        (
            f"Versión activa: **{loaded_levels + dictionaries_loaded}/7 archivos** · "
            f"**{len(flow):,} reglas reconstruidas** · "
            f"**{flow['CECO'].nunique():,} CECO** · "
            f"**{len(dic_users):,} usuarios**"
        ).replace(",", ".")
    )

    missing_users = users_not_in_dictionary(data)
    if missing_users:
        with st.expander(
            f"Usuarios sin cargo en diccionario ({len(missing_users)})",
            expanded=False,
        ):
            st.dataframe(
                pd.DataFrame({"Correo": missing_users}),
                use_container_width=True,
                hide_index=True,
            )

    if isinstance(file_names, dict):
        with st.expander("Archivos de la versión", expanded=False):
            file_rows = [
                {
                    "Archivo lógico": f"Liberador {level}",
                    "Archivo cargado": file_names.get(
                        FILE_ROLE_LIBERATORS[level],
                        file_names.get(level, ""),
                    ),
                    "Filas": len(
                        liberadores.get(level, pd.DataFrame())
                    ),
                }
                for level in LEVELS
            ]

            file_rows.extend([
                {
                    "Archivo lógico": "Diccionario CECO-Plantas",
                    "Archivo cargado": file_names.get(
                        FILE_ROLE_CECO,
                        "",
                    ),
                    "Filas": len(dic_ceco),
                },
                {
                    "Archivo lógico": "Diccionario Usuarios-Cargos",
                    "Archivo cargado": file_names.get(
                        FILE_ROLE_USERS,
                        "",
                    ),
                    "Filas": len(dic_users),
                },
            ])

            st.dataframe(
                pd.DataFrame(file_rows),
                use_container_width=True,
                hide_index=True,
            )

    render_random_generator(data)
    render_editable_case(data)



# ============================================================
# EJECUCIÓN
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()

    data = st.session_state.get(SESSION_DATA_KEY)

    if data is None:
        st.warning(
            "No hay una versión activa. Primero carga los siete archivos en **01 Cargar Versión**."
        )

        try:
            if st.button("📤 Ir a 01 Cargar Versión", type="primary"):
                st.switch_page("01_CARGAR_ARCHIVO_FLUJO.py")
        except Exception:
            st.info("Selecciona **01 Cargar Versión** desde el menú lateral.")

        st.stop()

    try:
        validate_flow_schema(data)
    except ValueError as error:
        st.error(str(error))
        st.stop()

    render_simulator(data)


if __name__ == "__main__":
    main()
