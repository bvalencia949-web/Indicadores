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
            items = sp_list.get_items() 
            
            data = [item.fields for item in items]
            return pd.DataFrame(data)
        return None
    except Exception as e:
        st.error(f"Error en get_data: {e}")
        return None

st.title("📊 Panel de Control COAM")

# Usamos un estado para saber si ya se cargó la data
if st.button("🔄 ACTUALIZAR REPORTES", width='stretch'):
    df_raw = get_data()
    
    if df_raw is not None:
        try:
            # 1. Verificación rápida: ¿Vienen las columnas?
            st.write("Columnas detectadas:", list(df_raw.columns))
            
            df = df_raw.copy()
            c_fuel = 'ConsumoDeclarado'
            c_water = 'Agua_Consumo'
            c_date = 'Created'

            # 2. Forzar conversión de datos
            if c_date in df.columns:
                df['Fecha'] = pd.to_datetime(df[c_date], errors='coerce').dt.date
            else:
                df['Fecha'] = pd.Timestamp.now().date()

            # Convertir a números y rellenar ceros
            for col in [c_fuel, c_water]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                else:
                    df[col] = 0.0

            df = df.sort_values('Fecha')

            # 3. Dibujar Gráficos (con validación)
            st.subheader("⛽ Combustible")
            fig1 = px.bar(df, x='Fecha', y=c_fuel if c_fuel in df.columns else None)
            st.plotly_chart(fig1, width='stretch')

            st.subheader("💧 Agua")
            fig2 = px.line(df, x='Fecha', y=c_water if c_water in df.columns else None, markers=True)
            st.plotly_chart(fig2, width='stretch')

            st.subheader("📋 Tabla de Control")
            st.dataframe(df, width='stretch')

        except Exception as e:
            st.error(f"Error procesando los datos: {e}")
    else:
        st.error("No se pudo obtener el DataFrame de SharePoint.")
