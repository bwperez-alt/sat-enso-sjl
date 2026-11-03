"""
Capa de datos del SAT ENSO – San Juan de Lurigancho.

Cada fuente se consulta con caché (st.cache_data). Si una fuente falla, la
función devuelve {"ok": False, ...} y el visor sigue funcionando con la
proyección estacional. Los errores NO se guardan en caché: se reintenta en la
siguiente visita.

Fuentes (gratuitas, sin clave):
- Open-Meteo Forecast API ............ precipitación horaria, humedad, temperatura y humedad del suelo
- Open-Meteo Flood API (GloFAS) ...... caudal diario pronosticado del Rímac
- NOAA CPC (RONI / ONI) .............. índice El Niño del Pacífico central
- OpenStreetMap Nominatim ............ límite distrital de San Juan de Lurigancho
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st

TZ = "America/Lima"
UA = {"User-Agent": "sat-enso-sjl/1.0 (+https://github.com/bwperez-alt/sat-enso-sjl)"}
DATA_DIR = Path(__file__).parent / "data"


def ahora_lima() -> dt.datetime:
    return dt.datetime.now(ZoneInfo(TZ))


def _stamp() -> str:
    return ahora_lima().strftime("%Y-%m-%d %H:%M")


def leer_json(nombre: str):
    return json.loads((DATA_DIR / nombre).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- lluvia (horaria)
VARS_HORARIAS = "precipitation,relative_humidity_2m,temperature_2m,soil_moisture_0_to_1cm"


def _r(v, n=1):
    return None if v is None else round(float(v), n)


@st.cache_data(ttl=3 * 3600, show_spinner=False)
def _lluvia(puntos: tuple) -> dict:
    """puntos: tupla de (nombre, lat, lon). Devuelve series horarias por punto
    (7 días de análisis del modelo + 16 días de pronóstico), hora de Lima."""
    params = {
        "latitude": ",".join(str(p[1]) for p in puntos),
        "longitude": ",".join(str(p[2]) for p in puntos),
        "hourly": VARS_HORARIAS,
        "timezone": TZ,
        "forecast_days": 16,
        "past_days": 7,
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, headers=UA, timeout=12)
    if r.status_code == 400:  # alguna variable de contexto no disponible: se pide solo la precipitación
        params["hourly"] = "precipitation"
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, headers=UA, timeout=12)
    r.raise_for_status()
    js = r.json()
    if isinstance(js, dict):
        js = [js]
    horas = js[0]["hourly"]["time"]
    serie = {}
    for p, j in zip(puntos, js):
        h = j["hourly"]
        serie[p[0]] = {
            "pp": [_r(v) for v in h["precipitation"]],
            "hr": [_r(v, 0) for v in h.get("relative_humidity_2m", [])],
            "t": [_r(v) for v in h.get("temperature_2m", [])],
            "suelo": [_r(v, 3) for v in h.get("soil_moisture_0_to_1cm", [])],
        }
    return {"ok": True, "horas": horas, "puntos": serie, "actualizado": _stamp()}


def lluvia_pronostico(cfg: dict) -> dict:
    puntos = tuple((p["nombre"], p["lat"], p["lon"]) for p in cfg["cabeceras"] + cfg["cuenca_alta"])
    try:
        out = dict(_lluvia(puntos))
        out["cabeceras"] = [p["nombre"] for p in cfg["cabeceras"]]
        out["cuenca_alta"] = [p["nombre"] for p in cfg["cuenca_alta"]]
        return out
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}


# ---------------------------------------------------------------- caudal
@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _caudal(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "river_discharge",
        "past_days": 3,
        "forecast_days": 30,
    }
    r = requests.get("https://flood-api.open-meteo.com/v1/flood", params=params, headers=UA, timeout=12)
    r.raise_for_status()
    d = r.json()["daily"]
    vals = [float(v) if v is not None else None for v in d["river_discharge"]]
    validos = [v for v in vals if v is not None]
    # Control de calidad: la celda GloFAS debe corresponder al cauce principal del Rímac
    if not validos or max(validos) < 3 or max(validos) > 1500:
        raise ValueError("serie GloFAS fuera de rango para el Rímac")
    return {"ok": True, "fechas": d["time"], "caudal": vals, "actualizado": _stamp()}


def caudal_pronostico(cfg: dict) -> dict:
    p = cfg["punto_caudal"]
    try:
        out = dict(_caudal(p["lat"], p["lon"]))
        out["punto"] = p["nombre"]
        return out
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}


# ---------------------------------------------------------------- ENSO (NOAA)
def _parse_indice(txt: str) -> list[dict]:
    filas = []
    for linea in txt.splitlines():
        partes = linea.split()
        if len(partes) < 3 or not partes[1].isdigit():
            continue
        try:
            filas.append({"temporada": partes[0], "anio": int(partes[1]), "anom": float(partes[-1])})
        except ValueError:
            continue
    return filas


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _noaa() -> dict:
    fuentes = [
        ("RONI", "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"),
        ("ONI", "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"),
    ]
    ultimo_error = None
    for nombre, url in fuentes:
        try:
            r = requests.get(url, headers=UA, timeout=12)
            r.raise_for_status()
            filas = _parse_indice(r.text)
            if filas:
                return {"ok": True, "indice": nombre, "ultimos": filas[-6:], "actualizado": _stamp(), "url": url}
        except Exception as e:  # noqa: BLE001
            ultimo_error = e
    raise RuntimeError(f"sin datos NOAA ({ultimo_error})")


def enso_noaa() -> dict:
    try:
        return _noaa()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}


# ---------------------------------------------------------------- límite distrital
@st.cache_data(ttl=30 * 24 * 3600, show_spinner=False)
def _limite() -> dict:
    params = {
        "q": "San Juan de Lurigancho, Lima, Perú",
        "format": "jsonv2",
        "polygon_geojson": 1,
        "polygon_threshold": 0.0002,
        "countrycodes": "pe",
        "limit": 5,
    }
    r = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=UA, timeout=12)
    r.raise_for_status()
    for item in r.json():
        geo = item.get("geojson") or {}
        if geo.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        lat, lon = float(item["lat"]), float(item["lon"])
        if -12.1 < lat < -11.8 and -77.1 < lon < -76.85:
            return {"ok": True, "geometria": geo, "fuente": "OpenStreetMap (Nominatim)", "actualizado": _stamp()}
    raise ValueError("no se encontró el polígono del distrito")


def limite_distrital() -> dict:
    try:
        return _limite()
    except Exception as e:  # noqa: BLE001
        respaldo = leer_json("limite_sjl_simplificado.geojson")
        return {"ok": False, "geometria": respaldo["geometry"], "fuente": "Límite simplificado (respaldo)",
                "error": f"{type(e).__name__}: {e}"[:200]}
