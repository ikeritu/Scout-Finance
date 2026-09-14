# User Guide FAQ v2.38CC

## Que es Scout Finance?
Una app local para investigar empresas con datos ya recolectados y auditados.

## Es una recomendacion de inversion?
No. No es asesoramiento financiero ni una recomendacion de inversion.

## Que significa que el ranking sea experimental?
Significa que ordena investigacion con un score cuantitativo, pero no esta validado como prediccion de rentabilidad futura.

## Que significa el score?
Es una puntuacion relativa calculada antes de abrir la app. Ayuda a priorizar revision, no a decidir operaciones.

## Que significa confianza?
Indica cuanta cobertura y comparabilidad tienen los factores disponibles.

## Que significa cobertura?
Es el porcentaje de factores reales disponibles para una empresa dentro del contrato del ranking.

## Por que algunas empresas estan bloqueadas?
Porque tienen cobertura real insuficiente. No se rellena con datos inventados.

## Por que algunas empresas no tienen adaptador?
Porque esa jurisdiccion todavia no tiene un adaptador real de ratios o crecimiento.

## Por que algunas empresas requieren revision?
Porque necesitan revision humana o un contrato especifico, por ejemplo entidades financieras.

## Puedo usarlo para decidir comprar o vender?
No. No sirve para decidir comprar, vender o mantener. Sirve para ordenar investigacion.

## Que hago si no arranca?
Comprueba que estas en la carpeta correcta, instala dependencias y ejecuta `run_local_ui_v2_37.bat`.

## Que hago si estoy en C:\Users\ikeri y Git dice que no es un repositorio?
Ejecuta `cd "D:\Proyectos\💰 Scout Finance"` y despues `git status`.

## Que hago si falta Streamlit?
Ejecuta `python -m pip install -r requirements.txt`.

## Que hago si el puerto 8501 esta ocupado?
Cierra el Streamlit anterior o arranca manualmente en otro puerto, por ejemplo `8502`.

## Que significa Google Finance aqui?
Es solo un enlace de consulta manual. Scout Finance no descarga ni procesa datos de Google Finance.

## Que son las watchlists?
Listas privadas locales para guardar empresas que quieres revisar despues.
