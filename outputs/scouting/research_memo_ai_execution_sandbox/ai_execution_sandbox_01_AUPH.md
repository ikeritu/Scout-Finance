# AI Execution Sandbox — AUPH

- Phase: 8I
- Company: Aurinia Pharmaceuticals Inc - Common Shares
- Ranking position: 1
- Quant score: 70.83
- AI gate status: closed
- AI allowed: False
- Execution status: skipped_gate_closed
- Estimated cost: 0.0
- Model used: None
- OpenAI called: False

## Skip reason

ENABLE_OPENAI is not True; ENABLE_AI_RESEARCH_MEMO is not True; ALLOW_AI_SPEND is not True; SCOUT_FINANCE_ALLOW_REAL_AI_EXECUTION is not True; AI_RESEARCH_MEMO_MAX_COST_USD must be > 0 for real execution; AI_RESEARCH_MEMO_MODEL is not configured

## Safety rules

- No inventar datos
- Marcar data_insufficient cuando falten datos
- Separar Objective data y AI interpretation
- No financial advice
- TOP N limitado a 3

## Simulated response

```json
{
  "ticker": "AUPH",
  "memo_status": "data_insufficient",
  "ai_interpretation_status": "skipped_gate_closed",
  "summary": "No AI response generated. Phase 8I is an execution sandbox and guardrail validation phase.",
  "data_policy": {
    "no_inventar_datos": true,
    "mark_data_insufficient": true,
    "objective_data_only": true
  },
  "data_gaps": "[\"financial_health: revenue_growth\", \"financial_health: gross_margin\", \"financial_health: operating_margin\", \"financial_health: net_margin\", \"financial_health: roe\", \"financial_health: roa\", \"financial_health: debt_to_equity\", \"financial_health: current_ratio\", \"financial_health: free_cash_flow\", \"valuation_analysis: pe\", \"valuation_analysis: price_to_sales\", \"valuation_analysis: price_to_book\", \"valuation_analysis: ev_to_ebitda\", \"valuation_analysis: fcf_yield\", \"risk_analysis: beta\", \"risk_analysis: volatility\", \"risk_analysis: max_drawdown\", \"risk_analysis: debt_to_equity\", \"risk_analysis: short_ratio\", \"risk_analysis: current_ratio\", \"risk_analysis: market_cap\", \"moat_analysis: gross_margin\", \"moat_analysis: operating_margin\", \"moat_analysis: roe\", \"moat_analysis: roic\", \"moat_analysis: revenue_growth\", \"growth_analysis: revenue_growth\", \"growth_analysis: earnings_growth\", \"growth_analysis: ebitda_growth\", \"growth_analysis: free_cash_flow_growth\", \"growth_analysis: analyst_growth\", \"institutional_view: institutional_ownership\", \"institutional_view: insider_ownership\", \"institutional_view: analyst_count\", \"institutional_view: recommendation_mean\", \"earnings_analysis: eps_growth\", \"earnings_analysis: revenue_growth\", \"earnings_analysis: earnings_surprise\", \"earnings_analysis: next_earnings_date\", \"business_model: local ranking rows do not provide enough company narrative data.\"]"
}
```
