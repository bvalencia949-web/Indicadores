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

if st.button("🔄 ACTUALIZAR DATOS Y GRÁFICOS", use_container_width=True):
    with st.spinner("Conectando con SharePoint..."):
        df = get_data()
        
        if df is not None and not df.empty:
            # --- DIAGNÓSTICO DE COLUMNAS ---
            # Esto te ayudará a ver cómo se llaman realmente tus columnas
            st.write("### 🔍 Columnas detectadas:", list(df.columns))
            
            # Intentamos detectar la fecha (SharePoint suele usar 'AuthorLookupId' o 'Modified')
            # Si 'Created' falló, buscaremos una alternativa común
            col_fecha = 'Created' if 'Created' in df.columns else (df.columns[0] if len(df.columns) > 0 else None)
            
            if col_fecha:
                df['Fecha_Limpia'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
            
            # --- CONFIGURACIÓN DE CONSUMOS ---
            # IMPORTANTE: Cambia estos nombres por los que aparezcan en la lista de arriba
            col_gasolina = 'Combustible' 
            col_agua = 'Agua'

            # Convertir a números
            for c in [col_gasolina, col_agua]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            # --- GRÁFICOS ---
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("⛽ Consumo de Combustible")
                if col_gasolina in df.columns:
                    fig1 = px.bar(df, x='Fecha_Limpia', y=col_gasolina, color_discrete_sequence=['#EF553B'])
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning(f"No se encontró la columna '{col_gasolina}'")

            with c2:
                st.subheader("💧 Consumo de Agua")
                if col_agua in df.columns:
                    fig2 = px.line(df, x='Fecha_Limpia', y=col_agua, markers=True)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning(f"No se encontró la columna '{col_agua}'")

            st.divider()
            st.subheader("📋 Tabla Completa")
            st.dataframe(df)
        else:
            st.error("No se encontraron datos.")
