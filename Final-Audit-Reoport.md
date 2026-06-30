Audit performed via full clone (incl. submodules) at commit 967c63d, main branch. Python, ~7,200 LOC in src/lithic_cli, MIT licensed.
Executive Summary
Lithic-CLI is a Python CLI/MCP tool that builds a "knowledge graph" of a codebase to help AI agents work with less context. The packaging, documentation, community-health files (SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, dependabot, CodeQL) and core shell-safety logic are unusually mature for a 0.2.0 project — better than most early-stage open-source tools. However, the audit found several concrete, reproducible breakages between the documented/declared deployment path and the actual code, plus a CI workflow that silently swallows test failures. These are the kind of issues that won't show up in casual review but will fail immediately for any real user trying to run the Docker/Kubernetes deployment or trust the green CI badge.
The most serious findings are not "exotic security bugs" — the shell-execution and path-traversal code is actually written carefully — but packaging/deployment correctness failures that mean the production Docker image as committed cannot start, and a CI test job that always reports success even when tests fail.

Repository Overview

Purpose: Index a codebase into a graph, then answer questions / compress output / generate commit messages / review diffs, for use by AI coding agents, both as a CLI and an MCP server.
Primary technologies: Python 3.12, click, pydantic, httpx, optional mcp, openai, anthropic SDKs, uv package manager, Docker, Kubernetes manifests.
Architecture: Three-layer design (Graph / Compression / Policy) coordinated by lithic_cli.orchestrator, wrapping three vendored upstream projects as git submodules (graphify, headroom, caveman).
Strengths: Subprocess calls use list-form (no shell=True), a real destructive-command confirmation gate, path-traversal guarding in tools/fs.py, CodeQL + Dependabot + pinned dependency versions, audit logging hooks, MCP rate limiting.
Weaknesses: The Docker/Kubernetes deployment path is broken in multiple independent ways; CI silently hides test failures; README/docs drift from the actual CLI surface; CHANGELOG.md is referenced but deleted; several "enterprise" modules (web, microservices, caching, streaming) exist but are not wired to documented commands consistently.


Detailed Findings
Category: Deployment / Production Readiness (Critical Cluster)
Finding 1 — Docker image cannot run: console script name mismatch

Severity: Critical | Confidence: High | Category: Correctness / Production Readiness
Affected files: Dockerfile (ENTRYPOINT line), pyproject.toml line 45
Evidence: pyproject.toml declares [project.scripts] lithic = "lithic_cli.cli:main" — the only installed console script is named lithic. The Dockerfile's ENTRYPOINT ["uv", "run", "lithic_cli", "mcp", "serve"] invokes a binary named lithic_cli, which does not exist.
Root cause: Inconsistent naming between the packaging metadata and the container entrypoint, likely from a rename of the project (Lithic → lithic_cli/lithic-cli) that wasn't propagated to the Dockerfile.
User impact: Anyone building and running the published Docker image gets an immediate command not found failure; the container never starts.
Suggested fix: Change ENTRYPOINT to ["uv", "run", "lithic", "mcp", "serve"], and add an integration test that actually builds and runs the image (docker run --rm <image> --help).
Difficulty: Easy | Priority: P0

Finding 2 — Docker has both ENTRYPOINT and CMD, producing a malformed final command

Severity: Critical | Confidence: High | Category: Correctness
Affected files: Dockerfile
Evidence: The file defines CMD ["python3", "-m", "lithic_cli.mcp.server"] followed later by ENTRYPOINT ["uv", "run", "lithic_cli", "mcp", "serve"]. In Docker exec-form semantics, CMD becomes default arguments appended to ENTRYPOINT, so the effective command at container start is uv run lithic_cli mcp serve python3 -m lithic_cli.mcp.server — a single broken command line, not "use CMD as a fallback module invocation."
Root cause: Two separate, conflicting ways of starting the server were left in the file (likely from iterative edits) without removing the earlier one.
User impact: Compounds Finding 1; even after fixing the binary name, the trailing stray arguments (python3 -m lithic_cli.mcp.server) would still be passed to lithic mcp serve, which is not designed to accept them.
Suggested fix: Keep only one launch mechanism — either ENTRYPOINT ["lithic"] + CMD ["mcp", "serve"] (preferred, since lithic is on PATH via the venv), or a single non-split ENTRYPOINT array. Remove the redundant CMD.
Difficulty: Easy | Priority: P0

Finding 3 — MCP extra not installed in the production image, but the entrypoint launches the MCP server

Severity: Critical | Confidence: High | Category: Correctness / Dependency Audit
Affected files: Dockerfile, pyproject.toml
Evidence: pyproject.toml lists mcp only under [project.optional-dependencies] mcp = ["mcp==1.28.1"], not in the base dependencies list. The Dockerfile builder stage runs uv sync --no-dev --frozen with no --extra mcp, then the runtime image's entrypoint runs mcp serve, which imports lithic_cli.mcp.server — a module that depends on the mcp package.
Root cause: The base dependency set and the container's actual runtime requirement are out of sync.
User impact: Even after fixing Findings 1–2, the container would crash on import with ModuleNotFoundError: mcp (or fail silently depending on how the import is guarded).
Suggested fix: Add --extra mcp to the uv sync command in the builder stage, or move mcp into core dependencies if the MCP server is the documented primary container workload.
Difficulty: Easy | Priority: P0

Finding 4 — Kubernetes manifest health/readiness probes target an HTTP server that doesn't exist for the stdio MCP workload

Severity: High | Confidence: High | Category: Production Readiness / Observability
Affected files: k8s/deployment.yaml, src/lithic_cli/mcp/server.py
Evidence: k8s/deployment.yaml defines livenessProbe/readinessProbe with httpGet: path: /health, port: 8000 and a Service exposing port 8000, while mcp/server.py contains the comment """Sliding-window rate limiter per-process — adequate for stdio only.""" and the whole module is built around stdio transport (matching the README: "Start the MCP server... over stdio"). There is no HTTP route handler for /health or /ready anywhere in mcp/server.py.
Root cause: The k8s manifest appears to have been written for a hypothetical HTTP/web mode (matching src/lithic_cli/web/__init__.py, which does exist as a 619-line module) but was paired with the stdio MCP entrypoint, not the web one.
User impact: If deployed as-is, Kubernetes will never mark the pod Ready (no listener on 8000 answering /health), so the Deployment will sit in CrashLoopBackOff/0/3 Ready indefinitely. This manifest is unusable without modification.
Suggested fix: Either (a) point the Deployment's command at lithic web --host 0.0.0.0 --port 8000 and confirm that module actually serves /health and /ready, or (b) if stdio MCP is the intended workload, remove the k8s manifest's HTTP probes/Service and use a process-liveness check instead (the existing healthcheck.py approach used in the Dockerfile is the right pattern — reuse it as an exec probe).
Difficulty: Medium | Priority: P0

Finding 5 — lithic init is referenced in example docs but does not exist in the CLI

Severity: Medium | Confidence: High | Category: Documentation / DX
Affected files: examples/README.md, examples/basic-usage/README.md
Evidence: Both files instruct users to run lithic init. Inspecting src/lithic_cli/cli.py's registered commands (index, ask, explain, graph_path, edit, review, commit, compress_file, web, services, stats, plus mcp serve/upstream-status referenced in README) shows no init command is defined anywhere in the file.
Root cause: Stale example documentation from an earlier CLI naming scheme (the quick start elsewhere correctly says lithic index .).
User impact: A new contributor following the bundled example will hit Error: No such command 'init' on their very first step — a serious first-impression DX failure for exactly the kind of beginner-friendly example documentation that's supposed to onboard people.
Suggested fix: Replace lithic init with lithic index . in both example READMEs; add a CI doc-lint step that greps documented commands against cli.py's registered command names.
Difficulty: Easy | Priority: P1

Finding 6 — README's CLI Commands table is incomplete relative to the actual CLI

Severity: Low | Confidence: High | Category: Documentation
Affected files: README.md, src/lithic_cli/cli.py
Evidence: The README's "CLI Commands" table omits lithic web and lithic services, even though both are real, documented-elsewhere (deeper in the same README, and in docs/comprehensive-improvements.md and docs/deployment.md) and registered in cli.py.
User impact: Minor — discoverability gap for the table meant to be the canonical command reference.
Suggested fix: Auto-generate the table from click's command registry as part of the doc build, so it can't drift again.
Difficulty: Easy | Priority: P3

Finding 7 — CHANGELOG.md is referenced/listed but no longer exists in the repository

Severity: Low | Confidence: High | Category: Documentation / Open Source Readiness
Affected files: repository root (file removed)
Evidence: git log --all -- CHANGELOG.md shows the file was created (feat: update changelog...) and then removed in a later Cleanup commit, yet GitHub's own repository file listing still surfaces CHANGELOG.md as a tracked path in cached views, and the project explicitly markets a lithic commit feature for Conventional-Commit-style messages, which implies changelog generation is a core use case.
Root cause: File was deleted without removing references/expectations around it.
User impact: Contributors and users have no way to see release-over-release changes; undermines trust for a tool explicitly pitched at producing changelog-quality commit messages.
Suggested fix: Restore CHANGELOG.md (Keep a Changelog format) and wire it into the release workflow, e.g. generated from Conventional Commits via release.yml.
Difficulty: Easy | Priority: P2


Category: CI/CD & Open Source Engineering Practices
Finding 8 — CI "test" jobs mask all test failures with || echo

Severity: High | Confidence: High | Category: Testing Debt / CI Integrity
Affected files: .github/workflows/ci.yml (test and test-extras jobs)
Evidence: Both jobs run uv run python -m pytest tests/test_basic.py -v || echo "Tests completed". In shell, A || B only runs B if A fails, and the step's exit code becomes B's exit code (0), so a failing test suite is reported as a passing CI step.
Root cause: A debugging/iteration leftover (likely added so early development pushes wouldn't block on flaky tests) that was never removed.
User impact: The green CI badge on the README is not trustworthy for the test/test-extras jobs — a regression in tests/test_basic.py would not block merges or be visible in the PR checks UI for those two jobs. (Note: the separate coverage.yml workflow does run the full tests/ suite without this suppression, which partially mitigates the risk but doesn't run on every PR push gate the same way ci.yml's required checks would.)
Suggested fix: Remove || echo "Tests completed" from both steps; let pytest's exit code propagate. Also expand the test job to run the full tests/ directory, not just test_basic.py, since 16 test files exist across tests/cli, tests/graph, tests/mcp, tests/updater, etc.
Difficulty: Easy | Priority: P0

Finding 9 — ci.yml lint/test jobs don't set explicit permissions:

Severity: Low | Confidence: Medium | Category: Security (GitHub Actions / Supply Chain)
Affected files: .github/workflows/ci.yml
Evidence: codeql.yml and release.yml both declare an explicit permissions: block (least-privilege practice); ci.yml's lint, test, and test-extras jobs declare none, meaning they inherit the repository/org default GITHUB_TOKEN permissions, which can be broader than needed for a job that only checks out code and runs lint/tests.
Root cause: Inconsistent application of the least-privilege pattern that's already used elsewhere in the same .github/workflows directory.
User impact: Low risk in this specific case (no write actions in these jobs), but it's a missed opportunity for defense-in-depth and inconsistent with the project's own established pattern.
Suggested fix: Add permissions: contents: read to each job in ci.yml.
Difficulty: Easy | Priority: P3

Finding 10 — Release workflow requests id-token: write but uses a static PyPI token instead of OIDC Trusted Publishing

Severity: Low | Confidence: Medium | Category: Supply Chain Security
Affected files: .github/workflows/release.yml
Evidence: The job declares permissions: id-token: write (the permission needed for OIDC-based trusted publishing) but then runs uv publish with env: UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }} — a long-lived static secret, not OIDC.
Root cause: Either the id-token: write permission is vestigial/unused, or trusted publishing was intended but not finished.
User impact: A static PYPI_TOKEN secret is a higher-value, longer-lived credential than an OIDC-based short-lived token; if leaked it grants ongoing publish rights until manually revoked.
Suggested fix: Either remove the unused id-token: write permission, or switch to PyPI Trusted Publishing (uv publish supports OIDC) and drop the static token entirely.
Difficulty: Medium | Priority: P2


Category: Security Review
Finding 11 — Shell execution path: well-implemented, no injection found

Severity: Informational (positive finding) | Confidence: High | Category: Security
Affected files: src/lithic_cli/tools/shell.py
Evidence: subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout) is called with command as a list[str], never with shell=True and never via string concatenation — this avoids the classic CWE-78 OS command injection pattern. A destructive-command heuristic (_is_destructive) gates rm -rf, git reset/clean, forced pushes, etc., behind an interactive confirmation or an explicit LITHIC_ALLOW_DESTRUCTIVE environment opt-in for non-interactive contexts.
Note: The destructive-command detection is a deny-list/heuristic, not a sandbox — it's reasonable as a guardrail against accidental destructive actions by an AI agent, but should not be treated as a hard security boundary (a determined or malicious caller could craft a command not matching any of the patterns, e.g. python -c "import os; os.system('rm -rf .')" would not match _DANGEROUS_PYTHON_KEYWORDS since it checks for the literal strings shutil, rmtree, os.remove, os.unlink, send2trash, not os.system).
Suggested fix (Medium priority, P2): Document explicitly in SECURITY.md that the destructive-command list is best-effort, not a sandbox; add os.system, subprocess, eval(, exec( to the keyword list as cheap additional coverage.

Finding 12 — VaultSecretBackend and other backends silently swallow all exceptions and fall back to plain environment variables

Severity: Medium | Confidence: High | Category: Security (Fail-Open) / Reliability
Affected files: src/lithic_cli/secrets.py, VaultSecretBackend.get_secret/list_secrets
Evidence: except Exception: return os.getenv(key.upper()) (and return [] for list_secrets) — any Vault error (network failure, auth failure, TLS verification failure, malformed response) is silently caught and the function falls back to reading a plain environment variable instead of raising or logging.
Root cause: Defensive coding taken too far — "fail open" rather than "fail closed" for a secrets backend.
User impact: In a production deployment that intentionally chose Vault for centralized secret rotation/auditing, a misconfigured Vault connection (e.g., expired token) will silently and invisibly fall back to whatever is in the process environment, with no error surfaced. This could mask a security misconfiguration or cause use of a stale/wrong key without any operator visibility.
Suggested fix: Log a warning (not silently pass) on the Vault exception path, and consider making fallback behavior configurable (fail_open vs fail_closed) rather than unconditional.
Difficulty: Easy | Priority: P2

Finding 13 — Path traversal guard (resolve_path_within_root) is reasonably solid but has a narrow symlink-of-symlink gap

Severity: Low | Confidence: Medium | Category: Security (CWE-22)
Affected files: src/lithic_cli/tools/fs.py
Evidence: The function resolves the candidate path, checks base.is_symlink() once and re-resolves through that single symlink hop, then validates the final resolved path is inside root via resolved.relative_to(root.resolve()). Because the final check uses the fully .resolve()d path (which Python's pathlib.resolve() itself follows symlinks recursively for), the one-hop manual symlink check looks partially redundant, and the final relative_to check is what actually provides protection against most traversal — that part looks correct.
Confidence note: I was not able to construct or run a live exploit against this in the audit; flagging as Low/Medium-confidence based on static reading rather than a verified bypass.
Suggested fix: Add a unit test specifically for nested-symlink traversal (tests/tools/test_fs.py exists but should explicitly include this case) to confirm the protection holds, and simplify the function to rely solely on Path.resolve() + relative_to() rather than the extra manual single-hop symlink branch, which adds complexity without clearly adding protection.
Difficulty: Easy | Priority: P3

Finding 14 — API keys read from plain environment variables / .env by default

Severity: Low (by design) | Confidence: High | Category: Security / Configuration
Affected files: src/lithic_cli/config.py, .env.example, src/lithic_cli/secrets.py
Evidence: EnvironmentSecretBackend is the default fallback if no Vault/K8s-secrets/.lithic/secrets.json is detected; config.py uses python-dotenv to load a .env file from the project root with override=False.
Note: This is standard and acceptable for a developer CLI tool (this is the Twelve-Factor App pattern), and .env.example plus .gitignore (which I confirmed lists .env) shows good hygiene against committing real secrets. Flagged only as informational since the project does also offer Vault/K8s-secret backends for production use, which is a sensible escalation path — no actual misuse found.

Finding 15 — lithic-cli core dependency graphifyy==0.8.49

Severity: Informational | Confidence: Medium | Category: Dependency Audit
Affected files: pyproject.toml
Evidence: All dependencies are pinned to exact versions (click==8.1.7, httpx==0.28.1, etc.) rather than ranges, with uv.lock for full lockfile reproducibility, and Dependabot configured for pip, github-actions, and gitsubmodule ecosystems on a weekly cadence.
This is good supply-chain hygiene; the only caveat is that I was unable to verify from the available repository whether any of these exact pins currently have published CVEs, since that requires live vulnerability-database lookups outside the scope of static repo review. Recommend running pip-audit or relying on Dependabot/CodeQL alerts (already configured) as the ongoing mechanism.


Category: Architecture
Finding 16 — Three large "enterprise" modules exist with unclear integration into the documented core workflow

Severity: Medium | Confidence: Medium | Category: Architecture / Maintainability
Affected files: src/lithic_cli/microservices/__init__.py (401 lines), src/lithic_cli/caching/__init__.py (399 lines), src/lithic_cli/streaming/__init__.py (373 lines), src/lithic_cli/web/__init__.py (619 lines) — all implemented as single large __init__.py files rather than proper submodule packages.
Evidence: These four files total ~1,800 lines (about 25% of the whole src/lithic_cli codebase) yet none of them appear in the README's primary "What it does" feature list, and the optional dependency groups they presumably need (redis, psycopg2-binary, fastapi, uvicorn, watchfiles, prometheus-client) are all under a single enterprise extra that nothing in the README's Quick Start references.
Root cause: Likely scope creep — "enterprise readiness" features (caching, streaming, microservices, web server) were added speculatively ahead of the core CLI/MCP workflow being fully stabilized (see Findings 1–4 showing the basic Docker/MCP path itself isn't yet working).
User impact: For a CLI labeled "0.2.0," this is a large surface area to maintain, test, and document, and it dilutes the otherwise tight, well-explained graph-first architecture description in docs/architecture.md. It also increases the dependency-vulnerability surface area unnecessarily for users who only want the core graph/CLI functionality.
Suggested fix: Either flesh these out into properly tested, documented "enterprise" features with their own docs page and examples, or move them behind a clearly marked "experimental" flag / separate package until the core path (Findings 1–4) is solid. Putting each in its own module.py (rather than __init__.py) inside the package would also improve readability and is the more conventional Python layout.
Difficulty: Large Refactor | Priority: P2

Finding 17 — Layered architecture (Graph / Compression / Policy / Orchestrator) is clearly documented and the code structure matches the documentation

Severity: Informational (positive) | Confidence: High
Evidence: docs/architecture.md and the README's Mermaid diagram describe lithic.graph.graphify_adapter, lithic.compression.headroom_adapter, and lithic.policy.response_policy coordinated by lithic.orchestrator — and the actual file tree (src/lithic_cli/graph/, compression/, policy/, orchestrator.py) matches this description exactly. This kind of doc-to-code fidelity for the core design is a genuine strength and worth preserving as the project grows the "enterprise" modules noted in Finding 16.


Risk Matrix
SeverityCountCritical3High2Medium4Low6Informational3

Top 10 Highest Priority Fixes

Fix Dockerfile binary name lithic_cli → lithic (Finding 1) — P0
Remove the duplicate/conflicting CMD + ENTRYPOINT in the Dockerfile (Finding 2) — P0
Install the mcp extra in the Docker build stage (Finding 3) — P0
Remove || echo "Tests completed" from ci.yml's test jobs so failures actually fail CI (Finding 8) — P0
Fix or remove the Kubernetes HTTP health/readiness probes that don't match the stdio MCP workload (Finding 4) — P0
Fix examples/*/README.md referencing the non-existent lithic init command (Finding 5) — P1
Stop silently swallowing exceptions in VaultSecretBackend (log instead of silent fallback) (Finding 12) — P2
Restore or remove the dangling CHANGELOG.md reference (Finding 7) — P2
Decide trusted-publishing vs static PyPI token in release.yml, and drop the unused id-token: write if not used (Finding 10) — P2
Scope or document the four large "enterprise" modules (web, microservices, caching, streaming) (Finding 16) — P2


Technical Debt Assessment

Architectural debt: Moderate — the core three-layer design is clean, but the enterprise modules (Finding 16) represent unintegrated scope that adds maintenance burden without corresponding tests/docs found during this audit.
Testing debt: High — CI doesn't actually gate on test failures for two of its three test-related jobs (Finding 8); the main test job only runs one test file out of sixteen.
Documentation debt: Moderate — strong document set exists (architecture.md, setup.md, deployment.md, source-review.md, merge-notes.md) but has drifted from the actual CLI surface in places (Findings 5, 6, 7).
Security debt: Low-Moderate — no injection vulnerabilities found; the fail-open Vault fallback (Finding 12) is the most concrete issue.
Operational debt: High — the documented production deployment path (Docker + Kubernetes) does not function as committed (Findings 1–4); anyone trying to follow docs/deployment.md today would hit failures.


Scores (0–100)
CategoryScoreJustificationSecurity72No injection/RCE found; subprocess handling is genuinely careful; deducted for the fail-open Vault fallback and unverifiable dependency CVE status.Architecture70Core layered design is clean and well-documented; deducted for unintegrated "enterprise" module sprawl.Code Quality70Readable, typed (mypy disallow_untyped_defs), ruff-linted; deducted for several __init__.py-as-module-dump files.PerformanceN/A (Unable to verify)No benchmarking data was generated in this audit beyond reading benchmarks/bench_compression.py's existence; no fabricated numbers are given.Testing4516 test files exist and a full-suite coverage workflow exists, but the primary CI gate (ci.yml) doesn't actually enforce test results (Finding 8).Documentation65Genuinely extensive docs set, but multiple confirmed drift/broken-reference issues (Findings 5, 6, 7).Developer Experience55The first onboarding example (lithic init) is broken (Finding 5); core uv sync + CLI quick start otherwise reads cleanly.Maintainability65Clear module boundaries for the core layers; large untested modules drag this down.Open Source Readiness78LICENSE, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, issue/PR templates, Dependabot, CodeQL all present — genuinely above average for this project stage.Production Readiness35The documented Docker/Kubernetes deployment path does not currently work as committed (Findings 1–4) — this is the single biggest score driver.Overall Repository Health62Solid foundations and unusually good open-source hygiene for community files and CI scaffolding, undercut by deployment-path breakage and a CI gate that doesn't actually gate. Fixable largely with P0/P1 items above.

Open Source Competitiveness
Compared to mature graph/codebase-indexing CLI tools (e.g., established code-intelligence or RAG-for-code tools), Lithic-CLI's community-health scaffolding is competitive (SECURITY.md, CodeQL, Dependabot, issue templates are all present, which many small projects skip). Its documentation breadth (8 docs files plus README) is also above average for a 0.2.0 release.
Where it currently falls short of mature comparable projects: a working, verified container/Kubernetes deployment story (most mature CLI/agent tools either don't ship a Docker image at all, or ship one that's been smoke-tested in CI); CI that actually enforces its own test suite; and a smaller, more focused core feature set rather than four large speculative "enterprise" modules bolted on early.
Recommended roadmap priority: stabilize and CI-test the core CLI + MCP + Docker path completely (Findings 1–4, 8) before continuing to build out web/microservices/caching/streaming — right now the "enterprise" surface area is larger than the verified-working core surface area, which is an inverted priority for a 0.2.0 project trying to attract contributors.

Immediate Actions (Next 24 Hours)

Fix the Dockerfile ENTRYPOINT (binary name + remove duplicate CMD) — Findings 1, 2.
Add --extra mcp to the Docker build's uv sync — Finding 3.
Remove || echo "Tests completed" from ci.yml — Finding 8.
Fix lithic init → lithic index . in both example READMEs — Finding 5.

Short-Term Roadmap (1–4 Weeks)

Rework k8s/deployment.yaml probes to match the actual transport (stdio exec probe, or wire it to lithic web) — Finding 4.
Expand ci.yml's test job to run the full tests/ directory, matching coverage.yml.
Add explicit permissions: contents: read to all CI jobs — Finding 9.
Fix the silent exception swallowing in VaultSecretBackend — Finding 12.
Restore CHANGELOG.md and wire it to lithic commit/release tooling — Finding 7.
Decide and implement PyPI Trusted Publishing vs. static token in release.yml — Finding 10.

Long-Term Roadmap (1–6 Months)

Either properly build out and document the web, microservices, caching, streaming modules with their own test coverage and docs, or move them out of the default package until ready — Finding 16.
Add a CI "docs-lint" step that cross-checks documented CLI commands against the live click command registry, to prevent future README/example drift.
Run a dependency vulnerability scan (pip-audit or similar) against the pinned uv.lock versions and review CodeQL findings on a recurring cadence — supplements the already-good Dependabot setup.
Add an automated "build & smoke-test the Docker image" CI job so deployment-path regressions like Findings 1–4 are caught automatically going forward.