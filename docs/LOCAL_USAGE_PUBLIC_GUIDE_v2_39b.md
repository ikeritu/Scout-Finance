# Local Usage Public Guide v2.39B

Scout Finance is a local research tool for exploring an experimental global ranking built from the project's validated local outputs.

It is not financial advice, it does not create recommendations, and it does not include a broker workflow. The ranking is experimental and must be interpreted with the documented limitations visible in the project reports.

## Stable Reference

- Branch: `phase9b-global-enrichment-v2-38b`
- Stable tag: `v2.38CJ-local-stable`
- Scope: `local_research_tool_only`

## Local Startup

```powershell
cd "D:\Proyectos\Scout Finance"
pip install -r requirements.txt
run_local_ui_v2_37.bat
```

Open Streamlit at `http://localhost:8501` and use the global experimental ranking screen.

Windows paths with spaces or emoji must be wrapped in quotes. For example, use `cd "D:\Proyectos\Scout Finance"` or your own quoted local path.

## Ranking Populations

- Main ranking: 318 assets with enough comparable evidence for the experimental ranking.
- Partial comparability: 373 assets with usable but incomplete comparability.
- Review required: 124 assets that need manual or methodological review before interpretation.
- Blocked: 270 assets with insufficient coverage.
- No adapter: 26 assets whose data exists but does not yet have a scoring adapter.

## Known Limitations

The project keeps documented limitations visible by design: data coverage gaps, European source constraints, Cboe Europe deferred scope, UK automation blockers, environment warnings and experimental ranking guardrails.
