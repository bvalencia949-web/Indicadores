import streamlit as st
from O365 import Account
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="COAM Indicadores", layout="wide")

def get_data():
    try:
        credentials = (st.secrets["sharepoint"]["client_id"], 
                       st.secrets["sharepoint"]["client_secret"])
        
        account = Account(credentials, 
                         auth_flow_type='credentials', 
                         tenant_id=st.secrets["sharepoint"]["tenant_id"])
        
        if account.authenticate():
            site = account.sharepoint().get_site(st.secrets["sharepoint"]["site_url"])
            sp_list = site.get_list_by_name(st.secrets["sharepoint"]["list_name"])
            items = sp_list.get_items() 
            
            # Convertimos a DataFrame
            df = pd.DataFrame([item.fields for item in items])
            return df
    except Exception as e:
        st.error(f"Error en la conexión: {e}")
    return None

st.title("📊 Panel de Control COAM")
st.write("Sincronizado con SharePoint en tiempo real")

if st.button("🔄 ACTUALIZAR DATOS Y GENERAR GRÁFICOS", use_container_width=True):
    with st.spinner("Leyendo información de COAM..."):
        df = get_data()
        
        if df is not None and not df.empty:
            # --- LÓGICA DE DETECCIÓN AUTOMÁTICA DE COLUMNAS ---
            # Buscamos columnas que contengan los nombres clave
            col_fecha = next((c for c in df.columns if 'Created' in c or 'Modified' in c), None)
            col_gas = next((c for c in df.columns if 'ConsumoDeclarado' in c), None)
            col_agua = next((c for c in df.columns if 'Agua_Consumo' in c), None)

            # --- PROCESAMIENTO DE DATOS ---
            # 1. Procesar Fecha
            if col_fecha:
                df['Fecha_Display'] = pd.to_datetime(df[col_fecha], errors='coerce')
                df = df.sort_values('Fecha_Display')
            
            # 2. Procesar Números (Combustible y Agua)
            for col_name in [col_gas, col_agua]:
                if col_name:
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)

            # --- VISUALIZACIÓN ---
            tab1, tab2 = st.tabs(["📈 Gráficos de Consumo", "📋 Datos Crudos"])

            with tab1:
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("⛽ Consumo de Combustible")
                    if col_gas:
                        fig1 = px.bar(df, x='Fecha_Display', y=col_gas, 
                                     labels={'Fecha_Display': 'Fecha', col_gas: 'Cantidad'},
                                     color_discrete_sequence=['#EF553B'])
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.warning("No se encontró la columna 'ConsumoDeclarado'")

                with col_right:
                    st.subheader("💧 Consumo de Agua")
                    if col_agua:
                        fig2 = px.line(df, x='Fecha_Display', y=col_agua, 
                                      markers=True,
                                      labels={'Fecha_Display': 'Fecha', col_agua: 'm³'})
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.warning("No se encontró la columna 'Agua_Consumo'")

            with tab2:
                st.subheader("Vista detallada de SharePoint")
                st.dataframe(df)

        else:
            st.error("No se encontraron registros en la lista prd_detalle_indicadores_consumos.")

st.divider()
st.caption("COAM Perú - Sistema de Indicadores Automáticos")
