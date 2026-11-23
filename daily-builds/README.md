# Daily Builds

A collection of small, well-crafted projects built one per day.

| Date | Project | Description | Link |
|------|---------|-------------|------|
| 2026-11-23 | rwx-guard | Offline permission-policy engine and auditor for AI-agent tool calls, in TypeScript: a small YAML/JSON policy (Unix-style 0/r/w/x levels, glob rules on tool names, paths, hosts and shell commands, argument constraints, rate budgets) decides allow/deny/ask for every tool call | [→ rwx-guard](./2026-11-23-rwx-guard/) |
| 2026-11-22 | chunk-bench | Offline RAG chunking benchmark: converts a Markdown/text corpus into chunks with several strategies (fixed, sentence, recursive, markdown-heading-aware), indexes them with a deterministic fake embedder plus BM25, and scores each strategy on a labelled question set (hit@k, MRR, context precision, token cost) | [→ chunk-bench](./2026-11-22-chunk-bench/) |
| 2026-11-21 | mcp-probe | Offline conformance & robustness tester for MCP servers with schema fuzzing, handshake validation, and CI scoring | [→ mcp-probe](./2026-11-21-mcp-probe/) |
| 2026-11-20 | agentlens | Offline analyzer for AI agent trace reliability with pattern detection, scoring, and CI gates | [→ agentlens](./2026-11-20-agentlens/) |
| 2026-11-19 | modelgate | Offline-testable, OpenAI-compatible LLM gateway with intelligent routing by cost/latency/quality, fallback, circuit breakers, caching, budgets, and replay simulator | [→ modelgate](./2026-11-19-modelgate/) |
| 2026-11-18 | skill-lint | Offline linter and quality scorer for agent SKILL.md files with CLI, JSON/SARIF output, and FastAPI endpoint | [→ skill-lint](./2026-11-18-skill-lint/) |
