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
        
        # Obtenemos los items de forma estándar
        items = sp_list.get_items() 
        
        # Extraemos los campos asegurando que existan
        rows = []
        for item in items:
            rows.append(item.fields)
            
        return pd.DataFrame(rows)
    return None

st.title("📊 Control de Consumos COAM")

if st.button("🔄 ACTUALIZAR DATOS Y GRÁFICOS", use_container_width=True):
    with st.spinner("Conectando con SharePoint..."):
        df = get_data()
        
        if df is not None and not df.empty:
            # Columnas confirmadas por tus enlaces internos
            col_gasolina = 'ConsumoDeclarado' 
            col_agua = 'Agua_Consumo'
            col_fecha = 'Created' 

            # Limpieza y conversión
            # Convertimos la fecha y ordenamos para que el gráfico sea cronológico
            df['Fecha_Limpia'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
            df = df.sort_values('Fecha_Limpia')

            # Convertimos consumos a números (importante para que el gráfico suba y baje)
            for c in [col_gasolina, col_agua]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            # --- RENDERIZADO DE GRÁFICOS ---
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("⛽ Consumo de Combustible")
                fig1 = px.bar(df, x='Fecha_Limpia', y=col_gasolina, 
                             color_discrete_sequence=['#EF553B'],
                             labels={'Fecha_Limpia': 'Día', col_gasolina: 'Consumo'})
                st.plotly_chart(fig1, use_container_width=True)

            with c2:
                st.subheader("💧 Consumo de Agua")
                fig2 = px.line(df, x='Fecha_Limpia', y=col_agua, 
                              markers=True,
                              labels={'Fecha_Limpia': 'Día', col_agua: 'm³'})
                st.plotly_chart(fig2, use_container_width=True)

            st.divider()
            st.subheader("📋 Tabla de Verificación")
            # Mostramos solo las columnas que nos interesan para validar
            st.dataframe(df[['Fecha_Limpia', col_gasolina, col_agua]], use_container_width=True)
            
        else:
            st.error("No se detectaron datos. Asegúrate de que la lista en SharePoint tenga registros.")
