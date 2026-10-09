"""Run JSON fixtures and write a machine-readable report."""

import argparse
import json
from pathlib import Path

from floweval.core import Case, evaluate, report
from floweval.strategies import BASELINES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.fixtures.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        parser.error("fixtures must be a JSON array")
    cases = []
    for record in data:
        if not isinstance(record, dict):
            parser.error("each fixture must be an object")
        record = dict(record)
        for field in ("history", "memories", "profile", "expected", "forbidden"):
            values = record.get(field, [])
            if not isinstance(values, list):
                parser.error(f"{field} must be an array")
            record[field] = tuple(values)
        cases.append(Case(**record))
    payload = json.dumps(report(evaluate(tuple(cases), BASELINES)), indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
