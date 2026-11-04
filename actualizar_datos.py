"""
Precalcula los datos del SAT y los guarda en un archivo JSON.
Lo ejecuta GitHub Actions cada hora (.github/workflows/actualizar-datos.yml).

Uso: python actualizar_datos.py salida/vivo.json
"""
import datetime as dt
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fuentes


def main(destino: str) -> int:
    cfg = fuentes.leer_json("config.json")
    tareas = {
        "lluvia": lambda: fuentes.lluvia_pronostico(cfg),
        "caudal": lambda: fuentes.caudal_pronostico(cfg),
        "noaa": fuentes.enso_noaa,
        "limite": fuentes.limite_distrital,
    }
    with ThreadPoolExecutor(max_workers=4) as ex:
        futuros = {k: ex.submit(f) for k, f in tareas.items()}
        datos = {k: f.result() for k, f in futuros.items()}
    datos["generado_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    datos["generado_lima"] = fuentes.ahora_lima().strftime("%Y-%m-%d %H:%M")
    out = Path(destino)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for k in tareas:
        estado = "OK" if datos[k].get("ok") else "FALLÓ: " + str(datos[k].get("error"))
        print(f"{k:8s} {estado}")
    # Falla el trabajo solo si no hay lluvia (el dato esencial)
    return 0 if datos["lluvia"].get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "salida/vivo.json"))
