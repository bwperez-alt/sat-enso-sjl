# SAT ENSO – San Juan de Lurigancho

**Sistema de Alerta Temprana de Huaicos, Deslizamientos e Inundación (ENSO)** para el distrito de San Juan de Lurigancho, Lima, Perú.

**Autor:** Perez Flores Brandon W. · [LinkedIn](https://www.linkedin.com/in/brandon-perez-flores/)

> ⚠️ Herramienta **indicativa y educativa**. No sustituye los avisos del SENAMHI, los comunicados del ENFEN ni las alertas del INDECI, CENEPRED o la Municipalidad de San Juan de Lurigancho.

## ¿Qué hace?
- Mapa de 12 sectores del distrito (quebradas, laderas y riberas del Rímac) con alerta de 5 niveles: Bajo, Alerta amarilla, Medio, Alto y Crítico.
- Escenarios del sistema de alerta del ENFEN (La Niña costera → El Niño costero extraordinario).
- **Proyección estacional** día a día y **simulación de evento** (lluvia 24 h / 72 h en la cuenca alta y caudal del Rímac en Chosica).
- Ranking de sectores, gráficos diarios de riesgo y lluvia, y sección de metodología.

## Modelo
`Riesgo = Peligro × Vulnerabilidad` (enfoque CENEPRED)

| Componente | Definición |
|---|---|
| Detonante lluvia (Hr) | 0,6·(R24−4)/26 + 0,4·(R72−10)/50, acotado 0–1 |
| Detonante fluvial (Hq) | (Q−50)/110, acotado 0–1 |
| Peligro | Susceptibilidad × mezcla según tipo: quebrada 0,75Hr+0,25Hq · ladera Hr · ribera 0,3Hr+0,7Hq |
| Riesgo | Peligro × (0,5 + 0,5·Vulnerabilidad) × 1,25, acotado 0–1 |

Niveles: Bajo < 0,20 · Alerta amarilla 0,20–0,40 · Medio 0,40–0,60 · Alto 0,60–0,80 · Crítico ≥ 0,80.

**Limitaciones:** en modo proyección, la lluvia y el caudal se generan a partir de una climatología mensual referencial multiplicada por el factor ENSO (no son observaciones). Umbrales, susceptibilidad y vulnerabilidad son referenciales y deben calibrarse con el registro de emergencias (INDECI–SINPAD) de 2017 y 2023. Límite distrital simplificado; ubicación de sectores aproximada.

## Fuentes para la versión operativa
ENFEN (comunicados e ICEN) · SENAMHI (pronósticos, avisos y estaciones del Rímac) · INGEMMET (zonas críticas) · CENEPRED–SIGRID (escenarios de riesgo) · INEI (población y viviendas) · INDECI–SINPAD (emergencias).

## Estructura
```
app.py                 # aplicación Streamlit
index.html             # visor (mapa, ranking, gráficos, metodología)
requirements.txt       # dependencias
.streamlit/config.toml # tema oscuro
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
