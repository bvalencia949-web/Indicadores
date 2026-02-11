import streamlit as st
from O365 import Account
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="COAM Indicadores", layout="wide")

def get_data():
    """Conecta con SharePoint y extrae los datos de la lista."""
    try:
        # 1. Validación de Secretos
        if "sharepoint" not in st.secrets:
            st.error("❌ No se encontró la sección [sharepoint] en los secrets.")
            return None
        
        credentials = (st.secrets["sharepoint"]["client_id"], 
                       st.secrets["sharepoint"]["client_secret"])
        
        # 2. Configuración de Cuenta
        # Usamos auth_flow_type='credentials' para acceso de aplicación (sin login de usuario)
        account = Account(credentials, 
                          auth_flow_type='credentials', 
                          tenant_id=st.secrets["sharepoint"]["tenant_id"])
        
        if not account.authenticate():
            st.error("❌ Falló la autenticación. Revisa Client ID, Secret y Permisos en Azure.")
            return None
        
        # 3. Acceso al Sitio
        # Nota: La URL debe ser del tipo 'https://dominio.sharepoint.com/sites/NombreSitio'
        site_url = st.secrets["sharepoint"]["site_url"]
        site = account.sharepoint().get_site(site_url)
        
        if not site:
            st.error(f"❌ No se pudo encontrar el sitio: {site_url}")
            return None

        # 4. Acceso a la Lista
        list_name = st.secrets["sharepoint"]["list_name"]
        sp_list = site.get_list_by_name(list_name)
        
        # 5. Obtención de ítems
        items = sp_list.get_items() 
        
        # 6. Transformación a DataFrame
        data = [item.fields for item in items]
        
        if not data:
            st.warning("⚠️ La conexión fue exitosa pero la lista parece estar vacía.")
            return pd.DataFrame()
            
        return pd.DataFrame(data)

    except Exception as e:
        # Captura el error real para saber exactamente qué falla
        st.error(f"❌ Error técnico detallado: {type(e).__name__}: {e}")
        return None

# --- INTERFAZ DE USUARIO ---
st.title("📊 Panel de Control COAM")
st.markdown("---")

# Botón para disparar la carga
if st.button("🔄 ACTUALIZAR REPORTES", use_container_width=True):
    with st.spinner("Conectando con SharePoint..."):
        df_raw = get_data()
    
    if df_raw is not None and not df_raw.empty:
        try:
            # Diagnóstico visual de columnas
            st.info(f"✅ Datos cargados: {len(df_raw)} registros encontrados.")
            with st.expander("Ver estructura de columnas detectadas"):
                st.write(list(df_raw.columns))
            
            df = df_raw.copy()
            
            # Nombres de columnas (Asegúrate de que coincidan con el nombre INTERNO de SharePoint)
            c_fuel = 'ConsumoDeclarado'
            c_water = 'Agua_Consumo'
            c_date = 'Created'

            # 1. Procesamiento de Fechas
            if c_date in df.columns:
                df['Fecha'] = pd.to_datetime(df[c_date], errors='coerce').dt.date
            else:
                # Si no existe 'Created', intentamos con la primera columna que parezca fecha o creamos una
                df['Fecha'] = pd.Timestamp.now().date()

            # 2. Procesamiento de Números
            for col in [c_fuel, c_water]:
                if col in df.columns:
                    # Convertimos a numérico, forzando errores a NaN y luego a 0
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                else:
                    st.warning(f"La columna '{col}' no se encontró en SharePoint. Se usará 0.")
                    df[col] = 0.0

            df = df.sort_values('Fecha')

            # 3. Visualizaciones
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("⛽ Consumo de Combustible")
                fig1 = px.bar(df, x='Fecha', y=c_fuel, 
                             color_discrete_sequence=['#FF4B4B'],
                             labels={c_fuel: 'Litros/Galones'})
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.subheader("💧 Consumo de Agua")
                fig2 = px.line(df, x='Fecha', y=c_water, 
                              markers=True,
                              line_shape='spline',
                              labels={c_water: 'Metros Cúbicos'})
                st.plotly_chart(fig2, use_container_width=True)

            # 4. Tabla Detallada
            st.markdown("---")
            st.subheader("📋 Tabla de Control")
            st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Error procesando los datos: {e}")
    
    elif df_raw is not None and df_raw.empty:
        st.warning("La lista de SharePoint está vacía.")
    else:
        st.error("No se pudo obtener información. Revisa los errores arriba.")

else:
    st.light("Haz clic en el botón superior para cargar los datos actuales de SharePoint.")
