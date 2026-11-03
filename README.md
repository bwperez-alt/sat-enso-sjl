# SAT ENSO – San Juan de Lurigancho

**Sistema de Alerta Temprana de Huaicos, Deslizamientos e Inundación (ENSO)** para el distrito de San Juan de Lurigancho, Lima, Perú.

**Autor:** Perez Flores Brandon W. · [LinkedIn](https://www.linkedin.com/in/brandon-perez-flores/)

> ⚠️ Herramienta **indicativa y educativa**. No sustituye los avisos del SENAMHI, los comunicados del ENFEN ni las alertas del INDECI, CENEPRED o la Municipalidad de San Juan de Lurigancho.

## ¿Qué hace?
- **Mapa satelital interactivo** (imagen satelital, topográfico, calles y modo oscuro) con 12 sectores de quebrada, ladera y ribera, coloreados en 5 niveles: Bajo, Alerta amarilla, Medio, Alto y Crítico.
- **Pronóstico real** de lluvia a 16 días en las cabeceras de las quebradas Canto Grande y Huaycoloro y en la cuenca alta del Rímac (Open-Meteo), y de **caudal del Rímac** a 30 días (GloFAS / Copernicus).
- **Proyección estacional** más allá del día 16, ajustada por el escenario del ENFEN.
- **Estado ENSO en vivo**: índice El Niño de NOAA (RONI/ONI) y estado del sistema de alerta del ENFEN.
- Buscador de sectores, ranking, gráficos diarios, **descarga en CSV** y modo de **simulación de eventos**.
- Panel de **fuentes de datos** que indica en todo momento qué datos son reales y cuáles son proyección.

## Modelo
`Riesgo = Peligro × Vulnerabilidad` (enfoque CENEPRED)

| Componente | Definición |
|---|---|
| Detonante lluvia (Hr) | 0,6·(R24−4)/26 + 0,4·(R72−10)/50, acotado 0–1 (lluvia en cabeceras de quebrada) |
| Detonante fluvial (Hq) | (Q−50)/110, acotado 0–1 (caudal del Rímac en Chosica) |
| Peligro | Susceptibilidad × mezcla según tipo: quebrada 0,75Hr+0,25Hq · ladera Hr · ribera 0,3Hr+0,7Hq |
| Riesgo | Peligro × (0,5 + 0,5·Vulnerabilidad) × 1,25, acotado 0–1 |

Niveles: Bajo < 0,20 · Alerta amarilla 0,20–0,40 · Medio 0,40–0,60 · Alto 0,60–0,80 · Crítico ≥ 0,80.

**Limitaciones:** umbrales, susceptibilidad y vulnerabilidad son referenciales y deben calibrarse con el registro de emergencias (INDECI–SINPAD) de 2017 y 2023, las zonas críticas del INGEMMET y los escenarios del CENEPRED–SIGRID. Los modelos globales pueden subestimar lluvias locales intensas. Ubicación de sectores aproximada.

## Fuentes de datos (gratuitas, sin clave)
| Dato | Fuente | Actualización |
|---|---|---|
| Lluvia diaria pronosticada | Open-Meteo Forecast API | cada 3 h |
| Caudal del Rímac | GloFAS (Copernicus) vía Open-Meteo Flood API | cada 6 h |
| Índice El Niño | NOAA CPC (RONI / ONI) | diario |
| Límite distrital | OpenStreetMap (Nominatim) | mensual |
| Estado ENFEN | `data/config.json` (editar a mano con cada comunicado) | manual |

Si una fuente no responde, la plataforma sigue funcionando con la proyección estacional y lo indica en el panel «Fuentes de datos».

## Cómo actualizar
- **Nuevo comunicado del ENFEN:** editar `data/config.json` (estado, número, fecha, resumen y `escenario_por_defecto`: `nina`, `na`, `vig`, `deb`, `mod`, `fue`, `ext`).
- **Corregir o agregar sectores:** editar `data/sectores.json` (coordenadas, tipo, susceptibilidad y vulnerabilidad entre 0 y 1).
- Al guardar en GitHub, Streamlit actualiza la plataforma automáticamente.

## Estructura
```
app.py                          # aplicación Streamlit
datos.py                        # consulta de fuentes en vivo con caché y respaldo
index.html                      # visor (mapa Leaflet, ranking, gráficos, metodología)
data/config.json                # estado ENFEN y puntos de pronóstico
data/sectores.json              # sectores de alerta
data/limite_sjl_simplificado.geojson  # límite de respaldo
requirements.txt
.streamlit/config.toml          # tema oscuro
```

## Ejecutar en local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud
1. Entrar a https://share.streamlit.io con la cuenta de GitHub.
2. **Create app** → repositorio `sat-enso-sjl`, rama `main`, archivo `app.py`.
3. En **App URL** escribir `sat-enso-sjl` → **Deploy**.

Inspirado en el *Sistema de Alerta Temprana y Riesgo de Inundación (ENSO) Costa Ecuatoriana* de Raúl Acevedo.

© Perez Flores Brandon W.
