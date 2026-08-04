import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
from collections import Counter

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Tablero Integrado - Clima, Ventas & EOS",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS optimizados para evitar desbordamientos y corregir renderizado
st.markdown("""
<style>
    /* Estilos generales */
    .main { padding: 1rem 2rem; }
    
    /* Tarjetas de Métricas Climáticas */
    .weather-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        box-sizing: border-box;
    }
    .weather-card h4 {
        margin-top: 0;
        color: #1f2937;
        font-size: 1.1rem;
    }
    .weather-metric-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 0.9rem;
    }
    .weather-val {
        font-weight: bold;
        color: #111827;
    }

    /* Contenedor de Festivos */
    .festivos-container {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
        box-sizing: border-box;
    }
    
    /* Ajustes para tarjetas de análisis */
    .analysis-container {
        background-color: #f0f7ff;
        border: 1px solid #bae6fd;
        border-radius: 8px;
        padding: 16px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNCIONES AUXILIARES & CLIMA (API)
# ==========================================
WMO_CODES = {
    0: ("Despejado / Soleado", "☀️"),
    1: ("Principalmente Despejado", "🌤️"),
    2: ("Parcialmente Nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla con Escarcha", "🌫️"),
    51: ("Llovizna Ligera", "🌦️"),
    53: ("Llovizna Moderada", "🌦️"),
    55: ("Llovizna Densa", "🌧️"),
    61: ("Lluvia Ligera", "🌧️"),
    63: ("Lluvia Moderada", "🌧️"),
    65: ("Lluvia Fuerte", "🌧️"),
    80: ("Chubascos Ligeros", "🌦️"),
    81: ("Chubascos Moderados", "🌧️"),
    82: ("Chubascos Violentos", "⛈️")
}

@st.cache_data(ttl=3600)
def obtener_datos_clima(lat=-33.4489, lon=-70.6693):
    """Obtiene el pronóstico meteorológico a 14 días desde Open-Meteo."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=auto&forecast_days=14"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        df_clima = pd.DataFrame({
            'fecha': pd.to_datetime(data['daily']['time']),
            'temp_max': data['daily']['temperature_2m_max'],
            'temp_min': data['daily']['temperature_2m_min'],
            'temp_mean': data['daily']['temperature_2m_mean'],
            'precipitacion': data['daily']['precipitation_sum'],
            'code': data['daily']['weathercode']
        })
        return df_clima
    except Exception as e:
        st.error(f"Error al conectar con el servicio meteorológico: {e}")
        return pd.DataFrame()

def obtener_resumen_semanal(df_semana):
    """Calcula métricas agregadas y clima predominante para una semana dada."""
    if df_semana.empty:
        return {}
    
    t_min = df_semana['temp_min'].min()
    t_max = df_semana['temp_max'].max()
    t_avg = df_semana['temp_mean'].mean()
    
    # Clima predominante (Moda de WMO)
    code_counts = Counter(df_semana['code'])
    most_common_code = code_counts.most_common(1)[0][0]
    estado, icono = WMO_CODES.get(most_common_code, ("Variable", "🌡️"))
    
    return {
        "min": t_min,
        "max": t_max,
        "avg": t_avg,
        "estado": estado,
        "icono": icono
    }

# ==========================================
# 3. MOCK DATA / GOOGLE SHEETS DUMMY
# ==========================================
@st.cache_data
def cargar_datos_comerciales():
    """Genera dataset simulado de ventas y metas para mantener integridad."""
    fechas = pd.date_range(end=datetime.today(), periods=60)
    data = []
    for f in fechas:
        data.append({
            'fecha': f,
            'ventas_reales': 1500000 + (f.day * 15000) + (100000 if f.weekday() >= 5 else 0),
            'meta_ventas': 1600000,
            'transacciones': 320 + f.day,
            'ticket_promedio': 4800
        })
    return pd.DataFrame(data)

# ==========================================
# 4. ESTRUCTURA PRINCIPAL DEL DASHBOARD
# ==========================================

st.title("🌤️ Análisis Clima, Ventas & EOS")
st.markdown("Tablero de gestión comercial interactivo y monitoreo meteorológico.")

# Carga de datos
df_clima = obtener_datos_clima()
df_ventas = cargar_datos_comerciales()

# Lista de festivos próximos (simulación / API)
festivos_proximos = [
    {"fecha": "15 Ago 2026", "nombre": "Asunción de la Virgen", "dias_faltantes": 11},
    {"fecha": "18 Sep 2026", "nombre": "Independencia Nacional", "dias_faltantes": 45},
    {"fecha": "19 Sep 2026", "nombre": "Día de las Glorias del Ejército", "dias_faltantes": 46}
]

# --- SECCIÓN: CLIMA & PRONÓSTICO A 2 SEMANAS ---
st.subheader("📌 Monitoreo Climatológico y Proyección de 2 Semanas")

if not df_clima.empty:
    # Dividir datos en Semana 1 (Días 1-7) y Semana 2 (Días 8-14)
    sem1_df = df_clima.iloc[0:7]
    sem2_df = df_clima.iloc[7:14]
    
    resumen_sem1 = obtener_resumen_semanal(sem1_df)
    resumen_sem2 = obtener_resumen_semanal(sem2_df)
    
    col_w1, col_w2, col_fest = st.columns([1, 1, 1])
    
    with col_w1:
        st.markdown(f"""
        <div class="weather-card">
            <h4>🗓️ Proyección Semana 1 (Días 1-7)</h4>
            <div style="font-size: 1.5rem; text-align: center; margin: 10px 0;">
                {resumen_sem1['icono']} <b>{resumen_sem1['estado']}</b>
            </div>
            <hr style="margin: 8px 0;">
            <div class="weather-metric-row"><span>Temp. Mínima:</span><span class="weather-val">{resumen_sem1['min']:.1f} °C</span></div>
            <div class="weather-metric-row"><span>Temp. Máxima:</span><span class="weather-val">{resumen_sem1['max']:.1f} °C</span></div>
            <div class="weather-metric-row"><span>Temp. Promedio:</span><span class="weather-val">{resumen_sem1['avg']:.1f} °C</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_w2:
        st.markdown(f"""
        <div class="weather-card" style="border-left-color: #28a745;">
            <h4>🗓️ Proyección Semana 2 (Días 8-14)</h4>
            <div style="font-size: 1.5rem; text-align: center; margin: 10px 0;">
                {resumen_sem2['icono']} <b>{resumen_sem2['estado']}</b>
            </div>
            <hr style="margin: 8px 0;">
            <div class="weather-metric-row"><span>Temp. Mínima:</span><span class="weather-val">{resumen_sem2['min']:.1f} °C</span></div>
            <div class="weather-metric-row"><span>Temp. Máxima:</span><span class="weather-val">{resumen_sem2['max']:.1f} °C</span></div>
            <div class="weather-metric-row"><span>Temp. Promedio:</span><span class="weather-val">{resumen_sem2['avg']:.1f} °C</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col_fest:
        st.markdown('<div class="festivos-container">', unsafe_allow_html=True)
        st.markdown("#### 🎉 Próximos Festivos")
        for f in festivos_proximos:
            st.markdown(f"**{f['fecha']}**: {f['nombre']} `({f['dias_faltantes']} días)`")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- GRÁFICO COMBINADO DE PRONÓSTICO ---
    fig_clima = make_subplots(specs=[[{"secondary_y": True}]])

    fig_clima.add_trace(
        go.Scatter(
            x=df_clima['fecha'], 
            y=df_clima['temp_max'], 
            name="Temp. Máxima (°C)", 
            line=dict(color='#ef4444', width=3)
        ),
        secondary_y=False
    )
    fig_clima.add_trace(
        go.Scatter(
            x=df_clima['fecha'], 
            y=df_clima['temp_min'], 
            name="Temp. Mínima (°C)", 
            line=dict(color='#3b82f6', width=2, dash='dash')
        ),
        secondary_y=False
    )
    fig_clima.add_trace(
        go.Bar(
            x=df_clima['fecha'], 
            y=df_clima['precipitacion'], 
            name="Precipitación (mm)", 
            marker_color='#60a5fa', 
            opacity=0.4
        ),
        secondary_y=True
    )

    fig_clima.update_layout(
        title="<b>Pronóstico Meteorológico Extendido (14 Días)</b>",
        height=380,
        margin=dict(l=20, r=20, t=80, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.12,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified"
    )

    fig_clima.update_xaxes(title_text="Fecha")
    fig_clima.update_yaxes(title_text="Temperatura (°C)", secondary_y=False)
    fig_clima.update_yaxes(title_text="Precipitación (mm)", secondary_y=True)

    st.plotly_chart(fig_clima, use_container_width=True)

# --- SECCIÓN CUALITATIVA / INTERPRETACIÓN COMERCIAL (REDESEÑADA NATIVA) ---
with st.container():
    st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
    st.subheader("💡 Opinión Analítica e Interpretación Comercial")
    
    st.markdown("""
    * **Impacto en Tráfico**: Las variaciones de temperatura esperadas para la Semana 1 favorecen un comportamiento estable en tiendas físicas.
    * **Estrategia de Inventario**: Ante la probabilidad de lloviznas hacia la Semana 2, se sugiere reforzar la exhibición de productos de temporada en zonas de alta visibilidad.
    * **Planificación Operativa**: Se recomienda coordinar la dotación de personal en salas considerando los picos de afluencia asociados a los días festivos cercanos.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ==========================================
# 5. COMPARADOR MULTI-EJE Y SCORECARD EOS
# ==========================================
st.subheader("📊 Análisis Comercial y Scorecard EOS")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("#### Comparativo Histórico: Ventas vs. Metas")
    fig_ventas = go.Figure()
    fig_ventas.add_trace(go.Bar(x=df_ventas['fecha'], y=df_ventas['ventas_reales'], name="Ventas Reales ($)", marker_color='#10b981'))
    fig_ventas.add_trace(go.Scatter(x=df_ventas['fecha'], y=df_ventas['meta_ventas'], name="Meta Diaria ($)", line=dict(color='#f59e0b', width=2, dash='dot')))
    
    fig_ventas.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_ventas, use_container_width=True)

with col_right:
    st.markdown("#### Scorecard EOS")
    
    cumplimiento_ventas = (df_ventas['ventas_reales'].sum() / df_ventas['meta_ventas'].sum()) * 100
    
    st.metric(
        label="Cumplimiento de Ventas", 
        value=f"{cumplimiento_ventas:.1f}%", 
        delta=f"{cumplimiento_ventas - 100:.1f}% vs Meta"
    )
    
    st.metric(
        label="Ticket Promedio Acumulado", 
        value=f"${df_ventas['ticket_promedio'].mean():,.0f}", 
        delta="+$150 vs mes anterior"
    )

    st.markdown("**Rocas del Trimestre (Q3):**")
    st.progress(0.85, text="Optimización Stock Clima (85%)")
    st.progress(0.60, text="Implementación Campaña Festivos (60%)")
