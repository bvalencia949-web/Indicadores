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
            return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
    return None

st.title("📊 Panel de Control COAM")

if st.button("🔄 ACTUALIZAR REPORTES", width='stretch'):
    status = st.empty() # Espacio para mensajes de estado
    status.info("🔍 Conectando con SharePoint...")
    
    df_raw = get_data()
    
    if df_raw is not None and not df_raw.empty:
        status.info("✅ Datos recibidos. Procesando columnas...")
        df = df_raw.copy()
        df.columns = [str(c) for c in df.columns]

        # Identificación flexible de columnas
        col_fecha = next((c for c in df.columns if 'Created' in c or 'Modified' in c), None)
        col_gas = next((c for c in df.columns if 'ConsumoDeclarado' in c), None)
        col_agua = next((c for c in df.columns if 'Agua_Consumo' in c), None)

        # Procesar Fecha
        if col_fecha:
            df['Fecha_Limpia'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
            df = df.sort_values('Fecha_Limpia')
        else:
            df['Fecha_Limpia'] = "Sin Fecha"

        # Procesar Números
        for c in [col_gas, col_agua]:
            if c:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        status.empty() # Limpiar mensaje de estado

        # --- MOSTRAR RESULTADOS ---
        # 1. KPIs Rápidos arriba
        kpi1, kpi2 = st.columns(2)
        if col_gas:
            kpi1.metric("Total Combustible", f"{df[col_gas].sum():,.2f}")
        if col_agua:
            kpi2.metric("Total Agua", f"{df[col_agua].sum():,.2f} m³")

        # 2. Gráficos en pestañas
        t1, t2 = st.tabs(["📈 Gráficos", "📋 Tabla Completa"])
        
        with t1:
            if col_gas:
                st.subheader("⛽ Consumo de Combustible")
                st.plotly_chart(px.bar(df, x='Fecha_Limpia', y=col_gas, color_discrete_sequence=['#EF553B']), width='stretch')
            
            if col_agua:
                st.subheader("💧 Consumo de Agua")
                st.plotly_chart(px.line(df, x='Fecha_Limpia', y=col_agua, markers=True), width='stretch')

        with t2:
            st.dataframe(df, width='stretch')
            
    elif df_raw is not None and df_raw.empty:
        status.warning("⚠️ La lista de SharePoint está conectada pero no tiene filas.")
    else:
        status.error("❌ No se pudo obtener información.")

st.divider()
st.caption("COAM Perú - 2026")
