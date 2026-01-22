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
        
        # SOLUCIÓN: Forzamos la expansión de los campos para evitar que lleguen None
        items = sp_list.get_items(expand='fields') 
        
        data = [item.fields for item in items]
        return pd.DataFrame(data)
    return None

st.title("📊 Control de Consumos COAM")

if st.button("🔄 ACTUALIZAR DATOS Y GRÁFICOS", use_container_width=True):
    with st.spinner("Conectando con SharePoint..."):
        df = get_data()
        
        if df is not None and not df.empty:
            # Nombres confirmados por el usuario
            col_gasolina = 'ConsumoDeclarado' 
            col_agua = 'Agua_Consumo'
            # SharePoint siempre tiene 'Created' como nombre interno de fecha de creación
            col_fecha = 'Created' 

            # Limpieza y conversión de tipos
            df['Fecha_Limpia'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
            
            for c in [col_gasolina, col_agua]:
                if c in df.columns:
                    # Convertimos a número y tratamos los errores
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                else:
                    st.error(f"Error crítico: La columna '{c}' no se encuentra en la respuesta de la API.")

            # --- GRÁFICOS ---
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("⛽ Consumo de Combustible")
                # Gráfico de barras por fecha
                fig1 = px.bar(df.sort_values('Fecha_Limpia'), 
                             x='Fecha_Limpia', y=col_gasolina, 
                             labels={'Fecha_Limpia': 'Fecha', col_gasolina: 'Galones/Litros'},
                             color_discrete_sequence=['#EF553B'])
                st.plotly_chart(fig1, use_container_width=True)

            with c2:
                st.subheader("💧 Consumo de Agua")
                # Gráfico de línea por fecha
                fig2 = px.line(df.sort_values('Fecha_Limpia'), 
                              x='Fecha_Limpia', y=col_agua, 
                              labels={'Fecha_Limpia': 'Fecha', col_agua: 'm³'},
                              markers=True)
                st.plotly_chart(fig2, use_container_width=True)

            st.divider()
            st.subheader("📋 Tabla de Datos")
            st.dataframe(df[[col_fecha, col_gasolina, col_agua]].sort_values(col_fecha, ascending=False))
        else:
            st.error("No se pudieron obtener datos. Verifica si la lista tiene registros cargados.")
