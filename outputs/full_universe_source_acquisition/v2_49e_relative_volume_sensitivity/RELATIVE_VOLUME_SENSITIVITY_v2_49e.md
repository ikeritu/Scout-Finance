# v2.49E — sensibilidad horaria del volumen relativo, aviso de sesión y comparación

Estado: `RELATIVE_VOLUME_SENSITIVITY_DOCUMENTED`. Código nuevo: un aviso de sesión de EE. UU. (solo presentación) y un script de comparación de solo lectura. **No se cambia el score ni el cálculo del volumen relativo.**

## Por qué importa
El volumen relativo decide señales y niveles: con ≥ 2 suma 9 puntos y, si el movimiento a 20 días es ≥ 20 %, activa además la señal de ruptura (+10, y cuenta como señal fuerte); con ≥ 3 suma 18. El único candidato que apareció (Cracker Barrel) dependía de ese corte: 44 puntos en vigilancia con 1,99 y 63 puntos como candidato con 2,03.

## Hechos observados
- **Horas de las dos búsquedas** (equipo en hora de Madrid): la del 16-oct a las 21:34 fue a las 15:34 en Nueva York, con el mercado abierto; la del 17-oct a las 00:44, a las 18:44, ya cerrado.
- **Qué lee la app:** `volume` de Yahoo (el volumen del día) entre `averageVolume` (media de 3 meses). El campo que el código intenta primero, `fast_info.last_volume`, no devolvió nada en las 22 empresas probadas; siempre se usa el segundo.
- **Con el mercado cerrado el volumen es estable:** coincide con la barra diaria de Yahoo con diferencias inferiores al 3 % en 21 de 22 empresas (la mayor entre ellas, AEYE, un 2,8 %); una (ANAB) difiere un 27 % entre las dos fuentes de Yahoo.
- **El denominador cambia tras el cierre**, al incluir el día que acaba de pasar: volumen relativo guardado a las 00:44 frente a una consulta posterior: CBRL 2,03 → 1,99; ARRY 3,23 → 3,17; ALLT 14,58 → 12,15 (su media sube de unos 309 mil a 370 mil al incluir el pico).
- **Consecuencia:** con datos de una consulta posterior, CBRL puntúa 44 y vuelve a «En vigilancia». Un cambio del 2 % en un cociente movió 19 puntos y el nivel.
- **Exposición** (datos guardados): 3 empresas a menos del 5 % del corte de 2,0 y 7 por encima; 1 a menos del 5 % del corte de 3,0 y 2 por encima.

## Inferencias (no medidas)
- La búsqueda de las 15:34 leyó un volumen parcial del día; es coherente con que CBRL puntuara 44 entonces y 63 después, pero no se midió.
- Con la sesión abierta el volumen relativo sale más bajo que al cierre. Cuánto más bajo no se ha medido: hoy es sábado y no hay sesión que consultar. **Pendiente:** repetir la sonda un día laborable durante la sesión y de nuevo tras el cierre.

## Comparación con un cálculo desde las barras diarias
Alternativa: volumen de la última sesión **completa** entre la media de las N sesiones anteriores (esa sesión excluida), con las barras ya guardadas en la caché local. Cada empresa se vuelve a puntuar con la puntuación vigente (volumen relativo y señal de ruptura); `scripts/compare_relative_volume_v2_49e.py` lo reproduce sin red ni escrituras. Resultados con los datos del 17-oct (140 empresas comparables):

| Ventana | Correlación de rangos | Mediana alternativo/actual | Cambian de lado en el corte de 2,0 | Empresas con puntos distintos | Nivel distinto | CBRL |
|---|---|---|---|---|---|---|
| 60 sesiones | 0,997 | 1,00 | 0 | 1 (máx. 9 puntos) | 0 | 2,04 → sigue candidato |
| 40 sesiones | 0,937 | 1,04 | 2 | 3 (máx. 19) | 1 | 1,91 → 44, en vigilancia |
| 20 sesiones | 0,840 | 1,02 | 2 | 2 (máx. 19) | 1 | 1,64 → 44, en vigilancia |

Los resúmenes completos están en `comparison_window_20.md`, `_40.md` y `_60.md` (solo cifras derivadas; los precios y volúmenes de origen quedan en la caché local).

### Lectura
- **Con 60 sesiones el alternativo reproduce el cálculo de hoy** (misma ordenación, mediana 1,00, ningún cambio de nivel) y elimina las dos inestabilidades: no depende de la hora de la búsqueda y numerador y denominador salen de la misma fuente. Es una sustitución de bajo impacto.
- **El resultado de CBRL depende de la ventana elegida** (60 lo mantiene, 40 y 20 lo sacan). La condición de «candidato» está en el borde de un corte escalonado y no es robusta a decisiones razonables de método. Eso es independiente de qué fuente de volumen se use.
- Decisión pendiente (de producto): adoptar el cálculo desde barras con ventana de 60 sesiones y, aparte, si se suavizan los cortes escalonados.

## Qué cambia en la app
- **Aviso:** si la sesión de EE. UU. puede estar abierta (lunes a viernes, 9:30–16:00 hora de Nueva York), la página de búsqueda avisa de que el volumen de hoy es parcial y de a partir de qué hora local buscar. Está redactado como posibilidad porque no se conocen los festivos. No bloquea la búsqueda.
- **Etiqueta de los datos:** si la última caché se guardó en sesión, el resumen añade «con el mercado de EE. UU. en sesión: el volumen de ese día era parcial».
- La variable `SCOUT_FINANCE_FAKE_NOW_UTC` fija el reloj en las pruebas (sin definirla se usa la hora real).

## Pruebas
`tests/qa_us_session_warning_v2_49e.py` (límites exactos de la sesión en horario de verano e invierno, fines de semana, cambios de hora de marzo y noviembre, aviso y etiqueta en la app real con reloj simulado) y `tests/qa_relative_volume_comparison_v2_49e.py` (la sesión medida queda fuera de su propia base, base completa y positiva, re-puntuación con la puntuación vigente, resumen). El entorno de pruebas compartido fija ahora un sábado para no depender de cuándo se ejecuta.
