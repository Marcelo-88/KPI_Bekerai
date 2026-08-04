import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as bg

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FRIDOLIN - Tablero Control EOS & KPIs",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# ESTILOS CSS AVANZADOS (DISEÑO PREMIUM)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* Estilos Generales */
    .main-header {
        background: linear-gradient(135deg, #800020 0%, #4A0012 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .main-header p {
        margin-top: 8px;
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Tarjetas Métricas */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 18px;
        border-left: 6px solid #800020;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #6c757d;
        text-transform: uppercase;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f2937;
        margin: 5px 0;
    }
    .metric-sub {
        font-size: 0.8rem;
    }
    .status-ok { color: #10B981; font-weight: 600; }
    .status-warning { color: #F59E0B; font-weight: 600; }
    .status-danger { color: #EF4444; font-weight: 600; }
    
    /* Ajustes Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARGA DE DATOS & DATOS DE RESPALDO (MOCK DATA)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_kpi_data():
    # Estructura completa de respaldo para asegurar que NADA quede en blanco
    data_kpis = {
        'Semana': ['Semana 1', 'Semana 1', 'Semana 1', 'Semana 2', 'Semana 2', 'Semana 2', 'Semana 3', 'Semana 3', 'Semana 3', 'Semana 4', 'Semana 4', 'Semana 4'],
        'KPI': ['Ventas Totales ($)', 'Margen Bruto (%)', 'NPS Cliente', 'Ventas Totales ($)', 'Margen Bruto (%)', 'NPS Cliente', 'Ventas Totales ($)', 'Margen Bruto (%)', 'NPS Cliente', 'Ventas Totales ($)', 'Margen Bruto (%)', 'NPS Cliente'],
        'Responsable': ['Carlos M.', 'Ana R.', 'Sofia T.', 'Carlos M.', 'Ana R.', 'Sofia T.', 'Carlos M.', 'Ana R.', 'Sofia T.', 'Carlos M.', 'Ana R.', 'Sofia T.'],
        'Objetivo': [100000, 45.0, 85, 100000, 45.0, 85, 105000, 45.0, 85, 105000, 45.0, 85],
        'Real': [98000, 42.5, 88, 102000, 46.1, 87, 94000, 41.0, 82, 108000, 45.8, 89],
    }
    df = pd.DataFrame(data_kpis)
    df['Cumplimiento (%)'] = (df['Real'] / df['Objetivo']) * 100
    
    def get_status(row):
        if row['Cumplimiento (%)'] >= 100:
            return 'Cumplido'
        elif row['Cumplimiento (%)'] >= 90:
            return 'En Rango'
        else:
            return 'Crítico'
            
    df['Estado'] = df.apply(get_status, axis=1)
    return df

@st.cache_data(ttl=60)
def load_tasks_data():
    tasks = {
        'ID': ['T-101', 'T-102', 'T-103', 'T-104', 'T-105'],
        'Roca / Tarea EOS': ['Implementar módulo de inventario', 'Optimizar tiempo de entrega', 'Capacitación del equipo de ventas', 'Auditoría de calidad semanal', 'Revisión presupuestaria Q3'],
        'Responsable': ['Carlos M.', 'Ana R.', 'Roberto G.', 'Sofia T.', 'Carlos M.'],
        'Prioridad': ['Alta', 'Media', 'Alta', 'Baja', 'Alta'],
        'Fecha Límite': ['2026-08-15', '2026-08-20', '2026-08-10', '2026-08-25', '2026-08-30'],
        'Estado': ['En Proceso', 'Pendiente', 'Completado', 'Pendiente', 'En Proceso']
    }
    return pd.DataFrame(tasks)

df_kpis = load_kpi_data()
df_tasks = load_tasks_data()

# -----------------------------------------------------------------------------
# BARRA LATERAL (SIDEBAR)
# -----------------------------------------------------------------------------
st.sidebar.title("📌 Menú Principal")

modulo = st.sidebar.radio(
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
    st.rerun()

st.sidebar.success("¡Datos actualizados!")
st.sidebar.markdown("[🌐 Abrir Sheet en Google Drive](https://drive.google.com)")

# -----------------------------------------------------------------------------
# ENCABEZADO
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="main-header">
        <h1>FRIDOLIN - TABLERO CONTROL EOS & KPIs</h1>
        <p>Monitoreo Semanal de Indicadores, Tareas y Cumplimiento Bekerai 2026</p>
    </div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MÓDULO 1: DASHBOARDS KPIS
# -----------------------------------------------------------------------------
if modulo == "📊 Dashboards KPIs":
    st.subheader("📌 Resumen de Indicadores Semanales")
    
    # Filtros superiores
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        semanas_disp = ["Todas"] + list(df_kpis['Semana'].unique())
        semana_sel = st.selectbox("Seleccionar Semana:", semanas_disp)
    with col_f2:
        kpis_disp = ["Todos"] + list(df_kpis['KPI'].unique())
        kpi_sel = st.selectbox("Seleccionar KPI:", kpis_disp)
        
    df_filtered = df_kpis.copy()
    if semana_sel != "Todas":
        df_filtered = df_filtered[df_filtered['Semana'] == semana_sel]
    if kpi_sel != "Todos":
        df_filtered = df_filtered[df_filtered['KPI'] == kpi_sel]

    # Tarjetas Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    total_kpis = len(df_filtered)
    prom_cumpl = df_filtered['Cumplimiento (%)'].mean() if not df_filtered.empty else 0
    num_cumplidos = len(df_filtered[df_filtered['Estado'] == 'Cumplido'])
    num_criticos = len(df_filtered[df_filtered['Estado'] == 'Crítico'])
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">KPIs Monitoreados</div>
                <div class="metric-value">{total_kpis}</div>
                <div class="metric-sub">Registros en filtro</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Cumplimiento Prom.</div>
                <div class="metric-value">{prom_cumpl:.1f}%</div>
                <div class="metric-sub status-ok">Meta: >95%</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">KPIs Cumplidos</div>
                <div class="metric-value">{num_cumplidos}</div>
                <div class="metric-sub status-ok">✓ En Meta</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">KPIs Críticos</div>
                <div class="metric-value">{num_criticos}</div>
                <div class="metric-sub status-danger">⚠️ Atención requerida</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Gráficos y Tabla
    col_g1, col_g2 = st.columns([3, 2])
    
    with col_g1:
        st.markdown("##### 📈 Evolución por Semana")
        fig_trend = px.line(
            df_filtered, 
            x='Semana', 
            y='Real', 
            color='KPI', 
            markers=True,
            text='Real',
            title="Valores Reales por Semana"
        )
        fig_trend.update_traces(textposition="top center")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_g2:
        st.markdown("##### 📊 Distribución de Estados")
        fig_pie = px.pie(
            df_filtered, 
            names='Estado', 
            color='Estado',
            color_discrete_map={'Cumplido':'#10B981', 'En Rango':'#F59E0B', 'Crítico':'#EF4444'},
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("##### 📋 Tabla Detallada")
    st.dataframe(df_filtered.style.highlight_max(axis=0, subset=['Cumplimiento (%)']), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# MÓDULO 2: COMPARADOR KPI VS KPI
# -----------------------------------------------------------------------------
elif modulo == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Comparador de Indicadores")
    
    col_c1, col_c2 = st.columns(2)
    kpis_lista = list(df_kpis['KPI'].unique())
    
    with col_c1:
        kpi_1 = st.selectbox("Selecciona Indicador A:", kpis_lista, index=0)
    with col_c2:
        kpi_2 = st.selectbox("Selecciona Indicador B:", kpis_lista, index=1 if len(kpis_lista)>1 else 0)
        
    df_k1 = df_kpis[df_kpis['KPI'] == kpi_1]
    df_k2 = df_kpis[df_kpis['KPI'] == kpi_2]
    
    fig_comp = bg.Figure()
    fig_comp.add_trace(bg.Scatter(x=df_k1['Semana'], y=df_k1['Real'], name=kpi_1, mode='lines+markers'))
    fig_comp.add_trace(bg.Scatter(x=df_k2['Semana'], y=df_k2['Real'], name=kpi_2, mode='lines+markers', yaxis='y2'))
    
    fig_comp.update_layout(
        title=f"Comparativa: {kpi_1} vs {kpi_2}",
        yaxis=dict(title=kpi_1),
        yaxis2=dict(title=kpi_2, overlaying='y', side='right'),
        legend=dict(x=0, y=1.1, orientation='h')
    )
    
    st.plotly_chart(fig_comp, use_container_width=True)

# -----------------------------------------------------------------------------
# MÓDULO 3: GESTIÓN DE TAREAS
# -----------------------------------------------------------------------------
elif modulo == "📝 Gestión de Tareas":
    st.subheader("📝 Seguimiento de Rocas y Tareas EOS")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric("Total Tareas", len(df_tasks))
    with col_t2:
        st.metric("Completadas", len(df_tasks[df_tasks['Estado'] == 'Completado']))
    with col_t3:
        st.metric("Pendientes / En Proceso", len(df_tasks[df_tasks['Estado'] != 'Completado']))
        
    st.markdown("---")
    st.dataframe(df_tasks, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# MÓDULO 4: SCORECARD & CUMPLIMIENTO
# -----------------------------------------------------------------------------
elif modulo == "🏆 Scorecard & Cumplimiento":
    st.subheader("🏆 Scorecard de Cumplimiento General EOS")
    
    df_scorecard = df_kpis.groupby('Responsable').agg(
        Total_KPIs=('KPI', 'count'),
        Cumplimiento_Promedio=('Cumplimiento (%)', 'mean')
    ).reset_index()
    
    fig_bar = px.bar(
        df_scorecard, 
        x='Responsable', 
        y='Cumplimiento_Promedio',
        color='Cumplimiento_Promedio',
        text_auto='.1f',
        title="Desempeño Promedio por Responsable (%)",
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("##### Resumen por Responsable")
    st.dataframe(df_scorecard, use_container_width=True, hide_index=True)
