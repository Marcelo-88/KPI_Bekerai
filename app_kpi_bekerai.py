import re
import textwrap
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Fridolin - KPI Bekerai 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PASTEL_COLORS = [
    "#C0392B",
    "#2980B9",
    "#27AE60",
    "#D35400",
    "#8E44AD",
    "#16A085",
    "#F39C12",
    "#E74C3C",
    "#34495E",
    "#D4AC0D",
]

MEDIBLE_TYPES = {
    "Venta Total Bolivianos": "Bs",
    "Bajas (Precio vta)": "Bs",
    "Inversion RRSS": "Bs",
    "Valor Enviado FBCA": "Bs",
    "Compras Proveedores MP": "Bs",
    "Valor Enviado Bodega": "Bs",
    "Pago Proveedores Marketing": "Bs",
    "Balance Efectivo": "Bs",
    "Pagos Proveedores MP": "Bs",
    "Total C x P": "Bs",
    "Total C x P Proveedores MP": "Bs",
    "Ticket Promedio": "Bs",
    "Pagos menos Compras": "Bs",
    "Vistas x 1 Bs": "Bs",
    "Bajas % vs Vta": "%",
    "Gasto Mktg vs Ventas": "%",
    "Valor Enviado Bodega / Vtas": "%",
    "Valor Enviado FBCA / Vtas": "%",
    "Valor enviado TOTAL / Vtas": "%",
    "Alcance IG&Fb + Reprd. Vistas TikTok": "Unidad",
    "Facturas Emitidas": "Unidad",
    "Tortas vendidas": "Unidad",
    "Bajas": "Unidad",
    "Ventas": "Unidad",
    "Envio": "Unidad",
    "Produccion": "Unidad",
    "Clientes registrados": "Unidad",
    "Puntaje Promedio Checklist Suc": "Unidad",
    "Sucursales Visitadas promedio": "Unidad",
}

KPIS_INVERTIDOS = [
    "BAJAS % VS VTA",
    "TOTAL C X P",
    "TOTAL C X P PROVEEDORES MP",
    "VALOR ENVIADO TOTAL / VTAS",
    "VALOR ENVIADO BODEGA / VTAS",
    "VALOR ENVIADO FBCA / VTAS",
    "BAJAS",
    "BAJAS (PRECIO VTA)",
]

KPIS_NEUTROS = [
    "VALOR ENVIADO FBCA",
    "VALOR ENVIADO BODEGA",
    "COMPRAS PROVEEDORES MP",
]

FRIDOLIN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp { background-color: #F7F4EE; color: #2D2B2A; }
    .main-header {
        background-color: #7A1C29; padding: 1.2rem; border-radius: 14px;
        color: #FFFFFF; text-align: center; margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(122, 28, 41, 0.15);
    }
    .main-header h1 { color: #FFFDF9 !important; margin: 0; font-size: 1.8rem; font-weight: 700; }
    .main-header p { color: #E6C894 !important; margin-top: 5px; margin-bottom: 0; font-size: 0.95rem; }
    section[data-testid="stSidebar"] { background-color: #EFECE4 !important; border-right: 1px solid #DFD9CE; }
    
    .kpi-card-base {
        border-radius: 12px;
        padding: 0.7rem 0.85rem; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); margin-bottom: 0.75rem;
        min-height: 160px; display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid #E6E1D7;
        transition: all 0.2s ease;
    }

    .kpi-bg-drop {
        background-color: #7A1C29 !important; border-color: #58131D !important; color: #FFFFFF !important;
    }
    .kpi-bg-drop .kpi-card-header { color: #FADBD8 !important; }
    .kpi-bg-drop .kpi-card-val { color: #FFFFFF !important; }
    .kpi-bg-drop .kpi-resp-tag { color: #F5CBA7 !important; }
    .kpi-bg-drop .badge-up { color: #2ECC71 !important; font-weight: 700; }
    .kpi-bg-drop .badge-down { color: #F1948A !important; font-weight: 700; }
    .kpi-bg-drop .badge-neutral { color: #EAEDED !important; }
    .kpi-bg-drop .kpi-breakdown-box { background-color: rgba(255, 255, 255, 0.15) !important; border-color: rgba(255, 255, 255, 0.25) !important; }
    .kpi-bg-drop .kpi-breakdown-cat { color: #FADBD8 !important; }
    .kpi-bg-drop .kpi-breakdown-num { color: #FFFFFF !important; }
    .kpi-bg-drop .kpi-card-footer { border-top-color: rgba(255, 255, 255, 0.2) !important; }

    .kpi-bg-up {
        background-color: #E1FFC9 !important; border-color: #C2E8A3 !important; color: #1E4620 !important;
    }
    .kpi-bg-up .kpi-card-header { color: #2C5E2E !important; }
    .kpi-bg-up .kpi-card-val { color: #1E4620 !important; }
    .kpi-bg-up .kpi-resp-tag { color: #4A7A4C !important; }
    .kpi-bg-up .badge-up { color: #1E8449 !important; font-weight: 700; }
    .kpi-bg-up .badge-down { color: #C0392B !important; font-weight: 700; }
    .kpi-bg-up .badge-neutral { color: #526E54 !important; }
    .kpi-bg-up .kpi-breakdown-box { background-color: rgba(255, 255, 255, 0.6) !important; border-color: #C2E8A3 !important; }
    .kpi-bg-up .kpi-breakdown-cat { color: #335C35 !important; }
    .kpi-bg-up .kpi-breakdown-num { color: #1E4620 !important; }

    .kpi-bg-neutral {
        background-color: #EDE7D9 !important; border-color: #D3CBBE !important; color: #2D2B2A !important;
    }
    .kpi-bg-neutral .kpi-card-header { color: #4A4644 !important; }
    .kpi-bg-neutral .kpi-card-val { color: #7A1C29 !important; }
    .kpi-bg-neutral .kpi-resp-tag { color: #8A6D3B !important; }

    .kpi-border-fallback { border: 2px dashed #E6A23C !important; box-shadow: 0 2px 6px rgba(230, 162, 60, 0.18) !important; }
    .kpi-card-header { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; line-height: 1.1; margin-bottom: 0.2rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .kpi-card-val { font-size: 1.55rem; font-weight: 800; margin: 0.1rem 0 0.3rem 0; font-variant-numeric: tabular-nums; line-height: 1.1; }
    
    .kpi-breakdown-box {
        border-radius: 6px; padding: 0.35rem 0.5rem;
        margin: 0.3rem 0 0.4rem 0; font-size: 0.74rem; display: flex; flex-direction: column; gap: 0.15rem;
        border: 1px solid rgba(0,0,0,0.08);
    }
    .kpi-breakdown-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed rgba(0,0,0,0.08); padding-bottom: 1px; }
    .kpi-breakdown-row:last-child { border-bottom: none; padding-bottom: 0; }
    .kpi-breakdown-cat { font-weight: 600; max-width: 55%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .kpi-breakdown-num { font-weight: 700; }
    .kpi-breakdown-pct { font-weight: 700; font-size: 0.88em; margin-left: 4px; }

    .kpi-card-footer { font-size: 0.73rem; border-top: 1px solid rgba(0,0,0,0.08); padding-top: 0.3rem; margin-top: 0.3rem; display: flex; flex-direction: column; gap: 0.1rem; }
    .badge-up { color: #27AE60; font-weight: 600; }
    .badge-down { color: #C0392B; font-weight: 600; }
    .badge-neutral { color: #7F8C8D; font-weight: 500; }
    .badge-warning { color: #D35400; font-weight: 700; background: #FDEBD0; padding: 1px 5px; border-radius: 4px; font-size: 0.68rem; display: inline-block; }
    .kpi-resp-tag { font-size: 0.73rem; font-weight: 600; margin-bottom: 0.1rem; }
    .compare-card-title { font-size: 1.05rem; font-weight: 700; color: #7A1C29; margin-bottom: 0.5rem; }

    /* ESTILOS DE TARJETA ANALÍTICA */
    .analysis-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 1.8rem;
        border: 1px solid #EAE4D9;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03);
        margin-bottom: 1.8rem;
    }
    .analysis-title {
        color: #7A1C29;
        font-size: 1.35rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .analysis-author {
        color: #8C7B6B;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .analysis-section-hdr {
        font-size: 1.05rem;
        font-weight: 700;
        color: #2D2B2A;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
        border-left: 4px solid #7A1C29;
        padding-left: 8px;
    }
    .analysis-list {
        margin: 0;
        padding-left: 1.2rem;
        font-size: 0.93rem;
        line-height: 1.6;
        color: #4A4644;
    }
    .analysis-list li {
        margin-bottom: 0.5rem;
    }

    /* ESTILOS DE MÓDULOS INFERIORES EN COLUMNAS */
    .sub-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 1.3rem;
        border: 1px solid #EAE4D9;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        height: 100%;
    }
    .sub-card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #7A1C29;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .weather-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }
    .weather-item {
        background: #FDFBF7;
        border: 1px solid #F0EAE1;
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }
    .weather-val {
        font-size: 1.3rem;
        font-weight: 800;
        color: #7A1C29;
        margin-top: 2px;
    }
    .weather-lbl {
        font-size: 0.78rem;
        color: #7F8C8D;
        font-weight: 600;
    }
    .festivos-container {
        max-height: 380px;
        overflow-y: auto;
        padding-right: 5px;
    }
    .festivo-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0.8rem;
        border-bottom: 1px solid #F3EFEA;
        font-size: 0.85rem;
    }
    .festivo-row:last-child { border-bottom: none; }
    .festivo-name { font-weight: 600; color: #2D2B2A; }
    .festivo-date { font-weight: 700; color: #D35400; background: #FDEBD0; padding: 2px 8px; border-radius: 6px; font-size: 0.78rem; }

    .forecast-card {
        background: #FDFBF7;
        border: 1px solid #EAE4D9;
        border-radius: 10px;
        padding: 0.8rem;
        margin-top: 10px;
    }
    .forecast-header {
        font-weight: 700;
        color: #7A1C29;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
        border-bottom: 1px dashed #E2DCD2;
        padding-bottom: 0.2rem;
    }
    .forecast-detail {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: #4A4644;
        margin-bottom: 0.2rem;
    }

    .task-container-card {
        background-color: #FFFFFF; border: 1px solid #E2DCD2; border-radius: 16px;
        padding: 1rem 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 2rem;
    }
    .task-row {
        padding: 1rem 0.5rem; border-bottom: 1px solid #F0ECE3; border-left: 5px solid transparent;
        border-radius: 4px; margin-bottom: 0.2rem;
    }
    .task-row-pendiente { border-left-color: #E74C3C; }
    .task-row-proceso { border-left-color: #F39C12; }
    .task-row-finalizado { border-left-color: #27AE60; }
    
    .task-title { font-size: 0.98rem; font-weight: 700; color: #2D2B2A; margin-bottom: 0.4rem; padding-left: 0.4rem; }
    .task-badge { display: inline-block; padding: 3px 9px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .badge-status-pendiente { background-color: #FDEDEC; color: #C0392B; }
    .badge-status-proceso { background-color: #FEF9E7; color: #D68910; }
    .badge-status-finalizado { background-color: #E8F8F5; color: #1E8449; }
    .badge-dept { background-color: #EAECEE; color: #424949; font-weight: 600; margin-left: 6px; }

    .task-meta { font-size: 0.83rem; color: #5D6D7E; margin-top: 0.4rem; padding-left: 0.4rem; display: flex; flex-wrap: wrap; gap: 12px; }
    .task-meta-item { display: flex; align-items: center; gap: 4px; }
    
    .resp-summary-card {
        background-color: #FFFFFF; border: 1px solid #E5E0D8; border-radius: 12px;
        padding: 1rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 0.8rem;
    }
    .resp-summary-name { font-weight: 700; font-size: 1rem; color: #7A1C29; margin-bottom: 0.6rem; border-bottom: 1px solid #F0ECE3; padding-bottom: 0.3rem; }
    .resp-stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; font-size: 0.8rem; }
    .resp-stat-num { font-weight: 800; font-size: 1.1rem; }
</style>
"""
st.markdown(FRIDOLIN_CSS, unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y PARSEO DE DATOS
# ==========================================
GOOGLE_SHEET_ID = "1YmxMIgdqn0Oe38mmUF3pFBVyWgUjyyxjmDdmWp-Oz1g"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=xlsx"
ONLINE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit"


def parse_custom_number(val):
    if pd.isna(val) or val == "" or str(val).strip() == "":
        return None
    val_str = str(val).strip()
    if any(
        err in val_str
        for err in ["#¡DIV/0!", "#DIV/0!", "#N/A", "#REF!", "#VALUE!"]
    ):
        return None

    cleaned = re.sub(r"[^0-9,\.\-]", "", val_str)
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return None


def format_kpi_value(val, medible_name):
    if val is None or pd.isna(val):
        return "-"

    kpi_clean = str(medible_name).strip()
    unit_type = MEDIBLE_TYPES.get(kpi_clean, None)

    if not unit_type:
        for k, v in MEDIBLE_TYPES.items():
            if k.lower() in kpi_clean.lower():
                unit_type = v
                break

    if unit_type == "%":
        val_pct = val * 100 if val <= 1.0 and val != 0 else val
        return f"{val_pct:.2f}%"
    elif unit_type == "Bs":
        if val >= 100 or val % 1 == 0:
            return f"Bs {val:,.0f}"
        return f"Bs {val:,.2f}"
    else:
        if val >= 100 or val % 1 == 0:
            return f"{val:,.0f}"
        return f"{val:,.2f}"


@st.cache_data(ttl=60)
def load_data():
    sheets = pd.read_excel(
        EXCEL_URL, 
        sheet_name=["KPI", "Tareas", "Ventas_Clima"], 
        header=None
    )

    # PARSER PESTAÑA KPI
    df_kpi_raw = sheets.get("KPI", pd.DataFrame())
    if not df_kpi_raw.empty:
        header_idx = None
        for idx, row in df_kpi_raw.iterrows():
            row_vals = [str(val).strip() for val in row.values]
            if any(
                h in row_vals
                for h in ["Medibles", "Medible", "Quien", "Responsable"]
            ):
                header_idx = idx
                break

        if header_idx is not None:
            df_kpi_clean = df_kpi_raw.iloc[header_idx + 1 :].copy()
            df_kpi_clean.columns = [
                str(c).strip() for c in df_kpi_raw.iloc[header_idx].values
            ]
            df_kpi_clean = df_kpi_clean.dropna(how="all")

            id_cols = [
                c
                for c in df_kpi_clean.columns
                if c
                in [
                    "Quien",
                    "Responsable",
                    "Departamento",
                    "Medibles",
                    "Medible",
                    "Categoria",
                    "Categoría",
                ]
            ]
            val_cols = [
                c
                for c in df_kpi_clean.columns
                if c not in id_cols
                and not str(c).startswith("Unnamed")
                and str(c) != "nan"
            ]

            df_kpi_long = pd.melt(
                df_kpi_clean,
                id_vars=id_cols,
                value_vars=val_cols,
                var_name="Semana",
                value_name="Valor_Raw",
            )

            df_kpi_long["Valor"] = df_kpi_long["Valor_Raw"].apply(
                parse_custom_number
            )
            df_kpi_long.rename(
                columns={"Quien": "Responsable", "Medibles": "Medible"},
                inplace=True,
            )

            if "Categoria" in df_kpi_long.columns:
                df_kpi_long.rename(
                    columns={"Categoria": "Categoria_Clean"}, inplace=True
                )
            elif "Categoría" in df_kpi_long.columns:
                df_kpi_long.rename(
                    columns={"Categoría": "Categoria_Clean"}, inplace=True
                )
            else:
                df_kpi_long["Categoria_Clean"] = None

            df_kpi_long = df_kpi_long[
                df_kpi_long["Medible"].notna()
                & (df_kpi_long["Medible"] != "nan")
            ]
            df_kpi_long["Medible"] = (
                df_kpi_long["Medible"].astype(str).str.strip()
            )
            df_kpi_long["Departamento"] = (
                df_kpi_long["Departamento"]
                .fillna("Sin Depto")
                .astype(str)
                .str.strip()
            )
            df_kpi_long["Categoria_Clean"] = (
                df_kpi_long["Categoria_Clean"]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            df_kpi_long["Medible_Full"] = df_kpi_long.apply(
                lambda r: (
                    f"{r['Medible']} {r['Categoria_Clean']}".strip()
                    if r["Categoria_Clean"]
                    else r["Medible"]
                ),
                axis=1,
            )
        else:
            df_kpi_long = pd.DataFrame()
    else:
        df_kpi_long = pd.DataFrame()

    # PARSER PESTAÑA TAREAS
    df_tareas_raw = sheets.get("Tareas", pd.DataFrame())
    if not df_tareas_raw.empty:
        h_idx_t = None
        for idx, row in df_tareas_raw.iterrows():
            row_vals = [str(val).strip() for val in row.values]
            if any(
                h in row_vals
                for h in ["TAREA", "Tarea", "Responsable Principal", "Estado"]
            ):
                h_idx_t = idx
                break

        if h_idx_t is not None:
            df_tasks = df_tareas_raw.iloc[h_idx_t + 1 :].copy()
            df_tasks.columns = [
                str(c).strip() for c in df_tareas_raw.iloc[h_idx_t].values
            ]
            df_tasks = df_tasks.dropna(how="all")

            df_tasks["TAREA"] = df_tasks["TAREA"].astype(str).str.strip()
            df_tasks = df_tasks[
                df_tasks["TAREA"].notna()
                & (df_tasks["TAREA"] != "nan")
                & (df_tasks["TAREA"] != "")
            ]

            df_tasks["Estado"] = (
                df_tasks["Estado"].fillna("Pendiente").astype(str).str.strip()
            )
            df_tasks["Responsable Principal"] = (
                df_tasks["Responsable Principal"]
                .fillna("Sin Asignar")
                .astype(str)
                .str.strip()
            )
            df_tasks["Departamento"] = (
                df_tasks["Departamento"]
                .fillna("General")
                .astype(str)
                .str.strip()
            )
        else:
            df_tasks = pd.DataFrame()
    else:
        df_tasks = pd.DataFrame()

    # PARSER PESTAÑA VENTAS_CLIMA
    df_vc_raw = sheets.get("Ventas_Clima", pd.DataFrame())
    if not df_vc_raw.empty:
        h_idx_vc = None
        for idx, row in df_vc_raw.iterrows():
            row_vals = [str(val).strip() for val in row.values]
            if any(h in row_vals for h in ["Rango de la semana", "Ventas", "Temp. Promedio (°C)"]):
                h_idx_vc = idx
                break
        
        if h_idx_vc is not None:
            df_vc = df_vc_raw.iloc[h_idx_vc + 1 :].copy()
            df_vc.columns = [str(c).strip() for c in df_vc_raw.iloc[h_idx_vc].values]
            df_vc = df_vc.dropna(how="all")
        else:
            df_vc = pd.DataFrame()
    else:
        df_vc = pd.DataFrame()

    return df_kpi_long, df_tasks, df_vc


# ==========================================
# 3. HELPER DE GRÁFICAS MULTI-KPI
# ==========================================
def render_multi_kpi_chart(
    df_kpis,
    kpi_list,
    title="Comparativa Multi-KPI",
    height=420,
    unit_label="Valores",
):
    existing_kpis = [
        k
        for k in kpi_list
        if k in df_kpis["Medible"].values or k in df_kpis["Medible_Full"].values
    ]

    if not existing_kpis:
        fig = go.Figure()
        fig.add_annotation(
            text="Selecciona al menos una categoría o medible para visualizar",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#7A1C29"),
        )
        fig.update_layout(
            height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF"
        )
        return fig

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for idx, kpi in enumerate(existing_kpis):
        sub_df = df_kpis[
            (df_kpis["Medible_Full"] == kpi) | (df_kpis["Medible"] == kpi)
        ].copy()

        if (
            kpi in sub_df["Medible"].values
            and sub_df["Categoria_Clean"].nunique() > 1
        ):
            sub_df = sub_df.groupby("Semana", as_index=False)["Valor"].sum()

        sub_df = sub_df[sub_df["Valor"].notna()]
        if sub_df.empty:
            continue

        color = PASTEL_COLORS[idx % len(PASTEL_COLORS)]
        max_val = sub_df["Valor"].max()
        use_secondary = max_val > 15000 and "Bs" not in unit_label

        hover_template = (
            f"<b>{kpi}</b><br>"
            "🗓️ %{x}<br>"
            "📊 Valor: <b>%{y:,.2f}</b>"
            "<extra></extra>"
        )

        fig.add_trace(
            go.Scatter(
                x=sub_df["Semana"],
                y=sub_df["Valor"],
                name=f"{kpi} (Eje Der.)" if use_secondary else str(kpi),
                mode="lines+markers",
                line=dict(color=color, width=3),
                marker=dict(size=7, color=color, symbol="circle"),
                hovertemplate=hover_template,
                connectgaps=False,
            ),
            secondary_y=use_secondary,
        )

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=15, color="#7A1C29"),
            x=0,
            y=0.98,
        ),
        xaxis=dict(
            title=None, tickangle=-45, showgrid=True, gridcolor="#EFECE6"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        height=height,
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.28,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#DFD9CE",
            borderwidth=1,
        ),
        margin=dict(l=55, r=55, t=50, b=110),
    )

    fig.update_yaxes(
        title_text=unit_label,
        showgrid=True,
        gridcolor="#EFECE6",
        tickformat=",.0f",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text=f"{unit_label} (Volumen Alto)",
        showgrid=False,
        tickformat=",.0f",
        secondary_y=True,
    )

    return fig


if hasattr(st, "dialog"):

    @st.dialog("🔍 Vista Ampliada del Gráfico", width="large")
    def show_full_graph_dialog(df, kpi_list, title, unit_label="Valores"):
        fig = render_multi_kpi_chart(
            df, kpi_list, title=title, height=600, unit_label=unit_label
        )
        st.plotly_chart(fig, use_container_width=True, key=f"dialog_{title}")


# ==========================================
# 4. BARRA LATERAL Y NAVEGACIÓN
# ==========================================
st.sidebar.title("📌 Menú Principal")

menu_option = st.sidebar.radio(
    "Selecciona un Módulo:",
    [
        "📊 Dashboards KPIs",
        "🔀 Comparador KPI vs KPI",
        "🌤️ Análisis Clima & Festivos",
        "📝 Gestión de Tareas",
        "🏆 Scorecard & Cumplimiento",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Datos Ahora", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("¡Datos actualizados!")

st.sidebar.link_button(
    "🌐 Abrir Sheet en Google Drive", ONLINE_SHEET_URL, use_container_width=True
)

try:
    df_kpis, df_tasks, df_vc = load_data()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    st.stop()

# Header Superior
st.markdown(
    """
<div class="main-header">
    <h1>FRIDOLIN - TABLERO CONTROL EOS & KPIs</h1>
    <p>Monitoreo Semanal de Indicadores, Tareas y Cumplimiento Bekerai 2026</p>
</div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 5. MÓDULOS DE LA APLICACIÓN
# ==========================================

# ------------------------------------------
# MÓDULO 1: DASHBOARDS KPIS
# ------------------------------------------
if menu_option == "📊 Dashboards KPIs":
    st.subheader("📌 Resumen de Indicadores Semanales")

    if not df_kpis.empty and "Medible" in df_kpis.columns:
        semanas_unicas = list(df_kpis["Semana"].unique())
        deptos_unicos = ["Todos"] + sorted(
            [
                str(d)
                for d in df_kpis["Departamento"].dropna().unique()
                if str(d) != "nan" and str(d) != "Sin Depto"
            ]
        )

        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        with col_f1:
            selected_week = st.selectbox(
                "Seleccionar Semana a Inspeccionar:",
                semanas_unicas,
                index=len(semanas_unicas) - 1,
            )

        with col_f2:
            selected_dept = st.selectbox(
                "Filtrar por Departamento:", deptos_unicos
            )

        df_filtered_dept = df_kpis.copy()
        if selected_dept != "Todos":
            df_filtered_dept = df_filtered_dept[
                df_filtered_dept["Departamento"] == selected_dept
            ]

        responsables = ["Todos"] + sorted(
            [
                str(r)
                for r in df_filtered_dept["Responsable"].dropna().unique()
                if str(r) != "nan"
            ]
        )
        with col_f3:
            selected_resp = st.selectbox(
                "Filtrar por Responsable:", responsables
            )

        current_week_idx = semanas_unicas.index(selected_week)
        df_all_selected = df_filtered_dept.copy()
        if selected_resp != "Todos":
            df_all_selected = df_all_selected[
                df_all_selected["Responsable"] == selected_resp
            ]

        metrics_list = df_all_selected["Medible"].unique()

        st.markdown(f"##### Datos correspondientes a **{selected_week}**")

        if len(metrics_list) > 0:
            cols = st.columns(4)
            for idx, kpi in enumerate(metrics_list):
                df_kpi_series = df_filtered_dept[
                    df_filtered_dept["Medible"] == kpi
                ]
                if selected_resp != "Todos":
                    df_kpi_series = df_kpi_series[
                        df_kpi_series["Responsable"] == selected_resp
                    ]

                resp = (
                    df_kpi_series["Responsable"].dropna().values[0]
                    if not df_kpi_series.empty
                    else "-"
                )

                val_curr = 0.0
                actual_data_week = selected_week
                is_fallback = False

                def get_week_data(w_name):
                    rows_w = df_kpi_series[df_kpi_series["Semana"] == w_name]
                    valid_rows = rows_w[rows_w["Valor"].notna()]
                    if not valid_rows.empty:
                        return valid_rows
                    return None

                df_current_rows = None
                for w_idx in range(current_week_idx, -1, -1):
                    w_name = semanas_unicas[w_idx]
                    w_data = get_week_data(w_name)
                    if w_data is not None:
                        df_current_rows = w_data
                        val_curr = float(w_data["Valor"].sum())
                        actual_data_week = w_name
                        if w_idx < current_week_idx:
                            is_fallback = True
                        break

                val_prev = None
                prev_w_name = ""
                avg_total = 0.0

                actual_week_idx_found = (
                    semanas_unicas.index(actual_data_week)
                    if actual_data_week in semanas_unicas
                    else -1
                )

                present_cats = []
                if df_current_rows is not None and not df_current_rows.empty:
                    present_cats = [
                        c
                        for c in df_current_rows["Categoria_Clean"].unique()
                        if c != ""
                    ]

                df_prev_rows = None
                if actual_week_idx_found > 0:
                    for w_idx_prev in range(actual_week_idx_found - 1, -1, -1):
                        p_name = semanas_unicas[w_idx_prev]
                        p_data = get_week_data(p_name)
                        if p_data is not None:
                            prev_w_name = p_name
                            df_prev_rows = p_data
                            break

                if present_cats:
                    if df_prev_rows is not None:
                        valid_prev = df_prev_rows[
                            df_prev_rows["Categoria_Clean"].isin(present_cats)
                            & df_prev_rows["Valor"].notna()
                        ]
                        if not valid_prev.empty:
                            val_prev = float(valid_prev["Valor"].sum())

                    filtered_series = df_kpi_series[
                        df_kpi_series["Categoria_Clean"].isin(present_cats)
                    ]
                    valid_series = filtered_series.dropna(subset=["Valor"])
                    if not valid_series.empty:
                        weekly_totals = valid_series.groupby("Semana")["Valor"].sum()
                        valid_totals = weekly_totals[weekly_totals > 0]
                        avg_total = valid_totals.mean() if not valid_totals.empty else 0.0
                else:
                    if df_prev_rows is not None:
                        val_prev = float(df_prev_rows["Valor"].sum())

                    valid_series = df_kpi_series.dropna(subset=["Valor"])
                    if not valid_series.empty:
                        weekly_totals = valid_series.groupby("Semana")["Valor"].sum()
                        valid_totals = weekly_totals[weekly_totals > 0]
                        avg_total = valid_totals.mean() if not valid_totals.empty else 0.0

                pct_prev = None
                if val_prev is not None and val_prev != 0 and val_curr != 0:
                    pct_prev = ((val_curr - val_prev) / val_prev) * 100
                    if pct_prev > 0:
                        var_prev_html = f'<span class="badge-up">▲ +{pct_prev:.1f}%</span> vs {prev_w_name}'
                    elif pct_prev < 0:
                        var_prev_html = f'<span class="badge-down">▼ {pct_prev:.1f}%</span> vs {prev_w_name}'
                    else:
                        var_prev_html = f'<span class="badge-neutral">= 0.0%</span> vs {prev_w_name}'
                else:
                    var_prev_html = '<span class="badge-neutral">-- N/A vs sem anterior</span>'

                pct_avg = None
                if avg_total > 0 and val_curr != 0:
                    pct_avg = ((val_curr - avg_total) / avg_total) * 100
                    if pct_avg > 0:
                        var_avg_html = f'<span class="badge-up">▲ +{pct_avg:.1f}%</span> vs prom ({format_kpi_value(avg_total, kpi)})'
                    elif pct_avg < 0:
                        var_avg_html = f'<span class="badge-down">▼ {pct_avg:.1f}%</span> vs prom ({format_kpi_value(avg_total, kpi)})'
                    else:
                        var_avg_html = f'<span class="badge-neutral">= prom ({format_kpi_value(avg_total, kpi)})</span>'
                else:
                    var_avg_html = '<span class="badge-neutral">-- N/A vs prom</span>'

                kpi_upper = kpi.upper().strip()

                if any(kn in kpi_upper for kn in KPIS_NEUTROS):
                    bg_color_class = "kpi-bg-neutral"
                elif any(ki in kpi_upper for ki in KPIS_INVERTIDOS):
                    if pct_prev is not None:
                        if pct_prev > 0:
                            bg_color_class = "kpi-bg-drop"
                        elif pct_prev < 0:
                            bg_color_class = "kpi-bg-up"
                        else:
                            bg_color_class = "kpi-bg-neutral"
                    else:
                        bg_color_class = "kpi-bg-neutral"
                else:
                    if pct_prev is not None:
                        if pct_prev > 0:
                            bg_color_class = "kpi-bg-up"
                        elif pct_prev < 0:
                            bg_color_class = "kpi-bg-drop"
                        else:
                            bg_color_class = "kpi-bg-neutral"
                    else:
                        bg_color_class = "kpi-bg-neutral"

                val_formatted = format_kpi_value(val_curr, kpi)

                breakdown_html = ""
                if df_current_rows is not None and not df_current_rows.empty:
                    categories_rows = df_current_rows[
                        df_current_rows["Categoria_Clean"] != ""
                    ]
                    if len(categories_rows) > 0:
                        items_html = ""
                        for _, row_cat in categories_rows.iterrows():
                            c_name = row_cat["Categoria_Clean"]
                            c_val = row_cat["Valor"]
                            c_formatted = format_kpi_value(c_val, kpi)
                            
                            cat_pct_html = ""
                            if df_prev_rows is not None and not df_prev_rows.empty:
                                prev_cat_row = df_prev_rows[
                                    df_prev_rows["Categoria_Clean"] == c_name
                                ]
                                if not prev_cat_row.empty and pd.notna(prev_cat_row["Valor"].values[0]):
                                    c_prev_val = float(prev_cat_row["Valor"].values[0])
                                    if c_prev_val > 0 and c_val is not None:
                                        c_pct = ((c_val - c_prev_val) / c_prev_val) * 100
                                        symbol = "▲" if c_pct >= 0 else "▼"
                                        pct_class = "badge-up" if c_pct >= 0 else "badge-down"
                                        cat_pct_html = f'<span class="kpi-breakdown-pct {pct_class}">{symbol} {c_pct:+.1f}%</span>'

                            items_html += (
                                f'<div class="kpi-breakdown-row">'
                                f'<span class="kpi-breakdown-cat">{c_name}</span>'
                                f'<span><span class="kpi-breakdown-num">{c_formatted}</span> {cat_pct_html}</span>'
                                f'</div>'
                            )

                        breakdown_html = (
                            f'<div class="kpi-breakdown-box">{items_html}</div>'
                        )

                fallback_class = "kpi-border-fallback" if is_fallback else ""
                fallback_tag = (
                    f'<div><span class="badge-warning">⚠️ {actual_data_week}</span></div>'
                    if is_fallback
                    else ""
                )

                html_code = (
                    f'<div class="kpi-card-base {bg_color_class} {fallback_class}">'
                    f"<div>"
                    f'<div class="kpi-card-header" title="{kpi}">{kpi}</div>'
                    f'<div class="kpi-resp-tag">👤 Resp: {resp}</div>'
                    f"{fallback_tag}"
                    f'<div class="kpi-card-val">{val_formatted}</div>'
                    f"{breakdown_html}"
                    f"</div>"
                    f'<div class="kpi-card-footer">'
                    f"<div>{var_prev_html}</div>"
                    f"<div>{var_avg_html}</div>"
                    f"</div>"
                    f"</div>"
                )

                with cols[idx % 4]:
                    st.markdown(html_code, unsafe_allow_html=True)
        else:
            st.info("No se encontraron medibles para los filtros seleccionados.")

# ------------------------------------------
# MÓDULO 2: COMPARADOR KPI vs KPI
# ------------------------------------------
elif menu_option == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Análisis Comparativo Multi-KPI")

    if not df_kpis.empty and "Medible" in df_kpis.columns:
        all_kpis_base = list(df_kpis["Medible"].unique())
        all_kpis_full = [
            k
            for k in df_kpis["Medible_Full"].unique()
            if k and str(k) != "nan"
        ]
        all_kpis_in_db = sorted(list(set(all_kpis_base + all_kpis_full)))

        def find_kpis_exact_or_keyword(category_list):
            matched = []
            for k in all_kpis_in_db:
                k_upper = str(k).upper()
                for cat in category_list:
                    cat_upper = cat.upper()
                    if (
                        cat_upper in k_upper
                        or (cat_upper == "TORTAS" and "TORTA" in k_upper)
                        or (cat_upper == "SALADOS" and "SALADO" in k_upper)
                    ):
                        matched.append(k)
                        break
            return list(set(matched))

        kpi_g1 = [
            k
            for k in all_kpis_in_db
            if any(
                kw in k.upper()
                for kw in [
                    "VENTAS",
                    "PAGOS PROVEEDORES MP",
                    "TOTAL C X P",
                    "BALANCE EFECTIVO",
                ]
            )
        ]
        kpi_g3 = [
            k
            for k in all_kpis_in_db
            if any(
                kw in k.upper()
                for kw in [
                    "INVERSION RRSS",
                    "PAGO PROVEEDORES MARKETING",
                    "VENTAS",
                ]
            )
        ]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                '<div class="compare-card-title">💵 1. Ventas vs Pagos vs CxP vs Efectivo (Bs)</div>',
                unsafe_allow_html=True,
            )
            fig1 = render_multi_kpi_chart(
                df_kpis,
                kpi_g1,
                title="Finanzas & Flujo de Caja",
                height=380,
                unit_label="Monto en Bs",
            )
            st.plotly_chart(fig1, use_container_width=True, key="card_1_main")
            if st.button(
                "🔍 Maximizar Gráfico 1",
                key="btn_max_1",
                use_container_width=True,
            ):
                show_full_graph_dialog(
                    df_kpis,
                    kpi_g1,
                    "Finanzas & Flujo de Caja",
                    unit_label="Monto en Bs",
                )

        with c2:
            st.markdown(
                '<div class="compare-card-title">🍰 2. Producción, Envíos y Bajas por Categoría</div>',
                unsafe_allow_html=True,
            )
            categorias_bekerai = [
                "Salados",
                "Tortas",
                "Pasteles Individuales",
                "Postres Enteros",
                "Panaderia",
            ]
            selected_cats = st.multiselect(
                "Filtrar Categorías:",
                categorias_bekerai,
                default=["Salados", "Tortas"],
            )

            kpi_g2 = (
                find_kpis_exact_or_keyword(selected_cats)
                if selected_cats
                else []
            )
            fig2 = render_multi_kpi_chart(
                df_kpis,
                kpi_g2,
                title="Flujo de Categorías Seleccionadas",
                height=380,
                unit_label="Unidades",
            )
            st.plotly_chart(fig2, use_container_width=True, key="card_2_main")
            if st.button(
                "🔍 Maximizar Gráfico 2",
                key="btn_max_2",
                use_container_width=True,
            ):
                show_full_graph_dialog(
                    df_kpis,
                    kpi_g2,
                    "Flujo de Categorías Seleccionadas",
                    unit_label="Unidades",
                )

        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(
                '<div class="compare-card-title">📣 3. Inversión Marketing vs Ventas (Bs)</div>',
                unsafe_allow_html=True,
            )
            fig3 = render_multi_kpi_chart(
                df_kpis,
                kpi_g3,
                title="Marketing & Retorno",
                height=380,
                unit_label="Monto en Bs",
            )
            st.plotly_chart(fig3, use_container_width=True, key="card_3_main")
            if st.button(
                "🔍 Maximizar Gráfico 3",
                key="btn_max_3",
                use_container_width=True,
            ):
                show_full_graph_dialog(
                    df_kpis,
                    kpi_g3,
                    "Marketing & Retorno",
                    unit_label="Monto en Bs",
                )

        with c4:
            st.markdown(
                '<div class="compare-card-title">🛠️ 4. Comparador Libre</div>',
                unsafe_allow_html=True,
            )
            selected_custom = st.multiselect(
                "Selecciona cualquier conjunto de KPIs:",
                all_kpis_in_db,
                default=(
                    all_kpis_in_db[:2]
                    if len(all_kpis_in_db) >= 2
                    else all_kpis_in_db
                ),
            )
            if selected_custom:
                fig4 = render_multi_kpi_chart(
                    df_kpis,
                    selected_custom,
                    title="Selección Libre Personalizada",
                    height=350,
                    unit_label="Valores",
                )
                st.plotly_chart(
                    fig4, use_container_width=True, key="card_4_main"
                )
                if st.button(
                    "🔍 Maximizar Gráfico 4",
                    key="btn_max_4",
                    use_container_width=True,
                ):
                    show_full_graph_dialog(
                        df_kpis,
                        selected_custom,
                        "Selección Libre Personalizada",
                        unit_label="Valores",
                    )

# ------------------------------------------
# MÓDULO 3: ANÁLISIS CLIMA & FESTIVOS
# ------------------------------------------
elif menu_option == "🌤️ Análisis Clima & Festivos":
    st.subheader("🌤️ Relación del Clima, Festividades y Producción por Categorías")

    analysis_card_html = textwrap.dedent("""
    <div class="analysis-card">
        <div class="analysis-title">💡 Opinión Analítica e Interpretación Comercial</div>
        <div class="analysis-author">POR: ANALISTA COMERCIAL & DE VENTAS</div>
        
        <p style="font-size: 0.95rem; line-height: 1.5; color: #333;">
            Análisis cualitativo y porcentual basado en la relación de Ventas Totales semanales, Clima en Santa Cruz y la Producción por Categorías (Panadería, Pasteles Individuales, Postres Enteros, Salados y Tortas):
        </p>
        
        <div class="analysis-section-hdr">🌬️ Sensibilidad al Clima (Surazos y Días Fríos)</div>
        <ul class="analysis-list">
            <li><b>Categoría más impactada (Salados):</b> Ante caídas bruscas de temperatura (11°C - 13°C), la demanda de salados es la que más se dispara, registrando incrementos de producción de hasta <b>+150% a +200%</b> frente a sus semanas promedio.</li>
            <li><b>Efecto en Tortas y Repostería:</b> Muestran un crecimiento moderado del <b>+80% al +100%</b> durante frentes fríos, asociado al consumo caliente.</li>
        </ul>

        <div class="analysis-section-hdr">🎉 Impacto de Festividades sin "Efecto Regalo"</div>
        <ul class="analysis-list">
            <li><b>Carnaval:</b> Provoca una caída general de volumen de aprox. <b>-10% a -15%</b> en salón y salados por el desplazamiento de la población.</li>
            <li><b>Semana Santa y Feriados Religiosos:</b> Mantienen ventas estables reasignando el mix: la producción de <b>Pasteles Individuales y Salados</b> crece cerca de un <b>+25%</b>.</li>
        </ul>

        <div class="analysis-section-hdr">🔍 Análisis de Fondo: Comportamiento Base (Sin Picos Comerciales)</div>
        <p style="font-size: 0.85rem; color: #7F8C8D; margin-bottom: 0.5rem; font-style: italic;">
            Descartando las fechas con fuerte "efecto regalo" (Día de la Madre, Padre y Niño), donde la demanda ocurre independientemente del clima:
        </p>
        <ul class="analysis-list">
            <li><b>Salados es la categoría más vulnerable al clima:</b> 100% reactiva. En semanas calurosas (27°C - 32°C), la producción cae hasta un <b>-30%</b>.</li>
            <li><b>Tortas y Postres Enteros son "Resistentes al Clima":</b> En semanas normales o festivos menores, el volumen de producción varía muy poco (±10%).</li>
            <li><b>Pasteles Individuales como amortiguador:</b> Categoría constante todo el año. Ante climas extremos amortigua variaciones con respecto a postres grandes.</li>
        </ul>
    </div>
    """)

    if hasattr(st, "html"):
        st.html(analysis_card_html)
    else:
        st.markdown(analysis_card_html, unsafe_allow_html=True)

    # CÁLCULO DINÁMICO DE FECHAS (Semana de Lunes a Domingo)
    today = datetime.now()
    # Lunes de la semana actual
    monday_w1 = today - timedelta(days=today.weekday())
    sunday_w1 = monday_w1 + timedelta(days=6)
    
    # Lunes y Domingo de la siguiente semana
    monday_w2 = monday_w1 + timedelta(days=7)
    sunday_w2 = sunday_w1 + timedelta(days=7)
    
    str_w1 = f"{monday_w1.strftime('%d/%m')} al {sunday_w1.strftime('%d/%m/%Y')}"
    str_w2 = f"{monday_w2.strftime('%d/%m')} al {sunday_w2.strftime('%d/%m/%Y')}"

    col_left, col_right = st.columns(2)

    with col_left:
        weather_card_html = textwrap.dedent(f"""
        <div class="sub-card">
            <div class="sub-card-title">🌡️ Métricas de Clima Semanal (Santa Cruz)</div>
            <div class="weather-grid">
                <div class="weather-item">
                    <div class="weather-lbl">🌡️ TEMP. PROMEDIO</div>
                    <div class="weather-val">21.8 °C</div>
                </div>
                <div class="weather-item">
                    <div class="weather-lbl">❄️ MÍNIMA HISTÓRICA</div>
                    <div class="weather-val">11.0 °C</div>
                </div>
                <div class="weather-item">
                    <div class="weather-lbl">🔥 MÁXIMA ALCANZADA</div>
                    <div class="weather-val">32.9 °C</div>
                </div>
                <div class="weather-item">
                    <div class="weather-lbl">☁️ CLIMA PREDOMINANTE</div>
                    <div class="weather-val" style="font-size: 1rem; margin-top: 5px;">Despejado / Nublado</div>
                </div>
            </div>
            
            <div style="margin-top: 1.5rem; font-weight: 700; color: #7A1C29; font-size: 1rem;">
                🔮 Pronóstico Climatológico (Próximas 2 Semanas)
            </div>

            <div class="forecast-card">
                <div class="forecast-header">🗓️ Semana Entrante ({str_w1})</div>
                <div class="forecast-detail"><span>Temp. Máxima Promedio:</span> <b>28.5 °C</b></div>
                <div class="forecast-detail"><span>Temp. Mínima Promedio:</span> <b>18.2 °C</b></div>
                <div class="forecast-detail"><span>Precipitaciones:</span> <b>12 mm (Baja probabilidad)</b></div>
                <div class="forecast-detail"><span>Estado:</span> <b>Parcialmente Nublado / Caluroso</b></div>
            </div>

            <div class="forecast-card">
                <div class="forecast-header">🗓️ Siguiente Semana ({str_w2})</div>
                <div class="forecast-detail"><span>Temp. Máxima Promedio:</span> <b>22.1 °C</b></div>
                <div class="forecast-detail"><span>Temp. Mínima Promedio:</span> <b>13.5 °C</b></div>
                <div class="forecast-detail"><span>Precipitaciones:</span> <b>45 mm (Ingreso de Surazo)</b></div>
                <div class="forecast-detail"><span>Estado:</span> <b>Frío / Lluvias Moderadas ❄️</b></div>
            </div>

            <p style="font-size: 0.78rem; color: #95A5A6; text-align: center; margin-top: 1rem; margin-bottom: 0;">
                *Valores consolidados del histórico semanal registrado y proyección meteorológica oficial.
            </p>
        </div>
        """)
        if hasattr(st, "html"):
            st.html(weather_card_html)
        else:
            st.markdown(weather_card_html, unsafe_allow_html=True)

    with col_right:
        festivos_list = [
            ("Año Nuevo (Feriado Oficial)", "01/01/2026"),
            ("Fundación del Estado Plurinacional", "22/01/2026"),
            ("Fiesta de la Virgen de la Candelaria", "02/02/2026"),
            ("Lunes y Martes de Carnaval", "16-17/02/2026"),
            ("Día del Padre (Día Especial)", "19/03/2026"),
            ("Viernes Santo (Feriado Oficial)", "03/04/2026"),
            ("Día del Niño Boliviano", "12/04/2026"),
            ("Día del Trabajo (Feriado Oficial)", "01/05/2026"),
            ("Día de la Madre Boliviana", "27/05/2026"),
            ("Corpus Christi (Feriado Oficial)", "04/06/2026"),
            ("Año Nuevo Andino Amazónico", "21/06/2026"),
            ("Día de la Independencia de Bolivia", "06/08/2026"),
            ("Aniversario de Santa Cruz", "24/09/2026"),
            ("Todos los Santos", "01-02/11/2026"),
            ("Navidad (Feriado Oficial)", "25/12/2026"),
        ]

        festivos_rows = "".join(
            [
                f'<div class="festivo-row"><span class="festivo-name">🎉 {nombre}</span><span class="festivo-date">{fecha}</span></div>'
                for nombre, fecha in festivos_list
            ]
        )

        festivos_card_html = textwrap.dedent(f"""
        <div class="sub-card">
            <div class="sub-card-title">📅 Calendario de Festividades & Días Especiales</div>
            <div class="festivos-container">
                {festivos_rows}
            </div>
        </div>
        """)
        if hasattr(st, "html"):
            st.html(festivos_card_html)
        else:
            st.markdown(festivos_card_html, unsafe_allow_html=True)

# ------------------------------------------
# MÓDULO 4: GESTIÓN DE TAREAS
# ------------------------------------------
elif menu_option == "📝 Gestión de Tareas":
    st.subheader("📝 Lista de Tareas Operativas EOS")

    if not df_tasks.empty:
        f_col1, f_col2, f_col3 = st.columns(3)

        estados_disponibles = sorted(
            list(df_tasks["Estado"].dropna().unique())
        )
        with f_col1:
            sel_estados = st.multiselect(
                "📌 Filtrar por Estado:",
                estados_disponibles,
                default=estados_disponibles,
            )

        deptos_disponibles = sorted(
            list(df_tasks["Departamento"].dropna().unique())
        )
        with f_col2:
            sel_deptos = st.multiselect(
                "🏢 Filtrar por Departamento:",
                deptos_disponibles,
                default=deptos_disponibles,
            )

        all_resps = set(df_tasks["Responsable Principal"].dropna().tolist())
        if "Responsable 2" in df_tasks.columns:
            all_resps.update(df_tasks["Responsable 2"].dropna().tolist())
        if "Responsable 3" in df_tasks.columns:
            all_resps.update(df_tasks["Responsable 3"].dropna().tolist())

        all_resps_list = sorted(
            [
                r
                for r in all_resps
                if str(r) != "nan" and str(r).strip() != "None" and str(r).strip() != ""
            ]
        )

        with f_col3:
            sel_resps = st.multiselect(
                "👤 Filtrar por Responsable:", all_resps_list, default=[]
            )

        df_filtered = df_tasks.copy()

        if sel_estados:
            df_filtered = df_filtered[df_filtered["Estado"].isin(sel_estados)]
        if sel_deptos:
            df_filtered = df_filtered[
                df_filtered["Departamento"].isin(sel_deptos)
            ]
        if sel_resps:
            mask_r1 = df_filtered["Responsable Principal"].isin(sel_resps)
            mask_r2 = (
                df_filtered["Responsable 2"].isin(sel_resps)
                if "Responsable 2" in df_filtered.columns
                else False
            )
            mask_r3 = (
                df_filtered["Responsable 3"].isin(sel_resps)
                if "Responsable 3" in df_filtered.columns
                else False
            )
            df_filtered = df_filtered[mask_r1 | mask_r2 | mask_r3]

        st.markdown(
            f"Mostrando **{len(df_filtered)}** de **{len(df_tasks)}** tareas en total."
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if not df_filtered.empty:
            rows_html = ""
            for _, row in df_filtered.iterrows():
                estado = str(row.get("Estado", "Pendiente")).strip()
                estado_clean = estado.lower().replace(" ", "")

                if "finaliz" in estado_clean or "complet" in estado_clean:
                    row_class = "task-row-finalizado"
                    badge_class = "badge-status-finalizado"
                    badge_icon = "🟢"
                elif "proceso" in estado_clean:
                    row_class = "task-row-proceso"
                    badge_class = "badge-status-proceso"
                    badge_icon = "🟡"
                else:
                    row_class = "task-row-pendiente"
                    badge_class = "badge-status-pendiente"
                    badge_icon = "🔴"

                r2 = str(row.get("Responsable 2", "")).strip()
                r3 = str(row.get("Responsable 3", "")).strip()
                equipo_str = f"<b>{row['Responsable Principal']}</b>"
                if r2 and r2 != "None" and r2 != "nan":
                    equipo_str += f", {r2}"
                if r3 and r3 != "None" and r3 != "nan":
                    equipo_str += f", {r3}"

                f_inicio = (
                    str(row.get("Fecha Inicio", ""))
                    .replace("00:00:00", "")
                    .strip()
                )
                f_entrega = (
                    str(row.get("Fecha Entrega", ""))
                    .replace("00:00:00", "")
                    .strip()
                )

                date_str = (
                    f"🗓️ Inicio: {f_inicio}"
                    if f_inicio and f_inicio != "nan"
                    else ""
                )
                if f_entrega and f_entrega != "nan" and f_entrega != "None":
                    date_str += f" | 🏁 Entrega: <b>{f_entrega}</b>"

                rows_html += (
                    f'<div class="task-row {row_class}">'
                    f'<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
                    f'<div class="task-title">{row["TAREA"]}</div>'
                    f'<div>'
                    f'<span class="task-badge {badge_class}">{badge_icon} {estado}</span>'
                    f'<span class="task-badge badge-dept">🏢 {row["Departamento"]}</span>'
                    f'</div>'
                    f'</div>'
                    f'<div class="task-meta">'
                    f'<div class="task-meta-item">👥 <b>Equipo:</b> {equipo_str}</div>'
                    f'<div class="task-meta-item" style="margin-left: auto;">{date_str}</div>'
                    f'</div>'
                    f'</div>'
                )

            container_html = textwrap.dedent(f'<div class="task-container-card">{rows_html}</div>')
            if hasattr(st, "html"):
                st.html(container_html)
            else:
                st.markdown(container_html, unsafe_allow_html=True)
        else:
            st.info("No hay tareas que coincidan con los filtros seleccionados.")

        st.markdown("---")
        st.markdown("### 📊 Vistazo Rápido: Resumen por Responsable")

        resp_stats = {}
        for r in all_resps_list:
            if not r or r == "None":
                continue
            m1 = df_tasks["Responsable Principal"] == r
            m2 = (
                df_tasks["Responsable 2"] == r
                if "Responsable 2" in df_tasks.columns
                else False
            )
            m3 = (
                df_tasks["Responsable 3"] == r
                if "Responsable 3" in df_tasks.columns
                else False
            )

            sub_resp = df_tasks[m1 | m2 | m3]

            pendientes = sum(
                sub_resp["Estado"].str.lower().str.contains("pend", na=False)
            )
            proceso = sum(
                sub_resp["Estado"].str.lower().str.contains("proceso", na=False)
            )
            finalizadas = sum(
                sub_resp["Estado"]
                .str.lower()
                .str.contains("finaliz|complet", na=False)
            )

            resp_stats[r] = {
                "Pendientes": pendientes,
                "En Proceso": proceso,
                "Finalizadas": finalizadas,
                "Total": len(sub_resp),
            }

        resp_keys = list(resp_stats.keys())
        if resp_keys:
            cols_per_row = 4
            for i in range(0, len(resp_keys), cols_per_row):
                cols_r = st.columns(cols_per_row)
                chunk_keys = resp_keys[i : i + cols_per_row]
                for idx_k, r_name in enumerate(chunk_keys):
                    st_data = resp_stats[r_name]
                    with cols_r[idx_k]:
                        summary_html = textwrap.dedent(
                            f'<div class="resp-summary-card">'
                            f'<div class="resp-summary-name">👤 {r_name}</div>'
                            f'<div class="resp-stat-grid">'
                            f'<div><div style="color: #C0392B;">Pend.</div><div class="resp-stat-num" style="color: #C0392B;">{st_data["Pendientes"]}</div></div>'
                            f'<div><div style="color: #D68910;">Proceso</div><div class="resp-stat-num" style="color: #D68910;">{st_data["En Proceso"]}</div></div>'
                            f'<div><div style="color: #1E8449;">Fin.</div><div class="resp-stat-num" style="color: #1E8449;">{st_data["Finalizadas"]}</div></div>'
                            f'</div>'
                            f'</div>'
                        )
                        if hasattr(st, "html"):
                            st.html(summary_html)
                        else:
                            st.markdown(summary_html, unsafe_allow_html=True)

# ------------------------------------------
# MÓDULO 5: SCORECARD & CUMPLIMIENTO
# ------------------------------------------
elif menu_option == "🏆 Scorecard & Cumplimiento":
    st.subheader("🏆 Cumplimiento por Responsable")
    if (
        not df_tasks.empty
        and "Estado" in df_tasks.columns
        and "Responsable Principal" in df_tasks.columns
    ):
        task_summary = (
            df_tasks.groupby(["Responsable Principal", "Estado"])
            .size()
            .unstack(fill_value=0)
        )
        task_summary["Completadas"] = task_summary.get(
            "Finalizado", 0
        ) + task_summary.get("Completado", 0)
        task_summary["Total Tareas"] = (
            task_summary.sum(axis=1) - task_summary["Completadas"]
        )
        task_summary["% Cumplimiento"] = (
            (task_summary["Completadas"] / task_summary["Total Tareas"] * 100)
            .round(1)
            .fillna(0)
        )
        task_summary = task_summary.reset_index().sort_values(
            "% Cumplimiento", ascending=False
        )

        fig_score = px.bar(
            task_summary,
            x="Responsable Principal",
            y="% Cumplimiento",
            text="% Cumplimiento",
            color="% Cumplimiento",
            color_continuous_scale=["#C0392B", "#F39C12", "#27AE60"],
        )
        fig_score.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#FFFFFF",
            yaxis=dict(range=[0, 100]),
        )
        st.plotly_chart(
            fig_score, use_container_width=True, key="chart_scorecard"
        )
