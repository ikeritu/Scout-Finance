# v1.6B1 — Remove Duplicate Main Invocation Hotfix

## Objetivo

Corregir el error de Streamlit:

```text
StreamlitDuplicateElementId
```

## Causa

El archivo `app.py` ejecutaba `main()` dos veces:

```python
if __name__ == "__main__":
    main()
```

y además quedaba un residuo antiguo:

```python
main(),
```

Al ejecutarse dos veces, Streamlit creaba de nuevo los mismos `selectbox` y fallaba por IDs duplicados.

## Cambio

- Elimina el residuo `main(),`.
- Mantiene solo el `main()` protegido por `if __name__ == "__main__":`.

## No toca

- scoring
- ranking score
- market data
- fundamentales
- OpenAI
- broker
- yfinance
- APIs externas
