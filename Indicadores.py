import streamlit as st
from O365 import Account
import pandas as pd

# Configuración de página para móviles
st.set_page_config(
    page_title="Indicadores COAM", 
    layout="centered", # Centrado se ve mejor en celulares
    initial_sidebar_state="collapsed"
)

def get_sharepoint_data():
    try:
        # Extraer credenciales de st.secrets (Configurado en la nube de Streamlit)
        credentials = (
            st.secrets["sharepoint"]["client_id"], 
            st.secrets["sharepoint"]["client_secret"]
        )
        
        account = Account(
            credentials, 
            auth_flow_type='credentials', 
            tenant_id=st.secrets["sharepoint"]["tenant_id"]
        )
        
        if account.authenticate():
            site = account.sharepoint().get_site(st.secrets["sharepoint"]["site_url"])
            sp_list = site.get_list_by_name(st.secrets["sharepoint"]["list_name"])
            
            # Obtener elementos (por defecto trae los últimos 25, puedes ajustar)
            items = sp_list.get_items()
            
            # Convertir a DataFrame
            data = [item.fields for item in items]
            df = pd.DataFrame(data)
            
            # Limpieza de columnas técnicas de SharePoint
            cols_to_drop = ['@odata.etag', 'id', 'ContentType', 'ComplianceAssetId', 'AuthorLookupId', 'EditorId']
            df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
            
            return df
        else:
            st.error("Error: No se pudo autenticar con Microsoft.")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- Interfaz en el Celular ---
st.title("📊 Consumos COAM")
st.info("Conectado a: prd_detalle_indicadores_consumos")

# Botón grande para actualizar (fácil de tocar con el pulgar)
if st.button("🔄 ACTUALIZAR DATOS", use_container_width=True):
    with st.spinner("Consultando SharePoint..."):
        df = get_sharepoint_data()
        
        if df is not None and not df.empty:
            st.success(f"Cargados {len(df)} registros.")
            
            # Buscador para filtrar rápido en la calle
            busqueda = st.text_input("🔍 Buscar por cualquier campo:")
            if busqueda:
                df = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            
            # Tabla interactiva adaptada al ancho del celular
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No se encontraron datos en la lista.")