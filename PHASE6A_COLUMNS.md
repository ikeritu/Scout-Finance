# Scout Finance — Columnas universo real

## Entrada flexible

El CSV real puede traer columnas con nombres distintos.

Ejemplos habituales:

```text
Symbol
Name
Last Sale
Net Change
% Change
Market Cap
Country
IPO Year
Volume
Sector
Industry
```

o:

```text
ticker
company_name
exchange
market_cap
price
volume
sector
industry
```

## Salida obligatoria

El normalizador debe producir:

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

## Reglas de normalización

### ticker

- mayúsculas;
- sin espacios;
- obligatorio.

### name

- nombre de empresa;
- si falta, usar ticker como fallback.

### exchange

- si falta, usar UNKNOWN;
- si viene como NasdaqGS/NasdaqGM, mapear a NASDAQ.

### country

- si falta, usar USA para universo USA inicial.

### region

- si country = USA, North America.

### currency

- por defecto USD para universo USA.

### sector / industry

- si faltan, usar Unknown.

### asset_type

- por defecto common_stock.

### is_active

- por defecto true.

### market_cap

- convertir a número;
- soportar valores con $, comas, M, B, T.

### price

- convertir a número;
- soportar valores con $.

### avg_volume_30d / avg_volume_90d

- si solo hay Volume, usar el mismo valor para ambas columnas temporalmente.

### data_source

- por ejemplo nasdaq_csv, manual_csv, fmp_csv.

### last_updated

- fecha actual si no viene en el CSV.
