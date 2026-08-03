import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as _go
import re

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA RECETARIO
# ==========================================
st.set_page_config(
    page_title="Fridolin - KPI_Bekerai",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS con el Rojo Borgoña del Recetario (#801B2B)
FRIDOLIN_CSS = """
<style>
    /* Fondo General Crema / Pastel */
    .stApp {
        background-color: #FAF6F0;
        color: #2C2C2C;
    }
    
    /* Header Principal Rojo Borgoña Recetario (#801B2B) */
    .main-header {
        background-color: #801B2B;
        padding: 1.5rem;
        border-radius: 12px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: #FFFDF9 !important;
        margin: 0;
        font-weight: 700;
    }
    
    .main-header p {
        color: #E2C08A !important;
        margin-top: 5px;
        font-size: 1.1rem;
    }

    /* Tarjetas de KPIs (KPI Cards) */
    .kpi-card {
        background-color: #FFFFFF;
        border-left: 5px solid #801B2B;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .kpi-title {
        color: #555555;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .kpi-value {
        color: #801B2B;
        font-size: 1.6rem;
        font-weight: bold;
    }
    .kpi-resp {
        color: #A67C1E;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #EFE8DE;
        border-radius: 6px 6px 0 0;
        color: #2C2C2C;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #801B2B !important;
        color: #FFFFFF !important;
    }
</style>
"""
st.markdown(FRIDOLIN_CSS, unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN Y CARGA EN VIVO DESDE GOOGLE DRIVE
# ==========================================

GOOGLE_SHEET_ID = "1xtRenOS7WgWdTcLBWRMUnN_To6irzyKS"
# Se obtiene en formato CSV dinámico desde Google Sheets
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)  # Auto-refresco cada 1 minuto
def load_data_from_drive():
    try:
        df_raw = pd.read_csv(SHEET_URL, header=None)
    except Exception:
        df_raw = pd.read_csv(SHEET_URL, header=None, on_bad_lines='skip')
    
    weeks = [f"Sem {i:02d}" for i in range(1, 31)]
    kpi_rows = []
    task_rows = []
    
    # Procesamiento flexible por cada fila del Google Sheet
    for _, row in df_raw.iterrows():
        row_vals = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip() != 'nan']
        if not row_vals:
            continue
            
        first_col = row_vals[0]
        
        # --- A. DETECCIÓN DE DATOS DE KPIs ---
        # Si la fila contiene responsables conocidos o nombres de KPIs conocidos
        if len(row) >= 5:
            col0 = str(row.iloc[0]).strip()
            col1 = str(row.iloc[1]).strip()
            
            # Buscar métricas en columna 0 o 1
            if any(k in col0.lower() or k in col1.lower() for k in ['venta', 'torta', 'efectivo', 'c x p', 'margen', 'baja', 'costo', 'produccion']):
                resp = col0 if len(col0) < 20 else "Asignado"
                metric = col1 if len(col0) < 20 else col0
                
                # Extraer valores numéricos de las siguientes columnas
                values = []
                for val_cell in row.iloc[2:32]:
                    v_clean = re.sub(r'[^\d.-]', '', str(val_cell))
                    try:
                        values.append(float(v_clean) if v_clean != '' else 0.0)
                    except Exception:
                        values.append(0.0)
                
                # Rellenar hasta 30 semanas si faltan
                while len(values) < 30:
                    values.append(0.0)
                    
                for wk, val in zip(weeks, values):
                    kpi_rows.append({
                        'Responsable': resp,
                        'Medible': metric,
                        'Semana': wk,
                        'Valor': val
                    })
                    
        # --- B. DETECCIÓN DE TAREAS ---
        if len(row_vals) >= 2 and not any(header in first_col.upper() for header in ['TAREA', 'MEDIBLE', 'SEMANA', 'RESPONSABLE']):
            task_name = row_vals[0]
            resp = row_vals[1] if len(row_vals) > 1 else "Por Asignar"
            fecha = row_vals[2] if len(row_vals) > 2 else ""
            status = row_vals[3] if len(row_vals) > 3 else "Pendiente"
            
            status_lower = status.lower()
            if 'proceso' in status_lower:
                status_clean = 'En Proceso'
            elif 'complet' in status_lower or 'listo' in status_lower:
                status_clean = 'Completado'
            else:
                status_clean = 'Pendiente'
                
            task_rows.append({
                'Semana': 'Sem 04',
                'Tarea': task_name,
                'Responsable': resp,
                'Fecha Entrega': fecha,
                'Estado': status_clean
            })

    df_kpis = pd.DataFrame(kpi_rows)
    df_tasks = pd.DataFrame(task_rows)
    
    return df_kpis, df_tasks, df_raw

# Barra lateral para forzar actualización
st.sidebar.title("⚙️ Opciones")
if st.sidebar.button("🔄 Actualizar Datos de Drive Ahora"):
    st.cache_data.clear()
    st.sidebar.success("¡Datos actualizados desde Google Drive!")

try:
    df_kpis, df_tasks, df_raw_preview = load_data_from_drive()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets. Detalles: {e}")
    st.stop()

# ==========================================
# 3. CABECERA PRINCIPAL
# ==========================================
st.markdown("""
<div class="main-header">
    <h1>FRIDOLIN - TABLERO CONTROL EOS & KPIs</h1>
    <p>Monitoreo Semanal de Indicadores, Tareas y Cumplimiento Bekerai 2026 (En Vivo)</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. MÓDULOS Y NAVEGACIÓN (TABS)
# ==========================================
tab1, tab2, tab3, tab4, tab_debug = st.tabs([
    "📊 Dashboards KPIs", 
    "🔀 Comparador KPI vs KPI", 
    "📝 Gestión de Tareas", 
    "🏆 Scorecard & Cumplimiento",
    "🔍 Explorador Sheet (Debug)"
])

# ------------------------------------------
# TAB 1: DASHBOARD GENERAL DE KPIs
# ------------------------------------------
with tab1:
    st.subheader("📌 Resumen de Indicadores Semanales")
    
    col_sel1, col_sel2 = st.columns([1, 3])
    with col_sel1:
        if not df_kpis.empty and 'Semana' in df_kpis.columns:
            selected_week = st.selectbox("Seleccionar Semana:", sorted(df_kpis['Semana'].unique()))
        else:
            selected_week = "Sem 01"
            
    df_week = df_kpis[df_kpis['Semana'] == selected_week] if not df_kpis.empty else pd.DataFrame()
    
    if not df_kpis.empty:
        available_metrics = df_kpis['Medible'].unique()
        kpis_to_show = list(available_metrics[:4]) if len(available_metrics) >= 4 else list(available_metrics)
        
        cols = st.columns(max(len(kpis_to_show), 1))
        
        for idx, kpi in enumerate(kpis_to_show):
            row = df_week[df_week['Medible'] == kpi] if not df_week.empty else pd.DataFrame()
            val = row['Valor'].values[0] if not row.empty else 0.0
            resp = row['Responsable'].values[0] if not row.empty else "-"
            
            with cols[idx]:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">{kpi}</div>
                    <div class="kpi-value">{val:,.0f}</div>
                    <div class="kpi-resp">Resp: {resp}</div>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("---")
        st.subheader("📈 Evolución Histórica de KPIs Clave")
        
        selected_kpi_trend = st.selectbox("Seleccionar KPI para ver evolución:", sorted(df_kpis['Medible'].unique()))
        df_trend = df_kpis[df_kpis['Medible'] == selected_kpi_trend].sort_values('Semana')
        
        fig_trend = px.line(
            df_trend, 
            x='Semana', 
            y='Valor', 
            markers=True,
            title=f"Evolución Histórica: {selected_kpi_trend}",
            color_discrete_sequence=['#801B2B']
        )
        fig_trend.update_layout(
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FAF6F0',
            xaxis_title="Semana",
            yaxis_title="Valor"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("⚠️ No se detectaron KPIs procesables directamente en la hoja por defecto. Revisa la pestaña 'Explorador Sheet' para ver los datos raw.")

# ------------------------------------------
# TAB 2: COMPARADOR KPI vs KPI
# ------------------------------------------
with tab2:
    st.subheader("🔀 Análisis Comparativo Multi-KPI")
    st.caption("Selecciona 2 métricas para analizar su correlación e impacto en el tiempo.")
    
    if not df_kpis.empty:
        c1, c2 = st.columns(2)
        metrics_list = sorted(df_kpis['Medible'].unique())
        with c1:
            kpi_1 = st.selectbox("Seleccionar Primer KPI (Eje Izquierdo):", metrics_list, index=0)
        with c2:
            kpi_2 = st.selectbox("Seleccionar Segundo KPI (Eje Derecho):", metrics_list, index=min(1, len(metrics_list)-1))
            
        df_k1 = df_kpis[df_kpis['Medible'] == kpi_1].sort_values('Semana')
        df_k2 = df_kpis[df_kpis['Medible'] == kpi_2].sort_values('Semana')
        
        fig_comp = _go.Figure()
        
        fig_comp.add_trace(_go.Scatter(
            x=df_k1['Semana'], y=df_k1['Valor'],
            name=kpi_1, line=dict(color='#801B2B', width=3)
        ))
        
        fig_comp.add_trace(_go.Scatter(
            x=df_k2['Semana'], y=df_k2['Valor'],
            name=kpi_2, line=dict(color='#E2C08A', width=3),
            yaxis="y2"
        ))
        
        fig_comp.update_layout(
            title=f"Comparativa: {kpi_1} vs {kpi_2}",
            xaxis=dict(title="Semana"),
            yaxis=dict(title=kpi_1, titlefont=dict(color="#801B2B"), tickfont=dict(color="#801B2B")),
            yaxis2=dict(title=kpi_2, titlefont=dict(color="#E2C08A"), tickfont=dict(color="#E2C08A"), overlaying="y", side="right"),
            paper_bgcolor='#FAF6F0',
            plot_bgcolor='#FFFFFF',
            legend=dict(x=0.01, y=0.99)
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)

# ------------------------------------------
# TAB 3: GESTIÓN DE TAREAS SEMANALES
# ------------------------------------------
with tab3:
    st.subheader("📝 Lista de Tareas y Operaciones EOS")
    
    if not df_tasks.empty:
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            sem_task_filter = st.selectbox("Filtrar por Semana (Tareas):", ["Todas"] + sorted(list(df_tasks['Semana'].unique())))
        with t_col2:
            resp_task_filter = st.selectbox("Filtrar por Responsable:", ["Todos"] + sorted(list(df_tasks['Responsable'].unique())))
            
        df_filtered_tasks = df_tasks.copy()
        if sem_task_filter != "Todas":
            df_filtered_tasks = df_filtered_tasks[df_filtered_tasks['Semana'] == sem_task_filter]
        if resp_task_filter != "Todos":
            df_filtered_tasks = df_filtered_tasks[df_filtered_tasks['Responsable'] == resp_task_filter]
            
        st.dataframe(
            df_filtered_tasks,
            use_container_width=True,
            hide_index=True
        )

# ------------------------------------------
# TAB 4: SCORECARD & % DE CUMPLIMIENTO
# ------------------------------------------
with tab4:
    st.subheader("🏆 Nivel de Cumplimiento por Integrante")
    
    if not df_tasks.empty:
        task_summary = df_tasks.groupby(['Responsable', 'Estado']).size().unstack(fill_value=0)
        
        for col_name in ['Completado', 'En Proceso', 'Pendiente']:
            if col_name not in task_summary.columns:
                task_summary[col_name] = 0
            
        task_summary['Total Tareas'] = task_summary.sum(axis=1)
        task_summary['% Cumplimiento'] = (task_summary['Completado'] / task_summary['Total Tareas'] * 100).round(1)
        
        task_summary = task_summary.reset_index().sort_values('% Cumplimiento', ascending=False)
        
        fig_score = px.bar(
            task_summary,
            x='Responsable',
            y='% Cumplimiento',
            text='% Cumplimiento',
            color='% Cumplimiento',
            color_continuous_scale=['#D9534F', '#F0AD4E', '#2E7D32'],
            title="Porcentaje de Cumplimiento de Tareas (%)"
        )
        fig_score.update_layout(
            paper_bgcolor='#FAF6F0',
            plot_bgcolor='#FFFFFF',
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig_score, use_container_width=True)
        
        st.subheader("📋 Resumen Detallado por Persona")
        st.dataframe(task_summary, use_container_width=True, hide_index=True)

# ------------------------------------------
# TAB 5: EXPLORADOR DRIVE (DEBUG)
# ------------------------------------------
with tab_debug:
    st.subheader("🔍 Previsualización directa del Google Sheet")
    st.caption("Esta vista muestra exactamente lo que la app está leyendo desde tu enlace de Google Drive:")
    st.dataframe(df_raw_preview, use_container_width=True)
