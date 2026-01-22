import streamlit as st
from O365 import Account
import pandas as pd
import plotly.express as px

# Configuración de página para móvil
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
            
            data = [item.fields for item in items]
            return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error técnico de conexión: {e}")
    return None

st.title("📊 Panel de Control COAM")

# Botón actualizado a la sintaxis 2026 (width='stretch')
if st.button("🔄 ACTUALIZAR REPORTES", width='stretch'):
    with st.spinner("Buscando datos en SharePoint..."):
        df_raw = get_data()
        
        if df_raw is not None and not df_raw.empty:
            df = df_raw.copy()
            df.columns = [str(c) for c in df.columns]

            # Detección inteligente de columnas
            col_fecha = next((c for c in df.columns if 'Created' in c or 'Modified' in c), None)
            col_gas = next((c for c in df.columns if 'ConsumoDeclarado' in c), None)
            col_agua = next((c for c in df.columns if 'Agua_Consumo' in c), None)

            # Procesamiento de Fecha
            if col_fecha:
                df['Fecha_Limpia'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
                df = df.sort_values('Fecha_Limpia')
            else:
                df['Fecha_Limpia'] = range(len(df))

            # Procesamiento de Números
            for c in [col_gas, col_agua]:
                if c:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            # --- RENDERIZADO ---
            tab1, tab2 = st.tabs(["📈 Gráficos Diarios", "📋 Tabla de Datos"])

            with tab1:
                # Gráfico Combustible
                st.subheader("⛽ Consumo de Combustible")
                if col_gas:
                    fig1 = px.bar(df, x='Fecha_Limpia', y=col_gas, 
                                 color_discrete_sequence=['#EF553B'],
                                 labels={'Fecha_Limpia': 'Día', col_gas: 'Cantidad'})
                    st.plotly_chart(fig1, on_select="ignore")
                else:
                    st.warning("No se encontró la columna de Combustible.")

                # Gráfico Agua
                st.subheader("💧 Consumo de Agua")
                if col_agua:
                    fig2 = px.line(df, x='Fecha_Limpia', y=col_agua, 
                                  markers=True,
                                  labels={'Fecha_Limpia': 'Día', col_agua: 'm³'})
                    st.plotly_chart(fig2, on_select="ignore")
                else:
                    st.warning("No se encontró la columna de Agua.")

            with tab2:
                st.subheader("Detalle de Registros")
                cols_view = [c for c in [col_fecha, col_gas, col_agua] if c is not None]
                # Tabla actualizada a la sintaxis 2026
                st.dataframe(df[cols_view], width='stretch')

        else:
            st.warning("Conectado, pero la lista parece estar vacía.")

st.divider()
st.caption("COAM - Generado automáticamente desde SharePoint")
