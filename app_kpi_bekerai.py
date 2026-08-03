import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# Estilos CSS con Branding Fridolin / Recetario (#801B2B)
FRIDOLIN_CSS = """
<style>
    /* Fondo General Crema / Pastel */
    .stApp {
        background-color: #FAF6F0;
        color: #2C2C2C;
    }
    
    /* Header Principal Rojo Borgoña Recetario */
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
# 2. CONEXIÓN Y CARGA EN VIVO DESDE GOOGLE DRIVE
# ==========================================

GOOGLE_SHEET_ID = "1xtRenOS7WgWdTcLBWRMUnN_To6irzyKS"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)  # Auto-refresco de datos cada 1 minuto
def load_data_from_drive():
    try:
        df_raw = pd.read_csv(SHEET_URL, header=None)
    except Exception:
        df_raw = pd.read_csv(SHEET_URL, header=None, on_bad_lines='skip')
    
    weeks = [f"Sem {i:02d}" for i in range(1, 31)]
    kpi_rows = []
    task_rows = []
    
    # Procesamiento robusto de filas
    for _, row in df_raw.iterrows():
        # Limpiar celdas vacías
        row_vals = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip() not in ['nan', 'None', '']]
        if not row_vals:
            continue
            
        col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col1 = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        
        # --- A. PARSER DE KPIs ---
        # Detectar filas que contengan nombres de métricas o responsables
        if len(row) >= 3:
            combined_text = f"{col0} {col1}".lower()
            if any(term in combined_text for term in ['venta', 'torta', 'efectivo', 'c x p', 'margen', 'baja', 'costo', 'produccion', 'desperdicio', 'ticket', 'cumplimiento', 'subida']):
                resp = col0 if (col0 and len(col0) < 25 and not any(char.isdigit() for char in col0)) else "Sin Asignar"
                metric = col1 if resp != "Sin Asignar" else col0
                
                # Ignorar encabezados genéricos
                if metric.upper() not in ['MEDIBLE', 'KPI', 'INDICADOR', 'TAREA']:
                    values = []
                    for val_cell in row.iloc[2:32]:
                        v_clean = re.sub(r'[^\d.-]', '', str(val_cell))
                        try:
                            values.append(float(v_clean) if v_clean != '' else 0.0)
                        except Exception:
                            values.append(0.0)
                    
                    while len(values) < 30:
                        values.append(0.0)
                        
                    for wk, val in zip(weeks, values):
                        kpi_rows.append({
                            'Responsable': resp,
                            'Medible': metric,
                            'Semana': wk,
                            'Valor': val
                        })
                        
        # --- B. PARSER DE TAREAS ---
        if len(row_vals) >= 2:
            first_col_upper = row_vals[0].upper()
            if not any(hdr in first_col_upper for hdr in ['TAREA', 'MEDIBLE', 'SEMANA', 'RESPONSABLE', 'RESP']):
                # Si parece una descripción de tarea
                if len(row_vals[0]) > 4 and not any(term in row_vals[0].lower() for term in ['semana', 'total', 'promedio']):
                    task_name = row_vals[0]
                    resp_task = row_vals[1] if len(row_vals) > 1 else "Por Asignar"
                    fecha = row_vals[2] if len(row_vals) > 2 else ""
                    status = row_vals[3] if len(row_vals) > 3 else "Pendiente"
                    
                    status_lower = status.lower()
                    if 'proceso' in status_lower:
                        status_clean = 'En Proceso'
                    elif 'complet' in status_lower or 'listo' in status_lower or 'hecho' in status_lower:
                        status_clean = 'Completado'
                    else:
                        status_clean = 'Pendiente'
                        
                    task_rows.append({
                        'Semana': 'Sem 04',
                        'Tarea': task_name,
                        'Responsable': resp_task,
                        'Fecha Entrega': fecha,
                        'Estado': status_clean
                    })

    df_kpis = pd.DataFrame(kpi_rows)
    df_tasks = pd.DataFrame(task_rows)
    
    return df_kpis, df_tasks, df_raw

# ==========================================
# 3. BARRA LATERAL (MENÚ PRINCIPAL Y OPCIONES)
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
if st.sidebar.button("🔄 Actualizar Datos de Drive Ahora", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("¡Datos actualizados desde Google Drive!")

# Carga de datos
try:
    df_kpis, df_tasks, df_raw_preview = load_data_from_drive()
except Exception as e:
    st.error(f"⚠️ Error al procesar los datos de Google Drive. Detalles: {e}")
    st.stop()

# Header Principal Superior
st.markdown("""
<div class="main-header">
    <h1>FRIDOLIN - TABLERO CONTROL EOS & KPIs</h1>
    <p>Monitoreo Semanal de Indicadores, Tareas y Cumplimiento Bekerai 2026 (En Vivo)</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. CONTENIDO SEGÚN LA OPCIÓN SELECCIONADA EN LA BARRA LATERAL
# ==========================================

# ------------------------------------------
# OPCIÓN 1: DASHBOARDS KPIs
# ------------------------------------------
if menu_option == "📊 Dashboards KPIs":
    st.subheader("📌 Resumen de Indicadores Semanales")
    
    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        col_sel1, col_sel2 = st.columns([1, 3])
        with col_sel1:
            selected_week = st.selectbox("Seleccionar Semana:", sorted(df_kpis['Semana'].unique()))
            
        df_week = df_kpis[df_kpis['Semana'] == selected_week]
        available_metrics = df_kpis['Medible'].unique()
        
        # Seleccionar hasta 4 métricas principales
        kpis_to_show = list(available_metrics[:4])
        cols = st.columns(max(len(kpis_to_show), 1))
        
        for idx, kpi in enumerate(kpis_to_show):
            row = df_week[df_week['Medible'] == kpi]
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
        
        selected_kpi_trend = st.selectbox("Seleccionar KPI para ver evolución:", sorted(available_metrics))
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
        st.info("ℹ️ No se detectaron métricas procesadas aún. Consulta la pestaña 'Explorador Sheet (Debug)' en la barra lateral para revisar los datos originales.")

# ------------------------------------------
# OPCIÓN 2: COMPARADOR KPI vs KPI
# ------------------------------------------
elif menu_option == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Análisis Comparativo Multi-KPI")
    st.caption("Selecciona 2 métricas para analizar su correlación e impacto en el tiempo.")
    
    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        metrics_list = sorted(df_kpis['Medible'].unique())
        
        if len(metrics_list) >= 1:
            c1, c2 = st.columns(2)
            with c1:
                kpi_1 = st.selectbox("Seleccionar Primer KPI (Eje Izquierdo):", metrics_list, index=0)
            with c2:
                default_index_2 = 1 if len(metrics_list) > 1 else 0
                kpi_2 = st.selectbox("Seleccionar Segundo KPI (Eje Derecho):", metrics_list, index=default_index_2)
                
            df_k1 = df_kpis[df_kpis['Medible'] == kpi_1].sort_values('Semana')
            df_k2 = df_kpis[df_kpis['Medible'] == kpi_2].sort_values('Semana')
            
            # Construcción segura del gráfico de dos ejes
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
            st.info("ℹ️ Necesitas al menos una métrica para comparar.")
    else:
        st.info("ℹ️ No hay suficiente data procesada para la comparación.")

# ------------------------------------------
# OPCIÓN 3: GESTIÓN DE TAREAS
# ------------------------------------------
elif menu_option == "📝 Gestión de Tareas":
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
    else:
        st.info("ℹ️ No se detectaron tareas formateadas en la hoja actual.")

# ------------------------------------------
# OPCIÓN 4: SCORECARD & CUMPLIMIENTO
# ------------------------------------------
elif menu_option == "🏆 Scorecard & Cumplimiento":
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
    else:
        st.info("ℹ️ No hay tareas registradas para calcular el nivel de cumplimiento.")

# ------------------------------------------
# OPCIÓN 5: EXPLORADOR SHEET (DEBUG)
# ------------------------------------------
elif menu_option == "🔍 Explorador Sheet (Debug)":
    st.subheader("🔍 Previsualización Directa del Google Sheet")
    st.caption("A continuación se muestra exactamente la tabla que la app recibe desde Google Drive:")
    st.dataframe(df_raw_preview, use_container_width=True)
