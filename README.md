# Vela47

Vela47 is a question-answering and research system that runs two agents over one shared document store. The RAG agent answers questions from the user's own documents in a few seconds. The deep agent takes on requests that need several steps, the web or code: it plans the work, hands each step to a ReAct subagent running against an isolated Docker sandbox, and merges the reports into one answer. Both agents cite their sources, and every stage of a run is streamed to the browser as it happens.

Everything runs on local models served by Ollama. The backend is a single FastAPI application. Persistence is SQLite or a local PostgreSQL container in development and PostgreSQL in production.

## Contents

- [Agents](#agents)
- [Use case](#use-case)
- [Request lifecycle](#request-lifecycle)
- [RAG agent](#rag-agent)
- [Deep agent](#deep-agent)
- [Retrieval and indexing](#retrieval-and-indexing)
- [Models](#models)
- [Memory and context](#memory-and-context)
- [Structured outputs](#structured-outputs)
- [Tools](#tools)
- [Sandbox](#sandbox)
- [Web access and document loading](#web-access-and-document-loading)
- [Tracing and streaming](#tracing-and-streaming)
- [Agent containment](#agent-containment)
- [Identity and access](#identity-and-access)
- [Persistence](#persistence)
- [Frontend](#frontend)
- [Failure handling](#failure-handling)
- [Testing and evaluation](#testing-and-evaluation)
- [Limits](#limits)
- [Cost](#cost)
- [Configuration](#configuration)
- [HTTP API](#http-api)
- [Running locally](#running-locally)
- [Deployment](#deployment)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)

## Agents

| | RAG agent | Deep agent |
|---|---|---|
| Intended for | Questions answered by the user's documents | Multi-step requests: research across sources, writing and testing code, reviewing files |
| Pipeline | query rewrite, hybrid retrieval, reranking, generation | planning, decomposition, subagent execution, merging |
| Sources | The user's documents | The user's documents (through the same hybrid search), the public web, the run's workspace |
| Model calls per request | 1 to 3 | up to about 30 |
| Typical latency on `qwen3.5:9b` | seconds | 2 to 3 minutes |

The agent is chosen per message (`agent=rag|deep` on the stream endpoint), so a single conversation can alternate between them. Each stored reply records which agent wrote it, and the conversation history is shared. Both agents read the same chunks and vectors with the same embedding model, so a document uploaded once is searchable by either.

## Use case

The target user is an engineer on a small team (operations, on-call, backend) who keeps internal material such as runbooks, handbooks and equipment manuals. Their questions often need two things at once: what the team's own documents say, and what the vendor's public documentation says.

**Corpus.** Documents the user uploads (plain text, Markdown, HTML, PDF, DOCX) or imports from a public URL. Each owner sees only their own documents. Defaults: 512 KB of extracted text per document, 2 MB per owner. The evaluation corpus is three internal documents (an operations runbook, an employee handbook and a sensor manual) defined in `tests/evals/evals_cases/evals_cases_rag_agent.py`.

**Web search.** Available to the deep agent's research subagent only, through DuckDuckGo, with page fetching restricted to public addresses.

**Example.** One conversation, both agents:

1. RAG: *"What does error E1042 mean and how do I fix it?"* Retrieval finds the runbook passage, reranking keeps it, and the answer says the service could not read the RDS secret after a rotation, that the task role needs `secretsmanager:GetSecretValue` on the new secret version, and cites `[1]` Operations Runbook.
2. Deep: *"What does AWS recommend so the next rotation causes no downtime, and how does that fit our runbook?"* The planner returns two RESEARCH steps. The first subagent calls `search_documents` and gets the runbook passage. The second calls `web_search`, then `fetch_url` on an AWS documentation page. The sources probe records which pages and documents were actually read, and merging writes one answer that names the runbook and the AWS URL next to the claims they support.

## Request lifecycle

1. The browser opens `GET /api/chat/stream` as an `EventSource`. The session cookie is the only credential, because `EventSource` cannot send headers.
2. The route authorizes `agent:Run` on the agent resource (`vrn:agent::rag-agent` or `vrn:agent::deep-agent`), then `session:Create` or `session:Write` on the conversation, then `knowledge:Search` on the owner's documents.
3. The owner's chunks are loaded from the database with their vectors.
4. A fresh agent is built for the request, wired to a tracer that belongs to this run only. Models hold configuration, not connections, so rebuilding is cheap. It also guarantees that nothing from another run can leak into this one. The sandbox pool and the web fetcher are process-wide and passed in.
5. The agent is refilled from the stored conversation and executed on a worker thread. Trace events are pushed onto an asyncio queue and leave as SSE frames.
6. When the answer is complete, the user message and the reply are stored. A new conversation is persisted only after its first successful answer.

## RAG agent

`app/intelligence/agents/rag_agent/`. Four layers run in order over a shared `RagContext`. The structure follows the deep agent: `RagPipeline`, a `RagPolicy` that resolves the layers, and a factory and registry for the layer types.

**Query.** Without history the question is used as is, with no model call. With history, the model rewrites a follow-up into a standalone query. The earlier turns are given as a transcript inside one message, not as chat turns, because a small model given real turns tends to answer instead of rewriting. A rewrite longer than the question plus 160 characters is treated as an answer and discarded.

**Retrieval.** Hybrid search runs twice, once for the original question and once for the rewrite, and the two rankings are fused with reciprocal rank fusion. A good rewrite makes a follow-up findable, and a bad one cannot lose what the question alone would have found. Twelve candidates go forward.

**Reranking.** One structured call scores every candidate from 0 to 10. The JSON schema is generated from the `RagRelevance` model and passed to Ollama as the output format, with `minItems` and `maxItems` set to the number of passages. Without the count, a model held to the schema could return an empty list. Passages are judged against the question as asked, with the rewrite shown only to resolve references. Ordering and the cut are vector store operations (`VectorDbOperationRerank`, `VectorDbOperationFilter`). Passages scoring at least 4 are kept, at most 4 of them. The reranker runs without reasoning and its output is capped at 512 tokens.

**Generation.** Sources come first, each under its number and document title, and the question comes last. The answer is streamed and must cite `[n]` after each claim. The reply carries `response_metadata.sources` with the document id, chunk index, rerank score and a 240-character excerpt for every number. A citation can therefore be traced to its passage even after the conversation is reopened. When no passage survives reranking, the model gets a narrower task: tell the user the documents do not cover the question. The question appears only quoted inside that instruction. The reply is a structured `{language, reply}` object, which makes the model name the question's language before writing the reply.

## Deep agent

`app/intelligence/agents/deep_agent/`. `DeepAgent` owns the conversation and never calls a model itself. Every inference happens inside a pipeline layer. `OperationPipeline` runs the layers that `OperationPolicyFull` resolves and threads one `OperationContext` through them. The pipeline also times each layer and reports what it produced, so layers need no tracing code of their own.

### Planning

The planner turns the request into an `OperationPlan`: a one-sentence goal and an ordered list of steps, each with a subagent type. The JSON schema comes from the Pydantic model and constrains decoding through Ollama's `format` parameter. The schema is deliberately kept out of the prompt. Its field descriptions are written for developers, and a small model given the full schema planned worse and sometimes copied it back. The prompt shows the shape through two short example plans instead, and a unit test keeps every schema field named in the prompt. The prompt asks for as few steps as the request needs, never more than four, and restricts CODE, TEST and REVIEW to requests about program code. The planner runs at temperature 0.1 without reasoning and sees up to eight earlier messages, so a follow-up such as "now add tests for it" can be planned.

### Decomposition

Deterministic, no model call. Each step becomes an `OperationTask` with a UUID, the step's instruction frozen verbatim, and the user's original request attached. A subagent sees its own task and the user's request, never the plan or the other steps.

### Subagent execution

For each task, a slot is leased from the sandbox pool, a fresh subagent of the task's type is built, and the task runs. A failure is recorded as an error result instead of propagating, so one failed step does not discard the others. The slot is released in a `finally` block. Tasks of one run execute in order and share the run's workspace, so files written by a CODE step are visible to the TEST step after it.

`OperationSubagent` is a minimal ReAct loop over a small fixed toolset:

| Type | Tools | Reads external content | Writes or executes |
|---|---|---|---|
| RESEARCH | `search_documents` (only when the owner has documents), `search_files`, `web_search`, `fetch_url` | yes | no |
| CODE | `list_files`, `read_file`, `write_file`, `edit_file` | no | writes files in its workspace |
| TEST | `list_files`, `read_file`, `write_test`, `run_tests` | no | writes tests, runs pytest in the sandbox |
| REVIEW | `list_files`, `read_file`, `search_files` | no | no |

Loop rules:

- At most 6 model calls with tools. After that, one final turn runs with the tools withdrawn, and the model is told so explicitly. Otherwise a model mid-task writes its next call as text and that text becomes the report.
- A first reply that calls no tool is answered once with a prompt to act. A second one is accepted, since some tasks need no tool.
- Any `<tool_call>` text left in the report is stripped. If nothing remains, the report says the step ran out of turns and includes the last real tool result (up to 1,200 characters).
- Subagents run at temperature 0.3 with a 24-message window and a sliding-window policy.

### Probes

A subagent's report is the model's account of its own work, and with small models that account drifts: tests reported as passing that never ran, files reported as written that were not. Probes check the work independently and attach their findings to the result as evidence, separate from the report.

| Probe | Used by | What it records |
|---|---|---|
| `OperationSubagentProbeSources` | RESEARCH | Pages actually returned by `fetch_url` and documents returned by `search_documents`, matched to their tool calls by id, successful results only. A step that only saw search snippets is reported as such. |
| `OperationSubagentProbeWorkspace` | CODE, TEST | Files created or changed, from SHA-256 snapshots of the workspace before and after the step. |
| `OperationSubagentProbeTests` | TEST | The headline of a fresh pytest run in the same sandbox after the step, whatever the subagent claimed. |

### Merging

Each report is written under the step it answers, followed by the probe facts on lines marked "Checked by the system". The merging prompt says those lines win when they disagree with a report, that failed steps must be reported as gaps, and that sources (URLs, document titles, file names) go next to the claims they support. The answer is streamed at temperature 0.6, in the language of the request.

## Retrieval and indexing

**Chunking.** `RagChunkerRecursive` is the default: 800-character chunks with a 120-character overlap, split on paragraphs, then lines, then sentences, then words, with the overlap built from whole pieces so it never cuts a sentence in half. `RagChunkerFixed` cuts constant-width windows. Both are selected through a factory and registry.

**Embeddings.** `qwen3-embedding:0.6b`, 1024 dimensions, embedded in batches at upload time. Queries carry the model's instruction prefix (`Instruct: ... Query: ...`), passages do not.

**Storage.** Each chunk is stored with its vector packed as float32 in `knowledge_chunks`. A chunk is represented in the framework as a `MessageSystem` with id `<document id>-<position>`, the document title as its name, and the document id and chunk index in its metadata, so the vector store needed no special type for documents.

**Search.** `VectorDbMemory` is an in-process store built per request from the owner's chunks. Cosine search is brute force, which is acceptable within the per-owner quota. Search is composed of operations resolved by a policy:

- `HybridSearchPolicy` runs hybrid search for `top_k × 2` entries, then removes near-duplicates (cosine ≥ 0.95), which keeps overlapping chunks of the same passage from filling the results.
- Hybrid search ranks every entry by cosine similarity and by BM25 and fuses the two rankings with reciprocal rank fusion (k = 60). The raw scores are on incomparable scales, but the ranks are not.
- BM25 uses k1 = 1.5, b = 0.75 and lower-cased Unicode word tokens, so Cyrillic and Latin text are tokenized the same way. It is what lets exact tokens such as error codes, function names and version numbers outrank passages that merely sound related.

Semantic-only and search-and-refine policies exist alongside it.

## Models

`ModelFoundation` wraps the Ollama client for blocking and streaming calls. `ModelConfig` is a Pydantic sampling configuration: temperature, top-p, top-k, repeat penalty, seed, stop sequences, context size, output cap, `think`, `keep_alive` (30 minutes by default) and a 120-second request timeout. `think` is passed as a top-level Ollama parameter. Inside `options` Ollama ignores it, and the model then reasons on every call.

All roles use `qwen3.5:9b` at an 8,192-token context. One context size for every call keeps a single loaded copy of the model serving planning, all subagents, merging and the RAG layers, since Ollama reloads a model when the requested context size changes.

| Role | Temperature | Reasoning | Notes |
|---|---|---|---|
| Planning | 0.1 | off | JSON schema as output format |
| Subagents | 0.3 | off | tool calling |
| Merging | 0.6 | off | streamed |
| RAG query rewrite | 0.1 | off | only with history |
| RAG reranking | 0.1 | off | JSON schema, output capped at 512 tokens |
| RAG generation | 0.4 | off | streamed |

Assistant turns are sent back to the model with their tool calls, and tool results with the name of the tool that produced them, so the model can pair each result with the call that asked for it.

## Memory and context

**Short-term memory** holds a conversation's messages. A `ContextWindow` is a bounded view over it that produces the message list for each call. When the window is full, a `ContextWindowPolicy` resolves a sequence of operations (slide, shrink, expand, flatten, summarize, truncate) that a manager applies. Policies are injected before each update by middleware: `MiddlewareSlidingWindow` drops the oldest exchange, and `MiddlewareSummarization` folds the oldest messages into one summary through a pluggable summarizer.

**Conversation history** reaches the agents bounded: the last 8 messages for the deep agent and the last 6 for the RAG agent, each cut to 1,200 characters. The deep agent passes history to planning and merging only, never to subagents. Continuity lives at the top and isolation at the bottom.

**Long-term memory** is the vector store described above.

## Structured outputs

Every parser takes a `MessageAI` and returns a typed output. The output types are text, JSON, list, classification against a closed vocabulary, and structured (validated against a Pydantic schema). They are created through `OutputParserFactory`. Structured parsing uses `model_validate_json`, so a malformed plan raises at the planning layer instead of failing three layers later.

Anywhere the system needs a shape, the schema is passed to Ollama as the output format and the same Pydantic model parses the reply. Enums the model writes are string enums. Prompts show one or two short examples instead of the schema itself.

## Tools

`ToolBase[TInput, TOutput]` with a Pydantic input model whose JSON schema is sent to the model. `ToolRegistry` maps names to instances. `ToolExecutor` validates the call's arguments against the input model, runs the tool and wraps the result in a `MessageTool`. Any exception becomes a tool result with `status="error"`, so the model reads the error and can change its call.

Tools act on the sandbox of the task they belong to. Because that sandbox only exists once a task is dispatched, blueprints hold tool factories, not instances.

| Tool | Behaviour |
|---|---|
| `list_files` | Indented tree with line counts, depth 3 by default, up to 200 entries |
| `read_file` | Numbered lines, 250 at a time. A missing file answers with the files that do exist |
| `search_files` | Matching lines across the workspace, optional glob and regex, up to 40 matches |
| `write_file` | Creates or replaces a whole file, reports which, warns on Python syntax errors |
| `edit_file` | Exact-text replacement, the text must occur exactly once, answers with a unified diff |
| `write_test` | Writes a pytest file, with the same syntax check |
| `run_tests` | `python -m pytest -q` in the sandbox; leads with what the exit code means, then pytest's summary |
| `search_documents` | Hybrid search over the owner's documents, 4 passages of up to 900 characters |
| `web_search` | Title, URL and snippet per result (6 by default); reminds the model that snippets are not sources |
| `fetch_url` | A page, PDF or DOCX as text, read in 4,000-character windows from `start_index` |

## Sandbox

`SandboxPoolDocker` brings up the Docker Compose project in `app/intelligence/sandbox/sandbox_image/` at application startup and reuses its 10 containers. Each service in `docker-compose.yaml` is one slot, and the pool reads the slots from the file. Each container has:

- a fixed address, `172.30.47.10` to `172.30.47.19`, on a network that is internal (no route out), has an isolated gateway (the host has no address on it) and blocks traffic between containers
- 512 MB of memory, 1 CPU, 256 processes
- the image built from the Dockerfile next to the compose file (`python:3.12-slim` with pytest)

Every start rebuilds the image from cache and recreates the containers, and shutdown brings the project down with its network. The eval runner brings up the same project, so the evals and the server cannot run at the same time. The isolated gateway needs a recent Docker Engine (developed on 29.8). Without it, an internal network still reaches every service listening on the host.

No host directory is mounted. A run's files live on the host under a per-run directory and are read and written there directly. For each command, the run's directory is streamed into the container's `/workspace` as a tar archive on `docker exec` stdin, the command runs with a 60-second timeout, and afterwards every process in the container is killed and the workspace deleted. A mount is fixed when a container starts, so the only way to reach every run's files through a mount would expose all runs to every container. A per-command copy exposes only one. Nothing a command writes comes back to the host. Command output is capped at 8,000 characters, keeping the head and the tail.

Leasing is guarded by a lock, and `acquire()` raises when no slot is free instead of blocking. Every path coming from a model is confined to the run's directory, and files are capped at 200 KB. Without Docker, `SandboxPoolInMemory` and `SandboxEnvLocal` take over: file tools still work, and `run()` refuses, so model-written code never runs on the host.

## Web access and document loading

**Fetching.** `WebFetcher` accepts only http and https URLs whose every resolved address is public. Loopback, private, link-local, shared, multicast and reserved ranges are refused, including when embedded in IPv6 forms (IPv4-mapped, 6to4, Teredo, NAT64). Redirects are followed manually, at most 5, and every hop is checked again. The connection goes to the address the guard approved, with the original host name in the `Host` header and as the TLS server name, so certificates are still verified while the name cannot be rebound to another address. Proxy environment variables are ignored. Responses are streamed and cut at 3 MB, with a 10-second timeout per request and a 30-second deadline overall.

**Search.** `WebSearchDuckDuckGo` uses DuckDuckGo's HTML endpoint through the same fetcher, so it needs no API key. Redirect-wrapped result links are unwrapped, and ads are dropped. A rate-limit challenge is reported as an error rather than as an empty result, so the model does not conclude that a topic does not exist. The backend sits behind `WebSearchBase` and can be replaced.

**Loaders** turn bytes into text and treat every input as hostile. A file that cannot be read raises `ValueError` with a sentence meant for a person or a model.

- Text: declared charset, then UTF-8, then a lossless single-byte fallback.
- HTML: keeps headings, paragraphs, lists, tables and preformatted blocks, and drops scripts, styles, navigation, footers and forms. When `<main>` or `<article>` holds at least 30% of the text, that part is used on its own. Built on the standard library's `HTMLParser`.
- PDF: the text layer, page by page, with words hyphenated across line breaks rejoined. Scans without a text layer are refused, and so are password-protected files.
- DOCX: paragraphs and tables in document order, with headings and list styles mapped to Markdown. Declared uncompressed sizes are checked before parsing (64 MB limit) to stop zip bombs.

## Tracing and streaming

Each run gets its own `TracingService`: a lock-protected buffer plus live subscribers, with callbacks invoked outside the lock. Components receive a tracer explicitly and never check whether one is present. `TracingServiceNull` stands in when tracing is off.

Event types: `pipeline_started/finished`, `layer_started/finished`, `subagent_started/finished`, `sandbox_acquired/released`, `model_invoked`, `tool_executed`, `run_failed`, `answer_chunk`. Durations are reported as started/finished pairs, so the UI can show a step as running the moment it begins.

The stream endpoint emits five SSE event types:

| Event | Payload |
|---|---|
| `session` | conversation id, title, whether it is new (always the first frame) |
| `trace` | a serialized trace event |
| `chunk` | a piece of the answer text |
| `answer` | the complete answer, the agent name and the RAG sources |
| `error` | the exception type and message |

The trace panel shows which layer is running and what it produced, each subagent with its instruction, report, evidence and status, every tool call with its result, and every sandbox lease.

## Agent containment

Validating the output schema says nothing about whether the model followed instructions hidden in a page it read. Vela47 does not rely on the model ignoring injected text. It limits what any model can do with it.

- The only subagent that reads external content (web pages, search results, documents) is RESEARCH, and it has no tool that writes files or runs code.
- The subagents that write and execute (CODE, TEST) have no network access through their tools, and their commands run in containers on a network that cannot reach the internet, the host or another sandbox.
- External text reaches a model only as a tool result, never as a system prompt, and always truncated: 4,000 characters per page window, 900 per passage, 300 per snippet.
- Fetching cannot reach internal addresses, so an injected "fetch http://169.254.169.254/..." fails at the guard.
- Documents and conversations are scoped to their owner by policy, and no tool can address another owner's data.
- Probe facts come from the system, not from the model, and the merging prompt ranks them above the reports.

No action in the current toolset has an effect outside the run's sandbox or changes the user's stored data, so runs do not pause for confirmation. Uploading documents and importing URLs are actions the user starts directly. A confirmation step is planned for any future tool with external side effects (see [Roadmap](#roadmap)).

## Identity and access

The security layer in `app/server/security/` follows the AWS IAM model within a single account.

**Entities** are who is asking: admin, user and guest. Admins and users sign in with a password and are stored. Guests are minted on request, identified by a random id and exist only inside their token. Users are created by admins only (`iam:CreateEntity`). The first admin is bootstrapped from configuration on startup.

**Roles** are what an entity acts as. An entity assumes a role through the role's trust policy and receives an `IdentityAccessRoleSession`, the equivalent of an STS session.

| Role | Trusted by | Session length | Grants |
|---|---|---|---|
| admin | admin entities | 1 hour | everything, including identity |
| user | users and admins | 12 hours | run agents; own conversations and documents |
| guest | guests | 12 hours | run agents; own conversations and documents |

An admin can sign in as the user role for everyday work.

**Policies** are frozen Pydantic documents of three kinds: permission policies (attached to a role), resource policies (attached to a resource) and trust policies (the resource policy of a role). Statements match actions, resources and principals with `*` and `?` wildcards and `${principal.id}` substitution. Resources are named with VRNs, `vrn:<service>:<owner>:<resource>`, for example `vrn:session:<owner id>:session/<id>`.

**Evaluation** follows AWS same-account logic: an explicit deny wins, otherwise any allow grants, otherwise the request is implicitly denied. `SecurityPipeline` runs authentication and then authorization and fails closed: a service rejects by raising, and a context that ends without an allow is denied. Routes check 401, then 404, then 403.

**Actions:** `agent:Run`, `iam:AssumeRole`, `iam:CreateEntity`, `session:Create|List|Read|Write|Delete`, `knowledge:Upload|List|Delete|Search`.

**Tokens and passwords.** The session is an HS256 JWT in an HttpOnly, SameSite=Strict cookie (`vela47_session`). The algorithm is pinned on decode, and the server keeps no session table. Passwords are salted scrypt hashes (N = 2^17, r = 8, p = 1) with self-describing parameters.

## Persistence

`db/` is independent of `app/` and uses SQLAlchemy 2. `DatabaseBase` defines start, transaction and shutdown, with `DatabaseSqlite` (a file at `db/vela47.sqlite3`) and `DatabasePostgres` (psycopg 3). Both are selected through a factory and registry. Development uses SQLite unless `VELA47_DATABASE_HOST` is set, and then PostgreSQL with a user and password from the environment, as in the development deployment. Production always uses PostgreSQL on RDS.

| Table | Contents |
|---|---|
| `identity_entities` | stored admins and users, password hashes |
| `identity_access_resource_policies` | resource policies attached to VRNs |
| `chat_sessions` | conversations, messages as JSON |
| `knowledge_documents` | document metadata and size per owner |
| `knowledge_chunks` | chunk text and float32-packed vectors |

The schema is created with `create_all` at startup. Messages are rebuilt from JSON through `MessageFactory`.

The database settings are a `DatabaseConfig` (`db/database_config.py`): the SQLite file, and the PostgreSQL endpoint, port, database name, SSL mode and RDS secret id. It holds no password. `Config` carries one, filled from the `VELA47_SQLITE_PATH` and `VELA47_DATABASE_*` variables. In development it also carries the credentials of the local PostgreSQL; in production it never holds database credentials.

`app/server/config.py` is the only code that reads the environment or AWS Secrets Manager. In production, the application secret (token key, bootstrap admin) is read once at startup, and the RDS-managed database secret is read for every new connection, so a password rotation needs no restart. Production refuses to start without a database host, database secret, region and token key.

## Frontend

Plain HTML, CSS and JavaScript served by FastAPI, with no build step.

- A sign-in gate, with a "Continue as guest" option.
- Three panes: conversations, chat and trace. Below 1100 px the conversation list becomes a drawer.
- A per-message agent selector (RAG or deep).
- A documents panel with upload, URL import, deletion and quota usage.
- RAG sources listed under each RAG answer.
- An identity menu with a role switch for admin entities and a "Create user" dialog for the admin role.

## Failure handling

The system expects a small local model to fail in specific, recurring ways and handles each one in code:

| Failure | Handling |
|---|---|
| Subagent announces what it will do and calls no tool | answered once with a prompt to act |
| Subagent hits the iteration cap mid-task | final turn without tools, explicitly announced |
| Tool call written as text in the report | stripped; if nothing is left, the last real tool result is passed on |
| Tool raises or arguments fail validation | returned to the model as an error result |
| Subagent crashes | recorded as an error result; the other steps continue and merging reports the gap |
| Reranker reply unparsable or cut at 512 tokens | candidates kept in retrieval order |
| Query rewrite looks like an answer | discarded, the original question is used |
| No passage passes reranking | structured "not covered" reply, the question is never answered from general knowledge |
| Context window full | resolved by the configured context window policy |
| Web search rate-limited | reported as an error, not as zero results |
| No Docker available | in-memory pool; commands are refused instead of running on the host |

## Testing and evaluation

**Unit tests.** About 950 tests under `tests/unit/`, offline, in roughly one second. Models, sandboxes, tracers and stores are replaced with fixtures from `tests/fixtures/`. Server tests use `TestClient` without the lifespan, so no containers start.

**Live evaluations.** `tests/evals/` runs the real agents against Ollama and Docker, end to end from the question to the final answer. The evals are excluded from the default run by the `evals` marker. Each case runs 3 times (`VELA47_EVALS_RUNS`) and a check passes when at least 2 of the runs pass it. Only objective checks are asserted.

RAG agent, 6 cases (including a follow-up, a Bulgarian question over English documents and two questions the corpus does not answer):

- `facts_found`: the answer contains the expected facts (regular expressions per case)
- `cites`: the answer cites a source, and for unanswerable questions it does not
- `language_ok`: the answer is in the language of the question
- `reranked`: reranking produced scores rather than falling back

Deep agent, 5 cases (web research, an event plan, code with tests, code with review, a question in Bulgarian):

- no crash, and no raw tool call passed off as a report
- `plan_ok`: every step has an allowed subagent type and the required types appear in order
- `within_max_steps`: at most 4 steps
- `echoes_report`: the answer is not a copy of the report merging was given
- `hidden_test_passed`: code the agent wrote passes a hidden pytest test the agent never saw

Also recorded per run: tool calls, tool errors, whether every step still names the subject of the request, whether the agent's own tests pass, whether the answer claims tests passed, and `false_test_claim`, set when the answer says tests pass and the re-run says otherwise.

**LLM-as-judge.** `tests/evals/evals_judge.py` scores a finished eval session with `qwen3:14b`, a larger model than the one under test, at temperature 0 with a JSON schema. It gives *helpfulness* and *faithfulness* scores from 1 to 5 with a reason. Faithfulness asks whether every concrete claim is supported by the evidence (the retrieved passages, or the subagent reports and probe facts), which covers whether the citations support the claims. The judge runs separately from the tests because its scores are opinions. It also marks facts newer than its training data as unfaithful, so its reasons should be read before trusting a drop.

Reference-based metrics such as BLEU, ROUGE and BERTScore are not used. Open-ended research questions have no single reference answer to compare against.

## Limits

| | Value |
|---|---|
| Context per model call | 8,192 tokens |
| Plan length | 4 steps (prompt rule) |
| Subagent loop | 6 tool-calling turns plus 1 report turn |
| Model calls per deep run | at most ~30: 1 planning + 4 × 7 subagent + 1 merging |
| Model calls per RAG request | 1 to 3 |
| RAG candidates / passages to generation | 12 / 4 |
| Reranker output | 512 tokens |
| History | deep 8 messages, RAG 6, each up to 1,200 characters |
| Model request timeout | 120 s |
| Sandbox pool | 10 containers, 512 MB, 1 CPU, 256 processes each |
| Sandbox command | 60 s, 8,000 characters of output |
| Fetched response | 3 MB, 10 s per request, 30 s total, 5 redirects |
| Document text / upload size / owner total | 512 KB / 8 MB / 2 MB |

## Cost

There is no per-token API cost: every model runs locally. Measured on an Apple M5 laptop with `qwen3.5:9b` (6.3 GB loaded at an 8K context, about 12 tokens per second), a deep run takes about 2.5 minutes and a RAG request a few seconds. On the planned deployment host, a `g6.xlarge` at about $0.80 per hour on demand, that is roughly $0.03 to $0.04 of instance time per deep run and well under a cent per RAG request, assuming the instance is busy. The L4 GPU is faster than the laptop, so these numbers are an upper bound.

Two forms of caching keep this down. Every role uses the same model at the same context size, so one copy stays loaded (`keep_alive` 30 minutes) and no call pays for a reload. And inside a subagent loop the prompt only grows by appending, so Ollama's prompt cache prefills just the new turn instead of the whole conversation.

## Configuration

All variables are read in `app/server/config.py`.

| Variable | Environment | Purpose |
|---|---|---|
| `VELA47_ENVIRONMENT` | both | `dev` (default) or `prod` |
| `VELA47_SQLITE_PATH` | dev | SQLite file, default `db/vela47.sqlite3` |
| `VELA47_TOKEN_SECRET` | dev | token signing key, at least 32 bytes; generated per run if unset |
| `VELA47_ADMIN_USERNAME`, `VELA47_ADMIN_PASSWORD` | dev | bootstrap admin |
| `VELA47_DATABASE_HOST` | both | prod: RDS endpoint (required); dev: PostgreSQL server, SQLite when unset |
| `VELA47_DATABASE_SECRET_ID` | prod | RDS-managed secret (required) |
| `VELA47_APP_SECRET_ID` | prod | secret with `token_secret`, `admin_username`, `admin_password` (required) |
| `VELA47_AWS_REGION` | prod | region, falls back to `AWS_REGION` / `AWS_DEFAULT_REGION` (required) |
| `VELA47_DATABASE_PORT`, `VELA47_DATABASE_NAME`, `VELA47_DATABASE_SSL_MODE` | both | defaults `5432`, `vela47`, `require` |
| `VELA47_DATABASE_USERNAME`, `VELA47_DATABASE_PASSWORD` | dev | PostgreSQL credentials, required with `VELA47_DATABASE_HOST` |
| `VELA47_KNOWLEDGE_MAX_FILE_BYTES` | both | extracted text per document, default 512 KB |
| `VELA47_KNOWLEDGE_MAX_UPLOAD_BYTES` | both | raw upload or URL import, default 8 MB |
| `VELA47_KNOWLEDGE_MAX_OWNER_BYTES` | both | total per owner, default 2 MB |
| `VELA47_EVALS_RUNS` | evals | runs per eval case, default 3 |

## HTTP API

| Method | Path | Action |
|---|---|---|
| `POST` | `/api/auth/guest` | start a guest session |
| `POST` | `/api/auth/login` | sign in with name, password and optional role |
| `POST` | `/api/auth/logout` | clear the session cookie |
| `GET` | `/api/auth/me` | current entity and role |
| `POST` | `/api/iam/entities` | create a user or admin (admin role) |
| `GET` | `/api/sessions` | list own conversations |
| `GET` | `/api/sessions/{id}` | read a conversation |
| `DELETE` | `/api/sessions/{id}` | delete a conversation |
| `GET` | `/api/chat/stream?message=&session_id=&agent=` | run an agent, SSE response |
| `GET` | `/api/knowledge` | list own documents and usage |
| `POST` | `/api/knowledge` | upload a document (text, or base64 for PDF and DOCX) |
| `POST` | `/api/knowledge/url` | import a document from a public URL |
| `DELETE` | `/api/knowledge/{id}` | delete a document and its chunks |

Upload limits are answered with 413.

## Running locally

Requirements: Python (developed on 3.15), Docker with Compose, and Ollama with about 10 GB of free memory for the models.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

ollama pull qwen3.5:9b
ollama pull qwen3-embedding:0.6b
ollama pull qwen3:14b                # optional, evaluation judge only

export VELA47_ADMIN_USERNAME=admin
export VELA47_ADMIN_PASSWORD='change-me-please'
export VELA47_TOKEN_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"

.venv/bin/python -m uvicorn app.server.server:app --reload
```

The first start builds the sandbox image and starts the container pool. The UI is served at `http://127.0.0.1:8000/`.

```bash
.venv/bin/python -m pytest -q                                        # unit tests
.venv/bin/python -m pytest -m evals -s                               # live evals, 15 to 20 minutes
.venv/bin/python -m tests.evals.evals_judge tests/evals/results/<session>   # judge a finished session
```

Eval results are written to `tests/evals/results/<time>-<commit>/`.

## Deployment

**Development.** `deploy/dev/` runs the server and its PostgreSQL in two containers on the local Docker Desktop, managed by Terraform with the `kreuzwerker/docker` provider. Ollama stays on the host.

```bash
cd deploy/dev
terraform init
terraform apply
terraform output -raw admin_password    # sign in as admin
terraform destroy
```

| | Server | Database |
|---|---|---|
| Image | `deploy/dev/images/app_image/` | `deploy/dev/images/db_image/` (`postgres:17-alpine`) |
| Network | `vela47-app-network`, `10.112.0.0/16`, gateway `10.112.0.1` | `vela47-db-network`, `10.111.0.0/16`, gateway `10.111.0.1` |
| Address | `10.112.0.2` | `10.111.0.2` |
| Published | `127.0.0.1:8000` | `127.0.0.1:5432` |
| Data | none | `vela47-db-data` volume |

No container is on both networks. The server connects to `10.111.0.2:5432`: the packets leave through the app network's gateway and enter through the database network's gateway, so PostgreSQL sees them coming from `10.111.0.1`. Docker forwards between two bridge networks only to a published port, which is why 5432 is published. Binding it to `127.0.0.1` keeps it off the LAN. Every other port of the database container is unreachable from the app network, and the sandbox network, whose gateway is isolated, cannot reach the database at all. A gateway address cannot be used as the published address, because Docker Desktop binds published addresses on the Mac.

The server image is built from the repository root, and `terraform apply` rebuilds it and replaces the container when a file under `app/` or `db/`, `requirements.txt` or the Dockerfile changes. The server container:

- runs in DEV mode against the database container, without SSL
- reaches Ollama on the host through `host.docker.internal`, so the models keep the host's GPU
- mounts the host's Docker socket and brings the sandbox project up through it, so the sandbox containers run beside the server rather than inside it. Run directories are streamed in over `docker exec`, so no path has to exist on the host. Stopping the container brings the project down.
- gets its token key, the database password and the password of the bootstrap admin `admin` from `random_password` resources, kept in the Terraform state (`terraform output -raw database_password` for `psql`)

The volume survives a rebuild of either container; `terraform destroy` deletes it.

The container and a server started with uvicorn use the same port and the same sandbox project, so only one of them can run at a time.

**Production.** The production configuration path (RDS PostgreSQL, Secrets Manager, rotation-safe credentials) is implemented. The deployment itself is not done yet. The target is:

- one EC2 GPU instance (`g6.xlarge`, NVIDIA L4 24 GB) running the FastAPI application, Ollama and the Docker sandbox pool
- RDS PostgreSQL, Multi-AZ
- Secrets Manager for the application secret and the RDS-managed database secret
- an Application Load Balancer terminating TLS

Serverless hosting does not fit this workload. Lambda cannot run Docker containers on demand and caps execution at 15 minutes, Fargate tasks have no Docker daemon to start sandboxes from, and neither provides a GPU for the model.

## Known limitations

- The four-step plan limit is a prompt rule; the plan schema does not enforce it.
- Subagents within one run execute sequentially. The pool bounds concurrency across runs, and when all 10 slots are leased, `acquire()` raises instead of queueing.
- Vector search is brute force over the owner's chunks on every request. That is fine within the 2 MB quota and is not meant for large corpora.
- Only RAG answers carry structured source metadata. Deep agent answers name their sources in the text.
- There is no dedicated prompt-injection classifier; containment is by capability (see [Agent containment](#agent-containment)).
- Guest conversations and documents become unreachable when the guest token expires and are not cleaned up.
- The schema is created with `create_all`; there are no migrations yet.
- DuckDuckGo's HTML endpoint can rate-limit a busy address.
- Uploads are JSON with base64 content rather than multipart.

## Roadmap

These parts are planned and may not all be completed:

- Agent-to-agent (A2A) communication between subagents. Today each subagent sees only its own task and the user's request.
- A human-in-the-loop channel over WebSocket, where the orchestrator can ask the user a question mid-run, with confirmation for tools that have external side effects.
- The AWS deployment described above.
- Enforcing the step limit in the plan schema, and running independent steps in parallel.
- Cleanup of expired guest data, and Alembic migrations.
