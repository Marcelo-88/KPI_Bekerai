import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Fridolin - Tablero KPIs", layout="wide")

# ==========================================
# 1. FUNCION DE CARGA Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data(ttl=600)
def cargar_datos(sheet_url):
    # Cargar CSV desde Google Sheets public/compartido
    df = pd.read_csv(sheet_url)
    
    # Limpiar nombres de columnas principales
    df.columns = [str(c).strip() for c in df.columns]
    
    return df

# ==========================================
# 2. FUNCION PARA RENDERIZAR LAS TARJETAS
# ==========================================
def renderizar_tarjetas_kpi(df_filtrado, col_semana, col_semana_ant=None):
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron datos para los filtros seleccionados.")
        return

    # Obtener los Medibles únicos respetando el orden original
    medibles_unicos = df_filtrado['Medibles'].dropna().unique()

    # Generar rejilla de tarjetas (máximo 4 columnas por fila)
    num_cols = min(len(medibles_unicos), 4) if len(medibles_unicos) > 0 else 1
    cols = st.columns(num_cols)

    for idx, medible in enumerate(medibles_unicos):
        # Asignación cíclica de columna en la interfaz
        col = cols[idx % num_cols]
        
        # Filtrar datos pertenecientes únicamente a este Medible (Titular)
        df_medible = df_filtrado[df_filtrado['Medibles'] == medible]
        
        # Extraer responsable del medible
        responsable = df_medible['Quien'].dropna().iloc[0] if 'Quien' in df_medible.columns and not df_medible['Quien'].dropna().empty else "No asignado"

        with col:
            # Cabecera HTML de la Tarjeta
            card_html = f"""
            <div style="
                border: 1px solid #d6d6d6;
                border-radius: 10px;
                padding: 16px;
                margin-bottom: 20px;
                background-color: #ffffff;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
            ">
                <div style="font-weight: 800; font-size: 1.15rem; color: #800000; text-transform: uppercase; letter-spacing: 0.5px;">
                    {medible}
                </div>
                <div style="font-size: 0.85rem; color: #555555; margin-top: 4px; margin-bottom: 12px;">
                    👤 <b>Resp:</b> {responsable}
                </div>
                <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 8px 0 12px 0;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.92rem;">
            """

            total_acumulado = 0.0
            conteo_filas = 0

            # Recorrer todas las subcategorías vinculadas a este medible
            for _, row in df_medible.iterrows():
                # Nombre de la categoría
                cat_nombre = str(row['Categoria']).strip() if pd.notna(row['Categoria']) and str(row['Categoria']).strip() != '' else "General"
                
                # Obtener valor numérico de la semana seleccionada
                val_raw = row.get(col_semana, 0)
                
                # Parseo seguro a flotante
                try:
                    if pd.isna(val_raw) or str(val_raw).strip() == '' or str(val_raw).strip() == '-':
                        val_num = 0.0
                    else:
                        # Limpieza de caracteres de moneda y formato latino
                        val_clean = str(val_raw).replace('Bs', '').replace('bs', '').replace('.', '').replace(',', '.').strip()
                        val_num = float(val_clean)
                except ValueError:
                    val_num = 0.0

                total_acumulado += val_num
                conteo_filas += 1

                # Formato visual con separadores de miles
                val_fmt = f"{val_num:,.0f}".replace(',', '.')

                card_html += f"""
                    <tr style="border-bottom: 1px solid #f9f9f9;">
                        <td style="padding: 6px 0; color: #333333;">{cat_nombre}</td>
                        <td style="padding: 6px 0; text-align: right; font-weight: 600; color: #111111;">{val_fmt}</td>
                    </tr>
                """

            # Fila adicional de TOTAL si el medible posee 2 o más subcategorías
            if conteo_filas > 1:
                total_fmt = f"{total_acumulado:,.0f}".replace(',', '.')
                card_html += f"""
                    <tr style="border-top: 2px solid #800000; font-weight: 700; background-color: #fafafa;">
                        <td style="padding: 8px 0 4px 4px; color: #800000;">TOTAL {medible}</td>
                        <td style="padding: 8px 4px 4px 0; text-align: right; color: #800000; font-size: 1rem;">{total_fmt}</td>
                    </tr>
                """

            card_html += """
                </table>
            </div>
            """

            # Inyectar tarjeta en el layout
            st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# 3. APLICACION PRINCIPAL (STREAMLIT)
# ==========================================
def main():
    st.title("📌 Resumen de Indicadores Semanales")

    # URL de exportación CSV de Google Sheets
    # (Reemplazar con la URL CSV de tu documento en producción)
    SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1YmxMlgdqn0Oe38mmUF3pFBVYWgUjyxjmDdmWp-Oz1g/gviz/tq?tqx=out:csv&sheet=KPI"

    try:
        df = cargar_datos(SHEET_CSV_URL)
    except Exception as e:
        st.error(f"Error al cargar los datos desde Google Sheets: {e}")
        return

    # Detectar dinámicamente las columnas de semanas (Sem 25, Sem 26... Sem 31)
    cols_semanas = [c for c in df.columns if 'Sem' in c or 'Semana' in c]
    
    if not cols_semanas:
        # Fallback si las semanas tienen nombres exactos como fechas o indices de columna
        cols_semanas = df.columns[4:].tolist()

    # Controles superiores (Filtros)
    f_col1, f_col2, f_col3 = st.columns(3)

    with f_col1:
        semana_sel = st.selectbox("Seleccionar Semana a Inspeccionar:", options=cols_semanas, index=len(cols_semanas)-1 if cols_semanas else 0)

    with f_col2:
        deptos = ["Todos"] + list(df['Departamento'].dropna().unique()) if 'Departamento' in df.columns else ["Todos"]
        depto_sel = st.selectbox("Filtrar por Departamento:", options=deptos)

    with f_col3:
        responsables = ["Todos"] + list(df['Quien'].dropna().unique()) if 'Quien' in df.columns else ["Todos"]
        resp_sel = st.selectbox("Filtrar por Responsable:", options=responsables)

    # Filtrar el DataFrame según la selección del usuario
    df_filtrado = df.copy()

    if depto_sel != "Todos" and 'Departamento' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Departamento'] == depto_sel]

    if resp_sel != "Todos" and 'Quien' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Quien'] == resp_sel]

    st.subheader(f"Datos correspondientes a {semana_sel}")

    # Dibujar las tarjetas unificadas por Medible
    renderizar_tarjetas_kpi(df_filtrado, col_semana=semana_sel)

if __name__ == "__main__":
    main()
