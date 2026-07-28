# ============================================================
# 01_CARGAR_ARCHIVO_FLUJO
# APP_FLUJO_LIBERACION_SERVICIOS
#
# Carga y valida el archivo Excel de flujo de liberación.
# Deja la información disponible en st.session_state para que
# 02_APP_SIMULADOR_ALEATORIO pueda utilizarla.
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
FLOW_REQUIRED_COLUMNS = [
    "CECO", "Planta", "Desde", "Hasta", "TipoDoc",
    "Lib1", "Lib2", "Lib3", "Lib4", "Lib5",
    "N_EO", "N_CD", "Match",
]
USER_REQUIRED_COLUMNS = ["Correo", "Cargo"]
DOC_LABEL = {"AZNB": "Material (AZNB)", "AZSR": "Servicio (AZSR)"}
LS_LABEL = "Liberador Servicios"

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_CASE_KEY = "flujo_liberacion_last_case"
SESSION_FILE_BYTES_KEY = "flujo_liberacion_file_bytes"


def compact_html(value: str) -> str:
    value = dedent(value).strip()
    return re.sub(r">\s+<", "><", value)


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer, .block-container {
                padding-top: 6.5rem !important;
                padding-bottom: 2.5rem;
            }
            .fl-logo-wrap {
                width: 100%; min-height: 90px; display: flex;
                justify-content: center; align-items: center;
                margin: .6rem 0 12px; overflow: visible;
            }
            .fl-logo-wrap img {
                width: 220px; max-width: min(60vw, 220px);
                max-height: 88px; object-fit: contain; display: block;
            }
            .fl-title {
                text-align: center; color: #17365D; font-size: 2rem;
                font-weight: 800; margin: .2rem 0;
            }
            .fl-subtitle {
                text-align: center; color: #64748B; font-size: 1rem;
                margin-bottom: 1.2rem;
            }
            .fl-section-title {
                color: #17365D; font-size: 1.1rem; font-weight: 800;
                margin: .4rem 0 .6rem;
            }
            .fl-help { color: #64748B; font-size: .88rem; margin-bottom: .8rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def buscar_logo() -> Path | None:
    return next((p for p in LOGO_CANDIDATES if p.exists() and p.is_file()), None)


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
                f'<div class="fl-logo-wrap"><img src="data:{mime};base64,{encoded}" alt="Logo"></div>'
            ),
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


def normalize_flow_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    flow = df.copy()
    flow.columns = [str(column).strip() for column in flow.columns]
    missing = [column for column in FLOW_REQUIRED_COLUMNS if column not in flow.columns]
    if missing:
        raise ValueError(
            "La hoja 'Flujo' no contiene todas las columnas obligatorias. "
            f"Faltan: {', '.join(missing)}."
        )

    flow["CECO"] = flow["CECO"].map(clean_user)
    flow["Planta"] = flow["Planta"].map(clean_user)
    flow["TipoDoc"] = flow["TipoDoc"].map(clean_user).str.upper()
    flow["Match"] = flow["Match"].map(clean_user).str.upper()
    for column in LIB_COLS:
        flow[column] = flow[column].map(clean_user)

    flow = flow[flow["CECO"].ne("") & flow["TipoDoc"].isin(DOC_LABEL)].copy()
    if flow.empty:
        raise ValueError("La hoja 'Flujo' no contiene registros válidos AZNB/AZSR.")

    for index, row in flow.iterrows():
        try:
            low = parse_bound(row["Desde"], low=True)
            high = parse_bound(row["Hasta"], low=False)
        except ValueError as exc:
            raise ValueError(f"Error de rango en la fila Excel {index + 2}: {exc}") from exc
        if low > high:
            raise ValueError(
                f"Rango inválido en la fila Excel {index + 2}: Desde es mayor que Hasta."
            )

    return flow.reset_index(drop=True)


def normalize_users_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame(columns=USER_REQUIRED_COLUMNS)
    users = df.copy()
    users.columns = [str(column).strip() for column in users.columns]
    for column in USER_REQUIRED_COLUMNS:
        if column not in users.columns:
            users[column] = ""
    users["Correo"] = users["Correo"].map(strip_user_email)
    users["Cargo"] = users["Cargo"].map(clean_user)
    return users[users["Correo"].ne("")].drop_duplicates("Correo", keep="last").reset_index(drop=True)


def load_workbook(uploaded_file: Any) -> tuple[dict[str, pd.DataFrame], bytes]:
    raw_bytes = uploaded_file.getvalue()
    if not raw_bytes:
        raise ValueError("El archivo cargado está vacío.")

    try:
        excel_file = pd.ExcelFile(BytesIO(raw_bytes))
    except Exception as exc:
        raise ValueError("No fue posible abrir el archivo. Verifica que sea un Excel válido.") from exc

    if "Flujo" not in excel_file.sheet_names:
        raise ValueError("El archivo debe contener una hoja llamada 'Flujo'.")

    try:
        flow_raw = pd.read_excel(excel_file, sheet_name="Flujo")
        users_raw = (
            pd.read_excel(excel_file, sheet_name="Dic_Usuarios")
            if "Dic_Usuarios" in excel_file.sheet_names else None
        )
    except Exception as exc:
        raise ValueError("No fue posible leer las hojas del archivo Excel.") from exc

    data = {
        "flujo": normalize_flow_dataframe(flow_raw),
        "dic_users": normalize_users_dataframe(users_raw),
    }
    return data, raw_bytes


def normalize_yes(value: Any) -> bool:
    return clean_user(value).upper() in {"SI", "SÍ", "YES", "TRUE", "1"}


def borrar_archivo_activo() -> None:
    for key in [SESSION_DATA_KEY, SESSION_FILE_KEY, SESSION_CASE_KEY, SESSION_FILE_BYTES_KEY]:
        st.session_state.pop(key, None)


def render_header() -> None:
    mostrar_logo()
    st.markdown('<div class="fl-title">01 Cargar Archivo</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fl-subtitle">Carga y validación de la base de flujo de liberación.</div>',
        unsafe_allow_html=True,
    )


def render_estado() -> None:
    data = st.session_state.get(SESSION_DATA_KEY)
    if data is None:
        st.info("No hay un archivo activo. Carga el Excel para habilitar el simulador.")
        return

    flow = data["flujo"]
    file_name = st.session_state.get(SESSION_FILE_KEY, "Archivo cargado")
    match_count = int(flow["Match"].map(normalize_yes).sum())
    st.success(
        f"Archivo activo: **{file_name}** · **{len(flow):,} filas** · "
        f"**{flow['CECO'].nunique():,} CECO** · **{match_count:,} filas MATCH**".replace(",", ".")
    )

    a, b, c = st.columns(3)
    a.metric("Filas", f"{len(flow):,}".replace(",", "."))
    b.metric("CECO", f"{flow['CECO'].nunique():,}".replace(",", "."))
    c.metric("Filas MATCH", f"{match_count:,}".replace(",", "."))

    with st.expander("Vista previa de la hoja Flujo", expanded=False):
        st.dataframe(flow.head(100), use_container_width=True, hide_index=True)

    users = data["dic_users"]
    with st.expander("Vista previa de Dic_Usuarios", expanded=False):
        if users.empty:
            st.info("El archivo no contiene la hoja Dic_Usuarios o no tiene usuarios válidos.")
        else:
            st.dataframe(users.head(100), use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Descargar archivo activo",
            data=st.session_state.get(SESSION_FILE_BYTES_KEY, b""),
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            disabled=not bool(st.session_state.get(SESSION_FILE_BYTES_KEY)),
        )
    with col2:
        if st.button("🗑️ Quitar archivo activo", use_container_width=True):
            borrar_archivo_activo()
            st.rerun()


def main() -> None:
    aplicar_estilos()
    render_header()

    st.markdown('<div class="fl-section-title">1. Seleccionar archivo Excel</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="fl-help">
            La hoja <b>Flujo</b> es obligatoria. La hoja <b>Dic_Usuarios</b> es opcional
            y se usa para mostrar el cargo asociado a cada correo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Archivo Excel",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        key="flujo_liberacion_uploader_v01",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        current_name = st.session_state.get(SESSION_FILE_KEY)
        if current_name != uploaded_file.name or SESSION_DATA_KEY not in st.session_state:
            try:
                with st.spinner("Leyendo y validando archivo..."):
                    data, raw_bytes = load_workbook(uploaded_file)
                st.session_state[SESSION_DATA_KEY] = data
                st.session_state[SESSION_FILE_KEY] = uploaded_file.name
                st.session_state[SESSION_FILE_BYTES_KEY] = raw_bytes
                st.session_state.pop(SESSION_CASE_KEY, None)
                st.toast("Archivo cargado correctamente.", icon="✅")
            except ValueError as exc:
                borrar_archivo_activo()
                st.error(str(exc))

    st.markdown("---")
    st.markdown('<div class="fl-section-title">2. Archivo activo</div>', unsafe_allow_html=True)
    render_estado()


if __name__ == "__main__":
    main()
