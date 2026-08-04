import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (FRIDOLIN)
# ==========================================
st.set_page_config(
    page_title="Fridolin - KPI Bekerai 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

FRIDOLIN_CSS = """
<style>
    .stApp {
        background-color: #FAF6F0;
        color: #2C2C2C;
    }
    .main-header {
        background-color: #801B2B;
        padding: 1.2rem;
        border-radius: 14px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    .main-header h1 {
        color: #FFFDF9 !important;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        color: #E2C08A !important;
        margin-top: 5px;
        margin-bottom: 0;
        font-size: 0.95rem;
    }
    section[data-testid="stSidebar"] {
        background-color: #F3ECE1 !important;
        border-right: 1px solid #E0D6C8;
    }
    
    /* TARJETAS ESTILO GROK BUILD (ESTÍLO CLEAN FRIDOLIN) */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E0D8;
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
        margin-bottom: 1rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card-header {
        font-size: 0.78rem;
        font-weight: 700;
        color: #666666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.4rem;
        height: 2.2rem;
        overflow: hidden;
    }
    .kpi-card-val {
        font-size: 1.65rem;
        font-weight: 800;
        color: #801B2B;
        margin-bottom: 0.6rem;
        font-variant-numeric: tabular-nums;
    }
    .kpi-card-footer {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        font-size: 0.78rem;
        border-top: 1px solid #F0EAE1;
        padding-top: 0.6rem;
    }
    .badge-up {
        color: #2E7D32;
        font-weight: 600;
    }
    .badge-down {
        color: #C62828;
        font-weight: 600;
    }
    .badge-neutral {
        color: #757575;
        font-weight: 500;
    }
    .kpi-resp-tag {
        font-size: 0.73rem;
        color: #A67C1E;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
</style>
"""
st.markdown(FRIDOLIN_CSS, unsafe_allow_html=True)

# ==========================================
# 2. CARGA DE DATOS DESDE GOOGLE DRIVE (XLSX)
# ==========================================
GOOGLE_SHEET_ID = "1YmxMIgdqn0Oe38mmUF3pFBVyWgUjyyxjmDdmWp-Oz1g"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)
def load_data():
    sheets = pd.read_excel(EXCEL_URL, sheet_name=None, header=None)
    
    # PARSER PESTAÑA KPI
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
            
            df_kpi_long['Valor'] = pd.to_numeric(df_kpi_long['Valor'], errors='coerce').fillna(0)
            df_kpi_long.rename(columns={'Quien': 'Responsable', 'Medibles': 'Medible'}, inplace=True)
            df_kpi_long = df_kpi_long[df_kpi_long['Medible'].notna() & (df_kpi_long['Medible'] != 'nan')]
        else:
            df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])
    else:
        df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])

    # PARSER PESTAÑA TAREAS
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
            df_tasks['Estado'] = df_tasks['Estado'].fillna('Pendiente')
            df_tasks['Responsable Principal'] = df_tasks['Responsable Principal'].fillna('Por Asignar')
        else:
            df_tasks = df_tareas_raw
    else:
        df_tasks = pd.DataFrame()

    return df_kpi_long, df_tasks

# ==========================================
# 3. BARRA LATERAL (MENÚ PRINCIPAL Y FILTROS)
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
st.sidebar.subheader("⚙️ Opciones de Datos")
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
# 4. CONTENIDO - MODULO 1: DASHBOARDS KPIs
# ==========================================
if menu_option == "📊 Dashboards KPIs":
    st.subheader("📌 Resumen de Indicadores Semanales")
    
    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        # Ordenar lista de semanas manteniendo orden cronológico
        semanas_unicas = list(df_kpis['Semana'].unique())
        
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            # Selecciona por defecto SIEMPRE la ÚLTIMA semana cargada
            selected_week = st.selectbox(
                "Seleccionar Semana a Inspeccionar:", 
                semanas_unicas, 
                index=len(semanas_unicas) - 1
            )
            
        responsables = ["Todos"] + sorted([str(r) for r in df_kpis['Responsable'].dropna().unique() if str(r) != 'nan'])
        with col_f2:
            selected_resp = st.selectbox("Filtrar tarjetas por Responsable:", responsables)

        # Determinar índice de la semana seleccionada y la anterior
        current_week_idx = semanas_unicas.index(selected_week)
        prev_week = semanas_unicas[current_week_idx - 1] if current_week_idx > 0 else None
        
        # Dataframe semana actual y anterior
        df_curr_week = df_kpis[df_kpis['Semana'] == selected_week]
        df_prev_week = df_kpis[df_kpis['Semana'] == prev_week] if prev_week else pd.DataFrame()
        
        if selected_resp != "Todos":
            df_curr_week = df_curr_week[df_curr_week['Responsable'] == selected_resp]
            
        metrics_list = df_curr_week['Medible'].unique()
        
        st.markdown(f"##### Datos de **{selected_week}**" + (f" *(comparado con {prev_week})*" if prev_week else ""))
        
        if len(metrics_list) > 0:
            # Grilla de 4 tarjetas por fila
            cols = st.columns(4)
            for idx, kpi in enumerate(metrics_list):
                row_curr = df_curr_week[df_curr_week['Medible'] == kpi]
                val_curr = float(row_curr['Valor'].values[0]) if not row_curr.empty else 0.0
                resp = row_curr['Responsable'].values[0] if not row_curr.empty else "-"
                
                # 1. Variación vs Semana Anterior
                val_prev = None
                if not df_prev_week.empty:
                    row_prev = df_prev_week[df_prev_week['Medible'] == kpi]
                    if not row_prev.empty:
                        val_prev = float(row_prev['Valor'].values[0])
                
                if val_prev is not None and val_prev != 0:
                    pct_prev = ((val_curr - val_prev) / val_prev) * 100
                    if pct_prev > 0:
                        var_prev_html = f'<span class="badge-up">▲ +{pct_prev:.1f}%</span> vs {prev_week}'
                    elif pct_prev < 0:
                        var_prev_html = f'<span class="badge-down">▼ {pct_prev:.1f}%</span> vs {prev_week}'
                    else:
                        var_prev_html = f'<span class="badge-neutral">= 0.0%</span> vs {prev_week}'
                else:
                    var_prev_html = '<span class="badge-neutral">-- N/A vs sem anterior</span>'
                    
                # 2. Variación vs Promedio Historico Total
                df_kpi_hist = df_kpis[df_kpis['Medible'] == kpi]
                avg_total = df_kpi_hist['Valor'].mean() if not df_kpi_hist.empty else 0.0
                
                if avg_total > 0:
                    pct_avg = ((val_curr - avg_total) / avg_total) * 100
                    if pct_avg > 0:
                        var_avg_html = f'<span class="badge-up">▲ +{pct_avg:.1f}%</span> vs prom ({avg_total:,.0f})'
                    elif pct_avg < 0:
                        var_avg_html = f'<span class="badge-down">▼ {pct_avg:.1f}%</span> vs prom ({avg_total:,.0f})'
                    else:
                        var_avg_html = f'<span class="badge-neutral">= prom ({avg_total:,.0f})</span>'
                else:
                    var_avg_html = '<span class="badge-neutral">-- N/A vs prom</span>'
                
                # Formato numérico en moneda/entero
                if val_curr >= 1000 or val_curr % 1 == 0:
                    val_formatted = f"{val_curr:,.0f}"
                else:
                    val_formatted = f"{val_curr:,.2f}"
                
                # Render Tarjeta Estilo Grok Build con colores Fridolin
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div>
                            <div class="kpi-card-header">{kpi}</div>
                            <div class="kpi-resp-tag">👤 Resp: {resp}</div>
                            <div class="kpi-card-val">{val_formatted}</div>
                        </div>
                        <div class="kpi-card-footer">
                            <div>{var_prev_html}</div>
                            <div>{var_avg_html}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No hay métricas disponibles para el filtro seleccionado.")
                
        st.markdown("---")
        st.subheader("📈 Evolución Histórica de KPIs")
        
        all_metrics = sorted([m for m in df_kpis['Medible'].dropna().unique() if str(m) != 'nan'])
        if all_metrics:
            selected_kpi_trend = st.selectbox("Seleccionar KPI para analizar su línea de tiempo:", all_metrics)
            
            df_trend = df_kpis[df_kpis['Medible'] == selected_kpi_trend]
            
            fig_trend = px.line(
                df_trend, 
                x='Semana', 
                y='Valor', 
                markers=True,
                title=f"Evolución Semanal: {selected_kpi_trend}",
                color_discrete_sequence=['#801B2B']
            )
            fig_trend.update_traces(line=dict(width=3), marker=dict(size=8))
            fig_trend.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FAF6F0',
                xaxis_title="Semana",
                yaxis_title="Valor"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("⚠️ No se encontraron datos en la pestaña KPI del documento.")

# ------------------------------------------
# MODULO 2: COMPARADOR KPI vs KPI
# ------------------------------------------
elif menu_option == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Análisis Comparativo Multi-KPI")
    
    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        metrics_list = sorted([m for m in df_kpis['Medible'].dropna().unique() if str(m) != 'nan'])
        
        if len(metrics_list) >= 2:
            c1, c2 = st.columns(2)
            with c1:
                kpi_1 = st.selectbox("Primer KPI (Eje Izquierdo):", metrics_list, index=0)
            with c2:
                kpi_2 = st.selectbox("Segundo KPI (Eje Derecho):", metrics_list, index=1)
                
            df_k1 = df_kpis[df_kpis['Medible'] == kpi_1]
            df_k2 = df_kpis[df_kpis['Medible'] == kpi_2]
            
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=df_k1['Semana'], y=df_k1['Valor'],
                name=str(kpi_1), line=dict(color='#801B2B', width=3)
            ))
            fig_comp.add_trace(go.Scatter(
                x=df_k2['Semana'], y=df_k2['Valor'],
                name=str(kpi_2), line=dict(color='#E2C08A', width=3),
                yaxis="y2"
            ))
            fig_comp.update_layout(
                title=dict(text=f"Comparativa: {kpi_1} vs {kpi_2}"),
                xaxis=dict(title="Semana"),
                yaxis=dict(title=dict(text=str(kpi_1), font=dict(color="#801B2B")), tickfont=dict(color="#801B2B")),
                yaxis2=dict(title=dict(text=str(kpi_2), font=dict(color="#E2C08A")), tickfont=dict(color="#E2C08A"), overlaying="y", side="right"),
                paper_bgcolor='#FAF6F0', plot_bgcolor='#FFFFFF', legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig_comp, use_container_width=True)

# ------------------------------------------
# MODULO 3: GESTIÓN DE TAREAS
# ------------------------------------------
elif menu_option == "📝 Gestión de Tareas":
    st.subheader("📝 Lista de Tareas y Operaciones EOS")
    if not df_tasks.empty:
        st.dataframe(df_tasks, use_container_width=True, hide_index=True)

# ------------------------------------------
# MODULO 4: SCORECARD & CUMPLIMIENTO
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
            color='% Cumplimiento', color_continuous_scale=['#D9534F', '#F0AD4E', '#2E7D32']
        )
        fig_score.update_layout(paper_bgcolor='#FAF6F0', plot_bgcolor='#FFFFFF', yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_score, use_container_width=True)

# ------------------------------------------
# MODULO 5: EXPLORADOR SHEET (DEBUG)
# ------------------------------------------
elif menu_option == "🔍 Explorador Sheet (Debug)":
    st.subheader("🔍 Previsualización Directa de Datos Procesados")
    st.dataframe(df_kpis, use_container_width=True)
