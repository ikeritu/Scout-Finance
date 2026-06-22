# Scout Finance — Fase 6A: Fuente y formato del universo real inicial

## Objetivo

Pasar del universo demo a un primer universo real controlado.

No vamos a empezar con 59.000 empresas de golpe.

El objetivo inicial es:

```text
CSV real pequeño/mediano
→ normalizar columnas
→ generar data/universe/global_universe.csv
→ ejecutar embudo v0.5
→ validar resultados
```

## Recomendación inicial

Empezar con un universo USA descargado/exportado en CSV.

Orden recomendado:

```text
1. Nasdaq screener / CSV externo de acciones USA
2. Normalizar a formato Scout Finance
3. Probar con 100-500 empresas
4. Escalar a 2.000-5.000
5. Después plantear universo global
```

## Por qué no empezar con API

Todavía no conviene depender de APIs porque:

- pueden tener límites;
- pueden cambiar precios;
- puede haber errores de credenciales;
- pueden introducir datos inconsistentes;
- hacen más difícil depurar el embudo.

Primero necesitamos validar que el embudo funciona con datos reales en CSV.

## Fuentes candidatas

### Opción A — Nasdaq Stock Screener / CSV

Ventajas:

- buena fuente inicial para USA;
- útil para obtener ticker, nombre, exchange, sector, industria y market cap;
- permite trabajar sin API.

Limitaciones:

- puede requerir adaptar nombres de columnas;
- no siempre trae todos los fundamentales necesarios para Stage 2/3.

### Opción B — SEC EDGAR company tickers

Ventajas:

- fuente oficial para identificar compañías, CIK, ticker y exchange;
- útil para validar identidad y evitar duplicados.

Limitaciones:

- no es una fuente completa de métricas de mercado;
- no sustituye datos de precio, volumen, market cap o fundamentales.

### Opción C — API tipo FMP/EODHD/Polygon/Finnhub/Tiingo

Ventajas:

- mejor para escalar;
- puede traer símbolos, perfiles y fundamentales.

Limitaciones:

- depende de API key;
- límites de uso;
- coste potencial;
- requiere cache y control de errores.

## Decisión recomendada para Fase 6A

Usar CSV como entrada principal.

No usar APIs todavía.

## Formato objetivo Scout Finance

El normalizador debe generar:

```text
data/universe/global_universe.csv
```

con las columnas mínimas que ya usa Fase 5B:

```text
ticker
name
exchange
country
region
currency
sector
industry
asset_type
is_active
market_cap
price
avg_volume_30d
avg_volume_90d
data_source
last_updated
```

## Flujo de Fase 6A

```text
data/raw/universe_source.csv
↓
src.prepare_real_universe_csv
↓
data/universe/global_universe.csv
↓
src.run_global_funnel_demo o fases individuales
```

## Nota importante

Si el CSV real no trae fundamentales, Stage 2 no podrá evaluar empresas de verdad.

Eso no es un fallo.

Primero validaremos Stage 1 real.

Después vendrá:

```text
Fase 6B — Enriquecimiento de datos fundamentales
```
