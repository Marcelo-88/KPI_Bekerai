import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Fridolin - KPI Bekerai 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS con Branding Fridolin / Recetario (#801B2B)
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
        padding: 1.2rem;
        border-radius: 12px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
        font-size: 1rem;
    }

    /* Estilos de Barra Lateral */
    section[data-testid="stSidebar"] {
        background-color: #F3ECE1 !important;
        border-right: 1px solid #E0D6C8;
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
        height: 2.5rem;
        overflow: hidden;
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
</style>
"""
st.markdown(FRIDOLIN_CSS, unsafe_allow_html=True)

# ==========================================
# 2. CARGA DE DATOS DESDE GOOGLE DRIVE (XLSX)
# ==========================================
GOOGLE_SHEET_ID = "1YmxMIgdqn0Oe38mmUF3pFBVyWgUjyyxjmDdmWp-Oz1g"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=60)  # Refresco automático cada 60 segundos
def load_data():
    # Leer las pestañas del Excel exportado
    sheets = pd.read_excel(EXCEL_URL, sheet_name=None)
    
    # --- A. PARSER PESTAÑA KPI ---
    df_kpi_raw = sheets.get('KPI', pd.DataFrame())
    
    if not df_kpi_raw.empty:
        id_cols = ['Quien', 'Departamento', 'Medibles']
        id_cols_present = [c for c in id_cols if c in df_kpi_raw.columns]
        val_cols = [c for c in df_kpi_raw.columns if c not in id_cols]
        
        # Despivotar semanas
        df_kpi_long = pd.melt(
            df_kpi_raw, 
            id_vars=id_cols_present, 
            value_vars=val_cols, 
            var_name='Semana', 
            value_name='Valor'
        )
        df_kpi_long['Valor'] = pd.to_numeric(df_kpi_long['Valor'], errors='coerce').fillna(0)
        df_kpi_long.rename(columns={'Quien': 'Responsable', 'Medibles': 'Medible'}, inplace=True)
    else:
        df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])

    # --- B. PARSER PESTAÑA TAREAS ---
    df_tareas_raw = sheets.get('Tareas', pd.DataFrame())
    if not df_tareas_raw.empty:
        # Reemplazar valores vacíos
        df_tareas_raw['Estado'] = df_tareas_raw['Estado'].fillna('Pendiente')
        df_tareas_raw['Responsable Principal'] = df_tareas_raw['Responsable Principal'].fillna('Por Asignar')
    else:
        df_tareas_raw = pd.DataFrame()

    return df_kpi_long, df_tareas_raw

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
    st.sidebar.success("¡Datos actualizados desde Google Drive!")

# Carga de datos
try:
    df_kpis, df_tasks = load_data()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets. Verifica los permisos de tu archivo. Detalles: {e}")
    st.stop()

# Header Principal Superior
st.markdown("""
<div class="main-header">
    <h1>FRIDOLIN - TABLERO CONTROL EOS & KPIs</h1>
    <p>Monitoreo Semanal de Indicadores, Tareas y Cumplimiento Bekerai 2026 (En Vivo)</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. CONTENIDO SEGÚN EL MÓDULO SELECCIONADO
# ==========================================

# ------------------------------------------
# MODULO 1: DASHBOARDS KPIs
# ------------------------------------------
if menu_option == "📊 Dashboards KPIs":
    st.subheader("📌 Resumen de Indicadores Semanales")
    
    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        semanas_disponibles = sorted(df_kpis['Semana'].unique().tolist())
        col_sel1, col_sel2 = st.columns([1, 2])
        with col_sel1:
            selected_week = st.selectbox("Seleccionar Semana:", semanas_disponibles, index=0)
            
        df_week = df_kpis[df_kpis['Semana'] == selected_week]
        
        # Filtro opcional por Responsable o Departamento
        responsables = ["Todos"] + sorted([str(r) for r in df_kpis['Responsable'].dropna().unique()])
        with col_sel2:
            selected_resp = st.selectbox("Filtrar tarjetas por Responsable:", responsables)
            
        if selected_resp != "Todos":
            df_week_cards = df_week[df_week['Responsable'] == selected_resp]
        else:
            df_week_cards = df_week
            
        # Mostrar tarjetas de métricas
        metrics_list = df_week_cards['Medible'].unique()
        if len(metrics_list) > 0:
            cols = st.columns(min(4, len(metrics_list)))
            for idx, kpi in enumerate(metrics_list[:12]):
                row = df_week_cards[df_week_cards['Medible'] == kpi]
                val = row['Valor'].values[0] if not row.empty else 0.0
                resp = row['Responsable'].values[0] if not row.empty else "-"
                
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-title">{kpi}</div>
                        <div class="kpi-value">{val:,.2f}</div>
                        <div class="kpi-resp">Resp: {resp}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No hay métricas para el filtro seleccionado.")
                
        st.markdown("---")
        st.subheader("📈 Evolución Histórica de KPIs Clave")
        
        all_metrics = sorted(df_kpis['Medible'].dropna().unique())
        selected_kpi_trend = st.selectbox("Seleccionar KPI para ver su tendencia:", all_metrics)
        
        df_trend = df_kpis[df_kpis['Medible'] == selected_kpi_trend]
        
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
        st.warning("⚠️ No se encontraron datos en la pestaña KPI del documento.")

# ------------------------------------------
# MODULO 2: COMPARADOR KPI vs KPI
# ------------------------------------------
elif menu_option == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Análisis Comparativo Multi-KPI")
    st.caption("Compara el comportamiento de 2 indicadores a lo largo de las semanas.")
    
    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        metrics_list = sorted(df_kpis['Medible'].dropna().unique())
        
        if len(metrics_list) >= 2:
            c1, c2 = st.columns(2)
            with c1:
                kpi_1 = st.selectbox("Seleccionar Primer KPI (Eje Izquierdo):", metrics_list, index=0)
            with c2:
                kpi_2 = st.selectbox("Seleccionar Segundo KPI (Eje Derecho):", metrics_list, index=1)
                
            df_k1 = df_kpis[df_kpis['Medible'] == kpi_1]
            df_k2 = df_kpis[df_kpis['Medible'] == kpi_2]
            
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Scatter(
                x=df_k1['Semana'], 
                y=df_k1['Valor'],
                name=str(kpi_1), 
                line=dict(color='#801B2B', width=3)
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=df_k2['Semana'], 
                y=df_k2['Valor'],
                name=str(kpi_2), 
                line=dict(color='#E2C08A', width=3),
                yaxis="y2"
            ))
            
            fig_comp.update_layout(
                title=dict(text=f"Comparativa: {kpi_1} vs {kpi_2}"),
                xaxis=dict(title="Semana"),
                yaxis=dict(
                    title=dict(text=str(kpi_1), font=dict(color="#801B2B")),
                    tickfont=dict(color="#801B2B")
                ),
                yaxis2=dict(
                    title=dict(text=str(kpi_2), font=dict(color="#E2C08A")),
                    tickfont=dict(color="#E2C08A"),
                    overlaying="y",
                    side="right"
                ),
                paper_bgcolor='#FAF6F0',
                plot_bgcolor='#FFFFFF',
                legend=dict(x=0.01, y=0.99)
            )
            
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Necesitas al menos 2 métricas en tu tabla para comparar.")
    else:
        st.info("No hay datos de KPIs disponibles.")

# ------------------------------------------
# MODULO 3: GESTIÓN DE TAREAS
# ------------------------------------------
elif menu_option == "📝 Gestión de Tareas":
    st.subheader("📝 Lista de Tareas y Operaciones EOS")
    
    if not df_tasks.empty:
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            depto_filter = st.selectbox("Filtrar por Departamento:", ["Todos"] + sorted(list(df_tasks['Departamento'].dropna().unique())))
        with t_col2:
            resp_filter = st.selectbox("Filtrar por Responsable Principal:", ["Todos"] + sorted(list(df_tasks['Responsable Principal'].dropna().unique())))
            
        df_filtered_tasks = df_tasks.copy()
        if depto_filter != "Todos":
            df_filtered_tasks = df_filtered_tasks[df_filtered_tasks['Departamento'] == depto_filter]
        if resp_filter != "Todos":
            df_filtered_tasks = df_filtered_tasks[df_filtered_tasks['Responsable Principal'] == resp_filter]
            
        st.dataframe(
            df_filtered_tasks,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No se encontraron registros en la pestaña 'Tareas'.")

# ------------------------------------------
# MODULO 4: SCORECARD & CUMPLIMIENTO
# ------------------------------------------
elif menu_option == "🏆 Scorecard & Cumplimiento":
    st.subheader("🏆 Cumplimiento de Tareas por Responsable")
    
    if not df_tasks.empty and 'Estado' in df_tasks.columns:
        task_summary = df_tasks.groupby(['Responsable Principal', 'Estado']).size().unstack(fill_value=0)
        
        for col_name in ['Finalizado', 'Completado', 'En Proceso', 'Pendiente']:
            if col_name not in task_summary.columns:
                task_summary[col_name] = 0
            
        task_summary['Completadas'] = task_summary.get('Finalizado', 0) + task_summary.get('Completado', 0)
        task_summary['Total Tareas'] = task_summary.sum(axis=1) - task_summary['Completadas']
        task_summary['% Cumplimiento'] = (task_summary['Completadas'] / task_summary['Total Tareas'] * 100).round(1).fillna(0)
        
        task_summary = task_summary.reset_index().sort_values('% Cumplimiento', ascending=False)
        
        fig_score = px.bar(
            task_summary,
            x='Responsable Principal',
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
        st.subheader("📋 Resumen Detallado")
        st.dataframe(task_summary, use_container_width=True, hide_index=True)
    else:
        st.info("No hay suficientes datos en la pestaña Tareas para generar el Scorecard.")

# ------------------------------------------
# MODULO 5: EXPLORADOR SHEET (DEBUG)
# ------------------------------------------
elif menu_option == "🔍 Explorador Sheet (Debug)":
    st.subheader("🔍 Previsualización Directa de Datos Procesados")
    st.write("**Pestaña KPI (Transformada para el Tablero):**")
    st.dataframe(df_kpis, use_container_width=True)
    
    st.write("**Pestaña Tareas (Raw):**")
    st.dataframe(df_tasks, use_container_width=True)
