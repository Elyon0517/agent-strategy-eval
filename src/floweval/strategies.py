"""Transparent context-selection baselines, without model calls."""

import re
from collections.abc import Callable

from floweval.core import Case


def no_memory(case: Case) -> str:
    return case.query


def short_term(case: Case) -> str:
    return "\n".join((*case.history[-4:], case.query))


def summary_memory(case: Case) -> str:
    return "\n".join((case.summary, case.query))


def retrieval_memory(case: Case) -> str:
    words = set(re.findall(r"\w+", case.query.casefold()))
    ranked = sorted(
        enumerate(case.memories),
        key=lambda item: (
            -len(words & set(re.findall(r"\w+", item[1].casefold()))),
            item[0],
        ),
    )
    selected = [
        value for _, value in ranked[:3] if words & set(re.findall(r"\w+", value.casefold()))
    ]
    return "\n".join((*selected, case.query))


def personalized_memory(case: Case) -> str:
    return "\n".join((*case.profile, retrieval_memory(case)))


BASELINES: dict[str, Callable[[Case], str]] = {
    "no-memory": no_memory,
    "short-term": short_term,
    "summary-memory": summary_memory,
    "retrieval-memory": retrieval_memory,
    "personalized-memory": personalized_memory,
}
