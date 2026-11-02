# Code Mode measurements

Measured on Windows 11, Python 3.13.15 and Deno 2.9.6. Five repetitions per scenario, real generated 4-second
1080x1920 FFmpeg fixture, temporary workspace, **zero social provider API requests**. Results are observations
from this machine, not production latency predictions. [Raw results](code-mode-windows.json) are authoritative.

From `mcp/social-forge`:

```sh
uv run --with tiktoken python benchmarks/code_mode.py --deno deno --repeats 5
```

The benchmark does not publish anything, load production credentials or require a paid service. First-time
dependency/tokenizer-cache installation can require internet access; timed scenarios use local services.
The current benchmark is Windows-only; rerun with `--output PATH` on other OSes before comparing them.

## Schema size

Tokens use `cl100k_base` over canonical serialized JSON, not an assertion about every client's tokenizer.

| Catalog | Tokens |
|---|---:|
| Existing 15 direct MCP tools | 1,460 |
| Equivalent private direct MCP harness (ten capability adapters) | 844 |
| Only the two Code Mode tools | 210 |
| Actual additive legacy + Code Mode catalog | 1,667 |

The shipped interface is always available and additive. Standard clients that load every schema see a **larger** catalog with
Code Mode present. Selecting only the two tools lowers initial schema size, but discovery results add schemas back
into the conversation. No client-specific filtering or hidden removal of legacy tools is assumed.

## Equivalent operation harness

The old direct tools have no exact accounts-list/proposal/approval counterpart. To avoid conflating unlike
operations, six paired scenarios use a private in-process FastMCP direct-tool harness over the **same
authorized capability adapters**. It is benchmark scaffolding, not additional shipped tools. Genuine existing
direct-tool timings are reported separately below; this harness is not described as a legacy API replacement.

Both sides run the same host handlers, permissions, schemas and SQLite audit. Code Mode adds restricted
process startup and stdio RPC. Latency measures the direct calls versus `execute`, excluding discovery time
and model/network latency. Round-trip counts are modeled agent/tool counts (including one search for Code
Mode), not network timing measurements. The schedule case activates once and then exercises idempotent
activation; it does not submit any remote scheduled publication.

| Scenario | Direct median ms | Code Mode median ms | Direct modeled trips | Code trips incl. search |
|---|---:|---:|---:|---:|
| Configured accounts | 8.462 | 81.318 | 1 | 2 |
| Three provider requirements | 25.557 | 97.064 | 3 | 2 |
| Validate video for three providers | 36.403 | 105.768 | 1 | 2 |
| Preview + multi-platform proposal | 92.172 | 163.249 | 2 | 2 |
| Approved schedule activation | 23.993 | 94.961 | 1 | 2 |
| Cached analytics | 8.654 | 80.039 | 1 | 2 |

Every paired result matched after excluding intentionally unique proposal IDs. No scenario reported an
error. This tests correctness against local implementations, **not** actual provider acceptance.
Null execution median: **53.5 ms**, including runtime version check/startup, protocol and local audit work.
Last-sample sandbox RSS in these cases was approximately 29 MiB. Sampled child CPU and RSS are in raw JSON;
10 ms sampling can miss short-lived CPU/allocation peaks and is not a hard kernel quota measurement.

## Model-visible JSON estimate

These estimates add schema, argument and result JSON. Code Mode also includes discovery result schemas and
returned metrics. They exclude actual model reasoning, natural-language history, billing conventions and
network transport envelopes. Unique IDs/metrics can cause small per-run variations. They are reproducible
serialization estimates, not observed LLM-token savings.

| Scenario | Direct harness | Code with only two selected schemas | Code with actual additive catalog |
|---|---:|---:|---:|
| Configured accounts | 928 | 492 | 1,949 |
| Three provider requirements | 1,388 | 1,011 | 2,468 |
| Three-provider media validation | 949 | 564 | 2,021 |
| Multi-platform proposal | 1,601 | 1,705 | 3,162 |
| Approved schedule activation | 917 | 504 | 1,961 |
| Cached analytics | 919 | 483 | 1,940 |

Code Mode did not win every selected-schema scenario and did not beat the full-catalog baseline in this
measurement. Its benefit here is composing host calls/transformations, with fewer modeled tool trips for
the three-provider requirements case. Keep direct tools for simple calls.

## Actual existing direct tools

The same temporary fixture was also used with shipped MCP tools. Median in-process timings:

| Tool | ms |
|---|---:|
| `brand_info` | 0.044 |
| `platform_rules` | 0.021 |
| `check_video` | 25.884 |
| `preview_post` | 1.416 |
| `insights_report` | 0.075 |

These omit the new capability audit/authorization layer and return different shapes, so they are not paired
as equivalent workflows with the new proposal/account APIs. They demonstrate why the direct path is preserved.

## Unmeasured work

Real provider latency, live quotas/scopes/processing outcomes, transport/network overhead, actual model-visible
conversations, host Python CPU/peak memory and a comparative engine/OS matrix were not measured. Provider
partial-failure/restart behavior is covered by fake publishers and actual Meta adapters with MockTransport
in tests, separately from latency benchmarks. No real publication test was authorized or run.
