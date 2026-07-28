# ============================================================
# 03_MODIFICACION_LIBERADORES
# APP_FLUJO_LIBERACION_SERVICIOS
#
# Lee el Excel cargado en 01_CARGAR_ARCHIVO_FLUJO, permite
# modificar los liberadores y reglas de la hoja Flujo, guarda
# los cambios en la sesión y genera un Excel actualizado con
# fecha y hora de modificación en el nombre.
# ============================================================

from __future__ import annotations

import base64
import re
from copy import deepcopy
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

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_FILE_BYTES_KEY = "flujo_liberacion_file_bytes"
SESSION_WORKING_KEY = "mod_liberadores_working_df_v01"
SESSION_BACKUP_KEY = "mod_liberadores_backup_df_v01"
SESSION_SOURCE_SIGNATURE_KEY = "mod_liberadores_source_signature_v01"
SESSION_LAST_SAVE_KEY = "mod_liberadores_last_save_v01"

LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]
FLOW_COLUMNS = [
    "CECO", "Planta", "Desde", "Hasta", "TipoDoc",
    "Lib1", "Lib2", "Lib3", "Lib4", "Lib5",
    "N_EO", "N_CD", "Match", "FuenteCD",
]

DOC_LABEL = {
    "TODOS": "Todos",
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
}

DOC_BG = {
    "AZNB": "background-color: #FFF1F0; color: #7A271A;",
    "AZSR": "background-color: #EFF8FF; color: #1849A9;",
}


# ============================================================
# UTILIDADES DE INTERFAZ
# ============================================================

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
                margin: .5rem 0 .65rem;
            }
            .fl-help {
                color: #64748B; font-size: .88rem; margin-bottom: .8rem;
            }
            .fl-status {
                padding: 12px 14px; border-radius: 12px;
                border: 1px solid #D0D5DD; background: #F9FAFB;
                margin-bottom: 14px;
            }
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
    return next((path for path in LOGO_CANDIDATES if path.exists() and path.is_file()), None)


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


# ============================================================
# NORMALIZACIÓN Y VALIDACIÓN
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
    return "" if text.lower() in {"nan", "none", "—", "-"} else text


def numeric_or_original(value: Any) -> Any:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    if isinstance(value, (int, float)):
        return value

    text = clean_text(value)
    if not text:
        return ""

    normalized = text.replace(" ", "")
    try:
        if re.fullmatch(r"[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?", normalized):
            return float(normalized.replace(",", "."))
    except ValueError:
        pass
    return text


def preparar_flujo(df: pd.DataFrame) -> pd.DataFrame:
    flujo = df.copy()
    flujo.columns = [str(column).strip() for column in flujo.columns]

    for column in FLOW_COLUMNS:
        if column not in flujo.columns:
            flujo[column] = ""

    flujo = flujo[FLOW_COLUMNS].copy()
    flujo["CECO"] = flujo["CECO"].map(clean_text)
    flujo["Planta"] = flujo["Planta"].map(clean_text)
    flujo["TipoDoc"] = flujo["TipoDoc"].map(clean_text).str.upper()
    flujo["Match"] = flujo["Match"].map(clean_text).str.upper()
    flujo["FuenteCD"] = flujo["FuenteCD"].map(clean_text)

    for column in LIB_COLS:
        flujo[column] = flujo[column].map(clean_text)

    for column in ["Desde", "Hasta"]:
        flujo[column] = flujo[column].map(numeric_or_original)

    for column in ["N_EO", "N_CD"]:
        flujo[column] = pd.to_numeric(flujo[column], errors="coerce").fillna(0).astype(int)

    flujo = flujo[flujo["CECO"].ne("")].reset_index(drop=True)
    flujo.insert(0, "_ID_FILA", range(1, len(flujo) + 1))
    return flujo


def validar_tabla(df: pd.DataFrame) -> list[str]:
    errores: list[str] = []

    if df.empty:
        errores.append("La tabla no puede quedar vacía.")
        return errores

    if df["CECO"].map(clean_text).eq("").any():
        errores.append("Existen filas sin CECO.")

    tipos_invalidos = sorted(
        set(df.loc[~df["TipoDoc"].isin(["AZNB", "AZSR"]), "TipoDoc"].astype(str))
    )
    if tipos_invalidos:
        errores.append(
            "TipoDoc solo puede ser AZNB o AZSR. Valores inválidos: "
            + ", ".join(tipos_invalidos[:8])
        )

    for column in ["Desde", "Hasta"]:
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.isna().any():
            errores.append(f"La columna {column} contiene valores no numéricos.")

    desde = pd.to_numeric(df["Desde"], errors="coerce")
    hasta = pd.to_numeric(df["Hasta"], errors="coerce")
    if (desde > hasta).fillna(False).any():
        errores.append("Existen filas donde Desde es mayor que Hasta.")

    for column in ["N_EO", "N_CD"]:
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.isna().any() or (numeric < 0).fillna(False).any():
            errores.append(f"La columna {column} debe contener enteros mayores o iguales a cero.")

    return errores


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

def firma_origen(file_name: str, file_bytes: bytes, rows: int) -> str:
    return f"{file_name}|{len(file_bytes)}|{rows}"


def inicializar_estado(data: dict[str, pd.DataFrame], file_name: str, file_bytes: bytes) -> None:
    flow = preparar_flujo(data["flujo"])
    signature = firma_origen(file_name, file_bytes, len(flow))

    if (
        SESSION_WORKING_KEY not in st.session_state
        or st.session_state.get(SESSION_SOURCE_SIGNATURE_KEY) != signature
    ):
        st.session_state[SESSION_WORKING_KEY] = flow
        st.session_state[SESSION_BACKUP_KEY] = flow.copy(deep=True)
        st.session_state[SESSION_SOURCE_SIGNATURE_KEY] = signature
        st.session_state.pop(SESSION_LAST_SAVE_KEY, None)


def obtener_trabajo() -> pd.DataFrame:
    value = st.session_state.get(SESSION_WORKING_KEY)
    if not isinstance(value, pd.DataFrame):
        return pd.DataFrame(columns=["_ID_FILA", *FLOW_COLUMNS])
    return value.copy(deep=True)


def guardar_trabajo(df: pd.DataFrame) -> None:
    normalized = df.copy(deep=True)
    normalized["TipoDoc"] = normalized["TipoDoc"].map(clean_text).str.upper()
    normalized["Match"] = normalized["Match"].map(clean_text).str.upper()
    for column in ["N_EO", "N_CD"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0).astype(int)
    st.session_state[SESSION_WORKING_KEY] = normalized.reset_index(drop=True)

    data = st.session_state.get(SESSION_DATA_KEY)
    if isinstance(data, dict):
        data_updated = dict(data)
        data_updated["flujo"] = normalized.drop(columns=["_ID_FILA"], errors="ignore").copy()
        st.session_state[SESSION_DATA_KEY] = data_updated


def restaurar_original() -> None:
    backup = st.session_state.get(SESSION_BACKUP_KEY)
    if isinstance(backup, pd.DataFrame):
        guardar_trabajo(backup.copy(deep=True))
        st.session_state.pop(SESSION_LAST_SAVE_KEY, None)


# ============================================================
# GENERACIÓN DEL EXCEL
# ============================================================

def excel_actualizado(original_bytes: bytes, flow_df: pd.DataFrame) -> bytes:
    if not original_bytes:
        raise ValueError("No se encontraron los bytes del Excel original en la sesión.")

    try:
        workbook = load_workbook(BytesIO(original_bytes))
    except Exception as exc:
        raise ValueError("No fue posible abrir el Excel original para actualizarlo.") from exc

    if "Flujo" in workbook.sheetnames:
        sheet = workbook["Flujo"]
    else:
        sheet = workbook.create_sheet("Flujo")

    # Limpiar valores existentes conservando la hoja, anchos y la mayor parte del formato.
    for row in sheet.iter_rows():
        for cell in row:
            cell.value = None

    export_df = flow_df.drop(columns=["_ID_FILA"], errors="ignore").copy()
    export_df = export_df[FLOW_COLUMNS]

    for row_index, row_values in enumerate(
        dataframe_to_rows(export_df, index=False, header=True), start=1
    ):
        for column_index, value in enumerate(row_values, start=1):
            sheet.cell(row=row_index, column=column_index, value=value)

    sheet.auto_filter.ref = sheet.dimensions
    sheet.freeze_panes = "A2"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def nombre_descarga(original_name: str) -> str:
    stem = Path(original_name or "BBDD_FLUJO_LIBERACION.xlsx").stem
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return f"{stem}_MODIFICADO_{timestamp}.xlsx"


# ============================================================
# TABLA Y EDICIÓN
# ============================================================

def style_preview(df: pd.DataFrame):
    def row_style(row: pd.Series) -> list[str]:
        style = DOC_BG.get(clean_text(row.get("TipoDoc")).upper(), "")
        return [style] * len(row)

    formatters = {
        "Desde": lambda value: f"{int(float(value)):,}".replace(",", ".") if clean_text(value) else "",
        "Hasta": lambda value: f"{int(float(value)):,}".replace(",", ".") if clean_text(value) else "",
    }
    return df.style.apply(row_style, axis=1).format(formatters)


def aplicar_edicion_filtrada(
    full_df: pd.DataFrame,
    original_subset: pd.DataFrame,
    edited_subset: pd.DataFrame,
) -> pd.DataFrame:
    result = full_df.copy(deep=True)

    original_ids = set(pd.to_numeric(original_subset["_ID_FILA"], errors="coerce").dropna().astype(int))
    edited = edited_subset.copy(deep=True)
    edited["_ID_FILA"] = pd.to_numeric(edited["_ID_FILA"], errors="coerce")

    # Filas borradas en el editor.
    edited_existing_ids = set(edited["_ID_FILA"].dropna().astype(int))
    deleted_ids = original_ids - edited_existing_ids
    if deleted_ids:
        result = result[~result["_ID_FILA"].isin(deleted_ids)].copy()

    # Actualizar filas existentes.
    for _, row in edited[edited["_ID_FILA"].notna()].iterrows():
        row_id = int(row["_ID_FILA"])
        mask = result["_ID_FILA"].eq(row_id)
        if mask.any():
            for column in FLOW_COLUMNS:
                result.loc[mask, column] = row[column]

    # Agregar filas nuevas creadas mediante num_rows="dynamic".
    new_rows = edited[edited["_ID_FILA"].isna()].copy()
    if not new_rows.empty:
        next_id = int(result["_ID_FILA"].max()) + 1 if not result.empty else 1
        rows_to_add = []
        for _, row in new_rows.iterrows():
            new_row = {column: row.get(column, "") for column in FLOW_COLUMNS}
            new_row["_ID_FILA"] = next_id
            next_id += 1
            rows_to_add.append(new_row)
        result = pd.concat([result, pd.DataFrame(rows_to_add)], ignore_index=True)

    return result[["_ID_FILA", *FLOW_COLUMNS]].reset_index(drop=True)


def render_editor() -> None:
    working = obtener_trabajo()
    if working.empty:
        st.warning("No existen registros disponibles para modificar.")
        return

    st.markdown('<div class="fl-section-title">1. Seleccionar registros</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fl-help">Filtra el CECO y el tipo de documento. La edición se realiza sobre las filas mostradas.</div>',
        unsafe_allow_html=True,
    )

    cecos = sorted(working["CECO"].map(clean_text).loc[lambda s: s.ne("")].unique().tolist())
    col_ceco, col_doc, col_match = st.columns([2.2, 1.4, 1.2])

    with col_ceco:
        selected_ceco = st.selectbox(
            "CECO",
            options=["TODOS", *cecos],
            format_func=lambda value: "Todos los CECO" if value == "TODOS" else value,
            key="mod_lib_ceco_filter_v01",
        )

    with col_doc:
        selected_doc = st.selectbox(
            "Tipo de documento",
            options=list(DOC_LABEL),
            format_func=lambda value: DOC_LABEL[value],
            key="mod_lib_doc_filter_v01",
        )

    with col_match:
        only_match = st.checkbox(
            "Solo MATCH",
            value=False,
            key="mod_lib_match_filter_v01",
        )

    mask = pd.Series(True, index=working.index)
    if selected_ceco != "TODOS":
        mask &= working["CECO"].eq(selected_ceco)
    if selected_doc != "TODOS":
        mask &= working["TipoDoc"].eq(selected_doc)
    if only_match:
        mask &= working["Match"].isin(["SI", "SÍ"])

    subset = working.loc[mask].copy().reset_index(drop=True)
    st.caption(f"Registros seleccionados: {len(subset):,}".replace(",", "."))

    if subset.empty:
        st.info("No hay filas que coincidan con los filtros seleccionados.")
        return

    st.markdown('<div class="fl-section-title">2. Modificar liberadores y reglas</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fl-help">Puedes editar celdas, agregar filas o eliminar filas. El identificador interno no es editable.</div>',
        unsafe_allow_html=True,
    )

    edited = st.data_editor(
        subset,
        key=f"mod_lib_editor_{selected_ceco}_{selected_doc}_{int(only_match)}",
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        height=min(620, max(260, 38 * (len(subset) + 2))),
        disabled=["_ID_FILA"],
        column_order=["_ID_FILA", *FLOW_COLUMNS],
        column_config={
            "_ID_FILA": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "CECO": st.column_config.TextColumn("CECO", required=True, width="medium"),
            "Planta": st.column_config.TextColumn("Planta", width="medium"),
            "Desde": st.column_config.NumberColumn("Desde", min_value=0, step=1, format="%.0f"),
            "Hasta": st.column_config.NumberColumn("Hasta", min_value=0, step=1, format="%.0f"),
            "TipoDoc": st.column_config.SelectboxColumn(
                "TipoDoc", options=["AZNB", "AZSR"], required=True, width="small"
            ),
            "N_EO": st.column_config.NumberColumn("N_EO", min_value=0, step=1, format="%d"),
            "N_CD": st.column_config.NumberColumn("N_CD", min_value=0, step=1, format="%d"),
            "Match": st.column_config.SelectboxColumn(
                "Match", options=["SI", "NO"], width="small"
            ),
        },
    )

    col_save, col_restore = st.columns([1.2, 1.2])
    with col_save:
        save_clicked = st.button(
            "💾 Guardar modificaciones",
            type="primary",
            use_container_width=True,
            key="mod_lib_save_v01",
        )
    with col_restore:
        restore_clicked = st.button(
            "↩️ Restaurar archivo cargado",
            use_container_width=True,
            key="mod_lib_restore_v01",
        )

    if save_clicked:
        candidate = aplicar_edicion_filtrada(working, subset, edited)
        errors = validar_tabla(candidate)
        if errors:
            for error in errors:
                st.error(error)
        else:
            guardar_trabajo(candidate)
            st.session_state[SESSION_LAST_SAVE_KEY] = datetime.now()
            st.success("Modificaciones guardadas en la sesión.")
            st.rerun()

    if restore_clicked:
        restaurar_original()
        st.success("Se restauró la versión cargada originalmente.")
        st.rerun()

    st.markdown('<div class="fl-section-title">3. Vista previa actual</div>', unsafe_allow_html=True)
    preview = obtener_trabajo().loc[mask].drop(columns=["_ID_FILA"], errors="ignore")
    st.dataframe(
        style_preview(preview),
        use_container_width=True,
        hide_index=True,
        height=min(440, max(230, 36 * (len(preview) + 1))),
    )


# ============================================================
# DESCARGA
# ============================================================

def render_download(file_name: str, original_bytes: bytes) -> None:
    st.markdown('<div class="fl-section-title">4. Descargar Excel actualizado</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fl-help">La descarga conserva las demás hojas del libro y reemplaza la hoja Flujo con la versión modificada.</div>',
        unsafe_allow_html=True,
    )

    working = obtener_trabajo()
    errors = validar_tabla(working)
    if errors:
        st.error("No es posible generar el Excel porque existen errores de validación.")
        for error in errors:
            st.write(f"- {error}")
        return

    try:
        output_bytes = excel_actualizado(original_bytes, working)
    except ValueError as exc:
        st.error(str(exc))
        return

    download_name = nombre_descarga(file_name)
    last_save = st.session_state.get(SESSION_LAST_SAVE_KEY)
    if isinstance(last_save, datetime):
        st.info(f"Última modificación guardada: {last_save.strftime('%d-%m-%Y %H:%M:%S')}")

    st.download_button(
        "⬇️ Descargar Excel modificado",
        data=output_bytes,
        file_name=download_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
        key="mod_lib_download_v01",
    )
    st.caption(f"Nombre de descarga: {download_name}")


# ============================================================
# APP PRINCIPAL
# ============================================================

def main() -> None:
    aplicar_estilos()
    mostrar_logo()

    st.markdown('<div class="fl-title">03 Modificación de Liberadores</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fl-subtitle">Edita las reglas de liberación y descarga el Excel actualizado.</div>',
        unsafe_allow_html=True,
    )

    data = st.session_state.get(SESSION_DATA_KEY)
    file_name = st.session_state.get(SESSION_FILE_KEY, "")
    file_bytes = st.session_state.get(SESSION_FILE_BYTES_KEY, b"")

    if not isinstance(data, dict) or not isinstance(data.get("flujo"), pd.DataFrame):
        st.warning(
            "No hay un archivo activo. Primero abre **01 Cargar archivo** y carga la base de datos."
        )
        return

    if not isinstance(file_bytes, (bytes, bytearray)) or not file_bytes:
        st.error(
            "La base está disponible, pero no se encontraron los bytes del Excel original. "
            "Vuelve a cargar el archivo desde **01 Cargar archivo**."
        )
        return

    inicializar_estado(data, file_name, bytes(file_bytes))
    working = obtener_trabajo()

    cecos = working["CECO"].nunique()
    material = int(working["TipoDoc"].eq("AZNB").sum())
    servicio = int(working["TipoDoc"].eq("AZSR").sum())

    st.markdown(
        compact_html(
            f"""
            <div class="fl-status">
                <strong>Archivo activo:</strong> {file_name or 'Archivo cargado'} ·
                <strong>{len(working):,}</strong> filas ·
                <strong>{cecos:,}</strong> CECO ·
                <span style="color:#B42318;font-weight:700;">{material:,} Material</span> ·
                <span style="color:#175CD3;font-weight:700;">{servicio:,} Servicio</span>
            </div>
            """.replace(",", ".")
        ),
        unsafe_allow_html=True,
    )

    render_editor()
    st.markdown("---")
    render_download(file_name, bytes(file_bytes))


main()
