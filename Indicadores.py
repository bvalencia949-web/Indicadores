import streamlit as st
from O365 import Account
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="COAM Indicadores", layout="wide")

def get_data():
    credentials = (st.secrets["sharepoint"]["client_id"], st.secrets["sharepoint"]["client_secret"])
    account = Account(credentials, auth_flow_type='credentials', tenant_id=st.secrets["sharepoint"]["tenant_id"])
    
    if account.authenticate():
        site = account.sharepoint().get_site(st.secrets["sharepoint"]["site_url"])
        sp_list = site.get_list_by_name(st.secrets["sharepoint"]["list_name"])
        items = sp_list.get_items()
        data = [item.fields for item in items]
        return pd.DataFrame(data)
    return None

st.title("📊 Control de Consumos COAM")

if st.button("🔄 ACTUALIZAR GRÁFICOS", use_container_width=True):
    with st.spinner("Procesando datos..."):
        df_raw = get_data()
        
        if df_raw is not None and not df_raw.empty:
            # --- LIMPIEZA DE DATOS (Ajusta los nombres de columnas si son distintos) ---
            df = df_raw.copy()
            
            # 1. Convertir fecha (Ajusta 'Created' por el nombre de tu columna de fecha si tienes una)
            df['Fecha'] = pd.to_datetime(df['Created']).dt.date
            
            # 2. Convertir consumos a números (Reemplaza con los nombres exactos de tus columnas)
            # Si tus columnas se llaman distinto, cambia 'Combustible' y 'Agua' abajo:
            columnas_consumo = ['Combustible', 'Agua'] 
            for col in columnas_consumo:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # --- VISUALIZACIÓN ---
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("⛽ Consumo de Combustible")
                if 'Combustible' in df.columns:
                    fig_fuel = px.bar(df, x='Fecha', y='Combustible', color_discrete_sequence=['#EF553B'])
                    st.plotly_chart(fig_fuel, use_container_width=True)

            with col2:
                st.subheader("💧 Consumo de Agua")
                if 'Agua' in df.columns:
                    fig_water = px.line(df, x='Fecha', y='Agua', markers=True)
                    st.plotly_chart(fig_water, use_container_width=True)

            st.divider()
            st.subheader("📋 Datos Detallados")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("No se pudieron cargar los datos.")
