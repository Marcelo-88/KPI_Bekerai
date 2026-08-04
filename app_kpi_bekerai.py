import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Fridolin - KPI Bekerai 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

PASTEL_COLORS = [
    '#C0392B', '#2980B9', '#27AE60', '#D35400', '#8E44AD',
    '#16A085', '#F39C12', '#E74C3C', '#34495E', '#D4AC0D'
]

FRIDOLIN_CSS = """
<style>
    .stApp { background-color: #F7F4EE; color: #2D2B2A; }
    .main-header {
        background-color: #7A1C29; padding: 1.2rem; border-radius: 14px;
        color: #FFFFFF; text-align: center; margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(122, 28, 41, 0.15);
    }
    .main-header h1 { color: #FFFDF9 !important; margin: 0; font-size: 1.8rem; font-weight: 700; }
    .main-header p { color: #E6C894 !important; margin-top: 5px; margin-bottom: 0; font-size: 0.95rem; }
    section[data-testid="stSidebar"] { background-color: #EFECE4 !important; border-right: 1px solid #DFD9CE; }
    
    /* ESTILOS KPIS */
    .kpi-card {
        background-color: #FFFFFF; border: 1px solid #E6E1D7; border-radius: 16px;
        padding: 1.1rem; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04); margin-bottom: 1rem;
        min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;
    }
    .kpi-card-fallback {
        background-color: #FFFDF5; border: 2px dashed #E6A23C; border-radius: 16px;
        padding: 1.1rem; box-shadow: 0 4px 8px rgba(230, 162, 60, 0.12); margin-bottom: 1rem;
        min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;
    }
    .kpi-card-header { font-size: 0.82rem; font-weight: 700; color: #4A4644; text-transform: uppercase; height: 2.2rem; overflow: hidden; }
    .kpi-card-val { font-size: 1.65rem; font-weight: 800; color: #7A1C29; margin-bottom: 0.4rem; font-variant-numeric: tabular-nums; }
    .kpi-card-footer { font-size: 0.78rem; border-top: 1px solid #F0ECE3; padding-top: 0.5rem; display: flex; flex-direction: column; gap: 0.2rem; }
    .badge-up { color: #27AE60; font-weight: 600; }
    .badge-down { color: #C0392B; font-weight: 600; }
    .badge-neutral { color: #7F8C8D; font-weight: 500; }
    .badge-warning { color: #D35400; font-weight: 700; background: #FDEBD0; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; }
    .kpi-resp-tag { font-size: 0.75rem; color: #A07828; font-weight: 600; margin-bottom: 0.3rem; }
    .compare-card-title { font-size: 1.05rem; font-weight: 700; color: #7A1C29; margin-bottom: 0.5rem; }

    /* CONTENEDOR ÚNICO PARA TAREAS */
    .task-container-card {
        background-color: #FFFFFF;
        border: 1px solid #E2DCD2;
        border-radius: 16px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        margin-bottom: 2rem;
    }

    /* FILAS DE TAREAS DENTRO DEL CONTENEDOR ÚNICO */
    .task-row {
        padding: 1rem 0.5rem;
        border-bottom: 1px solid #F0ECE3;
        border-left: 5px solid transparent;
        border-radius: 4px;
        margin-bottom: 0.2rem;
    }
    .task-row:last-child {
        border-bottom: none;
    }
    .task-row-pendiente { border-left-color: #E74C3C; }
    .task-row-proceso { border-left-color: #F39C12; }
    .task-row-finalizado { border-left-color: #27AE60; }
    
    .task-title { font-size: 0.98rem; font-weight: 700; color: #2D2B2A; margin-bottom: 0.4rem; padding-left: 0.4rem; }
    .task-badge {
        display: inline-block; padding: 3px 9px; border-radius: 12px; font-size: 0.75rem;
        font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .badge-status-pendiente { background-color: #FDEDEC; color: #C0392B; }
    .badge-status-proceso { background-color: #FEF9E7; color: #D68910; }
    .badge-status-finalizado { background-color: #E8F8F5; color: #1E8449; }
    .badge-dept { background-color: #EAECEE; color: #424949; font-weight: 600; margin-left: 6px; }

    .task-meta { font-size: 0.83rem; color: #5D6D7E; margin-top: 0.4rem; padding-left: 0.4rem; display: flex; flex-wrap: wrap; gap: 12px; }
    .task-meta-item { display: flex; align-items: center; gap: 4px; }
    
    /* TARJETA RESUMEN RESPONSABLE */
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
# 2. CARGA Y PARSEO DE DATOS DE GOOGLE SHEETS
# ==========================================
GOOGLE_SHEET_ID = "1YmxMIgdqn0Oe38mmUF3pFBVyWgUjyyxjmDdmWp-Oz1g"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=xlsx"

def parse_custom_number(val):
    if pd.isna(val) or val == "" or str(val).strip() == "":
        return None
    val_str = str(val).strip()
    if any(err in val_str for err in ['#¡DIV/0!', '#DIV/0!', '#N/A', '#REF!', '#VALUE!']):
        return None
        
    is_percent = '%' in val_str
    cleaned = re.sub(r'[^0-9,\.\-]', '', val_str)
    if not cleaned:
        return None
        
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
        
    try:
        num = float(cleaned)
        return (num / 100.0) if is_percent else num
    except ValueError:
        return None

@st.cache_data(ttl=60)
def load_data():
    sheets = pd.read_excel(EXCEL_URL, sheet_name=None, header=None)
    
    # 1. PARSER PESTAÑA KPI
    df_kpi_raw = sheets.get('KPI', pd.DataFrame())
    if not df_kpi_raw.empty:
        header_idx = None
        for idx, row in df_kpi_raw.iterrows():
            row_vals = [str(val).strip() for val in row.values]
            if any(h in row_vals for h in ['Medibles', 'Medible', 'Quien', 'Responsable']):
                header_idx = idx
                break
        
        if header_idx is not None:
            df_kpi_clean = df_kpi_raw.iloc[header_idx + 1:].copy()
            df_kpi_clean.columns = [str(c).strip() for c in df_kpi_raw.iloc[header_idx].values]
            df_kpi_clean = df_kpi_clean.dropna(how='all')
            
            id_cols = [c for c in df_kpi_clean.columns if c in ['Quien', 'Responsable', 'Departamento', 'Medibles', 'Medible']]
            val_cols = [c for c in df_kpi_clean.columns if c not in id_cols and not str(c).startswith('Unnamed') and str(c) != 'nan']
            
            df_kpi_long = pd.melt(
                df_kpi_clean, 
                id_vars=id_cols, 
                value_vars=val_cols, 
                var_name='Semana', 
                value_name='Valor'
            )
            
            df_kpi_long['Valor'] = df_kpi_long['Valor'].apply(parse_custom_number)
            df_kpi_long.rename(columns={'Quien': 'Responsable', 'Medibles': 'Medible'}, inplace=True)
            df_kpi_long = df_kpi_long[df_kpi_long['Medible'].notna() & (df_kpi_long['Medible'] != 'nan')]
            df_kpi_long['Medible'] = df_kpi_long['Medible'].astype(str).str.strip()
            
            mask_swap = (df_kpi_long['Medible'] == 'Envio Salados') & (df_kpi_long['Valor'] > 20000)
            if mask_swap.any():
                df_kpi_long.loc[mask_swap, 'Medible'] = 'Prod Salado'

        else:
            df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])
    else:
        df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])

    # 2. PARSER PESTAÑA TAREAS
    df_tareas_raw = sheets.get('Tareas', pd.DataFrame())
    if not df_tareas_raw.empty:
        h_idx_t = None
        for idx, row in df_tareas_raw.iterrows():
            row_vals = [str(val).strip() for val in row.values]
            if any(h in row_vals for h in ['TAREA', 'Tarea', 'Responsable Principal', 'Estado']):
                h_idx_t = idx
                break
        
        if h_idx_t is not None:
            df_tasks = df_tareas_raw.iloc[h_idx_t + 1:].copy()
            df_tasks.columns = [str(c).strip() for c in df_tareas_raw.iloc[h_idx_t].values]
            df_tasks = df_tasks.dropna(how='all')
            
            df_tasks['TAREA'] = df_tasks['TAREA'].astype(str).str.strip()
            df_tasks = df_tasks[df_tasks['TAREA'].notna() & (df_tasks['TAREA'] != 'nan') & (df_tasks['TAREA'] != '')]
            
            df_tasks['Estado'] = df_tasks['Estado'].fillna('Pendiente').astype(str).str.strip()
            df_tasks['Responsable Principal'] = df_tasks['Responsable Principal'].fillna('Sin Asignar').astype(str).str.strip()
            df_tasks['Departamento'] = df_tasks['Departamento'].fillna('General').astype(str).str.strip()
        else:
            df_tasks = df_tareas_raw
    else:
        df_tasks = pd.DataFrame()

    return df_kpi_long, df_tasks

# ==========================================
# 3. HELPER DE GRÁFICAS CON DOBLE EJE Y
# ==========================================
def render_multi_kpi_chart(df_kpis, kpi_list, title="Comparativa Multi-KPI", height=420, unit_label="Valores"):
    existing_kpis = [k for k in kpi_list if k in df_kpis['Medible'].values]
    
    if not existing_kpis:
        fig = go.Figure()
        fig.add_annotation(
            text="Selecciona al menos una categoría para visualizar",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#7A1C29")
        )
        fig.update_layout(height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF')
        return fig

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for idx, kpi in enumerate(existing_kpis):
        sub_df = df_kpis[(df_kpis['Medible'] == kpi) & (df_kpis['Valor'].notna())].copy()
        
        if sub_df.empty:
            continue
            
        color = PASTEL_COLORS[idx % len(PASTEL_COLORS)]
        is_money = "Bs" in unit_label or any(m in kpi.upper() for m in ['VENTAS', 'PAGO', 'C X P', 'EFECTIVO'])
        val_prefix = "Bs " if is_money else ""
        
        max_val = sub_df['Valor'].max()
        use_secondary = (max_val > 15000 and "Bs" not in unit_label)

        hover_template = (
            f"<b>{kpi}</b><br>"
            "🗓️ %{x}<br>"
            f"📊 Valor: <b>{val_prefix}%{{y:,.2f}}</b>"
            "<extra></extra>"
        )
        
        fig.add_trace(
            go.Scatter(
                x=sub_df['Semana'],
                y=sub_df['Valor'],
                name=f"{kpi} (Eje Der.)" if use_secondary else str(kpi),
                mode='lines+markers',
                line=dict(color=color, width=3),
                marker=dict(size=7, color=color, symbol='circle'),
                hovertemplate=hover_template,
                connectgaps=False
            ),
            secondary_y=use_secondary
        )
        
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=15, color="#7A1C29"), x=0, y=0.98),
        xaxis=dict(title=None, tickangle=-45, showgrid=True, gridcolor="#EFECE6"),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
        height=height, hovermode="closest",
        legend=dict(orientation="h", yanchor="top", y=-0.28, xanchor="center", x=0.5, bgcolor="rgba(255,255,255,0.85)", bordercolor="#DFD9CE", borderwidth=1),
        margin=dict(l=55, r=55, t=50, b=110)
    )

    fig.update_yaxes(title_text=unit_label, showgrid=True, gridcolor="#EFECE6", tickformat=",.0f", secondary_y=False)
    fig.update_yaxes(title_text=f"{unit_label} (Volumen Alto)", showgrid=False, tickformat=",.0f", secondary_y=True)

    return fig

if hasattr(st, "dialog"):
    @st.dialog("🔍 Vista Ampliada del Gráfico", width="large")
    def show_full_graph_dialog(df, kpi_list, title, unit_label="Valores"):
        fig = render_multi_kpi_chart(df, kpi_list, title=title, height=600, unit_label=unit_label)
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
        "📝 Gestión de Tareas", 
        "🏆 Scorecard & Cumplimiento",
        "🔍 Explorador Sheet (Debug)"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Datos Ahora", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("¡Datos actualizados!")

try:
    df_kpis, df_tasks = load_data()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    st.stop()

# Header Superior
st.markdown("""
<div class="main-header">
    <h1>FRIDOLIN - TABLERO CONTROL EOS & KPIs</h1>
    <p>Monitoreo Semanal de Indicadores, Tareas y Cumplimiento Bekerai 2026</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. MÓDULOS DE LA APLICACIÓN
# ==========================================

# ------------------------------------------
# MÓDULO 1: DASHBOARDS KPIS
# ------------------------------------------
if menu_option == "📊 Dashboards KPIs":
    st.subheader("📌 Resumen de Indicadores Semanales")
    
    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        semanas_unicas = list(df_kpis['Semana'].unique())
        
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            selected_week = st.selectbox(
                "Seleccionar Semana a Inspeccionar:", 
                semanas_unicas, 
                index=len(semanas_unicas) - 1
            )
            
        responsables = ["Todos"] + sorted([str(r) for r in df_kpis['Responsable'].dropna().unique() if str(r) != 'nan'])
        with col_f2:
            selected_resp = st.selectbox("Filtrar tarjetas por Responsable:", responsables)

        current_week_idx = semanas_unicas.index(selected_week)
        df_all_selected = df_kpis.copy()
        if selected_resp != "Todos":
            df_all_selected = df_all_selected[df_all_selected['Responsable'] == selected_resp]
            
        metrics_list = df_all_selected['Medible'].unique()
        
        st.markdown(f"##### Datos correspondientes a **{selected_week}**")
        
        if len(metrics_list) > 0:
            cols = st.columns(4)
            for idx, kpi in enumerate(metrics_list):
                df_kpi_series = df_kpis[df_kpis['Medible'] == kpi]
                resp = df_kpi_series['Responsable'].dropna().values[0] if not df_kpi_series.empty else "-"
                
                val_curr = 0.0
                actual_data_week = selected_week
                is_fallback = False
                
                for w_idx in range(current_week_idx, -1, -1):
                    w_name = semanas_unicas[w_idx]
                    row_w = df_kpi_series[df_kpi_series['Semana'] == w_name]
                    if not row_w.empty and pd.notna(row_w['Valor'].values[0]):
                        v = float(row_w['Valor'].values[0])
                        val_curr = v
                        actual_data_week = w_name
                        if w_idx < current_week_idx:
                            is_fallback = True
                        break
                            
                val_prev = None
                prev_w_name = ""
                actual_week_idx_found = semanas_unicas.index(actual_data_week) if actual_data_week in semanas_unicas else -1
                if actual_week_idx_found > 0:
                    prev_w_name = semanas_unicas[actual_week_idx_found - 1]
                    row_prev = df_kpi_series[df_kpi_series['Semana'] == prev_w_name]
                    if not row_prev.empty and pd.notna(row_prev['Valor'].values[0]):
                        val_prev = float(row_prev['Valor'].values[0])
                
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
                    
                valid_vals = df_kpi_series[df_kpi_series['Valor'].notna()]['Valor']
                avg_total = valid_vals.mean() if not valid_vals.empty else 0.0
                
                if avg_total > 0 and val_curr != 0:
                    pct_avg = ((val_curr - avg_total) / avg_total) * 100
                    if pct_avg > 0:
                        var_avg_html = f'<span class="badge-up">▲ +{pct_avg:.1f}%</span> vs prom ({avg_total:,.0f})'
                    elif pct_avg < 0:
                        var_avg_html = f'<span class="badge-down">▼ {pct_avg:.1f}%</span> vs prom ({avg_total:,.0f})'
                    else:
                        var_avg_html = f'<span class="badge-neutral">= prom ({avg_total:,.0f})</span>'
                else:
                    var_avg_html = '<span class="badge-neutral">-- N/A vs prom</span>'
                
                is_money = any(m in kpi.upper() for m in ['VENTAS', 'PAGO', 'C X P', 'EFECTIVO', 'COMPRAS', 'VALOR', 'PRECIO'])
                prefix = "Bs " if is_money else ""
                val_formatted = f"{prefix}{val_curr:,.0f}" if (val_curr >= 100 or val_curr % 1 == 0) else f"{prefix}{val_curr:,.2f}"
                
                card_class = "kpi-card-fallback" if is_fallback else "kpi-card"
                fallback_tag = f'<div style="margin-bottom:0.3rem;"><span class="badge-warning">⚠️ DATO DE {actual_data_week}</span></div>' if is_fallback else ""
                
                html_code = (
                    f'<div class="{card_class}">'
                    f'<div>'
                    f'<div class="kpi-card-header">{kpi}</div>'
                    f'<div class="kpi-resp-tag">👤 Resp: {resp}</div>'
                    f'{fallback_tag}'
                    f'<div class="kpi-card-val">{val_formatted}</div>'
                    f'</div>'
                    f'<div class="kpi-card-footer">'
                    f'<div>{var_prev_html}</div>'
                    f'<div>{var_avg_html}</div>'
                    f'</div>'
                    f'</div>'
                )
                
                with cols[idx % 4]:
                    st.markdown(html_code, unsafe_allow_html=True)

# ------------------------------------------
# MÓDULO 2: COMPARADOR KPI vs KPI
# ------------------------------------------
elif menu_option == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Análisis Comparativo Multi-KPI")

    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        all_kpis_in_db = list(df_kpis['Medible'].unique())
        
        def find_kpis_exact_or_keyword(category_list):
            matched = []
            for k in all_kpis_in_db:
                k_upper = str(k).upper()
                for cat in category_list:
                    cat_upper = cat.upper()
                    if cat_upper in k_upper or (cat_upper == "TORTAS" and "TORTA" in k_upper) or (cat_upper == "SALADOS" and "SALADO" in k_upper):
                        matched.append(k)
                        break
            return list(set(matched))

        kpi_g1 = [k for k in all_kpis_in_db if any(kw in k.upper() for kw in ["VENTAS", "PAGOS PROVEEDORES MP", "TOTAL C X P", "BALANCE EFECTIVO"])]
        kpi_g3 = [k for k in all_kpis_in_db if any(kw in k.upper() for kw in ["INVERSION RRSS", "PAGO PROVEEDORES MARKETING", "VENTAS"])]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="compare-card-title">💵 1. Ventas vs Pagos vs CxP vs Efectivo (Bs)</div>', unsafe_allow_html=True)
            fig1 = render_multi_kpi_chart(df_kpis, kpi_g1, title="Finanzas & Flujo de Caja", height=380, unit_label="Monto en Bs")
            st.plotly_chart(fig1, use_container_width=True, key="card_1_main")
            if st.button("🔍 Maximizar Gráfico 1", key="btn_max_1", use_container_width=True):
                show_full_graph_dialog(df_kpis, kpi_g1, "Finanzas & Flujo de Caja", unit_label="Monto en Bs")

        with c2:
            st.markdown('<div class="compare-card-title">🍰 2. Producción, Envíos y Bajas por Categoría</div>', unsafe_allow_html=True)
            categorias_bekerai = ["Salados", "Tortas", "Pasteles Individuales", "Postres Enteros", "Panaderia"]
            selected_cats = st.multiselect("Filtrar Categorías:", categorias_bekerai, default=["Salados", "Tortas"])

            kpi_g2 = find_kpis_exact_or_keyword(selected_cats) if selected_cats else []
            fig2 = render_multi_kpi_chart(df_kpis, kpi_g2, title="Flujo de Categorías Seleccionadas", height=380, unit_label="Unidades")
            st.plotly_chart(fig2, use_container_width=True, key="card_2_main")
            if st.button("🔍 Maximizar Gráfico 2", key="btn_max_2", use_container_width=True):
                show_full_graph_dialog(df_kpis, kpi_g2, "Flujo de Categorías Seleccionadas", unit_label="Unidades")

        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown('<div class="compare-card-title">📣 3. Inversión Marketing vs Ventas (Bs)</div>', unsafe_allow_html=True)
            fig3 = render_multi_kpi_chart(df_kpis, kpi_g3, title="Marketing & Retorno", height=380, unit_label="Monto en Bs")
            st.plotly_chart(fig3, use_container_width=True, key="card_3_main")
            if st.button("🔍 Maximizar Gráfico 3", key="btn_max_3", use_container_width=True):
                show_full_graph_dialog(df_kpis, kpi_g3, "Marketing & Retorno", unit_label="Monto en Bs")

        with c4:
            st.markdown('<div class="compare-card-title">🛠️ 4. Comparador Libre</div>', unsafe_allow_html=True)
            selected_custom = st.multiselect("Selecciona cualquier conjunto de KPIs:", all_kpis_in_db, default=all_kpis_in_db[:2] if len(all_kpis_in_db) >= 2 else all_kpis_in_db)
            if selected_custom:
                fig4 = render_multi_kpi_chart(df_kpis, selected_custom, title="Selección Libre Personalizada", height=350, unit_label="Valores")
                st.plotly_chart(fig4, use_container_width=True, key="card_4_main")
                if st.button("🔍 Maximizar Gráfico 4", key="btn_max_4", use_container_width=True):
                    show_full_graph_dialog(df_kpis, selected_custom, "Selección Libre Personalizada", unit_label="Valores")

# ------------------------------------------
# MÓDULO 3: GESTIÓN DE TAREAS (CONTENEDOR ÚNICO)
# ------------------------------------------
elif menu_option == "📝 Gestión de Tareas":
    st.subheader("📝 Lista de Tareas Operativas EOS")
    
    if not df_tasks.empty:
        # --- FILTROS ---
        f_col1, f_col2, f_col3 = st.columns(3)
        
        estados_disponibles = sorted(list(df_tasks['Estado'].dropna().unique()))
        with f_col1:
            sel_estados = st.multiselect("📌 Filtrar por Estado:", estados_disponibles, default=estados_disponibles)
            
        deptos_disponibles = sorted(list(df_tasks['Departamento'].dropna().unique()))
        with f_col2:
            sel_deptos = st.multiselect("🏢 Filtrar por Departamento:", deptos_disponibles, default=deptos_disponibles)
            
        all_resps = set(df_tasks['Responsable Principal'].dropna().tolist())
        if 'Responsable 2' in df_tasks.columns:
            all_resps.update(df_tasks['Responsable 2'].dropna().tolist())
        if 'Responsable 3' in df_tasks.columns:
            all_resps.update(df_tasks['Responsable 3'].dropna().tolist())
        
        all_resps_list = sorted([r for r in all_resps if str(r) != 'nan' and str(r).strip() != 'None' and str(r).strip() != ''])
        
        with f_col3:
            sel_resps = st.multiselect("👤 Filtrar por Responsable:", all_resps_list, default=[])

        # --- APLICACIÓN DE FILTROS ---
        df_filtered = df_tasks.copy()
        
        if sel_estados:
            df_filtered = df_filtered[df_filtered['Estado'].isin(sel_estados)]
        if sel_deptos:
            df_filtered = df_filtered[df_filtered['Departamento'].isin(sel_deptos)]
        if sel_resps:
            mask_r1 = df_filtered['Responsable Principal'].isin(sel_resps)
            mask_r2 = df_filtered['Responsable 2'].isin(sel_resps) if 'Responsable 2' in df_filtered.columns else False
            mask_r3 = df_filtered['Responsable 3'].isin(sel_resps) if 'Responsable 3' in df_filtered.columns else False
            df_filtered = df_filtered[mask_r1 | mask_r2 | mask_r3]

        st.markdown(f"Mostrando **{len(df_filtered)}** de **{len(df_tasks)}** tareas en total.")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- RENDERIZADO EN TARJETA/CONTENEDOR ÚNICO ---
        if not df_filtered.empty:
            rows_html = ""
            for _, row in df_filtered.iterrows():
                estado = str(row.get('Estado', 'Pendiente')).strip()
                estado_clean = estado.lower().replace(' ', '')
                
                if 'finaliz' in estado_clean or 'complet' in estado_clean:
                    row_class = "task-row-finalizado"
                    badge_class = "badge-status-finalizado"
                    badge_icon = "🟢"
                elif 'proceso' in estado_clean:
                    row_class = "task-row-proceso"
                    badge_class = "badge-status-proceso"
                    badge_icon = "🟡"
                else:
                    row_class = "task-row-pendiente"
                    badge_class = "badge-status-pendiente"
                    badge_icon = "🔴"

                r2 = str(row.get('Responsable 2', '')).strip()
                r3 = str(row.get('Responsable 3', '')).strip()
                equipo_str = f"<b>{row['Responsable Principal']}</b>"
                if r2 and r2 != 'None' and r2 != 'nan':
                    equipo_str += f", {r2}"
                if r3 and r3 != 'None' and r3 != 'nan':
                    equipo_str += f", {r3}"

                f_inicio = str(row.get('Fecha Inicio', '')).replace('00:00:00', '').strip()
                f_entrega = str(row.get('Fecha Entrega', '')).replace('00:00:00', '').strip()
                
                date_str = f"🗓️ Inicio: {f_inicio}" if f_inicio and f_inicio != 'nan' else ""
                if f_entrega and f_entrega != 'nan' and f_entrega != 'None':
                    date_str += f" | 🏁 Entrega: <b>{f_entrega}</b>"

                rows_html += f"""<div class="task-row {row_class}">
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<div class="task-title">{row['TAREA']}</div>
<div>
<span class="task-badge {badge_class}">{badge_icon} {estado}</span>
<span class="task-badge badge-dept">🏢 {row['Departamento']}</span>
</div>
</div>
<div class="task-meta">
<div class="task-meta-item">👥 <b>Equipo:</b> {equipo_str}</div>
<div class="task-meta-item" style="margin-left: auto;">{date_str}</div>
</div>
</div>"""

            container_html = f'<div class="task-container-card">{rows_html}</div>'
            st.markdown(container_html, unsafe_allow_html=True)
        else:
            st.info("No hay tareas que coincidan con los filtros seleccionados.")

        # --- SECCIÓN RESUMEN RÁPIDO POR RESPONSABLE (BOTTOM) ---
        st.markdown("---")
        st.markdown("### 📊 Vistazo Rápido: Resumen por Responsable")
        
        resp_stats = {}
        for r in all_resps_list:
            if not r or r == 'None':
                continue
            m1 = df_tasks['Responsable Principal'] == r
            m2 = df_tasks['Responsable 2'] == r if 'Responsable 2' in df_tasks.columns else False
            m3 = df_tasks['Responsable 3'] == r if 'Responsable 3' in df_tasks.columns else False
            
            sub_resp = df_tasks[m1 | m2 | m3]
            
            pendientes = sum(sub_resp['Estado'].str.lower().str.contains('pend', na=False))
            proceso = sum(sub_resp['Estado'].str.lower().str.contains('proceso', na=False))
            finalizadas = sum(sub_resp['Estado'].str.lower().str.contains('finaliz|complet', na=False))
            
            resp_stats[r] = {
                'Pendientes': pendientes,
                'En Proceso': proceso,
                'Finalizadas': finalizadas,
                'Total': len(sub_resp)
            }

        resp_keys = list(resp_stats.keys())
        if resp_keys:
            cols_per_row = 4
            for i in range(0, len(resp_keys), cols_per_row):
                cols_r = st.columns(cols_per_row)
                chunk_keys = resp_keys[i:i + cols_per_row]
                for idx_k, r_name in enumerate(chunk_keys):
                    st_data = resp_stats[r_name]
                    with cols_r[idx_k]:
                        summary_html = f"""<div class="resp-summary-card">
<div class="resp-summary-name">👤 {r_name}</div>
<div class="resp-stat-grid">
<div>
<div style="color: #C0392B;">Pend.</div>
<div class="resp-stat-num" style="color: #C0392B;">{st_data['Pendientes']}</div>
</div>
<div>
<div style="color: #D68910;">Proceso</div>
<div class="resp-stat-num" style="color: #D68910;">{st_data['En Proceso']}</div>
</div>
<div>
<div style="color: #1E8449;">Fin.</div>
<div class="resp-stat-num" style="color: #1E8449;">{st_data['Finalizadas']}</div>
</div>
</div>
</div>"""
                        st.markdown(summary_html, unsafe_allow_html=True)

# ------------------------------------------
# MÓDULO 4: SCORECARD & CUMPLIMIENTO
# ------------------------------------------
elif menu_option == "🏆 Scorecard & Cumplimiento":
    st.subheader("🏆 Cumplimiento por Responsable")
    if not df_tasks.empty and 'Estado' in df_tasks.columns and 'Responsable Principal' in df_tasks.columns:
        task_summary = df_tasks.groupby(['Responsable Principal', 'Estado']).size().unstack(fill_value=0)
        task_summary['Completadas'] = task_summary.get('Finalizado', 0) + task_summary.get('Completado', 0)
        task_summary['Total Tareas'] = task_summary.sum(axis=1) - task_summary['Completadas']
        task_summary['% Cumplimiento'] = (task_summary['Completadas'] / task_summary['Total Tareas'] * 100).round(1).fillna(0)
        task_summary = task_summary.reset_index().sort_values('% Cumplimiento', ascending=False)
        
        fig_score = px.bar(
            task_summary, x='Responsable Principal', y='% Cumplimiento', text='% Cumplimiento',
            color='% Cumplimiento', color_continuous_scale=['#C0392B', '#F39C12', '#27AE60']
        )
        fig_score.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF', yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_score, use_container_width=True, key="chart_scorecard")

# ------------------------------------------
# MÓDULO 5: EXPLORADOR SHEET
# ------------------------------------------
elif menu_option == "🔍 Explorador Sheet (Debug)":
    st.subheader("🔍 Previsualización Directa de Datos Procesados")
    st.dataframe(df_kpis, use_container_width=True)
