import json
import subprocess
import sys
from pathlib import Path

import pytest

from floweval import Case, evaluate, report
from floweval.strategies import BASELINES


def test_coverage_forbidden_and_tokens():
    case = Case("a", "q", expected=("Boston", "vegetarian"), forbidden=("Seattle",))
    row = evaluate((case,), {"s": lambda c: "BOSTON Seattle"}, count_tokens=lambda s: 2)[0]
    assert row.expected_coverage == 0.5
    assert row.forbidden_hits == 1
    assert row.passed is False
    assert row.output_tokens == 2


def test_strategy_failure_is_recorded_and_others_run():
    def broken(case):
        raise RuntimeError("private credentials must not enter reports")

    rows = evaluate(
        (Case("a", "q", expected=("yes",)),), {"bad": broken, "good": lambda c: "yes"}
    )
    assert rows[0].error == "RuntimeError"
    assert rows[1].passed is True
    assert "private" not in json.dumps(report(rows))
    assert report(rows)["strategies"]["bad"]["fixture_pass_rate"] == 0


def test_unscored_case_is_not_success():
    row = evaluate((Case("a", "q"),), {"s": lambda c: "anything"})[0]
    assert row.expected_coverage is None and row.passed is None
    assert report([row])["strategies"]["s"]["fixture_pass_rate"] is None


def test_distinct_baselines():
    case = Case(
        "a",
        "dinner",
        history=("recent",),
        summary="summary",
        memories=("dinner vegetarian", "unrelated"),
        profile=("Spanish",),
    )
    rows = evaluate((case,), BASELINES)
    assert len(rows) == 5
    assert len({strategy(case) for strategy in BASELINES.values()}) == 5
    assert "unrelated" not in BASELINES["retrieval-memory"](case)


def test_cli(tmp_path):
    output = tmp_path / "report.json"
    fixtures = Path(__file__).resolve().parents[1] / "examples/fixtures.json"
    subprocess.run(
        [sys.executable, "-m", "floweval.cli", str(fixtures), "--output", str(output)],
        check=True,
    )
    data = json.loads(output.read_text())
    assert len(data["measurements"]) == 15
    assert data["schema_version"] == 1


@pytest.mark.parametrize("tokens", [-1, True, 1.5])
def test_bad_token_count_recorded(tokens):
    row = evaluate((Case("a", "q"),), {"s": lambda c: "x"}, count_tokens=lambda text: tokens)[0]
    assert row.error == "ValueError"


def test_duplicate_case_ids_rejected():
    with pytest.raises(ValueError):
        evaluate((Case("a", "q"), Case("a", "q")), BASELINES)


def test_contradictory_fixture_rejected():
    with pytest.raises(ValueError):
        Case("a", "q", expected=("Boston",), forbidden=("boston",))
