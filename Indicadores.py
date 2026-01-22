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
            
            # Extraemos los campos de cada fila
            data = [item.fields for item in items]
            
            if not data:
                return pd.DataFrame()
                
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error técnico de conexión: {e}")
    return None

st.title("📊 Panel de Control COAM")

if st.button("🔄 ACTUALIZAR REPORTES", use_container_width=True):
    with st.spinner("Buscando datos en SharePoint..."):
        df_raw = get_data()
        
        if df_raw is not None and not df_raw.empty:
            # --- LIMPIEZA DE COLUMNAS (Para evitar el TypeError) ---
            df = df_raw.copy()
            # Aseguramos que todos los nombres de columnas sean strings y sin espacios
            df.columns = [str(c) for c in df.columns]

            # --- IDENTIFICACIÓN DE COLUMNAS ---
            # Buscamos coincidencias aunque el nombre interno sea distinto
            col_fecha = next((c for c in df.columns if 'Created' in c or 'Modified' in c), None)
            col_gas = next((c for c in df.columns if 'ConsumoDeclarado' in c), None)
            col_agua = next((c for c in df.columns if 'Agua_Consumo' in c), None)

            # --- PROCESAMIENTO ---
            # 1. Fecha
            if col_fecha:
                df['Fecha_Limpia'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
                df = df.sort_values('Fecha_Limpia')
            else:
                # Si no hay columna de sistema, creamos una ficticia para que no rompa el gráfico
                df['Fecha_Limpia'] = range(len(df))

            # 2. Números
            for c in [col_gas, col_agua]:
                if c:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            # --- INTERFAZ ---
            tab1, tab2 = st.tabs(["📈 Gráficos Diarios", "📋 Tabla de Datos"])

            with tab1:
                # Gráfico Combustible
                st.subheader("⛽ Consumo de Combustible")
                if col_gas:
                    fig1 = px.bar(df, x='Fecha_Limpia', y=col_gas, 
                                 color_discrete_sequence=['#EF553B'],
                                 labels={'Fecha_Limpia': 'Día', col_gas: 'Consumo'})
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning("No se encontró la columna de Combustible.")

                # Gráfico Agua
                st.subheader("💧 Consumo de Agua")
                if col_agua:
                    fig2 = px.line(df, x='Fecha_Limpia', y=col_agua, 
                                  markers=True,
                                  labels={'Fecha_Limpia': 'Día', col_agua: 'm³'})
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning("No se encontró la columna de Agua.")

            with tab2:
                st.subheader("Detalle de Registros")
                # Mostrar solo columnas útiles
                cols_view = [c for c in [col_fecha, col_gas, col_agua] if c is not None]
                st.dataframe(df[cols_view], use_container_width=True)

        else:
            st.warning("Conectado, pero la lista parece estar vacía.")

st.divider()
st.caption("COAM - Generado automáticamente desde SharePoint")
