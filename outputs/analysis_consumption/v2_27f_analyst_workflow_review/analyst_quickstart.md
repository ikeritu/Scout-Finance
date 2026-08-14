# Analyst quickstart — metadata workflow

## 1. Create a watchlist

```bash
python scripts/watchlist_builder_v2_27c.py init my_watchlist.json --name "Review list"
```

## 2. Add an asset

Use the stable identity whenever available. Otherwise provide ticker and exchange to prevent ambiguity.

```bash
python scripts/watchlist_builder_v2_27c.py add my_watchlist.json --catalog universe.csv --ticker SAN --exchange XMAD --tags bank,review --note "Review fundamentals separately"
```

## 3. Validate and export

```bash
python scripts/watchlist_builder_v2_27c.py validate my_watchlist.json --catalog universe.csv
python scripts/watchlist_builder_v2_27c.py export my_watchlist.json --output my_watchlist.csv
```

## 4. Check scoring state

```bash
python scripts/score_explorer_v2_27d.py --pointer outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json --output score_explorer.html
```

Today this correctly displays **FAIL-CLOSED**.

## 5. Generate a watchlist report

```bash
python scripts/report_generator_v2_27e.py --type watchlist --watchlist my_watchlist.json --scoring-pointer outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json --format html --output my_watchlist_report.html
```

The report is informational. It does not rank assets or recommend investments.
