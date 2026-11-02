# ADR 0001: Standard Python-hosted Code Mode with a restricted Deno process

Status: implemented standard interface; deployment limitations documented in [CODE_MODE.md](../CODE_MODE.md).

## Repository inspection and baseline

Before edits the worktree had only untracked `.archify/` and `.serena/`; they were left untouched.
The existing suite passed: **56 tests, 11.78 seconds** on this machine. The README, AGENTS.md, CLAUDE.md,
community-manager role, account/deployment docs, Python source, tests and GitHub workflows were inspected.

The backend is Python 3.12–3.13 with FastMCP 1.x, Pydantic via MCP, httpx, PyYAML and imageio-ffmpeg.
`domain` contains pure rules; `services` implements queue/media/publishing; `app` shares use cases between
thin CLI and MCP entrypoints. Fifteen tools are registered individually. There was no generic authorized
operation dispatcher, public SDK, capability registry, account directory or tenant identity model.

Implemented provider adapters are Meta (Instagram/Page Facebook Reels), YouTube and TikTok official APIs,
Postiz, browser and handoff. No LinkedIn or generic provider integration exists. YouTube handles local OAuth
and refresh through google-auth; Meta/TikTok credentials are loaded from ignored JSON. TikTok refresh is not
implemented. HTTP has a shared bearer guard; stdio trusts the launching owner. These are single-workspace
credentials, not per-request account ownership claims. No internal LLM is required or added.

Persistence consists of dated queue files, YAML PostSpec, JSON receipts, archived files and CSV analytics.
FFmpeg handles probing and existing analysis/render operations. An OS task/cron invokes the runner; no
database/worker broker/in-memory scheduler exists. Receipts skipped success, but before this change there
was no cross-worker lock or durable in-flight receipt before a provider call. CLI logs rotate; analytics
is a local snapshot cache with summaries. Provider errors previously became retryable strings and could
carry sensitive details. HTTP/MCP, adapters, ffmpeg, scheduler and client installation have existing tests;
CI covers Windows, Linux, macOS and an optional Docker deployment.

## Decision

Preserve Python, services, provider adapters and scheduling. Add ten explicitly allowed semantic capabilities
with schemas derived from typed handler annotations. Do not mirror all legacy tools into generated code:
publishing, approval issuance, OAuth, arbitrary file paths and heavy processing must not be generic dispatch targets.
Always expose two standard MCP tools because discovery lets clients obtain selected operation schemas progressively;
retain direct tools because the catalog is small and simple calls are cheaper without sandbox startup.

The architecture follows discovery plus execution principles in the [Cloudflare Code Mode article](https://blog.cloudflare.com/code-mode-mcp/)
and [MCP guide](https://developers.cloudflare.com/agents/model-context-protocol/guides/build-codemode-mcp-server/),
without adopting their infrastructure. It does not promise a 1,000-token catalog or universal token savings.

## Runtime alternatives

| Candidate | Isolation and async bridge | Installation/maintenance tradeoff | Measurement |
|---|---|---|---|
| Python QuickJS binding, embedded | Engine memory/interrupt controls; Python callbacks; insufficient process isolation alone | Small engine; bridge/promise scheduling and OS boundary would be additional work | Not measured |
| QuickJS in a separate restricted process | Could meet the boundary with additional OS containment/WASM work | Cross-platform packaging and async host RPC need independent engineering | Not measured |
| Node `vm` | Official docs explicitly say it is not a security mechanism | Common runtime, but not an acceptable sandbox by itself | Rejected on security, not speed |
| Deno 2 in a dedicated deny-all process | Runtime-enforced permissions around I/O; stdio RPC with Python authorization; native promises | Required Deno runtime plus core psutil dependency; existing releases for supported OSes | Tested Windows startup, CPU and sampled RSS; raw data in benchmark report |

Sources: [Deno permissions](https://docs.deno.com/runtime/fundamentals/security/),
[Deno security policy](https://github.com/denoland/deno/security/policy),
[QuickJS API](https://bellard.org/quickjs/quickjs.html),
[Python wrapper](https://github.com/PetterS/quickjs),
[Node vm security statement](https://nodejs.org/api/vm.html).
These sources were consulted; no unmeasured comparative latency/memory advantage is asserted. Deno is selected
for a maintained permission-enforcing runtime and cross-platform async IPC, not popularity or claimed speed.
No Rust component is introduced. Deno's runtime sandbox is not a kernel sandbox; resource enforcement includes
sampled monitoring, with explicit residual risks. A hard OS quota implementation was not fabricated.

## Authorization and durability

The deployment principal is configured by the owner; JS cannot supply it. Capability dispatch restricts
platforms to configured defaults intersected with the optional allowlist. Configured target IDs are resolved
in trusted adapters. Proposals store exact media/content/policy hashes in local SQLite. Approval lives in an
owner-only CLI path, never a JS/MCP capability. Activation writes a proposal reference to the existing sidecar;
the runner verifies it on every attempt. Changes to config, slot, content, assets, owner or expiry invalidate it.
Recurrence, multi-tenant service identity, live scope introspection and additional providers remain unsupported.

There is no durable JavaScript continuation engine. Proposals and scheduled queue entries are the durable
workflow boundary. Completed provider operations are represented by receipts, not replayed JS.
An OS lock serializes real runner work. Atomic in-flight receipt persistence precedes provider dispatch.
Unknown outcomes block retries until owner reconciliation; definite no-effect exceptions may be retried.
Partial failures are actual receipt states, never a cross-provider transaction. Operation IDs are local
stable correlation/deduplication keys; providers without idempotency support are not claimed to honor them.

## Consequences and validation limits

Code Mode is always registered and psutil is a core dependency. Execution adds process startup, schema discovery
and audit I/O. Its actual additive MCP catalog is larger; clients selecting only the two Code Mode schemas
see a smaller initial schema. Benchmarks report both, and show no latency advantage for local simple calls.
Normal tests use fake providers; real publication was not authorized or attempted. Native Windows execution and Linux Docker execution are
verified locally; native Linux/macOS are configured in CI, not claimed as locally run. The default Docker image
ships the official Deno binary. See the security/compatibility limitations in CODE_MODE.md before deployment.
