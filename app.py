"""
Sistema de Alerta Temprana de Huaicos, Deslizamientos e Inundación (ENSO)
San Juan de Lurigancho – Lima, Perú
Autor: Perez Flores Brandon W. · https://www.linkedin.com/in/brandon-perez-flores/

Herramienta indicativa y educativa. No sustituye los avisos oficiales de
SENAMHI, ENFEN, INDECI, CENEPRED ni de la Municipalidad de SJL.
"""
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="SAT ENSO · San Juan de Lurigancho",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Quitar márgenes y el encabezado de Streamlit para que el visor ocupe toda la pantalla
st.markdown(
    """
    <style>
      header[data-testid="stHeader"] {display:none;}
      .block-container {padding:0 !important; max-width:100% !important;}
      footer {visibility:hidden;}
      .stApp {background:#0f1720;}
    </style>
    """,
    unsafe_allow_html=True,
)

visor = Path(__file__).parent / "index.html"
if hasattr(st, "iframe"):
    st.iframe(visor, height=1550)
else:  # versiones antiguas de Streamlit
    import streamlit.components.v1 as components
    components.html(visor.read_text(encoding="utf-8"), height=1550, scrolling=True)
