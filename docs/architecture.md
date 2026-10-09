# Architecture

- Five transparent baselines: no memory, short-term, summary, retrieval and personalized memory.
- User-defined strategy callbacks; no dependency on either sibling repository.
- Expected phrase coverage, forbidden phrase hits, fixture pass rate and strategy errors.
- Output character count, optional caller-supplied token count and measured strategy latency.
- JSON fixture input and machine-readable CLI reports.

Bundled baselines select context; they do not call an LLM. Case-insensitive substring checks evaluate synthetic fixture requirements, not semantic task success or research-proven personalization. Query text is part of baseline output and can satisfy a check, so expected phrases should describe information absent from the query. Lexical retrieval is a baseline, not vector retrieval. Latency covers strategy execution only, not scoring or model latency unless your callback includes it. Token counts are absent unless you supply a tokenizer; characters are not tokens. No monetary cost is inferred. There is no sandbox for custom callbacks.

The three repositories have separate release cycles. Memory Kit owns canonical memory and reference session storage. ContextKit owns context assembly and budgeting. FlowEval owns experiments and measurement; callbacks can target either library or unrelated applications.
