# Scout Finance — Safety Limits

## 1. No es asesoramiento financiero

Scout Finance no da recomendaciones de compra o venta. Los resultados son material de análisis y requieren revisión humana.

## 2. No trading automático

Prohibido convertir esta versión en:

```text
bot de trading
sistema de señales automáticas
ejecutor de órdenes
agente autónomo
```

## 3. IA real desactivada

La capa IA de v0.9 está en dry-run.

```text
openai_called=False
api_called=False
yfinance_called=False
pipeline_recalculated=False
model_used=None
estimated_cost=0.0
```

## 4. Decisión humana obligatoria

Todo candidato debe pasar por estados manuales:

```text
pending_review
reviewed_watchlist
reviewed_reject
needs_more_data
```

## 5. No tocar freezes

No modificar directamente:

```text
releases/Scout_Finance_v0.9.0_experimental_ai_FREEZE.zip
releases/Scout_Finance_v1.0.0_candidate_FREEZE.zip
```

Si se necesita cambiar algo, abrir nueva fase.

## 6. Regla para futuras APIs

No añadir proveedores externos sin:

```text
flag explícito
dry-run por defecto
caché local
coste estimado
log de llamadas
checker de seguridad
```

## 7. Regla para OpenAI real

No activar OpenAI real sin:

```text
confirmación manual
modo dry-run conservado
estimación de coste
registro de modelo
registro de input/output
not_financial_advice=True
manual_review_required=True
```

## 8. Criterio de parada

Si una mejora no ayuda a revisar mejores candidatos o reducir errores humanos, no se implementa.
