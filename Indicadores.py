import streamlit as st
from O365 import Account
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="COAM Indicadores", layout="wide")

def get_data():
    credentials = (st.secrets["sharepoint"]["client_id"], 
                   st.secrets["sharepoint"]["client_secret"])
    
    account = Account(credentials, 
                     auth_flow_type='credentials', 
                     tenant_id=st.secrets["sharepoint"]["tenant_id"])
    
    if account.authenticate():
        site = account.sharepoint().get_site(st.secrets["sharepoint"]["site_url"])
        sp_list = site.get_list_by_name(st.secrets["sharepoint"]["list_name"])
        items = sp_list.get_items() 
        return pd.DataFrame([item.fields for item in items])
    return None

st.title("📊 Control de Consumos COAM")

if st.button("🔄 ACTUALIZAR DATOS Y GRÁFICOS", use_container_width=True):
    with st.spinner("Sincronizando con SharePoint..."):
        df = get_data()
        
        if df is not None and not df.empty:
            # --- MAPEO AUTOMÁTICO DE COLUMNAS ---
            # Buscamos la columna de fecha (Created o alguna que contenga 'Time' o 'Date')
            col_fecha = next((c for c in df.columns if 'Created' in c or 'Modified' in c), df.columns[0])
            
            # Buscamos combustible y agua por aproximación
            col_gas = next((c for c in df.columns if 'ConsumoDeclarado' in c), None)
            col_agua = next((c for c in df.columns if 'Agua_Consumo' in c), None)

            # Limpieza de Fecha
            df['Fecha_Display'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
            df = df.sort_values('Fecha_Display')

            # Conversión de Números
            for c in [col_gas, col_agua]:
                if c and c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            # --- RENDERIZADO ---
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⛽ Consumo de Combustible")
                if col_gas:
                    fig1 = px.bar(df, x='Fecha_Display', y=col_gas, color_discrete_sequence=['#EF553B'])
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning("No se detectó columna de combustible")

            with c2:
                st.subheader("💧 Consumo de Agua")
                if col_agua:
                    fig2 = px.line(df, x='Fecha_Display', y=col_agua, markers=True)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning("No se detectó columna de agua")

            st.divider()
            st.subheader("📋 Verificación de Columnas Internas")
            st.write("Si los gráficos salen vacíos, verifica los nombres aquí:")
            st.dataframe(df.head(10)) # Mostramos los datos reales para que los veas
            
        else:
            st.error("No se recibieron datos de SharePoint.")
