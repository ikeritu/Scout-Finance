# v2.33F — evaluación documental de fuentes oficiales por bolsa

Estado: **evaluación completada · sin fuente única que resuelva el problema completo**.

No se ha creado ninguna cuenta, ni usado ninguna clave, ni descargado datos, ni gastado dinero. Solo investigación de fuentes públicas.

## Resultado

- "Cboe Europe" (119 símbolos bloqueados) no es una bolsa de origen: son emisores de docenas de países distintos negociados en una plataforma de cruce paneuropea. No existe una única fuente oficial que resolverlos; primero haría falta un mapeo de identificadores (OpenFIGI, no ejecutado).
- **J-Quants (JPX/Japón, 42 símbolos bloqueados):** candidata más prometedora — oficial, gratuita, 2 años de histórico (mejor que EODHD), con 12 semanas de retraso y restricciones de redistribución.
- **Datos abiertos del gobierno de Taiwán (`data.gov.tw`):** oficial, gratuito, actualizado a diario; podría mejorar la profundidad de los 8 activos TWSE ya resueltos.
- Alemania/Xetra: solo existe un dataset público obsoleto (AWS), no viable.
- ASX y BVC: no se encontró ninguna fuente oficial gratuita.

Detalle completo, fuentes citadas y clasificación de la evidencia en `OFFICIAL_EXCHANGE_SOURCES_EVALUATION_v2_33f.md`.
