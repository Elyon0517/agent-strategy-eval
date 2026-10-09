"""Provider-independent evaluation with explicit fixture-based scoring."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any


@dataclass(frozen=True)
class Case:
    id: str
    query: str
    history: tuple[str, ...] = ()
    memories: tuple[str, ...] = ()
    profile: tuple[str, ...] = ()
    summary: str = ""
    expected: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("case ID is required")
        if not isinstance(self.query, str) or not isinstance(self.summary, str):
            raise ValueError("query and summary must be strings")
        for values in (
            self.history,
            self.memories,
            self.profile,
            self.expected,
            self.forbidden,
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError("case lists must be tuples of nonempty strings")
        normalized = [value.casefold() for value in self.expected]
        if len(set(normalized)) != len(normalized):
            raise ValueError("expected phrases must be unique")
        if set(normalized) & {value.casefold() for value in self.forbidden}:
            raise ValueError("a phrase cannot be both expected and forbidden")


@dataclass(frozen=True)
class Measurement:
    case_id: str
    strategy: str
    expected_coverage: float | None
    forbidden_hits: int
    passed: bool | None
    output_chars: int
    output_tokens: int | None
    latency_ms: float
    error: str | None


def evaluate(
    cases: tuple[Case, ...],
    strategies: dict[str, Callable[[Case], str]],
    *,
    count_tokens: Callable[[str], int] | None = None,
) -> list[Measurement]:
    if not cases or not strategies:
        raise ValueError("provide at least one case and strategy")
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("case IDs must be unique")
    if any(not name.strip() or not callable(fn) for name, fn in strategies.items()):
        raise ValueError("strategies require names and callables")
    measurements = []
    for case in cases:
        for name, strategy in strategies.items():
            started = perf_counter()
            try:
                output = strategy(case)
                latency = (perf_counter() - started) * 1000
                if not isinstance(output, str):
                    raise ValueError("strategy must return text")
                tokens = None if count_tokens is None else count_tokens(output)
                if tokens is not None and (
                    isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0
                ):
                    raise ValueError("token counter must return a nonnegative integer")
                lowered = output.casefold()
                hits = sum(phrase.casefold() in lowered for phrase in case.expected)
                forbidden = sum(phrase.casefold() in lowered for phrase in case.forbidden)
                coverage = hits / len(case.expected) if case.expected else None
                passed = (
                    (hits == len(case.expected) and forbidden == 0)
                    if (case.expected or case.forbidden)
                    else None
                )
                measurements.append(
                    Measurement(
                        case.id,
                        name,
                        coverage,
                        forbidden,
                        passed,
                        len(output),
                        tokens,
                        latency,
                        None,
                    )
                )
            except Exception as error:
                measurements.append(
                    Measurement(
                        case.id,
                        name,
                        None,
                        0,
                        False,
                        0,
                        None,
                        (perf_counter() - started) * 1000,
                        type(error).__name__,
                    )
                )
    return measurements


def report(measurements: list[Measurement]) -> dict[str, Any]:
    if not measurements:
        raise ValueError("no measurements to report")
    groups: dict[str, list[Measurement]] = {}
    for row in measurements:
        groups.setdefault(row.strategy, []).append(row)
    aggregate = {}
    for name, rows in groups.items():
        scored = [row for row in rows if row.passed is not None]
        aggregate[name] = {
            "cases": len(rows),
            "errors": sum(row.error is not None for row in rows),
            "scored_cases": len(scored),
            "fixture_pass_rate": sum(row.passed is True for row in scored) / len(scored)
            if scored
            else None,
            "mean_output_chars": sum(row.output_chars for row in rows) / len(rows),
            "mean_latency_ms": math.fsum(row.latency_ms for row in rows) / len(rows),
        }
    return {
        "schema_version": 1,
        "scoring": "case-insensitive substring fixture checks",
        "strategies": aggregate,
        "measurements": [asdict(row) for row in measurements],
    }
