import streamlit as st
from O365 import Account
import pandas as pd

# Configuración para celular
st.set_page_config(page_title="COAM Indicadores", layout="centered")

def get_data():
    # Carga de credenciales desde los Secrets de Streamlit
    credentials = (st.secrets["sharepoint"]["client_id"], 
                   st.secrets["sharepoint"]["client_secret"])
    
    # Configuración de la cuenta con tu Tenant ID real
    account = Account(credentials, 
                     auth_flow_type='credentials', 
                     tenant_id=st.secrets["sharepoint"]["tenant_id"])
    
    if account.authenticate():
        # Conexión al sitio y lista específica
        site = account.sharepoint().get_site(st.secrets["sharepoint"]["site_url"])
        sp_list = site.get_list_by_name(st.secrets["sharepoint"]["list_name"])
        items = sp_list.get_items()
        
        # Procesamiento de datos
        data = [item.fields for item in items]
        df = pd.DataFrame(data)
        
        # Limpiar columnas innecesarias de SharePoint para ver mejor en el móvil
        cols_to_exclude = ['@odata.etag', 'id', 'ContentType', 'ComplianceAssetId']
        df = df.drop(columns=[c for c in cols_to_exclude if c in df.columns])
        return df
    else:
        return None

# --- Interfaz de Usuario ---
st.title("📊 Indicadores COAM")
st.write("Visualización de consumos en tiempo real.")

# Botón grande para el celular
if st.button("🔄 CARGAR / ACTUALIZAR DATOS", use_container_width=True):
    with st.spinner("Conectando con SharePoint..."):
        try:
            df = get_data()
            if df is not None and not df.empty:
                st.success(f"¡{len(df)} registros encontrados!")
                
                # Buscador rápido
                filtro = st.text_input("🔍 Buscar en la lista:")
                if filtro:
                    df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]
                
                # Tabla adaptable
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No se encontraron datos o revisa los permisos en Azure.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")

st.divider()
st.caption("Acceso seguro vía Microsoft Graph API")
