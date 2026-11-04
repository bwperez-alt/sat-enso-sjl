# SAT El Niño Costero – San Juan de Lurigancho

**Sistema de Alerta Temprana ante Huaicos, Movimientos en Masa e Inundaciones asociados a El Niño Costero** para el distrito de San Juan de Lurigancho, Lima, Perú.

**Autor:** Perez Flores Brandon W. · [LinkedIn](https://www.linkedin.com/in/brandon-perez-flores/)
**Plataforma:** https://sat-enso-sjl.streamlit.app

> ⚠️ Herramienta **indicativa y educativa**. Los avisos que muestra **no son oficiales**. Siga siempre los avisos del SENAMHI, los comunicados del ENFEN y las indicaciones del INDECI y de la Municipalidad de San Juan de Lurigancho.

## Enfoque
La plataforma separa dos conceptos:

1. **Nivel de riesgo de referencia** (estático, 4 niveles como el CENEPRED: Bajo, Medio, Alto, Muy alto) = susceptibilidad × vulnerabilidad de cada sector.
2. **Aviso indicativo** (dinámico, por día: sin aviso, amarillo, naranja, rojo), que resulta de cruzar el nivel de riesgo con la **intensidad del detonante pronosticado** en una matriz basada en impacto:

| Detonante \ Riesgo | Bajo | Medio | Alto | Muy alto |
|---|---|---|---|---|
| Moderado (≥ U1) | Sin aviso | Sin aviso | Amarillo | Amarillo |
| Fuerte (≥ U2) | Sin aviso | Amarillo | Amarillo | Naranja |
| Extremo (≥ U3) | Amarillo | Naranja | Rojo | Rojo |

**Detonante pluvial** (cabeceras de las quebradas Canto Grande y Huaycoloro): nivel más alto entre la intensidad máxima en 1 h, el acumulado en 24 h y el acumulado en 72 h frente a los umbrales U1/U2/U3 (equivalentes conceptuales a P90/P95/P99 del SENAMHI). Con suelo húmedo (índice de precipitación antecedente ≥ umbral), los umbrales de 24 h se reducen un 20 %.
**Detonante fluvial** (sectores de ribera): caudal diario del Rímac en la estación Chosica.

## Qué incluye
- Mapa satelital, topográfico y de calles con avisos por sector (color) y nivel de riesgo (tamaño).
- Precipitación **horaria**: 7 días de análisis del modelo + 16 días de pronóstico; acumulados de 24 y 72 h; índice de lluvia antecedente.
- Caudal del Rímac (GloFAS) para sectores de ribera.
- **ICEN** (El Niño Costero) como indicador principal, estado y magnitud esperada del ENFEN; RONI/ONI de NOAA como contexto.
- Modo **escenario hipotético** con detonantes moderado, fuerte y extremo.
- Perspectiva estacional, recomendaciones ante cada aviso y números de emergencia.
- Buscador, descarga en CSV y panel de fuentes de datos.

## Datos ilustrativos y pendientes
- **Susceptibilidad y vulnerabilidad** de `data/sectores.json` son **ilustrativas**: deben reemplazarse por la susceptibilidad del INGEMMET o del CENEPRED y por una vulnerabilidad con exposición, fragilidad y resiliencia.
- **Elementos expuestos** (población, viviendas, establecimientos de salud e instituciones educativas) están pendientes de cargar desde el INEI y el catastro municipal.
- **Umbrales** de `data/config.json` son referenciales: deben reemplazarse por los percentiles del estudio de umbrales del SENAMHI para la cuenca del Rímac y por los umbrales hidrológicos oficiales de la estación Chosica, y calibrarse con eventos del SINPAD y del INGEMMET.
- Los últimos 7 días son **análisis del modelo**, no observaciones de estaciones.

## Fuentes de datos (gratuitas, sin clave)
| Dato | Fuente | Actualización |
|---|---|---|
| Precipitación horaria, humedad, temperatura, humedad del suelo | Open-Meteo Forecast API | cada 3 h |
| Caudal del Rímac | GloFAS (Copernicus) vía Open-Meteo Flood API | cada 6 h |
| ICEN y estado ENFEN | `data/config.json` (manual, con cada comunicado) | manual |
| RONI / ONI | NOAA CPC | diario |
| Límite distrital | OpenStreetMap (Nominatim) | mensual |

## Cómo actualizar
- **Nuevo comunicado del ENFEN o nuevo ICEN:** editar los bloques `enfen` e `icen` de `data/config.json`.
- **Umbrales:** bloque `umbrales` de `data/config.json`.
- **Sectores, susceptibilidad, vulnerabilidad y elementos expuestos:** `data/sectores.json`.
- Al guardar en GitHub, Streamlit actualiza la plataforma automáticamente.

## Actualización automática (GitHub Actions)
El flujo `.github/workflows/actualizar-datos.yml` se ejecuta **cada hora** (minuto 17): consulta las fuentes con `actualizar_datos.py` y publica `vivo.json` en la rama `datos`. Al abrirse, la app lee ese archivo (carga rápida); si tiene más de 3 horas o no está disponible, consulta las fuentes en vivo.

- Ejecutar a mano: pestaña **Actions → Actualizar datos → Run workflow**.
- GitHub desactiva los flujos programados de repositorios públicos sin actividad durante 60 días; si ocurre, reactívelo desde la pestaña **Actions**.

## Estructura
```
app.py                                # aplicación Streamlit
fuentes.py                            # consulta de fuentes (sin Streamlit)
datos.py                              # caché, datos precalculados y respaldo en vivo
actualizar_datos.py                   # precálculo horario (GitHub Actions)
index.html                            # visor
data/config.json                      # ENFEN, ICEN, umbrales, puntos de pronóstico
data/sectores.json                    # sectores
data/limite_sjl_simplificado.geojson  # límite de respaldo
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
