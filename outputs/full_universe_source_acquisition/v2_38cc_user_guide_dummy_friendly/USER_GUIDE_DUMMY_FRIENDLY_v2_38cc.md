# User Guide Dummy Friendly v2.38CC

## Que es Scout Finance

Scout Finance es una aplicacion local para investigar empresas. Lee datos y resultados que ya existen en tu ordenador y los muestra de forma ordenada.

## Que no es

No es asesoramiento financiero. No predice rentabilidad. No da precio objetivo. No crea senales de comprar, vender o mantener. No se conecta a brokers.

## Arranque rapido

1. Abre PowerShell.
2. Entra en la carpeta: `cd "D:\Proyectos\💰 Scout Finance"`.
3. Instala dependencias si hace falta: `python -m pip install -r requirements.txt`.
4. Arranca la app: `.\run_local_ui_v2_37.bat`.
5. Abre `http://localhost:8501` si el navegador no se abre solo.

## Pantallas principales

- `Inicio`: confirma que la app carga.
- `Universo global (43.089)`: muestra todas las empresas y la cobertura real.
- `Ranking global (experimental)`: muestra el ranking de investigacion.
- `Watchlist`: guarda empresas para revisarlas despues.

## Ranking global experimental

El ranking global experimental ordena empresas para priorizar investigacion. El resultado actual contiene 1111 empresas evaluadas: 318 en ranking principal, 373 con comparabilidad parcial, 124 en revision, 270 bloqueadas y 26 sin adaptador.

## Score

El score es una puntuacion relativa ya calculada antes de abrir la app. Un score mas alto solo significa mas prioridad de investigacion dentro de este modelo experimental.

## Confianza

La confianza resume la calidad de comparacion. `HIGH` y `MEDIUM` entran en el ranking principal; `LOW` queda separado como comparabilidad parcial.

## Cobertura

La cobertura indica cuantos factores reales existen para una empresa. Si la cobertura es demasiado baja, la empresa queda bloqueada.

## Estados

- `ELIGIBLE_PARTIAL`: aparece en el ranking principal.
- `PARTIAL_COMPARABILITY`: tiene score, pero se separa por menor comparabilidad.
- `REVIEW_REQUIRED`: necesita revision antes de cualquier puntuacion automatica.
- `BLOCKED`: no tiene cobertura suficiente.
- `NOT_YET_SCORED_NO_ADAPTER`: falta un adaptador real para esa jurisdiccion.

## Filtros y exportacion

Puedes buscar por empresa, ticker, ID o pais. Tambien puedes filtrar por pais, confianza, rango de score, rango de cobertura y Top N. El CSV filtrado exporta informacion de investigacion, no datos privados de watchlist.

## Google Finance

El enlace a Google Finance es una ayuda manual. Abre una busqueda para que revises informacion externa por tu cuenta. Scout Finance no descarga datos de Google.

## Watchlists

Las watchlists son listas privadas locales. Sirven para guardar empresas que quieres revisar mas tarde con tus propias notas.

## Limitaciones

Hay paises con cobertura parcial, empresas sin precio real, jurisdicciones sin adaptador, entidades financieras con contrato pendiente y empresas bloqueadas por falta de datos. La herramienta sigue siendo experimental.

## Errores frecuentes

- Si Git dice que no es un repositorio, entra primero en `D:\Proyectos\💰 Scout Finance`.
- Si falta Streamlit, ejecuta `python -m pip install -r requirements.txt`.
- Si el puerto `8501` esta ocupado, cierra la app anterior o usa otro puerto.
- Si falta un output, no inventes datos: revisa que la fase correspondiente este generada.
