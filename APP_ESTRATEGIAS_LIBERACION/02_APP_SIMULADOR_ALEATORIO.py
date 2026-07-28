# ============================================================
# 02_APP_SIMULADOR_ALEATORIO
# APP_FLUJO_LIBERACION_SERVICIOS
#
# Lee la base cargada por 01_CARGAR_ARCHIVO_FLUJO desde
# st.session_state y permite simular o buscar flujos.
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

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_CANDIDATES = [
    PROJECT_DIR / "assets" / "logo.svg", BASE_DIR / "assets" / "logo.svg",
    PROJECT_DIR / "assets" / "logo.png", BASE_DIR / "assets" / "logo.png",
    PROJECT_DIR / "assets" / "logo.jpg", BASE_DIR / "assets" / "logo.jpg",
]
LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]
DOC_LABEL = {"AZNB": "Material (AZNB)", "AZSR": "Servicio (AZSR)"}
DOC_COLOR = {"AZNB": "#C62828", "AZSR": "#1565C0"}
LS_LABEL = "Liberador Servicios"
SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_CASE_KEY = "flujo_liberacion_last_case"


def compact_html(value: str) -> str:
    value = dedent(value).strip()
    return re.sub(r">\s+<", "><", value)


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer, .block-container {
                padding-top: 6.5rem !important; padding-bottom: 2.5rem;
            }
            .fl-logo-wrap { width:100%; min-height:90px; display:flex; justify-content:center;
                align-items:center; margin:.6rem 0 12px; overflow:visible; }
            .fl-logo-wrap img { width:220px; max-width:min(60vw,220px); max-height:88px;
                object-fit:contain; display:block; }
            .fl-title { text-align:center; color:#17365D; font-size:2rem; font-weight:800; margin:.2rem 0; }
            .fl-subtitle { text-align:center; color:#64748B; font-size:1rem; margin-bottom:1.2rem; }
            .fl-section-title { color:#17365D; font-size:1.1rem; font-weight:800; margin:.4rem 0 .6rem; }
            .fl-card { font-family:Arial,sans-serif; padding:16px; background:#F8FAFC;
                border:1px solid #E2E8F0; border-radius:14px; box-shadow:0 1px 2px rgba(15,23,42,.05); }
            .fl-metric { border:1px solid #E2E8F0; border-radius:12px; padding:11px 13px;
                background:#FFF; min-height:78px; }
            .fl-metric-label { color:#64748B; font-size:11px; font-weight:700;
                text-transform:uppercase; letter-spacing:.03em; }
            .fl-metric-value { color:#17365D; font-size:17px; font-weight:800;
                margin-top:5px; word-break:break-word; }
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
            raw, mime = path.read_text(encoding="utf-8").encode("utf-8"), "image/svg+xml"
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


def clean_user(value: Any) -> str:
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


def parse_amount(value: str) -> int | None:
    text = (value or "").strip()
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


def normalize_int(value: Any) -> int:
    try:
        if value is None or pd.isna(value):
            return 0
        return int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError):
        return 0


def normalize_yes(value: Any) -> bool:
    return clean_user(value).upper() in {"SI", "SÍ", "YES", "TRUE", "1"}


def cargo_map(data: dict[str, pd.DataFrame]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for _, row in data["dic_users"].iterrows():
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


def pick_row(flow: pd.DataFrame, ceco: str, doc_type: str, amount: int | float) -> pd.Series | None:
    subset = flow[flow["CECO"].eq(ceco) & flow["TipoDoc"].eq(doc_type)]
    for _, row in subset.iterrows():
        if parse_bound(row["Desde"], True) <= amount <= parse_bound(row["Hasta"], False):
            return row
    return None


def libs_from_row(row: pd.Series) -> list[str]:
    return [strip_user_email(row[c]) for c in LIB_COLS if strip_user_email(row[c])]


def random_amount_for_row(row: pd.Series) -> int:
    low = max(0, int(parse_bound(row["Desde"], True)))
    high_value = parse_bound(row["Hasta"], False)
    high = low + 20_000_000 if high_value >= 1e17 else int(high_value)
    if high < low:
        raise ValueError("El rango seleccionado tiene límites inconsistentes.")
    return random.randint(low, high)


def build_case(data: dict[str, pd.DataFrame], ceco: str, doc_type: str | None = None,
               amount: int | None = None) -> dict[str, Any]:
    flow = data["flujo"]
    ceco = clean_user(ceco)
    docs = sorted(flow.loc[flow["CECO"].eq(ceco), "TipoDoc"].dropna().astype(str).unique().tolist())
    docs = [doc for doc in docs if doc in DOC_LABEL]
    if not docs:
        raise ValueError(f"No existen datos válidos para el CECO {ceco}.")
    if doc_type is None:
        doc_type = random.choice(docs)
    if doc_type not in docs:
        raise ValueError(f"El CECO {ceco} no tiene registros para {DOC_LABEL.get(doc_type, doc_type)}.")

    rows = flow[flow["CECO"].eq(ceco) & flow["TipoDoc"].eq(doc_type)]
    if amount is None:
        selected_row = rows.sample(n=1).iloc[0]
        amount = random_amount_for_row(selected_row)
    else:
        selected_row = pick_row(flow, ceco, doc_type, amount)
    if selected_row is None:
        raise ValueError("No se encontró un tramo para la combinación de CECO, tipo y monto indicada.")

    return {
        "ceco": ceco,
        "planta": clean_user(selected_row.get("Planta", "")),
        "doc": doc_type,
        "monto": int(amount),
        "desde": selected_row["Desde"],
        "hasta": selected_row["Hasta"],
        "match": normalize_yes(selected_row.get("Match", "")),
        "n_eo": normalize_int(selected_row.get("N_EO", 0)),
        "n_cd": normalize_int(selected_row.get("N_CD", 0)),
        "libs": libs_from_row(selected_row),
    }


def available_pairs(data: dict[str, pd.DataFrame], only_match: bool,
                    doc_filter: str) -> list[tuple[str, str]]:
    flow = data["flujo"]
    if only_match:
        flow = flow[flow["Match"].map(normalize_yes)]
    if doc_filter in DOC_LABEL:
        flow = flow[flow["TipoDoc"].eq(doc_filter)]
    return [(str(c), str(d)) for c, d in flow[["CECO", "TipoDoc"]].drop_duplicates()
            .itertuples(index=False, name=None) if d in DOC_LABEL]


def html_flow(case: dict[str, Any], data: dict[str, pd.DataFrame]) -> str:
    users = [u for u in case["libs"] if clean_user(u)]
    if not users:
        return "<p style='font-family:Arial;color:#64748B;'>El tramo no tiene liberadores registrados.</p>"
    range_text = f"{fmt_bound(case['desde'])} – {fmt_bound(case['hasta'])}"
    parts: list[str] = []
    for index, user in enumerate(users, start=1):
        is_eo = index <= case["n_eo"]
        background, border, text_color, group = (
            ("#EAF7EE", "#7BC596", "#166534", "EO") if is_eo
            else ("#F8FAFC", "#CBD5E1", "#1E3A8A", "CD")
        )
        parts.append(compact_html(f"""
            <div style="min-width:170px;max-width:225px;background:{background};border:2px solid {border};
                border-radius:12px;padding:11px;font-family:Arial,sans-serif;">
                <div style="font-size:11px;color:#64748B;font-weight:700;">Liberador {index} · {group}</div>
                <div style="font-weight:700;color:{text_color};margin:6px 0;overflow-wrap:anywhere;font-size:12px;">
                    {escape(display_with_cargo(user, data))}
                </div>
                <div style="font-size:10px;color:#64748B;">{escape(range_text)}</div>
            </div>
        """))
        if index < len(users):
            parts.append("<div style='font-size:21px;color:#94A3B8;font-weight:700;'>→</div>")
    return compact_html(
        "<div style='font-family:Arial;margin-top:14px;'>"
        "<div style='font-weight:800;color:#17365D;margin-bottom:8px;'>Flujo final</div>"
        "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:7px;'>"
        + "".join(parts) + "</div></div>"
    )


def html_case(case: dict[str, Any], data: dict[str, pd.DataFrame], title: str) -> str:
    badge = (
        "<span style='background:#166534;color:#FFF;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700;'>MATCH</span>"
        if case["match"] else
        "<span style='background:#C2410C;color:#FFF;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700;'>Solo CD</span>"
    )
    metrics = [
        ("CECO", case["ceco"]), ("Planta", case["planta"] or "—"),
        ("Tipo", DOC_LABEL.get(case["doc"], case["doc"])),
        ("Monto", fmt_money(case["monto"])),
        ("Tramo", f"{fmt_bound(case['desde'])} – {fmt_bound(case['hasta'])}"),
        ("Liberadores", str(len(case["libs"]))),
    ]
    doc_color = DOC_COLOR.get(case["doc"], "#17365D")
    metric_html = "".join(
        compact_html(f"""
            <div class="fl-metric"><div class="fl-metric-label">{escape(label)}</div>
            <div class="fl-metric-value" style="{'color:' + doc_color + ';' if label == 'Tipo' else ''}">
                {escape(value)}</div></div>
        """) for label, value in metrics
    )
    return compact_html(f"""
        <div class="fl-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                <div style="color:#17365D;font-size:17px;font-weight:800;">{escape(title)}</div>{badge}
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:9px;margin-top:13px;">
                {metric_html}
            </div>{html_flow(case, data)}
        </div>
    """)


def ceco_options(data: dict[str, pd.DataFrame]) -> list[str]:
    flow = data["flujo"]
    options = []
    for ceco in sorted(flow["CECO"].unique().tolist()):
        plants = flow.loc[flow["CECO"].eq(ceco), "Planta"].map(clean_user)
        plants = plants[plants.ne("")].unique().tolist()
        options.append(f"{ceco} | {plants[0]}" if plants else ceco)
    return options


def parse_ceco_label(value: str) -> str:
    text = clean_user(value)
    return text.split("|", 1)[0].strip() if "|" in text else text


def render_header() -> None:
    mostrar_logo()
    st.markdown('<div class="fl-title">02 Simulador Aleatorio</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fl-subtitle">Simulación de flujos de liberación para materiales y servicios.</div>',
        unsafe_allow_html=True,
    )


def render_simulator(data: dict[str, pd.DataFrame]) -> None:
    flow = data["flujo"]
    file_name = st.session_state.get(SESSION_FILE_KEY, "Archivo cargado")
    st.success(
        f"Usando archivo activo: **{file_name}** · **{len(flow):,} filas** · "
        f"**{flow['CECO'].nunique():,} CECO**".replace(",", ".")
    )

    st.markdown("---")
    st.markdown('<div class="fl-section-title">1. Configurar simulación</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        only_match = st.checkbox("Solo considerar CECO con MATCH", value=True, key="sim_only_match_v02")
        doc_filter = st.selectbox(
            "Tipo de documento", ["RAND", "AZNB", "AZSR"],
            format_func=lambda v: {"RAND": "Aleatorio (Material o Servicio)",
                                   "AZNB": "Material (AZNB)", "AZSR": "Servicio (AZSR)"}[v],
            key="sim_doc_filter_v02",
        )
        random_button = st.button("🎲 Generar caso aleatorio", type="primary",
                                  use_container_width=True, key="sim_random_button_v02")
    with right:
        selected_ceco_label = st.selectbox(
            "CECO", [""] + ceco_options(data),
            format_func=lambda v: "— Selecciona un CECO —" if not v else v,
            key="sim_ceco_v02",
        )
        manual_doc = st.selectbox(
            "Tipo para búsqueda", ["RAND", "AZNB", "AZSR"],
            format_func=lambda v: {"RAND": "Automático según CECO",
                                   "AZNB": "Material (AZNB)", "AZSR": "Servicio (AZSR)"}[v],
            key="sim_manual_doc_v02",
        )
        amount_text = st.text_input("Monto", placeholder="Vacío = monto automático", key="sim_amount_v02")
        search_button = st.button("🔎 Buscar CECO y monto", use_container_width=True, key="sim_search_button_v02")

    if random_button:
        try:
            pairs = available_pairs(data, only_match, doc_filter)
            if not pairs:
                raise ValueError("No existen combinaciones CECO/tipo para los filtros seleccionados.")
            ceco, doc_type = random.choice(pairs)
            st.session_state[SESSION_CASE_KEY] = {
                "case": build_case(data, ceco, doc_type, None),
                "title": f"Caso aleatorio · {DOC_LABEL[doc_type]}",
            }
        except ValueError as exc:
            st.error(str(exc))

    if search_button:
        try:
            ceco = parse_ceco_label(selected_ceco_label)
            if not ceco:
                raise ValueError("Selecciona un CECO para realizar la búsqueda.")
            amount = parse_amount(amount_text)
            docs = sorted(flow.loc[flow["CECO"].eq(ceco), "TipoDoc"].dropna().astype(str).unique().tolist())
            docs = [doc for doc in docs if doc in DOC_LABEL]
            if not docs:
                raise ValueError("El CECO seleccionado no tiene registros AZNB/AZSR.")
            doc_type = random.choice(docs) if manual_doc == "RAND" else manual_doc
            st.session_state[SESSION_CASE_KEY] = {
                "case": build_case(data, ceco, doc_type, amount),
                "title": "Resultado de búsqueda",
            }
        except ValueError as exc:
            st.error(str(exc))

    result = st.session_state.get(SESSION_CASE_KEY)
    st.markdown("---")
    st.markdown('<div class="fl-section-title">2. Resultado</div>', unsafe_allow_html=True)
    if result:
        st.markdown(html_case(result["case"], data, result["title"]), unsafe_allow_html=True)
        if st.button("🧹 Limpiar resultado", use_container_width=False):
            st.session_state.pop(SESSION_CASE_KEY, None)
            st.rerun()
    else:
        st.info("Genera un caso aleatorio o realiza una búsqueda para visualizar el flujo.")


def main() -> None:
    aplicar_estilos()
    render_header()
    data = st.session_state.get(SESSION_DATA_KEY)
    if data is None:
        st.warning("No hay un archivo activo. Primero carga la base en **01 Cargar Archivo**.")
        try:
            if st.button("📤 Ir a 01 Cargar Archivo", type="primary"):
                st.switch_page("01_CARGAR_ARCHIVO_FLUJO.py")
        except Exception:
            st.info("Selecciona **01 Cargar Archivo** desde el menú lateral.")
        st.stop()
    render_simulator(data)


if __name__ == "__main__":
    main()
