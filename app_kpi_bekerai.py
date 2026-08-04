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
    
    /* ESTILOS KPIS COMPACTOS */
    .kpi-card {
        background-color: #FFFFFF; border: 1px solid #E6E1D7; border-radius: 12px;
        padding: 0.7rem 0.9rem; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04); margin-bottom: 0.75rem;
        min-height: 145px; display: flex; flex-direction: column; justify-content: space-between;
    }
    .kpi-card-fallback {
        background-color: #FFFDF5; border: 2px dashed #E6A23C; border-radius: 12px;
        padding: 0.7rem 0.9rem; box-shadow: 0 2px 5px rgba(230, 162, 60, 0.12); margin-bottom: 0.75rem;
        min-height: 145px; display: flex; flex-direction: column; justify-content: space-between;
    }
    .kpi-card-header { font-size: 0.85rem; font-weight: 700; color: #4A4644; text-transform: uppercase; line-height: 1.2; margin-bottom: 0.2rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .kpi-card-val { font-size: 1.6rem; font-weight: 800; color: #7A1C29; margin: 0.2rem 0; font-variant-numeric: tabular-nums; line-height: 1.1; }
    .kpi-card-footer { font-size: 0.75rem; border-top: 1px solid #F0ECE3; padding-top: 0.3rem; margin-top: 0.3rem; display: flex; flex-direction: column; gap: 0.1rem; }
    .badge-up { color: #27AE60; font-weight: 600; }
    .badge-down { color: #C0392B; font-weight: 600; }
    .badge-neutral { color: #7F8C8D; font-weight: 500; }
    .badge-warning { color: #D35400; font-weight: 700; background: #FDEBD0; padding: 1px 5px; border-radius: 4px; font-size: 0.68rem; display: inline-block; }
    .kpi-resp-tag { font-size: 0.75rem; color: #A07828; font-weight: 600; margin-bottom: 0.1rem; }
    .compare-card-title { font-size: 1.05rem; font-weight: 700; color: #7A1C29; margin-bottom: 0.5rem; }

    /* CONTENEDOR TAREAS */
    .task-container-card {
        background-color: #FFFFFF; border: 1px solid #E2DCD2; border-radius: 16px;
        padding: 1rem 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 2rem;
    }
    .task-row {
        padding: 0.8rem 0.5rem; border-bottom: 1px solid #F0ECE3;
        border-left: 5px solid transparent; border-radius: 4px; margin-bottom: 0.2rem;
    }
    .task-row:last-child { border-bottom: none; }
    .task-row-pendiente { border-left-color: #E74C3C; }
    .task-row-proceso { border-left-color: #F39C12; }
    .task-row-finalizado { border-left-color: #27AE60; }
    
    .task-title { font-size: 0.95rem; font-weight: 700; color: #2D2B2A; margin-bottom: 0.3rem; padding-left: 0.4rem; }
    .task-badge {
        display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem;
        font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .badge-status-pendiente { background-color: #FDEDEC; color: #C0392B; }
    .badge-status-proceso { background-color: #FEF9E7; color: #D68910; }
    .badge-status-finalizado { background-color: #E8F8F5; color: #1E8449; }
    .badge-dept { background-color: #EAECEE; color: #424949; font-weight: 600; margin-left: 6px; }

    .task-meta { font-size: 0.82rem; color: #5D6D7E; margin-top: 0.3rem; padding-left: 0.4rem; display: flex; flex-wrap: wrap; gap: 12px; }
    .task-meta-item { display: flex; align-items: center; gap: 4px; }
</style>
"""

st.markdown(FRIDOLIN_CSS, unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y PARSEO PRECISO DE GOOGLE SHEETS
# ==========================================
GOOGLE_SHEET_ID = "1YmxMIgdqn0Oe38mmUF3pFBVyWgUjyyxjmDdmWp-Oz1g"
ONLINE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit"

URL_KPI_CSV = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=KPI"
URL_TAREAS_CSV = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Tareas"

def parse_custom_number(val):
    """
    Convierte valores con formato de texto (ej: Bs1.134.072,00 o 1.152.035) a flotantes puros.
    """
    if pd.isna(val) or val == "" or str(val).strip() == "":
        return None
    val_str = str(val).strip()
    if any(err in val_str for err in ['#¡DIV/0!', '#DIV/0!', '#N/A', '#REF!', '#VALUE!']):
        return None
        
    is_percent = '%' in val_str
    
    # Eliminar moneda "Bs" u otros caracteres no numéricos
    cleaned = re.sub(r'[^0-9,\.\-]', '', val_str)
    if not cleaned:
        return None
        
    # Manejar formato numérico Latino/Boliviano (Punto en miles, Coma en decimales)
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif '.' in cleaned and ',' not in cleaned:
        # Verificar si el punto actúa como separador de miles (ej: 1.152.035 o 47.185)
        parts = cleaned.split('.')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            cleaned = cleaned.replace('.', '')
    elif ',' in cleaned and '.' not in cleaned:
        cleaned = cleaned.replace(',', '.')
        
    try:
        num = float(cleaned)
        return (num / 100.0) if is_percent else num
    except ValueError:
        return None

@st.cache_data(ttl=30)
def load_data():
    # 1. PARSER PESTAÑA KPI
    try:
        df_kpi_raw = pd.read_csv(URL_KPI_CSV, header=None)
    except Exception:
        df_kpi_raw = pd.DataFrame()
        
    if not df_kpi_raw.empty:
        # Buscar la fila de encabezados real que contiene 'QUIEN', 'DEPARTAMENTO', 'MEDIBLES' (Fila 3 de la hoja)
        header_idx = None
        for idx, row in df_kpi_raw.iterrows():
            row_vals = [str(val).strip().upper() for val in row.values]
            if 'QUIEN' in row_vals and 'MEDIBLES' in row_vals:
                header_idx = idx
                break
        
        if header_idx is not None:
            df_kpi_clean = df_kpi_raw.iloc[header_idx + 1:].copy()
            headers = [str(c).strip() for c in df_kpi_raw.iloc[header_idx].values]
            df_kpi_clean.columns = headers
            df_kpi_clean = df_kpi_clean.dropna(how='all')
            
            # Definir de forma explícita las columnas estáticas
            master_cols = ['Quien', 'Departamento', 'Medibles', 'Categoria']
            
            # Identificar qué columnas reales corresponden a Metadatos y cuáles a Semanas
            id_cols = [c for c in df_kpi_clean.columns if c in master_cols or str(c).strip().upper() in ['QUIEN', 'DEPARTAMENTO', 'MEDIBLES', 'CATEGORIA']]
            val_cols = [c for c in df_kpi_clean.columns if c not in id_cols and str(c).strip() != '' and not str(c).startswith('Unnamed')]
            
            # Despivoteo (Melt)
            df_kpi_long = pd.melt(
                df_kpi_clean, 
                id_vars=id_cols, 
                value_vars=val_cols, 
                var_name='Semana', 
                value_name='Valor'
            )
            
            # Formatear números
            df_kpi_long['Valor'] = df_kpi_long['Valor'].apply(parse_custom_number)
            
            # Estandarizar nombres de columnas
            rename_dict = {}
            for col in df_kpi_long.columns:
                c_upper = str(col).strip().upper()
                if c_upper == 'QUIEN': rename_dict[col] = 'Responsable'
                elif c_upper == 'MEDIBLES': rename_dict[col] = 'Medible'
                elif c_upper == 'DEPARTAMENTO': rename_dict[col] = 'Departamento'
                elif c_upper == 'CATEGORIA': rename_dict[col] = 'Categoria'
            
            df_kpi_long.rename(columns=rename_dict, inplace=True)
            
            # Generar nombre único para medibles con categoría (ej: "Bajas - Panaderia")
            if 'Categoria' in df_kpi_long.columns:
                def make_medible_full(row):
                    med = str(row.get('Medible', '')).strip()
                    cat = str(row.get('Categoria', '')).strip()
                    if cat and cat.lower() != 'nan' and cat != '':
                        return f"{med} - {cat}"
                    return med
                
                df_kpi_long['Medible_Original'] = df_kpi_long['Medible']
                df_kpi_long['Medible'] = df_kpi_long.apply(make_medible_full, axis=1)

            # Filtrar registros nulos
            df_kpi_long = df_kpi_long[df_kpi_long['Medible'].notna() & (df_kpi_long['Medible'] != 'nan') & (df_kpi_long['Medible'] != '')]
            df_kpi_long['Departamento'] = df_kpi_long['Departamento'].fillna('General').astype(str).str.strip()
            df_kpi_long['Responsable'] = df_kpi_long['Responsable'].fillna('Sin Asignar').astype(str).str.strip()
            df_kpi_long['Semana'] = df_kpi_long['Semana'].astype(str).str.strip()

        else:
            df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])
    else:
        df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])

    # 2. PARSER PESTAÑA TAREAS
    try:
        df_tareas_raw = pd.read_csv(URL_TAREAS_CSV, header=None)
    except Exception:
        df_tareas_raw = pd.DataFrame()
        
    if not df_tareas_raw.empty:
        h_idx_t = None
        for idx, row in df_tareas_raw.iterrows():
            row_vals = [str(val).strip().upper() for val in row.values]
            if any(h in row_vals for h in ['TAREA', 'RESPONSABLE PRINCIPAL', 'ESTADO']):
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
            text="Selecciona al menos un indicador para visualizar",
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
        is_money = "Bs" in unit_label or any(m in kpi.upper() for m in ['VENTAS', 'VENTA', 'PAGO', 'C X P', 'EFECTIVO', 'INVERSION'])
        val_prefix = "Bs " if is_money else ""
        
        max_val = sub_df['Valor'].max()
        use_secondary = (max_val > 50000 and "Bs" not in unit_label)

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
                connectgaps=True
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
        "🏆 Scorecard & Cumplimiento"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Datos Ahora", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("¡Datos actualizados!")

st.sidebar.link_button("🌐 Abrir Sheet en Google Drive", ONLINE_SHEET_URL, use_container_width=True)

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
        deptos_unicos = ["Todos"] + sorted([str(d) for d in df_kpis['Departamento'].dropna().unique() if str(d) != 'nan'])
        
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        with col_f1:
            # Seleccionar por defecto la última semana disponible (ej: Sem 31)
            selected_week = st.selectbox(
                "Seleccionar Semana a Inspeccionar:", 
                semanas_unicas, 
                index=len(semanas_unicas) - 1 if len(semanas_unicas) > 0 else 0
            )
            
        with col_f2:
            selected_dept = st.selectbox("Filtrar por Departamento:", deptos_unicos)

        df_filtered_dept = df_kpis.copy()
        if selected_dept != "Todos":
            df_filtered_dept = df_filtered_dept[df_filtered_dept['Departamento'] == selected_dept]

        responsables = ["Todos"] + sorted([str(r) for r in df_filtered_dept['Responsable'].dropna().unique() if str(r) != 'nan'])
        with col_f3:
            selected_resp = st.selectbox("Filtrar por Responsable:", responsables)

        current_week_idx = semanas_unicas.index(selected_week) if selected_week in semanas_unicas else 0
        df_all_selected = df_filtered_dept.copy()
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
                
                # Buscar el valor más reciente hacia atrás si la semana seleccionada no tiene dato cargado
                for w_idx in range(current_week_idx, -1, -1):
                    w_name = semanas_unicas[w_idx]
                    row_w = df_kpi_series[df_kpi_series['Semana'] == w_name]
                    if not row_w.empty and pd.notna(row_w['Valor'].values[0]):
                        val_curr = float(row_w['Valor'].values[0])
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
                
                # Variación contra semana anterior
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
                    
                # Promedio histórico
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
                
                # Formato monetario o de unidades
                is_money = any(m in kpi.upper() for m in ['VENTA', 'PAGO', 'C X P', 'EFECTIVO', 'INVERSION', 'VALOR', 'PRECIO'])
                prefix = "Bs " if is_money else ""
                val_formatted = f"{prefix}{val_curr:,.0f}" if (val_curr >= 100 or val_curr % 1 == 0) else f"{prefix}{val_curr:,.2f}"
                
                card_class = "kpi-card-fallback" if is_fallback else "kpi-card"
                fallback_tag = f'<div><span class="badge-warning">⚠️ Dato de {actual_data_week}</span></div>' if is_fallback else ""
                
                html_code = (
                    f'<div class="{card_class}">'
                    f'<div>'
                    f'<div class="kpi-card-header" title="{kpi}">{kpi}</div>'
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
        else:
            st.info("No se encontraron indicadores para los filtros seleccionados.")

# ------------------------------------------
# MÓDULO 2: COMPARADOR KPI vs KPI
# ------------------------------------------
elif menu_option == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Análisis Comparativo Multi-KPI")

    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        all_kpis_in_db = list(df_kpis['Medible'].unique())
        
        kpi_g1 = [k for k in all_kpis_in_db if any(kw in k.upper() for kw in ["VENTA", "PAGOS", "C X P", "EFECTIVO", "VALOR ENVIADO"])]
        kpi_g3 = [k for k in all_kpis_in_db if any(kw in k.upper() for kw in ["INVERSION", "MARKETING", "VENTA"])]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="compare-card-title">💵 1. Ventas, Envíos y Finanzas (Bs)</div>', unsafe_allow_html=True)
            fig1 = render_multi_kpi_chart(df_kpis, kpi_g1, title="Finanzas & Flujo de Ventas", height=380, unit_label="Monto en Bs")
            st.plotly_chart(fig1, use_container_width=True, key="card_1_main")
            if st.button("🔍 Maximizar Gráfico 1", key="btn_max_1", use_container_width=True):
                show_full_graph_dialog(df_kpis, kpi_g1, "Finanzas & Flujo de Ventas", unit_label="Monto en Bs")

        with c2:
            st.markdown('<div class="compare-card-title">🍰 2. Producción vs Envíos vs Bajas</div>', unsafe_allow_html=True)
            categorias_bekerai = ["Salados", "Tortas", "Pasteles Individuales", "Postres Enteros", "Panaderia"]
            selected_cats = st.multiselect("Filtrar Categorías:", categorias_bekerai, default=["Salados", "Tortas"])

            kpi_g2 = [k for k in all_kpis_in_db if any(cat.upper() in k.upper() for cat in selected_cats)] if selected_cats else []
            fig2 = render_multi_kpi_chart(df_kpis, kpi_g2, title="Flujo Físico por Categorías", height=380, unit_label="Unidades")
            st.plotly_chart(fig2, use_container_width=True, key="card_2_main")
            if st.button("🔍 Maximizar Gráfico 2", key="btn_max_2", use_container_width=True):
                show_full_graph_dialog(df_kpis, kpi_g2, "Flujo Físico por Categorías", unit_label="Unidades")

        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown('<div class="compare-card-title">📣 3. Inversión Marketing vs Ventas</div>', unsafe_allow_html=True)
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
# MÓDULO 3: GESTIÓN DE TAREAS
# ------------------------------------------
elif menu_option == "📝 Gestión de Tareas":
    st.subheader("📝 Lista de Tareas Operativas EOS")
    
    if not df_tasks.empty:
        f_col1, f_col2, f_col3 = st.columns(3)
        
        estados_disponibles = sorted(list(df_tasks['Estado'].dropna().unique()))
        with f_col1:
            sel_estados = st.multiselect("📌 Filtrar por Estado:", estados_disponibles, default=estados_disponibles)
            
        deptos_disponibles = sorted(list(df_tasks['Departamento'].dropna().unique()))
        with f_col2:
            sel_deptos = st.multiselect("🏢 Filtrar por Departamento:", deptos_disponibles, default=deptos_disponibles)
            
        all_resps = sorted(list(df_tasks['Responsable Principal'].dropna().unique()))
        with f_col3:
            sel_resps = st.multiselect("👤 Filtrar por Responsable:", all_resps, default=[])

        df_filtered = df_tasks.copy()
        if sel_estados: df_filtered = df_filtered[df_filtered['Estado'].isin(sel_estados)]
        if sel_deptos: df_filtered = df_filtered[df_filtered['Departamento'].isin(sel_deptos)]
        if sel_resps: df_filtered = df_filtered[df_filtered['Responsable Principal'].isin(sel_resps)]

        st.markdown(f"Mostrando **{len(df_filtered)}** de **{len(df_tasks)}** tareas en total.")
        st.markdown("<br>", unsafe_allow_html=True)

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

                equipo_str = f"<b>{row['Responsable Principal']}</b>"
                f_inicio = str(row.get('Fecha Inicio', '')).replace('00:00:00', '').strip()
                f_entrega = str(row.get('Fecha Entrega', '')).replace('00:00:00', '').strip()
                
                date_str = f"🗓️ Inicio: {f_inicio}" if f_inicio and f_inicio != 'nan' else ""
                if f_entrega and f_entrega != 'nan' and f_entrega != 'None':
                    date_str += f" | 🏁 Entrega: <b>{f_entrega}</b>"

                rows_html += f"""
                <div class="task-row {row_class}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div class="task-title">{row['TAREA']}</div>
                        <div>
                            <span class="task-badge {badge_class}">{badge_icon} {estado}</span>
                            <span class="task-badge badge-dept">🏢 {row['Departamento']}</span>
                        </div>
                    </div>
                    <div class="task-meta">
                        <div class="task-meta-item">👥 <b>Responsable:</b> {equipo_str}</div>
                        <div class="task-meta-item" style="margin-left: auto;">{date_str}</div>
                    </div>
                </div>
                """

            container_html = f'<div class="task-container-card">{rows_html}</div>'
            st.markdown(container_html, unsafe_allow_html=True)
        else:
            st.info("No hay tareas que coincidan con los filtros seleccionados.")

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
