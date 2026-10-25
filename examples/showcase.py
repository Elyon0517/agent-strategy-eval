"""Evaluate the bundled fixtures and generate an inspectable HTML scorecard.

From the repository root: python examples/showcase.py
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from floweval import Case, evaluate, report
from floweval.strategies import BASELINES


def main() -> None:
    fixtures = json.loads(Path(__file__).with_name("fixtures.json").read_text())
    cases = tuple(
        Case(
            **{
                key: tuple(value) if isinstance(value, list) else value
                for key, value in row.items()
            }
        )
        for row in fixtures
    )
    result = report(evaluate(cases, BASELINES))
    assert len(result["measurements"]) == len(cases) * len(BASELINES)
    assert all(row["error"] is None for row in result["measurements"])
    out = Path("docs/showcase")
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    cards = ""
    for name, stats in result["strategies"].items():
        rate = stats["fixture_pass_rate"]
        percent = "unscored" if rate is None else f"{rate:.0%}"
        width = 0 if rate is None else rate * 100
        cards += (
            f'<article class="card"><small>BASELINE</small><h3>{escape(name)}</h3>'
            f"<p><strong>{percent}</strong> fixture pass rate · "
            f"{stats['scored_cases']} cases</p>"
            f'<div class="bar"><i style="width:{width}%"></i></div>'
            f"<p>{stats['mean_output_chars']:.0f} mean output characters · "
            f"{stats['errors']} errors</p></article>"
        )
    rows = ""
    for row in result["measurements"]:
        case = next(c for c in cases if c.id == row["case_id"])
        output = BASELINES[row["strategy"]](case)
        state = "PASS" if row["passed"] else "FAIL" if row["passed"] is False else "UNSCORED"
        rows += (
            f'<tr data-case="{escape(case.id, quote=True)}"><td>{escape(case.id)}</td>'
            f'<td>{escape(row["strategy"])}</td><td class="{state.lower()}">{state}</td>'
            f"<td>{row['output_chars']}</td><td><details><summary>Inspect context</summary>"
            f"<p>Expected: {escape(', '.join(case.expected))}</p><pre>{escape(output)}</pre>"
            "</details></td></tr>"
        )
    options = "".join(f"<option>{escape(c.id)}</option>" for c in cases)
    css = Path(__file__).with_name("showcase.css").read_text()
    document = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Strategy Eval — fixture scorecard</title><style>{css}</style>
<main><header><div class="eyebrow">AGENT STRATEGY EVAL / OFFLINE SCORECARD</div>
<h1>Which context survives?</h1><p>Compare five memory strategies on the same fixtures.
Inspect the selected context behind every pass and failure.</p></header>
<div class="stats"><div class="stat"><strong>{len(BASELINES)}</strong>
transparent baselines</div>
<div class="stat"><strong>{len(cases)}</strong>synthetic fixtures</div>
<div class="stat"><strong>{len(result["measurements"])}</strong>
measured strategy / case pairs</div></div>
<div class="flow"><span>JSON fixtures</span>→<span>Context selection</span>→
<span>Phrase checks</span>→<span>Inspectable report</span></div>
<div class="grid">{cards}</div><h2>Look beyond the aggregate</h2>
<label for="fixture">Fixture</label> <select id="fixture">
<option value="all">All fixtures</option>{options}</select>
<table><thead><tr><th>Fixture</th><th>Strategy</th><th>Result</th><th>Characters</th>
<th>Evidence</th></tr></thead><tbody>{rows}</tbody></table>
<footer>Real execution of bundled baselines; no LLM calls. Scores use case-insensitive substring
checks on synthetic fixtures, not semantic task success. Characters are not tokens.
<a href="report.json">Download full JSON including measured latency</a></footer></main>
<script>document.querySelector('#fixture').addEventListener('change',event=>{{
document.querySelectorAll('tbody tr').forEach(row=>{{row.hidden=event.target.value!=='all'&&
row.dataset.case!==event.target.value;}});}});</script></html>"""
    (out / "index.html").write_text(document)
    print(f"Evaluated {len(result['measurements'])} pairs; open {out / 'index.html'}")


if __name__ == "__main__":
    main()
