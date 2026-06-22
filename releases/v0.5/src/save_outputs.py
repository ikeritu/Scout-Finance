"""Save Scout Finance analysis outputs."""
from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from src.validate_analysis import validate_analysis_json

def _safe_token(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", str(value).strip().upper())
    return re.sub(r"_+", "_", cleaned).strip("_") or "UNKNOWN"

def build_output_stem(ticker: str, analysis_date: str | None = None) -> str:
    if analysis_date:
        try:
            dt = datetime.fromisoformat(str(analysis_date).replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return f"{_safe_token(ticker)}_{dt.strftime('%Y%m%d_%H%M%S')}"

def save_markdown_and_json(ticker: str, markdown_report: str, json_data: dict[str, Any], output_dir: str | Path = "outputs/analyses") -> dict[str, Path]:
    validation = validate_analysis_json(json_data)
    if not validation.is_valid:
        raise ValueError(f"Analysis JSON is invalid. Files were not saved.\nErrors: {validation.errors}\nWarnings: {validation.warnings}")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    stem = build_output_stem(ticker, json_data.get("analysis_date"))
    md_path = output_path / f"{stem}.md"
    json_path = output_path / f"{stem}.json"
    md_path.write_text(markdown_report, encoding="utf-8")
    json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}

def save_analysis_outputs(ticker: str, markdown_report: str, json_data: dict[str, Any], output_dir: str | Path = "outputs/analyses", create_visualizations: bool = True) -> dict[str, Path]:
    paths = save_markdown_and_json(ticker, markdown_report, json_data, output_dir)
    if not create_visualizations:
        return paths
    from src.visualizations import save_executive_card_html, save_scenarios_png, save_scorecard_png
    json_path = paths["json"]
    stem = json_path.stem
    out = json_path.parent
    scorecard = out / f"{stem}_scorecard.png"
    scenarios = out / f"{stem}_scenarios.png"
    executive = out / f"{stem}_executive_card.html"
    save_scorecard_png(json_data, scorecard)
    save_scenarios_png(json_data, scenarios)
    save_executive_card_html(json_data, executive)
    paths.update({"scorecard_png": scorecard, "scenarios_png": scenarios, "executive_card_html": executive})
    return paths
