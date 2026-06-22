# Scout Finance — Phase 8G Optional AI Interpretation Gate and Cost Guardrails

## Status

- Status: OK
- Memos loaded: 3
- Default TOP N: 3
- MAX TOP N: 3
- AI gate status: closed
- AI allowed: False
- Gate reason: ENABLE_OPENAI is not True; ENABLE_AI_RESEARCH_MEMO is not True; ALLOW_AI_SPEND is not True
- OpenAI called: False
- API called: False
- yfinance called: False
- Pipeline recalculated: False
- Estimated cost: 0.0
- Model used: null

## Guardrails

- ENABLE_OPENAI must be true.
- ENABLE_AI_RESEARCH_MEMO must be true.
- ALLOW_AI_SPEND must be true.
- TOP N is capped at 3.
- No inventar datos.
- Objective data must stay separated from AI interpretation.
- data_insufficient must be preserved when facts are missing.
- This phase does not call OpenAI; it only decides whether a later phase may be allowed to do so.

## Memos considered

- 1. AUPH — Aurinia Pharmaceuticals Inc - Common Shares — blocked_by_gate
- 2. BZ — KANZHUN LIMITED - American Depository Shares — blocked_by_gate
- 3. ADBE — Adobe Inc. - Common Stock — blocked_by_gate

## Next

8H — Prompt packaging and dry-run AI memo preview.
