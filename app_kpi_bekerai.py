import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    
    .kpi-card {
        background-color: #FFFFFF; border: 1px solid #E6E1D7; border-radius: 16px;
        padding: 1.1rem; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04); margin-bottom: 1rem;
        min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;
    }
    .kpi-card-header { font-size: 0.82rem; font-weight: 700; color: #4A4644; text-transform: uppercase; height: 2.2rem; }
    .kpi-card-val { font-size: 1.65rem; font-weight: 800; color: #7A1C29; margin-bottom: 0.4rem; }
    .kpi-card-footer { font-size: 0.78rem; border-top: 1px solid #F0ECE3; padding-top: 0.5rem; }
    .badge-up { color: #27AE60; font-weight: 600; }
    .badge-down { color: #C0392B; font-weight: 600; }
    .badge-neutral { color: #7F8C8D; font-weight: 500; }
    .compare-card-title { font-size: 1.05rem; font-weight: 700; color: #7A1C29; margin-bottom: 0.5rem; }
</style>
"""
st.markdown(FRIDOLIN_CSS, unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y CORRECCIÓN DE DATOS DEL SHEET
# ==========================================
GOOGLE_SHEET_ID = "1YmxMIgdqn0Oe38mmUF3pFBVyWgUjyyxjmDdmWp-Oz1g"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=xlsx"

def parse_custom_number(val):
    if pd.isna(val) or val == "" or str(val).strip() == "":
        return None  # Retornamos None para no falsear ceros en semanas no registradas
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
            
            # --- AUTO-CORRECCIÓN DE ERRORES DE CRUCE DE FILAS EN GOOGLE SHEET ---
            # Si "Envio Salados" tiene > 20,000 (claramente es Producción Salados cargado en la fila equivocada)
            mask_swap = (df_kpi_long['Medible'] == 'Envio Salados') & (df_kpi_long['Valor'] > 20000)
            if mask_swap.any():
                df_kpi_long.loc[mask_swap, 'Medible'] = 'Prod Salado'

        else:
            df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])
    else:
        df_kpi_long = pd.DataFrame(columns=['Responsable', 'Departamento', 'Medible', 'Semana', 'Valor'])

    # Tareas
    df_tareas_raw = sheets.get('Tareas', pd.DataFrame())
    df_tasks = df_tareas_raw if not df_tareas_raw.empty else pd.DataFrame()

    return df_kpi_long, df_tasks

# ==========================================
# 3. HELPER DE GRÁFICAS
# ==========================================
def render_multi_kpi_chart(df_kpis, kpi_list, title="Comparativa Multi-KPI", height=420, unit_label="Valores"):
    fig = go.Figure()
    
    existing_kpis = [k for k in kpi_list if k in df_kpis['Medible'].values]
    
    if not existing_kpis:
        fig.add_annotation(
            text="Selecciona al menos una categoría para visualizar",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#7A1C29")
        )
        fig.update_layout(height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF')
        return fig

    for idx, kpi in enumerate(existing_kpis):
        # Descartar semanas donde no existe registro (None / NaN) para evitar caídas a 0
        sub_df = df_kpis[(df_kpis['Medible'] == kpi) & (df_kpis['Valor'].notna())].copy()
        
        if sub_df.empty:
            continue
            
        color = PASTEL_COLORS[idx % len(PASTEL_COLORS)]
        is_money = "Bs" in unit_label or any(m in kpi.upper() for m in ['VENTAS', 'PAGO', 'C X P', 'EFECTIVO'])
        val_prefix = "Bs " if is_money else ""
        
        hover_template = (
            f"<b>{kpi}</b><br>"
            "🗓️ %{x}<br>"
            f"📊 Valor: <b>{val_prefix}%{{y:,.2f}}</b>"
            "<extra></extra>"
        )
        
        fig.add_trace(go.Scatter(
            x=sub_df['Semana'],
            y=sub_df['Valor'],
            name=str(kpi),
            mode='lines+markers',
            line=dict(color=color, width=3),
            marker=dict(size=7, color=color, symbol='circle'),
            hovertemplate=hover_template,
            connectgaps=False
        ))
        
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=15, color="#7A1C29"), x=0, y=0.98),
        xaxis=dict(title=None, tickangle=-45, showgrid=True, gridcolor="#EFECE6"),
        yaxis=dict(title=dict(text=unit_label, font=dict(size=12, color="#4A4644")), showgrid=True, gridcolor="#EFECE6", tickformat=",.0f", autorange=True),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
        height=height, hovermode="closest",
        legend=dict(orientation="h", yanchor="top", y=-0.28, xanchor="center", x=0.5, bgcolor="rgba(255,255,255,0.85)", bordercolor="#DFD9CE", borderwidth=1),
        margin=dict(l=55, r=30, t=50, b=110)
    )
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
menu_option = st.sidebar.radio("Selecciona un Módulo:", ["📊 Dashboards KPIs", "🔀 Comparador KPI vs KPI", "🔍 Explorador Sheet (Debug)"])

if st.sidebar.button("🔄 Actualizar Datos Ahora", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.success("¡Datos actualizados!")

try:
    df_kpis, df_tasks = load_data()
except Exception as e:
    st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
    st.stop()

st.markdown('<div class="main-header"><h1>FRIDOLIN - TABLERO CONTROL EOS & KPIs</h1><p>Monitoreo Semanal Bekerai 2026</p></div>', unsafe_allow_html=True)

# ==========================================
# 5. MÓDULO COMPARADOR DE KPIS
# ==========================================
if menu_option == "🔀 Comparador KPI vs KPI":
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

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="compare-card-title">💵 1. Finanzas en Bolivianos</div>', unsafe_allow_html=True)
            fig1 = render_multi_kpi_chart(df_kpis, kpi_g1, title="Finanzas & Flujo de Caja", height=380, unit_label="Monto en Bs")
            st.plotly_chart(fig1, use_container_width=True, key="card_1_main")

        with c2:
            st.markdown('<div class="compare-card-title">🍰 2. Producción, Envíos y Bajas por Categoría</div>', unsafe_allow_html=True)
            categorias_bekerai = ["Salados", "Tortas", "Pasteles Individuales", "Postres Enteros", "Panaderia"]
            selected_cats = st.multiselect("Filtrar Categorías:", categorias_bekerai, default=["Salados", "Tortas"])

            kpi_g2 = find_kpis_exact_or_keyword(selected_cats) if selected_cats else []
            fig2 = render_multi_kpi_chart(df_kpis, kpi_g2, title="Flujo de Categorías Seleccionadas", height=380, unit_label="Unidades")
            st.plotly_chart(fig2, use_container_width=True, key="card_2_main")
            
            if st.button("🔍 Maximizar Gráfico 2", key="btn_max_2", use_container_width=True):
                show_full_graph_dialog(df_kpis, kpi_g2, "Flujo de Categorías Seleccionadas", unit_label="Unidades")

elif menu_option == "📊 Dashboards KPIs":
    st.info("Ingresa al menú de la izquierda para explorar los gráficos comparativos de la app.")
elif menu_option == "🔍 Explorador Sheet (Debug)":
    st.subheader("🔍 Previsualización de Datos Procesados")
    st.dataframe(df_kpis, use_container_width=True)
