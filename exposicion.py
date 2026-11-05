"""
Exposición por sector (elementos expuestos) – SAT El Niño Costero SJL.

Lo ejecuta GitHub Actions una vez al mes (.github/workflows/actualizar-exposicion.yml).
Resultado: salida/exposicion.json (rama "datos").

Método (estimación, se rotula así en la plataforma):
1. Población: grilla de población de 100 m de WorldPop, ajustada para que el total
   del distrito coincida con la población censada oficial del INEI (Censos Nacionales 2025).
2. Edificaciones: huellas de edificaciones de Microsoft (Global ML Building Footprints),
   como aproximación al número de viviendas.
3. Zona de cada sector: círculo de radio configurable (config.json → exposicion.radio_m).
4. Áreas críticas oficiales: polígonos publicados por el CENEPRED (SIGRID) / INGEMMET,
   consultados por servicio ArcGIS REST. Se cuenta la población y las edificaciones dentro.

Uso: python exposicion.py salida/exposicion.json
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np
import requests
from pyproj import Transformer
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform, unary_union

import fuentes

BBOX = (-77.07, -12.07, -76.82, -11.82)  # SJL + zona de influencia (lon/lat)
UA = fuentes.UA
A_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32718", always_xy=True).transform
A_GEO = Transformer.from_crs("EPSG:32718", "EPSG:4326", always_xy=True).transform


def log(*a):
    print(*a, flush=True)


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


# ------------------------------------------------------------ geometrías
def circulo(lon, lat, radio_m):
    return transform(A_GEO, transform(A_UTM, Point(lon, lat)).buffer(radio_m, 48))


def limite_distrito():
    d = fuentes.limite_distrital()
    return shape(d["geometria"]), d.get("fuente", "")


# ------------------------------------------------------------ población (WorldPop)
def worldpop_url():
    hoy = dt.date.today().year
    for alias in ("G2_CN_POP_R25A_100m", "cic2020_100m"):
        try:
            r = requests.get(f"https://hub.worldpop.org/rest/data/pop/{alias}?iso3=PER", headers=UA, timeout=40)
            r.raise_for_status()
            datos = [d for d in r.json().get("data", []) if d.get("files")]
            datos.sort(key=lambda d: int(d.get("popyear", 0) or 0))
            cand = [d for d in datos if int(d.get("popyear", 0) or 0) <= hoy] or datos
            if not cand:
                continue
            d = cand[-1]
            tif = [f for f in d["files"] if f.lower().endswith(".tif")]
            if tif:
                return tif[0], f"WorldPop ({alias}, año {d.get('popyear')})"
        except Exception as e:  # noqa: BLE001
            log("WorldPop", alias, "falló:", e)
    raise RuntimeError("no se encontró la grilla de WorldPop para Perú")


class Grilla:
    def __init__(self, url):
        import rasterio
        from rasterio.windows import from_bounds

        with rasterio.open("/vsicurl/" + url) as src:
            win = from_bounds(*BBOX, transform=src.transform).round_offsets().round_lengths()
            arr = src.read(1, window=win).astype("float64")
            nod = src.nodata
            self.tr = src.window_transform(win)
        if nod is not None:
            arr[arr == nod] = 0
        arr[~np.isfinite(arr)] = 0
        arr[arr < 0] = 0
        self.arr = arr
        log("Grilla WorldPop leída:", arr.shape, "suma ventana", round(arr.sum()))

    def suma(self, geom) -> float:
        from rasterio.features import geometry_mask

        if geom.is_empty:
            return 0.0
        m = geometry_mask([mapping(geom)], out_shape=self.arr.shape, transform=self.tr, invert=True)
        return float(self.arr[m].sum())


# ------------------------------------------------------------ edificaciones (Microsoft)
def quadkey(x, y, z):
    q = ""
    for i in range(z, 0, -1):
        d = 0
        m = 1 << (i - 1)
        if x & m:
            d += 1
        if y & m:
            d += 2
        q += str(d)
    return q


def tile(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def edificaciones_centroides():
    """Devuelve una lista de (lon, lat) de edificaciones dentro del BBOX."""
    r = requests.get("https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv",
                     headers=UA, timeout=60)
    r.raise_for_status()
    filas = list(csv.DictReader(io.StringIO(r.text)))
    x0, y1 = tile(BBOX[0], BBOX[1], 9)
    x1, y0 = tile(BBOX[2], BBOX[3], 9)
    qks = {quadkey(x, y, 9) for x in range(min(x0, x1), max(x0, x1) + 1) for y in range(min(y0, y1), max(y0, y1) + 1)}
    urls = [f["Url"] for f in filas if f.get("Location") == "Peru" and f.get("QuadKey") in qks]
    log("Edificaciones: quadkeys", sorted(qks), "archivos", len(urls))
    pts = []
    for u in urls:
        rr = requests.get(u, headers=UA, timeout=600)
        rr.raise_for_status()
        with gzip.open(io.BytesIO(rr.content), "rt", encoding="utf-8") as fh:
            for linea in fh:
                try:
                    g = json.loads(linea)
                    g = g.get("geometry", g)
                    anillo = g["coordinates"][0]
                    lon = sum(p[0] for p in anillo) / len(anillo)
                    lat = sum(p[1] for p in anillo) / len(anillo)
                except Exception:  # noqa: BLE001
                    continue
                if BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]:
                    pts.append((lon, lat))
    log("Edificaciones en el área:", len(pts))
    return pts


def contar(pts_arr, geom) -> int:
    if geom.is_empty or pts_arr is None or not len(pts_arr):
        return 0
    from shapely import contains_xy

    minx, miny, maxx, maxy = geom.bounds
    sel = pts_arr[(pts_arr[:, 0] >= minx) & (pts_arr[:, 0] <= maxx) & (pts_arr[:, 1] >= miny) & (pts_arr[:, 1] <= maxy)]
    if not len(sel):
        return 0
    return int(contains_xy(geom, sel[:, 0], sel[:, 1]).sum())


# ------------------------------------------------------------ áreas críticas oficiales
SERVICIOS = [
    ("CENEPRED – SIGRID", "https://sigrid.cenepred.gob.pe/arcgis/rest/services/Cartografia_Peligros/MapServer"),
    ("INGEMMET – Perú en Alerta", "https://geocatminapp.ingemmet.gob.pe/arcgis/rest/services/SERV_PERUALERTA/MapServer"),
]


def areas_criticas():
    feats = []
    for fuente, base in SERVICIOS:
        try:
            r = requests.get(base + "/layers", params={"f": "json"}, headers=UA, timeout=60)
            r.raise_for_status()
            capas = r.json().get("layers", [])
        except Exception as e:  # noqa: BLE001
            log(fuente, "sin catálogo de capas:", e)
            continue
        for c in capas:
            nombre = c.get("name", "")
            n = norm(nombre)
            if c.get("type") != "Feature Layer" or "critic" not in n:
                continue
            if c.get("geometryType") not in ("esriGeometryPolygon", "esriGeometryPoint"):
                continue
            try:
                q = requests.get(f"{base}/{c['id']}/query", headers=UA, timeout=90, params={
                    "geometry": ",".join(map(str, BBOX)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                    "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "true",
                    "outSR": 4326, "f": "geojson"})
                q.raise_for_status()
                fc = q.json()
                n_ok = 0
                for f in fc.get("features", []):
                    if not f.get("geometry"):
                        continue
                    props = {k: v for k, v in (f.get("properties") or {}).items()
                             if v not in (None, "", " ") and not k.lower().startswith(("shape", "objectid", "fid", "globalid"))}
                    f["properties"] = {"fuente": fuente, "capa": nombre, **dict(list(props.items())[:12])}
                    feats.append(f)
                    n_ok += 1
                log(fuente, "capa", c["id"], nombre, "→", n_ok, "elementos")
            except Exception as e:  # noqa: BLE001
                log(fuente, "capa", c.get("id"), nombre, "falló:", e)
    return feats


# ------------------------------------------------------------ principal
def main(destino: str) -> int:
    cfg = fuentes.leer_json("config.json")
    sectores = fuentes.leer_json("sectores.json")
    exp_cfg = cfg.get("exposicion", {})
    radios = exp_cfg.get("radio_m", {"quebrada": 300, "ladera": 300, "ribera": 250})
    pob_of = exp_cfg.get("poblacion_oficial", {})
    out = {"generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "generado_lima": fuentes.ahora_lima().strftime("%Y-%m-%d %H:%M"),
           "metodo": "Estimación: población WorldPop ajustada al total censal INEI; edificaciones Microsoft; zona = círculo por sector.",
           "fuentes": {}, "sectores": {}, "distrito": {}, "areas_criticas": {"type": "FeatureCollection", "features": []}}

    distrito, f_lim = limite_distrito()
    out["fuentes"]["limite"] = f_lim

    # Población
    grilla, factor = None, None
    try:
        url, etiqueta = worldpop_url()
        grilla = Grilla(url)
        wp_dist = grilla.suma(distrito)
        oficial = pob_of.get("valor")
        factor = (oficial / wp_dist) if (oficial and wp_dist > 0) else 1.0
        out["fuentes"]["poblacion"] = f"{etiqueta}, ajustada a {pob_of.get('fuente', 'INEI')}"
        out["distrito"]["poblacion_worldpop"] = round(wp_dist)
        out["distrito"]["factor_ajuste"] = round(factor, 4)
        log("Población WorldPop distrito:", round(wp_dist), "factor:", round(factor, 3))
    except Exception as e:  # noqa: BLE001
        log("Población no disponible:", e)
        out["fuentes"]["poblacion"] = None

    # Edificaciones
    pts = None
    try:
        p = edificaciones_centroides()
        pts = np.array(p) if p else None
        out["fuentes"]["edificaciones"] = "Microsoft Global ML Building Footprints"
        if pts is not None:
            out["distrito"]["edificaciones"] = contar(pts, distrito)
    except Exception as e:  # noqa: BLE001
        log("Edificaciones no disponibles:", e)
        out["fuentes"]["edificaciones"] = None

    # Áreas críticas oficiales
    feats = areas_criticas()
    geoms = []
    for f in feats:
        try:
            g = shape(f["geometry"])
            if g.geom_type == "Point":
                continue
            geoms.append(g.buffer(0))
        except Exception:  # noqa: BLE001
            pass
    out["areas_criticas"]["features"] = feats
    union = unary_union(geoms) if geoms else None
    if union is not None and not union.is_empty:
        en_sjl = union.intersection(distrito)
        out["distrito"]["areas_criticas_poligonos"] = len(geoms)
        if grilla is not None:
            out["distrito"]["poblacion_en_areas_criticas"] = round(grilla.suma(en_sjl) * factor)
        if pts is not None:
            out["distrito"]["edificaciones_en_areas_criticas"] = contar(pts, en_sjl)
    out["fuentes"]["areas_criticas"] = sorted({f["properties"]["fuente"] + " · " + f["properties"]["capa"] for f in feats}) or None

    # Sectores
    for s in sectores:
        r = radios.get(s["tipo"], 300)
        zona = circulo(s["lon"], s["lat"], r)
        d = {"radio_m": r}
        if grilla is not None:
            d["poblacion"] = round(grilla.suma(zona) * factor)
        if pts is not None:
            d["edificaciones"] = contar(pts, zona)
        if union is not None and not union.is_empty:
            d["en_area_critica"] = bool(zona.intersects(union))
        out["sectores"][s["id"]] = d
        log("Sector", s["id"], d)

    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    Path(destino).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    ok = grilla is not None or pts is not None or bool(feats)
    log("Listo:", destino, "OK" if ok else "SIN DATOS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "salida/exposicion.json"))
