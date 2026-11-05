"""
Sistema de Alerta Temprana ante Huaicos, Movimientos en Masa e Inundaciones asociados a El Niño Costero
San Juan de Lurigancho – Lima, Perú
Autor: Perez Flores Brandon W. · https://www.linkedin.com/in/brandon-perez-flores/

Herramienta indicativa y educativa. No sustituye los avisos oficiales de
SENAMHI, ENFEN, INDECI, CENEPRED ni de la Municipalidad de SJL.
"""
import json
from pathlib import Path

import importlib

import streamlit as st

import datos

# Recarga el módulo de datos en cada ejecución: evita que Streamlit siga usando
# una versión anterior en memoria después de una actualización del repositorio.
datos = importlib.reload(datos)

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

from concurrent.futures import ThreadPoolExecutor

try:  # adjunta el contexto de Streamlit a los hilos (evita advertencias)
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
except Exception:  # noqa: BLE001
    add_script_run_ctx = get_script_run_ctx = None


def _en_paralelo(tareas: dict) -> dict:
    """Ejecuta las consultas a la vez: la primera carga tarda lo que la más lenta, no la suma."""
    ctx = get_script_run_ctx() if get_script_run_ctx else None

    def envolver(f):
        def run():
            if ctx is not None and add_script_run_ctx:
                import threading
                add_script_run_ctx(threading.current_thread(), ctx)
            return f()
        return run

    with ThreadPoolExecutor(max_workers=len(tareas)) as ex:
        futuros = {k: ex.submit(envolver(f)) for k, f in tareas.items()}
        return {k: fut.result() for k, fut in futuros.items()}


with st.spinner("Consultando pronósticos y estado de El Niño…"):
    pre = datos.precalculados()
    if pre:  # datos preparados cada hora por GitHub Actions: carga rápida
        vivos = {k: pre[k] for k in ("lluvia", "caudal", "noaa", "limite")}
        origen = {"tipo": "precalculado", "generado": pre.get("generado_lima")}
    else:  # respaldo: consulta en vivo
        vivos = _en_paralelo({
            "lluvia": lambda: datos.lluvia_pronostico(cfg),
            "caudal": lambda: datos.caudal_pronostico(cfg),
            "noaa": datos.enso_noaa,
            "limite": datos.limite_distrital,
        })
        origen = {"tipo": "en vivo", "generado": datos.ahora_lima().strftime("%Y-%m-%d %H:%M")}
    payload = {
        "origen": origen,
        "version": 3,
        "generado": datos.ahora_lima().strftime("%Y-%m-%d %H:%M"),
        "ahora": datos.ahora_lima().strftime("%Y-%m-%dT%H:00"),
        "hoy": datos.ahora_lima().strftime("%Y-%m-%d"),
        "config": cfg,
        "sectores": sectores,
        "oficial": datos.leer_json("oficial.json"),
        "exposicion": datos.exposicion(),
        **vivos,
    }

plantilla = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
datos_js = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
html = plantilla.replace("/*__DATA__*/null", datos_js, 1)

if hasattr(st, "iframe"):
    # "content": el marco se ajusta a la altura del contenido (clave en celulares)
    st.iframe(html, height="content")
else:  # versiones antiguas de Streamlit
    import streamlit.components.v1 as components

    components.html(html, height=2000, scrolling=True)
