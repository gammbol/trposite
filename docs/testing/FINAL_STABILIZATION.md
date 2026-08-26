# Final reliability stabilization

The final stabilization pass is based on failure modes exercised by the test cluster.

## Fixed issues

### Structured LLM output
The old recovery parser counted `{` and `}` characters manually. Braces inside JSON
string values (for example LaTeX sets and piecewise notation) could terminate the
object at the wrong position. Parsing now uses `json.JSONDecoder.raw_decode`, which
understands JSON string boundaries.

### Insufficient numerical evidence
A numerical check could previously pass after only one evaluable point when most
sample points were singular or otherwise skipped. A candidate now needs a minimum
number of independent valid samples before the numerical stage can pass.

### Provider failure latency
Consensus evaluation used to regard Ollama as always available. If the service was
offline, a generation request could wait for the full inference timeout. A fast
`/api/tags` health probe now marks the provider unavailable before consensus starts.
OpenAI-compatible providers also have explicit request timeouts and bounded retries.

### Confidence bounds
All verification confidence components and the final score are now clamped to the
closed interval `[0, 1]`, preventing malformed/custom check results from corrupting
ranking.

### SymPy multi-branch output
Reference solving now accepts list/tuple results from `dsolve`, keeps alternative
branches for diagnostics and selects a deterministic canonical branch for the
current verification pipeline.

## Regression coverage
Regression and resilience tests were added for JSON containing braces in strings,
provider availability, score bounds and minimum numerical evidence.
