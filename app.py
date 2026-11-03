"""
Sistema de Alerta Temprana ante Huaicos, Movimientos en Masa e Inundaciones asociados a El Niño Costero
San Juan de Lurigancho – Lima, Perú
Autor: Perez Flores Brandon W. · https://www.linkedin.com/in/brandon-perez-flores/

Herramienta indicativa y educativa. No sustituye los avisos oficiales de
SENAMHI, ENFEN, INDECI, CENEPRED ni de la Municipalidad de SJL.
"""
import json
from pathlib import Path

import streamlit as st

import datos

st.set_page_config(
    page_title="SAT ENSO · San Juan de Lurigancho",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      header[data-testid="stHeader"] {display:none;}
      .block-container {padding:0 !important; max-width:100% !important;}
      footer {visibility:hidden;}
      .stApp {background:#0f1720;}
      iframe {border:0;}
    </style>
    """,
    unsafe_allow_html=True,
)

cfg = datos.leer_json("config.json")
sectores = datos.leer_json("sectores.json")

with st.spinner("Consultando pronósticos y estado ENSO…"):
    payload = {
        "generado": datos.ahora_lima().strftime("%Y-%m-%d %H:%M"),
        "ahora": datos.ahora_lima().strftime("%Y-%m-%dT%H:00"),
        "hoy": datos.ahora_lima().strftime("%Y-%m-%d"),
        "config": cfg,
        "sectores": sectores,
        "lluvia": datos.lluvia_pronostico(cfg),
        "caudal": datos.caudal_pronostico(cfg),
        "noaa": datos.enso_noaa(),
        "limite": datos.limite_distrital(),
    }

plantilla = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
datos_js = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
html = plantilla.replace("/*__DATA__*/null", datos_js, 1)

if hasattr(st, "iframe"):
    st.iframe(html, height=2000)
else:  # versiones antiguas de Streamlit
    import streamlit.components.v1 as components

    components.html(html, height=2000, scrolling=True)
