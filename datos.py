"""
Capa de datos de la app Streamlit.

1. Intenta leer los datos precalculados cada hora por GitHub Actions
   (rama `datos` del repositorio): carga casi instantánea.
2. Si no existen o tienen más de 3 horas, consulta las fuentes en vivo
   (fuentes.py) con caché. Los errores no se guardan en caché.
"""
from __future__ import annotations

import datetime as dt
import importlib

import requests
import streamlit as st

import fuentes

fuentes = importlib.reload(fuentes)

TZ = fuentes.TZ
ahora_lima = fuentes.ahora_lima
leer_json = fuentes.leer_json

URL_PRECALCULADO = "https://raw.githubusercontent.com/bwperez-alt/sat-enso-sjl/datos/vivo.json"
MAX_HORAS_PRECALCULADO = 3


def _cache_ok(ttl):
    """Caché que solo guarda resultados correctos (si la función lanza error, no se guarda)."""
    return st.cache_data(ttl=ttl, show_spinner=False)


fuentes._lluvia = _cache_ok(3 * 3600)(fuentes._lluvia_raw)
fuentes._caudal = _cache_ok(6 * 3600)(fuentes._caudal_raw)
fuentes._noaa = _cache_ok(24 * 3600)(fuentes._noaa_raw)
fuentes._limite = _cache_ok(30 * 24 * 3600)(fuentes._limite_raw)

lluvia_pronostico = fuentes.lluvia_pronostico
caudal_pronostico = fuentes.caudal_pronostico
enso_noaa = fuentes.enso_noaa
limite_distrital = fuentes.limite_distrital


@st.cache_data(ttl=600, show_spinner=False)
def _leer_precalculado() -> dict:
    r = requests.get(URL_PRECALCULADO, headers=fuentes.UA, timeout=8)
    r.raise_for_status()
    return r.json()


def precalculados() -> dict | None:
    """Devuelve los datos precalculados si existen y son recientes; si no, None."""
    try:
        d = _leer_precalculado()
        generado = dt.datetime.fromisoformat(d["generado_utc"])
        edad = dt.datetime.now(dt.timezone.utc) - generado
        if edad > dt.timedelta(hours=MAX_HORAS_PRECALCULADO):
            return None
        if not (d.get("lluvia") or {}).get("ok"):
            return None
        return d
    except Exception:  # noqa: BLE001
        return None
