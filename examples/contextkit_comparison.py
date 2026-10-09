"""Optional integration example: install ContextKit 0.2 separately before running."""

from agent_memory_kit import MemoryEngine, Observation, Scope, SessionMemory
from agent_memory_kit.adapters import InMemoryStore
from contextkit import ContextCompiler, ContextManager

from floweval import Case, evaluate, report


def with_memory(case: Case) -> str:
    store = InMemoryStore()
    scope = Scope("evaluation", case.id)
    engine = MemoryEngine(store)
    for number, content in enumerate(case.memories):
        engine.observe(
            scope,
            Observation(
                f"event-{number}", f"record-{number}", 1, content, (f"fixture:{case.id}",)
            ),
        )
    manager = ContextManager(ContextCompiler(store), SessionMemory(), count_tokens=len)
    return manager.build(
        scope, session_id="trial", query=case.query, max_tokens=8000, reserved_tokens=500
    ).render()


case = Case("diet", "Plan dinner", memories=("Vegetarian meals",), expected=("vegetarian",))
results = evaluate(
    (case,), {"no-memory": lambda case: case.query, "contextkit-memory": with_memory}
)
print(report(results))
