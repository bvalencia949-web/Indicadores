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
            
            # FORZAMOS la carga de campos específicos para evitar el "None"
            # SharePoint requiere a veces expandir los campos de la lista
            query = sp_list.new_query()
            items = sp_list.get_items(query=query) 
            
            # Recolectamos datos asegurando que leemos el diccionario 'fields'
            data = []
            for item in items:
                # Accedemos directamente a la propiedad fields del objeto item
                data.append(item.fields)
            
            return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
    return None

st.title("📊 Panel de Control COAM")

if st.button("🔄 ACTUALIZAR REPORTES", width='stretch'):
    with st.spinner("Sincronizando datos..."):
        df_raw = get_data()
        
        if df_raw is not None and not df_raw.empty:
            df = df_raw.copy()
            
            # Nombres exactos de tus columnas en SharePoint
            c_fuel = 'ConsumoDeclarado'
            c_water = 'Agua_Consumo'
            c_date = 'Created'

            # 1. Procesar Fecha (Si Created viene null, usamos la fecha actual como respaldo)
            if c_date in df.columns:
                df['Fecha_Limpia'] = pd.to_datetime(df[c_date], errors='coerce').dt.date
            else:
                df['Fecha_Limpia'] = pd.Timestamp.now().date()
            
            # 2. Procesar Números (Convertir los 'None' en 0)
            for c in [c_fuel, c_water]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                else:
                    df[c] = 0.0

            df = df.sort_values('Fecha_Limpia')

            # --- VISTA DE PANELES ---
            t1, t2 = st.tabs(["📈 Gráficos", "📋 Tabla de Datos"])
            
            with t1:
                # Combustible
                fig_f = px.bar(df, x='Fecha_Limpia', y=c_fuel, 
                              title="⛽ Consumo Diario de Combustible",
                              color_discrete_sequence=['#EF553B'],
                              labels={'Fecha_Limpia': 'Día', c_fuel: 'Cantidad'})
                st.plotly_chart(fig_f, width='stretch')
                
                # Agua
                fig_w = px.line(df, x='Fecha_Limpia', y=c_water, 
                               title="💧 Consumo Diario de Agua",
                               markers=True,
                               labels={'Fecha_Limpia': 'Día', c_water: 'm³'})
                st.plotly_chart(fig_w, width='stretch')

            with t2:
                # Mostramos la tabla con los datos ya procesados (sin nulls)
                cols_to_show = [col for col in ['Fecha_Limpia', c_fuel, c_water] if col in df.columns]
                st.dataframe(df[cols_to_show], width='stretch')
        else:
            st.warning("No se encontraron datos. Verifica que la lista tenga registros con valores.")

st.divider()
st.caption("COAM Perú - Sistema Automatizado")
