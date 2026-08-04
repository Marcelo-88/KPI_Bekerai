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
    
    /* TARJETAS KPI DASHBOARD */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E0D8;
        border-radius: 16px;
        padding: 1.1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
        margin-bottom: 1rem;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .kpi-card-fallback {
        background-color: #FFFDF2;
        border: 2px dashed #E6A23C;
        border-radius: 16px;
        padding: 1.1rem;
        box-shadow: 0 4px 6px rgba(230, 162, 60, 0.1);
        margin-bottom: 1rem;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .kpi-card-header {
        font-size: 0.78rem;
        font-weight: 700;
        color: #555555;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
        height: 2.2rem;
        overflow: hidden;
    }
    .kpi-card-val {
        font-size: 1.65rem;
        font-weight: 800;
        color: #801B2B;
        margin-bottom: 0.4rem;
        font-variant-numeric: tabular-nums;
    }
    .kpi-card-footer {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        font-size: 0.76rem;
        border-top: 1px solid #F0EAE1;
        padding-top: 0.5rem;
    }
    .badge-up { color: #2E7D32; font-weight: 600; }
    .badge-down { color: #C62828; font-weight: 600; }
    .badge-neutral { color: #757575; font-weight: 500; }
    .badge-warning { color: #D97706; font-weight: 700; background: #FEF3C7; padding: 3px 6px; border-radius: 4px; display: inline-block; font-size: 0.72rem; }
    
    .kpi-resp-tag {
        font-size: 0.73rem;
        color: #A67C1E;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }

    /* ESTILO PARA TARJETAS DE COMPARACIÓN COMPACTAS */
    .compare-card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #801B2B;
        margin-bottom: 0.5rem;
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
# 3. HELPER PARA GRAFICAR MULTI-KPI CON DOBLE EJE
# ==========================================
def render_multi_kpi_chart(df_kpis, kpi_list, title="Comparativa Multi-KPI", height=500):
    fig = go.Figure()
    colors = ['#801B2B', '#E6A23C', '#2E7D32', '#1E88E5', '#8E24AA', '#D81B60', '#00ACC1', '#F4511E', '#3949AB', '#43A047']
    
    # Determinar rangos para ver si necesitamos doble eje
    max_vals = {}
    for kpi in kpi_list:
        sub_df = df_kpis[df_kpis['Medible'] == kpi]
        if not sub_df.empty:
            max_vals[kpi] = sub_df['Valor'].max()
            
    if not max_vals:
        return fig
        
    overall_max = max(max_vals.values()) if max_vals.values() else 1
    
    for idx, kpi in enumerate(kpi_list):
        sub_df = df_kpis[df_kpis['Medible'] == kpi]
        if sub_df.empty:
            continue
            
        color = colors[idx % len(colors)]
        max_v = max_vals.get(kpi, 0)
        
        # Si la métrica es muy grande respecto a las otras (ej: Alcance en Millones vs Ventas), asignar al Eje Y Secundario
        use_secondary_axis = (overall_max > 100000 and max_v > 100000 and max_v > min(max_vals.values()) * 10)
        
        fig.add_trace(go.Scatter(
            x=sub_df['Semana'],
            y=sub_df['Valor'],
            name=str(kpi),
            mode='lines+markers',
            line=dict(color=color, width=3),
            marker=dict(size=6),
            yaxis="y2" if use_secondary_axis else "y"
        ))
        
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#801B2B")),
        xaxis=dict(title="Semana"),
        yaxis=dict(title="Valores Estándar", showgrid=True),
        yaxis2=dict(title="Escala Grande (Secundaria)", overlaying="y", side="right", showgrid=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#FFFFFF',
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig

# ==========================================
# 4. BARRA LATERAL (MENÚ PRINCIPAL Y FILTROS)
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
# 5. CONTENIDO SEGÚN MÓDULO SELECCIONADO
# ==========================================

# MODULO 1: DASHBOARDS KPIs
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
        
        st.markdown(f"##### Datos de **{selected_week}**")
        
        if len(metrics_list) > 0:
            cols = st.columns(4)
            for idx, kpi in enumerate(metrics_list):
                df_kpi_series = df_kpis[df_kpis['Medible'] == kpi]
                resp = df_kpi_series['Responsable'].dropna().values[0] if not df_kpi_series.empty else "-"
                
                # BUSCAR ÚLTIMO DATO VÁLIDO (>0)
                val_curr = 0.0
                actual_data_week = selected_week
                is_fallback = False
                
                for w_idx in range(current_week_idx, -1, -1):
                    w_name = semanas_unicas[w_idx]
                    row_w = df_kpi_series[df_kpi_series['Semana'] == w_name]
                    if not row_w.empty:
                        v = float(row_w['Valor'].values[0])
                        if v > 0:
                            val_curr = v
                            actual_data_week = w_name
                            if w_idx < current_week_idx:
                                is_fallback = True
                            break
                            
                # BUSCAR DATO ANTERIOR
                val_prev = None
                prev_w_name = ""
                actual_week_idx_found = semanas_unicas.index(actual_data_week) if actual_data_week in semanas_unicas else -1
                if actual_week_idx_found > 0:
                    prev_w_name = semanas_unicas[actual_week_idx_found - 1]
                    row_prev = df_kpi_series[df_kpi_series['Semana'] == prev_w_name]
                    if not row_prev.empty:
                        val_prev = float(row_prev['Valor'].values[0])
                
                # Variación % vs Semana Anterior
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
                    
                # Variación % vs Promedio
                valid_vals = df_kpi_series[df_kpi_series['Valor'] > 0]['Valor']
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
                
                # Formateo
                if val_curr >= 1000 or val_curr % 1 == 0:
                    val_formatted = f"{val_curr:,.0f}"
                else:
                    val_formatted = f"{val_curr:,.2f}"
                
                if is_fallback:
                    card_class = "kpi-card-fallback"
                    fallback_tag = f'<div style="margin-bottom:0.3rem;"><span class="badge-warning">⚠️ DATO CORRESPONDE A {actual_data_week}</span></div>'
                else:
                    card_class = "kpi-card"
                    fallback_tag = ""
                
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

# ------------------------------------------
# MODULO 2: COMPARADOR KPI vs KPI (TARJETAS + MODAL AMPLIADO)
# ------------------------------------------
elif menu_option == "🔀 Comparador KPI vs KPI":
    st.subheader("🔀 Análisis Comparativo Multi-KPI (Tarjetas Interactivas)")
    st.caption("💡 *Tip: Haz clic en las líneas de la leyenda para ocultar o mostrar datos. Abre cada tarjeta para ver la gráfica ampliada.*")

    if not df_kpis.empty and 'Medible' in df_kpis.columns:
        
        # 1. DEFINICIÓN DE GRUPOS DE GRÁFICAS PREDEFINIDAS
        kpi_g1 = ["VENTAS", "PAGO PROVEEDORES MP", "TOTAL C X P PROVEEDORES MP", "BALANCE EFECTIVO"]
        
        kpi_g2 = [
            "PROD. TORTAS", "PROD. SALADO", "PROD. PANADERIA", "PROD. PASTELES INDIVIDUALES", "PROD. POSTRES ENTEROS",
            "ENVIO TORTAS", "ENVIO SALADO", "ENVIO PANADERIA", "ENVIO PASTELES INDIVIDUALES", "ENVIO POSTRES ENTEROS",
            "VENTAS TORTAS", "VENTAS SALADO", "VENTAS PANADERIA", "VENTAS PASTELES INDIVIDUALES", "VENTAS POSTRES ENTEROS",
            "BAJAS TORTAS", "BAJAS SALADO", "BAJAS PANADERIA", "BAJAS PASTELES INDIVIDUALES", "BAJAS POSTRES ENTEROS"
        ]
        
        kpi_g3 = [
            "INVERSION RRSS", 
            "ALCANCE IG&FB + REPRD. VISTAS TIKTOK", 
            "PAGO PROVEEDORES MARKETING", 
            "VENTAS"
        ]

        # GRID DE TARJETAS (2 COLUMNAS POR FILA)
        c1, c2 = st.columns(2)
        
        # --- TARJETA 1: FINANZAS & FLUSO ---
        with c1:
            st.markdown('<div class="compare-card-title">💵 1. Ventas vs Pagos vs CxP vs Efectivo</div>', unsafe_allow_html=True)
            fig1 = render_multi_kpi_chart(df_kpis, kpi_g1, title="Ventas vs Pagos vs CxP vs Efectivo", height=280)
            st.plotly_chart(fig1, use_container_width=True)
            
            with st.expander("🔍 **Ampliar Gráfica 1 (Pantalla Completa)**"):
                fig1_large = render_multi_kpi_chart(df_kpis, kpi_g1, title="1. Ventas vs Pagos vs CxP vs Balance Efectivo", height=600)
                st.plotly_chart(fig1_large, use_container_width=True)

        # --- TARJETA 3: MARKETING & VENTAS ---
        with c2:
            st.markdown('<div class="compare-card-title">📣 3. Marketing vs Alcance vs Ventas</div>', unsafe_allow_html=True)
            fig3 = render_multi_kpi_chart(df_kpis, kpi_g3, title="Inversión RRSS vs Alcance vs Ventas", height=280)
            st.plotly_chart(fig3, use_container_width=True)
            
            with st.expander("🔍 **Ampliar Gráfica 3 (Pantalla Completa)**"):
                fig3_large = render_multi_kpi_chart(df_kpis, kpi_g3, title="3. Inversión RRSS vs Alcance TikTok/Meta vs Gasto Mktg vs Ventas", height=600)
                st.plotly_chart(fig3_large, use_container_width=True)

        st.markdown("---")
        c3, c4 = st.columns(2)

        # --- TARJETA 2: PRODUCCIÓN vs ENVÍO vs VENTA vs BAJAS ---
        with c3:
            st.markdown('<div class="compare-card-title">🍰 2. Producción vs Envíos vs Ventas vs Bajas</div>', unsafe_allow_html=True)
            fig2 = render_multi_kpi_chart(df_kpis, kpi_g2, title="Flujo Completo de Productos", height=280)
            st.plotly_chart(fig2, use_container_width=True)
            
            with st.expander("🔍 **Ampliar Gráfica 2 (Pantalla Completa)**"):
                fig2_large = render_multi_kpi_chart(df_kpis, kpi_g2, title="2. Producción vs Envíos vs Ventas vs Bajas (Todas las líneas)", height=650)
                st.plotly_chart(fig2_large, use_container_width=True)

        # --- TARJETA 4: COMPARADOR PERSONALIZADO (A MEDIDA) ---
        with c4:
            st.markdown('<div class="compare-card-title">🛠️ 4. Comparador Personalizado</div>', unsafe_allow_html=True)
            all_metrics_available = sorted([m for m in df_kpis['Medible'].dropna().unique() if str(m) != 'nan'])
            
            selected_custom = st.multiselect(
                "Selecciona las métricas a comparar:",
                all_metrics_available,
                default=all_metrics_available[:2] if len(all_metrics_available) >= 2 else all_metrics_available
            )
            
            if selected_custom:
                fig4 = render_multi_kpi_chart(df_kpis, selected_custom, title="Comparativa Personalizada", height=280)
                st.plotly_chart(fig4, use_container_width=True)
                
                with st.expander("🔍 **Ampliar Gráfica Personalizada (Pantalla Completa)**"):
                    fig4_large = render_multi_kpi_chart(df_kpis, selected_custom, title="Comparativa Personalizada Selección Libre", height=600)
                    st.plotly_chart(fig4_large, use_container_width=True)
            else:
                st.info("Por favor selecciona al menos una métrica para mostrar la gráfica.")

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
