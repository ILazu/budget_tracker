import os
import io
from datetime import datetime
from typing import Tuple, List

import streamlit as st
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
import matplotlib.pyplot as plt
import qrcode

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
APP_TITLE = "Desglose Económico Mensual"
FILE_NAME = "desglose_económico_esc_teo.xlsx"
SPANISH_MONTHS = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# RANGOS FIJOS INTERNOS
DON_START, DON_END = 3, 102       # Donaciones: filas 3–102
EXP_START, EXP_END = 106, 205     # Gastos: filas 106–205


# ------------------------------------------------------------
# FUNCIONES DE ARCHIVO
# ------------------------------------------------------------
def month_sheet_name(year: int, month: int) -> str:
    return f"{SPANISH_MONTHS[month]} {year}"


def ensure_workbook(path: str):
    if not os.path.exists(path):
        wb = Workbook()
        ws = wb.active
        ws.title = "Inicio"
        ws["A1"] = "Archivo creado por el Desglose Económico Mensual."
        ws["A2"] = "Las hojas se crean automáticamente al ingresar datos."
        wb.save(path)


def openpyxl_get_ws(wb, sheet_name: str) -> Worksheet:
    if sheet_name in wb.sheetnames:
        return wb[sheet_name]
    ws = wb.create_sheet(sheet_name)
    # Encabezados Donaciones
    ws["A1"] = "DONACIONES"
    ws["A2"], ws["B2"], ws["C2"] = "Fecha", "Descripción", "Monto"
    # Encabezados Gastos (separados internamente)
    ws["A105"] = "GASTOS (Comida y Meriendas)"
    ws["A106"], ws["B106"], ws["C106"] = "Fecha", "Descripción", "Monto"
    wb.save(FILE_NAME)
    return ws


def read_table(ws: Worksheet, start_row: int, end_row: int) -> pd.DataFrame:
    rows = []
    for row in range(start_row, end_row + 1):
        c1, c2, c3 = ws.cell(row=row, column=1).value, ws.cell(row=row, column=2).value, ws.cell(row=row, column=3).value
        if c1 is None and c2 is None and c3 is None:
            continue
        rows.append([c1, c2, c3])
    df = pd.DataFrame(rows, columns=["Fecha", "Descripción", "Monto"])
    if not df.empty:
        try:
            df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
        except Exception:
            pass
        df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0.0)
    return df


def append_row(ws: Worksheet, start_row: int, end_row: int, values: List):
    for row in range(start_row, end_row + 1):
        if all(ws.cell(row=row, column=c).value is None for c in range(1, 4)):
            for col, val in enumerate(values, start=1):
                ws.cell(row=row, column=col).value = val
            return
    st.error("⚠️ Se alcanzó el límite de 100 registros en esta sección.")


def clear_month_data(ws: Worksheet):
    for row in range(DON_START, DON_END + 1):
        for col in range(1, 4):
            ws.cell(row=row, column=col).value = None
    for row in range(EXP_START, EXP_END + 1):
        for col in range(1, 4):
            ws.cell(row=row, column=col).value = None


def get_month_data(year: int, month: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    ensure_workbook(FILE_NAME)
    wb = load_workbook(FILE_NAME)
    ws = openpyxl_get_ws(wb, month_sheet_name(year, month))
    donations = read_table(ws, DON_START, DON_END)
    expenses = read_table(ws, EXP_START, EXP_END)
    wb.save(FILE_NAME)
    return donations, expenses


def add_donation(year: int, month: int, date_str: str, desc: str, amount: float):
    ensure_workbook(FILE_NAME)
    wb = load_workbook(FILE_NAME)
    ws = openpyxl_get_ws(wb, month_sheet_name(year, month))
    append_row(ws, DON_START, DON_END, [date_str, desc, amount])
    wb.save(FILE_NAME)


def add_expense(year: int, month: int, date_str: str, desc: str, amount: float):
    ensure_workbook(FILE_NAME)
    wb = load_workbook(FILE_NAME)
    ws = openpyxl_get_ws(wb, month_sheet_name(year, month))
    append_row(ws, EXP_START, EXP_END, [date_str, desc, amount])
    wb.save(FILE_NAME)


def monthly_totals(don_df: pd.DataFrame, exp_df: pd.DataFrame) -> Tuple[float, float]:
    d_total = float(don_df["Monto"].sum()) if not don_df.empty else 0.0
    e_total = float(exp_df["Monto"].sum()) if not exp_df.empty else 0.0
    return d_total, e_total


def compute_previous_balance_for_month(year: int, month: int, initial_prev_jan: float) -> float:
    prev = float(initial_prev_jan)
    for m in range(1, month):
        don, exp = get_month_data(year, m)
        d, e = monthly_totals(don, exp)
        prev = prev + d - e
    return prev


# ------------------------------------------------------------
# INTERFAZ STREAMLIT
# ------------------------------------------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide")
st.title(APP_TITLE)

now = datetime.now()
col_y, col_m, col_mode = st.columns([1, 1, 1])
with col_y:
    year = st.number_input("Año", min_value=2000, max_value=2100, value=now.year, step=1)
with col_m:
    month = st.selectbox("Mes", list(range(1, 13)), index=now.month - 1, format_func=lambda x: SPANISH_MONTHS[x])
with col_mode:
    viewer_mode = st.toggle("Modo solo lectura (para estudiantes)", value=True)

# Configuración lateral
with st.sidebar:
    st.header("Configuración")
    st.markdown("**Saldo inicial de enero:**")
    initial_prev_jan = st.number_input("Saldo previo de enero", min_value=0.0, step=50.0, value=0.0, format="%.2f")

    st.divider()
    st.subheader("Código de administrador")
    admin_input = st.text_input("Introduce el código para habilitar edición", type="password")
    admin_secret = st.secrets.get("ADMIN_CODE", "")
    is_admin = bool(admin_secret) and admin_input == admin_secret
    editing_enabled = (not viewer_mode) and is_admin

st.subheader(f"Mes: {SPANISH_MONTHS[month]} {year}")

# Datos
donations_df, expenses_df = get_month_data(year, month)

# Formularios
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Registrar Donación")
    with st.form("don_form", clear_on_submit=True):
        d_date = st.date_input("Fecha", value=datetime.now().date())
        d_desc = st.text_input("Descripción", placeholder="Donativo anónimo / actividad X")
        d_amount = st.number_input("Monto", min_value=0.0, step=1.0, format="%.2f")
        if st.form_submit_button("Agregar donación", disabled=not editing_enabled):
            add_donation(year, month, d_date.isoformat(), d_desc, d_amount)
            st.rerun()

with col2:
    st.markdown("### Registrar Gasto (Comida y Meriendas)")
    with st.form("exp_form", clear_on_submit=True):
        e_date = st.date_input("Fecha ", value=datetime.now().date())
        e_desc = st.text_input("Descripción", placeholder="Pizza reunión / meriendas asamblea")
        e_amount = st.number_input("Monto ", min_value=0.0, step=1.0, format="%.2f")
        if st.form_submit_button("Agregar gasto", disabled=not editing_enabled):
            add_expense(year, month, e_date.isoformat(), e_desc, e_amount)
            st.rerun()

st.divider()

# Cálculos
prev_balance = compute_previous_balance_for_month(year, month, initial_prev_jan)
don_total, exp_total = monthly_totals(donations_df, expenses_df)
total_budget = prev_balance + don_total
remaining = total_budget - exp_total

left, right = st.columns(2)
with left:
    st.metric("Saldo previo", f"${prev_balance:,.2f}")
    st.metric("Donaciones", f"${don_total:,.2f}")
    st.metric("Presupuesto total", f"${total_budget:,.2f}")
with right:
    st.metric("Gastos", f"${exp_total:,.2f}")
    st.metric("Saldo restante", f"${remaining:,.2f}")

# Tablas
st.markdown("#### Donaciones")
st.dataframe(donations_df, use_container_width=True)
st.markdown("#### Gastos (Comida y Meriendas)")
st.dataframe(expenses_df, use_container_width=True)

# Gráficas
st.divider()
col_g1, col_g2 = st.columns(2)
with col_g1:
    fig1 = plt.figure(figsize=(4, 4))
    plt.pie([prev_balance, don_total], labels=["Saldo Previo", "Donaciones"], autopct="%1.1f%%", startangle=90)
    plt.title("Origen de fondos")
    st.pyplot(fig1)
with col_g2:
    fig2 = plt.figure(figsize=(4, 4))
    plt.pie([exp_total, max(remaining, 0)], labels=["Gastado", "Restante"], autopct="%1.1f%%", startangle=90)
    plt.title("Uso del presupuesto")
    st.pyplot(fig2)

# Descargar Excel
if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "rb") as f:
        st.download_button("Descargar Excel del año", f, FILE_NAME)

# QR
st.divider()
st.subheader("Código QR para compartir")
url = st.text_input("URL pública del dashboard")
if st.button("Generar QR") and url.strip():
    qr_img = qrcode.make(url.strip())
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    st.image(buf.getvalue(), caption="Escanea para abrir")

# ------------------------------------------------------------
# BOTÓN ADMIN: VACIAR MES
# ------------------------------------------------------------
if editing_enabled:
    st.divider()
    if st.button("🗑️ Vaciar mes actual"):
        wb = load_workbook(FILE_NAME)
        ws = openpyxl_get_ws(wb, month_sheet_name(year, month))
        clear_month_data(ws)
        wb.save(FILE_NAME)
        st.rerun()

st.caption("© Consejo Estudiantil — Streamlit, OpenPyXL, Matplotlib y QRCode")
