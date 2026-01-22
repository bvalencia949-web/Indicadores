import streamlit as st
from O365 import Account
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="COAM Indicadores", layout="wide")

def get_data():
    try:
        credentials = (st.secrets["sharepoint"]["client_id"], 
                       st.secrets["sharepoint"]["client_secret"])
        account = Account(credentials, auth_flow_type='credentials', 
                         tenant_id=st.secrets["sharepoint"]["tenant_id"])
        
        if account.authenticate():
            site = account.sharepoint().get_site(st.secrets["sharepoint"]["site_url"])
            sp_list = site.get_list_by_name(st.secrets["sharepoint"]["list_name"])
            
            # Obtenemos los items de forma directa sin usar QueryBuilder para evitar el error
            items = sp_list.get_items() 
            
            # Extraemos los datos del diccionario 'fields' de cada item
            data = []
            for item in items:
                # SharePoint guarda los datos reales dentro del atributo .fields
                data.append(item.fields)
            
            return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error técnico: {e}")
    return None

st.title("📊 Panel de Control COAM")

if st.button("🔄 ACTUALIZAR REPORTES", width='stretch'):
    with st.spinner("Sincronizando con SharePoint..."):
        df_raw = get_data()
        
        if df_raw is not None and not df_raw.empty:
            df = df_raw.copy()
            
            # Definimos los nombres de tus columnas según tus enlaces de SharePoint
            c_fuel = 'ConsumoDeclarado'
            c_water = 'Agua_Consumo'
            c_date = 'Created' # Nombre estándar interno para fecha de creación

            # 1. Limpieza de Fecha
            if c_date in df.columns:
                df['Fecha_Grafico'] = pd.to_datetime(df[c_date], errors='coerce').dt.date
            else:
                # Si no encuentra 'Created', intenta con la primera columna que parezca fecha
                df['Fecha_Grafico'] = pd.Timestamp.now().date()
            
            # 2. Limpieza de Números (Convierte los 'None' en 0 para que el gráfico no falle)
            for c in [c_fuel, c_water]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                else:
                    df[c] = 0.0

            df = df.sort_values('Fecha_Grafico')

            # --- VISUALIZACIÓN ---
            tab_g, tab_t = st.tabs(["📈 Gráficos Diarios", "📋 Tabla de Datos"])
            
            with tab_g:
                # Gráfico de Combustible
                fig_fuel = px.bar(df, x='Fecha_Grafico', y=c_fuel, 
                                 title="⛽ Consumo Diario de Combustible",
                                 color_discrete_sequence=['#EF553B'],
                                 labels={'Fecha_Grafico': 'Día', c_fuel: 'Cantidad'})
                st.plotly_chart(fig_fuel, width='stretch')
                
                # Gráfico de Agua
                fig_water = px.line(df, x='Fecha_Grafico', y=c_water, 
                                  title="💧 Consumo Diario de Agua",
                                  markers=True,
                                  labels={'Fecha_Grafico': 'Día', c_water: 'm³'})
                st.plotly_chart(fig_water, width='stretch')

            with tab_t:
                # Mostramos solo las columnas clave para verificar
                cols = [col for col in ['Fecha_Grafico', c_fuel, c_water] if col in df.columns]
                st.dataframe(df[cols], width='stretch')
        else:
            st.warning("No se encontraron datos. Verifica que los registros en SharePoint no estén vacíos.")

st.divider()
st.caption("Sistema de Indicadores COAM - v2.1")
